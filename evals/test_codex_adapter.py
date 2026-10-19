import json
import os
import platform
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import codex_adapter as adapter


class AdapterTests(unittest.TestCase):
    def test_role_pin_preserves_instructions_and_only_changes_execution_defaults(self):
        source = 'name="executor"\nmodel="old"\nmodel_reasoning_effort="medium"\ndeveloper_instructions="""\nmodel="instruction example"\nKeep the actual role guidance.\n"""\n'
        frozen = adapter.pin_role_text(source, 'gpt-6.1-sol', 'high')
        self.assertIn('model = "gpt-6.1-sol"', frozen)
        self.assertIn('model_reasoning_effort = "high"', frozen)
        self.assertIn('model="instruction example"', frozen)
        self.assertIn('Keep the actual role guidance.', frozen)
        self.assertEqual(adapter.pin_role_text('developer_instructions="role"\n', 'm', 'high'),
                         'model_reasoning_effort = "high"\nmodel = "m"\ndeveloper_instructions="role"\n')
        ambiguous = 'developer_instructions="""\nmodel="example"\n"""\nmodel="old"\n'
        with self.assertRaisesRegex(ValueError, 'outside model/effort'):
            adapter.pin_role_text(ambiguous, 'm', 'high')

    def test_installed_role_discovery_is_recursive_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            nested = home / 'agents/nested'
            nested.mkdir(parents=True)
            source = nested / 'implementation.toml'
            valid = 'name="executor"\ndescription="Implementation role"\ndeveloper_instructions="keep me"\n'
            source.write_text(valid)
            self.assertEqual(adapter.installed_role_sources(home), {'executor': source})
            for malformed in ('name=', 'name="executor"', 'name="unsafe.role"\ndescription="Role"'):
                with self.subTest(malformed=malformed):
                    source.write_text(malformed)
                    with self.assertRaises(ValueError):
                        adapter.installed_role_sources(home)
            source.write_text(valid)
            duplicate = home / 'agents/duplicate.toml'
            duplicate.write_text(valid)
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                adapter.installed_role_sources(home)
            duplicate.unlink()
            (home / 'agents/link.toml').symlink_to(source)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                adapter.installed_role_sources(home)

    def test_prepare_wires_bounded_role_snapshot_and_resume_tamper_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / 'work'
            work.mkdir()
            source = root / 'executor.toml'
            source.write_text('name="executor"\ndescription="Implementation role"\nmodel_reasoning_effort="medium"\ndeveloper_instructions="keep me"\n')
            with patch.object(adapter, 'installed_role_sources', return_value={'executor': source}), patch.object(adapter, 'probe_isolation', return_value=[]), patch.object(adapter, 'probe_network', return_value=[]):
                prepared = adapter.prepare('codex', work, root / 'runtime', [], [], 'gpt-6.1-sol', 'high')
            self.assertEqual(prepared['role_preset']['covered_roles'], ['executor'])
            self.assertFalse(prepared['role_preset']['complete_effective_inventory_verified'])
            self.assertFalse(prepared['role_preset']['uniform_effort_enforced'])
            pin = prepared['role_pins']['executor']
            self.assertIn('agents.executor.config_file=' + json.dumps(pin['config_file']), prepared['config_args'])
            self.assertEqual(pin['source_sha256'], adapter.hashlib.sha256(source.read_bytes()).hexdigest())
            command = adapter.command(prepared, 'continue', 'session')
            self.assertIn('agents.executor.config_file=' + json.dumps(pin['config_file']), command)
            frozen = Path(pin['config_file'])
            frozen.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'writable'):
                adapter.command(prepared, 'continue', 'session')

    def test_role_freeze_ignores_later_installed_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'executor.toml'
            source.write_text('name="executor"\ndescription="Implementation role"\nmodel="old"\nmodel_reasoning_effort="medium"\ndeveloper_instructions="keep me"\n')
            runtime = root / 'runtime'
            runtime.mkdir()
            pins = adapter.freeze_role_sources(runtime, {'executor': source}, 'gpt-6.1-sol', 'high')
            frozen = Path(pins['executor']['config_file'])
            source.write_text('model="changed later"\ndeveloper_instructions="different"\n')
            self.assertIn('model_reasoning_effort = "high"', frozen.read_text())
            self.assertIn('developer_instructions="keep me"', frozen.read_text())
            adapter.verify_role_pins({'role_pins': pins})
            self.assertEqual(frozen.stat().st_mode & 0o222, 0)
            self.assertEqual(frozen.parent.stat().st_mode & 0o222, 0)
            with self.assertRaises(FileExistsError):
                adapter.freeze_role_sources(runtime, {'executor': source}, 'm', 'low')

    def test_role_freeze_rejects_changed_source_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'executor.toml'
            source.write_text('name="writer"\ndescription="Changed role"\n')
            runtime = root / 'runtime'
            runtime.mkdir()
            with self.assertRaisesRegex(ValueError, 'metadata changed'):
                adapter.freeze_role_sources(runtime, {'executor': source}, 'm', 'high')

    def test_role_freeze_rejects_name_removed_after_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / 'home'
            source = home / 'agents/executor.toml'
            source.parent.mkdir(parents=True)
            source.write_text('name="executor"\ndescription="Implementation role"\ndeveloper_instructions="role"\n')
            sources = adapter.installed_role_sources(home)
            source.write_text('developer_instructions="role"\n')
            runtime = root / 'runtime'
            runtime.mkdir()
            with self.assertRaisesRegex(ValueError, 'metadata changed'):
                adapter.freeze_role_sources(runtime, sources, 'm', 'high')

    @unittest.skipUnless(shutil.which('codex'), 'requires installed Codex CLI')
    def test_role_override_passes_strict_config_without_model_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'executor.toml'
            source.write_text('name="executor"\ndescription="Implementation role"\nmodel="old"\nmodel_reasoning_effort="medium"\ndeveloper_instructions="keep me"\n')
            runtime = root / 'runtime'
            runtime.mkdir()
            pins = adapter.freeze_role_sources(runtime, {'executor': source}, 'gpt-6.1-sol', 'high')
            override = 'agents.executor.config_file=' + json.dumps(pins['executor']['config_file'])
            result = subprocess.run([shutil.which('codex'), 'exec', '--strict-config', '--ignore-user-config',
                                     '--ignore-rules', '--skip-git-repo-check', '-C', str(root), '-c', override,
                                     '--output-schema', str(root / 'missing-schema.json'),
                                     'No model request: missing schema admission probe'],
                                    capture_output=True, text=True, check=False, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Failed to read output schema file', result.stderr)
            self.assertNotIn('Error loading config.toml', result.stderr)
            self.assertNotIn('Ignoring malformed agent role definition', result.stderr)

    def test_frozen_role_tamper_rejects_command(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'executor.toml'
            path.write_text('model="m"\n')
            prepared = {'role_pins': {'executor': {'config_file': str(path),
                        'sha256': adapter.hashlib.sha256(path.read_bytes()).hexdigest()}}}
            path.chmod(0o444)
            adapter.verify_role_pins(prepared)
            path.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'writable'):
                adapter.command(prepared, 'unused')
            path.write_text('model="tampered"\n')
            path.chmod(0o444)
            with self.assertRaisesRegex(ValueError, 'modified'):
                adapter.command(prepared, 'unused')

    def test_response_usage_not_cumulative_or_fork_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'root.jsonl'
            context = {'type': 'turn_context', 'payload': {'turn_id': 't', 'model': 'gpt-6.1-sol', 'effort': 'high'}}
            def response(thread, identity, tokens):
                return {'type': 'token_usage_record', 'payload': {'session_id': 'root', 'thread_id': thread,
                    'response_id': identity, 'turn_id': 't', 'usage': {'input_tokens': tokens,
                    'cached_input_tokens': 10, 'cache_write_input_tokens': 20, 'output_tokens': 5,
                    'reasoning_output_tokens': 4}, 'thread_token_usage': {'input_tokens': 99999}}}
            events = [context, response('root', 'a', 100), response('root', 'b', 200),
                      response('root', 'a', 100), response('child', 'c', 100)]
            path.write_text('\n'.join(map(json.dumps, events)))
            result = adapter.normalize_usage('root', [path], ['root', 'child'])
            self.assertTrue(result['accounting_complete'])
            self.assertEqual(result['response_count'], 3)
            self.assertEqual(result['totals']['input_tokens'], 400)
            self.assertEqual(result['totals']['output_tokens'], 15)
            self.assertAlmostEqual(result['modeled_api_usd'], .000923)

    def test_missing_write_counts_are_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'root.jsonl'
            path.write_text(json.dumps({'type': 'token_usage_record', 'payload': {
                'session_id': 'root', 'thread_id': 'root', 'response_id': 'a', 'usage': {
                    'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 1}}}))
            result = adapter.normalize_usage('root', [path], ['root', 'child'])
            self.assertFalse(result['accounting_complete'])
            self.assertIsNone(result['modeled_api_usd'])
            self.assertIn('missing_thread_usage:child', result['problems'])

    def test_resume_preserves_config_and_schema(self):
        prepared = {'binary': 'codex', 'model': 'gpt-6.1-sol', 'work': '/work',
                    'schema_path': '/schema', 'response_path': '/response',
                    'config_args': ['-c', 'default_permissions="bench"']}
        command = adapter.command(prepared, 'continue', 'session')
        self.assertEqual(command[:4], ['codex', 'exec', 'resume', 'session'])
        self.assertIn('--ignore-user-config', command)
        self.assertNotIn('--sandbox', command)
        self.assertNotIn('-C', command)

    def test_observer_reads_children_and_retains_accounting_records(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home / 'root.jsonl'
            child = home / 'child.jsonl'
            def write(path, thread, parent=None):
                source = {'subagent': {'thread_spawn': {'parent_thread_id': parent}}} if parent else 'cli'
                events = [{'type': 'session_meta', 'payload': {'id': thread, 'source': source, 'timestamp': '1970-01-01T00:00:01Z'}},
                          {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': thread, 'started_at': 1}},
                          {'type': 'turn_context', 'payload': {'turn_id': thread, 'model': 'gpt-6.1-sol', 'effort': 'high'}},
                          {'type': 'token_usage_record', 'payload': {'session_id': 'root', 'thread_id': thread,
                           'response_id': thread, 'turn_id': thread, 'usage': {'input_tokens': 100,
                           'cached_input_tokens': 0, 'cache_write_input_tokens': 0, 'output_tokens': 1}}},
                          {'type': 'event_msg', 'payload': {'type': 'task_complete', 'turn_id': thread}}]
                path.write_text('\n'.join(map(json.dumps, events)))
            write(root, 'root')
            write(child, 'child', 'root')
            with sqlite3.connect(home / 'state_5.sqlite') as db:
                db.execute('CREATE TABLE threads(id TEXT, rollout_path TEXT, created_at INTEGER)')
                db.execute('CREATE TABLE thread_spawn_edges(parent_thread_id TEXT, child_thread_id TEXT, status TEXT)')
                db.executemany('INSERT INTO threads VALUES(?,?,?)', [('root', str(root), 1), ('child', str(child), 2)])
                db.execute("INSERT INTO thread_spawn_edges VALUES('root','child','open')")
            result = adapter.collect_usage('root', home / 'artifacts', home)
            self.assertTrue(result['accounting_complete'])
            self.assertEqual(result['response_count'], 2)
            self.assertTrue((home / 'artifacts/rollout-accounting.jsonl').is_file())
            with sqlite3.connect(home / 'state_5.sqlite') as db:
                db.execute('DELETE FROM thread_spawn_edges')
            result = adapter.collect_usage('root', home / 'artifacts', home)
            self.assertEqual(result['response_count'], 2)
            self.assertTrue(result['accounting_complete'])
            self.assertEqual(result['lifecycle']['child']['state'], 'complete')

    def test_lifecycle_rejects_running_error_interruption_and_truncation(self):
        meta = {'type': 'session_meta', 'payload': {'id': 'child', 'timestamp': '1970-01-01T00:00:01Z'}}
        start = {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': 'own', 'started_at': 1}}
        usage = {'type': 'token_usage_record', 'payload': {'thread_id': 'child', 'turn_id': 'own'}}
        complete = {'type': 'event_msg', 'payload': {'type': 'task_complete', 'turn_id': 'own'}}
        cases = [([meta, start, usage, complete], 'complete'),
                 ([meta, start, usage], 'running'),
                 ([meta, start, usage, {'type': 'event_msg', 'payload': {'type': 'error'}} , complete], 'error'),
                 ([meta, start, usage, {'type': 'event_msg', 'payload': {'type': 'turn_aborted', 'turn_id': 'own'}}], 'interrupted'),
                 ([meta, start, usage, complete, {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': 'next', 'started_at': 2}}], 'running'),
                 ([meta, start, usage, complete, {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': 'next'}}], 'missing_start_metadata'),
                 ([meta, start, usage, complete, {'type': 'event_msg', 'payload': {'type': 'task_started', 'started_at': 2}}], 'missing_start_metadata'),
                 ([meta, start, usage, complete, {'type': 'token_usage_record', 'payload': {'thread_id': 'child', 'turn_id': 'next'}}], 'missing_start_metadata'),
                 ([start, usage, complete], 'missing_ownership')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'child.jsonl'
            for events, expected in cases:
                with self.subTest(expected=expected, events=len(events)):
                    path.write_text('\n'.join(map(json.dumps, events)))
                    self.assertEqual(adapter.lifecycle_status('child', path)['state'], expected)
            path.write_text('\n'.join(map(json.dumps, [meta, start, usage, complete])) + '\n{"truncated":')
            self.assertEqual(adapter.lifecycle_status('child', path)['state'], 'missing_or_truncated')
            self.assertEqual(adapter.lifecycle_status('child', Path(directory) / 'absent')['state'], 'missing_or_truncated')

    def test_inherited_parent_terminal_does_not_complete_child(self):
        events = [{'type': 'session_meta', 'payload': {'id': 'child', 'timestamp': '1970-01-01T00:00:02Z'}},
                  {'type': 'session_meta', 'payload': {'id': 'parent', 'timestamp': '1970-01-01T00:00:01Z'}},
                  {'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': 'parent-turn', 'started_at': 2}},
                  {'type': 'token_usage_record', 'payload': {'thread_id': 'parent', 'turn_id': 'parent-turn'}},
                  {'type': 'event_msg', 'payload': {'type': 'task_complete', 'turn_id': 'parent-turn'}}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'child.jsonl'
            path.write_text('\n'.join(map(json.dumps, events)))
            self.assertNotEqual(adapter.lifecycle_status('child', path)['state'], 'complete')
            events.insert(3, {'type': 'token_usage_record', 'payload': {'thread_id': 'child', 'turn_id': 'own-turn'}})
            path.write_text('\n'.join(map(json.dumps, events)))
            self.assertNotEqual(adapter.lifecycle_status('child', path)['state'], 'complete')

    @unittest.skipUnless(platform.system() == 'Darwin' and shutil.which('codex'), 'requires native Codex sandbox')
    def test_live_filesystem_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work, active = root / 'work', root / 'active'
            work.mkdir()
            active.mkdir()
            subprocess.run(['git', 'init', '-q', str(work)], check=True)
            (active / 'SKILL.md').write_text('active workflow')
            private = root / 'private.txt'
            private.write_text('guard')
            prepared = adapter.prepare('codex', work, root / 'runtime', [active], [private],
                                       'gpt-6.1-sol', 'high', dependency_setup=True)
            self.assertTrue(all(probe['passed'] for probe in prepared['isolation_evidence']))
            config = '\n'.join(prepared['config_args'])
            self.assertIn('registry.npmjs.org', config)
            self.assertIn('shell_environment_policy.inherit="core"', config)
            result = subprocess.run([shutil.which('codex'), 'sandbox', '-P', 'bench', '-C', str(work),
                                     *prepared['config_args'], '--', '/usr/bin/git',
                                     '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@example.invalid',
                                     'commit', '--allow-empty', '-m', 'probe'],
                                    env=dict(os.environ, **prepared['shell_environment']),
                                    capture_output=True, check=False, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    @unittest.skipUnless(platform.system() == 'Darwin' and shutil.which('codex') and os.environ.get('PLAYWRIGHT_MODULE'), 'requires installed browser and Codex')
    def test_live_broker_admission_with_failing_public_baseline(self):
        from browser_runtime import prepare_browser_check
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / 'work'
            work.mkdir()
            baseline = work / 'test_baseline.cjs'
            baseline.write_text("require('node:test')('baseline',()=>require('node:assert').ok(false));")
            browser = prepare_browser_check(root / 'browser', work, [], codex_sandbox=True)
            prepared = adapter.prepare('codex', work, root / 'runtime', [], [], 'gpt-6.1-sol', 'high', browser)
            self.assertTrue(all(probe['passed'] for probe in prepared['isolation_evidence']))
            proof = prepared['isolation_evidence'][-1]
            self.assertEqual(proof['public_test_exit'], 1)
            self.assertTrue(Path(proof['log']).is_file())
            self.assertEqual(list(work.glob('test_*.cjs')), [baseline])

    def test_browser_summary_does_not_admit_failed_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / 'work'
            work.mkdir()
            browser = {'command': str(root / 'browser/browser-check'), 'mcp_bridge': '/bridge',
                       'enforcement': 'native_seatbelt_mcp_capability',
                       'runtimeproof': {'module': '/fake/playwright'}}
            log = work / '.tmp/browser-check/raw.log'
            log.parent.mkdir(parents=True)
            log.write_text('not ok 1 - codex-admission-fixed')
            responses = [{'id': 2, 'result': {'tools': [{'name': 'check'}, {'name': 'red_check'}]}},
                         {'id': 3, 'result': {'content': [{'text': json.dumps({'exit_code': 1,
                          'output': 'Browser check exit: 1\nRaw log: ' + str(log)})}]}}]
            with patch.object(adapter, 'probe_isolation', return_value=[]), patch.object(adapter, 'probe_network', return_value=[]), patch.object(adapter.subprocess, 'run') as run, patch.object(adapter.uuid, 'uuid4') as identity:
                identity.return_value.hex = 'fixed'
                run.return_value.stdout = '\n'.join(map(json.dumps, responses))
                run.return_value.stderr = ''
                with self.assertRaisesRegex(ValueError, 'browser capability admission failed'):
                    adapter.prepare('codex', work, root / 'runtime', [], [], 'gpt-6.1-sol', 'high', browser)
            self.assertFalse((work / 'test_codex-admission-fixed.cjs').exists())
            self.assertTrue((root / 'runtime/browser-admission.log').is_file())

    def test_failed_boundary_rejects_prepare(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(adapter.subprocess, 'run') as run:
            run.return_value.returncode = 0
            with self.assertRaisesRegex(ValueError, 'home_read_denied'):
                adapter.prepare('codex', directory, Path(directory) / 'runtime', [], [], 'gpt-6.1-sol', 'high')


if __name__ == '__main__':
    unittest.main()
