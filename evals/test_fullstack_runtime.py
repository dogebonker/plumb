"""Calibrate the neutral full-stack case and its process cleanup boundary."""
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from fullstack_runtime import (
    copy_dependencies,
    free_port,
    grade_fullstack,
    server_sandbox,
    start_proxy,
    stop_server,
)

CASE = Path(__file__).resolve().parent / 'cases' / 'support-fullstack'
GLOAM = CASE.parent / 'gloam-chat'
# A mapping that hides what the product leaks: the raw-log scan must still see it.
STRIPPING_MAPPING = '''def strip(value):
    if isinstance(value, dict):
        return {key: strip(item) for key, item in value.items() if key != 'tapped_by'}
    return [strip(item) for item in value] if isinstance(value, list) else value


def handle(request, product):
    response = product.call(request.method, request.path + ('?' + request.query if request.query else ''), request.body or None)
    try:
        body = json.dumps(strip(response.json()))
    except ValueError:
        body = response.body
    return response.status, body, [('Set-Cookie', cookie) for cookie in response.headers.get_all('Set-Cookie') or []]
'''
# A mapping that answers searches from a health check alone, with nothing found.
HEALTH_ONLY_MAPPING = '''def handle(request, product):
    if request.path.endswith('/search'):
        product.call('GET', '/health')
        return 200, {'posts': []}
    response = product.call(request.method, request.path + ('?' + request.query if request.query else ''), request.body or None)
    return response.status, response.body, [('Set-Cookie', cookie) for cookie in response.headers.get_all('Set-Cookie') or []]
'''
# A mapping that refuses on the product's behalf: the refusal must come from the product.
SELF_REFUSING_MAPPING = '''def handle(request, product):
    if (request.json or {}).get('to') == 'bryn@saltroad.test':
        return 403, {'error': 'Players whisper only to the Keeper.'}
    response = product.call(request.method, request.path + ('?' + request.query if request.query else ''), request.body or None)
    return response.status, response.body, [('Set-Cookie', cookie) for cookie in response.headers.get_all('Set-Cookie') or []]
'''
# Unrelated reads cannot supply evidence that a whisper write was refused.
UNRELATED_READ_REFUSING_MAPPING = SELF_REFUSING_MAPPING.replace(
    "        return 403", "        product.call('GET', '/api/me')\n        return 403")
UNRELATED_FAILED_READ_REFUSING_MAPPING = SELF_REFUSING_MAPPING.replace(
    "        return 403", "        product.call('GET', '/api/scenes/not-built')\n        return 404")
# A product that lacks a latent feature: the adapter answers the contract's "not built" for its routes.
NOT_BUILT_MAPPING = '''def handle(request, product):
    if LACKS:
        return 404, {'error': 'not built'}
    response = product.call(request.method, request.path + ('?' + request.query if request.query else ''), request.body or None)
    return response.status, response.body, [('Set-Cookie', cookie) for cookie in response.headers.get_all('Set-Cookie') or []]
'''



