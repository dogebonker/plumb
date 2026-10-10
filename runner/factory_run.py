#!/usr/bin/env python3
"""Headless factory runner: one pass over a repository's factory changes.

For each change in headless mode it reads the change's pull request, records
the approvals that approvers gave there (the agent never approves), and runs
the next factory skill through a headless harness. Run it from cron or CI;
each pass does at most one skill run per change.

    python3 runner/factory_run.py <repo> [--harness "claude -p"]

Commands, as the first line of a pull-request review by an approver:
    approve <product|architecture|interface|slices>
    sign off slice <NN>
Any other review or comment text from an approver after the change started
waiting is passed to the next skill run as the approvers' reply.

ponytail: edits status.yaml with line regexes, matching the one-line flow maps
the factory skills write; a YAML library if the format grows.
"""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

GATES = ["product", "architecture", "interface", "slices"]
DOCS = {"product": "01-product.md", "architecture": "02-architecture.md",
        "interface": "03-interface.md", "slices": "04-slices.md"}


def run(cwd, *cmd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}: {r.stderr.strip()}")
    return r.stdout


def scalar(text, key):
    m = re.search(rf"^{key}:\s*\"?([^\"#\n]*?)\"?\s*(#.*)?$", text, re.MULTILINE)
    return m.group(1).strip() if m and m.group(1).strip() not in ("", "null") else None


def gate_state(text, gate):
    m = re.search(rf"^\s+{gate}:\s*\{{[^}}]*\bstate:\s*(\w+)", text, re.MULTILINE)
    return m.group(1) if m else None


def slices(text):
    block = re.search(r"^slices:(.*?)(?=^\w)", text + "\nend:", re.MULTILINE | re.DOTALL)
    found = []
    for line in (block.group(1) if block else "").splitlines():
        m = re.match(r"^\s*-\s*\{(.*)\}", line)
        if m:
            sid = re.search(r"\bid:\s*(\w+)", m.group(1))
            state = re.search(r"\bstate:\s*(\w+)", m.group(1))
            head = re.search(r"\bhead_commit:\s*(\w+)", m.group(1))
            found.append({"id": sid.group(1) if sid else "?", "state": state.group(1) if state else None,
                          "head_commit": head.group(1) if head and head.group(1) != "null" else None})
    return found


def set_scalar(text, key, value):
    return re.sub(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.MULTILINE)


def set_gate(text, gate, approved_by, approved_at, digest):
    line = f"  {gate}: {{ state: approved, approved_by: {approved_by}, approved_at: {approved_at}, doc_sha256: {digest} }}"
    return re.sub(rf"^\s+{gate}:\s*\{{.*\}}\s*$", line, text, count=1, flags=re.MULTILINE)


def set_slice_done(text, sid):
    def done(m):
        return re.sub(r"\bstate:\s*\w+", "state: done", m.group(0), count=1)
    return re.sub(rf"^\s*-\s*\{{[^}}]*\bid:\s*0*{int(sid)}\b[^}}]*\}}", done, text, count=1, flags=re.MULTILINE)


def next_skill(text):
    """The skill a change needs next, or None when it is finished."""
    if scalar(text, "reconciled") == "true":
        return None
    for gate in GATES:
        if gate_state(text, gate) not in ("approved", "skipped"):
            return f"factory-{gate}"
    found = slices(text)
    for s in found:
        if s["state"] != "done":
            return "factory-review" if s["state"] == "green" else "factory-build"
    return "factory-reconcile" if found else None


def command(body):
    first = (body or "").strip().splitlines()[0].strip().lower() if (body or "").strip() else ""
    m = re.fullmatch(r"approve (product|architecture|interface|slices)", first)
    if m:
        return ("approve", m.group(1))
    m = re.fullmatch(r"sign off slice (\d+)", first)
    if m:
        return ("sign-off", m.group(1))
    return None


def doc_hash_at(repo, commit, path):
    try:
        return hashlib.sha256(run(repo, "git", "show", f"{commit}:{path}").encode()).hexdigest()
    except RuntimeError:
        return None


