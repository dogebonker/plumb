"""Separate quality dimensions must retain missingness and cumulative accounting."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import quality_report as quality


class QualityReportTests(unittest.TestCase):
    def test_quality_and_delivery_remain_separate(self):
        case = {"provide_acceptance": True, "acceptance_files": ["test_feature.py"], "shared_inputs": [{"path": "policy.md"}],
                "archgraph_rules": "/private/layout.yaml", "archgraph_rules_sha256": "pin"}
        record = {"status": "timeout", "tests": {"status": "pass"},
                  "archgraph": {"status": "no_new_violations", "rules_sha256": "pin"},
                  "acceptance_integrity": {"verified": True, "files": {"test_feature.py": "a", "policy.md": "b"}, "changed": []}}
        metrics = quality.metrics(case, record, {})
        self.assertEqual(metrics["delivery"], "fail")
        self.assertEqual(metrics["supplied_tests"], "pass")
        self.assertEqual(metrics["pinned_policy_architecture"], "pass")
        self.assertEqual(metrics["acceptance_integrity"], "pass")
        self.assertEqual(metrics["shared_input_integrity"], "pass")
        self.assertEqual(metrics["semantic_history"], "unmeasured")

    def test_cycle_only_missing_receipts_and_unsupported_dimensions_stay_unmeasured(self):
        metrics = quality.metrics({}, {"status": "infrastructure_error", "archgraph": {"status": "no_new_violations"}},
                                  {"dimensions": {"history": {"status": "perfect"}}})
        self.assertTrue(all(value == "unmeasured" for value in metrics.values()))

    def test_assertion_failure_is_measured_but_grading_timeout_is_unmeasured(self):
        case = {"provide_acceptance": True, "acceptance_files": ["test_feature.py"]}
        for status, expected in (("assertion_failure", "fail"), ("timeout", "unmeasured")):
            with self.subTest(status=status):
                result = quality.metrics(case, {"tests": {"status": status}}, {})
                self.assertEqual(result["supplied_tests"], expected)

    def test_denominators_include_only_measured_observations(self):
        values = quality.summarize([{"metrics": {"delivery": "pass"}}, {"metrics": {"delivery": "fail"}},
                                    {"metrics": {"delivery": "unmeasured"}}])
        self.assertEqual(values["delivery"], {"pass": 1, "fail": 1, "unmeasured": 1, "measured": 2, "total": 3})

    def test_cost_uses_final_cumulative_receipt_and_never_sums_resume_snapshots(self):
        record = {"attempts": [{"usage": {"tokens": 10, "cost_usd": .1}}, {"usage": {"tokens": 25, "cost_usd": .3}}],
                  "task_seconds": 40, "probe_usage": {"tokens": 3, "cost_usd": .01}, "probe_seconds": 2}
        costs = quality.costs(record)
        self.assertEqual(costs["task"]["tokens"], 25)
        self.assertEqual(costs["probe"]["tokens"], 3)
        record["attempts"][-1]["usage"]["tokens"] = None
        self.assertIsNone(quality.costs(record)["task"]["tokens"])
        aggregate = quality.summarize_costs([costs["task"], {"tokens": None, "native_usd": None, "seconds": None}])
        self.assertIsNone(aggregate["tokens"]["total"])
        self.assertEqual(aggregate["tokens"]["measured_sum"], 25)
        self.assertEqual(aggregate["tokens"]["measured"], 1)

    def test_partial_integrity_receipt_cannot_prove_all_immutable_files(self):
        case = {"provide_acceptance": True, "acceptance_files": ["test_a.py", "test_b.py"]}
        record = {"acceptance_integrity": {"verified": True, "files": {"test_a.py": "pin"}, "changed": []}}
        self.assertEqual(quality.metrics(case, record, {})["acceptance_integrity"], "unmeasured")
        record["acceptance_integrity"]["changed"] = ["test_b.py"]
        self.assertEqual(quality.metrics(case, record, {})["acceptance_integrity"], "fail")

    def test_build_calls_existing_authority_and_binds_inputs_without_public_private_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = {"model": "pinned"}
            (root / "run.json").write_text(json.dumps(config))
            (root / "manifest.json").write_text(json.dumps({"cases": [{"id": "task", "provide_acceptance": True, "acceptance_files": ["test_feature.py"]}]}))
            path = root / "trials/task/factory/result.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"status": "timeout", "source_sha256": "source-pin", "grading_error": "PRIVATE SECRET"}))
            with patch("quality_report.pr_benchmark.report", return_value={"accepted": {"factory": 0}}) as authority:
                report = quality.build_report(root)
            authority.assert_called_once_with(root.resolve())
            self.assertEqual(report["rows"][2]["source_sha256"], "source-pin")
            self.assertEqual(len(report["input_receipts"]["run.json"]), 64)
            self.assertNotIn("PRIVATE SECRET", quality.markdown(report))
            self.assertIn("new violations", quality.markdown(report))
            self.assertNotIn("winner", report)

    def test_existing_authority_rejects_tampering_before_new_report(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch("quality_report.pr_benchmark.report", side_effect=ValueError("frozen packet changed")), \
                self.assertRaisesRegex(ValueError, "frozen packet changed"):
            quality.build_report(Path(temporary))

    def test_missing_dimensions_stay_unknown_and_source_binding_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "trials/task/factory/result.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"source_sha256": "source"}))
            key = {"anonymous": {"case": "task", "arm": "factory", "source_sha256": "source"}}
            (root / "blind-key.json").write_text(json.dumps(key))
            (root / "verdicts.json").write_text(json.dumps({"verdicts": {"anonymous": {"verdict": "accept"}}}))
            reviews, _ = quality.frozen_reviews(root)
            self.assertEqual(reviews["task", "factory"]["dimensions"], {})
            key["anonymous"]["source_sha256"] = "different"
            (root / "blind-key.json").write_text(json.dumps(key))
            with self.assertRaisesRegex(ValueError, "source binding"):
                quality.frozen_reviews(root)


if __name__ == "__main__":
    unittest.main()
