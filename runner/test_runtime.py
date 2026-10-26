"""Mechanical handoff and isolated RED regressions: python3 runner/test_runtime.py."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('plumb_runtime', Path(__file__).resolve().parents[1] / 'kit/runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git('init', '-q', '-b', 'plumb/demo')
        self.git('config', 'user.name', 'test')
        self.git('config', 'user.email', 'test@example.com')
        (self.repo / 'code').write_text('RED')
        self.git('add', '.')
        self.git('commit', '-qm', 'red')
        self.red = self.git('rev-parse', 'HEAD')
        (self.repo / 'code').write_text('GREEN')
        self.git('commit', '-qam', 'green')
        self.green = self.git('rev-parse', 'HEAD')
        self.change = self.repo / '.plumb/changes/demo'
        self.change.mkdir(parents=True)
        self.status = self.change / 'status.yaml'
        self.status.write_text(f'branch: plumb/demo\nslices:\n  - {{ id: 4, state: green, test_commit: {self.red}, head_commit: {self.green} }}\n')
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

    def red_cli(self, commit, checkpoint, *options, command=None):
        return subprocess.run([sys.executable, str(Path(runtime.__file__)), 'red', '--repo', str(self.repo),
                               '--commit', commit, '--checkpoint', str(checkpoint), *options, '--',
                               *(command or [sys.executable, 'test_code.py'])], capture_output=True, text=True, check=False)

    def test_corrected_test_cli_proves_old_bug_without_changing_live_work(self):
        (self.repo / 'test_code.py').write_text("from pathlib import Path\nassert Path('code').read_text() == 'GREEN'\n")
        self.git('add', 'test_code.py')
        self.git('commit', '-qm', 'wrong test')
        base = self.git('rev-parse', 'HEAD')
        original = (self.repo / 'test_code.py').read_bytes()
        (self.repo / 'test_code.py').write_text("from pathlib import Path\nassert Path('code').read_text() == 'FIXED'\n")
        self.git('commit', '-qam', 'correct test')
        tests = self.git('rev-parse', 'HEAD')
        corrected = (self.repo / 'test_code.py').read_bytes()
        (self.repo / 'code').write_text('FIXED')
        self.git('commit', '-qam', 'fix source')
        head = self.git('rev-parse', 'HEAD')
        (self.repo / 'code').write_text('STAGED')
        self.git('add', 'code')
        (self.repo / 'code').write_text('DIRTY')
        (self.repo / 'untracked').write_text('keep')
        before = self.git('status', '--porcelain', '--untracked-files=all', '--', '.', ':!.plumb')
        index = self.git('show', ':code')
        for source, expected in ((base, 1), (head, 0)):
            checkpoint = self.change / f'overlay-{expected}.json'
            result = self.red_cli(source[:12], checkpoint, '--tests-from', tests[:12], '--test-file', 'test_code.py')
            self.assertEqual(result.returncode, expected, result.stderr)
            record = json.loads(checkpoint.read_text())
            self.assertEqual(record['exit_code'], expected)
            self.assertEqual(record['base_commit'], source)
            self.assertEqual(record['tests_commit'], tests)
            self.assertEqual(record['test_files']['test_code.py'], {
                'original_sha256': hashlib.sha256(original if source == base else corrected).hexdigest(),
                'corrected_sha256': hashlib.sha256(corrected).hexdigest()})
        timeout = self.red_cli(base, self.change / 'overlay-timeout.json', '--tests-from', tests,
                               '--test-file', 'test_code.py', '--timeout', '1',
                               command=[sys.executable, '-c', 'import time; time.sleep(5)'])
        self.assertEqual(timeout.returncode, 124, timeout.stderr)
        self.assertIsNone(json.loads((self.change / 'overlay-timeout.json').read_text())['exit_code'])
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=all', '--', '.', ':!.plumb'), before)
        self.assertEqual(self.git('show', ':code'), index)
        self.assertEqual((self.repo / 'code').read_text(), 'DIRTY')
        self.assertEqual((self.repo / 'untracked').read_text(), 'keep')

    def test_overlay_cli_rejects_unsafe_paths_and_unpaired_options_before_command(self):
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests/test_ok.py').write_text('assert False\n')
        (self.repo / 'linked').symlink_to('tests', target_is_directory=True)
        (self.repo / 'test_link.py').symlink_to('tests/test_ok.py')
        self.git('add', 'tests', 'linked', 'test_link.py')
        self.git('commit', '-qm', 'test paths')
        tests = self.git('rev-parse', 'HEAD')
        for options in [('--tests-from', tests), ('--tests-from', ''), ('--test-file', 'tests/test_ok.py'), *[
                ('--tests-from', tests, '--test-file', path) for path in
                ('../test.py', '/test.py', 'tests/../test.py', './tests/test_ok.py', '.git/config',
                 '.plumb/test.py', 'tests', 'test_link.py', 'linked/test_ok.py', 'missing.py')]]:
            with self.subTest(options=options):
                result = self.red_cli(self.red, self.change / 'unsafe.json', *options,
                                      command=[sys.executable, '-c', "raise SystemExit(77)"])
                self.assertNotIn(result.returncode, (0, 77), result.stderr)
                self.assertFalse((self.change / 'unsafe.json').exists())

    def test_overlay_absent_original_and_nonancestor_commits(self):
        (self.repo / 'test_new.py').write_text('assert False\n')
        self.git('add', 'test_new.py')
        self.git('commit', '-qm', 'new regression')
        tests = self.git('rev-parse', 'HEAD')
        checkpoint = self.change / 'new-test.json'
        result = self.red_cli(self.red, checkpoint, '--tests-from', tests, '--test-file', 'test_new.py',
                              command=[sys.executable, 'test_new.py'])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIsNone(json.loads(checkpoint.read_text())['test_files']['test_new.py']['original_sha256'])
        self.git('checkout', '-qb', 'unrelated', self.red)
        (self.repo / 'code').write_text('OTHER')
        self.git('commit', '-qam', 'other branch')
        unrelated = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-q', 'plumb/demo')
        for source, overlay in ((unrelated, tests), (self.red, unrelated)):
            result = self.red_cli(source, self.change / 'nonancestor.json', '--tests-from', overlay,
                                  '--test-file', 'test_new.py', command=[sys.executable, '-c', 'raise SystemExit(77)'])
            self.assertNotIn(result.returncode, (0, 77))
            self.assertFalse((self.change / 'nonancestor.json').exists())

    def test_overlay_rejects_base_symlink_and_preserves_new_executable_tests(self):
        (self.repo / 'tests').symlink_to('outside', target_is_directory=True)
        self.git('add', 'tests')
        self.git('commit', '-qm', 'base symlink')
        base = self.git('rev-parse', 'HEAD')
        (self.repo / 'tests').unlink()
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests/test_ok.py').write_text('assert False\n')
        executable = self.repo / 'test_exec'
        executable.write_text('#!/bin/sh\nexit 23\n')
        executable.chmod(0o755)
        self.git('add', 'tests', 'test_exec')
        self.git('commit', '-qm', 'regular tests')
        tests = self.git('rev-parse', 'HEAD')
        checkpoint = self.change / 'base-symlink.json'
        rejected = self.red_cli(base, checkpoint, '--tests-from', tests, '--test-file', 'tests/test_ok.py',
                                command=[sys.executable, '-c', 'raise SystemExit(77)'])
        self.assertNotIn(rejected.returncode, (0, 77))
        self.assertFalse(checkpoint.exists())
        checkpoint = self.change / 'executable.json'
        result = self.red_cli(self.red, checkpoint, '--tests-from', tests, '--test-file', 'test_exec',
                              '--test-file', 'tests/test_ok.py', command=['./test_exec'])
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(set(json.loads(checkpoint.read_text())['test_files']), {'test_exec', 'tests/test_ok.py'})

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
        self.assertTrue(clone.is_relative_to(self.repo.resolve() / '.plumb/scratch'))
        self.assertEqual(self.git('check-ignore', '.plumb/scratch/owned-file'), '.plumb/scratch/owned-file')
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
        self.assertEqual(self.git('symbolic-ref', '--short', 'HEAD'), 'plumb/demo')
        self.assertEqual((self.repo / 'code').read_text(), 'DIRTY GREEN')
        self.assertEqual((self.repo / 'untracked').read_text(), 'keep')
        record = json.loads(checkpoint.read_text())
        self.assertEqual(record['deliverable_head'], self.green)
        self.assertEqual(record['state'], 'timeout')
        self.assertFalse(Path(record['verification_clone']).exists())


if __name__ == '__main__':
    unittest.main()
