import unittest

from listing import archived_share, latest, page_count
from notes import make_note


class ListingTests(unittest.TestCase):
    def test_page_count(self):
        self.assertEqual((page_count(7, 3), page_count(6, 3), page_count(0, 3)), (3, 2, 0))

    def test_latest(self):
        notes = [make_note("a", 1, ["work"]), make_note("b", 2, ["home"]), make_note("c", 3, ["work"])]
        self.assertEqual(latest(notes, "work")["title"], "c")
        self.assertEqual(latest(notes[:2], "work")["title"], "a")
        self.assertIsNone(latest(notes, "travel"))

    def test_archived_share(self):
        notes = [make_note("a", 1, archived=True)] + [make_note(title, 2) for title in "bcd"]
        self.assertEqual((archived_share(notes), archived_share([])), (0.25, 0.0))
