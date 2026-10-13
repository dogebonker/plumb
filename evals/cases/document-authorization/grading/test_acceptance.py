import unittest

from documents import DocumentStore


class AuthorizationAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"id": "notes", "owner_id": "alice", "content": "private notes"},
            {"id": "bob-notes", "owner_id": "bob", "content": "bob's notes"},
            {"id": "empty", "owner_id": "alice", "content": ""},
        ]
        self.store = DocumentStore(self.records)

    def assert_denied(self, document_id, requester_id, **kwargs):
        with self.assertRaises(LookupError) as caught:
            self.store.get_document(document_id, requester_id, **kwargs)
        self.assertIs(type(caught.exception), LookupError)
        self.assertEqual(str(caught.exception), "document not found")

    def test_cross_owner_and_case_sensitive_identity(self):
        for document_id, requester_id in [("notes", "bob"), ("bob-notes", "alice"), ("notes", "Alice"), ("empty", "bob")]:
            with self.subTest(document=document_id, requester=requester_id):
                self.assert_denied(document_id, requester_id)

    def test_anonymous_and_invalid_identities_even_for_admin(self):
        for requester_id in [None, "", 0, True, [], {}]:
            for is_admin in [False, True]:
                with self.subTest(requester=requester_id, admin=is_admin):
                    self.assert_denied("notes", requester_id, is_admin=is_admin)

    def test_only_boolean_true_grants_admin_access(self):
        for flag in [False, None, "true", "false", 1, [True]]:
            with self.subTest(flag=flag):
                self.assert_denied("notes", "bob", is_admin=flag)
        self.assertEqual(self.store.get_document("notes", "bob", is_admin=True), "private notes")

    def test_missing_and_forbidden_responses_match(self):
        for requester_id in ["alice", "bob", None]:
            for flag in [False, True]:
                with self.subTest(requester=requester_id, admin=flag):
                    self.assert_denied("unknown", requester_id, is_admin=flag)

    def test_compatibility_and_failed_reads_do_not_mutate(self):
        before = {key: dict(value) for key, value in self.store.documents.items()}
        self.assert_denied("notes", "bob")
        self.assert_denied("missing", "alice")
        self.assertEqual(self.store.documents, before)
        self.assertEqual(self.store.get_document("notes", "alice"), "private notes")
        self.assertEqual(self.store.get_document("bob-notes", "bob"), "bob's notes")
        self.assertEqual(self.store.get_document("empty", "alice", is_admin=False), "")
        self.assertEqual(self.records, list(before.values()))
