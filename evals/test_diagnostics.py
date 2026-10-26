"""Offline diagnostics must preserve uncertainty and never publish tool inputs."""
import json
import tempfile
import unittest
from pathlib import Path

import diagnostics


def event(name, arguments, identity, timestamp=None):
    value = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": arguments, "id": identity}]}}
    if timestamp is not None:
        value["timestamp"] = timestamp
    return value


class DiagnosticTests(unittest.TestCase):
    def test_repeats_are_hashed_and_duplicate_native_ids_not_recounted(self):
        private = "echo PRIVATE_SECRET"
        first = event("Bash", {"command": private}, "one")
        report = diagnostics.profile_events([first, first, event("Bash", {"command": private}, "two")])
        self.assertEqual(report["tool_calls"], {"Bash": 2})
        self.assertEqual(report["repeated_inputs"][0]["count"], 2)
        self.assertNotIn(private, json.dumps(report))
        self.assertIsNone(report["observed_seconds"])

    def test_stage_time_requires_timestamped_evidence_and_is_not_model_time(self):
        report = diagnostics.profile_events([
            event("Skill", {"skill": "factory:plumb-plan"}, "a", 100),
            event("Read", {"file_path": "private.py"}, "b", 104),
            event("AskUserQuestion", {"questions": [{}, {}]}, "c", 109)])
        self.assertEqual(report["stage_observed_seconds"], {"plumb-plan": 9})
        self.assertEqual(report["question_items"], 2)
        self.assertEqual(report["observed_seconds"], 9)
        self.assertNotIn("model_seconds", report)

    def test_unattributed_calls_remain_unknown_and_artifact_paths_are_evidence(self):
        report = diagnostics.profile_events([
            event("Bash", {"command": "pytest"}, "a"),
            event("Read", {"file_path": "/work/.plumb/changes/x/architecture.md"}, "b")])
        self.assertEqual(report["stage_tool_calls"]["unknown"], 2)
        self.assertEqual(report["artifact_accesses"][0]["stage_hint"], "plumb-architecture")
        self.assertEqual(report["stage_evidence"], [])

    def test_runs_from_before_the_rename_keep_their_factory_stage_names(self):
        report = diagnostics.profile_events([
            event("Skill", {"skill": "factory:factory-plan"}, "a", 100),
            event("Read", {"file_path": "/work/.software-factory/changes/x/02-architecture.md"}, "b", 103),
            event("Bash", {"command": "cat skills/factory-build/SKILL.md"}, "c", 104)])
        self.assertEqual(report["stage_observed_seconds"], {"factory-plan": 4})
        self.assertEqual(report["artifact_accesses"][0]["stage_hint"], "factory-architecture")

    def test_numbered_artifacts_and_bash_mentions_never_establish_active_stage(self):
        events = [event("Bash", {"command": "cat /private/plumb-build/SKILL.md"}, "a", 100)]
        for index, (name, expected) in enumerate((("01-product", "product"), ("02-architecture", "architecture"),
                                                 ("03-interface", "interface"), ("04-slices", "slices"))):
            events.append(event("Read", {"file_path": f"/private/.plumb/changes/x/{name}.md"}, str(index), 101 + index))
        report = diagnostics.profile_events(events)
        self.assertEqual([row["stage_hint"] for row in report["artifact_accesses"]],
                         ["plumb-product", "plumb-architecture", "plumb-interface", "plumb-slices"])
        self.assertEqual(report["skill_file_mentions"][0]["skill"], "plumb-build")
        self.assertEqual(report["stage_evidence"], [])
        self.assertEqual(report["stage_tool_calls"], {"unknown": 5})
        self.assertEqual(report["stage_observed_seconds"], {"unknown": 4})
        self.assertNotIn("/private", json.dumps(report))

    def test_child_stage_never_changes_root_stage_or_overlapping_root_intervals(self):
        child = event("Skill", {"skill": "plumb-review"}, "child", 101)
        child["parent_tool_use_id"] = "private-parent-id"
        report = diagnostics.profile_events([
            event("Skill", {"skill": "plumb-build"}, "root", 100), child,
            event("Read", {"file_path": "source.py"}, "read", 104)])
        self.assertEqual(report["stage_observed_seconds"], {"plumb-build": 4})
        self.assertEqual(report["stage_tool_calls"], {"plumb-build": 2, "plumb-review": 1})
        self.assertNotIn("private-parent-id", json.dumps(report))

    def test_default_case_ids_match_actual_retained_trial_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ids = ("goldengate-1038", "limitless-4798", "bot-10", "limitless-4795")
            for identity in ids:
                trial = root / "trials" / identity / "factory"
                trial.mkdir(parents=True)
                (trial / "result.json").write_text(json.dumps({"status": "timeout"}))
            report = diagnostics.build_report(root)
            self.assertEqual(len(report["trials"]), 4)
            self.assertEqual(report["missing_cases"], [])

    def test_resume_deltas_do_not_sum_cumulative_usage_or_bridge_unknown_gaps(self):
        attempts = [{"usage": {"tokens": 10, "cost_usd": .1}},
                    {"usage": {"tokens": 25, "cost_usd": .3}},
                    {"usage": {"tokens": None}},
                    {"usage": {"tokens": 40, "cost_usd": .4}}]
        values = diagnostics.usage_deltas(attempts, "native-session")
        self.assertEqual([v["tokens"] for v in values], [10, 15, None, None])
        self.assertAlmostEqual(values[1]["cost_usd"], .2)
        self.assertIsNone(diagnostics.usage_deltas(attempts, None)[0]["tokens"])

    def test_report_binds_receipts_separates_delivery_from_quality_and_supports_subset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run.json").write_text(json.dumps({"model": "opus", "framework_sha256": "abc"}))
            trial = root / "trials" / "goldengate1038" / "factory"
            trial.mkdir(parents=True)
            (trial / "result.json").write_text(json.dumps({"session": "s", "status": "timeout",
                "source_sha256": "def", "tests": {"status": "pass"}, "attempts": [
                    {"seconds": 10, "usage": {"tokens": 12}, "response": {"state": "question"}}]}))
            (trial / "turn-000.jsonl").write_text(json.dumps(event("Bash", {"command": "secret"}, "a")) + "\n")
            report = diagnostics.build_report(root, ["goldengate1038"])
            row = report["trials"][0]
            self.assertEqual(row["delivery"]["reason"], "execution guard elapsed; stage cause unknown")
            self.assertEqual(row["quality"]["tests"], "pass")
            self.assertEqual(row["quality"]["review"], "unknown")
            self.assertEqual(row["bindings"]["source_sha256"], "def")
            self.assertEqual(len(row["receipts"][0]["sha256"]), 64)
            self.assertEqual(row["attempts"][0]["response_questions"], 1)
            self.assertEqual(report["missing_cases"], [])
            self.assertNotIn("secret", diagnostics.markdown(report))

    def test_malformed_preamble_does_not_shift_native_timing_indices(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "turn-000.jsonl"
            path.write_text("not-json\n[]\n" + json.dumps(event("Skill", {"skill": "plumb-build"}, "a")) +
                            "\nfalse\n" + json.dumps(event("Bash", {"command": "test"}, "b")) + "\n")
            path.with_suffix(".timings.jsonl").write_text(
                '{"event_index": 0, "timestamp": 100}\n{"event_index": 1, "timestamp": 103}\n')
            events, _ = diagnostics.read_events(path)
            report = diagnostics.profile_events(events)
            self.assertEqual(report["unparsed_lines"], 3)
            self.assertEqual(report["stage_observed_seconds"], {"unknown": 3})
            self.assertEqual([item["event_index"] for item in report["timestamp_observations"]], [2, 4])
            self.assertEqual(report["observed_seconds"], 3)

    def test_timing_sidecar_uses_receipt_time_without_claiming_execution_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "turn-000.jsonl"
            path.write_text(json.dumps(event("Skill", {"skill": "plumb-build"}, "a")) + "\n" +
                            json.dumps(event("Bash", {"command": "test"}, "b")) + "\n")
            path.with_suffix(".timings.jsonl").write_text(
                '{"event_index": 0, "timestamp": 100}\n{"event_index": 1, "timestamp": 103}\n')
            events, receipts = diagnostics.read_events(path)
            report = diagnostics.profile_events(events)
            self.assertEqual(report["observed_seconds"], 3)
            self.assertEqual(report["timestamp_sources"], ["receipt"])
            self.assertEqual(len(receipts), 2)


if __name__ == "__main__":
    unittest.main()
