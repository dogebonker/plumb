from .storage import remove_document

def delete_document(document, actor_id):
    if document['owner_id'] != actor_id:
        raise PermissionError('Only the owner may delete')
    return remove_document(document)
