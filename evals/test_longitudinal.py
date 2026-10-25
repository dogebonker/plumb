"""Consecutive changes retain each arm's candidate and stop on failure."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import longitudinal


def git(work, *args):
    return subprocess.check_output(['/usr/bin/git', '-c', 'commit.gpgsign=false',
                                    '-c', 'core.hooksPath=/dev/null',
                                    '-c', 'user.name=Benchmark test', '-c', 'user.email=test@example.invalid',
                                    '-C', str(work), *args], text=True).strip()


def initialize(work):
    work.mkdir(parents=True, exist_ok=True)
    if not (work / '.git').exists():
        git(work, 'init', '-q')
        git(work, 'commit', '--allow-empty', '-qm', 'Initial test workspace')


class ChainTests(unittest.TestCase):
    def test_candidate_and_overlay_handoffs_keep_source_and_commit_only_tests(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / 'work'
            initialize(work)
            (work / 'source.py').write_text('candidate implementation')
            (work / 'history.md').write_text('actor decision history')
            (work / 'test_feature.py').write_text('initial acceptance')
            candidate = longitudinal.host_savepoint(work, phase='candidate')
            self.assertTrue(candidate['created'])
            self.assertEqual(git(work, 'status', '--porcelain'), '')
            (work / 'test_feature.py').write_text('approved next acceptance')
            overlay = longitudinal.host_savepoint(work, phase='acceptance_overlay', paths=['test_feature.py'])
            self.assertEqual(overlay['changed_files'], ['test_feature.py'])
            self.assertEqual(git(work, 'diff', '--name-only', candidate['commit'], overlay['commit']), 'test_feature.py')
            self.assertEqual((work / 'source.py').read_text(), 'candidate implementation')
            self.assertEqual((work / 'history.md').read_text(), 'actor decision history')
            self.assertIn('not approval', overlay['authority'])

    def test_savepoint_rejects_parent_repository_and_external_git_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initialize(root / 'original')
            child = root / 'original' / 'nested'
            child.mkdir()
            before = git(root / 'original', 'rev-parse', 'HEAD')
            with self.assertRaisesRegex(ValueError, 'workspace Git'):
                longitudinal.host_savepoint(child, phase='candidate')
            external = root / 'external'
            external.mkdir()
            (external / '.git').symlink_to(root / 'original/.git', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'workspace Git'):
                longitudinal.host_savepoint(external, phase='candidate')
            self.assertEqual(git(root / 'original', 'rev-parse', 'HEAD'), before)

    def test_overlay_commit_refuses_unrelated_dirty_source(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            initialize(work)
            (work / 'source.py').write_text('unrelated dirty candidate')
            (work / 'test_feature.py').write_text('next acceptance')
            before = git(work, 'rev-parse', 'HEAD')
            with self.assertRaisesRegex(ValueError, 'outside.*overlay'):
                longitudinal.host_savepoint(work, phase='acceptance_overlay', paths=['test_feature.py'])
            self.assertEqual(git(work, 'rev-parse', 'HEAD'), before)
            self.assertEqual((work / 'source.py').read_text(), 'unrelated dirty candidate')

    def test_host_rejects_actor_configured_clean_filter_before_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / 'work'
            initialize(work)
            sentinel = Path(folder) / 'filter-ran'
            filter_script = Path(folder) / 'filter.sh'
            filter_script.write_text('#!/bin/sh\ntouch "' + str(sentinel) + '"\ncat\n')
            filter_script.chmod(0o755)
            git(work, 'config', 'filter.untrusted.clean', str(filter_script))
            git(work, 'config', 'filter.untrusted.process', str(filter_script))
            (work / '.gitattributes').write_text('*.py filter=untrusted\n')
            (work / 'source.py').write_text('candidate source')
            with self.assertRaisesRegex(ValueError, 'filter'):
                longitudinal.host_savepoint(work, phase='candidate')
            self.assertFalse(sentinel.exists())
            self.assertEqual((work / 'source.py').read_text(), 'candidate source')

    def test_host_rejects_metadata_index_link_and_alternates_before_git_work(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for redirect in ('index', 'objects/info/alternates', 'commondir', 'gitdir', 'config.worktree'):
                with self.subTest(redirect=redirect):
                    work = root / redirect.replace('/', '-')
                    initialize(work)
                    target = root / 'external-data'
                    target.write_text('external data must remain unchanged')
                    path = work / '.git' / redirect
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if path.exists():
                        path.unlink()
                    if redirect == 'index':
                        path.symlink_to(target)
                    else:
                        path.write_text(str(target))
                    with self.assertRaisesRegex(ValueError, 'metadata|redirect'):
                        longitudinal.host_savepoint(work, phase='candidate')
                    self.assertEqual(target.read_text(), 'external data must remain unchanged')

    def test_host_diff_provenance_never_executes_external_diff_or_textconv(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder) / 'work'
            initialize(work)
            sentinel = Path(folder) / 'diff-ran'
            script = Path(folder) / 'diff.sh'
            script.write_text('#!/bin/sh\ntouch "' + str(sentinel) + '"\ncat\n')
            script.chmod(0o755)
            git(work, 'config', 'diff.external', str(script))
            git(work, 'config', 'diff.untrusted.textconv', str(script))
            (work / '.gitattributes').write_text('*.py diff=untrusted\n')
            (work / 'source.py').write_text('first candidate')
            longitudinal.host_savepoint(work, phase='candidate')
            (work / 'source.py').write_text('updated candidate')
            longitudinal.host_savepoint(work, phase='candidate')
            self.assertFalse(sentinel.exists())

    def test_host_rejects_include_and_core_worktree_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for key in ('include.path', 'core.worktree'):
                with self.subTest(key=key):
                    work = root / key
                    initialize(work)
                    target = root / 'external-config'
                    target.write_text('[core]\n    bare = false\n')
                    git(work, 'config', key, str(target))
                    with self.assertRaisesRegex(ValueError, 'includes|redirect'):
                        longitudinal.host_savepoint(work, phase='candidate')
                    self.assertEqual(target.read_text(), '[core]\n    bare = false\n')

    def test_synthetic_savepoint_disables_hooks_and_signing(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            initialize(work)
            sentinel = work / 'hook-ran'
            hook = work / '.git/hooks/pre-commit'
            hook.write_text('#!/bin/sh\ntouch "' + str(sentinel) + '"\nexit 1\n')
            hook.chmod(0o755)
            git(work, 'config', 'commit.gpgsign', 'true')
            git(work, 'config', 'user.signingkey', 'unavailable-test-key')
            (work / 'source.py').write_text('candidate')
            result = longitudinal.host_savepoint(work, phase='candidate')
            self.assertFalse(sentinel.exists())
            self.assertNotIn('gpgsig ', git(work, 'cat-file', 'commit', result['commit']))

    def test_chain_commits_pinned_overlay_before_next_trial(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            overlay = root / 'next-test.py'
            overlay.write_text('approved next test')
            cases = self.cases()[:2]
            cases[1].update(provide_acceptance=True, acceptance_overlays=[
                {'path': 'test_feature.py', 'source': str(overlay), 'sha256': longitudinal.pr_benchmark.sha(overlay)}])
            def host(config, case, entry, out):
                work = Path(entry['runtime']) / 'work'
                initialize(work)
                if case['id'] == '1':
                    (work / 'test_feature.py').write_text('initial test')
                    (work / 'source.py').write_text('own previous candidate')
                    (work / 'history.md').write_text('own prior decision')
                else:
                    self.assertEqual(git(work, 'status', '--porcelain'), '')
                    self.assertEqual((work / 'test_feature.py').read_text(), 'approved next test')
                    self.assertEqual((work / 'source.py').read_text(), 'own previous candidate')
                    self.assertEqual((work / 'history.md').read_text(), 'own prior decision')
                return {'status': 'complete', 'session': case['id'], 'tests': {'status': 'pass'}}
            report = longitudinal.run({'cases': cases, 'shared_context': 'facts'}, {}, root / 'evidence', trial_fn=host)
            for arm in longitudinal.pr_benchmark.ARMS:
                rows = report['arms'][arm]
                self.assertTrue(rows[0]['host_handoff']['candidate_savepoint']['created'])
                provenance = rows[1]['host_handoff']['acceptance_overlay']
                self.assertTrue(provenance['created'])
                self.assertEqual(provenance['changed_files'], ['test_feature.py'])

    def test_hardlinked_acceptance_target_holds_before_overlay_or_next_trial(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            outside = root / 'outside.py'
            outside.write_text('external original')
            overlay = root / 'next-test.py'
            overlay.write_text('new acceptance')
            cases = self.cases()[:2]
            cases[1].update(provide_acceptance=True, acceptance_overlays=[
                {'path': 'test_feature.py', 'source': str(overlay), 'sha256': longitudinal.pr_benchmark.sha(overlay)}])
            calls = []
            def host(config, case, entry, out):
                calls.append(case['id'])
                work = Path(entry['runtime']) / 'work'
                initialize(work)
                if case['id'] == '1':
                    os.link(outside, work / 'test_feature.py')
                    (work / 'source.py').write_text('own candidate')
                return {'status': 'complete', 'session': case['id'], 'tests': {'status': 'pass'}}
            with self.assertRaisesRegex(ValueError, 'hardlink'):
                longitudinal.run({'cases': cases, 'shared_context': 'facts'}, {}, root / 'evidence', trial_fn=host)
            self.assertEqual(outside.read_text(), 'external original')
            self.assertEqual(calls, ['1'])
            work = root / 'evidence-actors' / 'bare' / 'work'
            self.assertEqual((work / 'test_feature.py').read_text(), 'external original')
            report = json.loads((root / 'evidence/report.json').read_text())
            self.assertEqual(len(report['arms']['bare']), 1)
            previous = report['arms']['bare'][0]['host_handoff']['candidate_savepoint']['commit']
            self.assertEqual(git(work, 'rev-parse', 'HEAD'), previous)
            self.assertNotIn('acceptance_overlay', report['arms']['bare'][0]['host_handoff'])

    def test_failed_candidate_is_never_committed_or_overlaid(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initial = {}
            def host(config, case, entry, out):
                work = Path(entry['runtime']) / 'work'
                initialize(work)
                initial[entry['arm']] = git(work, 'rev-parse', 'HEAD')
                (work / 'source.py').write_text('stopped candidate stays dirty')
                return {'status': 'complete', 'session': case['id'], 'tests': {'status': 'assertion_failure'}}
            report = longitudinal.run({'cases': self.cases(), 'shared_context': 'facts'}, {}, root / 'evidence', trial_fn=host)
            for arm in longitudinal.pr_benchmark.ARMS:
                work = root / 'evidence-actors' / arm / 'work'
                self.assertEqual(git(work, 'rev-parse', 'HEAD'), initial[arm])
                self.assertEqual((work / 'source.py').read_text(), 'stopped candidate stays dirty')
                self.assertTrue(git(work, 'status', '--porcelain'))
                self.assertEqual(report['arms'][arm][0]['host_handoff'], {})
                self.assertEqual(report['arms'][arm][1]['status'], 'not_run_inherited_failure')

    def test_costs_use_final_cumulative_task_usage_and_separate_probe(self):
        def host(config, case, entry, out):
            initialize(Path(entry['runtime']) / 'work')
            return {'status': 'complete', 'session': case['id'], 'tests': {'status': 'pass'},
                    'attempts': [{'usage': {'tokens': 100, 'cost_usd': .2}},
                                 {'usage': {'tokens': 250, 'cost_usd': .5}}],
                    'task_seconds': 12.5, 'probe_usage': {'tokens': 11, 'cost_usd': .03},
                    'probe_seconds': 5, 'seconds': 17.5, 'observed_tokens': 261, 'cost_usd': 999}
        with tempfile.TemporaryDirectory() as folder:
            report = longitudinal.run({'cases': self.cases(), 'shared_context': 'facts'}, {},
                                      Path(folder) / 'evidence', trial_fn=host)
        row = report['arms']['bare'][0]
        self.assertEqual((row['tokens'], row['cost_usd'], row['seconds']), (250, .5, 12.5))
        self.assertEqual(row['probe_usage'], {'tokens': 11, 'cost_usd': .03})
        self.assertEqual(row['probe_seconds'], 5)
        self.assertEqual(row['result']['observed_tokens'], 261)
        self.assertEqual(row['result']['cost_usd'], 999)

    def test_unknown_task_cost_does_not_become_known_probe_cost(self):
        def host(config, case, entry, out):
            return {'status': 'timeout', 'attempts': [{'usage': {'tokens': None, 'cost_usd': None}}],
                    'task_seconds': None, 'probe_usage': {'tokens': 11, 'cost_usd': .03},
                    'probe_seconds': 5, 'observed_tokens': 11}
        with tempfile.TemporaryDirectory() as folder:
            report = longitudinal.run({'cases': self.cases(), 'shared_context': 'facts'}, {},
                                      Path(folder) / 'evidence', trial_fn=host)
        row = report['arms']['bare'][0]
        self.assertIsNone(row['tokens'])
        self.assertIsNone(row['cost_usd'])
        self.assertIsNone(row['seconds'])
        self.assertEqual(row['probe_usage'], {'tokens': 11, 'cost_usd': .03})

    def test_actual_assertion_failure_is_a_measured_correctness_failure(self):
        self.assertEqual(longitudinal.scores({'status': 'complete', 'tests': {'status': 'assertion_failure'}})['correctness'], 'fail')

    def cases(self):
        return [{'id': str(i), 'base_commit': str(i) * 40, 'reference_commit': str(i + 1) * 40,
                 'pr': {'title': 'feature', 'body': ''}, 'prepared_dir': '/unused', 'acceptance_files': ['test_feature.py']} for i in range(1, 4)]

    def test_chain_rejects_disconnected_references(self):
        cases = self.cases()
        cases[1]['base_commit'] = 'f' * 40
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            longitudinal.validate_chain({'cases': cases, 'shared_context': 'standing decisions'})

    def test_all_arms_share_facts_and_keep_their_own_previous_workspace(self):
        calls = []
        def host(config, case, entry, out):
            work = Path(entry['runtime']) / 'work'
            initialize(work)
            marker = work / 'previous'
            self.assertEqual(git(work, 'status', '--porcelain'), '')
            calls.append((entry['arm'], marker.read_text() if marker.exists() else None,
                          case['pr']['body']))
            marker.write_text(case['id'])
            return {'status': 'complete', 'session': case['id'], 'source_sha256': case['id'], 'workspace': str(work),
                    'tests': {'status': 'pass'}, 'archgraph': {'status': 'no_new_violations'}}
        with tempfile.TemporaryDirectory() as folder:
            result = longitudinal.run({'cases': self.cases(), 'shared_context': 'standing decisions'},
                                      {}, Path(folder) / "evidence", trial_fn=host)
        self.assertEqual(len(calls), 9)
        self.assertEqual([c[1] for c in calls[:3]], [None, '1', '2'])
        self.assertTrue(all('standing decisions' in c[2] for c in calls))
        self.assertEqual(result['arms']['factory'][0]['scores']['history'], 'unmeasured')
        self.assertEqual(result['arms']['factory'][0]['scores']['architecture'], 'unmeasured')

    def test_failure_halts_without_reset_and_marks_inherited_steps(self):
        calls = []
        def host(config, case, entry, out):
            calls.append(case['id'])
            return {'status': 'timeout', 'source_sha256': 'failed-candidate'}
        with tempfile.TemporaryDirectory() as folder:
            result = longitudinal.run({'cases': self.cases(), 'shared_context': 'facts'}, {}, Path(folder) / "evidence", trial_fn=host)
        self.assertEqual(calls, ['1', '1', '1'])
        self.assertEqual(result['arms']['bare'][1]['status'], 'not_run_inherited_failure')
        self.assertEqual(result['arms']['bare'][0]['result']['source_sha256'], 'failed-candidate')

    def test_reused_session_is_not_completion(self):
        def host(config, case, entry, out):
            initialize(Path(entry['runtime']) / 'work')
            return {'status': 'complete', 'session': 'same', 'tests': {'status': 'pass'}}
        with tempfile.TemporaryDirectory() as folder:
            result = longitudinal.run({'cases': self.cases(), 'shared_context': 'facts'}, {},
                                      Path(folder) / 'evidence', trial_fn=host)
        self.assertEqual(result['arms']['bare'][1]['status'], 'fresh_session_unverified')
        self.assertEqual(result['arms']['bare'][2]['status'], 'not_run_inherited_failure')

    def test_history_is_not_credited_without_evidence(self):
        def host(config, case, entry, out):
            initialize(Path(entry['runtime']) / 'work')
            return {'status': 'complete', 'session': case['id'], 'tests': {'status': 'pass'}}
        with tempfile.TemporaryDirectory() as folder, self.assertRaisesRegex(ValueError, 'requires semantic/mechanical evidence'):
            longitudinal.run({'cases': self.cases(), 'shared_context': 'facts'}, {},
                                 Path(folder) / 'evidence', trial_fn=host,
                                 score_fn=lambda *args: {'history': {'verdict': 'pass'}})

    def test_later_acceptance_cannot_silently_reuse_old_tests(self):
        cases = self.cases()
        cases[1]['provide_acceptance'] = True
        def host(config, case, entry, out):
            initialize(Path(entry['runtime']) / 'work')
            return {'status': 'complete', 'session': case['id'], 'tests': {'status': 'pass'}}
        with tempfile.TemporaryDirectory() as folder, self.assertRaisesRegex(ValueError, 'every later immutable acceptance'):
            longitudinal.run({'cases': cases, 'shared_context': 'facts'}, {},
                                 Path(folder) / 'evidence', trial_fn=host)
