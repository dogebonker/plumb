import unittest

from ingester import accept


class AcceptTests(unittest.TestCase):
    def test_existing_accepted_batches(self):
        for size in (0, 1, 5):
            with self.subTest(size=size):
                items = list(range(size))
                stored = ["existing"]
                self.assertEqual(accept(items, stored), size)
                self.assertEqual(stored, ["existing"] + items)


if __name__ == "__main__":
    unittest.main()
