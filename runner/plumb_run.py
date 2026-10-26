#!/usr/bin/env python3
"""Headless Plumb runner: one pass over a repository's headless Plumb changes.

Each change lives on a `plumb/<slug>` branch with one pull request. Per pass
and per change, the runner re-derives every approval from approvers' pull-request
reviews (an approval written into status.yaml any other way is undone), then
runs the next Plumb skill through a headless harness. Run it from cron or CI
in a dedicated clone:

    python3 runner/plumb_run.py <clone> --approvers alice,bob

Changes are read from .plumb/changes/*/status.yaml. The harness's clone
reads the kit and skills from the framework cache, so the operator of a runner host
runs bin/plumb-install <commit> for each commit a change's .plumb/plumb.lock
names, into ~/.plumb/framework/<commit>/, and links its skills user-level:
project links are untracked, so the clone has none. The operator also runs that commit's
bin/plumb-packs-fetch on its own kit/packs.lock.yaml, so the packs it pins are in
~/.plumb/packs/<name>@<hash>/; never on a branch's lock, which the harness can
write. The runner skips a change whose lock pins packs other than its framework's
kit/packs.lock.yaml. The runner never installs or fetches. The lock
comes from the branch, which the harness controls, so it only selects among the commits
installed here: the runner skips a change whose lock is missing, names a dev_path, or
names anything but a full 40-hex commit installed on this host (kit/, skills/ and
hooks/ present), and reports a branch that still keeps its changes in .factory/ or .software-factory/.

Approver reviews in state APPROVED, first line:
    start                                          the runner may work on this change
    approve <product|architecture|interface|slices>
    sign off slice <NN>
A later CHANGES_REQUESTED review by the same approver revokes their earlier ones.
The harness runs only on a branch head the runner or harness left, or one an
approver approved: anyone else's push waits for an approver's review. It runs
in a throwaway clone, so nothing it writes reaches the runner's own clone.
While a change waits for its approvers, their other comments and reviews after
its question are passed to the next skill run as their replies.

Reads status.yaml with the Plumb hook's parser, which relies on the one-line
flow maps the skills write; a YAML library if that format grows.
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from plumb_gate import GATES, field, parse_status

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "kit"))
from usage import read_events, receipt

BRANCH = re.compile(r"^(?:plumb|factory)/[A-Za-z0-9._/-]+$")  # factory/: changes started before the rename
SHA = re.compile(r"^[0-9a-f]{40}$")
PACK_ENTRY = re.compile(r"\s+([^\s:#]+):\s*\{([^{}]*)\}\s*(#.*)?")  # the same entry form as bin/plumb-packs-fetch
GIT_SAFE = ("-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false")
HARNESS = "claude -p --model claude-opus-5-5 --setting-sources user --strict-mcp-config --output-format stream-json --verbose"
GIT_TIMEOUT = 300
MAX_REPLY_BYTES = 100_000
PENDING = "{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }"
FRAMEWORK = Path.home() / ".plumb" / "framework"
NOT_PLANNING = {".plumb/plumb.lock", ".plumb/principles.md"}


def write_json(path, value):
    """Keep the previous trusted checkpoint intact on interruption."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run(cwd, *cmd, timeout=GIT_TIMEOUT, binary=False):
    if cmd[0] == "git":
        cmd = ("git", *GIT_SAFE, *cmd[1:])  # hooks or fsmonitor a harness left in .git never run
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


def has_stamp(repo, ref, path):
    """A design file Plumb made: it carries the stamp, unlike an architecture DESIGN.md."""
    try:
        return "factory:design-schema" in run(repo, "git", "show", f"{ref}:{path}")
    except RuntimeError:
        return False


def is_ancestor(repo, older, newer):
    try:
        run(repo, "git", "merge-base", "--is-ancestor", older, newer)
        return True
    except RuntimeError:
        return False


