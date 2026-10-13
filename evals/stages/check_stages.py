"""Self-check the stage cases without a model or agent.

For each case: set it up in a temp dir, check that the hook and the chain check accept the state and that its
public tests pass, then grade the untouched setup (nop: must not pass), the oracle's end state (must pass) and each
oracle/wrong_*.py end state (must not pass). case.json's stop_when must hold for the oracle and not for the nop.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "hooks"))

import factory_gate  # noqa: E402
from stagelib import git, git_ok, sha256, tests_at  # noqa: E402


def run(*args):
    result = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, timeout=300,
                            check=False)
    if result.returncode:
        raise AssertionError(f"{' '.join(map(str, args))} exited {result.returncode}\n{result.stdout}{result.stderr}")
    return result.stdout


def grade(case, workspace):
    return json.loads(run(case / "grade.py", workspace).strip().splitlines()[-1])


def check_state(case, metadata, workspace):
    """The status.yaml parses as the hook reads it, approved gates match their hashes, commits exist."""
    change = workspace / ".software-factory/changes" / metadata["slug"]
    status = factory_gate.parse_status((change / "status.yaml").read_text())
    assert len(status["gates"]) == 4, "status.yaml: the hook cannot read four gates"
    assert status["branch"] == git(workspace, "symbolic-ref", "--short", "HEAD"), "status.yaml: branch"
    for gate, doc in factory_gate.GATES:
        if status["gates"][gate]["state"] == "approved":
            assert status["gates"][gate]["doc_sha256"] == sha256(change / doc), f"{gate}: doc_sha256"
    for item in status["slices"]:
        head = item["head_commit"]
        assert head in (None, "null") or git_ok(workspace, "cat-file", "-e", f"{head}^{{commit}}") is not None, head
    reason = factory_gate.check(change, status, "any.py") or ""
    assert "cannot read" not in reason and "changed after" not in reason, f"hook: {reason}"
    results = tests_at(workspace, "HEAD")
    assert results and all(outcome == "ok" for outcome, _ in results.values()), f"public tests at HEAD: {results}"
    words = case / "grading/forbidden_words.txt"
    if words.exists():
        source = " ".join(path.read_text() for path in (case / "fixture").rglob("*.py"))
        found = [word for word in words.read_text().splitlines() if word and re.search(word, source, re.I)]
        assert not found, f"forbidden words in the fixture: {found}"


def stopped(metadata, workspace):
    """Every stop_when condition holds: its file exists and its regex matches."""
    return all((workspace / item["path"]).exists() and re.search(item["regex"], (workspace / item["path"]).read_text())
               for item in metadata["stop_when"])


def check_case(case):
    metadata = json.loads((case / "case.json").read_text())
    errors, wrong = [], {}
    with tempfile.TemporaryDirectory(prefix="factory-stage-") as temporary:
        def end_state(name, script=None):
            workspace = Path(temporary) / name
            run(case / "setup.py", workspace)
            if script:
                run(script, workspace)
            return workspace, grade(case, workspace)

        nop, nop_scores = end_state("nop")
        check_state(case, metadata, nop)
        oracle, oracle_scores = end_state("oracle", case / "oracle/apply.py")
        if stopped(metadata, nop) or not stopped(metadata, oracle):
            errors.append("stop_when must hold for the oracle and not for the nop")
        for script in sorted((case / "oracle").glob("wrong_*.py")):
            wrong[script.stem] = end_state(script.stem, script)[1]
    if nop_scores["pass"]:
        errors.append(f"nop passed {nop_scores}")
    if not oracle_scores["pass"]:
        errors.append(f"oracle failed {oracle_scores}")
    errors += [f"{name} passed {scores}" for name, scores in wrong.items() if scores["pass"]]
    failed = lambda scores: ", ".join(key for key, value in scores.items() if key != "pass" and value < 1)  # noqa: E731
    print(f"{metadata['id']}: state ok; nop {'PASS' if nop_scores['pass'] else 'FAIL'} ({failed(nop_scores)}); "
          f"oracle {'PASS' if oracle_scores['pass'] else 'FAIL'}; "
          + "; ".join(f"{name} {'PASS' if s['pass'] else 'FAIL'} ({failed(s)})" for name, s in wrong.items()))
    return errors


def main():
    cases = sorted(path.parent for path in HERE.glob("*/case.json"))
    if len(cases) != 5:
        raise AssertionError(f"expected five stage cases, found {len(cases)}")
    errors = []
    for case in cases:
        try:
            errors += [f"{case.name}: {error}" for error in check_case(case)]
        except (AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
            print(f"{case.name}: ERROR {error}")
            errors.append(f"{case.name}: {error}")
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
