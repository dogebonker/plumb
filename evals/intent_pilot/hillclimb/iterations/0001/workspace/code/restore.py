from .slug import encode_project


def restore_path(project, session_id):
    return encode_project(project) + "/" + session_id + ".jsonl"
