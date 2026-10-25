"""Durable journal recovery checks; no model/runtime calls."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
import v2_checkpoint as checkpoint


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_journal_tail_recovers_interruption_before_checkpoint_replace(self):
        checkpoint.save(self.root, {'phase': 'worker_done'})
        old = (self.root / 'checkpoint.json').read_bytes()
        checkpoint.save(self.root, {'phase': 'gates_pass'})
        (self.root / 'checkpoint.json').write_bytes(old)
        self.assertEqual(checkpoint.load(self.root), {'phase': 'gates_pass'})

    def test_corrupted_truncated_duplicate_and_nonfinite_journals_fail_closed(self):
        path = self.root / 'events.jsonl'
        for text in ('{broken\n', '{}', '[]\n', '{"kind":1,"kind":2}\n', '{"tokens":NaN}\n'):
            with self.subTest(text=text):
                path.write_text(text)
                with self.assertRaises((ValueError, TypeError)):
                    checkpoint.strict_events(path)

    def test_chain_corruption_and_unrelated_checkpoint_fail_closed(self):
        checkpoint.save(self.root, {'phase': 'worker_done'})
        path = self.root / 'checkpoint.jsonl'
        row = json.loads(path.read_text())
        row['sequence'] = 3
        path.write_text(json.dumps(row) + '\n')
        with self.assertRaisesRegex(ValueError, 'chain corrupted'):
            checkpoint.load(self.root)

    def test_missing_checkpoint_does_not_reconstruct_approval_from_files(self):
        (self.root / 'plan.json').write_text('{"approved":true}')
        with self.assertRaisesRegex(ValueError, 'checkpoint missing'):
            checkpoint.load(self.root)

    def test_read_only_binding_includes_nested_content_and_modes(self):
        directory = self.root / 'dependencies'
        directory.mkdir()
        file = directory / 'module.js'
        file.write_text('first')
        before = checkpoint.file_binding(directory)
        file.write_text('second')
        self.assertNotEqual(before, checkpoint.file_binding(directory))
        before = checkpoint.file_binding(directory)
        file.chmod(0o700)
        self.assertNotEqual(before, checkpoint.file_binding(directory))

    def test_registration_requires_original_canonical_directory(self):
        checkpoint.register(self.root, 'plan', self.root / 'original')
        checkpoint.register(self.root, 'plan', self.root / 'original')
        with self.assertRaisesRegex(ValueError, 'registered'):
            checkpoint.register(self.root, 'plan', self.root / 'replacement')

class ControllerRecoveryGuards(unittest.TestCase):
    def setUp(self):
        from test_factory_v2 import ControllerTests
        self.fixture = ControllerTests('test_contract_first_serial_three_and_original_dirty_unchanged')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def interrupt(self, phase):
        from unittest.mock import patch

        import factory_v2
        class Crash(BaseException):
            pass
        original = factory_v2._save_checkpoint
        def crash(path, state):
            original(path, state)
            if state['active'].get('phase') == phase or state['phase'] == phase:
                raise Crash()
        with patch.object(factory_v2, '_save_checkpoint', crash), self.assertRaises(Crash):
            self.fixture.run_change()

    def test_unclean_elapsed_interval_consumes_budget_without_another_model(self):
        from unittest.mock import patch

        import factory_v2
        self.interrupt('worker_done')
        calls = list(self.fixture.calls)
        current = factory_v2.time.time()
        with patch.object(factory_v2.time, 'time', return_value=current + 1000):
            result = self.fixture.run_change(resume=True)
        self.assertEqual(result['status'], 'blocked', result)
        self.assertEqual(self.fixture.calls, calls)
        self.assertIn('budget exhausted', result['reason'])

    def test_interrupted_arbitrary_prune_is_held_without_replay(self):
        self.interrupt('prune_pending')
        calls = list(self.fixture.calls)
        result = self.fixture.run_change(resume=True)
        self.assertEqual(result['status'], 'blocked', result)
        self.assertEqual(self.fixture.calls, calls)
        self.assertIn('callback is held', result['reason'])

    def test_changed_read_only_runtime_rejects_resume(self):
        directory = self.fixture.root / 'runtime'
        directory.mkdir()
        module = directory / 'module.js'
        module.write_text('before')
        # This deliberately uses the same host callback and read-only declaration.
        result = self.fixture.run_change(read_only=[directory])
        self.assertEqual(result['status'], 'ready_for_final_merge', result)
        module.write_text('after')
        with self.assertRaisesRegex(ValueError, 'exact runtime bindings'):
            self.fixture.run_change(read_only=[directory], resume=True)


    def test_second_worker_receipt_crash_keeps_nonzero_cumulative_delta(self):
        from unittest.mock import patch

        import factory_v2
        class Crash(BaseException):
            pass
        original = factory_v2.receipt
        count = 0
        def crash(*args, **kwargs):
            nonlocal count
            row = original(*args, **kwargs)
            if args[2] == 'worker':
                count += 1
                if count == 2:
                    raise Crash()
            return row
        with patch.object(factory_v2, 'receipt', crash), self.assertRaises(Crash):
            self.fixture.run_change()
        result = self.fixture.run_change(resume=True)
        self.assertEqual(result['status'], 'ready_for_final_merge', result)
        rows = factory_v2.read_events(self.fixture.run_dir / 'usage.jsonl')
        self.assertEqual(len(rows), 4)
        self.assertEqual([row['observed_tokens'] for row in rows if row['skill'] == 'worker'], [64, 64])
        self.assertEqual(result['metrics']['observed_tokens'], 136)


    def test_accepted_event_crash_is_not_counted_twice(self):
        from unittest.mock import patch

        import factory_v2
        class Crash(BaseException):
            pass
        original = factory_v2.append_durable
        def crash(path, event):
            original(path, event)
            if event.get('kind') == 'accepted':
                raise Crash()
        with patch.object(factory_v2, 'append_durable', crash), self.assertRaises(Crash):
            self.fixture.run_change()
        result = self.fixture.run_change(resume=True)
        self.assertEqual(result['status'], 'ready_for_final_merge', result)
        events = factory_v2.read_events(self.fixture.run_dir / 'events.jsonl')
        accepted = [event['slice'] for event in events if event.get('kind') == 'accepted']
        self.assertEqual(accepted, ['contracts', 'feature'])


    def test_stale_resume_cannot_spend_after_another_resume_advances(self):
        import threading
        from unittest.mock import patch

        import factory_v2
        self.interrupt('initial')
        original = factory_v2._load_checkpoint
        loaded, proceed = threading.Event(), threading.Event()
        outcomes = []
        def pause(path):
            state = original(path)
            if threading.current_thread().name == 'stale-resume':
                loaded.set()
                if not proceed.wait(30):
                    raise RuntimeError('test resume coordination timed out')
            return state
        def resume():
            outcomes.append(self.fixture.run_change(resume=True))
        with patch.object(factory_v2, '_load_checkpoint', pause):
            stale = threading.Thread(target=resume, name='stale-resume')
            stale.start()
            self.assertTrue(loaded.wait(10))
            try:
                active = self.fixture.run_change(resume=True)
                self.assertEqual(active['status'], 'ready_for_final_merge', active)
                calls = list(self.fixture.calls)
            finally:
                proceed.set()
                stale.join(30)
        self.assertFalse(stale.is_alive())
        self.assertEqual(self.fixture.calls, calls)
        self.assertEqual(outcomes[0]['status'], 'blocked')
        self.assertIn('stale', outcomes[0]['reason'])

    def test_gate_failure_event_crash_is_not_counted_twice(self):
        from unittest.mock import patch

        import factory_v2
        class Crash(BaseException):
            pass
        original = factory_v2.append_durable
        original_gates = self.fixture.gates
        self.fixture.plan['slices'][0]['budget'].update(retries=1, tokens=200)
        failures = 0
        def gates(*args, **kwargs):
            nonlocal failures
            evidence = original_gates(*args, **kwargs)
            if args[2] == 'contracts' and failures < 2:
                failures += 1
                evidence['status'] = 'fail'
            return evidence
        self.fixture.gates = gates
        def crash(path, event):
            original(path, event)
            if event.get('kind') == 'gate_failure':
                raise Crash()
        with patch.object(factory_v2, 'append_durable', crash), self.assertRaises(Crash):
            self.fixture.run_change()
        result = self.fixture.run_change(resume=True)
        self.assertEqual(result['status'], 'ready_for_final_merge', result)
        failures = [event for event in factory_v2.read_events(self.fixture.run_dir / 'events.jsonl')
                    if event.get('kind') == 'gate_failure']
        self.assertEqual(len(failures), 1)

    def test_unpaid_clone_before_checkout_resumes_without_discarding_work(self):
        from unittest.mock import patch

        import factory_v2
        class Crash(BaseException):
            pass
        original = factory_v2._git
        def crash(root, *args):
            output = original(root, *args)
            if args and args[0] == 'clone':
                raise Crash()
            return output
        with patch.object(factory_v2, '_git', crash), self.assertRaises(Crash):
            self.fixture.run_change()
        self.assertEqual(self.fixture.calls, [])
        result = self.fixture.run_change(resume=True)
        self.assertEqual(result['status'], 'ready_for_final_merge', result)


if __name__ == '__main__':
    unittest.main()
