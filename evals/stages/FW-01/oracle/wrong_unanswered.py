"""A wrong FW-01 end: two of four questions have no answer. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import ANSWERS, QUESTIONS, research, workspace_arg  # noqa: E402

if __name__ == "__main__":
    research(workspace_arg(), QUESTIONS, ANSWERS[:2])