def command(body):
    lines = body.strip().splitlines()
    first = lines[0].strip().lower() if lines else ""
    if first == "start":
        return ("start", None)
    m = re.fullmatch(r"approve (product|architecture|interface|slices)", first)
    if m:
        return ("approve", m.group(1))
    m = re.fullmatch(r"sign off slice (\d+)", first)
    return ("sign-off", m.group(1)) if m else None


def next_skill(status, has_design=True):
    """The skill a change needs next, or None when it is finished."""
    if status["scalars"].get("reconciled") == "true":
        return None
    if status["scalars"].get("ui") == "true" and not has_design:
        return "plumb-ui-ux"
    for gate, _ in GATES:
        if status["gates"].get(gate, {}).get("state") not in ("approved", "skipped"):
            return f"plumb-{gate}"
    for s in status["slices"]:
        if s["state"] != "done":
            return "plumb-review" if s["state"] == "green" else "plumb-build"
    return "plumb-reconcile" if status["slices"] else None


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


def only_plumb(repo, older, newer):
    changed = run(repo, "git", "diff", "--no-renames", "--name-only", older, newer).split()
    # .factory/ and .software-factory/ are pre-migration planning folders: deleting them in a migration commit is not source.
    return all((path.startswith(".plumb/") and path not in NOT_PLANNING) or path.startswith((".factory/", ".software-factory/"))
               for path in changed)


def missing_framework(repo, ref, change):
    """Why this host cannot run the framework the change's plumb.lock names at ref, or None when it can."""
    lock = f"{Path(change).parent.parent}/plumb.lock"
    try:
        lines = re.findall(r"^framework:(.*)$", run(repo, "git", "show", f"{ref}:{lock}"), re.MULTILINE)
    except RuntimeError:
        return f"no {lock}; run /plumb-init in the project"
    if len(lines) > 1:
        return f"{lock} has {len(lines)} framework lines; expected 1"
    # The lock comes from the branch, which the harness controls: it only selects among commits installed here.
    commit, dev_path = (field(lines[0], "commit"), field(lines[0], "dev_path")) if lines else (None, None)
    if dev_path:
        return f"{lock} names a dev_path; headless runs only a pinned framework commit"
    if not commit or not SHA.fullmatch(commit):
        return f"{lock} names no full 40-hex framework commit"
    if not all((FRAMEWORK / commit / part).is_dir() for part in ("kit", "skills", "hooks")):  # as bin/plumb-install
        return f"framework {commit[:12]} from {lock} is not installed in {FRAMEWORK}"
    # Pack pins steer what agents read as rules, so the branch may not choose them: they must equal the
    # approved pins of the installed framework, which the operator fetched from that framework's own lock.
    pinned = pack_pins(run(repo, "git", "show", f"{ref}:{lock}"))
    if pinned is None:
        return f"{lock} has a malformed packs: block; run /plumb-upgrade"
    approved_file = FRAMEWORK / commit / "kit" / "packs.lock.yaml"
    approved = pack_pins(approved_file.read_text()) if approved_file.is_file() else {}
    if pinned != approved:
        return f"{lock} pins packs other than framework {commit[:12]}'s kit/packs.lock.yaml; run /plumb-upgrade"
    return None


def pack_pins(text):
    """{name: (source, path, hash)} from a lock's packs: block, read as strictly as bin/plumb-packs-fetch reads
    it, so the runner and the fetch never disagree on what a lock pins; None when the block is malformed."""
    pins, inside, blocks = {}, False, 0
    for line in text.splitlines():
        if re.match(r"^packs\s*:", line):
            blocks += 1
            if blocks > 1 or not re.fullmatch(r"packs:\s*(\{\})?\s*(#.*)?", line):
                return None
            inside = True
        elif inside and re.match(r"^\S", line):
            inside = False
        elif inside and line.strip() and not line.lstrip().startswith("#"):
            entry = PACK_ENTRY.fullmatch(line)
            if not entry or entry[1] in pins:
                return None
            pins[entry[1]] = tuple(field(entry[2], key) for key in ("source", "path", "hash"))
    return pins


