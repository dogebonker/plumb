"""Trusted QA proxy. The grader launches its own copy; any copy in the product is ignored.

Listens on PORT. Requests under /qa go to the mapping's handle(request, product); every other
connection is relayed byte for byte to the product on 127.0.0.1:PRODUCT_PORT, so the product's
own pages, API and sockets pass through untouched. The mapping runs in worker child processes
(`qa_proxy.py worker`, sandboxed by the grader through QA_WORKER) that reach the product only by
asking this process over a pipe; only this process calls the product and appends each raw product
response to QA_RAW_LOG for the grader.
"""
import ast
import base64
import builtins
import http.client
import json
import os
import queue
import re
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
from email.message import Message
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

PRODUCT_PORT = int(os.environ.get('PRODUCT_PORT', '0'))
WORKERS = queue.Queue()
encode, decode = (lambda data: base64.b64encode(data).decode()), base64.b64decode
RAW_LOG = os.environ.get('QA_RAW_LOG')
MAPPING = Path(os.environ.get('QA_MAPPING') or Path(__file__).with_name('mapping.py'))
LOCK = threading.Lock()
# The mapping is plain functions over data: no imports, no classes, no dunders, no frame or format
# introspection, and only these names. The grader also runs the proxy in its own sandbox.
MODULES = {'json': json, 're': re, 'parse': urllib.parse}
MODULE_NAMES = {'json': {'loads', 'dumps', 'JSONDecodeError'},
                're': {'match', 'search', 'fullmatch', 'sub', 'split', 'findall', 'compile', 'escape', 'IGNORECASE'},
                'parse': {'quote', 'unquote', 'urlencode', 'parse_qs', 'parse_qsl', 'urlsplit'}}
BUILTINS = {name: getattr(builtins, name) for name in (
    'len', 'str', 'int', 'float', 'bool', 'dict', 'list', 'tuple', 'set', 'isinstance', 'range', 'enumerate', 'zip',
    'sorted', 'min', 'max', 'any', 'all', 'sum', 'map', 'filter', 'reversed', 'Exception', 'ValueError', 'KeyError',
    'TypeError', 'IndexError')}
BANNED_ATTRIBUTES = re.compile(r'_|(gi|cr|ag|f|tb|co)_|format$|format_map$|mro$')


def load_mapping():
    tree = ast.parse(MAPPING.read_text(), str(MAPPING))
    module_uses = {id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                   and isinstance(node.value, ast.Name) and node.attr in MODULE_NAMES.get(node.value.id, ())}
    for node in ast.walk(tree):
        bad = (isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.Global, ast.Nonlocal))
               or isinstance(node, ast.Name) and (node.id.startswith('_') or node.id in MODULES and id(node) not in module_uses)
               or isinstance(node, ast.Attribute) and BANNED_ATTRIBUTES.match(node.attr))
        if bad:
            sys.exit(f'qa/mapping.py line {node.lineno}: {ast.unparse(node)[:80]} is not allowed; '
                     'a mapping reaches the product only through the client it is given')
    namespace = {'__builtins__': BUILTINS, **MODULES}
    exec(compile(tree, str(MAPPING), 'exec'), namespace)  # noqa: S102 — AST-limited mapping inside the native worker sandbox
    return namespace['handle']


def record(entry):
    if RAW_LOG:
        line = (json.dumps(entry) + '\n').encode()
        with LOCK:
            fd = os.open(RAW_LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            try:
                os.write(fd, line)
            finally:
                os.close(fd)


class Product:
    """The mapping's only route to the product. Sends the caller's cookies unless headers override them."""

    def __init__(self, account, cookie, request):
        self.account, self.cookie, self.request = account, cookie, request

    def call(self, method, path, body=None, headers=None):
        sent = {'Cookie': self.cookie} if self.cookie else {}
        sent['Origin'] = f'http://127.0.0.1:{PRODUCT_PORT}'
        if body is not None and not isinstance(body, (bytes, str)):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode()
        if body is not None:
            sent['Content-Type'] = 'application/json'
        sent.update(headers or {})
        connection = http.client.HTTPConnection('127.0.0.1', PRODUCT_PORT, timeout=10)
        try:
            connection.request(method, path, body=body, headers=sent)
            response = connection.getresponse()
            raw = response.read()
        finally:
            connection.close()
        record({'account': self.account, 'method': method, 'path': path, 'status': response.status,
                'body': raw.decode('utf-8', 'replace'),
                'request_body': body.decode('utf-8', 'replace') if body is not None else None,
                'qa_request': {key: self.request[key] for key in ('method', 'path', 'query')} | {
                    'body': decode(self.request['body']).decode('utf-8', 'replace')}})
        return SimpleNamespace(status=response.status, headers=response.headers, body=raw,
                               text=raw.decode('utf-8', 'replace'), json=lambda: json.loads(raw or b'null'))


class Worker:
    """One child running the mapping. It sends {"call"} lines, gets {"response"} lines, ends with {"result"} or {"error"}."""

    def __init__(self):
        command = json.loads(os.environ['QA_WORKER']) if os.environ.get('QA_WORKER') else [
            sys.executable, '-I', '-B', __file__, 'worker']
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        env={'PATH': os.defpath, 'QA_MAPPING': str(MAPPING)})
        if self.receive() != {'ready': True}:
            raise ConnectionError('The mapping worker did not start; see its error above.')

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + '\n').encode())
        self.process.stdin.flush()

    def receive(self):
        line = self.process.stdout.readline()
        if not line:
            raise ConnectionError('mapping worker exited')
        return json.loads(line)

    def run(self, request, product):
        self.send({'request': request})
        while 'call' in (message := self.receive()):
            call = message['call']
            response = product.call(call['method'], call['path'], None if call['body'] is None else decode(call['body']), call['headers'])
            self.send({'response': {'status': response.status, 'headers': response.headers.items(), 'body': encode(response.body)}})
        if 'error' in message:
            raise RuntimeError(message['error'])
        return message['result']['status'], decode(message['result']['body']), message['result']['headers']


