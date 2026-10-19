"""Gloam reference: standard-library HTTP server and SQLite, nothing else."""
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

DB = os.environ['DATABASE_PATH']
PASSWORD = hashlib.sha256(b'benchmark-pass').digest()
SESSIONS = {}
# ponytail: one lock serializes all storage work; arrival order is the lock order. Per-scene locks if tables grow.
LOCK = threading.Lock()
SCHEMA = """
CREATE TABLE tables (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE people (email TEXT PRIMARY KEY, table_id TEXT NOT NULL REFERENCES tables(id), role TEXT NOT NULL,
                     character TEXT, departed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE scenes (id INTEGER PRIMARY KEY AUTOINCREMENT, table_id TEXT NOT NULL REFERENCES tables(id),
                     title TEXT NOT NULL, state TEXT NOT NULL);
CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, scene_id INTEGER NOT NULL REFERENCES scenes(id),
                    author TEXT NOT NULL REFERENCES people(email), body TEXT NOT NULL, in_character INTEGER NOT NULL,
                    speaker TEXT NOT NULL, recipient TEXT, version INTEGER NOT NULL, created_at TEXT NOT NULL,
                    veiled INTEGER NOT NULL DEFAULT 0, client_key TEXT, UNIQUE (author, client_key));
"""
SEED = {
    'salt-road': ('The Salt Road', 'keeper@saltroad.test',
                  [('ash@saltroad.test', 'Marrow'), ('bryn@saltroad.test', 'Sister Vey'), ('cato@saltroad.test', 'Old Tam')],
                  'The Drowned Mile', 'Marrow counts the mile markers as the water climbs past the third one.'),
    'neon-fathoms': ('Neon Fathoms', 'keeper@fathoms.test', [('dana@fathoms.test', 'Kestrel')],
                     'Pressure Drop', 'Kestrel taps the gauge. The needle keeps sinking.'),
}


