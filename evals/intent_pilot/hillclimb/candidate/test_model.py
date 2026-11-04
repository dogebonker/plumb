"""Model-boundary tests run without network calls or a provider subscription."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from plumb.model import ClaudeModel


class ModelBoundaryTests(unittest.TestCase):
    def provider(self, *, model="claude-fable-5-1", result=None):
        return {
            "is_error": False,
            "subtype": "success",
            "result": json.dumps(result or {"ok": True}),
            "modelUsage": {
                model: {
                    "inputTokens": 10,
                    "outputTokens": 5,
                    "cacheReadInputTokens": 0,
                    "cacheCreationInputTokens": 0,
                }
            },
            "total_cost_usd": 0.01,
            "subagent_stats": {"spawned": 0},
            "permission_denials": [],
        }

    def process(self, provider):
        process = Mock(returncode=0)
        process.communicate.return_value = (json.dumps(provider), "")
        return process

    def test_two_real_receipts_ignore_prompt_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            model = ClaudeModel(temporary, max_calls=2)
            with patch(
                "plumb.model.subprocess.Popen",
                side_effect=lambda *a, **k: self.process(self.provider()),
            ) as spawn:
                self.assertEqual(model("system", {"task": "one"}), {"ok": True})
                self.assertEqual(model("system", {"task": "two"}), {"ok": True})
                self.assertEqual(model.usage()["calls"], 2)
                self.assertEqual(model.usage()["tokens"], 30)
                self.assertFalse(model.usage()["unknown"])
                with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
                    model("system", {"task": "three"})
                self.assertEqual(spawn.call_count, 2)

    def test_unknown_prior_usage_prevents_another_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, "call-0001.json").write_text(
                json.dumps({"list_cost_usd": None, "tokens": None})
            )
            with (
                patch("plumb.model.subprocess.Popen") as spawn,
                self.assertRaisesRegex(RuntimeError, "unknown usage"),
            ):
                ClaudeModel(temporary)("system", {})
            spawn.assert_not_called()

    def test_unpinned_provider_is_rejected_and_raw_evidence_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch(
                    "plumb.model.subprocess.Popen",
                    return_value=self.process(self.provider(model="other")),
                ),
                self.assertRaisesRegex(RuntimeError, "response failed"),
            ):
                ClaudeModel(temporary)("system", {})
            receipt = json.loads(Path(temporary, "call-0001.json").read_text())
            self.assertEqual(receipt["status"], "failed")
            self.assertIn("unpinned", receipt["error"])
            self.assertEqual(receipt["list_cost_usd"], 0.01)

    def test_provider_input_has_no_filesystem_or_command_tools(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch(
                "plumb.model.subprocess.Popen",
                return_value=self.process(self.provider()),
            ) as spawn:
                ClaudeModel(temporary)("system", {})
            args, kwargs = spawn.call_args
            command = args[0]
            self.assertEqual(command[command.index("--tools") + 1], "")
            self.assertIn("--safe-mode", command)
            self.assertEqual(kwargs["env"]["CLAUDE_CODE_MAX_RETRIES"], "0")

    def test_prompt_archive_hardlink_does_not_modify_other_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.md"
            source.write_text("Original source.\n")
            receipts = root / "receipts"
            receipts.mkdir()
            os.link(source, receipts / "call-0001.prompt.json")
            with patch(
                "plumb.model.subprocess.Popen",
                return_value=self.process(self.provider()),
            ):
                ClaudeModel(receipts)("system", {})
            self.assertEqual(source.read_text(), "Original source.\n")


if __name__ == "__main__":
    unittest.main()
