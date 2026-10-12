"""Notes kept in memory."""


class Store:
    def __init__(self):
        self.notes = []

    def add(self, title):
        note = {"id": len(self.notes) + 1, "title": title, "archived": False}
        self.notes.append(note)
        return note

    def archive(self, note_id):
        """Mark the note archived and return it, or None when no note has that id."""
        for note in self.notes:
            if note["id"] == note_id:
                note["archived"] = True
                return note
        return None

    def list(self, archived=None):
        """All notes, or only those whose archived flag equals archived."""
        return [note for note in self.notes if archived is None or note["archived"] == archived]
