"""Count the pages notes fill, find the latest note with a tag, and the archived share."""


def page_count(total: int, size: int) -> int:
    """Pages needed to show total notes, size per page; size is at least 1."""
    return total // size


def latest(notes: list[dict], tag: str) -> dict | None:
    """The most recently added note with tag, or None; notes are stored oldest first."""
    for index in range(len(notes) - 1, -1, -1):
        if tag in notes[index]["tags"]:
            return notes[index]
    return None


def archived_share(notes: list[dict]) -> float:
    """Fraction of notes that are archived."""
    archived = sum(1 for note in notes if note["archived"])
    return archived / len(notes)
