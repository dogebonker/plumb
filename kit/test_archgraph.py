"""Executable integration contracts; no native installation required."""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('plumb_archgraph', Path(__file__).with_name('archgraph.py'))


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.repo = self.home / 'repo'
        self.repo.mkdir()
        for command in (['init', '-q'], ['config', 'user.email', 'test@example.com'], ['config', 'user.name', 'Test']):
            subprocess.run(['git', *command], cwd=self.repo, check=True)
        (self.repo / 'a space.py').write_text('x = 1\n')
        (self.repo / 'layout.yaml').write_text('modules: []\n')
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        subprocess.run(['git', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'base'], cwd=self.repo, check=True)
        self.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(self.module)
        output = patch.object(self.module, 'print', create=True)
        output.start()
        self.addCleanup(output.stop)
        self.calls = []

    def args(self, command='prepare'):
        return argparse.Namespace(command=command, repo=str(self.repo), root='.', base='HEAD', files=['a space.py'] if command == 'check' else ['a space.py', 'deleted.py', 'docs.md'], task='Implement feature', budget='8k', language='python', rules='layout.yaml', out=str(self.home / 'evidence'))

    def fake(self, argv, cwd, output, allowed=(0,)):
        self.calls.append((argv, Path(cwd)))
        if 'scan' in argv:
            Path(argv[argv.index('-o') + 1]).write_text(json.dumps({'files': [{'path': 'a space.py'}], 'edges': [], 'modules': [], 'cycles': []}))
            value = {}
        elif 'context' in argv:
            value = {'entries': [], 'omitted': ['a space.py'], 'limitations': ['partial native symbols'], 'budget': 8000, 'used_tokens': 0}
        elif 'diff' in argv:
            value = {'new_forbidden': [], 'new_cycles': [], 'new_unplanned': []}
        else:
            value = {'schema': 'archgraph/brief/v1', 'result': {}, 'omitted': {}}
        Path(output).write_text(json.dumps(value))
        return 0

    def run_fake(self, args, fake=None):
        with patch.object(self.module, 'resolve_binary', return_value={'binary': '/verified/archgraph', 'source_pin': self.module.PIN}), patch.object(self.module, 'run', side_effect=fake or self.fake):
            return self.module.execute(args)

    def test_missing_tool_is_skipped_not_pass(self):
        with patch.object(self.module, 'resolve_binary', side_effect=self.module.Unavailable('missing')):
            self.assertEqual(self.module.execute(self.args()), 2)
        self.assertEqual(json.loads((self.home / 'evidence/report.json').read_text())['status'], 'skipped')

    def test_preserves_changed_file_coverage_and_spaces(self):
        self.assertEqual(self.run_fake(self.args()), 0)
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertEqual(report['changed_files'], self.args().files)
        self.assertEqual(report['context']['omitted'], ['a space.py'])
        context = next(argv for argv, _ in self.calls if 'context' in argv)
        self.assertIn('a space.py', context)
        self.assertTrue(all('--no-daemon' in argv for argv, _ in self.calls))

    def test_output_inside_repo_is_rejected(self):
        args = self.args()
        args.out = str(self.repo / 'evidence')
        self.assertEqual(self.run_fake(args), 2)
        self.assertFalse((self.repo / 'evidence').exists())

    def test_both_scans_use_identical_current_rules(self):
        self.assertEqual(self.run_fake(self.args('check')), 0)
        scans = [(a, cwd) for a, cwd in self.calls if 'scan' in a]
        self.assertEqual(len(scans), 2)
        self.assertEqual(scans[0][0][scans[0][0].index('--rules') + 1], scans[1][0][scans[1][0].index('--rules') + 1])
        self.assertNotEqual(scans[0][1], scans[1][1])
        self.assertIn('--include-tests', scans[0][0])

    def test_planted_violation_fails(self):
        def violation(argv, cwd, output, allowed=(0,)):
            result = self.fake(argv, cwd, output, allowed)
            if 'diff' in argv:
                Path(output).write_text(json.dumps({'new_forbidden': [{'file': 'a space.py'}], 'new_cycles': [], 'new_unplanned': []}))
                return 1
            return result
        self.assertEqual(self.run_fake(self.args('check'), violation), 1)

    def test_malformed_native_output_is_error(self):
        def malformed(argv, cwd, output, allowed=(0,)):
            self.fake(argv, cwd, output, allowed)
            if 'diff' in argv:
                Path(output).write_text('{}')
            return 0
        self.assertEqual(self.run_fake(self.args('check'), malformed), 2)

    def test_source_changed_during_scan_is_error(self):
        def changing(argv, cwd, output, allowed=(0,)):
            result = self.fake(argv, cwd, output, allowed)
            (self.repo / 'a space.py').write_text('changed\n')
            return result
        self.assertEqual(self.run_fake(self.args(), changing), 2)

    def test_prepare_records_base_commit_and_rejects_invalid_base(self):
        self.assertEqual(self.run_fake(self.args()), 0)
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertEqual(report['base_commit'], subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.repo).decode().strip())
        args = self.args()
        args.out = str(self.home / 'invalid-base')
        args.base = 'not-a-real-commit'
        self.assertEqual(self.run_fake(args), 2)

    def test_export_ignore_cannot_produce_clean_base_proof(self):
        (self.repo / '.gitattributes').write_text('"a space.py" export-ignore\n')
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        subprocess.run(['git', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'attributes'], cwd=self.repo, check=True)
        self.assertEqual(self.run_fake(self.args('check')), 2)
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertIn('omitted', report['reason'])

    def test_git_reads_disable_repository_hooks_and_fsmonitor(self):
        with patch.object(self.module.subprocess, 'check_output', return_value=b'') as call:
            self.module.git(self.repo, 'ls-files')
        argv = call.call_args.args[0]
        self.assertIn('core.fsmonitor=false', argv)
        self.assertIn('core.hooksPath=/dev/null', argv)

    def test_nested_repo_argument_is_rejected_before_scanning(self):
        nested = self.repo / 'nested'
        nested.mkdir()
        args = self.args('check')
        args.repo = str(nested)
        self.assertEqual(self.run_fake(args), 2)
        self.assertFalse(self.calls)
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertIn('Git top-level', report['reason'])

    def test_default_policy_cannot_follow_external_symlink(self):
        external = self.home / 'external.yaml'
        external.write_text('modules: []\n')
        (self.repo / 'layout.yaml').unlink()
        (self.repo / 'layout.yaml').symlink_to(external)
        args = self.args()
        args.rules = None
        self.assertEqual(self.run_fake(args), 2)
        self.assertFalse(self.calls)

    def test_report_records_effective_scope_and_context_inputs(self):
        args = self.args()
        self.assertEqual(self.run_fake(args), 0)
        report = json.loads((self.home / 'evidence/report.json').read_text())
        inputs = report['inputs']
        self.assertEqual(inputs['repo'], str(self.repo.resolve()))
        self.assertEqual(inputs['root'], '.')
        self.assertEqual(inputs['language'], 'python')
        self.assertEqual(inputs['engine'], 'native')
        self.assertTrue(inputs['symbols'])
        self.assertTrue(inputs['include_tests'])
        self.assertEqual(inputs['rules'], 'layout.yaml')
        self.assertEqual(inputs['budget'], '8k')
        self.assertEqual(inputs['task'], args.task)
        self.assertEqual(inputs['files'], args.files)

    def test_explicit_python_package_is_identical_at_both_endpoints(self):
        args = self.args('check')
        args.package = 'shop'
        self.assertEqual(self.run_fake(args), 0)
        scans = [argv for argv, _ in self.calls if 'scan' in argv]
        self.assertTrue(all(argv[argv.index('--package') + 1] == 'shop' for argv in scans))
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertEqual(report['inputs']['package'], 'shop')

    def test_package_is_rejected_for_non_python(self):
        args = self.args()
        args.package = 'shop'
        args.language = 'typescript'
        self.assertEqual(self.run_fake(args), 2)
        self.assertFalse(self.calls)

    def test_prepare_retains_unscanned_seed_without_explaining_it(self):
        args = self.args()
        args.files = ['unscanned.py']
        (self.repo / 'unscanned.py').write_text('x = 1\n')
        self.assertEqual(self.run_fake(args), 0)
        self.assertFalse(any('explain' in argv for argv, _ in self.calls))
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertEqual(report['unscanned_files'], ['unscanned.py'])

    def test_check_derives_dirty_and_untracked_coverage_and_blocks_gap(self):
        (self.repo / 'a space.py').write_text('x = 2\n')
        (self.repo / 'unscanned.py').write_text('x = 1\n')
        args = self.args('check')
        args.files = []
        self.assertEqual(self.run_fake(args), 2)
        report = json.loads((self.home / 'evidence/report.json').read_text())
        self.assertEqual(report['changed_files'], ['a space.py', 'unscanned.py'])
        self.assertEqual(report['unscanned_files'], ['unscanned.py'])
        self.assertIn('coverage', report['reason'])

    def test_command_failure_is_error(self):
        with patch.object(self.module, 'resolve_binary', return_value={'binary': '/verified/archgraph'}), patch.object(self.module, 'run', side_effect=ValueError('command failed')):
            self.assertEqual(self.module.execute(self.args()), 2)

    def test_process_output_is_bounded(self):
        import sys
        with patch.object(self.module, 'LIMIT', 32), self.assertRaises(ValueError):
            self.module.run([sys.executable, '-c', "print('x' * 1000)"], self.repo, self.home / 'output')

    def test_doctor_needs_no_repository(self):
        with patch.object(self.module, 'resolve_binary', return_value={'binary': '/verified/archgraph'}):
            self.assertEqual(self.module.execute(argparse.Namespace(command='doctor')), 0)

    def test_explicit_binary_requires_hash(self):
        binary = self.home / 'archgraph'
        binary.write_text('artifact')
        with patch.dict(os.environ, {'ARCHGRAPH_BIN': str(binary), 'ARCHGRAPH_SHA256': ''}), self.assertRaises(self.module.Unavailable):
            self.module.resolve_binary()
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        with patch.dict(os.environ, {'ARCHGRAPH_BIN': str(binary), 'ARCHGRAPH_SHA256': digest}):
            self.assertEqual(self.module.resolve_binary()['binary_sha256'], digest)


if __name__ == '__main__':
    unittest.main()
