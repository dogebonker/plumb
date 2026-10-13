"""A wrong REV-01 end: the review fixes both bugs but deletes the slice's tests. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apply import FIXES, FINDINGS  # noqa: E402
from review_oracle import review  # noqa: E402
from stagelib import workspace_arg  # noqa: E402

if __name__ == "__main__":
    workspace = workspace_arg()
    tests = (workspace / "test_listing.py").read_text()
    review(workspace, "rev01", {**FIXES, "test_listing.py": [(tests, "")]}, FINDINGS)