def record(repo, change, text, reviews):
    """Apply approver commands from reviews. Returns the new status text and what was recorded."""
    rel = change.relative_to(repo).as_posix()
    recorded = []
    for rv in sorted(reviews, key=lambda r: r["submitted_at"]):
        cmd = command(rv["body"])
        if not cmd:
            continue
        kind, arg = cmd
        if kind == "approve" and gate_state(text, arg) == "pending" and next_skill(text) == f"factory-{arg}":
            current = change / DOCS[arg]
            digest = hashlib.sha256(current.read_bytes()).hexdigest() if current.exists() else None
            if digest and doc_hash_at(repo, rv["commit_id"], f"{rel}/{DOCS[arg]}") == digest:
                text = set_gate(text, arg, rv["login"], rv["submitted_at"], digest)
                recorded.append(f"{arg} approved by {rv['login']}")
        if kind == "sign-off":
            match = [s for s in slices(text) if s["id"].lstrip("0") == arg.lstrip("0") and s["state"] == "green"]
            review_md = change / "slices" / f"{int(arg):02d}" / "review.md"
            if match and match[0]["head_commit"] and review_md.exists():
                try:
                    run(repo, "git", "merge-base", "--is-ancestor", match[0]["head_commit"], rv["commit_id"])
                except RuntimeError:
                    continue
                text = set_slice_done(text, arg)
                review_md.write_text(re.sub(r"(## Sign-off\n).*", rf"\g<1>{rv['login']}, {rv['submitted_at']}",
                                            review_md.read_text(), count=1))
                recorded.append(f"slice {arg} signed off by {rv['login']}")
    return text, recorded


def pull_request(repo, branch):
    prs = json.loads(run(repo, "gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number"))
    if not prs:
        return None, [], []
    n = prs[0]["number"]
    raw = json.loads(run(repo, "gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{n}/reviews", "--paginate"))
    reviews = [{"login": r["user"]["login"], "body": r.get("body") or "", "commit_id": r["commit_id"],
                "submitted_at": r["submitted_at"]} for r in raw if r.get("submitted_at")]
    raw = json.loads(run(repo, "gh", "api", f"repos/{{owner}}/{{repo}}/issues/{n}/comments", "--paginate"))
    comments = [{"login": c["user"]["login"], "body": c.get("body") or "", "at": c["created_at"]} for c in raw]
    return n, reviews, comments


def approvers(text):
    raw = scalar(text, "approvers") or ""
    return {a.strip() for a in raw.strip("[]").split(",") if a.strip()}


def pass_change(repo, status_file, harness):
    text = status_file.read_text()
    if scalar(text, "mode") != "headless" or next_skill(text) is None:
        return
    branch = scalar(text, "branch")
    run(repo, "git", "checkout", branch)
    run(repo, "git", "pull", "--ff-only")
    text = status_file.read_text()
    number, reviews, comments = pull_request(repo, branch)
    if number is None:
        print(f"{status_file.parent.name}: no open pull request for {branch}; open one first", file=sys.stderr)
        return
    allowed = approvers(text)
    reviews = [r for r in reviews if r["login"] in allowed]
    text, recorded = record(repo, status_file.parent, text, reviews)
    waiting = scalar(text, "waiting_since")
    replies = [c for c in comments if c["login"] in allowed and (not waiting or c["at"] > waiting)]
    replies += [{"login": r["login"], "body": r["body"], "at": r["submitted_at"]} for r in reviews
                if not command(r["body"]) and r["body"].strip() and (not waiting or r["submitted_at"] > waiting)]
    if recorded:
        status_file.write_text(text)
        run(repo, "git", "add", status_file.parent.relative_to(repo).as_posix())
        run(repo, "git", "commit", "-m", f"chore(factory): runner records {'; '.join(recorded)}")
        run(repo, "git", "push")
    if waiting and not recorded and not replies:
        return
    skill = next_skill(text)
    if skill is None:
        return
    status_file.write_text(set_scalar(text, "waiting_since", "null"))
    prompt = f"/{skill} {status_file.parent.name}"
    if replies:
        prompt += "\n\nReplies from the pull request, by approvers:\n" + "\n\n".join(
            f"{r['login']} ({r['at']}):\n{r['body']}" for r in sorted(replies, key=lambda r: r["at"]))
    subprocess.run([*shlex.split(harness), prompt], cwd=repo, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("--harness", default="claude -p")
    args = parser.parse_args()
    repo = args.repo.resolve()
    for status_file in sorted((repo / ".factory" / "changes").glob("*/status.yaml")):
        try:
            pass_change(repo, status_file, args.harness)
        except RuntimeError as e:
            print(f"{status_file.parent.name}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
