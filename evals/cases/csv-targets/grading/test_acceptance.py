import unittest

from targets import parse_targets


class CsvAcceptanceTests(unittest.TestCase):
    def test_existing_simple_input_and_invalid_headers(self):
        self.assertEqual(parse_targets("\nname, region, enabled\n api , eu , TRUE\nworker,us,false\n"), [
            {"name": "api", "region": "eu", "enabled": True},
            {"name": "worker", "region": "us", "enabled": False},
        ])
        self.assertEqual(parse_targets(" \n\n"), [])
        for header in ["wrong,region,enabled", "region,name,enabled", "name,region", "name,region,enabled,extra"]:
            with self.subTest(header=header), self.assertRaises(ValueError):
                parse_targets(header + "\na,b,true")

    def test_quoted_commas_and_escaped_quotes(self):
        self.assertEqual(parse_targets('name,region,enabled\n"api, blue","eu ""west""",TrUe\n'), [
            {"name": "api, blue", "region": 'eu "west"', "enabled": True},
        ])

    def test_multiline_and_crlf(self):
        self.assertEqual(parse_targets('name,region,enabled\r\n"api\r\nblue",eu,false\r\n'), [
            {"name": "api\r\nblue", "region": "eu", "enabled": False},
        ])

    def test_blank_records_quoted_values_and_header(self):
        self.assertEqual(parse_targets('\n"name","region","enabled"\n \t \n" api "," eu "," false "\n'), [
            {"name": "api", "region": "eu", "enabled": False},
        ])

    def test_validation_still_applies_to_parsed_fields(self):
        for row in [' , , ', '""', '"",eu,true', 'api,"  ",true', 'api,eu,"yes"', 'api,eu', '"api,x",eu,true,extra', '"unterminated,eu,true', '"api"junk,eu,true']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_targets("name,region,enabled\n" + row)

    def test_order_duplicates_and_header_only(self):
        text = 'name,region,enabled\n"a,b",eu,true\n"a,b",eu,false\n'
        self.assertEqual([row["enabled"] for row in parse_targets(text)], [True, False])
        self.assertEqual(parse_targets('"name",region,enabled\n'), [])
