import unittest

from notes import Notebook


class NotebookTests(unittest.TestCase):
    def test_delete_removes_note(self):
        book = Notebook()
        book.add("milk")
        eggs = book.add("eggs")
        book.delete(eggs)
        self.assertEqual(book.titles(), ["milk"])

    def test_delete_of_unknown_id_raises(self):
        with self.assertRaises(KeyError):
            Notebook().delete(3)
