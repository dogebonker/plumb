import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pr_benchmark as bench


class ReportingAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {"model": "pinned", "effort": "high", "margin_percentage_points": 10, "timeout_seconds": 30}
        self.cases = [{"id": f"task{i}", "provide_acceptance": True} for i in range(20)]
        self.usage = {"models": ["pinned"], "model_usage": {"pinned": {}}, "tokens": 100, "cost_usd": .1}
        verified = {"verified": True}
        self.record = {"status": "complete", "task_seconds": 10, "probe_seconds": 1,
                       "probe_usage": self.usage, "probe_inventory": verified,
                       "probe_model_usage": verified, "isolation_probe": verified,
                       "acceptance_integrity": verified,
                       "tests": {"status": "pass", "isolation": verified},
                       "archgraph": {"status": "no_new_violations"},
                       "attempts": [{"timeout": False, "returncode": 0, "seconds": 10,
                                     "response": {"state": "complete"}, "usage": self.usage,
                                     "inventory": verified, "model_usage_verification": verified}]}
        bench.write(self.root / "run.json", self.config)
        self.key = {}
        self.verdicts = {}
        for case in self.cases:
            for arm in bench.ARMS:
                identity = f"{case['id']}-{arm}"
                packet = self.root / "blind" / identity
                packet.mkdir(parents=True)
                result = self.root / "trials" / case['id'] / arm / "result.json"
                result.parent.mkdir(parents=True)
                bench.write(result, self.record)
                self.key[identity] = {"case": case['id'], "arm": arm,
                                      "packet_sha256": bench.benchmark.tree_hash(packet),
                                      "result_sha256": bench.sha(result)}
                self.verdicts[identity] = {"verdict": "accept", "reason": "Synthetic fixture."}

    def change(self, **changes):
        record = copy.deepcopy(self.record)
        record.update(changes)
        path = self.root / "trials/task0/factory/result.json"
        bench.write(path, record)
        self.key['task0-factory']['result_sha256'] = bench.sha(path)
        return record

    def report(self):
        bench.write(self.root / "blind-key.json", self.key)
        bench.write(self.root / "verdicts.json", {"key_sha256": bench.sha(self.root / "blind-key.json"), "verdicts": self.verdicts})
        with patch.object(bench, 'verify_inputs', return_value=self.cases):
            return bench.report(self.root)

    def timeout(self):
        attempt = copy.deepcopy(self.record['attempts'][0])
        attempt.update(timeout=True, returncode=-9, seconds=30, response=None,
                       usage={"models": [], "model_usage": None, "tokens": None, "cost_usd": None},
                       model_usage_verification={"verified": False})
        return self.change(status="timeout", task_seconds=30, attempts=[attempt])

    def test_verified_timeout_without_usage_does_not_block_quality(self):
        self.timeout()
        result = self.report()
        self.assertTrue(result['complete'])
        self.assertFalse(result['accounting_complete'])
        self.assertEqual(result['accepted']['factory'], 19)
        self.assertEqual(result['quality_coverage']['factory'], 20)
        self.assertEqual(result['accounting_coverage']['factory']['tokens'], 19)
        self.assertIn('| factory | unknown | unknown | 220.0 / 10.0 |', result['report'])
        self.assertNotIn('no winner', result['report'])
        self.assertIn('does not establish statistical superiority', result['report'])

    def test_timeout_with_prior_cumulative_usage_reports_lower_bound_once(self):
        record = self.timeout()
        prior = copy.deepcopy(self.record['attempts'][0])
        prior['response'] = {"state": "question"}
        self.change(**{**record, 'attempts': [prior, record['attempts'][0]]})
        result = self.report()
        self.assertTrue(result['complete'])
        self.assertFalse(result['accounting_complete'])
        self.assertIn('2000 (20/20 tasks observed)', result['report'])
        self.assertIn('2.000000 (20/20 tasks observed)', result['report'])

    def test_infrastructure_and_invalid_treatment_remain_unknown(self):
        for status in ('infrastructure_error', 'execution_failed', 'isolation_failed', 'model_evidence_failed', 'interrupted', 'invalid_workspace'):
            with self.subTest(status=status):
                self.change(status=status)
                result = self.report()
                self.assertFalse(result['complete'])
                self.assertEqual(result['accepted']['factory'], 19)
                self.assertIn('no winner', result['report'])

    def test_timeout_requires_guard_setup_and_all_earlier_model_evidence(self):
        record = self.timeout()
        for changes in ({'grading_error': 'infrastructure'}, {'interrupted': True},
                        {'probe_inventory': {'verified': False}}, {'isolation_probe': {'verified': False}},
                        {'tests': {'status': 'setup_error', 'isolation': {'verified': True}}}):
            with self.subTest(changes=changes):
                self.change(**{**record, **changes})
                self.assertFalse(self.report()['complete'])
        for change in ({'seconds': 29}, {'returncode': 1}, {'timeout': False},
                       {'usage': {'models': ['other-model'], 'model_usage': None}}):
            attempt = {**record['attempts'][0], **change}
            self.change(**{**record, 'attempts': [attempt]})
            self.assertFalse(self.report()['complete'])
        prior = {**self.record['attempts'][0], 'model_usage_verification': {'verified': False}}
        self.change(**{**record, 'attempts': [prior, record['attempts'][0]]})
        self.assertFalse(self.report()['complete'])

    def test_apparently_accepted_invalid_or_tampered_result_is_not_accepted(self):
        for changes in ({'acceptance_integrity': {'verified': False}},
                        {'status': 'acceptance_tampered', 'acceptance_integrity': {'verified': False}},
                        {'isolation_probe': {'verified': False}},
                        {'tests': {'status': 'coverage_missing', 'isolation': {'verified': True}}},
                        {'archgraph': {'status': 'scan_error'}}):
            with self.subTest(changes=changes):
                self.change(**changes)
                self.assertEqual(self.report()['accepted']['factory'], 19)

    def test_complete_delivery_still_requires_pinned_native_usage(self):
        attempt = {**self.record['attempts'][0], 'usage': {'tokens': None}, 'model_usage_verification': {'verified': False}}
        self.change(attempts=[attempt])
        self.assertFalse(self.report()['complete'])

    def test_complete_delivery_does_not_hide_failed_native_turn(self):
        for changes in ({'returncode': 1}, {'response': None},
                        {'response': {'state': 'api_error'}}):
            with self.subTest(changes=changes):
                self.change(attempts=[{**self.record['attempts'][0], **changes}])
                self.assertFalse(self.report()['complete'])

    def test_unknown_cost_never_becomes_zero_or_blocks_quality(self):
        attempt = copy.deepcopy(self.record['attempts'][0])
        attempt['usage']['cost_usd'] = None
        self.change(attempts=[attempt])
        result = self.report()
        self.assertTrue(result['complete'])
        self.assertFalse(result['accounting_complete'])
        self.assertEqual(result['accounting_coverage']['factory']['usd'], 19)
        self.assertIn('| factory | 2000 / 100 | unknown |', result['report'])
        self.assertIn('1.900000 (19/20 tasks observed)', result['report'])

    def test_candidate_error_needs_passing_isolated_reference_control(self):
        for control in ({'status': 'setup_error'}, {'status': 'pass'}):
            self.change(tests={'status': 'candidate_error', 'isolation': {'verified': True}, 'reference_control': control})
            self.assertFalse(self.report()['complete'])
        self.change(tests={'status': 'candidate_error', 'isolation': {'verified': True},
                           'reference_control': {'status': 'pass', 'isolation': {'verified': True}}})
        self.assertTrue(self.report()['complete'])


if __name__ == '__main__':
    unittest.main()