def refill():
    try:
        WORKERS.put(Worker())
    except (ConnectionError, OSError, ValueError) as error:
        print(f'Could not start a mapping worker: {error!r}', file=sys.stderr, flush=True)


class QA(BaseHTTPRequestHandler):
    def handle_qa(self):
        url = urlsplit(self.path)
        raw = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        cookie = self.headers.get('Cookie', '')
        request = {'method': self.command, 'path': url.path[len('/qa'):] or '/', 'query': url.query, 'body': encode(raw), 'cookie': cookie}
        # Each request gets a fresh worker, so no mapping state survives across requests or accounts.
        worker = WORKERS.get()
        threading.Thread(target=refill, daemon=True).start()
        try:
            status, payload, headers = worker.run(request, Product(self.headers.get('X-QA-Account', ''), cookie, request))
        except Exception as error:  # noqa: BLE001 — adapter faults become explicit failed answers at the request boundary
            status, payload, headers = 502, json.dumps({'error': f'QA adapter failed: {error!r}'}).encode(), []
        finally:
            worker.process.kill()
            worker.process.wait()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = handle_qa

    def log_message(self, *args):
        pass


def relay(source, target):
    try:
        while data := source.recv(65536):
            target.sendall(data)
    except OSError:
        pass
    finally:
        try:
            target.shutdown(socket.SHUT_WR)
        except OSError:
            pass


class Connection(socketserver.BaseRequestHandler):
    def handle(self):
        head, deadline = b'', time.monotonic() + 10
        while b'\r\n' not in head and len(head) < 8192 and time.monotonic() < deadline:
            peeked = self.request.recv(8192, socket.MSG_PEEK)
            if not peeked:
                return
            if peeked == head:
                time.sleep(.01)
            head = peeked
        parts = head.split(b' ', 2)
        target = parts[1] if len(parts) > 2 else b''
        if target == b'/qa' or target.startswith((b'/qa/', b'/qa?')):
            QA(self.request, self.client_address, self.server)
            return
        try:
            upstream = socket.create_connection(('127.0.0.1', PRODUCT_PORT), timeout=10)
        except OSError:
            return
        upstream.settimeout(None)
        with upstream:
            back = threading.Thread(target=relay, args=(upstream, self.request), daemon=True)
            back.start()
            relay(self.request, upstream)
            back.join()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def worker():
    """Child side: run the mapping; every product call goes to the parent over stdout and comes back on stdin."""
    def send(message):
        sys.stdout.write(json.dumps(message) + '\n')
        sys.stdout.flush()

    def receive():
        return json.loads(sys.stdin.readline())

    def call(method, path, body=None, headers=None):
        if body is not None and not isinstance(body, (bytes, str)):
            body = json.dumps(body)
        send({'call': {'method': method, 'path': path, 'body': None if body is None else encode(body.encode() if isinstance(body, str) else body),
                       'headers': headers or {}}})
        answer = receive()['response']
        message, raw = Message(), decode(answer['body'])
        for name, value in answer['headers']:
            message[name] = value
        return SimpleNamespace(status=answer['status'], headers=message, body=raw, text=raw.decode('utf-8', 'replace'),
                               json=lambda: json.loads(raw or b'null'))

    handle = load_mapping()
    send({'ready': True})
    for line in sys.stdin:
        request = json.loads(line)['request']
        raw = decode(request['body'])
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = None
        try:
            status, body, *rest = handle(SimpleNamespace(**{**request, 'body': raw, 'json': parsed}), SimpleNamespace(call=call))
            payload = body if isinstance(body, bytes) else body.encode() if isinstance(body, str) else json.dumps(body).encode()
            send({'result': {'status': status, 'body': encode(payload), 'headers': [list(pair) for pair in (rest[0] if rest else [])]}})
        except Exception as error:  # noqa: BLE001 — worker faults cross the IPC boundary as explicit errors
            send({'error': repr(error)})


if __name__ == '__main__':
    if sys.argv[1:] == ['worker']:
        worker()
    else:
        for _ in range(4):  # fresh workers kept ready; each serves one /qa request
            WORKERS.put(Worker())
        Server((os.environ.get('HOST', '127.0.0.1'), int(os.environ['PORT'])), Connection).serve_forever()
