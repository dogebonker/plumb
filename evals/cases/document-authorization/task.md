# Document read authorization

Repair the authorization boundary in `DocumentStore.get_document(document_id, requester_id, *, is_admin=False)` in `documents.py`. Keep the signature and string content return value.

An authenticated requester may read a document only if its `owner_id` equals the requester ID, or the trusted `is_admin` flag is literally `True`. A requester ID is authenticated when it is a nonempty string; `None`, empty strings, and other types must never grant access, even with the admin flag. A truthy nonboolean admin flag must not grant administrative access. Stored owner IDs are nonempty strings.

For both unknown document IDs and denied access, raise `LookupError("document not found")`. The same response must apply whether the document exists, so callers cannot use denied reads to probe its existence. Preserve owner reads, authenticated admin reads, empty document content, and the original missing-document response. Failed reads must leave the stored documents unchanged. The flag is supplied by a trusted caller; no login system, HTTP layer, or new dependency is needed.