def unmigrated(repo, ref):
    """True when ref's tree still keeps its changes in .factory/ or .software-factory/ and has no .plumb/changes."""
    def has(path):
        return run(repo, "git", "ls-tree", ref, "--", path).split()[1:2] == ["tree"]
    return (has(".factory/changes") or has(".software-factory/changes")) and not has(".plumb/changes")


def home_problem():
    home = os.environ.get("HOME", "")
    if not os.path.isabs(home) or Path(home).resolve() == Path("/"):
        return f"HOME is {home!r}; the framework cache needs an absolute HOME other than /"
    return None


def verify(repo, ref, change, text, approvals, may_skip):
    """Re-derive gate approvals and slice sign-offs from approval reviews.

    `change` is the change folder relative to the repository; `approvals` are
    APPROVED reviews by approvers; `may_skip` are the gates an approver's start
    review covered as skipped. Returns the corrected status text and notes.
    """
    head = run(repo, "git", "rev-parse", ref).strip()
    status = parse_status(text)
    notes, blocked, approved_at, approval_commit = [], False, {}, {}
    chain = {}
    for gate, doc in GATES:
        state = status["gates"].get(gate, {}).get("state")
        if state == "skipped" and gate in may_skip:
            continue
        if state == "skipped":
            text = set_gate(text, gate, PENDING)
            notes.append(f"{gate} reset to pending: triage did not skip it")
            state = "pending"
        current = blob_sha256(repo, ref, f"{change}/{doc}")
        chain[doc] = current
        # Each review covers the current upstream document snapshot, even when reviews arrive out of order.
        backing = [r for r in approvals if command(r["body"]) == ("approve", gate)
                   and is_ancestor(repo, r["commit"], head)
                   and all(digest and blob_sha256(repo, r["commit"], f"{change}/{path}") == digest
                           for path, digest in chain.items())]
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
        if state == "approved":
            approved_at[gate] = max(r["at"] for r in backing)
            approval_commit[gate] = max(backing, key=lambda r: r["at"])["commit"]
        blocked = blocked or state != "approved"
    slices_at = approved_at.get("slices")  # from the reviews, never from status.yaml
    # A send-back to the slices gate (reconcile's acceptance step) must not undo earlier sign-offs. A sign-off
    # from before the current slices approval still counts for a done slice, but only when the approved commit's
    # status.yaml already showed that slice done at the same head_commit: the approver saw it kept, so an agent
    # cannot revive a rewound slice by editing status.yaml. While the slices gate is not approved, nothing can
    # run past it, so earlier sign-offs keep their slices done until the next approval decides.
    first_slices_at = min((r["at"] for r in approvals if command(r["body"]) == ("approve", "slices")), default=None)
    kept = set()
    if "slices" in approval_commit:
        try:
            at_approval = parse_status(run(repo, "git", "show", f"{approval_commit['slices']}:{change}/status.yaml"))
            kept = {(x["id"].lstrip("0"), x["head_commit"]) for x in at_approval["slices"] if x["state"] == "done"}
        except RuntimeError:
            print(f"{change}: no status.yaml at the approved slices commit; earlier sign-offs are not kept",
                  file=sys.stderr)
    for s in status["slices"]:
        nn = s["id"].zfill(2)
        signed = [r for r in approvals if (c := command(r["body"])) and c[0] == "sign-off"
                  and c[1].lstrip("0") == s["id"].lstrip("0")]
        # A sign-off covers the slice's code exactly: head_commit is a full sha, only .plumb/ changed
        # between it and the reviewed commit, and the review came after a slices gate approval.
        signed = [r for r in signed if s["head_commit"] and SHA.match(s["head_commit"])
                  and first_slices_at and r["at"] > first_slices_at
                  and is_ancestor(repo, s["head_commit"], r["commit"]) and is_ancestor(repo, r["commit"], ref)
                  and only_plumb(repo, s["head_commit"], r["commit"])
                  and blob_sha256(repo, r["commit"], f"{change}/slices/{nn}/review.md")]
        if slices_at and (s["id"].lstrip("0"), s["head_commit"]) not in kept:
            signed = [r for r in signed if r["at"] > slices_at]
        if s["state"] == "done" and not signed:
            text = set_slice_state(text, s["id"], "green")
            notes.append(f"slice {nn} reset to green: no matching sign-off")
        elif s["state"] == "green" and not blocked and [r for r in signed if r["commit"] == head
                                                         and r["at"] > slices_at]:
            text = set_slice_state(text, s["id"], "done")
            notes.append(f"slice {nn} signed off by {max(signed, key=lambda r: r['at'])['login']}")
    if notes:
        text = replace(text, r"^waiting_since:.*$", "waiting_since: null")
    return text, notes


