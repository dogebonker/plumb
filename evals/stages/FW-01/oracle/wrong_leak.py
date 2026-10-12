"""A wrong FW-01 end: the questions carry product words. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import ANSWERS, QUESTIONS, research, workspace_arg  # noqa: E402

if __name__ == "__main__":
    research(workspace_arg(), [QUESTIONS[0], "Which code could serve a resurrection or a reaper job?", *QUESTIONS[2:]], ANSWERS)
