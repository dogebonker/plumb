"""Own the disposable full-stack server process and reuse the native grading policy."""
import functools
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


@functools.lru_cache(maxsize=1)
def installed_python_runtimes():
    """Discover Python identities only by probing the observer or fixed public install locations."""
    candidates = {Path(sys.executable)}
    for directory in ('/usr/bin', '/usr/local/bin', '/opt/homebrew/bin'):
        root = Path(directory)
        if root.is_dir():
            candidates.update(path for path in root.iterdir() if re.fullmatch(r'python3(?:\.\d+)?', path.name))
    targets = {Path(sys.executable).resolve()}
    readable = {Path(sys.base_prefix).resolve()}
    code = ('import json,sys,sysconfig;print(json.dumps({"executable":sys.executable,'
            '"base_executable":getattr(sys,"_base_executable",sys.executable),'
            '"base_prefix":sys.base_prefix,"stdlib":sysconfig.get_path("stdlib")}))')
    for executable in sorted(candidates):
        if not executable.is_file() or not os.access(executable, os.X_OK):
            continue
        try:
            probe = subprocess.run([str(executable), '-I', '-S', '-c', code],
                                   env={'PATH': os.defpath}, capture_output=True, text=True, timeout=5, check=False)
            if probe.returncode:
                continue
            identity = json.loads(probe.stdout)
            for key in ('executable', 'base_executable'):
                path = Path(identity[key])
                if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
                    raise ValueError('Invalid installed Python identity')
                targets.add(path.resolve(strict=True))
                readable.add(path.absolute().parent.parent)
            targets.add(executable.resolve(strict=True))
            for key in ('base_prefix', 'stdlib'):
                path = Path(identity[key])
                if not path.is_absolute() or not path.is_dir():
                    raise ValueError('Invalid installed Python runtime path')
                readable.add(path.resolve(strict=True))
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
            continue
    home = Path.home().resolve()
    broad_roots = {home, *home.parents}
    return frozenset(targets), frozenset(path.resolve() for path in readable if path.resolve() not in broad_roots)


def copy_dependencies(work, product):
    """Retain installed local dependencies while remapping links into the copied project."""
    original_work = Path(work).absolute()
    work, product = original_work.resolve(), Path(product).resolve()
    python_targets, _ = installed_python_runtimes()
    roots = []
    for directory, names, _ in os.walk(work, followlinks=False):
        for name in list(names):
            if name in {'node_modules', '.venv'}:
                roots.append(Path(directory) / name)
                names.remove(name)
            elif name in {'.git', '.software-factory', '.factory', '.claude', '.tmp', '__pycache__'}:
                names.remove(name)
    for source in roots:
        if not source.resolve().is_relative_to(work):
            raise ValueError(f'Dependency root escapes project: {source.relative_to(work)}')
        entries = [source, *source.rglob('*')]
        links = []
        for entry in entries:
            if not entry.is_symlink():
                continue
            try:
                resolved = entry.resolve(strict=True)
            except (OSError, RuntimeError) as error:
                raise ValueError(f'Invalid dependency symlink: {entry.relative_to(work)}') from error
            relative = entry.relative_to(work)
            runtime_python = (len(relative.parts) >= 3 and relative.parts[-3:-1] == ('.venv', 'bin')
                              and re.fullmatch(r'python(?:3(?:\.\d+)?)?', entry.name)
                              and resolved in python_targets)
            if not resolved.is_relative_to(work) and not runtime_python:
                raise ValueError(f'Dependency symlink escapes project: {relative}')
            links.append((relative, resolved, runtime_python))
        destination = product / source.relative_to(work)
        shutil.copytree(source, destination, symlinks=True)
        for relative, resolved, runtime_python in links:
            target = product / relative
            if not target.is_symlink():
                continue
            target.unlink()
            if runtime_python:
                target.symlink_to(resolved)
            else:
                mapped = product / resolved.relative_to(work)
                target.symlink_to(os.path.relpath(mapped, target.parent), target_is_directory=resolved.is_dir())
        if source.name == '.venv':
            old_paths = {str(source), str(original_work / source.relative_to(work))}
            for launcher in (destination / 'bin').iterdir():
                if not launcher.is_file():
                    continue
                raw = launcher.read_bytes()
                if not raw.startswith(b'#!') and launcher.name != 'activate':
                    continue
                lines = raw.splitlines(keepends=True)
                head = raw if launcher.name == 'activate' else b''.join(lines[:3])
                relocated = head
                for old_path in old_paths:
                    relocated = relocated.replace(old_path.encode(), str(destination).encode())
                if relocated != head:
                    launcher.write_bytes(relocated + (b'' if launcher.name == 'activate' else b''.join(lines[3:])))


