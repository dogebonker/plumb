"""Grade a RED-01 workspace: python3 grade.py <workspace>. Prints one JSON line."""

import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import change_dir, commit_by_subject, git_ok, report, tests_at, workspace_arg  # noqa: E402

RED_KINDS = {"AssertionError", "NotImplementedError"}  # an assertion, or the stub's error
MUTANTS = [CASE / "grading/mutant_empty.py", CASE / "grading/mutant_ge.py"]
REFERENCE = CASE / "oracle/green/notes.py"


def share(values):
    values = list(values)
    return sum(values) / len(values) if values else 0


if __name__ == "__main__":
    workspace = workspace_arg()
    scores = dict.fromkeys(["red_real", "old_tests_pass", "names_match", "tests_unchanged", "reference_green",
                            "mutants_killed"], 0)
    slices = change_dir(workspace, "red01") / "04-slices.md"
    expected = set(re.findall(r"^Tests first:.*?::\s*(\w+)", slices.read_text(), re.M)) if slices.exists() else set()
    test = commit_by_subject(workspace, r"^test\(red01\): slice 01 red$")
    feat = commit_by_subject(workspace, r"^feat\(red01\): slice 01$")
    if test:
        before = {name for name, (outcome, _) in tests_at(workspace, f"{test}~1").items() if outcome == "ok"}
        at = tests_at(workspace, test)
        new = [name for name in at if name not in before]
        scores["red_real"] = share(at[name][0] in ("FAIL", "ERROR") and at[name][1] in RED_KINDS for name in new)
        scores["old_tests_pass"] = share(at.get(name, ("missing",))[0] == "ok" for name in before)
        scores["names_match"] = bool(expected) and {name.rsplit(".", 1)[-1] for name in new} == expected
        files = [path for path in (git_ok(workspace, "diff", "--name-only", f"{test}~1", test) or "").split()
                 if Path(path).name.startswith("test")]
        scores["tests_unchanged"] = bool(feat and files) and git_ok(workspace, "diff", "--quiet", test, feat,
                                                                     "--", *files) is not None
        reference = tests_at(workspace, test, {"notes.py": REFERENCE})
        scores["reference_green"] = share(reference.get(name, ("missing",))[0] == "ok" for name in new)
        killed = [tests_at(workspace, test, {"notes.py": mutant}) for mutant in MUTANTS]
        scores["mutants_killed"] = share(any(result.get(name) == ("FAIL", "AssertionError") for result in killed)
                                         for name in new)
    hidden = tests_at(workspace, "HEAD", {"test_hidden_archive.py": CASE / "grading/test_hidden_archive.py"},
                      ["test_hidden_archive"])
    scores["hidden_pass"] = share(outcome == "ok" for outcome, _ in hidden.values())
    report(scores, list(scores))
