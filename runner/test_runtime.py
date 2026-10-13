"""Mechanical handoff and isolated RED regressions: python3 runner/test_runtime.py."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('factory_runtime', Path(__file__).resolve().parents[1] / 'kit/runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git('init', '-q', '-b', 'factory/demo')
        self.git('config', 'user.name', 'test')
        self.git('config', 'user.email', 'test@example.com')
        (self.repo / 'code').write_text('RED')
        self.git('add', '.')
        self.git('commit', '-qm', 'red')
        self.red = self.git('rev-parse', 'HEAD')
        (self.repo / 'code').write_text('GREEN')
        self.git('commit', '-qam', 'green')
        self.green = self.git('rev-parse', 'HEAD')
        self.change = self.repo / '.software-factory/changes/demo'
        self.change.mkdir(parents=True)
        self.status = self.change / 'status.yaml'
        self.status.write_text(f'branch: factory/demo\nslices:\n  - {{ id: 4, state: green, test_commit: {self.red}, head_commit: {self.green} }}\n')
        self.review = self.change / 'slices/04/review.md'
        self.review.parent.mkdir(parents=True)
        self.review.write_text('Reviewed exact slice path')
        self.completion = {'task_id': 'step-4', 'agent_id': 'native-9', 'state': 'completed', 'children': []}
        self.report = {'state': 'completed', 'children': [],
                       'status_sha256': hashlib.sha256(self.status.read_bytes()).hexdigest(),
                       'artifacts': [str(self.review.relative_to(self.repo))]}

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args], text=True).strip()

    def validate(self):
        return runtime.validate_handoff(self.repo, self.report, 'demo', 'step-4', 'native-9', '4', 'green', self.completion)

    def test_parent_owned_native_completion_envelope(self):
        # Actual caller combines the observed native return with an identity-free child report.
        self.assertNotIn('agent_id', self.report)
        self.assertEqual(self.validate(), [str(self.review.resolve())])
        self.report['agent_id'] = 'invented-by-child'
        self.assertEqual(self.validate(), [str(self.review.resolve())])
        for field, value in [('agent_id', 'wrong-native-return'), ('state', 'running'),
                             ('children', [{'id': 'unknown', 'state': 'running'}])]:
            old = self.completion[field]
            self.completion[field] = value
            with self.assertRaises(ValueError):
                self.validate()
            self.completion[field] = old
        with self.assertRaises(ValueError):
            runtime.validate_handoff(self.repo, self.report, 'demo', 'step-4', 'native-9', '4', 'green')

    def test_exact_returned_path_and_disk_state(self):
        self.assertEqual(self.validate(), [str(self.review.resolve())])
        self.report['artifacts'] = [str((self.change / 'review.md').relative_to(self.repo))]
        with self.assertRaises(ValueError):
            self.validate()

    def test_premature_or_wrong_identity_and_stale_state(self):
        for field, value in [('children', [{'id': 'executor', 'state': 'running'}]),
                             ('status_sha256', 'old')]:
            with self.subTest(field=field):
                old = self.report[field]
                self.report[field] = value
                with self.assertRaises(ValueError):
                    self.validate()
                self.report[field] = old
        self.status.write_text(self.status.read_text().replace('state: green', 'state: building'))
        self.report['status_sha256'] = hashlib.sha256(self.status.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.validate()

    def test_completed_rejects_unresolved_children_and_stale_source(self):
        self.completion['children'] = [{'id': 'executor', 'state': 'completed'}]
        for state in ('question', 'blocked'):
            self.report['children'] = [{'id': 'executor', 'state': state}]
            with self.assertRaises(ValueError):
                self.validate()
        self.report['children'] = []
        self.completion['children'] = []
        (self.repo / 'code').write_text('dirty')
        with self.assertRaises(ValueError):
            self.validate()
        self.git('add', 'code')
        self.git('commit', '-qm', 'later source edit')
        with self.assertRaises(ValueError):
            self.validate()

    def test_red_clone_is_workspace_local_and_resolves_node_dependencies(self):
        dependency = self.repo / 'node_modules/example'
        dependency.mkdir(parents=True)
        (dependency / 'index.js').write_text('module.exports=42')
        checkpoint = self.change / 'red-local.json'
        code = runtime.verify_red(self.repo, self.red, ['node', '-e',
                                  "const a=require('node:assert');a.equal(require('example'),42);a.equal(require('node:fs').readFileSync('code','utf8'),'RED')"], checkpoint, 10)
        self.assertEqual(code, 0)
        clone = Path(json.loads(checkpoint.read_text())['verification_clone'])
        self.assertTrue(clone.is_relative_to(self.repo.resolve() / '.software-factory/scratch'))
        self.assertEqual(self.git('check-ignore', '.software-factory/scratch/owned-file'), '.software-factory/scratch/owned-file')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.green)

    def test_browser_red_request_pins_recorded_commit_and_safe_checkpoint(self):
        path = runtime.prepare_browser_red(self.repo, self.red, 'demo-04-red-1')
        self.assertEqual(json.loads(path.read_text()), {'commit': self.red, 'checkpoint': 'demo-04-red-1'})
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.green)
        for checkpoint in ('../escape', '', 'a/b'):
            with self.assertRaises(ValueError):
                runtime.prepare_browser_red(self.repo, self.red, checkpoint)

    def test_fixed_green_browser_wrapper_is_not_red_command(self):
        with self.assertRaisesRegex(ValueError, 'red_test_command'):
            runtime.verify_red(self.repo, self.red, ['/runtime/browser-check'], self.change / 'red.json', 10)

    def test_red_timeout_preserves_green_and_dirty_files(self):
        (self.repo / 'code').write_text('DIRTY GREEN')
        (self.repo / 'untracked').write_text('keep')
        checkpoint = self.change / 'red-check.json'
        code = runtime.verify_red(self.repo, self.red, [sys.executable, '-c',
                                  "from pathlib import Path; import time; assert Path('code').read_text() == 'RED'; time.sleep(10)"], checkpoint, .1)
        self.assertIsNone(code)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.green)
        self.assertEqual(self.git('symbolic-ref', '--short', 'HEAD'), 'factory/demo')
        self.assertEqual((self.repo / 'code').read_text(), 'DIRTY GREEN')
        self.assertEqual((self.repo / 'untracked').read_text(), 'keep')
        record = json.loads(checkpoint.read_text())
        self.assertEqual(record['deliverable_head'], self.green)
        self.assertEqual(record['state'], 'timeout')
        self.assertFalse(Path(record['verification_clone']).exists())


if __name__ == '__main__':
    unittest.main()
