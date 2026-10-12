import unittest
from datetime import datetime

from notes import Note


class NoteTests(unittest.TestCase):
    def test_new_note_is_not_archived(self):
        self.assertIsNone(Note("milk", datetime(2026, 9, 1)).archived_at)
