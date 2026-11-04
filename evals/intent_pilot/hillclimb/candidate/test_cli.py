"""Artifact destinations cannot bypass the read-only CLI phases."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from plumb.__main__ import main


class ArtifactScopeTests(unittest.TestCase):
    def run_command(self, arguments):
        model = Mock()
        model.usage.return_value = {"calls": 0, "tokens": 0, "unknown": False}
        model.last_receipt = None
        with (
            patch("sys.argv", ["plumb", *arguments]),
            patch("plumb.__main__.ClaudeModel", return_value=model) as factory,
            patch(
                "plumb.__main__.reconcile",
                return_value={"outcome": "unknown", "question": "Need evidence"},
            ),
            patch("plumb.__main__.propose", return_value={"proposal_id": "example"}),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            status = main()
        return status, factory

    def test_check_output_cannot_replace_reviewed_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            target = workspace / "code/main.py"
            target.parent.mkdir(parents=True)
            target.write_text("value = 1\n")
            status, factory = self.run_command(
                [
                    "check",
                    str(workspace),
                    "--output",
                    str(target),
                    "--receipts",
                    str(root / "receipts"),
                ]
            )
            self.assertEqual(status, 2)
            factory.assert_not_called()
            self.assertEqual(target.read_text(), "value = 1\n")

    def test_propose_output_cannot_replace_reviewed_knowledge(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            target = workspace / "knowledge/module.md"
            target.parent.mkdir(parents=True)
            target.write_text("Original requirement.\n")
            report = root / "report.json"
            report.write_text(json.dumps({"workspace": str(workspace)}))
            status, factory = self.run_command(
                [
                    "propose",
                    str(report),
                    "--choice",
                    "knowledge",
                    "--output",
                    str(target),
                    "--receipts",
                    str(root / "receipts"),
                ]
            )
            self.assertEqual(status, 2)
            factory.assert_not_called()
            self.assertEqual(target.read_text(), "Original requirement.\n")

    def test_receipts_cannot_be_written_inside_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            status, factory = self.run_command(
                [
                    "check",
                    str(workspace),
                    "--output",
                    str(root / "report.json"),
                    "--receipts",
                    str(workspace / "receipts"),
                ]
            )
            self.assertEqual(status, 2)
            factory.assert_not_called()
            self.assertFalse((workspace / "receipts").exists())

    def test_symlink_to_reviewed_file_is_not_an_output_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            target = workspace / "source.md"
            target.write_text("Original source.\n")
            alias = root / "report.json"
            alias.symlink_to(target)
            status, factory = self.run_command(
                [
                    "check",
                    str(workspace),
                    "--output",
                    str(alias),
                    "--receipts",
                    str(root / "receipts"),
                ]
            )
            self.assertEqual(status, 2)
            factory.assert_not_called()
            self.assertEqual(target.read_text(), "Original source.\n")

    def test_external_hardlink_output_does_not_change_reviewed_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            target = workspace / "source.md"
            target.write_text("Original source.\n")
            alias = root / "report.json"
            os.link(target, alias)
            status, _ = self.run_command(
                [
                    "check",
                    str(workspace),
                    "--output",
                    str(alias),
                    "--receipts",
                    str(root / "receipts"),
                ]
            )
            self.assertEqual(status, 3)
            self.assertEqual(target.read_text(), "Original source.\n")
            self.assertEqual(json.loads(alias.read_text())["outcome"], "unknown")


if __name__ == "__main__":
    unittest.main()
