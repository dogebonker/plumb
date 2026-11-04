"""Behavior checks for the pilot's evidence boundary, not its model quality."""

import unittest

import pilot


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            "focus": "Preserve session identity",
            "source_url": "https://example.invalid/decision",
            "raw_intent": "A subagent must retain its own session identity.",
            "bundle_intent": "A subagent must retain its own session identity.",
            "code": {
                "src/adapter.rs": "fn session_id() {\n    return parent_session_id;\n}\n"
            },
            "expected": "SECRET LABEL",
        }
        self.response = {
            "verdict": "mismatch",
            "intent_quote": self.case["raw_intent"],
            "code_path": "src/adapter.rs",
            "code_quote": "return parent_session_id;",
            "explanation": "The child borrows the parent id.",
            "question": "Should the child retain its own id?",
        }

    def test_valid_quotes_produce_a_real_code_line(self):
        observation = pilot.validate(self.response, self.case, "raw")
        self.assertEqual(observation["derived_code_line"], 2)
        self.assertEqual(observation["status"], "valid")

    def test_invented_intent_is_not_a_finding(self):
        self.response["intent_quote"] = "All sessions must use the parent identity."
        with self.assertRaisesRegex(ValueError, "intent quote absent"):
            pilot.validate(self.response, self.case, "raw")

    def test_invented_code_is_not_a_finding(self):
        self.response["code_quote"] = "return child_session_id;"
        with self.assertRaisesRegex(ValueError, "code quote absent"):
            pilot.validate(self.response, self.case, "raw")

    def test_other_file_cannot_supply_the_evidence(self):
        self.response["code_path"] = "src/unseen.rs"
        with self.assertRaisesRegex(ValueError, "code quote absent"):
            pilot.validate(self.response, self.case, "bundle")

    def test_uncertain_is_preserved_instead_of_clean(self):
        self.response["verdict"] = "uncertain"
        self.response["code_quote"] = ""
        self.assertEqual(
            pilot.validate(self.response, self.case, "raw")["status"], "uncertain"
        )

    def test_unknown_verdict_and_empty_evidence_are_rejected(self):
        for field, value in [
            ("verdict", "clean"),
            ("code_quote", ""),
            ("intent_quote", ""),
        ]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                pilot.validate({**self.response, field: value}, self.case, "raw")

    def test_packet_excludes_labels_and_uses_the_same_code_in_both_arms(self):
        raw = pilot.packet(self.case, "raw")
        bundle = pilot.packet(self.case, "bundle")
        self.assertNotIn("SECRET LABEL", raw)
        self.assertNotIn("SECRET LABEL", bundle)
        self.assertEqual(
            raw.split("PRODUCTION CODE:\n")[1], bundle.split("PRODUCTION CODE:\n")[1]
        )


if __name__ == "__main__":
    unittest.main()
