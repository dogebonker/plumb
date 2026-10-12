"""Notes kept in memory."""


class Notebook:
    def __init__(self):
        self.notes = {}
        self.next_id = 1

    def add(self, title):
        note_id = self.next_id
        self.notes[note_id] = {"id": note_id, "title": title}
        self.next_id += 1
        return note_id

    def delete(self, note_id):
        """Remove the note for good; an unknown id raises KeyError."""
        del self.notes[note_id]

    def titles(self):
        return [note["title"] for note in self.notes.values()]
