"""Shared by the stage cases: build a fixture repository with factory state, and run and parse unittest."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]
NAME, EMAIL = "Sam Rivera", "sam.rivera@example.com"
SESSION = "5f1c2e9a"
TEST_COMMAND = "python3 -m unittest discover -s . -p 'test*.py'"
LADDER = ("Simplification ladder: stop at the first rung that holds: does it need to exist; is it already in the "
          "codebase; does the standard library do it; does the platform; does an installed dependency; can it be "
          "one line; only then the minimum code.")
CONSTRAINTS = """# Constraints: notes

Standing requirements, promises and constraints of this project. Every change reads this file. Each row ends mapped to an enforcement.

| ID | Kind | Statement | Fit criterion | Source | Enforced by |
| --- | --- | --- | --- | --- | --- |
"""


def git(repo, *args, env=None):
    result = subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
                            capture_output=True, text=True, env=env, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def git_ok(repo, *args):
    try:
        return git(repo, *args)
    except RuntimeError:
        return None


def factory_commit():
    return git_ok(FACTORY, "rev-parse", "HEAD") or "unknown"


def new_repo(target, case_dir, exclude=()):
    """Copy the case's fixture into an empty target, minus `exclude`, and start a git repository on main."""
    target = Path(target)
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"{target} is not empty")
    shutil.copytree(Path(case_dir) / "fixture", target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", *exclude))
    git(target, "init", "-q", "-b", "main")
    git(target, "config", "user.name", NAME)
    git(target, "config", "user.email", EMAIL)
    return target


def commit(repo, message, *paths):
    """Stage paths and commit with a fixed author and a date one minute after the previous commit."""
    minute = int(git(repo, "rev-list", "--count", "--all"))
    date = f"2026-10-01T{9 + minute // 60:02d}:{minute % 60:02d}:00+00:00"
    env = {**os.environ, "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL, "GIT_AUTHOR_DATE": date,
           "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL, "GIT_COMMITTER_DATE": date}
    git(repo, "add", "--", *paths)
    git(repo, "commit", "-q", "-m", message, env=env)
    return git(repo, "rev-parse", "HEAD")


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def when(minute):
    return f"2026-10-01T10:{minute:02d}:00Z"


def value(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int) or re.fullmatch(r"[A-Za-z_][\w.-]*|[0-9a-f]{40}|[0-9a-f]{64}", v):
        return str(v)
    return json.dumps(v)


def flow(mapping):
    return "{ " + ", ".join(f"{key}: {value(v)}" for key, v in mapping.items()) + " }"


def approved(doc, minute):
    return {"state": "approved", "approved_by": NAME, "approved_at": when(minute), "doc_sha256": sha256(doc)}


def pending_gate():
    return {"state": "pending", "approved_by": None, "approved_at": None, "doc_sha256": None}


def event(minute, step, name, ref="-", detail=None):
    return {"at": when(minute), "step": step, "event": name, "ref": ref,
            "detail": detail or f"session {SESSION}, factory {factory_commit()[:7]}"}


def status_yaml(s):
    """Render status.yaml in the triage template's order, with gates, slices and history as one-line flow maps."""
    gates = "\n".join(f"  {gate + ':':<13} {flow(s['gates'][gate])}"
                      for gate in ("product", "architecture", "interface", "slices"))
    slices = "".join(f"\n  - {flow(item)}" for item in s["slices"]) or " []"
    history = "".join(f"\n  - {flow(item)}" for item in s["history"])
    sent_back = flow(s["sent_back"]) if s.get("sent_back") else "null"
    return f"""feature: {s['slug']}
task: {json.dumps(s['task'])}
track: {s['track']}
track_proposed: {s['track']}
factory_dir: committed
branch: factory/{s['slug']}
change_base_commit: {s['base']}
factory_commit: {factory_commit()}
test_command: {json.dumps(TEST_COMMAND)}
test_file_command: "python3 -m unittest {{file}}"
check_command: "python3 -m compileall -q ."
baseline_failures: []
gates:
{gates}
slices:{slices}
sent_back: {sent_back}
stubbing: false
ui: false
reconciled: false
mode: interactive
waiting_since: null
deviations: []
pond_sessions: []
notes_for_fresh_session: {json.dumps(s['notes'])}
history:{history}
"""


def lenses_yaml(profile, dev_command="none", dev_url=""):
    model = {"crud-service": "transaction-scripts", "domain-core": "rich"}[profile]
    return f"""profile: {profile}
domain_model: {model}
money: false
domain: none
modules:
  - path: .
    language: python
    language_version: "3.10"
    pack: python
    dev_command: {json.dumps(dev_command)}
    dev_url: {json.dumps(dev_url)}
    layers: []
    bdd: off
"""


def triage(repo, s, profile, dev_command="none", dev_url=""):
    """Branch off main, write .factory/system and the change's status.yaml, and commit as triage does."""
    git(repo, "checkout", "-q", "-b", f"factory/{s['slug']}")
    write(repo / ".factory/system/lenses.yaml", lenses_yaml(profile, dev_command, dev_url))
    write(repo / ".factory/system/constraints.md", CONSTRAINTS)
    save(repo, s)
    return commit(repo, f"chore(factory): triage {s['slug']}", ".factory")


def change_dir(repo, slug):
    return Path(repo) / ".factory/changes" / slug


def save(repo, s):
    write(change_dir(repo, s["slug"]) / "status.yaml", status_yaml(s))


def approve(repo, s, gate, doc_name, text, minute):
    """Write a gate document, approve it in status.yaml and commit as an interactive approval does."""
    doc = write(change_dir(repo, s["slug"]) / doc_name, text)
    s["gates"][gate] = approved(doc, minute)
    s["history"].append(event(minute - 1, f"factory-{gate}", "step_start"))
    save(repo, s)
    return commit(repo, f"chore(factory): {gate} {s['slug']}", ".factory")


def build_slice(repo, slug, stubs, tests, number="01"):
    """Commit a slice's red (its tests, with stubs for the fixture's implementation files) and then its green."""
    real = {path: (repo / path).read_text() for path in stubs}
    for path, text in stubs.items():
        write(repo / path, text)
    test = commit(repo, f"test({slug}): slice {number} red", *stubs, *tests)
    for path, text in real.items():
        write(repo / path, text)
    return test, commit(repo, f"feat({slug}): slice {number}", *stubs)


def read_status(workspace, slug):
    path = change_dir(workspace, slug) / "status.yaml"
    return path.read_text() if path.exists() else ""


def flow_field(text, key):
    match = re.search(rf"\b{key}:\s*[\"']?([^,\"'}}]*?)[\"']?\s*(?:,|}})", text)
    return match.group(1).strip() if match else None


def commit_by_subject(workspace, pattern):
    """Newest commit on HEAD whose subject matches the regex, or None."""
    for line in (git_ok(workspace, "log", "--format=%H %s", "HEAD") or "").splitlines():
        sha, _, subject = line.partition(" ")
        if re.search(pattern, subject):
            return sha
    return None


def export(workspace, sha, extra=None):
    """Extract the tree at sha into a new temp directory, then copy `extra` ({name in the tree: source path})."""
    tree = Path(tempfile.mkdtemp(prefix="factory-stage-"))
    archive = subprocess.run(["git", "-C", str(workspace), "archive", "--format=tar", sha],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
    for name, path in (extra or {}).items():
        shutil.copy2(path, tree / name)
    return tree


def parse_unittest(text):
    """Map each test id in `unittest -v` output to (outcome, error kind); kind is the exception name, or None."""
    results = {}

    def test_id(name, owner):
        return owner if owner.endswith("." + name) else f"{owner}.{name}"

    for name, owner, outcome in re.findall(
            r"^(\w+) \(([\w.]+)\)[^\n]*?(?:\n[^\n]*?)? \.\.\. (ok|FAIL|ERROR|skipped|expected failure|unexpected success)",
            text, re.M):
        results[test_id(name, owner)] = (outcome, None)
    for block in re.split(r"^={50,}$", text, flags=re.M)[1:]:
        header = re.match(r"\s*(FAIL|ERROR): (\w+) \(([\w.]+)\)", block)
        if not header:
            continue
        trace = re.split(r"^-{50,}$", block, flags=re.M)
        lines = [line for line in (trace[1] if len(trace) > 1 else "").splitlines() if line.strip()]
        kind = lines[-1].split(":")[0].strip().split(".")[-1] if lines else None
        results[test_id(header.group(2), header.group(3))] = (header.group(1), kind)
    return results


def run_unittest(tree, *args):
    try:
        result = subprocess.run([sys.executable, "-m", "unittest", *args, "-v"], cwd=tree,
                                capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired:
        return {"<timeout>": ("ERROR", "Timeout")}
    return parse_unittest(result.stderr)


def tests_at(workspace, sha, extra=None, args=("discover", "-s", ".", "-p", "test*.py")):
    tree = export(workspace, sha, extra)
    try:
        return run_unittest(tree, *args)
    finally:
        shutil.rmtree(tree)


def passed(results, name):
    return any(test.endswith("." + name) and outcome == "ok" for test, (outcome, _) in results.items())


def report(scores, required):
    scores = {key: round(float(v), 3) for key, v in scores.items()}
    scores["pass"] = all(scores[key] == 1 for key in required)
    print(json.dumps(scores))


def workspace_arg():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <workspace>")
    return Path(sys.argv[1]).resolve()


def review_md_ok(path):
    """review.md follows factory-review's template (its headings and a Range line) and its Sign-off is filled."""
    if not path.exists():
        return 0
    text = path.read_text()
    needed = [r"^# Review: milestone", r"^Range: \S+\.\.\S+", r"^## Phase 1", r"^## Polish",
              r"^## Lens reviewers", r"^## Follow-ups", r"^## Sign-off[ \t]*\n+[ \t]*[^<\s#]"]
    return int(all(re.search(pattern, text, re.M) for pattern in needed))


def review_range(path):
    match = re.search(r"^Range: (\w+)\.\.(\w+)", path.read_text(), re.M) if path.exists() else None
    return match.groups() if match else (None, None)


def same_commit(full, given):
    return bool(full and given and len(given) >= 7 and full.startswith(given))


def findings(text):
    """(severity, outcome, line) for each finding in review.md's Polish and Lens reviewers sections.

    A finding is a line `[tag] severity path: finding -> outcome`, numbered, bulleted or bolded or not, or a
    challenge card table with a Severity row and a Response row.
    """
    found = []
    for body in re.findall(r"^## (?:Polish|Lens reviewers)[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        for block in re.split(r"\n[ \t]*\n", body):
            card = re.search(r"\|\s*Severity\s*\|\s*\**\s*(block|fix|note)\b", block, re.I)
            if card:
                response = re.search(r"\|\s*Response\s*\|\s*\**\s*([\w-]+)", block)
                found.append((card.group(1).lower(), response.group(1).lower() if response else "", block))
                continue
            for line in block.splitlines():
                clean = re.sub(r"[*`]", "", line).strip().lstrip("-+ ").strip()
                match = re.match(r"(?:\d+[.)]\s*)?(?:\[[^\]]+\]\s*)?(block|fix|note)\b(.*:.*)$", clean, re.I)
                if match:
                    outcome = re.search(r"->\s*([\w-]+)\W*$", match.group(2))
                    found.append((match.group(1).lower(), outcome.group(1).lower() if outcome else "", clean))
    return found


def active_block_or_fix(text):
    """Findings of severity block or fix that were not dropped."""
    return [line for severity, outcome, line in findings(text) if severity in ("block", "fix") and outcome != "dropped"]


def slice_field(status, key, number="01"):
    line = re.search(rf"^\s*-\s*\{{.*\bid: \"?{number}\"?.*\}}", status, re.M)
    return flow_field(line.group(0), key) if line else None
