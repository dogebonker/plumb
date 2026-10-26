"""Run: python3 -m unittest discover -s runner -p test_usage.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
from usage import receipt


def result(n=10, session='s', parent=None):
    return {'type': 'result', 'session_id': session, 'parent_tool_use_id': parent,
            'modelUsage': {'model': {'inputTokens': n, 'cacheReadInputTokens': 20,
                                    'cacheCreationInputTokens': 3, 'outputTokens': 4}}}


class UsageTests(unittest.TestCase):
    def test_cumulative_resume_and_children_are_not_added(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            first = receipt(ledger, 'task', 'plumb-product', [result(), result(999, parent='child')])
            again = receipt(ledger, 'task', 'plumb-product', [result()])
            next_step = receipt(ledger, 'task', 'plumb-product', [result(15)])
            self.assertEqual(first['tokens'], 37)
            self.assertEqual(again['tokens'], 0)
            self.assertEqual(next_step['tokens'], 5)
            self.assertEqual(next_step['models']['model']['inputTokens'], 5)
            self.assertIsNone(first['calls'])
            self.assertIsNone(again['calls'])

    def test_unknown_is_not_zero_and_partial_is_a_lower_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            unknown = receipt(ledger, 'task', 'skill', [])
            partial = receipt(ledger, 'task', 'skill', [result()], partial=True)
            self.assertIsNone(unknown['tokens'])
            self.assertIsNone(unknown['calls'])
            self.assertIsNone(partial['tokens'])
            self.assertEqual(partial['observed_tokens'], 37)
            self.assertTrue(partial['problems'])

    def test_missing_classes_and_counter_regression_are_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            receipt(ledger, 'task', 'skill', [result()])
            self.assertIsNone(receipt(ledger, 'task', 'skill', [result(5)])['tokens'])
            bad = result(session='other')
            del bad['modelUsage']['model']['outputTokens']
            missing = receipt(ledger, 'task', 'skill', [bad])
            self.assertIsNone(missing['tokens'])
            self.assertEqual(missing['observed_tokens'], 33)
            self.assertEqual(receipt(ledger, 'task', 'skill', [bad])['observed_tokens'], 0)
            self.assertEqual(receipt(ledger, 'task', 'skill', [result(session='other')])['tokens'], 4)
            self.assertEqual(len(ledger.read_text().splitlines()), 5)

    def test_new_invocations_and_unknown_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            receipt(ledger, 'task', 'skill', [], invocation='one')
            receipt(ledger, 'task', 'skill', [result()], invocation='one')
            receipt(ledger, 'task', 'skill', [result()], invocation='two')
            from usage import report
            complete = report(ledger)
            self.assertEqual(complete['tokens'], 74)
            self.assertEqual(complete['skills'][0]['invocations'], 2)
            self.assertEqual(complete['skills'][0]['unknown_invocations'], 0)
            self.assertEqual(complete['skills'][0]['token_classes']['cacheReadInputTokens'], 40)
            self.assertIsNone(complete['skills'][0]['calls'])
            self.assertIsNone(complete['actual_cost_usd'])
            child = receipt(ledger, 'task', 'nested', [result()], invocation='child', parent='one')
            self.assertIsNone(child['tokens'])
            self.assertIsNone(child['observed_tokens'])
            self.assertIsNone(report(ledger)['tokens'])
            self.assertEqual(report(ledger)['observed_tokens'], 74)
            self.assertEqual(report(ledger)['skills'][1]['unknown_invocations'], 1)
            self.assertIsNone(report(ledger)['skills'][1]['token_classes']['inputTokens'])
            self.assertIsNone(report(ledger)['skills'][1]['observed_tokens'])

    def test_capture_uses_parent_directory_and_keeps_process_group(self):
        from unittest.mock import Mock, patch

        import plumb_run
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'work'
            work.mkdir()
            proc = Mock()
            proc.wait.return_value = 0
            def start(cmd, **kwargs):
                self.assertTrue(kwargs['start_new_session'])
                self.assertEqual(kwargs['env']['PLUMB_RUNNER_MANAGED'], '1')
                kwargs['stdout'].write((json.dumps(result()) + '\n').encode())
                return proc
            with patch.object(plumb_run.subprocess, 'Popen', side_effect=start):
                self.assertEqual(plumb_run.run_harness(
                    ['claude', '-p', '--output-format', 'stream-json', '--verbose', '/plumb-product t'], work, 2), 0)
            self.assertEqual(json.loads((Path(tmp) / 'usage-stream.jsonl').read_text())['type'], 'result')

    def test_interactive_entry_snapshot_is_not_charged_to_skill(self):
        from usage import report
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            entry = receipt(ledger, 'task', 'plumb-review', [result(100)], baseline_only=True)
            self.assertIsNone(entry['tokens'])
            self.assertIsNone(report(ledger)['observed_tokens'])
            receipt(ledger, 'task', 'plumb-review', [result(110)])
            self.assertEqual(report(ledger)['tokens'], 10)
            self.assertEqual(report(ledger)['skills'][0]['token_classes']['inputTokens'], 10)

    def test_incomplete_entry_baseline_never_claims_exact_exit_total(self):
        from usage import report
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'usage.jsonl'
            entry = result(100)
            del entry['modelUsage']['model']['outputTokens']
            receipt(ledger, 'task', 'skill', [entry], baseline_only=True)
            exit_event = result(110)
            exit_event['modelUsage']['model']['outputTokens'] = 999
            exit_row = receipt(ledger, 'task', 'skill', [exit_event])
            self.assertIsNone(exit_row['tokens'])
            self.assertEqual(exit_row['observed_tokens'], 10)
            self.assertNotIn('outputTokens', exit_row['models']['model'])
            self.assertIsNone(receipt(ledger, 'task', 'skill', [exit_event])['tokens'])
            self.assertIsNone(report(ledger)['tokens'])
            self.assertEqual(report(ledger)['observed_tokens'], 10)


if __name__ == '__main__':
    unittest.main()