def server_sandbox(product, temporary, case, artifact, public_env):
    """Give submitted code its own policy, with no access to hidden grader inputs or outputs."""
    from browser_runtime import sandbox_policy
    sandbox, node = shutil.which('sandbox-exec'), shutil.which('node')
    if not sandbox or not node:
        raise ValueError('Full-stack servers require native sandbox-exec and node')
    data = temporary / 'server-runtime'
    data.mkdir()
    protected = [case.resolve(), temporary / 'runtime', artifact.resolve(), temporary / 'grading.sb']
    _, python_roots = installed_python_runtimes()
    policy = sandbox_policy(product, [data, *python_roots], [product, data], node, protected, strict_reads=True)
    policy += ('(allow network-outbound (remote ip "localhost:*"))\n'
               '(allow network-inbound (local ip "localhost:*"))\n'
               '(allow network-bind (local ip "localhost:*"))\n')
    readable = [product, data, *python_roots, Path(node).resolve().parent.parent, Path(sys.executable).resolve().parent.parent]
    ancestors = {parent for path in readable for parent in path.parents}
    policy += ''.join(f'(allow file-read-metadata (literal {json.dumps(str(path))}))\n' for path in sorted(ancestors))
    policy += ''.join(f'(deny file-write* (subpath {json.dumps(str(path))}))\n' for path in protected)
    profile = temporary / 'server.sb'
    profile.write_text(policy)
    env = {key: public_env[key] for key in ('PATH', 'HOST', 'PORT', 'DATABASE_PATH')}
    env.update({key: public_env[key] for key in ('PRODUCT_PORT',) if key in public_env})
    env.update(HOME=str(data), TMPDIR=str(data))
    return [sandbox, '-f', str(profile)], env


def start_proxy(case, qa, port, product_port, log):
    """Launch the trusted proxy. It owns the raw log and the only route to the product; the adapter's mapping runs
    in worker children whose sandbox reads just the grader's snapshot of it and has no network and no writable log."""
    from browser_runtime import sandbox_policy
    _, python_roots = installed_python_runtimes()
    proxy = case.resolve() / 'grading' / 'qa_proxy.py'
    scratch = qa.parent / 'qa-worker'
    scratch.mkdir()
    readable = [proxy, *python_roots]
    policy = sandbox_policy(qa / 'mapping.py', readable, [scratch], shutil.which('node'), [], strict_reads=True)
    ancestors = {parent for path in [qa / 'mapping.py', *readable, Path(sys.executable).resolve().parent.parent] for parent in path.parents}
    policy += ''.join(f'(allow file-read-metadata (literal {json.dumps(str(path))}))\n' for path in sorted(ancestors))
    profile = qa.parent / 'qa-worker.sb'
    profile.write_text(policy)
    worker = [shutil.which('sandbox-exec'), '-f', str(profile), sys.executable, '-I', '-B', str(proxy), 'worker']
    env = {'PATH': os.defpath, 'HOST': '127.0.0.1', 'PORT': str(port), 'PRODUCT_PORT': str(product_port),
           'QA_RAW_LOG': str(qa / 'raw.jsonl'), 'QA_MAPPING': str(qa / 'mapping.py'), 'QA_WORKER': json.dumps(worker)}
    with log.open('w') as output:
        return subprocess.Popen([sys.executable, '-I', '-B', str(proxy)], env=env, stdin=subprocess.DEVNULL,
                                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)


def stop_server(process):
    """Kill only the process group created by this grader, including foreground children."""
    if process is not None and not getattr(process, '_factory_stopped', False):
        process._factory_stopped = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:  # macOS refuses signals to a group whose exited leader is not yet reaped
            if process.poll() is None:
                raise
        process.wait(timeout=10)
        if thread := getattr(process, '_factory_log_thread', None):
            thread.join(timeout=10)


