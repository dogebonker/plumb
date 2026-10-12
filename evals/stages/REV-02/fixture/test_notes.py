import unittest

from notes import make_note


class MakeNoteTests(unittest.TestCase):
    def test_make_note_keeps_title_and_tags(self):
        note = make_note("milk", 10, tags=["home"])
        self.assertEqual((note["title"], note["tags"], note["archived"]), ("milk", {"home"}, False))
