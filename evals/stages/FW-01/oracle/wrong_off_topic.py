"""A wrong FW-01 end: research about code that does not exist, answered with nothing. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import research, workspace_arg  # noqa: E402

if __name__ == "__main__":
    research(workspace_arg(), ["How does the HTTP server authenticate requests?", "Which database stores users?"],
             ["not found", "not found"])