def triage_skips(repo, ref, status_path, starts):
    """Gates skipped both by the commit that created status.yaml and at an approver's start review of it."""
    first = run(repo, "git", "log", "--reverse", "--first-parent", "--diff-filter=A", "--format=%H",
                ref, "--", status_path).split()[:1]

    def skipped_at(commit):
        try:
            gates = parse_status(run(repo, "git", "show", f"{commit}:{status_path}"))["gates"]
        except RuntimeError:
            return set()
        return {g for g, v in gates.items() if v.get("state") == "skipped" and g != "slices"}

    if not first:
        return set()
    covered = [r["commit"] for r in starts if is_ancestor(repo, first[0], r["commit"])]
    return set().union(*(skipped_at(first[0]) & skipped_at(c) for c in covered)) if covered else set()


def run_harness(cmd, cwd, timeout):
    """Run the harness in its own process group, so a timeout stops its tools too."""
    observed = Path(cmd[0]).name == "claude" and "stream-json" in cmd
    stream = (Path(cwd).parent / "usage-stream.jsonl").open("ab") if observed else None
    environment = {**os.environ, "PLUMB_RUNNER_MANAGED": "1"}
    if Path(cmd[0]).name == 'claude' and '--model' in cmd and cmd[cmd.index('--model') + 1] == 'claude-opus-5-5':
        environment.update(CLAUDE_CODE_SUBAGENT_MODEL='claude-opus-5-5',
                           CLAUDE_CODE_SUBAGENT_MODEL_FORCE='1', CLAUDE_CODE_DISABLE_BACKGROUND_TASKS='1')
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, start_new_session=True, stdout=stream,
                                env=environment)
        try:
            return proc.wait(timeout=timeout)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise
    finally:
        if stream:
            stream.close()


def created_commits(clone):
    """Commits the harness created in its clone, read from the reflog file without running git there."""
    log = clone / ".git" / "logs" / "HEAD"
    made = ("commit", "rebase (pick)", "rebase -i (pick)", "rebase (continue)", "revert")
    created = set()
    for line in (log.read_text(errors="replace").splitlines() if log.exists() else []):
        head, _, message = line.partition("\t")
        parts = head.split()
        if len(parts) > 1 and message.startswith(made):
            created.add(parts[1])
    return created


def new_head_trusted(repo, before, after, created):
    """A head the harness left: the old head or a fast-forward of it made only of commits the harness created."""
    if after == before:
        return True
    return is_ancestor(repo, before, after) and all(
        c in created for c in run(repo, "git", "rev-list", f"{before}..{after}").split())


