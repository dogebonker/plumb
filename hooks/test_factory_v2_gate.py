"""The v2 model tool guard rejects before candidate writes occur."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory_v2_gate import write_problem
from v2_contract import checked_path


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.root = self.home / 'repo'
        self.root.mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/code.py').write_text('sentinel')
        (self.root / 'readme.txt').write_text('read only')
        self.policy = {'schema_version': 1, 'run_id': 'run', 'slice_id': 'feature', 'root': str(self.root),
                       'owns': ['src/'], 'reads': ['readme.txt'], 'frozen': ['src/frozen.py']}
        self.policy_path = self.home / 'policy.json'
        self.policy_path.write_text(json.dumps(self.policy))

    def hook(self, request, policy=None):
        return subprocess.run([sys.executable, str(Path(__file__).with_name('factory_v2_gate.py')),
                               '--policy', str(policy or self.policy_path)], input=request,
                              text=True, capture_output=True, check=False)

    def test_permitted_reads_edits_writes_and_searches(self):
        cases = [('Write', {'file_path': 'src/new.py', 'content': 'new'}),
                 ('Edit', {'file_path': 'src/code.py', 'old_string': 'sentinel', 'new_string': 'new'}),
                 ('Read', {'file_path': str(self.root / 'readme.txt')}),
                 ('Grep', {'path': 'src', 'pattern': 'sentinel'}),
                 ('Glob', {'path': 'src/', 'pattern': '**/*.py'})]
        for name, value in cases:
            with self.subTest(name=name):
                self.assertIsNone(write_problem(self.policy, name, value))
                result = self.hook(json.dumps({'tool_name': name, 'tool_input': value, 'cwd': '/untrusted'}))
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / 'src/code.py').read_text(), 'sentinel')
        self.assertFalse((self.root / 'src/new.py').exists())

    def test_foreground_helper_is_opt_in_and_cannot_choose_a_cheaper_model(self):
        request = {'description': 'Check parser', 'prompt': 'Inspect the approved parser scope.',
                   'subagent_type': 'factory-helper'}
        self.assertIsNotNone(write_problem(self.policy, 'Agent', request))
        policy = dict(self.policy, allow_subagents=True)
        self.assertIsNone(write_problem(policy, 'Agent', request))
        self.policy_path.write_text(json.dumps(policy))
        result = self.hook(json.dumps({'tool_name': 'Agent', 'tool_input': request}))
        self.assertEqual(result.returncode, 0, result.stderr)
        for change in ({'model': 'sonnet'}, {'subagent_type': 'Explore'},
                       {'run_in_background': True}, {'isolation': 'worktree'},
                       {'tools': ['Bash']}, {'max_turns': True}):
            with self.subTest(change=change):
                self.assertIsNotNone(write_problem(policy, 'Agent', dict(request, **change)))
        self.assertIsNotNone(write_problem(policy, 'Write', {'file_path': 'readme.txt', 'content': 'x'}))
        self.assertIsNotNone(write_problem(policy, 'Write', {'file_path': 'src/frozen.py', 'content': 'x'}))

    def test_removed_source_tool_settings_and_unknown_mcp_fail_closed(self):
        for value in ('serena', None, 'other'):
            with self.subTest(value=value):
                stale = dict(self.policy, source_tool=value)
                self.assertIsNotNone(write_problem(stale, 'Read', {'file_path': 'readme.txt'}))
        for name in ('mcp__serena__initial_instructions', 'mcp__other__read_file'):
            self.assertIsNotNone(write_problem(self.policy, name, {}))

    def test_native_structured_result_has_no_file_capability(self):
        worker = {'state': 'complete', 'summary': 'Finished approved work.'}
        reviewer = {'binding': {'source_tree': 'a' * 64}, 'gate_evidence_sha256': 'b' * 64,
                    'decision': 'accept', 'findings': []}
        for value in (worker, reviewer):
            self.assertIsNone(write_problem(self.policy, 'StructuredOutput', value))
            result = self.hook(json.dumps({'tool_name': 'StructuredOutput', 'tool_input': value}))
            self.assertEqual(result.returncode, 0, result.stderr)
        for value in ({}, dict(worker, file_path='/outside'), dict(worker, state='approved'),
                      dict(reviewer, decision='reject'), {'file_path': 'src/code.py', 'content': 'destroy'}):
            self.assertIsNotNone(write_problem(self.policy, 'StructuredOutput', value))
        self.assertEqual((self.root / 'src/code.py').read_text(), 'sentinel')

    def test_native_typescript_edits_obey_ownership_and_frozen_paths(self):
        for extension in ('.ts', '.tsx', '.mts', '.cts'):
            path = 'src/module' + extension
            (self.root / path).write_text('export const value = 1;')
            value = {'file_path': path, 'old_string': '1', 'new_string': '2'}
            with self.subTest(extension=extension):
                self.assertIsNone(write_problem(self.policy, 'Edit', value))
                result = self.hook(json.dumps({'tool_name': 'Edit', 'tool_input': value}))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsNotNone(write_problem(dict(self.policy, frozen=[path]), 'Edit', value))
                self.assertIsNotNone(write_problem(dict(self.policy, owns=[]), 'Edit', value))
                self.assertEqual((self.root / path).read_text(), 'export const value = 1;')

    def test_denials_preserve_sentinel(self):
        for path in ('../outside', '/etc/passwd', 'src/../readme.txt', './src/code.py',
                     'src//code.py', '.git/config', '.claude/settings.json', '.factory/state',
                     '.software-factory/plan.yaml', 'AGENTS.md', 'src/../AGENTS.md',
                     'src/frozen.py', 'readme.txt', 'src/Code.py', 'src/co\nde.py'):
            with self.subTest(path=path):
                request = {'tool_name': 'Write', 'tool_input': {'file_path': path, 'content': 'destroy'}}
                self.assertIsNotNone(write_problem(self.policy, **request))
                result = self.hook(json.dumps(request))
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual((self.root / 'src/code.py').read_text(), 'sentinel')

    def test_links_and_nested_control_paths_are_denied(self):
        outside = self.home / 'outside'
        outside.write_text('outside sentinel')
        (self.root / 'src/symlink').symlink_to(outside)
        os.link(outside, self.root / 'src/hardlink')
        (self.root / 'src/dirlink').symlink_to(self.home, target_is_directory=True)
        for path in ('src/symlink', 'src/hardlink', 'src/dirlink/new'):
            self.assertIsNotNone(write_problem(self.policy, 'Write', {'file_path': path, 'content': 'destroy'}))
        self.assertIsNotNone(write_problem(self.policy, 'Grep', {'path': 'src', 'pattern': '.'}))
        self.assertEqual(outside.read_text(), 'outside sentinel')
        (self.root / 'src/.git').mkdir()
        self.assertIsNotNone(write_problem(self.policy, 'Glob', {'path': 'src', 'pattern': '**/*'}))

    def test_unicode_alias_write_is_denied_before_sentinel_changes(self):
        composed, decomposed = 'src/café.py', 'src/cafe\u0301.py'
        sentinel = self.root / composed
        sentinel.write_text('frozen sentinel')
        self.policy['frozen'] = [composed]
        self.policy['owns'] = [decomposed]
        request = {'tool_name': 'Write', 'tool_input': {'file_path': decomposed, 'content': 'destroy'}}
        self.assertIsNotNone(write_problem(self.policy, **request))
        self.policy_path.write_text(json.dumps(self.policy))
        self.assertEqual(self.hook(json.dumps(request)).returncode, 2)
        self.policy['owns'] = ['src/']
        self.assertIsNotNone(write_problem(self.policy, **request))
        self.assertEqual(sentinel.read_text(), 'frozen sentinel')
        with self.assertRaisesRegex(ValueError, 'NFC'):
            checked_path(self.root, decomposed)
        with self.assertRaisesRegex(ValueError, 'NFC'):
            checked_path(self.root / 'cafe\u0301', 'file')

    def test_nfc_path_accepts_decomposed_filesystem_entry_spelling(self):
        composed, decomposed = 'café.py', 'cafe\u0301.py'
        target = self.root / 'src' / composed
        target.write_text('sentinel')
        original = Path.iterdir
        def directory_entries(path):
            for entry in original(path):
                yield entry.with_name(decomposed) if entry == target else entry
        with patch.object(Path, 'iterdir', directory_entries):
            # APFS can report NFD entry names for a legitimate NFC lookup.
            self.assertIsNone(write_problem(self.policy, 'Write',
                                            {'file_path': 'src/' + composed, 'content': 'new'}))
        self.assertEqual(target.read_text(), 'sentinel')

    def test_unknown_tools_ambiguous_payloads_and_patterns_fail_closed(self):
        cases = [('Bash', {'command': 'touch x'}), ('MultiEdit', {}), ('Read', {}),
                 ('Write', {'file_path': 'src/code.py'}),
                 ('Write', {'file_path': 'src/code.py', 'content': 'x', 'path': 'other'}),
                 ('Grep', {'pattern': '.'}),
                 ('Glob', {'path': 'src', 'pattern': '../*'}),
                 ('Glob', {'path': 'src', 'pattern': '/etc/*'}),
                 ('Read', {'file_path': 'src/code.py', 'offset': True})]
        for name, value in cases:
            with self.subTest(name=name, value=value):
                self.assertIsNotNone(write_problem(self.policy, name, value))
        for request in ('{}', '[]', '{"tool_name":"Read","tool_name":"Write","tool_input":{}}',
                        '{"tool_name":"Read","tool_input":{"file_path":NaN}}'):
            self.assertEqual(self.hook(request).returncode, 2)

    def test_policy_must_be_external_explicit_and_strict(self):
        request = json.dumps({'tool_name': 'Read', 'tool_input': {'file_path': 'src/code.py'}})
        local = self.root / 'policy.json'
        local.write_text(self.policy_path.read_text())
        self.assertEqual(self.hook(request, local).returncode, 2)
        self.policy_path.write_text('{"schema_version":1,"schema_version":1}')
        self.assertEqual(self.hook(request).returncode, 2)
        self.policy['reads'].append('Src/new.py')
        self.assertIsNotNone(write_problem(self.policy, 'Read', {'file_path': 'src/code.py'}))
        self.policy['reads'].pop()
        self.policy['extra'] = 'authority'
        self.assertIsNotNone(write_problem(self.policy, 'Read', {'file_path': 'src/code.py'}))


if __name__ == '__main__':
    unittest.main()
