"""A wrong RED-01 end: red tests fail on assertTrue(False), and green deletes them. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import GREEN, RED, build, workspace_arg  # noqa: E402

TESTS = '''import unittest


class ArchiveTests(unittest.TestCase):
    def test_archives_note_older_than_30_days(self):
        self.assertTrue(False)

    def test_keeps_note_exactly_30_days_old(self):
        self.assertTrue(False)
'''

if __name__ == "__main__":
    build(workspace_arg(), {**RED, "test_archive.py": TESTS}, {**GREEN, "test_archive.py": None})