class FullstackTests(unittest.TestCase):
    def test_stop_only_owned_group(self):
        process = subprocess.Popen(['/bin/sh', '-c', 'sleep 30 & wait'], start_new_session=True)
        sibling = subprocess.Popen(['sleep', '30'], start_new_session=True)
        try:
            stop_server(process)
            self.assertIsNotNone(process.returncode)
            self.assertIsNone(sibling.poll(), 'Unrelated server group must remain alive')
            stop_server(process)
        finally:
            stop_server(sibling)

    def test_dependency_links_stay_inside_copied_product(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work, product = root / 'work', root / 'product'
            package = work / 'frontend' / 'node_modules' / 'package'
            package.mkdir(parents=True)
            (package / 'index.js').write_text('module.exports = 1')
            (package.parent / 'alias').symlink_to(package)
            product.mkdir()
            copy_dependencies(work, product)
            alias = product / 'frontend' / 'node_modules' / 'alias'
            self.assertEqual(alias.resolve(), (product / 'frontend' / 'node_modules' / 'package').resolve())
            self.assertEqual((alias / 'index.js').read_text(), 'module.exports = 1')
            venv = work / '.venv' / 'bin'
            venv.mkdir(parents=True)
            (venv / 'python').symlink_to(Path(sys.executable).resolve())
            copied = root / 'with-python'
            copy_dependencies(work, copied)
            self.assertTrue((copied / '.venv' / 'bin' / 'python').is_symlink())
            self.assertEqual((copied / '.venv' / 'bin' / 'python').resolve(), Path(sys.executable).resolve())
            outside = root / 'secret'
            outside.write_text('host secret')
            (package.parent / 'escape').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'escapes project'):
                copy_dependencies(work, root / 'rejected')
            self.assertFalse((root / 'rejected' / 'frontend' / 'node_modules').exists())

    def test_venv_console_entrypoint_survives_source_removal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work, product = root / 'work', root / 'product'
            venv = work / '.venv'
            subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(venv)], check=True, timeout=20)
            launcher = venv / 'bin' / 'hello'
            launcher.write_text(f'#!{venv}/bin/python\nprint("relocated entrypoint")\n')
            launcher.chmod(0o755)
            copy_dependencies(work, product)
            shutil.rmtree(work)
            check = subprocess.run([str(product / '.venv' / 'bin' / 'hello')], capture_output=True,
                                   text=True, timeout=10, check=False)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertEqual(check.stdout.strip(), 'relocated entrypoint')
            activated = subprocess.run(['/bin/sh', '-c', '. "$1/.venv/bin/activate"; python -c "print(123)"', 'sh', str(product)],
                                       capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual(activated.returncode, 0, activated.stdout + activated.stderr)
            self.assertEqual(activated.stdout.strip(), '123')

    @unittest.skipUnless(platform.system() == 'Darwin', 'Apple system Python regression')
    def test_system_python_venv_ssl_survives_source_removal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            work, product = root / 'work', root / 'product'
            venv = work / '.venv'
            subprocess.run(['/usr/bin/python3', '-m', 'venv', '--without-pip', str(venv)], check=True, timeout=20)
            launcher = venv / 'bin' / 'tls-check'
            launcher.write_text(f'#!{venv}/bin/python\nimport ssl; print(ssl.OPENSSL_VERSION)\n')
            launcher.chmod(0o755)
            copy_dependencies(work, product)
            shutil.rmtree(work)
            hidden, artifact = root / 'case', root / 'artifacts'
            hidden.mkdir()
            artifact.mkdir()
            prefix, env = server_sandbox(product, root, hidden, artifact, {
                'PATH': os.defpath, 'HOST': '127.0.0.1', 'PORT': '8999', 'DATABASE_PATH': str(product / 'db')})
            check = subprocess.run([*prefix, str(product / '.venv' / 'bin' / 'tls-check')], cwd=product,
                                   env=env, capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertRegex(check.stdout, 'LibreSSL|OpenSSL')

    def test_submitted_python_target_is_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work, product = root / 'work', root / 'product'
            interpreter = work / '.venv' / 'bin' / 'python'
            interpreter.parent.mkdir(parents=True)
            marker = root / 'executed'
            outside = root / 'untrusted-python'
            outside.write_text(f'#!/bin/sh\ntouch "{marker}"\n')
            outside.chmod(0o755)
            interpreter.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'escapes project'):
                copy_dependencies(work, product)
            self.assertFalse(marker.exists())

    @unittest.skipUnless(platform.system() == 'Darwin' and shutil.which('sandbox-exec'), 'Native macOS sandbox required')
    def test_server_cannot_access_hidden_grader_or_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            temporary = Path(folder).resolve()
            product, hidden, artifact = temporary / 'product', temporary / 'case', temporary / 'artifacts'
            for directory in (product, hidden / 'grading', artifact, temporary / 'runtime'):
                directory.mkdir(parents=True)
            secret = hidden / 'grading' / 'acceptance.cjs'
            report = artifact / 'grade.json'
            grader_data = temporary / 'runtime' / 'snapshot.json'
            grader_policy = temporary / 'grading.sb'
            (temporary / 'qa').mkdir()
            raw_log = temporary / 'qa' / 'raw.jsonl'  # only the grader's proxy writes the raw product log
            targets = [secret, report, grader_data, grader_policy, temporary / 'private-host.txt', raw_log]
            for path in targets:
                path.write_text('hidden canary')
            (product / 'public.txt').write_text('public app')
            env = {'PATH': str(Path(sys.executable).resolve().parent) + os.pathsep + os.defpath,
                   'HOST': '127.0.0.1', 'PORT': '8999', 'DATABASE_PATH': str(product / 'db'),
                   'BROWSER_ARTIFACTS': str(artifact), 'BENCHMARK_SNAPSHOT': str(grader_data)}
            prefix, server_env = server_sandbox(product, temporary, hidden, artifact, env)
            self.assertNotIn('BROWSER_ARTIFACTS', server_env)
            self.assertNotIn('BENCHMARK_SNAPSHOT', server_env)
            code = """
import pathlib, sys
assert pathlib.Path('public.txt').read_text() == 'public app'
pathlib.Path('own.txt').write_text('allowed')
for target in sys.argv[1:]:
    path = pathlib.Path(target)
    for action in ('read', 'write'):
        try:
            path.read_text() if action == 'read' else path.write_text('tampered')
        except PermissionError:
            continue
        raise AssertionError(action + ' was allowed: ' + target)
"""
            check = subprocess.run([*prefix, sys.executable, '-c', code, *map(str, targets)], cwd=product,
                                   env=server_env, capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            for target in targets:
                self.assertEqual(target.read_text(), 'hidden canary')

    @unittest.skipUnless(os.environ.get('PLAYWRIGHT_MODULE'), 'Installed Playwright required')
    def test_baseline_oracle_and_mutants(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            work = root / 'work'
            shutil.copytree(CASE / 'fixture', work)
            smoke = subprocess.run(['/bin/sh', 'benchmark.sh', 'setup'], cwd=work, capture_output=True, text=True, check=False)
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            baseline, output = grade_fullstack(CASE, work, root / 'baseline')
            self.assertFalse(baseline['accepted'], output)
            self.assertEqual(baseline['tests'], 19, output)
            for file in (CASE / 'oracle').iterdir():
                if file.is_file():
                    shutil.copy2(file, work / file.name)
            oracle, output = grade_fullstack(CASE, work, root / 'oracle')
            self.assertTrue(oracle['accepted'], json.dumps(oracle) + '\n' + output)
            self.assertEqual(len(oracle['requirements']), 10)
            self.assertEqual(len(oracle['outcomes']), 5)
            self.assertTrue(all(outcome['accepted'] for outcome in oracle['outcomes']))
            self.assertEqual(set(oracle['screenshots']), {'desktop', 'mobile', 'details'})
            self.assertTrue(all(Path(path).is_file() for path in oracle['screenshots'].values()))
            app = work / 'server.py'
            source = app.read_text()
            mutants = {
                'logout-still-valid': source.replace('SESSIONS.pop(token, None)', 'pass'),
                'tenant-leak': source.replace("return ticket['tenant'] == user['tenant'] and", 'return True or'),
                'reset-on-start': source.replace("with connection() as con:\n            con.execute('SELECT data FROM tickets LIMIT 1').fetchall()", "reset()"),
            }
            for name, faulty in mutants.items():
                self.assertNotEqual(source, faulty)
                app.write_text(faulty)
                result, output = grade_fullstack(CASE, work, root / name)
                self.assertFalse(result['accepted'], name + output)
                failures = {c['name'] for c in result.get('checks', []) if not c['passed']}
                expected = {'tenant-leak': 'tenant_boundaries', 'reset-on-start': 'restart_retains_committed_data', 'logout-still-valid': 'login_logout'}
                self.assertIn(expected[name], failures)
            app.write_text(source)
            ui = work / 'index.html'
            html = ui.read_text()
            variant = html.replace("document.createElement('button');b.className='ticket'", "document.createElement('a');b.href='#';b.className='ticket'")
            variant = variant.replace("tickets.length+' tickets'", "tickets.length+' ticket'+(tickets.length===1?'':'s')")
            variant = variant.replace('close();await refresh()', 'await refresh()')
            variant = variant.replace('open(ticket,opener)', 'await new Promise(resolve=>setTimeout(resolve,150));open(ticket,opener)')
            variant += """<script>
for (const select of document.querySelectorAll('#priority, #editPriority')) {
    const options = [...select.options].map(option => ({value: option.value, text: option.text}));
    const control = document.createElement('button');
    control.id = select.id;
    control.type = 'button';
    control.setAttribute('role', 'combobox');
    control.setAttribute('aria-label', select.getAttribute('aria-label'));
    control.setAttribute('aria-haspopup', 'listbox');
    control.setAttribute('aria-expanded', 'false');
    control.oninput = select.oninput;
    let value = select.value;
    Object.defineProperty(control, 'value', {
        get() { return value; },
        set(next) { value = next; control.textContent = options.find(option => option.value === value).text; }
    });
    control.value = value;
    control.onclick = () => {
        const list = document.createElement('div');
        list.setAttribute('role', 'listbox');
        list.style = 'position:fixed;top:20px;left:20px;background:white;padding:12px;z-index:10';
        control.setAttribute('aria-expanded', 'true');
        for (const option of options) {
            const button = document.createElement('button');
            button.type = 'button';
            button.setAttribute('role', 'option');
            button.textContent = option.text;
            button.onclick = () => {
                control.value = option.value;
                control.setAttribute('aria-expanded', 'false');
                list.remove();
                control.dispatchEvent(new Event('input', {bubbles: true}));
                control.focus();
            };
            list.append(button);
        }
        (control.closest('dialog') || document.body).append(list);
    };
    select.replaceWith(control);
}
</script>"""
            self.assertNotEqual(variant, html)
            ui.write_text(variant)
            semantic, output = grade_fullstack(CASE, work, root / 'links-singular')
            self.assertTrue(semantic['accepted'], json.dumps(semantic) + '\n' + output)

    @unittest.skipUnless(platform.system() == 'Darwin' and shutil.which('sandbox-exec'), 'Native macOS sandbox required')
    def test_mapping_without_its_denylist_still_cannot_touch_raw_log_or_product(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            case, qa, site = root / 'case', root / 'qa', root / 'site'
            shutil.copytree(GLOAM / 'grading', case / 'grading')
            proxy = case / 'grading' / 'qa_proxy.py'
            source = proxy.read_text()
            unguarded = source.replace('        if bad:\n', '        if False:\n').replace("{'__builtins__': BUILTINS, **MODULES}", '{**MODULES}')
            self.assertEqual(source.count('        if bad:\n') + source.count("{'__builtins__': BUILTINS, **MODULES}"), 2)
            proxy.write_text(unguarded)  # simulate a mapping that escaped every in-process restriction
            qa.mkdir()
            site.mkdir()
            (site / 'index.html').write_text('product page')
            log, product_port, port = qa / 'raw.jsonl', free_port(), free_port()
            (qa / 'mapping.py').write_text(f'''import socket
def handle(request, product):
    outcome = []
    for mode in ('a', 'w'):
        try:
            open({str(log)!r}, mode).write('{{"account": "forged"}}\\n')
            outcome.append(mode + ': written')
        except OSError as error:
            outcome.append(mode + ': ' + type(error).__name__)
    try:
        socket.create_connection(('127.0.0.1', {product_port}), timeout=2)
        outcome.append('product reached directly')
    except OSError as error:
        outcome.append('direct: ' + type(error).__name__)
    return 200, {{'outcome': outcome, 'status': product.call('GET', '/').status}}
''')
            product = subprocess.Popen([sys.executable, '-m', 'http.server', str(product_port), '--bind', '127.0.0.1'], cwd=site,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            server = start_proxy(case, qa, port, product_port, root / 'proxy.log')
            try:
                for _ in range(100):
                    try:
                        request = urllib.request.Request(f'http://127.0.0.1:{port}/qa/probe', headers={'X-QA-Account': 'tester'})
                        with urllib.request.urlopen(request, timeout=5) as response:
                            answer = json.loads(response.read())
                        break
                    except OSError:
                        time.sleep(.1)
                else:
                    self.fail((root / 'proxy.log').read_text())
            finally:
                stop_server(server)
                stop_server(product)
            self.assertEqual(answer, {'outcome': ['a: PermissionError', 'w: PermissionError', 'direct: PermissionError'], 'status': 200})
            entries = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([(entry['account'], entry['path'], entry['status']) for entry in entries], [('tester', '/', 200)])

    @unittest.skipUnless(os.environ.get('PLAYWRIGHT_MODULE'), 'Installed Playwright required')
    def test_gloam_browser_and_keyboard_can_select_table_before_scene(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / 'work'
            shutil.copytree(GLOAM / 'fixture', work)
            shutil.copytree(GLOAM / 'oracle', work, dirs_exist_ok=True)
            html = work / 'index.html'
            html.write_text(html.read_text().replace(
                '<div id="app"', '<button id="tablePicker" data-testid="table-link" type="button" hidden>The Salt Road</button>\n<div id="app"'
            ).replace('async function show(){', '''async function show(){
  $('login').hidden=$('app').hidden=true;
  $('tablePicker').hidden=false;
  $('tablePicker').onclick=async()=>{$('tablePicker').hidden=true;await showScenes()}}
async function showScenes(){'''))
            ui = work / 'qa' / 'ui.json'
            ui.write_text(json.dumps(json.loads(ui.read_text()) | {'table-link': '[data-testid=table-link]'}))
            result, output = grade_fullstack(GLOAM, work, root / 'grade')
            self.assertTrue(result['accepted'], json.dumps(result) + '\n' + output)

    @unittest.skipUnless(os.environ.get('PLAYWRIGHT_MODULE'), 'Installed Playwright required')
    def test_gloam_browser_uses_product_host_and_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / 'work'
            shutil.copytree(GLOAM / 'fixture', work)
            shutil.copytree(GLOAM / 'oracle', work, dirs_exist_ok=True)
            server = work / 'server.py'
            server.write_text(server.read_text().replace(
                'class Handler(BaseHTTPRequestHandler):\n',
                '''class Handler(BaseHTTPRequestHandler):
    def parse_request(self):
        if not super().parse_request():
            return False
        host = f"127.0.0.1:{os.environ['PORT']}"
        if self.headers.get('Host') != host:
            self.send_error(403, 'Unexpected Host')
            return False
        origin = self.headers.get('Origin')
        if self.command not in ('GET', 'HEAD', 'OPTIONS') and origin != 'http://' + host:
            self.send_error(403, 'Unexpected Origin')
            return False
        return True

'''))
            result, output = grade_fullstack(GLOAM, work, root / 'grade')
            self.assertTrue(result['accepted'], json.dumps(result) + '\n' + output)
            raw = [json.loads(line) for line in (root / 'grade' / 'qa-raw.jsonl').read_text().splitlines()]
            self.assertTrue(any(entry.get('account') == 'anonymous' for entry in raw))

    @unittest.skipUnless(os.environ.get('PLAYWRIGHT_MODULE'), 'Installed Playwright required')
    def test_gloam_grades_through_trusted_proxy_and_raw_log(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            work = root / 'work'
            shutil.copytree(GLOAM / 'fixture', work)
            shutil.copytree(GLOAM / 'oracle', work, dirs_exist_ok=True)
            (work / 'qa' / 'qa_proxy.py').write_text('raise SystemExit("an agent copy must be overwritten")')
            oracle, output = grade_fullstack(GLOAM, work, root / 'oracle')
            self.assertTrue(oracle['accepted'], json.dumps(oracle) + '\n' + output)
            self.assertEqual(len(oracle['checks']), 23)
            server, html = (work / 'server.py').read_text(), (work / 'index.html').read_text()
            tapper = server.replace("con.execute('UPDATE scenes SET state=? WHERE id=?', ('paused', scene['id']))",
                                    "con.execute('UPDATE scenes SET state=? WHERE id=?', ('paused', scene['id'])); TAPPED[scene['id']] = user['email']"
                                    ).replace("    data = {'id': scene['id'], 'title': scene['title'], 'state': scene['state']}\n",
                                              "    data = {'id': scene['id'], 'title': scene['title'], 'state': scene['state'], 'tapped_by': TAPPED.get(scene['id'])}\n"
                                              ).replace('SESSIONS = {}\n', 'SESSIONS = {}\nTAPPED = {}\n')
            mutants = {
                'tapper-email': ({'server.py': tapper}, 'xcard_anonymous_pause_veil'),
                'adapter-strips-tapper-email': ({'server.py': tapper, 'qa/mapping.py': STRIPPING_MAPPING}, 'xcard_anonymous_pause_veil'),
                'messages-dm': ({'index.html': html.replace('<h2>Scenes</h2>', '<h2>Messages</h2>').replace(
                    "'Whisper to '+(r.role==='keeper'?'the Keeper':r.character)", "'DM '+(r.role==='keeper'?'the Keeper':r.character)")},
                    'owner_vocabulary_on_screen'),
                'adapter-refuses-for-product': ({'server.py': server.replace(
                    "user['role'] == 'keeper' or target['role'] == 'keeper')", 'True)'), 'qa/mapping.py': SELF_REFUSING_MAPPING},
                    'whispers_keeper_and_player_only'),
                'adapter-unrelated-successful-read': ({'server.py': server.replace(
                    "user['role'] == 'keeper' or target['role'] == 'keeper')", 'True)'),
                    'qa/mapping.py': UNRELATED_READ_REFUSING_MAPPING}, 'whispers_keeper_and_player_only'),
                'adapter-unrelated-failed-read': ({'server.py': server.replace(
                    "user['role'] == 'keeper' or target['role'] == 'keeper')", 'True)'),
                    'qa/mapping.py': UNRELATED_FAILED_READ_REFUSING_MAPPING}, 'whispers_keeper_and_player_only'),
                'canon-editable': ({'server.py': server.replace(
                    "    if post['canon']:\n        raise Refused(409, 'Someone has posted after this. It is canon now.')\n", '')}, 'canon_after_reply'),
                # A missing feature fails its own checks; baseline and unrelated latent checks skip the parts that need it.
                'whispers-not-built': ({'qa/mapping.py': NOT_BUILT_MAPPING.replace('LACKS', "request.path.endswith('/whispers')")},
                                       'whispers_keeper_and_player_only'),
                'edits-not-built': ({'qa/mapping.py': NOT_BUILT_MAPPING.replace('LACKS', "request.method == 'PATCH'")},
                                    {'stale_version_refused_newer_kept', 'canon_after_reply'}),
                # Sessions kept in the database: signing in fails with a 5xx on unwritable storage, which is a safe refusal.
                'durable-sessions': ({'server.py': server.replace(
                    "                token = secrets.token_urlsafe(32)\n",
                    "                con = connect()\n                try:\n                    with con:\n"
                    "                        con.execute('UPDATE people SET role=role WHERE email=?', (found['email'],))\n"
                    "                finally:\n                    con.close()\n                token = secrets.token_urlsafe(32)\n")}, set()),
            }
            originals = {name: (work / name).read_text() for name in ('server.py', 'index.html', 'qa/mapping.py')}
            for name, (files, target) in mutants.items():
                for file, text in files.items():
                    self.assertNotEqual(originals[file], text, name)
                    (work / file).write_text(text)
                result, output = grade_fullstack(GLOAM, work, root / name)
                failures = {c['name'] for c in result.get('checks', []) if not c['passed']}
                self.assertEqual(failures, {target} if isinstance(target, str) else target, name + output)
                if name.endswith('-not-built'):
                    closed = next(c for c in result['checks'] if c['name'] == 'drawn_to_a_close_read_only')
                    self.assertTrue(closed['passed'] and closed.get('skipped'), name)
                if name.startswith('adapter-unrelated-'):
                    raw = [json.loads(line) for line in (root / name / 'qa-raw.jsonl').read_text().splitlines()]
                    reads = [entry for entry in raw if entry.get('qa_request', {}).get('method') == 'POST'
                             and 'Thistlewick' in entry['qa_request']['body']]
                    self.assertEqual(len(reads), 1)
                    self.assertEqual((reads[0]['method'], reads[0]['status']),
                                     ('GET', 200 if name.endswith('successful-read') else 404))
                    self.assertTrue(reads[0]['qa_request']['path'].endswith('/whispers'))
                    self.assertIsNone(reads[0]['request_body'])
                    self.assertIn('lacks a product refusal', next(c['error'] for c in result['checks'] if c['name'] == target))
                for file, text in originals.items():
                    (work / file).write_text(text)
            (work / 'qa/mapping.py').write_text(HEALTH_ONLY_MAPPING)
            result, output = grade_fullstack(GLOAM, work, root / 'health-only')
            failures = {c['name']: c.get('error', '') for c in result.get('checks', []) if not c['passed']}
            leak_checks = {'whispers_keeper_and_player_only', 'xcard_anonymous_pause_veil', 'release_from_table', 'drawn_to_a_close_read_only'}
            # B02 and B03 fail first on the search answer itself: 200 for anonymous, nothing found at the own table.
            self.assertEqual(set(failures), leak_checks | {'anonymous_401', 'cross_table_isolation'}, output)
            for name in leak_checks:
                self.assertIn('without a logged product call (health checks do not count)', failures[name])
            (work / 'qa/mapping.py').write_text(originals['qa/mapping.py'])
            raw = [json.loads(line) for line in (root / 'adapter-strips-tapper-email' / 'qa-raw.jsonl').read_text().splitlines()]
            self.assertTrue(any('tapped_by' in entry['body'] and 'bryn@saltroad.test' in entry['body'] for entry in raw),
                            'The product leak must reach the raw log even though the adapter strips it')


if __name__ == '__main__':
    unittest.main()
