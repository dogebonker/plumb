"""Real Git source changes through the CLI; scripted inference, no model usage."""
import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from plumb.__main__ import main
from plumb.test_core import Script, response


class ConnectedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.workspace = self.root / 'module'
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/main.py').write_text('value = 1\n')
        (self.repo / 'decision.md').write_text('# Intent\nThe value must be two.\n')
        self.commit()
        code, result, _ = self.command('init', str(self.workspace), '--repo', str(self.repo),
            '--module', 'Example', '--code', 'src', '--source', 'decision.md', '--section', 'Intent')
        self.assertEqual((code, result['status']), (0, 'current'))

    def git(self, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        return subprocess.check_output(['git', '-c', 'core.hooksPath=' + os.devnull,
            '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args], env=env,
            stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def command(self, *arguments, actor=None):
        output, errors = io.StringIO(), io.StringIO()
        model = Mock(side_effect=actor if actor else AssertionError('Unexpected model call'))
        model.usage.return_value = {'calls': 0, 'tokens': 0, 'unknown': False}
        model.last_receipt = None
        with patch('sys.argv', ['plumb', *arguments]), \
                patch('plumb.__main__.ClaudeModel', return_value=model) as factory, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = main()
        return code, json.loads(output.getvalue()) if output.getvalue() else errors.getvalue(), factory

    def actor(self, word='two', edit=False):
        terminal = response(outcome='code_wrong', explanation='Value differs from selected intent.',
            question='Should code follow the selected intent?', evidence=[
                {'path': 'code/src/main.py', 'quote': 'value = 1'},
                {'path': 'sources/decision.md', 'quote': f'The value must be {word}.'}])
        if edit:
            terminal['edits'] = [{'path': 'code/src/main.py', 'old': 'value = 1',
                'new': 'value = ' + ('2' if word == 'two' else '3'), 'reason': 'Explicit code choice.'}]
        return Script(response('inspect', reads=[{'path': path, 'start_line': 0, 'end_line': 0}
            for path in ['code/src/main.py', 'sources/decision.md']]), terminal)

    def check(self, word='two'):
        return self.command('check', str(self.workspace), '--source-repo', str(self.repo),
            '--decision', 'Use the selected committed intent.', '--output', str(self.root / 'report.json'),
            '--receipts', str(self.root / 'receipts'), actor=self.actor(word))

    def propose(self, word='two'):
        return self.command('propose', str(self.root / 'report.json'), '--choice', 'code',
            '--source-repo', str(self.repo), '--output', str(self.root / 'proposal.json'),
            '--receipts', str(self.root / 'receipts'), actor=self.actor(word, edit=True))

    def test_source_commit_blocks_old_correction_until_refresh_and_recheck(self):
        self.assertEqual(self.check()[0], 1)
        report = json.loads((self.root / 'report.json').read_text())
        self.assertEqual(report['upstream_freshness'], 'version_checked')
        self.assertEqual(report['source_scope'], 'local_git_ref')
        self.assertEqual(self.propose()[0], 0)
        before = {p: p.read_bytes() for p in self.workspace.rglob('*')
                  if p.is_file() and 'sources' not in p.parts}
        (self.repo / 'decision.md').write_text('# Intent\nThe value must be three.\n')
        self.commit()
        self.assertEqual(self.command('status', str(self.workspace), '--repo', str(self.repo))[0], 1)
        code, error, _ = self.command('apply', str(self.root / 'proposal.json'), '--repo', str(self.repo))
        self.assertEqual(code, 2)
        self.assertIn('changed', error)
        code, _, factory = self.check('three')
        self.assertEqual(code, 2)
        factory.assert_not_called()
        code, _, factory = self.propose('three')
        self.assertEqual(code, 2)
        factory.assert_not_called()
        code, result, _ = self.command('refresh', str(self.workspace), '--repo', str(self.repo))
        self.assertEqual((code, result['status']), (0, 'updated'))
        self.assertFalse(result['knowledge_updated'])
        self.assertTrue(result['review_required'])
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        code, error, _ = self.command('apply', str(self.root / 'proposal.json'), '--repo', str(self.repo))
        self.assertEqual(code, 2)
        self.assertIn('stale', error)
        self.assertEqual(self.check('three')[0], 1)
        self.assertEqual(self.propose('three')[0], 0)
        capture = (self.workspace / 'sources/decision.md').read_bytes()
        code, result, _ = self.command('apply', str(self.root / 'proposal.json'), '--repo', str(self.repo))
        self.assertEqual((code, result['status']), (0, 'applied'))
        self.assertEqual(result['source_scope'], 'local_git_ref')
        self.assertEqual((self.workspace / 'code/src/main.py').read_text(), 'value = 3\n')
        self.assertEqual((self.repo / 'src/main.py').read_text(), 'value = 1\n')
        self.assertEqual((self.workspace / 'sources/decision.md').read_bytes(), capture)
        self.assertEqual(self.command('apply', str(self.root / 'proposal.json'), '--repo', str(self.repo))[1]['status'], 'already_applied')

    def test_explicit_repository_and_bound_report_required_before_inference(self):
        code, error, factory = self.command('check', str(self.workspace),
            '--output', str(self.root / 'report.json'), '--receipts', str(self.root / 'receipts'))
        self.assertEqual(code, 2)
        self.assertIn('--source-repo', error)
        factory.assert_not_called()
        self.assertEqual(self.check()[0], 1)
        report_path = self.root / 'report.json'
        report = json.loads(report_path.read_text())
        report.pop('source_binding')
        report_path.write_text(json.dumps(report))
        code, error, factory = self.propose()
        self.assertEqual(code, 2)
        self.assertIn('fresh connected check', error)
        factory.assert_not_called()
