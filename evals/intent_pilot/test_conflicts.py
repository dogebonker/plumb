"""Evidence-boundary checks for the source-applicability trial."""

import unittest

import conflicts


class ConflictEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            "sources": {
                "old": {"content": "Paths must be NFC-normalized.\n"},
                "new": {
                    "content": "NFC normalization\ndoes not apply to session paths.\n"
                },
            },
            "code": {"adapter.rs": "return original_path;"},
            "code_original": {
                "adapter.rs": "// scope\nfn restore() {\n    return original_path;\n}\n"
            },
            "code_revision": "a" * 40,
        }
        self.response = {
            "code_status": "unknown",
            "source_status": "conflict",
            "needs_human": True,
            "evidence": [
                {
                    "kind": "source",
                    "id": "old",
                    "quote": "Paths must be NFC-normalized.",
                },
                {
                    "kind": "source",
                    "id": "new",
                    "quote": "NFC normalization does not apply to session paths.",
                },
            ],
            "explanation": "The supplied current rules disagree.",
            "question": "Which normalization rule currently applies?",
        }

    def test_source_wrapping_restores_original_text_and_line(self):
        citations = conflicts.validate(self.response, self.case)
        self.assertEqual(
            citations[1]["original_quote"],
            "NFC normalization\ndoes not apply to session paths.",
        )
        self.assertEqual(citations[1]["line"], 1)

    def test_changed_meaning_does_not_pass_whitespace_matching(self):
        self.response["evidence"][1]["quote"] = (
            "NFC normalization does apply to session paths."
        )
        with self.assertRaisesRegex(ValueError, "absent or ambiguous"):
            conflicts.validate(self.response, self.case)

    def test_conflict_requires_both_source_citations(self):
        self.response["evidence"].pop()
        with self.assertRaisesRegex(ValueError, "two source citations"):
            conflicts.validate(self.response, self.case)

    def test_ambiguous_source_quote_requires_more_context(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            conflicts.source_span(
                "Paths must be normalized. Paths must be normalized.",
                "Paths must be normalized.",
            )

    def test_code_judgment_needs_exact_code_evidence(self):
        self.response.update(
            code_status="aligned", source_status="compatible", needs_human=False
        )
        with self.assertRaisesRegex(ValueError, "needs code evidence"):
            conflicts.validate(self.response, self.case)
        self.response["evidence"].append(
            {"kind": "code", "id": "adapter.rs", "quote": "return original_path;"}
        )
        citations = conflicts.validate(self.response, self.case)
        self.assertEqual(citations[-1]["line"], 3)
        self.assertEqual(citations[-1]["revision"], "a" * 40)

    def test_synthetic_excerpt_join_is_not_real_source_evidence(self):
        self.response.update(code_status="mismatch", source_status="compatible")
        self.case["code"]["adapter.rs"] = "return original_path;\nreturn invented_path;"
        self.response["evidence"].append(
            {
                "kind": "code",
                "id": "adapter.rs",
                "quote": self.case["code"]["adapter.rs"],
            }
        )
        with self.assertRaisesRegex(ValueError, "code quote absent"):
            conflicts.validate(self.response, self.case)

    def test_missing_evidence_remains_a_human_question(self):
        self.response.update(source_status="compatible")
        self.response["evidence"] = self.response["evidence"][:1]
        conflicts.validate(self.response, self.case)
        self.response["question"] = ""
        with self.assertRaisesRegex(ValueError, "missing human question"):
            conflicts.validate(self.response, self.case)


if __name__ == "__main__":
    unittest.main()
