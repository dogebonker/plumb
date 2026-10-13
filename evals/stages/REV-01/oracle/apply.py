"""Turn a fresh REV-01 setup into the ideal end of /factory-review: python3 apply.py <workspace>."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_oracle import review  # noqa: E402
from stagelib import workspace_arg  # noqa: E402

FIXES = {"listing.py": [
    ("    return total // size", "    return (total + size - 1) // size"),
    ("    archived = sum", "    if not notes:\n        return 0.0\n    archived = sum"),
]}
FINDINGS = """1. [review/correctness] fix listing.py: page_count drops a partly filled last page, 7 notes at 3 per page give 2 -> auto-fixed
2. [review/correctness] fix listing.py: archived_share divides by zero when there are no notes -> auto-fixed
3. [review/correctness] fix listing.py: latest's range(len(notes) - 1, -1, -1) looks one short -> dropped"""

if __name__ == "__main__":
    review(workspace_arg(), "rev01", FIXES, FINDINGS)
