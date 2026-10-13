import unittest

from catalog import DocumentCatalog


class PaginationAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.documents = [
            {"id": "z", "owner_id": "alice", "title": "Z"},
            {"id": "b", "owner_id": "bob", "title": "Private"},
            {"id": "10", "owner_id": "alice", "title": "Ten"},
            {"id": "2", "owner_id": "alice", "title": "Two"},
            {"id": "a", "owner_id": "alice", "title": "A"},
        ]
        self.catalog = DocumentCatalog(self.documents)

    def test_pages_and_owner_isolation(self):
        first = self.catalog.list_page("alice", limit=2)
        self.assertEqual(first, {"items": [self.documents[2], self.documents[3]], "next_cursor": "2"})
        second = self.catalog.list_page("alice", limit=2, after=first["next_cursor"])
        self.assertEqual(second, {"items": [self.documents[4], self.documents[0]], "next_cursor": None})
        self.assertEqual(self.catalog.list_page("bob", limit=1), {"items": [self.documents[1]], "next_cursor": None})

    def test_cursor_is_exclusive_and_need_not_exist(self):
        for after, expected in [("2", ["a", "z"]), ("3", ["a", "z"]), ("", ["10", "2", "a", "z"]), ("zz", [])]:
            with self.subTest(after=after):
                page = self.catalog.list_page("alice", after=after)
                self.assertEqual([document["id"] for document in page["items"]], expected)
                self.assertIsNone(page["next_cursor"])

    def test_default_limit_and_last_page(self):
        catalog = DocumentCatalog({"id": f"{i:02d}", "owner_id": "alice"} for i in reversed(range(21)))
        page = catalog.list_page("alice")
        self.assertEqual([item["id"] for item in page["items"]], [f"{i:02d}" for i in range(20)])
        self.assertEqual(page["next_cursor"], "19")
        self.assertEqual(catalog.list_page("alice", after="19"), {"items": [{"id": "20", "owner_id": "alice"}], "next_cursor": None})

    def test_empty_and_exact_page_boundary(self):
        self.assertEqual(self.catalog.list_page("nobody", limit=1), {"items": [], "next_cursor": None})
        self.assertEqual(DocumentCatalog([]).list_page("alice"), {"items": [], "next_cursor": None})
        self.assertIsNone(self.catalog.list_page("alice", limit=4)["next_cursor"])

    def test_invalid_arguments_even_for_empty_catalog(self):
        catalog = DocumentCatalog([])
        for limit in [True, False, 1.5, "2", None]:
            with self.subTest(limit=limit), self.assertRaises(TypeError):
                catalog.list_page("alice", limit=limit)
        for limit in [0, -1]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                catalog.list_page("alice", limit=limit)
        for after in [1, False, [], {}]:
            with self.subTest(after=after), self.assertRaises(TypeError):
                catalog.list_page("alice", after=after)

    def test_listing_does_not_change_existing_behavior(self):
        before = [dict(document) for document in self.documents]
        self.catalog.list_page("alice", limit=1)
        self.assertEqual(self.catalog.documents, before)
        self.assertEqual(self.catalog.list_documents("alice"), [self.documents[0], *self.documents[2:]])
        self.assertEqual(self.catalog.list_documents("missing"), [])
        self.assertEqual(DocumentCatalog([]).list_documents("alice"), [])
