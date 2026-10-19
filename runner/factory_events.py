"""Authenticated webhooks wake existing approved work; payloads grant no authority."""
import argparse
import fcntl
import hashlib
import hmac
import json
import os
import sqlite3
import sys
import tempfile
import time
import uuid
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit.v2_contract import strict_json

MAX_BODY = 1024 * 1024


def fingerprint(route):
    return hashlib.sha256(json.dumps(route, sort_keys=True).encode()).hexdigest()


class Queue:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path.touch(mode=0o600, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS deliveries (
                    provider TEXT, delivery TEXT, route TEXT, body_sha TEXT, received REAL,
                    PRIMARY KEY(provider,delivery), UNIQUE(provider,route,body_sha));
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY, route TEXT, binding TEXT, state TEXT,
                    available REAL, step INTEGER, owner TEXT, detail TEXT);
                CREATE UNIQUE INDEX IF NOT EXISTS one_pending ON jobs(route) WHERE state='pending';
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=1)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def put(db, route, binding, now, step=0):
        pending = db.execute("SELECT binding FROM jobs WHERE route=? AND state='pending'", (route,)).fetchone()
        if pending and pending['binding'] != binding:
            raise ValueError('pending route configuration changed; reconcile it before admission')
        db.execute("INSERT OR IGNORE INTO jobs(route,binding,state,available,step) VALUES(?,?,'pending',?,?)",
                   (route, binding, now, step))
        db.execute("UPDATE jobs SET step=max(step,?),available=max(available,?) WHERE route=? AND state='pending'",
                   (step, now, route))

    def enqueue(self, route, binding, provider, delivery, body_sha, now):
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT route,body_sha FROM deliveries WHERE provider=? AND delivery=?',
                               (provider, delivery)).fetchone()
            if prior:
                if tuple(prior) != (route, body_sha):
                    raise ValueError('delivery ID rebound to another payload or route')
                return {'status': 'duplicate'}
            if db.execute('SELECT 1 FROM deliveries WHERE provider=? AND route=? AND body_sha=?',
                          (provider, route, body_sha)).fetchone():
                return {'status': 'duplicate'}
            db.execute('INSERT INTO deliveries VALUES(?,?,?,?,?)', (provider, delivery, route, body_sha, now))
            self.put(db, route, binding, now)
        return {'status': 'queued'}

    def claim(self, now):
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("""SELECT * FROM jobs AS j WHERE state='pending' AND available<=?
                AND NOT EXISTS(SELECT 1 FROM jobs AS r WHERE r.route=j.route AND r.state='running')
                ORDER BY id LIMIT 1""", (now,)).fetchone()
            if row is None:
                return None
            job = dict(row, owner=uuid.uuid4().hex)
            db.execute("UPDATE jobs SET state='running',owner=? WHERE id=?", (job['owner'], job['id']))
            return job

    def finish(self, job, result, now, *, again=False, delay=0):
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            changed = db.execute("UPDATE jobs SET state=?,detail=? WHERE id=? AND owner=? AND state='running'",
                                 (result['status'], json.dumps(result), job['id'], job['owner'])).rowcount
            if changed != 1:
                raise ValueError('stale job completion')
            if again:
                self.put(db, job['route'], job['binding'], now + delay,
                         job['step'] + (result['status'] == 'progress'))
            elif result['status'] in {'blocked', 'failed'}:
                db.execute("UPDATE jobs SET state='blocked',detail=? WHERE route=? AND state='pending'",
                           (json.dumps({'reason': 'preceding work failed or exhausted its wake limit'}), job['route']))

    def jobs(self):
        with closing(self.connect()) as db:
            return [dict(row) for row in db.execute('SELECT * FROM jobs ORDER BY id')]


def ingest(queue, route_id, route, headers, body, secret, *, now=None):
    now = time.time() if now is None else now
    if not isinstance(body, bytes) or len(body) > MAX_BODY or not secret:
        raise ValueError('invalid body or missing server-side secret')
    headers = {key.lower(): value for key, value in headers.items()}
    provider = route['provider']
    if provider not in {'github', 'linear'}:
        raise ValueError('unsupported provider')
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    signature = headers.get('x-hub-signature-256' if provider == 'github' else 'linear-signature', '')
    if not hmac.compare_digest(signature, ('sha256=' if provider == 'github' else '') + expected):
        raise ValueError('invalid webhook signature')
    delivery = str(uuid.UUID(headers.get('x-github-delivery' if provider == 'github' else 'linear-delivery', '')))
    data = strict_json(body.decode('utf-8'))
    if not isinstance(data, dict):
        raise TypeError('webhook body must be an object')
    if provider == 'github':
        repo = data.get('repository')
        if not isinstance(repo, dict) or type(repo.get('id')) is not int or str(repo['id']) != route['repository_id']:
            raise ValueError('repository outside configured route')
        event = headers.get('x-github-event')
        if event not in {'push', 'pull_request', 'pull_request_review', 'issues', 'check_suite', 'check_run'}:
            return {'status': 'ignored'}
    else:
        timestamp = data.get('webhookTimestamp')
        if type(timestamp) is not int or abs(now * 1000 - timestamp) > 60_000:
            raise ValueError('stale or invalid Linear timestamp')
        issue = data.get('data')
        if (data.get('organizationId') != route['organization_id'] or not isinstance(issue, dict)
                or issue.get('projectId') != route['project_id']):
            raise ValueError('Linear workspace/project outside configured route')
        if data.get('type') != 'Issue' or headers.get('linear-event') != 'Issue' or data.get('action') not in {'create', 'update', 'remove'}:
            return {'status': 'ignored'}
    return queue.enqueue(route_id, fingerprint(route), provider, delivery, hashlib.sha256(body).hexdigest(), now)


