"""Real-PR corpus selection stays independent of agent outcomes."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pr_corpus


class CorpusTests(unittest.TestCase):
    def test_go_case_uses_module_view_and_exact_pr_requirements(self):
        source = {'id': 'repo', 'repo': '/source', 'kind': 'go', 'source_subdir': 'apps/api',
                  'claude_md': 'Existing project guidance.'}
        pr = {'number': 7, 'title': 'Add a public status field', 'body': 'Preserve access rules.',
              'url': 'https://github.com/owner/repo/pull/7', 'mergedAt': '2026-10-01T00:00:00Z',
              'mergeCommit': {'oid': 'a' * 40}, 'files': [{'path': p} for p in (
                  'apps/api/internal/status/status.go', 'apps/api/internal/status/status_test.go',
                  'apps/frontend/future.test.ts', 'apps/api/internal/status/integration_test.go')]}
        def git(repo, *args):
            if args[0] == 'rev-parse':
                self.assertEqual(args[1], 'a' * 40 + '^1')
                return 'b' * 40
            return 'func TestStatus(t *testing.T) {}\n'
        with patch.object(pr_corpus, 'git', side_effect=git):
            case = pr_corpus.make_case(source, pr)
        self.assertEqual(case['base_commit'], 'b' * 40)
        self.assertEqual(case['acceptance_files'], ['internal/status/status_test.go'])
        self.assertEqual(case['requirements'], pr['title'] + '\n\n' + pr['body'])
        self.assertIn('./internal/status', case['test_command'])
        self.assertNotIn('apps/frontend', str(case['test_command']))

    def test_jest_typechain_is_explicit_and_precedes_test_arguments(self):
        source = {'id': 'repo', 'repo': '/source', 'kind': 'jest', 'node_modules': '/cache',
                  'node_adapter': __file__, 'claude_md': 'Project guidance.'}
        pr = {'number': 7, 'title': 'Add a feature', 'body': 'Expected behavior.', 'url': 'https://example.test/7',
              'mergedAt': '2026-10-01T00:00:00Z', 'mergeCommit': {'oid': 'reference'},
              'files': [{'path': path} for path in ('src/feature.spec.ts', 'src/tests/fixtures/data.json',
                                                       'src/tests/helpers/build-feature.ts', 'src/feature.ts')]}
        with patch.object(pr_corpus, 'git', return_value='base'):
            plain = pr_corpus.make_case(source, pr)['test_command']
            generated_case = pr_corpus.make_case({**source, 'typechain': True}, pr)
            generated = generated_case['test_command']
        self.assertNotIn('--typechain', plain)
        self.assertLess(generated.index('--typechain'), generated.index('--'))
        self.assertEqual(generated_case['acceptance_support_files'],
                         ['src/tests/fixtures/data.json', 'src/tests/helpers/build-feature.ts'])
        self.assertNotIn('src/tests/fixtures/data.json', generated)
        self.assertEqual(generated_case['acceptance_files'], ['src/feature.spec.ts'])
        self.assertTrue(generated_case['provide_acceptance'])

    def test_go_feature_failure_requires_actual_production_declaration_delta(self):
        cases = [
            ('undefined: NewThing', 'func NewThing() {}', '', 'NewThing'),
            ('q.SuggestedAnswerOptions undefined (type *models.Question has no field or method SuggestedAnswerOptions)',
             'type Question struct {\n SuggestedAnswerOptions []string\n}',
             'type Question struct {\n Name string\n}', 'SuggestedAnswerOptions'),
            ('too many arguments in call to proposedUpdateDTO',
             'func proposedUpdateDTO(question Question, options []string) DTO { return DTO{} }',
             'func proposedUpdateDTO(question Question) DTO { return DTO{} }', 'proposedUpdateDTO'),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            reference = Path(temporary)
            (reference / 'internal').mkdir()
            for output, new, old, symbol in cases:
                (reference / 'internal/feature.go').write_text(new)
                case = {'repo': '/source', 'base_commit': 'base', 'reference_commit': 'reference',
                        'source_subdir': 'apps/api', 'acceptance_files': ['internal/feature_test.go']}
                pr = {'files': [{'path': 'apps/api/internal/feature.go'}]}
                result = {'baseline': {'status': 'setup_error', 'output': output},
                          'reference_result': {'status': 'pass'}, 'reference': reference}
                with patch.object(pr_corpus, 'git', return_value=new), \
                        patch.object(pr_corpus.subprocess, 'run', return_value=SimpleNamespace(stdout=old)):
                    expected = pr_corpus.go_feature_failure(case, pr, result)
                    self.assertEqual(expected['symbol'], symbol)
                    self.assertEqual(expected['reference_file'], 'internal/feature.go')
                    result['baseline']['status'] = 'expected_feature_failure'
                    self.assertEqual(pr_corpus.go_feature_failure(case, pr, result), expected)
                    result['baseline']['output'] += '\nno required module provides package missing/dependency'
                    self.assertIsNone(pr_corpus.go_feature_failure(case, pr, result))
                    result['baseline']['output'] = output
                    result['reference_result']['status'] = 'setup_error'
                    self.assertIsNone(pr_corpus.go_feature_failure(case, pr, result))
                    result['reference_result']['status'] = 'pass'
                    for path in ('apps/api/internal/mocks/feature.go', 'apps/api/internal/testhelpers/feature.go',
                                 'apps/api/internal/fixture_feature.go', 'apps/api/internal/feature_test.go'):
                        self.assertIsNone(pr_corpus.go_feature_failure(case, {'files': [{'path': path}]}, result))
                with patch.object(pr_corpus, 'git', return_value=new), \
                        patch.object(pr_corpus.subprocess, 'run', return_value=SimpleNamespace(stdout=new)):
                    self.assertIsNone(pr_corpus.go_feature_failure(case, pr, result))

    def test_resume_preserves_and_revalidates_derived_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = root / 'metadata.json'
            metadata.write_text('[{"number": 1, "files": [{"path": "feature.go"}]}]')
            source = {'id': 'go', 'repo': '/source', 'kind': 'go', 'metadata': str(metadata), 'pr_numbers': [1]}
            case = {'id': 'go-1', 'repo': '/source', 'base_commit': 'base', 'reference_commit': 'reference',
                    'acceptance_files': ['feature_test.go']}
            expected = {'pattern': 'undefined: NewThing', 'symbol': 'NewThing', 'reference_file': 'feature.go'}
            def admit(case, destination, timeout, **kwargs):
                destination.mkdir()
                (destination / 'reference').mkdir()
                (destination / 'reference/feature.go').write_text('func NewThing() {}')
                return {'admitted': False, 'baseline': {'status': 'setup_error', 'output': 'undefined: NewThing'},
                        'reference_result': {'status': 'pass'}, 'reference': destination / 'reference'}
            with patch.object(pr_corpus, 'make_case', return_value=case), \
                    patch.object(pr_corpus, 'admit_case', side_effect=admit), \
                    patch.object(pr_corpus, 'go_feature_failure', return_value=expected):
                first = pr_corpus.prepare({'sources': [source]}, root / 'out', target=1)
            self.assertEqual(first['selected'], 1)
            with patch.object(pr_corpus, 'make_case', return_value={k: v for k, v in case.items() if k != 'expected_feature_failure'}), \
                    patch.object(pr_corpus, 'admit_case') as admission, \
                    patch.object(pr_corpus, 'go_feature_failure', return_value=expected) as classifier:
                resumed = pr_corpus.prepare({'sources': [source]}, root / 'out', target=1)
            self.assertEqual(resumed['selected'], 1)
            admission.assert_not_called()
            classifier.assert_called_once()

    def test_new_relative_production_module_calibration_rejects_dependencies_and_existing_modules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actor, reference = root / 'actor', root / 'reference'
            actor.mkdir()
            (reference / 'utils').mkdir(parents=True)
            (reference / 'tests').mkdir()
            (reference / 'utils/prices.ts').write_text('export function groupPrices() { return []; }')
            (reference / 'tests/prices.spec.ts').write_text("import { groupPrices } from '../utils/prices';")
            case = {'acceptance_files': ['tests/prices.spec.ts']}
            pr = {'files': [{'path': 'utils/prices.ts'}, {'path': 'tests/prices.spec.ts'}]}
            output = "Cannot find module '../utils/prices' from 'tests/prices.spec.ts'"
            result = {'actor': actor, 'reference': reference, 'baseline': {'status': 'setup_error', 'output': output},
                      'reference_result': {'status': 'pass'}}
            expected = pr_corpus.module_feature_failure(case, pr, result)
            self.assertEqual(expected['symbol'], 'groupPrices')
            self.assertEqual(expected['missing_module'], '../utils/prices')
            self.assertEqual(expected['importing_test'], 'tests/prices.spec.ts')
            result['baseline']['status'] = 'expected_feature_failure'
            self.assertEqual(pr_corpus.module_feature_failure(case, pr, result), expected)
            result['baseline']['output'] += "\nCannot find module 'missing-dependency' from 'tests/prices.spec.ts'"
            self.assertIsNone(pr_corpus.module_feature_failure(case, pr, result))
            result['baseline']['output'] = output
            (actor / 'utils').mkdir()
            (actor / 'utils/prices.js').write_text('existing alternative resolution')
            self.assertIsNone(pr_corpus.module_feature_failure(case, pr, result))

    def test_relative_and_mapped_alias_reports_resolve_to_the_same_new_module(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actor, reference = root / 'actor', root / 'reference'
            actor.mkdir()
            (reference / 'src/utils').mkdir(parents=True)
            (reference / 'src/tests').mkdir()
            config = '{"compilerOptions":{"baseUrl":"./","paths":{"@app/*":["src/*"]}}}'
            for directory in (actor, reference):
                (directory / 'tsconfig.json').write_text(config)
            (reference / 'src/utils/prices.ts').write_text('export function groupPrices() { return []; }')
            (reference / 'src/tests/prices.spec.ts').write_text("import { groupPrices } from '../utils/prices';")
            (reference / 'src/tests/service.spec.ts').write_text("import { groupPrices } from '@app/utils/prices';")
            case = {'acceptance_files': ['src/tests/prices.spec.ts', 'src/tests/service.spec.ts']}
            pr = {'files': [{'path': 'src/utils/prices.ts'}, {'path': 'src/tests/prices.spec.ts'}]}
            output = ("FAIL src/tests/service.spec.ts\n"
                      "Could not locate module @app/utils/prices mapped as:\n/work/src/$1\n"
                      "FAIL src/tests/prices.spec.ts\n"
                      "Cannot find module '../utils/prices' from 'tests/prices.spec.ts'")
            result = {'actor': actor, 'reference': reference, 'baseline': {'status': 'setup_error', 'output': output},
                      'reference_result': {'status': 'pass'}}
            expected = pr_corpus.module_feature_failure(case, pr, result)
            self.assertEqual(expected['module_aliases'], ['@app/utils/prices'])
            self.assertEqual(expected['importing_test'], 'src/tests/prices.spec.ts')
            result['baseline']['output'] += '\nCould not locate module @app/unrelated mapped as:'
            self.assertIsNone(pr_corpus.module_feature_failure(case, pr, result))
            result['baseline']['output'] = output
            (actor / 'tsconfig.json').write_text(config.replace('src/*', 'different/*'))
            self.assertIsNone(pr_corpus.module_feature_failure(case, pr, result))

    def test_vitest_unquoted_local_importer_and_loader_zero_test_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actor, reference = root / 'actor', root / 'reference'
            actor.mkdir()
            (reference / 'src/core').mkdir(parents=True)
            (reference / 'src/core/open-order.ts').write_text('export function orderToOpen() { return null; }')
            (reference / 'src/core/open-order.test.ts').write_text('import { orderToOpen } from "./open-order";')
            case = {'acceptance_files': ['src/core/open-order.test.ts']}
            pr = {'files': [{'path': 'src/core/open-order.ts'}, {'path': 'src/core/open-order.test.ts'}]}
            output = ("Tests no tests\nError: Cannot find module './open-order' imported from "
                      '/tmp/grading/work/src/core/open-order.test.ts\n')
            result = {'actor': actor, 'reference': reference, 'baseline': {'status': 'setup_error', 'output': output},
                      'reference_result': {'status': 'pass'}}
            expected = pr_corpus.module_feature_failure(case, pr, result)
            self.assertEqual(expected['symbol'], 'orderToOpen')
            self.assertEqual(expected['importing_test'], 'src/core/open-order.test.ts')
            result['baseline']['output'] += '\nno tests collected'
            self.assertIsNone(pr_corpus.module_feature_failure(case, pr, result))

    def test_selection_is_round_robin_and_calibration_failures_are_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = []
            for name in ('a', 'b'):
                metadata = root / (name + '.json')
                metadata.write_text(json.dumps([{'number': n} for n in (1, 2)]))
                sources.append({'id': name, 'repo': '/source/' + name, 'metadata': str(metadata), 'pr_numbers': [1, 2]})
            order = []
            def case(source, pr):
                return {'id': source['id'] + '-' + str(pr['number'])}
            def admit(case, destination, timeout, **kwargs):
                self.assertTrue(callable(kwargs['runner']))
                destination.mkdir()
                order.append(case['id'])
                admitted = case['id'] != 'a-1'
                return {'admitted': admitted, 'baseline': {'status': 'assertion_failure'},
                        'reference_result': {'status': 'pass' if admitted else 'setup_error'}}
            with patch.object(pr_corpus, 'make_case', side_effect=case), patch.object(pr_corpus, 'admit_case', side_effect=admit):
                result = pr_corpus.prepare({'sources': sources}, root / 'out', target=3)
            self.assertEqual(order, ['a-1', 'b-1', 'a-2', 'b-2'])
            self.assertEqual(result['selected'], 3)
            audit = json.loads((root / 'out/admission-audit.json').read_text())
            self.assertEqual(audit['selected'], ['b-1', 'a-2', 'b-2'])
            self.assertEqual(audit['excluded'][0]['id'], 'a-1')
            manifest = json.loads((root / 'out/manifest.json').read_text())
            self.assertTrue(manifest['quality_only'])
            self.assertEqual(manifest['minimum_quality_margin_pp'], 10)


if __name__ == '__main__':
    unittest.main()
