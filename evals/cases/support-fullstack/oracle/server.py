"""Reference app, intentionally standard-library only."""
import hashlib
import json
import os
import secrets
import sqlite3
import sys
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DB = os.environ['DATABASE_PATH']
USERS = {f'{role}@{tenant}.test': {'email': f'{role}@{tenant}.test', 'role': role, 'tenant': tenant}
         for tenant in ('acme', 'north') for role in ('operator', 'customer')}
SESSIONS = {}
PASSWORD = hashlib.sha256(b'benchmark-pass').digest()

def connection():
    con = sqlite3.connect(DB, timeout=2)
    con.execute('PRAGMA foreign_keys=ON')
    return con

def reset():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    with connection() as con:
        con.execute('DROP TABLE IF EXISTS tickets')
        con.execute('CREATE TABLE tickets (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        for tenant, prefix in [('acme', 'T00'), ('north', 'T10')]:
            for number, title, status, priority in [(1, 'Password reset expired', 'open', 'high'), (2, 'Export stalls', 'pending', 'low')]:
                ticket = {'id': prefix + str(number), 'title': title, 'description': title + ' for our team.', 'status': status,
                          'priority': priority, 'assignee': None, 'customer': f'customer@{tenant}.test', 'tenant': tenant,
                          'version': 1, 'comments': [], 'history': [{'type': 'create', 'actor': f'customer@{tenant}.test'}]}
                con.execute('INSERT INTO tickets VALUES (?,?)', (ticket['id'], json.dumps(ticket)))

def visible(ticket, user):
    return ticket['tenant'] == user['tenant'] and (user['role'] == 'operator' or ticket['customer'] == user['email'])

def text(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError('Required text is empty or too long')
    return value.strip()

class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, cookie=None):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            data = Path(__file__).with_name('index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.api()

    def do_POST(self):
        self.api()

    def do_PATCH(self):
        self.api()

    def api(self):
        route = urlsplit(self.path)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 10000:
                raise ValueError('Request too large')
            body = json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(body, dict):
                raise TypeError('Object required')
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookie['session'].value if 'session' in cookie else ''
            user = SESSIONS.get(token)
            if route.path == '/health' and self.command == 'GET':
                return self.send(200, {'ready': True})
            if route.path == '/api/login' and self.command == 'POST':
                email = body.get('email')
                if email not in USERS or not isinstance(body.get('password'), str) or not secrets.compare_digest(hashlib.sha256(body['password'].encode()).digest(), PASSWORD):
                    return self.send(401, {'error': 'Invalid credentials'})
                token = secrets.token_urlsafe(32)
                SESSIONS[token] = USERS[email]
                return self.send(200, {'user': USERS[email]}, f'session={token}; HttpOnly; SameSite=Lax; Path=/')
            if not user:
                return self.send(401, {'error': 'Log in required'})
            if route.path == '/api/logout' and self.command == 'POST':
                SESSIONS.pop(token, None)
                return self.send(200, {}, 'session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/')
            if route.path == '/api/me' and self.command == 'GET':
                return self.send(200, {'user': user})
            with connection() as con:
                if self.command != 'GET':
                    con.execute('BEGIN IMMEDIATE')
                rows = [json.loads(row[0]) for row in con.execute('SELECT data FROM tickets ORDER BY id')]
                if route.path == '/api/tickets' and self.command == 'GET':
                    filters = parse_qs(route.query)
                    rows = [t for t in rows if visible(t, user)]
                    for name in ('status', 'priority'):
                        value = filters.get(name, ['all'])[0]
                        if value not in ('', 'all'):
                            rows = [t for t in rows if t[name] == value]
                    q = filters.get('q', [''])[0].lower()
                    return self.send(200, {'tickets': [t for t in rows if q in (t['title'] + ' ' + t['description']).lower()]})
                if route.path == '/api/tickets' and self.command == 'POST':
                    if set(body) != {'title', 'description'}:
                        raise ValueError('Only title and description accepted')
                    ticket = {'id': 'T' + secrets.token_hex(6), 'title': text(body['title'], 120), 'description': text(body['description'], 4000),
                              'status': 'open', 'priority': 'medium', 'assignee': None, 'tenant': user['tenant'], 'customer': user['email'],
                              'version': 1, 'comments': [], 'history': [{'type': 'create', 'actor': user['email']}]}
                    con.execute('INSERT INTO tickets VALUES (?,?)', (ticket['id'], json.dumps(ticket)))
                    con.commit()
                    return self.send(201, {'ticket': ticket})
                parts = route.path.strip('/').split('/')
                ticket = next((t for t in rows if len(parts) >= 3 and t['id'] == parts[2] and visible(t, user)), None)
                if not ticket or parts[:2] != ['api', 'tickets']:
                    return self.send(404, {'error': 'Ticket not found'})
                if self.command == 'GET' and len(parts) == 3:
                    return self.send(200, {'ticket': ticket})
                allowed = {'version', 'text'} if parts[3:] == ['comments'] else {'version', 'title', 'description', 'status', 'priority', 'assignee'}
                if not set(body) <= allowed or 'version' not in body or type(body['version']) is not int:
                    raise ValueError('Invalid fields or version')
                if self.command == 'PATCH' and user['role'] != 'operator':
                    return self.send(403, {'error': 'Operator required'})
                if body['version'] != ticket['version']:
                    return self.send(409, {'error': 'Ticket changed; reload before retrying'})
                if self.command == 'POST' and parts[3:] == ['comments']:
                    ticket['comments'].append({'text': text(body.get('text'), 2000), 'actor': user['email']})
                    event, code = 'comment', 201
                elif self.command == 'PATCH' and len(parts) == 3:
                    for key in ('title', 'description'):
                        if key in body:
                            ticket[key] = text(body[key], 120 if key == 'title' else 4000)
                    for key, options in [('status', ('open', 'pending', 'resolved')), ('priority', ('low', 'medium', 'high')), ('assignee', (None, f'operator@{user["tenant"]}.test'))]:
                        if key in body:
                            if body[key] not in options:
                                raise ValueError('Invalid ' + key)
                            ticket[key] = body[key]
                    event, code = 'edit', 200
                else:
                    return self.send(404, {'error': 'Endpoint not found'})
                ticket['version'] += 1
                ticket['history'].append({'type': event, 'actor': user['email']})
                con.execute('UPDATE tickets SET data=? WHERE id=?', (json.dumps(ticket), ticket['id']))
                con.commit()
                return self.send(code, {'ticket': ticket})
        except (ValueError, KeyError, TypeError):
            self.send(400, {'error': 'Invalid request fields'})
        except sqlite3.Error:
            self.send(503, {'error': 'Storage unavailable; changes were not saved'})

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset()
    else:
        with connection() as con:
            con.execute('SELECT data FROM tickets LIMIT 1').fetchall()
        ThreadingHTTPServer((os.environ.get('HOST', '127.0.0.1'), int(os.environ['PORT'])), Handler).serve_forever()
