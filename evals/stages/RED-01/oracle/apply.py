"""Turn a fresh RED-01 setup into the ideal end of one /factory-build step: python3 apply.py <workspace>."""

import re
import sys
from pathlib import Path

ORACLE = Path(__file__).resolve().parent
sys.path.insert(0, str(ORACLE.parents[1]))

from stagelib import change_dir, commit, git, workspace_arg, write  # noqa: E402

RED = {name: (ORACLE / "red" / name).read_text() for name in ("notes.py", "test_archive.py")}
GREEN = {"notes.py": (ORACLE / "green/notes.py").read_text()}


def build(workspace, red, green):
    """Commit red then green as the executor does, and record the slice as green. A None text deletes the file."""
    start = git(workspace, "rev-parse", "HEAD")
    commits = []
    for files, message in ((red, "test(red01): slice 01 red"), (green, "feat(red01): slice 01")):
        for name, text in files.items():
            if text is None:
                (workspace / name).unlink()
            else:
                write(workspace / name, text)
        commits.append(commit(workspace, message, *files))
    test, head = commits
    status = change_dir(workspace, "red01") / "status.yaml"
    write(status, re.sub(r"state: pending, base_commit: null, test_commit: null, head_commit: null",
                         f"state: green, base_commit: {start}, test_commit: {test}, head_commit: {head}",
                         status.read_text()).replace("slices approved. Next: /factory-build",
                                                     "Milestone 1 green. Next: /factory-review"))
    write(change_dir(workspace, "red01") / "slices/01/checks.md", f"""# Checks: slice 01, archive stale notes

Range: {start}..{head}
- Allowed files: pass
- Frozen contract: pass
- Red tests unchanged: pass
- Red: {test} failed on the new tests. Green: {head} passes test_command.
- Lint: pass
""")


if __name__ == "__main__":
    build(workspace_arg(), RED, GREEN)
