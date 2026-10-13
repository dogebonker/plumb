"""Document reads used by the service's authenticated request handler."""


class DocumentStore:
    def __init__(self, documents):
        self.documents = {document["id"]: dict(document) for document in documents}

    def get_document(self, document_id, requester_id, *, is_admin=False):
        document = self.documents.get(document_id)
        if document is None:
            raise LookupError("document not found")
        return document["content"]
