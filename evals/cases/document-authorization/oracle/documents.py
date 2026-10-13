"""Document reads used by the service's authenticated request handler."""


class DocumentStore:
    def __init__(self, documents):
        self.documents = {document["id"]: dict(document) for document in documents}

    def get_document(self, document_id, requester_id, *, is_admin=False):
        document = self.documents.get(document_id)
        if (document is None or not isinstance(requester_id, str) or not requester_id
                or (document["owner_id"] != requester_id and is_admin is not True)):
            raise LookupError("document not found")
        return document["content"]
