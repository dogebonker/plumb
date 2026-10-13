import unittest

from targets import parse_targets


class ExistingTargetsTests(unittest.TestCase):
    def test_simple_targets_and_whitespace(self):
        self.assertEqual(parse_targets("\nname, region, enabled\n api , eu , TRUE\nworker,us,false\n"), [
            {"name": "api", "region": "eu", "enabled": True},
            {"name": "worker", "region": "us", "enabled": False},
        ])

    def test_empty(self):
        self.assertEqual(parse_targets(" \n\n"), [])

    def test_invalid_input(self):
        for text in ["wrong,region,enabled", "name,region,enabled\na,b", "name,region,enabled\na,b,yes", "name,region,enabled\n,b,true"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_targets(text)
