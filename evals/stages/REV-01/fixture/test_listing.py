import unittest

from listing import archived_share, latest, page_count
from notes import make_note


class ListingTests(unittest.TestCase):
    def test_page_count(self):
        self.assertEqual(page_count(6, 3), 2)

    def test_latest(self):
        notes = [make_note("a", 1, ["work"]), make_note("b", 2, ["home"]), make_note("c", 3, ["work"])]
        self.assertEqual(latest(notes, "work")["title"], "c")

    def test_archived_share(self):
        notes = [make_note("a", 1, archived=True)] + [make_note(title, 2) for title in "bcd"]
        self.assertEqual(archived_share(notes), 0.25)
