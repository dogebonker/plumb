import unittest

from listing import archived_share, latest, page_count
from notes import make_note


class HiddenListingTests(unittest.TestCase):
    def test_b1_partly_filled_last_page_counts(self):
        self.assertEqual((page_count(7, 3), page_count(6, 3), page_count(0, 3)), (3, 2, 0))

    def test_b2_no_notes_share_is_zero(self):
        self.assertEqual(archived_share([]), 0.0)
        self.assertEqual(archived_share([make_note("a", 1, archived=True), make_note("b", 2)]), 0.5)

    def test_d1_latest_scans_every_note_newest_first(self):
        notes = [make_note("a", 1, ["work"]), make_note("b", 2, ["home"]), make_note("c", 3, ["work"])]
        self.assertEqual(latest(notes, "work")["title"], "c")
        self.assertEqual(latest(notes[:2], "work")["title"], "a")
        self.assertIsNone(latest(notes, "travel"))
        self.assertIsNone(latest([], "work"))
