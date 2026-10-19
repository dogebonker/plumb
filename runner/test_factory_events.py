"""Authenticated wake-ups never supply execution or approval authority."""
import hashlib
import hmac
import json
import tempfile
import threading
import time
import unittest
import uuid
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from runner import factory_events as events


class EventTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.queue = events.Queue(Path(self.tmp.name) / 'queue.sqlite')
        self.route = {'provider': 'github', 'repository_id': '7', 'repo': '/trusted/clone',
                      'approvers': ['alice'], 'secret_env': 'FACTORY_TEST_SECRET', 'max_steps': 3}
        self.now = time.time()

    def delivery(self, payload=None, *, route=None, ident=None, now=None):
        route = route or self.route
        body = json.dumps(payload or {'repository': {'id': 7}, 'action': 'closed',
                                     'pull_request': {'merged': True}}).encode()
        signature = hmac.new(b'secret', body, hashlib.sha256).hexdigest()
        headers = ({'X-Hub-Signature-256': 'sha256=' + signature, 'X-GitHub-Event': 'pull_request',
                    'X-GitHub-Delivery': ident or str(uuid.uuid4())} if route['provider'] == 'github' else
                   {'Linear-Signature': signature, 'Linear-Event': 'Issue', 'Linear-Delivery': ident or str(uuid.uuid4())})
        return events.ingest(self.queue, 'project', route, headers, body, b'secret', now=self.now if now is None else now)

    def test_verified_delivery_deduplicates_and_cannot_rebind(self):
        ident = str(uuid.uuid4())
        self.assertEqual(self.delivery(ident=ident)['status'], 'queued')
        self.assertEqual(self.delivery(ident=ident)['status'], 'duplicate')
        self.assertEqual(self.delivery()['status'], 'duplicate')  # unsigned ID change cannot replay body
        with self.assertRaises(ValueError):
            self.delivery({'repository': {'id': 7}, 'action': 'opened'}, ident=ident)
        self.assertEqual(len(self.queue.jobs()), 1)

    def test_signature_and_repository_scope_rejected_before_enqueue(self):
        with self.assertRaises(ValueError):
            events.ingest(self.queue, 'project', self.route, {}, b'{}', b'secret', now=self.now)
        with self.assertRaises(ValueError):
            self.delivery({'repository': {'id': 8}})
        self.assertEqual(self.queue.jobs(), [])

    def test_linear_freshness_and_scope(self):
        route = {**self.route, 'provider': 'linear', 'organization_id': 'org', 'project_id': 'proj'}
        payload = {'organizationId': 'org', 'type': 'Issue', 'action': 'update',
                   'webhookTimestamp': int(self.now * 1000), 'data': {'projectId': 'proj'}}
        self.assertEqual(self.delivery(payload, route=route)['status'], 'queued')
        with self.assertRaises(ValueError):
            self.delivery({**payload, 'webhookTimestamp': int((self.now - 61) * 1000)}, route=route)
        with self.assertRaises(ValueError):
            self.delivery({**payload, 'data': {'projectId': 'other'}}, route=route)

    def test_progress_schedules_next_tick_waiting_stops_and_no_payload_dispatched(self):
        self.delivery()
        seen = []
        def dispatch(route):
            seen.append(route)
            return {'status': 'progress'}
        self.assertEqual(events.process_one(self.queue, {'project': self.route}, dispatch)['status'], 'progress')
        self.assertEqual(seen, [self.route])
        self.assertEqual(len([j for j in self.queue.jobs() if j['state'] == 'pending']), 1)
        events.process_one(self.queue, {'project': self.route}, lambda route: {'status': 'waiting'})
        self.assertEqual(events.process_one(self.queue, {'project': self.route}, dispatch)['status'], 'idle')

    def test_new_event_while_running_is_not_lost(self):
        self.delivery()
        def dispatch(route):
            self.delivery({'repository': {'id': 7}, 'action': 'synchronize'})
            return {'status': 'waiting'}
        events.process_one(self.queue, {'project': self.route}, dispatch)
        self.assertEqual(len([j for j in self.queue.jobs() if j['state'] == 'pending']), 1)

    def test_config_changes_fail_closed_and_crashed_running_job_is_not_replayed(self):
        self.delivery()
        called = []
        report = events.process_one(self.queue, {'project': {**self.route, 'approvers': ['mallory']}},
                                    lambda route: called.append(route))
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(called, [])
        self.delivery({'repository': {'id': 7}, 'action': 'opened'})
        claim = self.queue.claim(self.now + 1)
        self.assertIsNotNone(claim)
        self.delivery({'repository': {'id': 7}, 'action': 'reopened'})
        self.assertIsNone(self.queue.claim(self.now + 2))

    def test_budget_stops_runaway_progress_and_unknown_results_do_not_retry(self):
        self.delivery()
        for _ in range(3):
            result = events.process_one(self.queue, {'project': self.route}, lambda route: {'status': 'progress'})
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(events.process_one(self.queue, {'project': self.route}, lambda route: {})['status'], 'idle')
        self.delivery({'repository': {'id': 7}, 'action': 'new'})
        self.assertEqual(events.process_one(self.queue, {'project': self.route}, lambda route: {})['status'], 'failed')

    def test_concurrent_self_events_cannot_reset_step_limit_or_retry_failure(self):
        self.delivery()
        calls = []
        def dispatch(route):
            calls.append(1)
            self.delivery({'repository': {'id': 7}, 'action': f'push-{len(calls)}'})
            return {'status': 'progress'}
        for _ in range(3):
            result = events.process_one(self.queue, {'project': self.route}, dispatch)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(events.process_one(self.queue, {'project': self.route}, dispatch)['status'], 'idle')
        self.assertEqual(len(calls), 3)

    def test_events_arriving_before_failure_are_held_and_busy_keeps_backoff(self):
        self.delivery()
        def fail(route):
            self.delivery({'repository': {'id': 7}, 'action': 'during-failure'})
            return {'status': 'failed'}
        events.process_one(self.queue, {'project': self.route}, fail)
        self.assertEqual(events.process_one(self.queue, {'project': self.route}, fail)['status'], 'idle')
        self.delivery({'repository': {'id': 7}, 'action': 'after-failure'})
        def busy(route):
            self.delivery({'repository': {'id': 7}, 'action': 'during-busy'})
            return {'status': 'busy'}
        events.process_one(self.queue, {'project': self.route}, busy)
        pending = [j for j in self.queue.jobs() if j['state'] == 'pending']
        self.assertEqual(len(pending), 1)
        self.assertGreaterEqual(pending[0]['available'], time.time() + 14)

    def test_http_acknowledges_only_durable_authenticated_enqueue(self):
        body = json.dumps({'repository': {'id': 7}}).encode()
        headers = {'X-Hub-Signature-256': 'sha256=' + hmac.new(b'secret', body, hashlib.sha256).hexdigest(),
                   'X-GitHub-Event': 'push', 'X-GitHub-Delivery': str(uuid.uuid4())}
        with patch.dict('os.environ', FACTORY_TEST_SECRET='secret'):
            server = ThreadingHTTPServer(('127.0.0.1', 0), events.receiver(self.queue, {'project': self.route}))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                conn.request('POST', '/hooks/project', body=body, headers=headers)
                response = conn.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.read())['status'], 'queued')
                conn.close()
                self.assertEqual(self.queue.jobs()[0]['state'], 'pending')
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_atomic_runner_checkpoint_preserves_old_state_on_replace_failure(self):
        from runner import factory_run
        target = Path(self.tmp.name) / 'heads.json'
        target.write_text('{"old":true}')
        with patch.object(factory_run.os, 'replace', side_effect=OSError('interrupted')), self.assertRaises(OSError):
            factory_run.write_json(target, {'new': True})
        self.assertEqual(json.loads(target.read_text()), {'old': True})


if __name__ == '__main__':
    unittest.main()
