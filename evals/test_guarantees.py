"""The report must retain failures, unsupported checks and source bindings."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import guarantees


class GuaranteeReportTests(unittest.TestCase):
    def test_real_scope_regression_and_persistent_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            report = guarantees.run(Path(folder), names=['scope'])
            self.assertEqual(report['cases'][0]['status'], 'pass')
            self.assertTrue(report['sources']['kit/v2_gates.py'])
            self.assertTrue((Path(folder) / 'scope.json').exists())

    def test_unsupported_is_not_pass_and_failure_is_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(guarantees, 'execute', return_value={'returncode': 2, 'stdout': '', 'stderr': 'missing'}):
                report = guarantees.run(Path(folder), names=['imports'])
            self.assertEqual(report['cases'][0]['status'], 'unsupported')
            self.assertFalse(report['passed'])

    def test_never_overwrites_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            guarantees.run(Path(folder), names=['scope'])
            with self.assertRaises(FileExistsError):
                guarantees.run(Path(folder), names=['scope'])

    def test_frozen_bdd_and_test_writes_denied_by_real_hook(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'tests').mkdir()
            frozen = ['tests/contract.feature', 'tests/test_contract.py']
            for name in frozen:
                (root / name).write_text('immutable approved scenario')
            policy = root / 'policy.json'
            policy.write_text(json.dumps({'schema_version': 1, 'run_id': 'fixture', 'slice_id': 'feature',
                                          'root': str(root), 'owns': ['tests/'], 'reads': [], 'frozen': frozen}))
            for name in frozen:
                result = subprocess.run([sys.executable, str(guarantees.ROOT / 'hooks/plumb_v2_gate.py'),
                                         '--policy', str(policy)], input=json.dumps({
                                             'tool_name': 'Write', 'tool_input': {'file_path': name, 'content': 'weakened'}}),
                                        text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual((root / name).read_text(), 'immutable approved scenario')
