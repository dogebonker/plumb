"""A wrong REV-01 end: the right fixes, plus a fix-severity finding on correct code. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apply import FIXES, POLISH  # noqa: E402
from review_oracle import review  # noqa: E402
from stagelib import workspace_arg  # noqa: E402

if __name__ == "__main__":
    review(workspace_arg(), "rev01", FIXES,
           POLISH + "\n- **4. [polish/design] fix test_notes.py: make_note should copy tags -> follow-up**")
