"""Notes and when they were archived."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Note:
    title: str
    created: datetime
    archived_at: datetime | None = None


def archive_stale(notes: list[Note], now: datetime) -> list[Note]:
    """Set archived_at to now on every note created more than 30 days before now; return those notes in order."""
    stale = [note for note in notes if now - note.created >= timedelta(days=30)]
    for note in stale:
        note.archived_at = now
    return stale
