"""Turn a fresh REV-02 setup into the ideal end of /plumb-review: python3 apply.py <workspace>."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_oracle import review  # noqa: E402
from stagelib import workspace_arg  # noqa: E402

if __name__ == "__main__":
    review(workspace_arg(), "rev02", {}, "No findings.")