def harness_pass(repo, branch, head, cmd, setup, timeout):
    """Run the harness in a throwaway clone of the trusted head. Returns its exit code and created commits."""
    url = run(repo, "git", "remote", "get-url", "origin").strip()
    root = Path(tempfile.mkdtemp(prefix="plumb-harness-"))
    work = root / "work"
    work.mkdir()
    code = None
    outcome = "setup-or-clone-failure"
    ledger = repo / ".git" / "plumb-usage" / "usage.jsonl"
    skills = re.findall(r"\bplumb-[a-z-]+\b", cmd[-1]) if cmd else []
    skill = skills[0] if skills else "unknown"
    try:
        run(work, "git", "clone", "-q", "--branch", branch, url, ".")
        if run(work, "git", "rev-parse", "HEAD").strip() != head:
            raise RuntimeError("the branch moved after its head was checked; the next pass looks again")
        # Harness skills commit locally; only a successful runner publishes their trusted commits.
        run(work, "git", "config", "remote.origin.pushurl", str(root / "publication-disabled"))
        try:
            code = 0
            if setup:
                receipt(ledger, branch, "runner-setup", [], root.name + "-setup")
                try:
                    code = run_harness(shlex.split(setup), work, timeout)
                finally:
                    if (root / "usage-stream.jsonl").exists():
                        (root / "usage-stream.jsonl").rename(root / "setup-usage-stream.jsonl")
            if code == 0:
                receipt(ledger, branch, skill, [], root.name)
                code = run_harness(cmd, work, timeout)
        except subprocess.TimeoutExpired:
            code = None
        if code == 0:
            if run(work, "git", "status", "--porcelain").strip():
                raise RuntimeError("successful harness left uncommitted work; retained for recovery")
            after = run(work, "git", "rev-parse", "HEAD").strip()
            run(repo, "git", "fetch", "--no-tags", str(work), after)
            if not new_head_trusted(repo, head, after, created_commits(work)):
                raise RuntimeError("harness head contains untrusted commits; retained without publishing")
            if after != head:
                run(repo, "git", "push", f"--force-with-lease=refs/heads/{branch}:{head}", "origin",
                    f"{after}:refs/heads/{branch}")
        outcome = "success" if code == 0 else "timeout" if code is None else "nonzero"
        return code, created_commits(work)
    finally:
        try:
            # Receipts live outside the harness clone and survive success, failure and timeout.
            evidence = repo / ".git" / "plumb-usage" / root.name
            evidence.mkdir(parents=True, exist_ok=True)
            source = root / "usage-stream.jsonl"
            if source.exists():
                shutil.copyfile(source, evidence / source.name)
            receipt(ledger, branch, skill, read_events(source), root.name,
                    partial=outcome != "success", source=str(evidence / source.name))
            if setup:
                setup_source = root / "setup-usage-stream.jsonl"
                if setup_source.exists():
                    shutil.copyfile(setup_source, evidence / setup_source.name)
                receipt(ledger, branch,
                        "runner-setup", read_events(setup_source), root.name + "-setup",
                        partial=outcome != "success", source=str(evidence / setup_source.name))
        except (OSError, ValueError) as error:
            outcome = "usage-recording-failure"
            print(f"usage receipt failed; retaining harness evidence: {error}", file=sys.stderr)
        if outcome == "success":
            shutil.rmtree(root, ignore_errors=True)
        else:
            # Preserve the whole clone: commits, index, dirty and untracked files, including detached RED.
            (root / "checkpoint.json").write_text(json.dumps(
                {"branch": branch, "trusted_head": head, "outcome": outcome, "exit_code": code}, indent=2) + "\n")
            recovery = repo / ".git" / "plumb-recovery"
            recovery.mkdir(parents=True, exist_ok=True)
            destination = recovery / root.name
            shutil.move(str(root), destination)
            print(f"Plumb harness evidence retained at {destination}", file=sys.stderr)


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


def approver_reviews(reviews, allowed):
    """APPROVED reviews by approvers, minus those a later CHANGES_REQUESTED review by the same approver revokes."""
    mine = [r for r in reviews if r["login"].lower() in allowed]
    return [r for r in mine if r["state"] == "APPROVED" and r["commit"] and not any(
        o["login"].lower() == r["login"].lower() and o["state"] == "CHANGES_REQUESTED" and o["at"] > r["at"]
        for o in mine)]


