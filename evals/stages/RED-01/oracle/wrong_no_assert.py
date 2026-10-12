"""A wrong RED-01 end: red tests only call the stub and assert nothing. Must fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply import GREEN, RED, build, workspace_arg  # noqa: E402

TESTS = '''import unittest
from datetime import datetime

from notes import Note, archive_stale

NOW = datetime(2026, 10, 12, 12, 0)


class ArchiveTests(unittest.TestCase):
    def test_archives_note_older_than_30_days(self):
        archive_stale([Note("milk", datetime(2026, 9, 1, 12, 0))], NOW)

    def test_keeps_note_exactly_30_days_old(self):
        archive_stale([Note("eggs", datetime(2026, 9, 12, 12, 0))], NOW)
'''

if __name__ == "__main__":
    build(workspace_arg(), {**RED, "test_archive.py": TESTS}, GREEN)
