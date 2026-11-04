import unittest
from unittest.mock import Mock

from ingester import accept


class AcceptTests(unittest.TestCase):
    def test_existing_accepted_batches(self):
        for size in (0, 1, 5):
            with self.subTest(size=size):
                items = list(range(size))
                stored = ["existing"]
                self.assertEqual(accept(items, stored), size)
                self.assertEqual(stored, ["existing"] + items)


    def test_all_supported_sizes_and_iterables(self):
        for size in range(6):
            for as_iterator in (False, True):
                with self.subTest(size=size, iterator=as_iterator):
                    expected = list(range(size))
                    items = iter(expected) if as_iterator else expected
                    stored = ["existing"]
                    self.assertEqual(accept(items, stored), size)
                    self.assertEqual(stored, ["existing"] + expected)

    def test_oversize_rejected_without_storage_calls(self):
        for size in (6, 9):
            for as_iterator in (False, True):
                with self.subTest(size=size, iterator=as_iterator):
                    items = iter(range(size)) if as_iterator else list(range(size))
                    store = Mock()
                    with self.assertRaisesRegex(ValueError, "five"):
                        accept(items, store)
                    store.append.assert_not_called()


if __name__ == "__main__":
    unittest.main()
