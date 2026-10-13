import unittest

from documents import DocumentStore


class ExistingDocumentTests(unittest.TestCase):
    def setUp(self):
        self.store = DocumentStore([
            {"id": "notes", "owner_id": "alice", "content": "meeting notes"},
            {"id": "empty", "owner_id": "alice", "content": ""},
        ])

    def test_owner_read(self):
        self.assertEqual(self.store.get_document("notes", "alice"), "meeting notes")
        self.assertEqual(self.store.get_document("empty", "alice"), "")

    def test_admin_read(self):
        self.assertEqual(self.store.get_document("notes", "admin", is_admin=True), "meeting notes")

    def test_unknown_document(self):
        with self.assertRaisesRegex(LookupError, "^document not found$"):
            self.store.get_document("missing", "alice")