def dispatch_legacy(route):
    from runner import factory_run
    repo = Path(route['repo'])
    identity = factory_run.run(repo, 'gh', 'api', 'repos/{owner}/{repo}', '--jq', '.id').strip()
    if identity != route['repository_id']:
        raise ValueError('configured clone does not match repository ID')
    with tempfile.TemporaryDirectory(prefix='factory-pass-') as scratch:
        report = Path(scratch) / 'factory-pass.json'
        code = factory_run.main([str(repo), '--approvers', ','.join(route['approvers']), '--report', str(report)])
        if code or not report.is_file():
            raise RuntimeError('runner failed without a usable structured report')
        return strict_json(report.read_text())


def process_one(queue, routes, dispatch=dispatch_legacy):
    with queue.path.with_suffix('.worker.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'busy'}
        job = queue.claim(time.time())
        if job is None:
            return {'status': 'idle'}
        result = {'status': 'failed'}
        try:
            route = routes.get(job['route'])
            if not route or fingerprint(route) != job['binding']:
                result = {'status': 'blocked', 'reason': 'route changed; operator reconciliation required'}
            else:
                result = dispatch(route)
                if not isinstance(result, dict) or result.get('status') not in {'progress', 'busy', 'waiting', 'blocked', 'idle', 'failed'}:
                    raise ValueError('invalid dispatcher result')
                if result['status'] == 'progress' and job['step'] + 1 >= route['max_steps']:
                    result = {**result, 'status': 'blocked', 'reason': 'wake chain step limit reached'}
        except Exception as error:  # noqa: BLE001 - preserve durable failure, never replay ambiguous work
            result = {'status': 'failed', 'reason': str(error)}
        queue.finish(job, result, time.time(), again=result['status'] in {'progress', 'busy'},
                     delay=15 if result['status'] == 'busy' else 0)
        return result


def configuration(path):
    routes = strict_json(Path(path).read_text())
    if not isinstance(routes, dict) or not routes:
        raise ValueError('expected nonempty route map')
    for ident, route in routes.items():
        if not isinstance(ident, str) or not ident or '/' in ident or not isinstance(route, dict):
            raise ValueError('invalid configured route')
        provider = route.get('provider')
        keys = {'provider', 'repo', 'approvers', 'secret_env', 'repository_id', 'max_steps'}
        keys |= {'organization_id', 'project_id'} if provider == 'linear' else set()
        if provider not in {'github', 'linear'} or set(route) != keys:
            raise ValueError('invalid route fields')
        if (not isinstance(route['repo'], str) or not Path(route['repo']).is_absolute()
                or not isinstance(route['approvers'], list) or not route['approvers']
                or any(not isinstance(x, str) or not x.strip() or ',' in x for x in route['approvers'])
                or type(route['max_steps']) is not int or not 1 <= route['max_steps'] <= 1000
                or any(not isinstance(route[x], str) or not route[x] for x in keys - {'approvers', 'max_steps'})):
            raise ValueError('invalid route values')
    return routes


def receiver(queue, routes):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(2)

        def log_message(self, *_):
            pass  # Webhook URLs/headers and ticket bodies do not enter request logs.

        def do_POST(self):
            route_id = self.path.removeprefix('/hooks/') if self.path.startswith('/hooks/') else ''
            if route_id not in routes:
                self.send_error(404)
                return
            try:
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or not lengths[0].isdigit() or not 0 < int(lengths[0]) <= MAX_BODY or self.headers.get('Transfer-Encoding'):
                    raise ValueError('invalid Content-Length or transfer encoding')
                if any(len(self.headers.get_all(name)) != 1 for name in self.headers):
                    raise ValueError('duplicate request headers')
                body = self.rfile.read(int(lengths[0]))
                if len(body) != int(lengths[0]):
                    raise ValueError('incomplete request body')
                route = routes[route_id]
                secret = os.environ.get(route['secret_env'], '').encode()
                result = ingest(queue, route_id, route, dict(self.headers), body, secret)
                encoded = json.dumps(result).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            except (ValueError, OSError, KeyError, TypeError):
                self.send_error(400, 'webhook rejected')
            except sqlite3.Error:
                self.send_error(503, 'durable queue unavailable')
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['serve', 'worker', 'status'])
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    queue = Queue(args.db)
    if args.action == 'status':
        print(json.dumps(queue.jobs(), indent=2))
        return
    if not args.config:
        parser.error('--config is required')
    routes = configuration(args.config)
    if args.action == 'serve':
        with ThreadingHTTPServer(('127.0.0.1', args.port), receiver(queue, routes)) as server:
            server.serve_forever()
    else:
        while True:
            result = process_one(queue, routes)
            if args.once:
                print(json.dumps(result, indent=2))
                return
            if result['status'] != 'progress':
                time.sleep(1)


if __name__ == '__main__':
    main()
