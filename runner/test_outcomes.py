"""Run: python3 -m unittest discover -s runner -p test_outcomes.py"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
from outcomes import report


def sample():
    return {'as_of': '2025-02-01T00:00:00Z', 'window_days': 7,
            'features': [{'id': 'one', 'arm': 'factory', 'merge_sha': 'a' * 40,
                          'merged_at': '2025-01-01T00:00:00Z',
                          'observation': {'through': '2025-01-08T00:00:00Z',
                                          'confidence': 'confirmed', 'evidence': 'incident-export:1'}}],
            'incidents': []}


def incident():
    return {'id': 'inc-1', 'feature': 'one', 'merge_sha': 'a' * 40,
            'detected_at': '2025-01-02T00:00:00Z', 'recovered_at': None,
            'confidence': 'confirmed', 'evidence': 'incident:1'}


class OutcomeTests(unittest.TestCase):
    def test_complete_window_can_report_confirmed_zero(self):
        result = report(sample())
        self.assertEqual(result['features'][0]['escaped_defects'], 0)
        self.assertEqual(result['cohorts'][0]['defects_per_feature'], 0)
        self.assertEqual(result['cohorts'][0]['observed_features'], 1)
        self.assertIsNone(result['features'][0]['adoption'])

    def test_unmerged_unobserved_and_immature_are_not_zero(self):
        for change in ('unmerged', 'unobserved', 'immature', 'unconfirmed'):
            with self.subTest(change=change):
                data = sample()
                feature = data['features'][0]
                if change == 'unmerged':
                    feature.update(merge_sha=None, merged_at=None, observation=None)
                elif change == 'unobserved':
                    feature['observation'] = None
                elif change == 'immature':
                    data['as_of'] = '2025-01-04T00:00:00Z'
                    feature['observation']['through'] = data['as_of']
                else:
                    feature['observation']['confidence'] = 'reported'
                result = report(data)
                self.assertIsNone(result['features'][0]['escaped_defects'])
                self.assertIsNone(result['cohorts'][0]['defects_per_feature'])
                self.assertEqual(result['cohorts'][0]['observed_features'], 0)

    def test_incident_dedup_and_censored_recovery(self):
        data = sample()
        data['incidents'] = [incident(), incident()]
        result = report(data)
        self.assertEqual(result['features'][0]['escaped_defects'], 1)
        self.assertEqual(len(result['recovery']), 1)
        self.assertIsNone(result['recovery'][0]['recovered_seconds'])
        self.assertEqual(result['recovery'][0]['ongoing_seconds'], 30 * 86400)
        self.assertTrue(result['recovery'][0]['right_censored'])

    def test_recovery_after_defect_window_is_still_measured(self):
        data = sample()
        row = incident()
        row['recovered_at'] = '2025-01-10T00:00:00Z'
        data['incidents'] = [row]
        result = report(data)
        self.assertEqual(result['recovery'][0]['recovered_seconds'], 8 * 86400)
        self.assertFalse(result['recovery'][0]['right_censored'])

    def test_late_and_suspected_incidents_are_not_confirmed_window_defects(self):
        data = sample()
        suspected = incident()
        suspected['confidence'] = 'suspected'
        late = incident()
        late.update(id='inc-2', detected_at='2025-01-15T00:00:00Z')
        data['incidents'] = [suspected, late]
        result = report(data)
        self.assertEqual(result['features'][0]['escaped_defects'], 0)
        self.assertEqual(result['features'][0]['suspected_defects'], 1)
        self.assertEqual(result['recovery'], [])

    def test_explicit_adoption_denominator_and_separate_cohorts(self):
        data = sample()
        data['features'][0]['adoption'] = {
            'event': 'completed first report', 'population': 'enabled internal analysts',
            'eligible': 8, 'adopted': 3, 'through': '2025-01-08T00:00:00Z',
            'confidence': 'confirmed', 'evidence': 'analytics:cohort-1'}
        other = copy.deepcopy(data['features'][0])
        other.update(id='control', arm='claude-md', merge_sha='b' * 40, adoption=None)
        data['features'].append(other)
        result = report(data)
        self.assertEqual(result['features'][0]['adoption']['rate'], 3 / 8)
        self.assertEqual(len(result['cohorts']), 2)
        self.assertIsNone(result['features'][1]['adoption'])
        data['features'][0]['adoption']['eligible'] = 0
        data['features'][0]['adoption']['adopted'] = 0
        self.assertIsNone(report(data)['features'][0]['adoption']['rate'])

    def test_invalid_records_fail_closed(self):
        mutations = [
            lambda d: d.update(window_days=0),
            lambda d: d.update(as_of='2999-01-01T00:00:00Z'),
            lambda d: d['features'][0].update(merged_at='2025-01-01'),
            lambda d: d['features'][0].update(merge_sha='main'),
            lambda d: d['features'][0]['observation'].update(through='2025-02-02T00:00:00Z'),
            lambda d: d['incidents'][0].update(feature='unknown'),
            lambda d: d['incidents'][0].update(merge_sha='b' * 40),
            lambda d: d['incidents'][0].update(detected_at='2024-12-31T00:00:00Z'),
            lambda d: d['incidents'][0].update(recovered_at='2025-01-01T00:00:00Z'),
            lambda d: d['incidents'][0].update(evidence=''),
            lambda d: d['incidents'][0].update(confidence='certain-ish'),
            lambda d: d['features'].append(copy.deepcopy(d['features'][0])),
            lambda d: d['incidents'].append(dict(d['incidents'][0], evidence='conflicting')),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                data = sample()
                data['incidents'] = [incident()]
                mutate(data)
                with self.assertRaises(ValueError):
                    report(data)

    def test_cli_emits_json_and_rejects_invalid_data(self):
        script = Path(__file__).resolve().parents[1] / 'kit/outcomes.py'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input.json'
            path.write_text(json.dumps(sample()))
            command = [sys.executable, str(script), 'report', '--input', str(path)]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['window_days'], 7)
            path.write_text('{"as_of": "bad"}')
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