def request(base, route, method='GET', body=None, cookie=''):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + route, data=data, method=method,
                                 headers={'Content-Type': 'application/json', 'Cookie': cookie})
    try:
        response = urllib.request.urlopen(req, timeout=3)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        cookies = response.headers.get_all('Set-Cookie') or []
        return response.status, json.loads(raw or b'{}'), '; '.join(cookie.split(';')[0] for cookie in cookies)


def login(base, email):
    status, _, cookie = request(base, '/api/login', 'POST', {'email': email, 'password': 'benchmark-pass'})
    assert status == 200, f'Login failed with {status}'
    return cookie


def support_probe(base):
    """Operator session: snapshot committed tickets, attempt one ticket write, count probe writes."""
    cookie = login(base, 'operator@acme.test')
    def snapshot():
        status, data, _ = request(base, '/api/tickets', cookie=cookie)
        assert status == 200 and isinstance(data.get('tickets'), list)
        return sorted(data['tickets'], key=lambda t: t['id'])
    def write():
        status, data, _ = request(base, '/api/tickets', 'POST', {'title': 'Must not commit', 'description': 'Readonly database'}, cookie)
        return status, data
    def count():
        _, data, _ = request(base, '/api/tickets?q=Must%20not%20commit', cookie=cookie)
        return len(data['tickets'])
    return snapshot, write, count


GLOAM_POST_FIELDS = ('id', 'scene', 'body', 'in_character', 'speaker', 'to', 'version', 'created_at')


class LoginRefused(AssertionError):
    """The product refused to sign in with a server error, as one that stores sessions durably must on unwritable storage."""


def gloam_probe(base):
    """Keeper session through the adapter's /qa API: snapshot every scene's contract fields, attempt one named in-character post."""
    base += '/qa'
    status, data, cookie = request(base, '/api/login', 'POST', {'email': 'keeper@saltroad.test', 'password': 'benchmark-pass'})
    if status >= 500 and data.get('error'):
        raise LoginRefused(f'Login refused with {status}')
    assert 200 <= status < 300, f'Login failed with {status}'  # the adapter passes the product's own success codes
    status, me, _ = request(base, '/api/me', cookie=cookie)
    assert 200 <= status < 300
    table = me['user']['table']
    table = urllib.parse.quote(str(table['id'] if isinstance(table, dict) else table), safe='')
    def scenes():
        status, data, _ = request(base, f'/api/tables/{table}/scenes', cookie=cookie)
        assert 200 <= status < 300 and isinstance(data.get('scenes'), list)
        return data['scenes']
    def scene(identifier):
        status, data, _ = request(base, f'/api/scenes/{identifier}', cookie=cookie)
        assert 200 <= status < 300
        return data['scene']
    drowned = next(item['id'] for item in scenes() if item['title'] == 'The Drowned Mile')
    def snapshot():
        return [{'id': item['id'], 'title': item['title'], 'state': item['state'],
                 'posts': [{key: post.get(key) for key in GLOAM_POST_FIELDS} for post in scene(item['id'])['posts']]}
                for item in sorted(scenes(), key=lambda item: str(item['id']))]
    def write():
        status, data, _ = request(base, f'/api/scenes/{drowned}/posts', 'POST',
                                  {'body': 'Must not commit', 'in_character': True, 'character': 'The Ferryman'}, cookie)
        return status, data
    def count():
        return sum(post.get('body') == 'Must not commit' for post in scene(drowned)['posts'])
    return snapshot, write, count


# Each case supplies its durability probe and the requirement IDs of the three runtime checks.
DURABILITY = {
    'support-fullstack': (support_probe, {'restart': ['NFR-02'], 'storage': ['NFR-03'], 'malformed': ['NFR-02']}),
    'gloam-chat': (gloam_probe, {'restart': ['B05'], 'storage': ['L11'], 'malformed': ['L11']}),
}


