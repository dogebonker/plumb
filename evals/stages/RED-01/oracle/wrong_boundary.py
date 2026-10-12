"""A wrong RED-01 end: the red boundary test expects a 30-day-old note archived; green corrects it. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import GREEN, RED, build, workspace_arg  # noqa: E402

WRONG = RED["test_archive.py"].replace("        self.assertIsNone(note.archived_at)",
                                       "        self.assertEqual(note.archived_at, NOW)")

if __name__ == "__main__":
    assert WRONG != RED["test_archive.py"]
    build(workspace_arg(), {**RED, "test_archive.py": WRONG}, {**GREEN, "test_archive.py": RED["test_archive.py"]})
