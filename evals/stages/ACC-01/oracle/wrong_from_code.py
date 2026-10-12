"""A wrong ACC-01 end: acceptance.md written from reading the code, with no request to the product. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import record, workspace_arg  # noqa: E402

if __name__ == "__main__":
    record(workspace_arg(), "app.py", "app.py:31 store.add returns the note with archived false",
           "app.py:25 GET /notes?archived=true calls store.list() without the flag, so eggs would be listed",
           "app.py:35 store.archive sets archived true")
