"""Executable ADR paths: missing enforcement, draft conflict and held drift."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from kit import adr


class ADRTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.put('source.py', 'amount = 1.0\n')
        self.put('test_money.py', 'def test_integer_money(): pass\n')
        self.put('.plumb/system/adr/0007-money.md',
                 '# 0007 Money\nStatus: accepted\nContext: source.py\n'
                 'Decision: Money is never a float.\nEnforced by: test: test_integer_money\n')
        self.put('.plumb/system/constraints.md',
                 '| ID | Kind | Statement | Fit criterion | Source | Enforced by |\n'
                 '| SYS-C-01 | Constraint | No floats | integer | setup | human-verified |\n')
        self.draft = '.plumb/changes/demo/02-architecture.md'
        self.put(self.draft, '# Architecture\n## Decisions\n### Money\nSupersedes: none\n'
                 'Decision: Store money as a float.\n## Open questions\n')
        self.put('.plumb/changes/demo/status.yaml',
                 'gates:\n  architecture: { state: pending }\n')
        self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def put(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def manifest(self):
        return {'head': self.git('rev-parse', 'HEAD'), 'checks': [{
            'kind': 'test', 'name': 'test_integer_money',
            'defined_in': [{'path': 'test_money.py', 'symbol': 'test_integer_money'}],
            'argv': ['python3', '-c', 'pass'], 'cwd': '.', 'timeout': 5}]}

    def test_missing_named_check_blocks_and_existing_check_passes(self):
        empty = {'head': self.git('rev-parse', 'HEAD'), 'checks': []}
        self.assertFalse(adr.check(self.repo, empty)['ready'])
        self.assertTrue(adr.check(self.repo, self.manifest())['ready'])
        m = self.manifest()
        m['checks'][0]['defined_in'][0]['symbol'] = 'test_missing'
        self.assertFalse(adr.check(self.repo, m)['ready'])

    def cards(self):
        inventory = adr.inventory(self.repo)
        return {'inventory_sha256': adr.digest(inventory), 'drafts': {
            self.draft: hashlib.sha256((self.repo / self.draft).read_bytes()).hexdigest()},
            'conflicts': [{'anchor': 'ADR 0007', 'draft': self.draft,
                           'standing_quote': 'Money is never a float.',
                           'draft_quote': 'Store money as a float.', 'reason': 'Contradictory representation.'}]}

    def test_conflict_opens_question_and_approval_summary_without_editing_approved(self):
        result = adr.conformance(self.repo, [self.draft], self.cards())
        self.assertFalse(result['ready'])
        self.assertIn('supersedes ADR 0007 or withdraw', (self.repo / self.draft).read_text())
        self.assertIn('ADR 0007', result['approval_summary'][0])
        original = (self.repo / self.draft).read_bytes()
        self.put('.plumb/changes/demo/status.yaml',
                 'gates:\n  architecture: { state: approved }\n')
        with self.assertRaisesRegex(ValueError, 'approved'):
            adr.conformance(self.repo, [self.draft], self.cards())
        self.assertEqual(original, (self.repo / self.draft).read_bytes())

    def test_stale_or_wrong_anchor_cards_fail_without_writing(self):
        original = (self.repo / self.draft).read_bytes()
        cards = self.cards()
        cards['conflicts'][0]['standing_quote'] = 'invented'
        with self.assertRaises(ValueError):
            adr.conformance(self.repo, [self.draft], cards)
        self.assertEqual(original, (self.repo / self.draft).read_bytes())
        cards = self.cards()
        cards['inventory_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            adr.conformance(self.repo, [self.draft], cards)

    def test_drift_writes_each_adr_and_holds_contradiction(self):
        path = self.repo / '.plumb/system/adr/0007-money.md'
        path.write_text(path.read_text().replace('test: test_integer_money', 'human-verified'))
        self.commit()
        output = self.repo / '.plumb/changes/demo/drift.md'
        human = {'inventory_sha256': adr.digest(adr.inventory(self.repo)), 'adrs': [{
            'id': '0007', 'verdict': 'drifted', 'path': 'source.py', 'line': 1,
            'quote': 'amount = 1.0', 'reason': 'The value is a float.'}]}
        report = adr.drift(self.repo, {'head': self.git('rev-parse', 'HEAD'), 'checks': []}, human, output)
        self.assertFalse(report['ready'])
        self.assertEqual(report['held'], ['0007'])
        self.assertIn('ADR 0007 | drifted', output.read_text())
        self.assertIn('accept drift with a reason', output.read_text())
        human['adrs'][0]['quote'] = 'invented'
        with self.assertRaises(ValueError):
            adr.drift(self.repo, {'head': self.git('rev-parse', 'HEAD'), 'checks': []}, human, output)

    def test_small_only_validates_covers_ids(self):
        self.draft = '.plumb/changes/demo/04-slices.md'
        self.put(self.draft, '# Slices\nCovers: SYS-C-99\n')
        self.put('.plumb/changes/demo/status.yaml',
                 'track: small\ngates:\n  slices: { state: pending }\n')
        result = adr.conformance(self.repo, [self.draft], None, small=True)
        self.assertFalse(result['ready'])
        self.assertIn('SYS-C-99', result['approval_summary'][0])

    def test_manifest_staleness_dirty_source_and_unknown_verdict_fail_closed(self):
        m = self.manifest()
        m['head'] = '0' * 40
        with self.assertRaises(ValueError):
            adr.check(self.repo, m)
        self.put('source.py', 'amount = 2\n')
        with self.assertRaisesRegex(ValueError, 'committed source'):
            adr.check(self.repo, self.manifest())

    def test_legacy_lines_are_human_until_reconcile_requires_explicit_enforcement(self):
        path = self.repo / '.plumb/system/adr/0007-money.md'
        path.write_text(path.read_text().replace('Enforced by: test: test_integer_money\n', ''))
        self.commit()
        manifest = {'head': self.git('rev-parse', 'HEAD'), 'checks': []}
        self.assertTrue(adr.check(self.repo, manifest)['ready'])
        self.assertFalse(adr.check(self.repo, manifest, require_lines=True)['ready'])
        output = self.repo / '.plumb/changes/demo/drift.md'
        missing_human = {'inventory_sha256': adr.digest(adr.inventory(self.repo)), 'adrs': []}
        self.assertFalse(adr.drift(self.repo, manifest, missing_human, output)['ready'])
        self.assertIn('not run', output.read_text())

    def test_supersedes_must_be_in_the_affected_decision(self):
        path = self.repo / self.draft
        path.write_text(path.read_text().replace('## Open questions',
                        '### Different decision\nSupersedes: 0007\n## Open questions'))
        self.assertFalse(adr.conformance(self.repo, [self.draft], self.cards())['ready'])
        path.write_text('# Architecture\n## Decisions\n### Money\nSupersedes: ADR 0007\n'
                        'Decision: Store money as a float.\n## Open questions\n')
        report = adr.conformance(self.repo, [self.draft], self.cards())
        self.assertTrue(report['ready'])
        self.assertIn('actual approval', report['approval_summary'][0])

    def test_failed_or_unavailable_commands_are_not_green(self):
        m = self.manifest()
        m['checks'][0]['argv'] = ['python3', '-c', 'raise SystemExit(1)']
        self.assertEqual(adr.check(self.repo, m)['adrs'][0]['status'], 'fail')
        m['checks'][0]['argv'] = ['/definitely-absent-plumb-command']
        self.assertEqual(adr.check(self.repo, m)['adrs'][0]['status'], 'not run')

    def test_drift_cannot_overwrite_source_or_an_approved_document(self):
        inv = adr.inventory(self.repo)
        for output in (self.repo / 'source.py', self.repo / self.draft):
            with self.assertRaisesRegex(ValueError, 'drift output'):
                adr.drift(self.repo, self.manifest(), {'inventory_sha256': adr.digest(inv), 'adrs': []}, output)

    def test_report_outputs_cannot_overwrite_approved_or_aliased_documents(self):
        import json
        import os
        import sys
        for target in (self.repo / self.draft, self.repo / 'source.py'):
            before = target.read_bytes()
            p = subprocess.run([sys.executable, str(Path(adr.__file__)), 'inventory', '--repo', str(self.repo),
                                '--output', str(target)], capture_output=True, check=False)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(target.read_bytes(), before)
        alias = self.repo / '.plumb/changes/demo/adr-inventory.json'
        os.link(self.repo / self.draft, alias)
        with self.assertRaises(ValueError):
            adr.report_path(self.repo, alias)
        alias.unlink()
        alias.symlink_to(self.repo / self.draft)
        with self.assertRaises(ValueError):
            adr.report_path(self.repo, alias)
        report = json.loads(subprocess.check_output([
            sys.executable, str(Path(adr.__file__)), 'inventory', '--repo', str(self.repo)]))
        self.assertEqual(report['inventory_sha256'], adr.digest(report['inventory']))

    def test_fenced_supersedes_and_small_on_architecture_cannot_bypass_conflict(self):
        path = self.repo / self.draft
        path.write_text(path.read_text().replace('Supersedes: none', '```text\nSupersedes: 0007\n```'))
        self.assertFalse(adr.conformance(self.repo, [self.draft], self.cards())['ready'])
        with self.assertRaisesRegex(ValueError, 'small'):
            adr.conformance(self.repo, [self.draft], None, small=True)

    def test_command_cannot_redirect_the_final_drift_write(self):
        output = self.repo / '.plumb/changes/demo/drift.md'
        original = (self.repo / self.draft).read_bytes()
        m = self.manifest()
        m['checks'][0]['argv'] = ['python3', '-c',
            'from pathlib import Path; Path(".plumb/changes/demo/drift.md").symlink_to("02-architecture.md")']
        human = {'inventory_sha256': adr.digest(adr.inventory(self.repo)), 'adrs': []}
        with self.assertRaisesRegex(ValueError, 'symlink'):
            adr.drift(self.repo, m, human, output)
        self.assertEqual((self.repo / self.draft).read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
