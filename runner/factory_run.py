#!/usr/bin/env python3
"""Headless factory runner: one pass over a repository's headless factory changes.

Each change lives on a `factory/<slug>` branch with one pull request. Per pass
and per change, the runner re-derives every approval from approvers' pull-request
reviews (an approval written into status.yaml any other way is undone), then
runs the next factory skill through a headless harness. Run it from cron or CI
in a dedicated clone:

    python3 runner/factory_run.py <clone> --approvers alice,bob [--harness "claude -p"]

Approver reviews in state APPROVED, first line:
    approve <product|architecture|interface|slices>
    sign off slice <NN>
While a change waits for its approvers, their other comments and reviews after
its question are passed to the next skill run as their replies.

Reads status.yaml with the factory hook's parser, which relies on the one-line
flow maps the skills write; a YAML library if that format grows.
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from factory_gate import GATES, parse_status

BRANCH = re.compile(r"^factory/[A-Za-z0-9._/-]+$")
GIT_TIMEOUT = 300
MAX_REPLY_BYTES = 100_000
PENDING = "{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }"


def run(cwd, *cmd, timeout=GIT_TIMEOUT, binary=False):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=not binary, check=False, timeout=timeout)
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace") if binary else r.stderr
        raise RuntimeError(f"{' '.join(cmd[:3])}: {err.strip()}")
    return r.stdout


def blob_sha256(repo, ref, path):
    try:
        return hashlib.sha256(run(repo, "git", "show", f"{ref}:{path}", binary=True)).hexdigest()
    except RuntimeError:
        return None


def is_ancestor(repo, older, newer):
    try:
        run(repo, "git", "merge-base", "--is-ancestor", older, newer)
        return True
    except RuntimeError:
        return False


def command(body):
    lines = body.strip().splitlines()
    first = lines[0].strip().lower() if lines else ""
    m = re.fullmatch(r"approve (product|architecture|interface|slices)", first)
    if m:
        return ("approve", m.group(1))
    m = re.fullmatch(r"sign off slice (\d+)", first)
    return ("sign-off", m.group(1)) if m else None


def next_skill(status):
    """The skill a change needs next, or None when it is finished."""
    if status["scalars"].get("reconciled") == "true":
        return None
    for gate, _ in GATES:
        if status["gates"].get(gate, {}).get("state") not in ("approved", "skipped"):
            return f"factory-{gate}"
    for s in status["slices"]:
        if s["state"] != "done":
            return "factory-review" if s["state"] == "green" else "factory-build"
    return "factory-reconcile" if status["slices"] else None


def replace(text, pattern, new):
    out, n = re.subn(pattern, new, text, count=1, flags=re.MULTILINE)
    if n != 1:
        raise RuntimeError(f"status.yaml has no line matching {pattern!r}")
    return out


def set_gate(text, gate, value):
    return replace(text, rf"^\s+{gate}:\s*\{{.*\}}.*$", f"  {gate}: {value}")


def set_slice_state(text, sid, state):
    def swap(m):
        return re.sub(r"\bstate:\s*[\"']?\w+[\"']?", f"state: {state}", m.group(0), count=1)
    out, n = re.subn(rf"^\s*-\s*\{{[^}}]*\bid:\s*[\"']?0*{int(sid)}\b[^}}]*\}}", swap, text, count=1,
                     flags=re.MULTILINE)
    if n != 1:
        raise RuntimeError(f"status.yaml has no slice {sid}")
    return out


def verify(repo, ref, change, text, approvals, may_skip):
    """Re-derive gate approvals and slice sign-offs from approval reviews.

    `change` is the change folder relative to the repository; `approvals` are
    APPROVED reviews by approvers; `may_skip` are the gates triage skipped.
    Returns the corrected status text and notes.
    """
    status = parse_status(text)
    notes, blocked = [], False
    for gate, doc in GATES:
        state = status["gates"].get(gate, {}).get("state")
        if state == "skipped" and gate in may_skip:
            continue
        if state == "skipped":
            text = set_gate(text, gate, PENDING)
            notes.append(f"{gate} reset to pending: triage did not skip it")
            state = "pending"
        current = blob_sha256(repo, ref, f"{change}/{doc}")
        backing = [r for r in approvals if command(r["body"]) == ("approve", gate)
                   and current and blob_sha256(repo, r["commit"], f"{change}/{doc}") == current]
        if state == "approved" and (blocked or not backing
                                    or status["gates"][gate]["doc_sha256"] != current):
            text = set_gate(text, gate, PENDING)
            notes.append(f"{gate} reset to pending: no matching approval")
            state = "pending"
        if state != "approved" and not blocked and backing:
            r = max(backing, key=lambda r: r["at"])
            text = set_gate(text, gate, f"{{ state: approved, approved_by: {r['login']}, "
                                        f"approved_at: {r['at']}, doc_sha256: {current} }}")
            notes.append(f"{gate} approved by {r['login']}")
            state = "approved"
        blocked = blocked or state != "approved"
    for s in status["slices"]:
        nn = s["id"].zfill(2)
        signed = [r for r in approvals if (c := command(r["body"])) and c[0] == "sign-off"
                  and c[1].lstrip("0") == s["id"].lstrip("0")]
        signed = [r for r in signed if s["head_commit"] and is_ancestor(repo, s["head_commit"], r["commit"])
                  and blob_sha256(repo, r["commit"], f"{change}/slices/{nn}/review.md")]
        if s["state"] == "done" and not signed:
            text = set_slice_state(text, s["id"], "green")
            notes.append(f"slice {nn} reset to green: no matching sign-off")
        elif s["state"] == "green" and signed and not blocked:
            text = set_slice_state(text, s["id"], "done")
            notes.append(f"slice {nn} signed off by {max(signed, key=lambda r: r['at'])['login']}")
    if notes:
        text = replace(text, r"^waiting_since:.*$", "waiting_since: null")
    return text, notes


def triage_skips(repo, ref, status_path):
    """Gates skipped by the commit that created status.yaml on the branch's own line, which triage wrote."""
    first = run(repo, "git", "log", "--reverse", "--first-parent", "--diff-filter=A", "--format=%H",
                ref, "--", status_path).split()[:1]
    if not first:
        return set()
    try:
        gates = parse_status(run(repo, "git", "show", f"{first[0]}:{status_path}"))["gates"]
    except RuntimeError:
        return set()
    return {g for g, v in gates.items() if v.get("state") == "skipped" and g != "slices"}


