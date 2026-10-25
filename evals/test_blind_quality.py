"""Independent judge evidence and isolation regressions; never calls a model."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import blind_quality as judge


def verdict():
    absent = {"status": "unmeasured", "reason": "No standing history or architecture policy supplied.", "evidence": []}
    return {"verdict": "accept", "reason": "Approved behavior implemented.", "dimensions": {
        "correctness": {"status": "pass", "reason": "Requirement and implementation agree.", "evidence": [
            {"path": "TASK.md", "line": 1, "quote": "Return one"},
            {"path": "source/app.py", "line": 1, "quote": "return 1"}]},
        **{name: dict(absent) for name in ("architecture", "history", "rule_compliance")}}}


class BlindQualityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.packet = self.root / "anonymous"
        self.packet.mkdir()
        for tree in ("base", "source"):
            (self.packet / tree).mkdir()
            (self.packet / tree / "app.py").write_text("def app(): return 1\n")
        (self.packet / "TASK.md").write_text("Return one\n")
        (self.packet / "change.diff").write_text("diff\n")

    def tearDown(self):
        self.temporary.cleanup()

    def test_supported_verdict_preserves_unknown_dimensions(self):
        self.assertEqual(judge.validate_verdict(verdict(), self.packet)["dimensions"]["history"]["status"], "unmeasured")

    def test_malformed_unsupported_and_unanchored_verdicts_are_not_accepted(self):
        values = [None, {}, {**verdict(), "verdict": "maybe"}]
        for status in ("unknown", "PASS"):
            value = verdict()
            value["dimensions"]["correctness"]["status"] = status
            values.append(value)
        for evidence in ([], [{"path": "source/app.py", "line": 999, "quote": "return 1"}],
                         [{"path": "../blind-key.json", "line": 1, "quote": "secret"}],
                         [{"path": "source/app.py", "line": 1, "quote": "invented evidence"}]):
            value = verdict()
            value["dimensions"]["correctness"]["evidence"] = evidence
            values.append(value)
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                judge.validate_verdict(value, self.packet)

    def test_history_presence_cannot_satisfy_semantic_comparison(self):
        value = verdict()
        value["dimensions"]["history"] = {"status": "pass", "reason": "A decision file exists.",
            "evidence": [{"path": "source/app.py", "line": 1, "quote": "return 1"}]}
        with self.assertRaisesRegex(ValueError, "standing intent"):
            judge.validate_verdict(value, self.packet)

    def test_verdict_must_agree_with_dimension_findings(self):
        value = verdict()
        value["dimensions"]["correctness"]["status"] = "fail"
        with self.assertRaises(ValueError):
            judge.validate_verdict(value, self.packet)
        value["verdict"] = "reject"
        self.assertEqual(judge.validate_verdict(value, self.packet)["verdict"], "reject")

    def test_native_terminal_parser_rejects_missing_duplicate_and_error_receipts(self):
        result = {"type": "result", "subtype": "success", "result": json.dumps(verdict())}
        self.assertEqual(judge.terminal_verdict([result]), verdict())
        for events in ([], [result, result], [{**result, "is_error": True}], [{**result, "result": "not json"}]):
            with self.assertRaises(ValueError):
                judge.terminal_verdict(events)

    def test_single_whole_json_fence_matches_plain_and_rejects_extra_content(self):
        body = json.dumps(verdict())
        def receipt(text):
            return [{"type": "result", "subtype": "success", "result": text}]
        self.assertEqual(judge.terminal_verdict(receipt(body)),
                         judge.terminal_verdict(receipt("```json\n" + body + "\n```")))
        for malformed in ("```json\n" + body + "\n```\ntrailing prose",
                          "prose\n```json\n" + body + "\n```",
                          "```json\n" + body + "\n```\n```json\n" + body + "\n```",
                          "```json\n" + body + "\n" + body + "\n```",
                          "```json\nnot-json\n```", "```json\n[]\n```"):
            with self.subTest(body=malformed), self.assertRaises(ValueError):
                value = judge.terminal_verdict(receipt(malformed))
                judge.validate_verdict(value, self.packet)

    def test_settings_have_no_key_and_guard_denies_mutation_delegation_or_external_reads(self):
        invocation = self.root / "judge"
        invocation.mkdir()
        policy, settings = judge.prepare_settings(self.packet, invocation)
        self.assertEqual(policy["owns"], [])
        self.assertFalse(settings["autoMemoryEnabled"])
        self.assertEqual(settings["hooks"]["PreToolUse"][0]["matcher"], "*")
        self.assertNotIn("blind-key", json.dumps(settings))
        hook = judge.HOOK
        for name, arguments in (("Read", {"file_path": str(self.packet / "TASK.md")}),
                                ("Read", {"file_path": str(self.root / "blind-key.json")}),
                                ("Write", {"file_path": str(self.packet / "source/app.py"), "content": "changed"}),
                                ("Bash", {"command": "cat secret"}), ("Agent", {})):
            run = subprocess.run([judge.sys.executable, "-I", str(hook), "--policy", str(invocation / "policy.json")],
                                 input=json.dumps({"tool_name": name, "tool_input": arguments}), capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0 if name == "Read" and arguments["file_path"].endswith("TASK.md") else 2)

    def test_new_judge_uses_fresh_session_readonly_tools_and_no_ambient_plugins(self):
        invocation = self.root / "judge"
        invocation.mkdir()
        judge.prepare_settings(self.packet, invocation)
        first = judge.command("claude", "claude-opus-5-5", invocation, "one")
        second = judge.command("claude", "claude-opus-5-5", invocation, "two")
        self.assertNotEqual(first[first.index("--session-id") + 1], second[second.index("--session-id") + 1])
        self.assertEqual(first[first.index("--tools") + 1], "Read,Grep,Glob")
        self.assertNotIn("--resume", first)
        self.assertNotIn("--plugin-dir", first)
        self.assertIn("--strict-mcp-config", first)
        self.assertIn("semantic", judge.prompt(self.packet))
        self.assertNotIn("blind-key", judge.prompt(self.packet))

    def test_invalid_or_missing_native_inventory_never_promotes_verdict(self):
        init = {"type": "system", "subtype": "init", "plugins": [], "mcp_servers": [], "model": "pinned"}
        self.assertTrue(judge.inventory([init], "pinned")["verified"])
        for events in ([], [{**init, "plugins": [{"name": "factory"}]}], [{**init, "mcp_servers": [{}]}]):
            self.assertFalse(judge.inventory(events, "pinned")["verified"])

    def test_export_uses_only_validated_verdicts_and_never_silently_skips_failure(self):
        out = self.root / "judges"
        out.mkdir()
        run = out / "anonymous"
        run.mkdir()
        native = run / "native.jsonl"
        native.write_text(json.dumps({"type": "result", "subtype": "success", "result": json.dumps(verdict())}) + "\n")
        record = {"status": "complete", "packet_id": "anonymous", "packet_path": str(self.packet),
                  "verdict": verdict(), "packet_sha256": judge.benchmark.tree_hash(self.packet),
                  "receipts": {"native.jsonl": judge.sha(native)}}
        (run / "result.json").write_text(json.dumps(record))
        self.assertEqual(judge.export_verdicts(out), {"anonymous": verdict()})
        original = native.read_text()
        native.write_text("tampered\n")
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            judge.export_verdicts(out)
        native.write_text(original)
        record["status"] = "invalid_verdict"
        (run / "result.json").write_text(json.dumps(record))
        with self.assertRaises(ValueError):
            judge.export_verdicts(out)

    def test_full_mocked_native_run_binds_usage_as_evaluator_overhead(self):
        events = [{"type": "system", "subtype": "init", "plugins": [], "mcp_servers": [], "model": "claude-opus-5-5"},
                  {"type": "result", "subtype": "success", "result": json.dumps(verdict()), "total_cost_usd": .02,
                   "modelUsage": {"claude-opus-5-5": {"inputTokens": 10, "outputTokens": 5,
                       "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0}}}]
        def launch(*args, **kwargs):
            argv = args[0]
            events[0]["session_id"] = argv[argv.index("--session-id") + 1]
            kwargs["stdout"].write("\n".join(map(json.dumps, events)) + "\n")
            class Process:
                pid = 999999
                @staticmethod
                def wait(timeout=None):
                    return 0
            return Process()
        before = judge.benchmark.tree_hash(self.packet)
        with patch("blind_quality.subprocess.Popen", side_effect=launch), patch("blind_quality.os.killpg"):
            result = judge.run_judge(self.packet, self.root / "receipt", "claude", "claude-opus-5-5", 30)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["evaluator_overhead"]["usage"]["tokens"], 15)
        self.assertEqual(result["evaluator_overhead"]["usage"]["cost_usd"], .02)
        self.assertEqual(result["packet_sha256"], before)
        self.assertEqual(judge.benchmark.tree_hash(self.packet), before)
        self.assertNotIn("actor_tokens", result)

    def test_native_session_mismatch_cannot_complete_judgment(self):
        events = [{"type": "system", "subtype": "init", "plugins": [], "mcp_servers": [],
                   "model": "claude-opus-5-5", "session_id": "another-session"}]
        def launch(*args, **kwargs):
            kwargs["stdout"].write(json.dumps(events[0]) + "\n")
            class Process:
                pid = 999999
                @staticmethod
                def wait(timeout=None):
                    return 0
            return Process()
        with patch("blind_quality.subprocess.Popen", side_effect=launch), patch("blind_quality.os.killpg"):
            result = judge.run_judge(self.packet, self.root / "mismatch", "claude", "claude-opus-5-5", 30)
        self.assertEqual(result["status"], "invalid_verdict")
        self.assertFalse(result["session_verification"]["verified"])
        self.assertEqual(result["session_verification"]["observed"], ["another-session"])

    def test_retained_run_is_immutable_and_never_launches_second_paid_judge(self):
        out = self.root / "judged"
        out.mkdir()
        (out / "result.json").write_text(json.dumps({"status": "blocked"}))
        with patch("blind_quality.subprocess.Popen") as process, self.assertRaises(FileExistsError):
            judge.run_judge(self.packet, out, "claude", "claude-opus-5-5", 30)
        process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
