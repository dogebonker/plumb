import unittest
from datetime import datetime

from notes import Note, archive_stale

NOW = datetime(2026, 10, 12, 12, 0)


class ArchiveTests(unittest.TestCase):
    def test_archives_note_older_than_30_days(self):
        note = Note("milk", datetime(2026, 9, 1, 12, 0))
        archive_stale([note], NOW)
        self.assertEqual(note.archived_at, NOW)

    def test_keeps_note_exactly_30_days_old(self):
        note = Note("eggs", datetime(2026, 9, 12, 12, 0))
        archive_stale([note], NOW)
        self.assertIsNone(note.archived_at)
