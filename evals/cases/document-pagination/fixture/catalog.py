"""In-memory catalog used by the document service."""


class DocumentCatalog:
    def __init__(self, documents):
        self.documents = list(documents)

    def list_documents(self, owner_id):
        return [document for document in self.documents if document["owner_id"] == owner_id]
