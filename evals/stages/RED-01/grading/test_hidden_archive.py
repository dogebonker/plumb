import unittest
from datetime import datetime

from notes import Note, archive_stale

NOW = datetime(2026, 10, 12, 12, 0)


class HiddenArchiveTests(unittest.TestCase):
    def test_archives_note_older_than_30_days(self):
        note = Note("milk", datetime(2026, 9, 1, 12, 0))
        self.assertEqual(archive_stale([note], NOW), [note])
        self.assertEqual(note.archived_at, NOW)

    def test_keeps_note_exactly_30_days_old(self):
        note = Note("eggs", datetime(2026, 9, 12, 12, 0))
        self.assertEqual(archive_stale([note], NOW), [])
        self.assertIsNone(note.archived_at)

    def test_one_minute_past_30_days_is_archived(self):
        note = Note("tea", datetime(2026, 9, 12, 11, 59))
        archive_stale([note], NOW)
        self.assertEqual(note.archived_at, NOW)

    def test_returns_archived_notes_in_input_order(self):
        old, fresh, older = Note("a", datetime(2026, 9, 5)), Note("b", datetime(2026, 10, 1)), Note("c", datetime(2026, 8, 1))
        self.assertEqual(archive_stale([old, fresh, older], NOW), [old, older])
        self.assertIsNone(fresh.archived_at)
