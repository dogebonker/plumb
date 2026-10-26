"""A wrong REV-02 end: review.md is the bare template, unsigned, and the slice stays green. Must fail."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stagelib import FACTORY, change_dir, commit, workspace_arg, write  # noqa: E402

if __name__ == "__main__":
    workspace = workspace_arg()
    commit(workspace, "chore(plumb): milestone 1 review", ".plumb")
    template = (FACTORY / "skills/plumb-review/SKILL.md").read_text()
    body = re.search(r"```markdown\n(# Review:.*?)```", template, re.S).group(1)
    write(change_dir(workspace, "rev02") / "slices/01/review.md", body)
