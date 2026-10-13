# Document catalog pagination

Add `DocumentCatalog.list_page(owner_id, *, limit=20, after=None)` to `catalog.py`. Keep the existing constructor and `list_documents(owner_id)` behavior.

Return `{"items": [...], "next_cursor": ...}`. Items are existing document dictionaries belonging to the requested owner, sorted by their string `id` in ascending lexicographic order. Return at most `limit` items. If `after` is provided, return only IDs strictly greater than it; the cursor need not identify an existing document. If more matching items remain, `next_cursor` is the ID of the last returned item; otherwise it is `None`. An empty result has an empty items list and a `None` cursor. Filtering must happen before pagination, so other owners never consume page slots or affect the cursor.

`limit` must be a positive integer: reject booleans and other types with `TypeError`, and zero or negative integers with `ValueError`. `after` must be a string or `None`; reject other types with `TypeError`. Assume stored IDs are unique strings and owner IDs are strings. Do not mutate catalog ordering or stored documents when listing pages. No new dependencies or persistence layer are needed.