def run_harness(cmd, cwd, timeout):
    """Run the harness in its own process group, so a timeout stops its tools too."""
    proc = subprocess.Popen(cmd, cwd=cwd, start_new_session=True)
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise


def pull_request(repo, branch):
    prs = json.loads(run(repo, "gh", "pr", "list", "--head", branch, "--state", "open",
                         "--json", "number,isCrossRepository"))
    prs = [p for p in prs if not p["isCrossRepository"]]
    if len(prs) != 1:
        raise RuntimeError(f"{len(prs)} open pull requests from {branch} in this repository; expected 1")
    n = prs[0]["number"]
    view = json.loads(run(repo, "gh", "pr", "view", str(n), "--json", "reviews,comments"))
    pages = json.loads(run(repo, "gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{n}/comments",
                           "--paginate", "--slurp"))
    reviews = [{"login": r["author"]["login"], "state": r["state"], "body": r.get("body") or "",
                "commit": (r.get("commit") or {}).get("oid"), "at": r["submittedAt"]} for r in view["reviews"]]
    notes = [{"login": c["author"]["login"], "body": c.get("body") or "", "at": c["createdAt"]}
             for c in view["comments"]]
    notes += [{"login": c["user"]["login"], "body": f"On {c['path']}: {c.get('body') or ''}", "at": c["created_at"]}
              for page in pages for c in page]
    return reviews, notes


