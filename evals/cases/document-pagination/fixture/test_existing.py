import unittest

from catalog import DocumentCatalog


class ExistingCatalogTests(unittest.TestCase):
    def test_owner_filter_and_insertion_order(self):
        documents = [
            {"id": "z", "owner_id": "alice", "title": "Last"},
            {"id": "b", "owner_id": "bob", "title": "Other"},
            {"id": "a", "owner_id": "alice", "title": "First"},
        ]
        catalog = DocumentCatalog(iter(documents))
        self.assertEqual(catalog.list_documents("alice"), [documents[0], documents[2]])
        self.assertEqual(catalog.list_documents("missing"), [])

    def test_empty_catalog(self):
        self.assertEqual(DocumentCatalog([]).list_documents("alice"), [])
