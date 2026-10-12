"""A wrong REV-02 end: a signed review.md, but the planning state was never committed. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_oracle import review  # noqa: E402
from stagelib import workspace_arg  # noqa: E402

if __name__ == "__main__":
    review(workspace_arg(), "rev02", {}, "No findings.", planning_commit=False)