def free_port():
    # A server in another run must never be touched; select a new loopback port.
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def start_server(prefix, product, env, log, timeout=15, health=None):
    process = subprocess.Popen([*prefix, '/bin/sh', 'benchmark.sh', 'start'], cwd=product, env=env,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    def capture():
        with process.stdout:
            while chunk := process.stdout.read1(65536):
                log.write(chunk.decode(errors='replace'))
                log.flush()
    process._factory_log_thread = threading.Thread(target=capture, daemon=True)
    process._factory_log_thread.start()
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise ValueError('Server exited before health check')
            try:
                with urllib.request.urlopen(health or f'http://{env["HOST"]}:{env["PORT"]}/health', timeout=3) as ready:
                    if ready.status == 200:
                        return process
            except (OSError, ValueError):
                pass
            time.sleep(.1)
        raise ValueError('Server did not become healthy within 15 seconds')
    except BaseException:
        stop_server(process)
        raise


def grade_fullstack(case, work, artifact):
    # Import lazily: benchmark dispatches here without a circular module initialization.
    from benchmark import copy_product, grading_sandbox
    artifact = Path(artifact).resolve()
    artifact.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((case / 'case.json').read_text())
    expected = metadata['test_count']
    checks, output, process, proxy = [], '', None, None
    result = {'accepted': False, 'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0, 'expected_tests': expected}
    with tempfile.TemporaryDirectory(prefix='factory-fullstack-') as folder:
        temporary = Path(folder).resolve()
        product = temporary / 'product'
        try:
            copy_product(work, product)
            copy_dependencies(work, product)
            prefix, env = grading_sandbox(product, temporary, case, artifact, True)
            port = free_port()
            database = product / '.benchmark-data' / 'database'
            database.parent.mkdir()
            base = f'http://127.0.0.1:{port}'
            env['PATH'] = str(Path(sys.executable).resolve().parent) + os.pathsep + env['PATH']
            env.update(HOST='127.0.0.1', PORT=str(port), DATABASE_PATH=str(database),
                       BENCHMARK_BASE=base)
            public, health, qa = env, None, temporary / 'qa'
            if metadata.get('adapter'):
                # Browsers use the native origin; the separate QA proxy preserves a mapping snapshot taken
                # before product code runs and logs raw answers.
                qa.mkdir()
                for name in ('mapping.py', 'ui.json'):
                    if (product / 'qa' / name).is_file():
                        shutil.copy2(product / 'qa' / name, qa / name)
                product_port = free_port()
                env.update(QA_RAW_LOG=str(qa / 'raw.jsonl'), QA_UI=str(qa / 'ui.json'),
                           BENCHMARK_PRODUCT_BASE=f'http://127.0.0.1:{product_port}')
                public = {**env, 'PORT': str(product_port), 'PRODUCT_PORT': str(product_port)}
                health = base + '/qa/health'
            server_prefix, server_env = server_sandbox(product, temporary, case, artifact, public)
            start = functools.partial(start_server, health=health)
            with (artifact / 'server.log').open('w') as log:
                reset = subprocess.Popen([*server_prefix, '/bin/sh', 'benchmark.sh', 'reset'], cwd=product,
                                         env=server_env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    stdout, stderr = reset.communicate(timeout=30)
                    output += stdout + stderr
                finally:
                    stop_server(reset)
                if reset.returncode:
                    raise ValueError('Explicit seed/reset command failed')
                if metadata.get('adapter'):
                    proxy = start_proxy(case, qa, port, product_port, artifact / 'proxy.log')
                process = start(server_prefix, product, server_env, log)
                grader = subprocess.Popen([*prefix, shutil.which('node'), str(case / 'grading' / 'acceptance.cjs')],
                                          cwd=product, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          text=True, start_new_session=True)
                try:
                    stdout, stderr = grader.communicate(timeout=100)
                except BaseException:
                    stop_server(grader)
                    raise
                output += stdout + stderr
                lines = [line[len('BENCHMARK_GRADE='):] for line in stdout.splitlines() if line.startswith('BENCHMARK_GRADE=')]
                if len(lines) != 1:
                    raise ValueError('Full-stack grader did not complete exactly once')
                counts = json.loads(lines[0])
                checks = counts['checks']
                if len(checks) != expected - 3:
                    raise ValueError('Incomplete full-stack browser/API checks')
                probe, ids = DURABILITY[metadata['id']]
                try:
                    saved = probe(base)[0]()
                except (OSError, ValueError, KeyError, TypeError, StopIteration, AssertionError):
                    saved = None
                stop_server(process)
                process = None
                try:
                    if saved is None:
                        raise ValueError('Cannot capture committed data before restart')
                    process = start(server_prefix, product, server_env, log)
                    assert probe(base)[0]() == saved, 'Committed data changed across restart'
                    checks.append({'name': 'restart_retains_committed_data', 'ids': ids['restart'], 'passed': True})
                except (OSError, ValueError, KeyError, TypeError, StopIteration, AssertionError) as error:
                    checks.append({'name': 'restart_retains_committed_data', 'ids': ids['restart'], 'passed': False, 'error': str(error)})
                try:
                    if process is None:
                        raise ValueError('Server unavailable for write failure check')
                    modes = {p: p.stat().st_mode & 0o777 for p in [database.parent, *database.parent.rglob('*')]}
                    stop_server(process)
                    process = None
                    try:
                        for path in modes:
                            path.chmod(0o555 if path.is_dir() else 0o444)
                        try:
                            process = start(server_prefix, product, server_env, log, timeout=3)
                        except ValueError:
                            pass  # Refusing readiness on unwritable durable storage is safe.
                        if process is not None:
                            try:
                                status, data = probe(base)[1]()
                                assert status >= 500 and data.get('error'), f'Failed durable write acknowledged with {status}'
                            except LoginRefused:
                                pass  # Refusing to sign in on unwritable storage is safe, like refusing readiness.
                    finally:
                        stop_server(process)
                        process = None
                        for path, mode in modes.items():
                            path.chmod(mode)
                    process = start(server_prefix, product, server_env, log)
                    snapshot, write, count = probe(base)
                    assert count() == 0, 'A refused write was kept'
                    assert snapshot() == saved, 'Committed data changed after the storage failure'
                    status, _ = write()
                    assert (200 <= status < 300 if metadata.get('adapter') else status == 201), 'Restoring writable storage must permit retry'
                    assert count() == 1, 'Retry must be kept exactly once'
                    checks.append({'name': 'storage_failure_not_acknowledged', 'ids': ids['storage'], 'passed': True})
                except (OSError, ValueError, KeyError, TypeError, StopIteration, AssertionError) as error:
                    checks.append({'name': 'storage_failure_not_acknowledged', 'ids': ids['storage'], 'passed': False, 'error': str(error)})
                stop_server(process)
                process = None
                try:
                    # DATABASE_PATH is a disposable file or directory; corrupt existing bytes without resetting.
                    if database.is_dir():
                        files = sorted(p for p in database.rglob('*') if p.is_file())
                        if not files:
                            raise ValueError('Database has no durable files')
                    else:
                        files = [database]
                    for damaged in files:
                        damaged.write_bytes(b'benchmark-invalid-database\x00')
                    originals = {damaged: damaged.read_bytes() for damaged in files}
                    try:
                        process = start(server_prefix, product, server_env, log, timeout=3)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError('Malformed database was silently accepted')
                    assert all(damaged.read_bytes() == original for damaged, original in originals.items())
                    checks.append({'name': 'malformed_database_preserved', 'ids': ids['malformed'], 'passed': True})
                except (OSError, ValueError, AssertionError) as error:
                    checks.append({'name': 'malformed_database_preserved', 'ids': ids['malformed'], 'passed': False, 'error': str(error)})
                stop_server(process)
                process = None
            result.update(tests=len(checks), failures=sum(not item['passed'] for item in checks), checks=checks,
                          returncode=grader.returncode)
            result['accepted'] = len(checks) == expected and not result['failures'] and grader.returncode == 0
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            output += '\n' + str(error)
            result.update(error=str(error), errors=1, checks=checks)
        finally:
            stop_server(process)
            stop_server(proxy)
            if (raw := temporary / 'qa' / 'raw.jsonl').is_file():
                shutil.copy2(raw, artifact / 'qa-raw.jsonl')  # the adapter's view of the product, kept for review
    result['requirements'] = {identifier: {
        'passed': bool(related := [check for check in checks if identifier in check.get('ids', [])]) and all(check['passed'] for check in related),
        'checks': [check['name'] for check in related],
    } for identifier in metadata.get('requirement_ids', [])}
    result['outcomes'] = [{**outcome, 'accepted': all(result['requirements'][identifier]['passed'] for identifier in outcome['requirements'])}
                          for outcome in metadata.get('outcomes', [])]
    result['screenshots'] = {name: str(path) for name, filename in {
        'desktop': 'viewport-1280.png', 'mobile': 'viewport-360.png', 'details': 'desktop-details.png',
    }.items() if (path := artifact / filename).is_file()}
    (artifact / 'grading.log').write_text(output)
    artifact.with_suffix('.txt').write_text(output)
    return result, output
