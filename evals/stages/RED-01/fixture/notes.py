"""Notes and when they were archived."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    title: str
    created: datetime
    archived_at: datetime | None = None