def pass_change(repo, branch, status_path, allowed, harness, prompt, timeout):
    ref = f"origin/{branch}"
    text = run(repo, "git", "show", f"{ref}:{status_path}")
    status = parse_status(text)
    if (status["scalars"].get("mode") != "headless" or status["branch"] != branch
            or status["scalars"].get("reconciled") == "true"):
        return
    change = str(Path(status_path).parent)
    slug = Path(change).name
    reviews, notes = pull_request(repo, branch)
    approvals = [r for r in reviews if r["state"] == "APPROVED" and r["login"].lower() in allowed and r["commit"]]
    may_skip = triage_skips(repo, ref, status_path)
    text, recorded = verify(repo, ref, change, text, approvals, may_skip)
    if recorded and verify(repo, ref, change, text, approvals, may_skip)[1]:
        raise RuntimeError("status.yaml has duplicate or malformed gate or slice lines; fix it by hand")
    skill = next_skill(parse_status(text))
    waiting = parse_status(text)["scalars"].get("waiting_since")
    replies = []
    if waiting:
        replies = [n for n in notes if n["login"].lower() in allowed and n["at"] > waiting]
        replies += [{"login": r["login"], "body": r["body"], "at": r["at"]} for r in reviews
                    if r["login"].lower() in allowed and r["body"].strip() and not command(r["body"])
                    and r["at"] > waiting]
    if not recorded and (skill is None or (waiting and not replies)):
        return
    if run(repo, "git", "status", "--porcelain").strip():
        raise RuntimeError("the clone has uncommitted changes; the runner needs a clean, dedicated clone")
    run(repo, "git", "checkout", "-B", branch, ref)
    if recorded:
        (repo / status_path).write_text(text)
        try:
            run(repo, "git", "add", status_path)
            run(repo, "git", "commit", "-m", f"chore(factory): runner: {'; '.join(recorded)}")
            run(repo, "git", "push", "origin", f"HEAD:{branch}")
        except RuntimeError:
            run(repo, "git", "reset", "-q", "--hard", ref)
            raise
        print(f"{slug}: {'; '.join(recorded)}")
    if skill is None:
        return
    message = prompt.format(skill=skill, slug=slug)
    if replies:
        body = "\n\n".join(f"{r['login']} ({r['at']}):\n{r['body']}" for r in sorted(replies, key=lambda r: r["at"]))
        body = body.encode()[-MAX_REPLY_BYTES:].decode(errors="ignore")
        message += "\n\nReplies from the pull request, by approvers:\n" + body
    try:
        code = run_harness([*shlex.split(harness), message], repo, timeout)
        if code != 0:
            print(f"{slug}: {skill} exited with {code}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"{slug}: {skill} timed out after {timeout} s", file=sys.stderr)
    if run(repo, "git", "status", "--porcelain").strip():
        raise RuntimeError(f"{skill} left uncommitted changes; the next pass waits until the clone is clean")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path, help="a clean clone dedicated to the runner")
    parser.add_argument("--approvers", required=True, help="comma-separated GitHub logins whose reviews approve")
    parser.add_argument("--harness", default="claude -p")
    parser.add_argument("--prompt", default="/{skill} {slug}", help="prompt template for the harness")
    parser.add_argument("--timeout", type=int, default=3600, help="seconds per skill run")
    args = parser.parse_args()
    repo = args.repo.resolve()
    approvers = {a.strip().lower() for a in args.approvers.split(",") if a.strip()}
    approvers.discard(run(repo, "gh", "api", "user", "--jq", ".login").strip().lower())  # the harness's own login
    with open(repo / ".git" / "factory-runner.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("another runner pass is still going", file=sys.stderr)
            return 0
        start = run(repo, "git", "rev-parse", "--abbrev-ref", "HEAD").strip()
        run(repo, "git", "fetch", "--prune", "origin")
        refs = run(repo, "git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/factory/").split()
        for ref in refs:
            branch = ref.removeprefix("origin/")
            if not BRANCH.match(branch):
                continue
            names = run(repo, "git", "ls-tree", "-r", "--name-only", ref, ".factory/changes/").split()
            for status_path in [n for n in names if re.fullmatch(r"\.factory/changes/[^/]+/status\.yaml", n)]:
                try:
                    pass_change(repo, branch, status_path, approvers, args.harness, args.prompt, args.timeout)
                except Exception as e:  # noqa: BLE001 - one change's failure must not stop the others
                    print(f"{branch}: {type(e).__name__}: {e}", file=sys.stderr)
        if start != "HEAD" and not run(repo, "git", "status", "--porcelain").strip():
            run(repo, "git", "checkout", start)
    return 0


if __name__ == "__main__":
    sys.exit(main())
