"""Strict v2 contract and dependency invariants."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
import v2_contract as contract


def plan_fixture():
    gates = [{'id': kind, 'kind': kind, 'argv': ['python3', '-c', 'pass'], 'timeout_seconds': 10}
             for kind in ('tests', 'typecheck', 'lint', 'nfr')]
    def item(ident, kind, owns, depends):
        return {'id': ident, 'kind': kind, 'depends_on': depends, 'owns': owns, 'reads': [],
                'interfaces': [], 'fr': [{'id': 'FR-' + ident, 'given': 'input', 'when': 'run', 'then': 'output',
                                          'gate_id': 'tests', 'case_id': 'test_' + ident}],
                'rules': {'ids': ['no-cycle'], 'surfaces': []}, 'gates': ['tests', 'typecheck', 'lint'],
                'budget': {'tokens': 100, 'seconds': 10, 'retries': 0, 'review_passes': 1, 'review_tokens': 50}}
    return {'schema_version': 1, 'change_id': 'example', 'base_commit': 'a' * 40,
            'policy': {'layout': {'path': 'layout.json', 'sha256': 'b' * 64},
                       'permitted_rule_ids': ['no-cycle'], 'gate_definitions': gates},
            'frozen_inputs': [{'path': 'tests/scenarios.json', 'sha256': 'c' * 64, 'kind': 'fr'}],
            'budget': {'tokens': 500, 'seconds': 100, 'opus_share_limit': .25},
            'slices': [item('contracts', 'contract', ['src/contracts.py'], []),
                       item('feature', 'feature', ['src/feature.py'], ['contracts'])]}


class ContractTests(unittest.TestCase):
    def test_replan_allocation_is_explicit_bounded_and_changes_approval_digest(self):
        plan = plan_fixture()
        original = contract.digest(plan)
        plan['replan_budget'] = {'tokens': 10, 'seconds': 10, 'max_calls': 2}
        contract.validate_plan(plan)
        self.assertNotEqual(original, contract.digest(plan))
        for field, value in (('tokens', 501), ('seconds', 101), ('max_calls', 0), ('max_calls', True)):
            changed = copy.deepcopy(plan)
            changed['replan_budget'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                contract.validate_plan(changed)

    def test_manifest_and_inline_normalize_to_same_plan(self):
        plan = plan_fixture()
        contract.validate_plan(plan)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            manifest = copy.deepcopy(plan)
            manifest['slices'] = []
            for item in plan['slices']:
                filename = item['id'] + '.yaml'
                (root / filename).write_text(json.dumps(item))
                manifest['slices'].append(filename)
            path = root / 'plan.yaml'
            path.write_text(json.dumps(manifest))
            self.assertEqual(contract.load_plan(path), plan)
            self.assertEqual(contract.ready_slices(plan, set(), set()), ['contracts'])
            self.assertEqual(contract.ready_slices(plan, {'contracts'}, set()), ['feature'])
            self.assertEqual(contract.ready_slices(plan, {'contracts'}, {'feature'}), [])
            with self.assertRaises(ValueError):
                contract.ready_slices(plan, {'missing'}, set())
            (root / 'contracts.yaml').write_text('{"id":"x","id":"y"}')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                contract.load_plan(path)

    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                contract.strict_json(text)
        self.assertEqual(contract.digest({'a': 1, 'b': 2}), contract.digest({'b': 2, 'a': 1}))
        with self.assertRaises(ValueError):
            contract.digest({'a': float('inf')})

    def test_invalid_schemas_and_references(self):
        mutations = [
            lambda p: p.update(extra=True),
            lambda p: p.update(schema_version=True),
            lambda p: p['budget'].update(tokens=True),
            lambda p: p['budget'].update(opus_share_limit=float('nan')),
            lambda p: p['budget'].update(opus_share_limit=.26),
            lambda p: p['slices'][1].update(depends_on=[]),
            lambda p: p['slices'][1].update(depends_on=['missing']),
            lambda p: p['slices'][0].update(depends_on=['feature']),
            lambda p: p['slices'][1].update(gates=['tests', 'lint']),
            lambda p: p['slices'][1]['fr'][0].update(gate_id='missing'),
            lambda p: p['slices'][1]['fr'][0].update(case_id=''),
            lambda p: p.update(frozen_inputs=[]),
            lambda p: p['slices'][1]['rules'].update(ids=['unknown']),
            lambda p: p['slices'][1]['budget'].update(retries=-1),
            lambda p: p['slices'][1].update(owns=['tests/']),
            lambda p: p['slices'][1].update(owns=['src/contracts.py']),
            lambda p: p['slices'][1].update(interfaces=[{'path': 'other.py', 'symbol': 'x', 'signature': 'x()'}]),
        ]
        for mutate in mutations:
            plan = plan_fixture()
            mutate(plan)
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                contract.validate_plan(plan)

    def test_optional_gate_outputs_and_case_aliases(self):
        plan = plan_fixture()
        gate = plan['policy']['gate_definitions'][0]
        gate['outputs'] = ['build/', 'cache.tsbuildinfo']
        contract.validate_plan(plan)
        for output in ('../escape', '.git/cache', 'tests/', 'layout.json'):
            gate['outputs'] = [output]
            with self.subTest(output=output), self.assertRaises(ValueError):
                contract.validate_plan(plan)
        gate['outputs'] = []
        plan['slices'][1]['reads'] = ['Src/contracts.py']
        with self.assertRaisesRegex(ValueError, 'case alias'):
            contract.validate_plan(plan)

    def test_one_export_cannot_have_conflicting_approved_signatures(self):
        plan = plan_fixture()
        surface = {'path': 'src/feature.py', 'symbol': 'run', 'signature': '() => string'}
        plan['slices'][1]['interfaces'] = [surface]
        plan['slices'][1]['rules']['surfaces'] = [dict(surface)]
        contract.validate_plan(plan)
        plan['slices'][1]['rules']['surfaces'][0]['signature'] = '() => number'
        with self.assertRaisesRegex(ValueError, 'conflicting surface signatures'):
            contract.validate_plan(plan)

    def test_final_integration_gate_is_a_separate_approved_test(self):
        plan = plan_fixture()
        plan['policy']['gate_definitions'].append(
            {'id': 'merged-http', 'kind': 'tests', 'argv': ['node', 'check.mjs', 'final'],
             'timeout_seconds': 60})
        plan['policy']['final_test_gate'] = 'merged-http'
        contract.validate_plan(plan)
        for value in ('missing', 'lint', 'tests'):
            plan['policy']['final_test_gate'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                contract.validate_plan(plan)

    def test_plan_rejects_decomposed_unicode_paths(self):
        for field in ('owns', 'reads'):
            plan = plan_fixture()
            plan['slices'][1][field] = ['src/cafe\u0301.py']
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'NFC'):
                contract.validate_plan(plan)
        plan = plan_fixture()
        plan['frozen_inputs'][0]['path'] = 'tests/cafe\u0301.json'
        with self.assertRaisesRegex(ValueError, 'NFC'):
            contract.validate_plan(plan)
        self.assertTrue(contract.overlaps('src/café.py', 'src/cafe\u0301.py'))

    def test_cycles_and_unordered_read_write_conflicts(self):
        plan = plan_fixture()
        third = copy.deepcopy(plan['slices'][1])
        third.update(id='other', owns=['src/other.py'], reads=['src/feature.py'])
        third['fr'] = []
        plan['slices'].append(third)
        with self.assertRaisesRegex(ValueError, 'dependency ordering'):
            contract.validate_plan(plan)
        third['depends_on'].append('feature')
        contract.validate_plan(plan)
        plan['slices'][1]['depends_on'].append('other')
        with self.assertRaisesRegex(ValueError, 'cycle'):
            contract.validate_plan(plan)

    def test_unsafe_paths_and_manifest_links(self):
        for path in ('../x', '/x', 'a/../x', 'a//x', './x', 'x\\y', 'x*', '.git/config',
                     '.CLAUDE/hooks', 'AGENTS.md', 'x\n'):
            plan = plan_fixture()
            plan['slices'][1]['owns'] = [path]
            with self.subTest(path=path), self.assertRaises(ValueError):
                contract.validate_plan(plan)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'slice.yaml').write_text('{}')
            (root / 'link.yaml').symlink_to(root / 'slice.yaml')
            plan = plan_fixture()
            plan['slices'] = ['link.yaml']
            path = root / 'plan.yaml'
            path.write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, 'symlink'):
                contract.load_plan(path)
            plan['slices'] = ['../slice.yaml']
            path.write_text(json.dumps(plan))
            with self.assertRaises(ValueError):
                contract.load_plan(path)

    def test_review_binding_and_decisions(self):
        binding = {'run_id': 'run', 'head': 'a' * 40}
        review = {'binding': binding, 'gate_evidence_sha256': 'a' * 64, 'decision': 'accept', 'findings': []}
        contract.validate_review(review, binding)
        with self.assertRaisesRegex(ValueError, 'binding'):
            contract.validate_review(review, {'run_id': 'other', 'head': 'a' * 40})
        for decision in ('reject', 'spec_defect'):
            review['decision'] = decision
            with self.assertRaises(ValueError):
                contract.validate_review(review, binding)
            review['findings'] = [{'criterion_id': 1, 'path': 'src/x.py', 'message': 'missing behavior'}]
            contract.validate_review(review, binding)
            review['findings'][0]['criterion_id'] = True
            with self.assertRaises(ValueError):
                contract.validate_review(review, binding)
            review['findings'] = []


if __name__ == '__main__':
    unittest.main()
