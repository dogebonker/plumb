"""In-memory catalog used by the document service."""


class DocumentCatalog:
    def __init__(self, documents):
        self.documents = list(documents)

    def list_documents(self, owner_id):
        return [document for document in self.documents if document["owner_id"] == owner_id]

    def list_page(self, owner_id, *, limit=20, after=None):
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise TypeError("limit must be an integer")
        if limit <= 0:
            raise ValueError("limit must be positive")
        if after is not None and not isinstance(after, str):
            raise TypeError("after must be a string or None")
        documents = sorted((document for document in self.list_documents(owner_id)
                            if after is None or document["id"] > after), key=lambda document: document["id"])
        items = documents[:limit]
        return {"items": items, "next_cursor": items[-1]["id"] if len(documents) > limit else None}
