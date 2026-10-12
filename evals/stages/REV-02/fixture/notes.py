"""Notes kept in memory, oldest first."""


def make_note(title, created, tags=(), archived=False):
    """A note as a plain dict; created is a Unix time in seconds."""
    return {"title": title, "created": created, "tags": set(tags), "archived": archived}
