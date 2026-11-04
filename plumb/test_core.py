"""Offline boundary checks for the clean-slate core."""
import copy
import tempfile
import unittest
from pathlib import Path

from plumb.core import apply, propose, reconcile


def response(action='finish', **fields):
    result = {'action': action, 'reads': [], 'searches': [], 'outcome': '', 'explanation': '',
              'question': '', 'evidence': [], 'links': [], 'edits': []}
    result.update(fields)
    return result


class Script:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.payloads = []

    def __call__(self, system, payload):
        self.payloads.append(payload)
        return next(self.responses)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.files = {'code/main.py': 'from guard import safe\nvalue = 1\n',
                      'code/guard.py': 'safe = True\n',
                      'knowledge/index.md': 'The value\nmust be two.\n',
                      'sources/design.md': 'The value must be two.\n'}
        for name, text in self.files.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)

    def inspect(self):
        return response('inspect', reads=[{'path': path, 'start_line': 0, 'end_line': 0} for path in self.files])

    def finish(self, **fields):
        return response(outcome='code_wrong', explanation='Value differs from requirement.',
                        question='Should the value be two?', evidence=[
                            {'path': 'code/main.py', 'quote': 'value = 1'},
                            {'path': 'knowledge/index.md', 'quote': 'The value must be two.'}], **fields)

    def report(self):
        return reconcile(self.root, Script(self.inspect(), self.finish()))

    def proposal(self, choice='code'):
        edit = {'path': 'code/main.py', 'old': 'value = 1', 'new': 'value = 2', 'reason': 'Operator chose code.'}
        if choice == 'knowledge':
            edit = {'path': 'knowledge/index.md', 'old': 'two', 'new': 'one', 'reason': 'Operator chose knowledge.'}
        return propose(self.report(), choice, Script(self.inspect(), self.finish(edits=[edit])))

    def test_check_reads_only_on_request_and_restores_prose_citation(self):
        script = Script(self.inspect(), self.finish(links=[{
            'from_path': 'code/main.py', 'to_path': 'code/guard.py', 'quote': 'from guard import safe'}]))
        report = reconcile(self.root, script)
        self.assertEqual(report['outcome'], 'code_wrong')
        self.assertNotIn('snapshot', script.payloads[0])
        self.assertEqual(script.payloads[0]['results']['reads'], [])
        self.assertEqual(report['evidence'][1]['quote'], 'The value\nmust be two.')
        self.assertEqual(report['evidence'][1]['line'], 1)
        self.assertEqual(report['links'][0]['line'], 1)
        self.assertEqual(report['snapshot'], self.files)
        self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])

    def test_no_doc_approval_and_no_unsolicited_edit(self):
        script = Script(self.inspect(), self.finish(edits=[{'path': 'code/main.py', 'old': '1', 'new': '2', 'reason': 'approved'}]))
        report = reconcile(self.root, script)
        self.assertEqual(report['outcome'], 'unknown')
        self.assertIn('cannot propose', report['error'])
        with self.assertRaises(ValueError):
            propose(self.report(), 'approved', Script())

    def test_apply_is_separate_atomic_and_idempotent(self):
        proposal = self.proposal()
        original = copy.deepcopy(proposal)
        self.assertIn('value = 1', (self.root / 'code/main.py').read_text())
        receipt = apply(proposal)
        self.assertEqual(receipt['status'], 'applied')
        self.assertEqual(receipt['choice'], 'code')
        self.assertEqual(apply(proposal)['status'], 'already_applied')
        self.assertEqual(proposal, original)
        self.assertIn('value = 2', (self.root / 'code/main.py').read_text())

    def test_chosen_correction_does_not_require_a_repeated_human_question(self):
        resolved = self.finish(edits=[{'path': 'knowledge/index.md', 'old': 'two',
                                     'new': 'one', 'reason': 'Explicit knowledge choice.'}])
        resolved['question'] = ''
        proposal = propose(self.report(), 'knowledge', Script(self.inspect(), resolved))
        self.assertEqual(proposal['choice'], 'knowledge')
        self.assertEqual(proposal['edits'][0]['new'], 'one')
        check = reconcile(self.root, Script(self.inspect(), {**resolved, 'edits': []}))
        self.assertEqual(check['outcome'], 'unknown')
        self.assertIn('human question', check['error'])

    def test_unresolved_or_aligned_report_cannot_start_a_correction(self):
        for outcome in ('unknown', 'sources_conflict', 'aligned'):
            with self.subTest(outcome=outcome):
                report = self.report()
                report['outcome'] = outcome
                edit = {'path': 'code/main.py', 'old': 'value = 1', 'new': 'value = 2',
                        'reason': 'A code choice does not choose the governing source.'}
                actor = Script(self.inspect(), self.finish(edits=[edit]))
                with self.assertRaisesRegex(ValueError, 'resolved actionable'):
                    propose(report, 'code', actor)
                self.assertEqual(actor.payloads, [])
                self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])

    def test_unresolved_proposal_result_cannot_be_applied(self):
        edit = {'path': 'code/main.py', 'old': 'value = 1', 'new': 'value = 2',
                'reason': 'Do not apply an unresolved inference.'}
        for outcome in ('unknown', 'sources_conflict', 'aligned'):
            with self.subTest(outcome=outcome):
                terminal = self.finish(edits=[edit])
                terminal['outcome'] = outcome
                if outcome == 'sources_conflict':
                    terminal['evidence'].append({'path': 'sources/design.md', 'quote': 'The value must be two.'})
                with self.assertRaisesRegex(ValueError, 'resolved actionable'):
                    propose(self.report(), 'code', Script(self.inspect(), terminal))

    def test_unreadable_source_prevents_alignment_without_calling_model(self):
        from plumb.core import MAX_FILE_BYTES
        path = self.root / 'sources/large.md'
        path.write_text('New source rule.\n' + 'x' * MAX_FILE_BYTES)
        terminal = self.finish()
        terminal['outcome'], terminal['question'] = 'aligned', ''
        actor = Script(self.inspect(), terminal)
        report = reconcile(self.root, actor)
        self.assertEqual(report['outcome'], 'unknown')
        self.assertIn('sources/large.md', report['question'])
        self.assertEqual(actor.payloads, [])
        self.assertTrue(report['skipped'])

    def test_new_unreadable_source_blocks_an_existing_proposal(self):
        from plumb.core import MAX_FILE_BYTES
        proposal = self.proposal()
        (self.root / 'sources/new.md').write_text('New source rule.\n' + 'x' * MAX_FILE_BYTES)
        with self.assertRaisesRegex(ValueError, 'not fully readable'):
            apply(proposal)
        self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])

    def test_nonregular_input_returns_unknown_without_model_or_blocking(self):
        import os
        os.mkfifo(self.root / 'sources/pipe.md')
        actor = Script()
        report = reconcile(self.root, actor)
        self.assertEqual(report['outcome'], 'unknown')
        self.assertEqual(actor.payloads, [])

    def test_apply_requires_actionable_proposal_provenance(self):
        from plumb.core import _identity
        original = self.proposal()
        for before, after in [(None, None), ('unknown', 'code_wrong'), ('code_wrong', 'unknown'), ('aligned', 'code_wrong')]:
            with self.subTest(before=before, after=after):
                proposal = copy.deepcopy(original)
                proposal.pop('proposal_id')
                if before is None:
                    proposal.pop('check_outcome')
                    proposal.pop('proposal_outcome')
                else:
                    proposal.update(check_outcome=before, proposal_outcome=after)
                proposal['proposal_id'] = _identity(proposal)
                with self.assertRaisesRegex(ValueError, 'resolved actionable'):
                    apply(proposal)
                self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])

    def test_knowledge_choice_cannot_change_code_or_sources(self):
        proposal = self.proposal('knowledge')
        self.assertEqual(apply(proposal)['status'], 'applied')
        self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])
        for name in ('sources/design.md', 'code/main.py', '../escape'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                propose(self.report(), 'knowledge', Script(self.inspect(), self.finish(edits=[{
                    'path': name, 'old': '1', 'new': '2', 'reason': 'bad scope'}])))

    def test_all_inputs_bound_and_new_files_rejected(self):
        for change in ('source', 'new'):
            with self.subTest(change=change):
                proposal = self.proposal()
                path = self.root / ('sources/design.md' if change == 'source' else 'code/new.py')
                before = path.read_text() if path.exists() else None
                path.write_text('changed')
                with self.assertRaises(ValueError):
                    apply(proposal)
                if before is None:
                    path.unlink()
                else:
                    path.write_text(before)
                self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])

    def test_symlink_and_hidden_files_not_exposed(self):
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / 'secret'
            outside.write_text('secret')
            (self.root / 'code/link.py').symlink_to(outside)
            (self.root / '.plumb').mkdir()
            (self.root / '.plumb/receipt').write_text('private runtime')
            (self.root / 'evals').mkdir()
            (self.root / 'evals/hidden.py').write_text('hidden labels')
            report = self.report()
            self.assertEqual(set(report['snapshot']), set(self.files))
            self.assertEqual(report['outcome'], 'unknown')
            (self.root / 'code/link.py').unlink()
            proposal = self.proposal()
            target = self.root / 'code/main.py'
            target.unlink()
            target.symlink_to(outside)
            with self.assertRaises(ValueError):
                apply(proposal)
            self.assertEqual(outside.read_text(), 'secret')

    def test_code_citation_must_be_exact_and_inspected(self):
        for script in (Script(self.finish()), Script(self.inspect(), response(
                outcome='unknown', explanation='uncertain', question='Which value?',
                evidence=[{'path': 'code/main.py', 'quote': 'value  = 1'}]))):
            self.assertEqual(reconcile(self.root, script)['outcome'], 'unknown')
            self.assertIn('error', reconcile(self.root, Script(response(
                outcome='aligned', explanation='trust me'))) )

    def test_conflict_needs_distinct_citations_and_question(self):
        report = reconcile(self.root, Script(self.inspect(), response(
            outcome='sources_conflict', explanation='Sources differ.', question='Which source governs?',
            evidence=[{'path': 'knowledge/index.md', 'quote': 'must be two.'},
                      {'path': 'sources/design.md', 'quote': 'must be two.'}])))
        self.assertEqual(report['outcome'], 'sources_conflict')
        bad = reconcile(self.root, Script(self.inspect(), response(
            outcome='sources_conflict', explanation='Conflict.', question='Which?',
            evidence=[{'path': 'sources/design.md', 'quote': 'must be two.'}])))
        self.assertEqual(bad['outcome'], 'unknown')

    def test_search_is_literal_and_budget_exhaustion_is_unknown(self):
        report = reconcile(self.root, Script(response('inspect', searches=['value'])), max_rounds=1)
        self.assertEqual(report['outcome'], 'unknown')
        self.assertTrue(report['trace'][0]['results']['searches'][0]['hits'])
        bad = reconcile(self.root, Script(response('inspect', reads=[{
            'path': '../outside', 'start_line': 0, 'end_line': 0}])))
        self.assertEqual(bad['outcome'], 'unknown')

    def test_malformed_response_and_ambiguous_replacement_fail_closed(self):
        malformed = reconcile(self.root, Script({'action': 'finish'}))
        self.assertEqual(malformed['outcome'], 'unknown')
        self.assertEqual(malformed['trace'][0]['response'], {'action': 'finish'})
        self.assertEqual(malformed['trace'][0]['snapshot_id'], malformed['snapshot_id'])
        for old in ('', 'e', 'missing'):
            with self.subTest(old=old), self.assertRaises(ValueError):
                propose(self.report(), 'code', Script(self.inspect(), self.finish(edits=[{
                    'path': 'code/main.py', 'old': old, 'new': 'x', 'reason': 'test'}])))

    def test_connected_source_verification_is_required_before_model_or_write(self):
        binding = {'scope': 'local_git_ref', 'version': 'one'}
        actor = Script()
        with self.assertRaisesRegex(ValueError, 'source verifier'):
            reconcile(self.root, actor, source_binding=binding)
        self.assertEqual(actor.payloads, [])
        report = self.report()
        report['source_binding'] = binding
        with self.assertRaisesRegex(ValueError, 'source verifier'):
            propose(report, 'code', actor)
        proposal = self.proposal()
        from plumb.core import _identity
        proposal.pop('proposal_id')
        proposal['source_binding'] = binding
        proposal['proposal_id'] = _identity(proposal)
        with self.assertRaisesRegex(ValueError, 'source verifier'):
            apply(proposal)
        self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])
        unconnected = self.report()
        unbound_proposal = self.proposal()
        (self.root / '.plumb').mkdir()
        (self.root / '.plumb/source.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'bound source'):
            reconcile(self.root, actor)
        with self.assertRaisesRegex(ValueError, 'bound source'):
            propose(unconnected, 'code', actor)
        with self.assertRaisesRegex(ValueError, 'bound source'):
            apply(unbound_proposal)

    def test_source_change_during_model_or_final_write_blocks_result(self):
        binding = {'scope': 'local_git_ref', 'version': 'one'}
        calls = []

        def verifier(value):
            self.assertEqual(value, binding)
            calls.append(value)
            value['version'] = 'mutated callback copy'
            if len(calls) == 2:
                raise ValueError('source changed')

        with self.assertRaisesRegex(ValueError, 'source changed'):
            reconcile(self.root, Script(self.inspect(), self.finish()),
                      source_binding=binding, verify_sources=verifier)
        self.assertEqual(binding['version'], 'one')
        report = self.report()
        report['source_binding'] = binding
        edit = {'path': 'code/main.py', 'old': 'value = 1', 'new': 'value = 2', 'reason': 'Chosen code.'}
        calls.clear()
        with self.assertRaisesRegex(ValueError, 'source changed'):
            propose(report, 'code', Script(self.inspect(), self.finish(edits=[edit])), verify_sources=verifier)
        proposal = propose(report, 'code', Script(self.inspect(), self.finish(edits=[edit])),
                           verify_sources=lambda value: None)
        calls.clear()
        with self.assertRaisesRegex(ValueError, 'source changed'):
            apply(proposal, verify_sources=verifier)
        self.assertEqual((self.root / 'code/main.py').read_text(), self.files['code/main.py'])
        self.assertEqual(list((self.root / 'code').glob('.plumb-*')), [])


if __name__ == '__main__':
    unittest.main()