def pass_change(repo, branch, status_path, allowed, harness, prompt, timeout, heads, setup=None):
    ref = f"origin/{branch}"
    text = run(repo, "git", "show", f"{ref}:{status_path}")
    status = parse_status(text)
    if (status["scalars"].get("mode") != "headless" or status["branch"] != branch
            or status["scalars"].get("reconciled") == "true"):
        return {"status": "idle"}
    change = str(Path(status_path).parent)
    slug = Path(change).name
    reviews, notes = pull_request(repo, branch)
    approvals = approver_reviews(reviews, allowed)
    starts = [r for r in approvals if command(r["body"]) == ("start", None)]
    if not starts:
        if any(r["login"].lower() in allowed for r in reviews):
            print(f"{slug}: no standing start review by an approver; a later CHANGES_REQUESTED revokes it",
                  file=sys.stderr)
        return {"status": "waiting", "reason": "no standing start review"}
    head = run(repo, "git", "rev-parse", ref).strip()
    trusted = heads.get(branch) == head or any(r["commit"] == head for r in approvals)
    may_skip = triage_skips(repo, ref, status_path, starts)
    text, recorded = verify(repo, ref, change, text, approvals, may_skip)
    if recorded and verify(repo, ref, change, text, approvals, may_skip)[1]:
        raise RuntimeError("status.yaml has duplicate or malformed gate or slice lines; fix it by hand")
    has_design = any(has_stamp(repo, ref, f) for f in ("DESIGN.md", ".plumb/system/design.md"))
    skill = next_skill(parse_status(text), has_design)
    waiting = parse_status(text)["scalars"].get("waiting_since")
    replies = []
    if waiting:
        replies = [n for n in notes if n["login"].lower() in allowed and n["at"] > waiting]
        replies += [{"login": r["login"], "body": r["body"], "at": r["at"]} for r in reviews
                    if r["login"].lower() in allowed and r["body"].strip() and not command(r["body"])
                    and r["at"] > waiting]
    if not recorded and (skill is None or (waiting and not replies) or not trusted):
        if skill and not trusted:
            print(f"{slug}: {head[:12]} was pushed by someone else; waiting for an approver to review it", file=sys.stderr)
        return {"status": "waiting" if skill else "idle", "reason": "awaiting authority/reply or no ready step"}
    if run(repo, "git", "status", "--porcelain").strip():
        raise RuntimeError("the clone has uncommitted changes; the runner needs a clean, dedicated clone")
    run(repo, "git", "checkout", "-B", branch, ref)
    if recorded:
        (repo / status_path).write_text(text)
        try:
            run(repo, "git", "add", status_path)
            run(repo, "git", "commit", "-m", f"chore(plumb): runner: {'; '.join(recorded)}")
            run(repo, "git", "push", "origin", f"HEAD:{branch}")
        except RuntimeError:
            run(repo, "git", "reset", "-q", "--hard", ref)
            raise
        print(f"{slug}: {'; '.join(recorded)}")
        head = run(repo, "git", "rev-parse", "HEAD").strip()
        if trusted:
            heads[branch] = head
    if skill is None or not trusted:
        return {"status": "progress" if recorded and trusted else "waiting"}
    missing = missing_framework(repo, ref, change)
    if missing:
        print(f"{slug}: {missing}; not running {skill}", file=sys.stderr)
        return {"status": "blocked", "reason": missing}
    message = prompt.format(skill=skill, slug=slug)
    message += "\nPLUMB_RUNNER_MANAGED=1: commit the step locally; do not push. The runner publishes only successful clean work."
    if replies:
        body = "\n\n".join(f"{r['login']} ({r['at']}):\n{r['body']}" for r in sorted(replies, key=lambda r: r["at"]))
        body = body.encode()[-MAX_REPLY_BYTES:].decode(errors="ignore")
        message += "\n\nReplies from the pull request, by approvers:\n" + body
    code, created = harness_pass(repo, branch, head, [*shlex.split(harness), message], setup, timeout)
    if code is None:
        print(f"{slug}: {skill} timed out after {timeout} s", file=sys.stderr)
    elif code != 0:
        print(f"{slug}: {skill} exited with {code}", file=sys.stderr)
    run(repo, "git", "fetch", "origin", branch)
    after = run(repo, "git", "rev-parse", ref).strip()
    if new_head_trusted(repo, head, after, created):
        heads[branch] = after
    else:
        print(f"{slug}: {after[:12]} holds commits the harness did not write; waiting for an approver", file=sys.stderr)

    state = "failed" if code != 0 else ("progress" if after != head and heads.get(branch) == after else "idle")
    return {"status": state, "skill": skill, "before": head, "after": after}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path, help="a clean clone dedicated to the runner")
    parser.add_argument("--approvers", required=True, help="comma-separated GitHub logins whose reviews approve")
    parser.add_argument("--harness", default=HARNESS, help="headless agent command; keep repository settings off")
    parser.add_argument("--prompt", default="/{skill} {slug}", help="prompt template for the harness")
    parser.add_argument("--timeout", type=int, default=3600, help="seconds per skill run")
    parser.add_argument("--setup", help="command run in the harness's fresh clone first, e.g. 'npm ci'")
    parser.add_argument("--report", type=Path, help="structured pass result outside the dedicated clone")
    args = parser.parse_args(argv)
    summary = {"status": "idle", "changes": []}
    def finish(code):
        if args.report:
            target = args.report.absolute()
            if target.is_symlink() or target.resolve().is_relative_to(args.repo.resolve()):
                raise ValueError("pass report must be a regular artifact outside the clone")
            write_json(target, summary)
        return code
    if home_problem():
        print(home_problem(), file=sys.stderr)
        summary.update(status="failed", reason=home_problem())
        return finish(1)
    repo = args.repo.resolve()
    approvers = {a.strip().lower() for a in args.approvers.split(",") if a.strip()}
    approvers.discard(run(repo, "gh", "api", "user", "--jq", ".login").strip().lower())  # the harness's own login
    with open(repo / ".git" / "plumb-runner.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("another runner pass is still going", file=sys.stderr)
            summary["status"] = "busy"
            return finish(0)
        start = run(repo, "git", "rev-parse", "--abbrev-ref", "HEAD").strip()
        run(repo, "git", "fetch", "--prune", "origin")
        heads_file = repo / ".git" / "plumb-runner-heads.json"
        heads = json.loads(heads_file.read_text()) if heads_file.exists() else {}
        refs = run(repo, "git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/plumb/", "refs/remotes/origin/factory/").split()
        for ref in refs:
            branch = ref.removeprefix("origin/")
            if not BRANCH.match(branch):
                continue
            if unmigrated(repo, ref):
                print(f"{branch}: still uses .factory/ or .software-factory/; run /plumb-init", file=sys.stderr)
                continue
            names = run(repo, "git", "ls-tree", "-r", "--name-only", ref, ".plumb/changes/").split()
            own = [n for n in names if re.fullmatch(r"\.plumb/changes/[^/]+/status\.yaml", n)
                   and parse_status(run(repo, "git", "show", f"{ref}:{n}"))["branch"] == branch]
            if len(own) > 1:
                print(f"{branch}: {len(own)} changes claim this branch; expected 1", file=sys.stderr)
                continue
            for status_path in own:
                try:
                    outcome = pass_change(repo, branch, status_path, approvers, args.harness, args.prompt, args.timeout,
                                          heads, args.setup)
                    summary["changes"].append(dict(outcome, branch=branch))
                    if outcome["status"] == "progress":
                        write_json(heads_file, heads)
                except Exception as e:  # noqa: BLE001 - one change's failure must not stop the others
                    print(f"{branch}: {type(e).__name__}: {e}", file=sys.stderr)
                    summary["changes"].append({"branch": branch, "status": "failed", "reason": str(e)})
        write_json(heads_file, heads)
        if start != "HEAD" and not run(repo, "git", "status", "--porcelain").strip():
            run(repo, "git", "checkout", start)
    states = {row["status"] for row in summary["changes"]}
    summary["status"] = next((x for x in ("failed", "progress", "blocked", "waiting") if x in states), "idle")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