class Refused(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def connect():
    # mode=rw never creates a database: a missing file refuses to start instead of starting empty.
    con = sqlite3.connect(f'file:{DB}?mode=rw', uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def reset():
    path = Path(DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    for stale in (path, Path(DB + '-journal')):
        stale.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    with con:
        con.executescript(SCHEMA)
        for table, (name, keeper, players, scene, body) in SEED.items():
            con.execute('INSERT INTO tables VALUES (?,?)', (table, name))
            con.execute('INSERT INTO people (email, table_id, role) VALUES (?,?,?)', (keeper, table, 'keeper'))
            con.executemany('INSERT INTO people (email, table_id, role, character) VALUES (?,?,?,?)',
                            [(email, table, 'player', character) for email, character in players])
            scene_id = con.execute('INSERT INTO scenes (table_id, title, state) VALUES (?,?,?)', (table, scene, 'open')).lastrowid
            con.execute('INSERT INTO posts (scene_id, author, body, in_character, speaker, version, created_at) VALUES (?,?,?,?,?,?,?)',
                        (scene_id, players[0][0], body, 1, players[0][1], 1, now()))
    con.close()


def check_storage():
    """Refuse to start on missing or damaged data; never repair, reseed or overwrite."""
    try:
        con = connect()
        result = con.execute('PRAGMA quick_check').fetchone()[0]
        if result != 'ok':
            raise sqlite3.DatabaseError(result)
        for table in ('tables', 'people', 'scenes', 'posts'):
            con.execute(f'SELECT count(*) FROM {table}').fetchone()
        con.close()
    except sqlite3.Error as error:
        sys.exit(f'Gloam will not start: the campaign data at {DB} is missing or damaged ({error}). Nothing was changed.')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def text(value, limit, message):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise Refused(400, message)
    return value.strip()


def visible(post, user):
    return post['recipient'] is None or user['email'] in (post['author'], post['recipient'])


def post_json(con, post, user):
    later = con.execute('SELECT author, recipient FROM posts WHERE scene_id=? AND id>? AND author!=?',
                        (post['scene_id'], post['id'], post['author'])).fetchall()
    canon = any(row['recipient'] is None or post['author'] in (row['author'], row['recipient']) for row in later)
    author = con.execute('SELECT departed FROM people WHERE email=?', (post['author'],)).fetchone()
    return {'id': post['id'], 'scene': post['scene_id'], 'body': '' if post['veiled'] else post['body'],
            'in_character': bool(post['in_character']), 'speaker': post['speaker'], 'to': post['recipient'],
            'version': post['version'], 'created_at': post['created_at'], 'veiled': bool(post['veiled']),
            'canon': canon, 'mine': post['author'] == user['email'], 'departed': bool(author['departed'])}


def scene_json(con, scene, user, posts=True):
    data = {'id': scene['id'], 'title': scene['title'], 'state': scene['state']}
    if posts:
        rows = con.execute('SELECT * FROM posts WHERE scene_id=? ORDER BY id', (scene['id'],)).fetchall()
        data['posts'] = [post_json(con, row, user) for row in rows if visible(row, user)]
    return data


def person(con, email):
    row = con.execute('SELECT * FROM people WHERE email=?', (email,)).fetchone()
    return dict(row) if row else None


def scene_for(con, scene_id, user):
    row = con.execute('SELECT * FROM scenes WHERE id=? AND table_id=?', (scene_id, user['table'])).fetchone()
    if not row:
        raise Refused(404, 'That scene isn\'t at your table.')
    return row


def me(con, user):
    roster = con.execute('SELECT email, role, character, departed FROM people WHERE table_id=? ORDER BY role DESC, email',
                         (user['table'],)).fetchall()
    name = con.execute('SELECT name FROM tables WHERE id=?', (user['table'],)).fetchone()['name']
    return {'email': user['email'], 'role': user['role'], 'table': user['table'], 'table_name': name,
            'character': user['character'], 'roster': [dict(row) | {'departed': bool(row['departed'])} for row in roster]}


def route(con, method, parts, query, body, user):
    if parts == ['me'] and method == 'GET':
        return 200, {'user': me(con, user)}
    if parts[:1] == ['tables'] and len(parts) >= 3:
        if unquote(parts[1]) != user['table']:
            raise Refused(404, 'That table isn\'t yours.')
        if parts[2:] == ['scenes'] and method == 'GET':
            rows = con.execute('SELECT * FROM scenes WHERE table_id=? ORDER BY id', (user['table'],)).fetchall()
            return 200, {'scenes': [scene_json(con, row, user, posts=False) for row in rows]}
        if parts[2:] == ['scenes'] and method == 'POST':
            if user['role'] != 'keeper':
                raise Refused(403, 'Only the Keeper starts a scene.')
            title = text(body.get('title'), 120, 'A scene needs a title.')
            scene_id = con.execute('INSERT INTO scenes (table_id, title, state) VALUES (?,?,?)', (user['table'], title, 'open')).lastrowid
            return 201, {'scene': scene_json(con, scene_for(con, scene_id, user), user)}
        if parts[2:] == ['search'] and method == 'GET':
            q = query.get('q', [''])[0].strip().lower()
            rows = con.execute('SELECT posts.* FROM posts JOIN scenes ON scenes.id=posts.scene_id '
                               'WHERE scenes.table_id=? AND posts.veiled=0 ORDER BY posts.id', (user['table'],)).fetchall()
            return 200, {'posts': [post_json(con, row, user) for row in rows if q and visible(row, user) and q in row['body'].lower()]}
        if parts[2:] == ['whispers']:
            # Whispers are scene posts with a recipient; this route lists or sends them the way the QA contract names.
            if method == 'POST':
                if not set(body) <= {'to', 'body', 'scene', 'in_character'} or not isinstance(body.get('to'), str):
                    raise Refused(400, 'A whisper needs someone to hear it.')
                scene = scene_for(con, int(body.get('scene')), user)
                if scene['state'] == 'drawn':
                    raise Refused(409, 'This scene has been drawn to a close. It stays as it was.')
                code, data = create_post(con, scene, {'body': body.get('body'), 'to': body['to'],
                                                      'in_character': bool(body.get('in_character', False))}, user)
                return code, {'whisper': data['post']}
            if method == 'GET':
                other, scene = query.get('with', [''])[0], scene_for(con, int(query['scene'][0]), user)
                rows = con.execute('SELECT * FROM posts WHERE scene_id=? AND recipient IS NOT NULL ORDER BY id', (scene['id'],)).fetchall()
                return 200, {'whispers': [post_json(con, row, user) | {'from': row['author']} for row in rows
                                          if visible(row, user) and {row['author'], row['recipient']} == {user['email'], other}]}
        if len(parts) == 4 and parts[2] == 'players' and method == 'DELETE':
            target = person(con, unquote(parts[3]))
            if user['role'] != 'keeper':
                raise Refused(403, 'Only the Keeper releases a player from the table.')
            if not target or target['table_id'] != user['table'] or target['role'] != 'player' or target['departed']:
                raise Refused(404, 'There is no such player at this table.')
            con.execute('UPDATE people SET departed=1 WHERE email=?', (target['email'],))
            for token, session in list(SESSIONS.items()):
                if session == target['email']:
                    SESSIONS.pop(token, None)
            return 200, {}
    if parts[:1] == ['scenes'] and len(parts) >= 2 and parts[1].isdigit():
        scene = scene_for(con, int(parts[1]), user)
        action = parts[2:]
        if not action and method == 'GET':
            return 200, {'scene': scene_json(con, scene, user)}
        if scene['state'] == 'drawn':
            raise Refused(409, 'This scene has been drawn to a close. It stays as it was.')
        if action == ['posts'] and method == 'POST':
            return create_post(con, scene, body, user)
        if action == ['xcard'] and method == 'POST':
            if body.get('post') is not None:
                target = con.execute('SELECT * FROM posts WHERE id=? AND scene_id=?', (body['post'], scene['id'])).fetchone()
                if not target or not visible(target, user):
                    raise Refused(404, 'That post isn\'t in this scene.')
                con.execute('UPDATE posts SET veiled=1 WHERE id=?', (target['id'],))
            con.execute('UPDATE scenes SET state=? WHERE id=?', ('paused', scene['id']))
            return 200, {'scene': scene_json(con, scene_for(con, scene['id'], user), user)}
        if action in (['resume'], ['close']) and method == 'POST':
            if user['role'] != 'keeper':
                raise Refused(403, 'Only the Keeper can do that.')
            if action == ['resume'] and scene['state'] != 'paused':
                raise Refused(409, 'This scene isn\'t paused.')
            con.execute('UPDATE scenes SET state=? WHERE id=?', ('open' if action == ['resume'] else 'drawn', scene['id']))
            return 200, {'scene': scene_json(con, scene_for(con, scene['id'], user), user)}
    if parts[:1] == ['posts'] and len(parts) == 2 and parts[1].isdigit() and method in ('PATCH', 'DELETE'):
        return change_post(con, method, int(parts[1]), body, user)
    raise Refused(404, 'Nothing lives at that address.')


def create_post(con, scene, body, user):
    if not set(body) <= {'body', 'in_character', 'to', 'character', 'key'} or not isinstance(body.get('in_character'), bool):
        raise Refused(400, 'A post needs text and whether it is in character.')
    words = text(body.get('body'), 20000, 'Write something first.')
    in_character = body['in_character']
    if in_character and scene['state'] == 'paused':
        raise Refused(409, 'The scene is paused. Out of character only, until the Keeper resumes.')
    recipient = body.get('to') or None
    if recipient is not None:
        target = person(con, recipient) if isinstance(recipient, str) else None
        allowed = target and target['table_id'] == user['table'] and not target['departed'] and target['email'] != user['email'] and (
            user['role'] == 'keeper' or target['role'] == 'keeper')
        if not allowed:
            raise Refused(403, 'Players whisper only to the Keeper.')
    character = body.get('character')
    if not in_character:
        speaker = user['email']
    elif user['role'] == 'keeper':
        speaker = text(character, 60, 'Name who is speaking.')
    else:
        if character not in (None, '', user['character']):
            raise Refused(403, f'You speak as {user["character"]} at this table.')
        speaker = user['character']
    key = body.get('key')
    if key is not None:
        sent = con.execute('SELECT * FROM posts WHERE author=? AND client_key=?', (user['email'], str(key))).fetchone()
        if sent:
            return 201, {'post': post_json(con, sent, user)}
    post_id = con.execute('INSERT INTO posts (scene_id, author, body, in_character, speaker, recipient, version, created_at, client_key) '
                          'VALUES (?,?,?,?,?,?,?,?,?)', (scene['id'], user['email'], words, int(in_character), speaker, recipient, 1, now(),
                                                         None if key is None else str(key))).lastrowid
    return 201, {'post': post_json(con, con.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone(), user)}


def change_post(con, method, post_id, body, user):
    row = con.execute('SELECT posts.* FROM posts JOIN scenes ON scenes.id=posts.scene_id WHERE posts.id=? AND scenes.table_id=?',
                      (post_id, user['table'])).fetchone()
    if not row or not visible(row, user):
        raise Refused(404, 'That post isn\'t here.')
    post = post_json(con, row, user)
    if row['author'] != user['email'] or row['veiled']:
        raise Refused(403, 'Only the author changes a post.')
    if scene_for(con, row['scene_id'], user)['state'] == 'drawn':
        raise Refused(409, 'This scene has been drawn to a close. It stays as it was.')
    if post['canon']:
        raise Refused(409, 'Someone has posted after this. It is canon now.')
    if method == 'DELETE':
        con.execute('DELETE FROM posts WHERE id=?', (post_id,))
        return 200, {}
    if not set(body) <= {'version', 'body'} or type(body.get('version')) is not int:
        raise Refused(400, 'An edit needs the version you started from.')
    if body['version'] != row['version']:
        return 409, {'error': 'Someone saved a newer version first. Gloam kept the newer text. Your edit is still here.', 'post': post}
    con.execute('UPDATE posts SET body=?, version=version+1 WHERE id=?', (text(body.get('body'), 20000, 'Write something first.'), post_id))
    return 200, {'post': post_json(con, con.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone(), user)}


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, cookie=None, kind='application/json', raw=None):
        data = raw if raw is not None else json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            return self.send(200, None, kind='text/html; charset=utf-8', raw=Path(__file__).with_name('index.html').read_bytes())
        self.api()

    def api(self):
        url = urlsplit(self.path)
        try:
            if url.path == '/health' and self.command == 'GET':
                return self.send(200, {'ready': True})
            length = int(self.headers.get('Content-Length') or 0)
            if length > 100000:
                raise Refused(413, 'That post is too long to send.')
            body = json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(body, dict):
                raise Refused(400, 'Send a JSON object.')
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookie['session'].value if 'session' in cookie else ''
            if url.path == '/api/login' and self.command == 'POST':
                with LOCK:
                    con = connect()
                    found = person(con, body.get('email')) if isinstance(body.get('email'), str) else None
                    con.close()
                password = body.get('password')
                if not found or not isinstance(password, str) or not secrets.compare_digest(hashlib.sha256(password.encode()).digest(), PASSWORD):
                    raise Refused(401, 'That email and password don\'t match.')
                if found['departed']:
                    raise Refused(403, 'You are no longer at this table.')
                token = secrets.token_urlsafe(32)
                SESSIONS[token] = found['email']
                user = {'email': found['email'], 'role': found['role'], 'table': found['table_id']}
                return self.send(200, {'user': user}, f'session={token}; HttpOnly; SameSite=Lax; Path=/')
            if token not in SESSIONS:
                raise Refused(401, 'Log in to see your table.')
            if url.path == '/api/logout' and self.command == 'POST':
                SESSIONS.pop(token, None)
                return self.send(200, {}, 'session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/')
            parts = url.path.strip('/').split('/')
            if parts[0] != 'api':
                raise Refused(404, 'Nothing lives at that address.')
            with LOCK:
                con = connect()
                try:
                    found = person(con, SESSIONS.get(token))
                    if not found or found['departed']:
                        SESSIONS.pop(token, None)
                        raise Refused(401, 'Log in to see your table.')
                    user = {'email': found['email'], 'role': found['role'], 'table': found['table_id'], 'character': found['character']}
                    with con:
                        code, data = route(con, self.command, parts[1:], parse_qs(url.query), body, user)
                finally:
                    con.close()
            self.send(code, data)
        except Refused as refusal:
            self.send(refusal.code, {'error': str(refusal)})
        except (ValueError, TypeError, KeyError):
            self.send(400, {'error': 'That request didn\'t make sense to Gloam.'})
        except sqlite3.Error:
            self.send(503, {'error': 'Gloam could not save that. Nothing was changed. Send it again.'})

    do_POST = do_PATCH = do_DELETE = api

if __name__ == '__main__':
    if sys.argv[1:] == ['reset']:
        reset()
    else:
        check_storage()
        ThreadingHTTPServer((os.environ.get('HOST', '127.0.0.1'), int(os.environ['PORT'])), Handler).serve_forever()
