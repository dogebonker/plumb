"""Build the REV-01 start state in an empty target directory: python3 setup.py <target>."""

import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from review_setup import setup  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: setup.py <target>")
    setup(CASE, sys.argv[1], "rev01")
