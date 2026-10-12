import unittest

from store import Store


class StoreTests(unittest.TestCase):
    def test_list_filters_by_archived_flag(self):
        store = Store()
        store.add("milk")
        store.add("eggs")
        store.archive(1)
        self.assertEqual([note["title"] for note in store.list(archived=True)], ["milk"])
        self.assertEqual([note["title"] for note in store.list(archived=False)], ["eggs"])
        self.assertEqual(len(store.list()), 2)

    def test_archive_of_unknown_id_is_none(self):
        self.assertIsNone(Store().archive(7))
