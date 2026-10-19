"""Bounded v2 mechanical evidence; execution fails closed without macOS Seatbelt.

Archgraph proves export names; the pinned TypeScript compiler helper additionally
proves signatures. Other signature capabilities remain unsupported. FR coverage
is a frozen-runner report, not proof against deliberate exploits of that runner.
NFR reports use {"nfr": {criterion_id: observed_number}}; thresholds mean at_most.
Commands get one TCP loopback server port through FACTORY_TEST_PORT. Releasing
its reservation before launch leaves a race; this is not server identity proof.
Deadlines terminate the leader/current process group; detached descendants can survive.
"""
import hashlib
import io
import json
import math
import os
import selectors
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

try:
    from .v2_contract import (
        checked_path,
        covered,
        digest,
        relative_path,
        sha,
        strict_json,
        validate_plan,
    )
except ImportError:
    from v2_contract import (
        checked_path,
        covered,
        digest,
        relative_path,
        sha,
        strict_json,
        validate_plan,
    )

BINDING_FIELDS = {'plan_sha256', 'source_commit', 'source_tree', 'contract_sha256', 'policy_sha256', 'tools_sha256'}


def _sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def tree_sha256(root):
    """Pin entries and resolve link chains inside the tree without traversing aliases."""
    original = Path(root)
    if original.is_symlink() or not original.is_dir():
        raise ValueError('dependency tree root must be a real directory')
    root = original.resolve()
    entries = {}
    def resolve(current, parts, seen):
        for part in parts:
            if part in ('', '.'):
                continue
            if part == '..':
                if current == root:
                    raise ValueError('dependency link outside trusted tree')
                current = current.parent
                continue
            current /= part
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode):
                target = Path(os.readlink(current))
                if target.is_absolute():
                    raise ValueError('dependency link outside trusted tree')
                if current in seen:
                    raise ValueError('cyclic dependency link')
                current = resolve(current.parent, target.parts, seen | {current})
        return current
    def visit(directory):
        for path in sorted(directory.iterdir()):
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            record = {'mode': stat.S_IMODE(info.st_mode)}
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                try:
                    resolve(root, path.relative_to(root).parts, set())
                    path.stat()  # Verify actual traversal, including invalid non-directory/.. components.
                except OSError as error:
                    raise ValueError('dangling or invalid dependency link: ' + relative) from error
                record.update(kind='symlink', target=target)
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink != 1:
                    raise ValueError('hardlinked dependency file: ' + relative)
                record.update(kind='file', sha256=_sha(path))
            elif stat.S_ISDIR(info.st_mode):
                record['kind'] = 'directory'
                visit(path)
            else:
                raise ValueError('unsupported dependency entry: ' + relative)
            entries[relative] = record
    visit(root)
    return digest(entries)


def _git(root, *args):
    return subprocess.check_output(['/usr/bin/git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
                                    '-C', str(root), *args], stderr=subprocess.PIPE)


def _files(root):
    names = _git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').decode().split('\0')
    result = {}
    for name in sorted(set(filter(None, names))):
        relative_path(name, controls=True)
        path = checked_path(root, name)
        if path.exists() and not path.is_file():
            raise ValueError('tracked source is not a regular file: ' + name)
        if path.is_file():
            result[name] = {'sha256': _sha(path), 'executable': bool(path.stat().st_mode & 0o111)}
    return result


def snapshot(worktree: Path, frozen: list[dict], tools: dict) -> dict:
    root = Path(worktree).resolve()
    files = _files(root)
    for entry in frozen:
        relative_path(entry['path'], controls=True)
        path = checked_path(root, entry['path'])
        if not path.is_file() or _sha(path) != entry['sha256']:
            raise ValueError('frozen input changed: ' + entry['path'])
    if 'dependencylock' in tools and 'dependencytree' not in tools:
        raise ValueError('dependency tree pin required alongside installed lock')
    if 'typescript' in tools and ('typescriptlib' not in tools
            or Path(tools['typescriptlib']['path']).resolve() != Path(tools['typescript']['path']).resolve().parent):
        raise ValueError('TypeScript compiler lib tree pin required')
    for name, tool in tools.items():
        path = Path(tool['path'])
        if (not path.is_absolute() or not (path.is_file() or path.is_dir())
                or (tree_sha256(path) if path.is_dir() else _sha(path)) != tool['sha256']):
            raise ValueError('pinned tool changed: ' + name)
    return {'source_commit': _git(root, 'rev-parse', 'HEAD').decode().strip(),
            'source_tree': digest(files), 'tools_sha256': digest(tools)}


def check_scope(worktree, base_commit, owns) -> dict:
    root = Path(worktree).resolve()
    for path in owns:
        relative_path(path, directory=True)
    changed = set(filter(None, _git(root, 'diff', '--no-ext-diff', '--no-textconv', '--name-only', '--no-renames', '-z', base_commit, '--').decode().split('\0')))
    changed.update(filter(None, _git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')))
    violations = sorted(p for p in changed if not covered(p, owns))
    return {'status': 'fail' if violations else 'pass', 'base_commit': base_commit,
            'changed': sorted(changed), 'violations': violations}


def check_surfaces(expected: list[dict], exported: dict) -> dict:
    if exported.get('complete') is not True or exported.get('limitations'):
        return {'status': 'unsupported', 'reason': 'export coverage incomplete'}
    files = exported.get('files', [])
    files = {x['path'] if isinstance(x, dict) else x for x in files}
    if not {x['path'] for x in expected} <= files:
        return {'status': 'unsupported', 'reason': 'declared surface files absent from scan'}
    actual = exported.get('exports')
    if not isinstance(actual, list):
        return {'status': 'unsupported', 'reason': 'export evidence missing'}
    wanted = {(x['path'], x['symbol']): x['signature'] for x in expected}
    found = {}
    for entry in actual:
        path, symbol = entry.get('path', entry.get('file')), entry.get('symbol', entry.get('name'))
        if not isinstance(path, str) or not isinstance(symbol, str):
            return {'status': 'unsupported', 'reason': 'malformed export evidence'}
        if (path, symbol) not in wanted:
            return {'status': 'fail', 'reason': 'undeclared export: ' + path + '::' + symbol}
        if entry.get('compatible') is False:
            return {'status': 'fail', 'reason': 'incompatible export type: ' + path + '::' + symbol}
        if not isinstance(entry.get('signature'), str):
            return {'status': 'unsupported', 'reason': 'pinned exporter does not prove signatures'}
        found[path, symbol] = entry['signature']
    if found != wanted:
        return {'status': 'fail', 'reason': 'export names or signatures differ from contract'}
    return {'status': 'pass', 'exports': actual, 'files': sorted(files)}


def verify_evidence(evidence, current_binding) -> None:
    if (not isinstance(current_binding, dict) or set(current_binding) != BINDING_FIELDS
            or not isinstance(evidence, dict) or evidence.get('binding') != current_binding):
        raise ValueError('gate evidence binding mismatch')
    for key, value in current_binding.items():
        sha(value, 40 if key == 'source_commit' else 64)
    rows, required = evidence.get('gates'), evidence.get('required_gates')
    if not isinstance(rows, list) or not isinstance(required, list) or not required or any(not isinstance(row, dict) for row in [*rows, *required]):
        raise ValueError('gate evidence incomplete or not passing')
    declared = [(row.get('id'), row.get('kind')) for row in required]
    executed = [(row.get('id'), row.get('kind')) for row in rows if row.get('kind') in ('tests', 'typecheck', 'lint', 'nfr')]
    if (len(set(declared)) != len(declared) or sorted(declared) != sorted(executed)
            or not {'tests', 'typecheck', 'lint'} <= {row.get('kind') for row in required}):
        raise ValueError('required gate evidence missing or duplicated')
    if (evidence.get('status') != 'pass'
            or any(evidence.get(key, {}).get('status') != 'pass' for key in ('scope', 'architecture', 'surfaces'))):
        raise ValueError('gate evidence incomplete or not passing')
    for row in rows:
        if (row.get('status') != 'pass' or row.get('exit_code') != 0
                or not isinstance(row.get('argv'), list) or not row['argv']
                or type(row.get('duration_ms')) is not int or row['duration_ms'] < 0):
            raise ValueError('gate evidence incomplete or not passing')
        sha(row.get('output_sha256'))
    for requirement in required:
        row = next(row for row in rows if (row['id'], row['kind']) == (requirement['id'], requirement['kind']))
        if not set(requirement.get('case_ids', [])) <= set(row.get('case_ids', [])):
            raise ValueError('required FR execution coverage missing')
        for criterion in requirement.get('nfr', []):
            measurements = [value for value in row.get('nfr', [])
                            if value.get('id') == criterion['id'] and value.get('threshold') == criterion['threshold']]
            if (len(measurements) != 1 or measurements[0].get('threshold') != criterion['threshold']
                    or measurements[0].get('operator') != 'at_most'
                    or type(measurements[0].get('observed')) not in (int, float)
                    or type(measurements[0]['observed']) is float and not math.isfinite(measurements[0]['observed'])
                    or measurements[0]['observed'] > criterion['threshold']):
                raise ValueError('required NFR measurement evidence missing or exceeding threshold')


def _sandbox_profile(source, scratch, outputs, read_only, test_port=None):
    # Explicit local test servers only; no home or arbitrary dependency-cache access.
    def rule(action, path, tree=True):
        return '(' + action + ' (' + ('subpath' if tree else 'literal') + ' ' + json.dumps(str(Path(path).resolve())) + '))'
    rules = ['(version 1)', '(deny default)', '(allow process-exec process-fork)',
             '(allow signal (target self))', '(allow signal (target children))',
             '(deny process-info* (target others))',
             '(allow file-read-metadata)', '(allow file-read* (literal "/"))',
             '(allow file-read* (literal "/dev/null") (literal "/dev/urandom") (literal "/dev/random"))',
             '(allow file-write* (literal "/dev/null"))']
    if test_port is not None:
        if type(test_port) is not int or not 1 <= test_port <= 65535:
            raise ValueError('invalid sandbox test port')
        endpoint = json.dumps('localhost:' + str(test_port))
        rules.extend(['(allow network-bind (local tcp ' + endpoint + '))',
                      '(allow network-inbound (local tcp ' + endpoint + '))',
                      '(allow network-outbound (remote tcp ' + endpoint + '))'])
    # Exact Node metadata and native page sizes; host process inspection and Mach lookup stay denied.
    metadata = ('kern.ostype', 'kern.osrelease', 'kern.version', 'kern.hostname',
                'hw.machine', 'hw.model', 'hw.memsize', 'hw.activecpu', 'hw.pagesize_compat')
    rules.append('(allow sysctl-read ' + ' '.join('(sysctl-name ' + json.dumps(key) + ')' for key in metadata) + ')')
    for path in ('/System/Library', '/usr/lib', '/usr/bin', '/usr/sbin', '/usr/libexec', '/usr/share',
                 '/bin', '/sbin', '/private/var/db/dyld'):
        rules.append(rule('allow file-read*', path))
    for path in (source, scratch, *read_only):
        rules.append(rule('allow file-read*', path, Path(path).is_dir()))
    for path in (scratch, *outputs):
        rules.append(rule('allow file-write*', path, Path(path).is_dir()))
    return '\n'.join(rules)


def _preflight(source, scratch, read_only):
    if sys.platform != 'darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        raise RuntimeError('native macOS sandbox-exec unavailable; no unsandboxed fallback')
    with tempfile.TemporaryDirectory(prefix='factory-canary-') as temp:
        sentinel = Path(temp).resolve() / 'sentinel'
        sentinel.write_text('protected')
        profile = _sandbox_profile(source, scratch, (), read_only)
        commands = [['/bin/cat', str(sentinel)], ['/usr/bin/touch', str(sentinel)],
                    ['/usr/bin/touch', str(source / '.factory-write-canary')]]
        for command in commands:
            result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, *command], capture_output=True, timeout=10, check=False)
            if result.returncode == 0:
                raise RuntimeError('sandbox denied-read/write preflight failed')
        result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, '/usr/bin/touch', str(scratch / 'allowed')], capture_output=True, timeout=10, check=False)
        if result.returncode != 0 or sentinel.read_text() != 'protected':
            raise RuntimeError('sandbox unavailable or canary changed')
        host = subprocess.Popen(['/bin/sleep', '20'])
        try:
            result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, '/bin/kill', '-TERM', str(host.pid)],
                                    capture_output=True, timeout=10, check=False)
            if result.returncode == 0 or host.poll() is not None:
                raise RuntimeError('sandbox host-signal denial preflight failed')
        finally:
            if host.poll() is None:
                host.kill()
            host.wait()


def _command(argv, root, scratch, outputs, read_only, log, timeout, tool_dirs=()):
    started = time.monotonic()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(('127.0.0.1', 0))
        test_port = reservation.getsockname()[1]
    profile = _sandbox_profile(root, scratch, outputs, read_only, test_port=test_port)
    limit = 4 * 1024 * 1024
    with log.open('xb') as stream:
        process = subprocess.Popen(['/usr/bin/sandbox-exec', '-p', profile, *argv], cwd=root,
                                   env={'PATH': ':'.join([*map(str, tool_dirs), '/usr/bin', '/bin', '/usr/sbin', '/sbin']), 'HOME': str(scratch),
                                        'TMPDIR': str(scratch), 'PYTHONDONTWRITEBYTECODE': '1', 'FACTORY_TEST_PORT': str(test_port),
                                        'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        size = 0
        try:
            while selector.get_map():
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(argv, timeout)
                for key, _ in selector.select(min(remaining, .2)):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fd)
                    else:
                        stream.write(chunk[:limit - size])
                        size += len(chunk)
                        if size > limit:
                            raise OverflowError('command output limit')
            code = process.wait(timeout=max(.001, timeout - (time.monotonic() - started)))
        except (subprocess.TimeoutExpired, OverflowError):
            code = -signal.SIGKILL
        finally:
            # Separate scratch directories also isolate processes that change groups.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            selector.close()
            process.stdout.close()
    row = {'argv': argv, 'exit_code': code, 'duration_ms': round((time.monotonic() - started) * 1000),
           'output_sha256': _sha(log), 'status': 'pass' if code == 0 else 'fail', 'test_port': test_port,
           'process_lifecycle': 'leader timeout and current process group cleanup; detached descendants not contained'}
    if code != 0:
        with log.open('rb') as captured:
            captured.seek(max(0, log.stat().st_size - 8192))
            tail = captured.read(8192).decode('utf-8', errors='replace')
        row['untrusted_output_excerpt'] = tail.encode('utf-8')[-8192:].decode('utf-8', errors='ignore')
    return row


def _base_copy(root, commit, destination):
    archive = _git(root, 'archive', '--format=tar', commit)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for entry in tar.getmembers():
            relative_path(entry.name.rstrip('/'), controls=True)
            if not (entry.isfile() or entry.isdir()):
                raise ValueError('baseline contains links or special files')
        tar.extractall(destination)


def _run_gates(worktree, plan, slice_id, binding, *, artifacts, tools, read_only=(), scope_base_commit=None, contract_inputs=(), final=False):
    evidence = {'binding': dict(binding), 'gates': [], 'required_gates': [], 'scope': {'status': 'unsupported'},
                'architecture': {'status': 'unsupported'}, 'surfaces': {'status': 'unsupported'}, 'status': 'unsupported'}
    try:
        validate_plan(plan)
        root = Path(worktree).resolve()
        artifacts = Path(artifacts).resolve()
        if artifacts == root or root in artifacts.parents:
            raise ValueError('artifacts must be outside worktree')
        artifacts.mkdir(parents=True, exist_ok=True)
        contract = next(s for s in plan['slices'] if s['kind'] == 'contract')
        for entry in contract_inputs:
            if (set(entry) != {'path', 'sha256', 'kind'} or entry['kind'] != 'interface'
                    or not covered(entry['path'], contract['owns'])):
                raise ValueError('invalid accepted contract input')
            relative_path(entry['path'])
            sha(entry['sha256'])
        if final:
            item = {'owns': [path for item in plan['slices'] for path in item['owns']],
                    'interfaces': [value for item in plan['slices'] for value in item['interfaces']],
                    'fr': [value for item in plan['slices'] for value in item['fr']],
                    'nfr': list({(value['id'], value['gate_id'], value['threshold']): value
                                 for item in plan['slices'] for value in item.get('nfr', [])}.values()),
                    'rules': {'surfaces': [value for item in plan['slices'] for value in item['rules']['surfaces']]},
                    'gates': list(dict.fromkeys(gate for item in plan['slices'] for gate in item['gates']))}
        else:
            item = next(s for s in plan['slices'] if s['id'] == slice_id)
        contract_files = {name for name in _files(root) if covered(name, contract['owns'])}
        if (final or item.get('kind') == 'feature' or contract_inputs) and {entry['path'] for entry in contract_inputs} != contract_files:
            raise ValueError('accepted contract input set incomplete or changed')
        definitions = {gate['id']: gate for gate in plan['policy']['gate_definitions']}
        final_test = plan['policy'].get('final_test_gate') if final else None
        if final_test:
            item['gates'] = [final_test, *(gate for gate in item['gates'] if definitions[gate]['kind'] != 'tests')]
            item['fr'] = list({fr['case_id']: dict(fr, gate_id=final_test) for fr in item['fr']}.values())
        evidence['required_gates'] = [{'id': ident, 'kind': definitions[ident]['kind'],
                                      'case_ids': [fr['case_id'] for fr in item['fr'] if fr['gate_id'] == ident],
                                      'nfr': [{'id': criterion['id'], 'threshold': criterion['threshold'], 'operator': 'at_most'}
                                              for criterion in item.get('nfr', []) if criterion['gate_id'] == ident]}
                                     for ident in item['gates']]
        frozen = [*plan['frozen_inputs'], *contract_inputs, dict(plan['policy']['layout'], kind='layout')]
        def fresh():
            current = {**snapshot(root, frozen, tools), 'plan_sha256': digest(plan),
                       'contract_sha256': digest({'slice': contract, 'files': list(contract_inputs)}),
                       'policy_sha256': digest(plan['policy'])}
            if current != binding:
                raise ValueError('source/policy/tool binding changed')
        fresh()
        scope_base = scope_base_commit or plan['base_commit']
        sha(scope_base, 40)
        evidence['scope'] = check_scope(root, scope_base, item['owns'])
        if evidence['scope']['status'] != 'pass':
            evidence['status'] = 'fail'
            return evidence
        if any(Path(name).suffix in ('.js', '.jsx', '.mjs', '.cjs') for name in _files(root) if covered(name, item['owns'])):
            raise RuntimeError('owned JavaScript surface proof is unsupported')
        language_map = {'.py': 'python', '.ts': 'typescript', '.tsx': 'typescript', '.mts': 'typescript', '.cts': 'typescript', '.go': 'go', '.ex': 'elixir', '.exs': 'elixir'}
        languages = {language_map[Path(p).suffix] for p in [*(name for name in _files(root) if covered(name, item['owns'])),
                     *(x['path'] for x in item['interfaces'])] if Path(p).suffix in language_map}
        if len(languages) != 1 or not {'archgraph', 'git'} <= tools.keys():
            raise RuntimeError('one supported language and pinned archgraph/git required')
        language = next(iter(languages))
        declared_reads = list(dict.fromkeys(Path(p).resolve() for p in read_only))
        trusted = list(dict.fromkeys([*declared_reads, *(Path(tool['path']).resolve() for tool in tools.values())]))
        with tempfile.TemporaryDirectory(prefix='factory-gates-') as temporary:
            temporary = Path(temporary).resolve()
            candidate, base, scratch = (temporary / name for name in ('candidate', 'base', 'scratch'))
            for path in (candidate, base, scratch):
                path.mkdir()
            for name, metadata in _files(root).items():
                target = candidate / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(checked_path(root, name).read_bytes())
                target.chmod(0o755 if metadata['executable'] else 0o644)
            copied = {name: {'sha256': _sha(candidate / name),
                             'executable': bool((candidate / name).stat().st_mode & 0o111)}
                      for name in _files(root)}
            if digest(copied) != binding['source_tree']:
                raise ValueError('candidate copy does not match bound source')
            for entry in frozen:
                target = candidate / entry['path']
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(checked_path(root, entry['path']).read_bytes())
                if _sha(target) != entry['sha256']:
                    raise ValueError('copied frozen input changed: ' + entry['path'])
            dependency_roots = [path for path in declared_reads if path.name == 'node_modules' and path.is_dir()]
            if dependency_roots:
                dependency_pin = tools.get('dependencylock', {})
                tree_pin = tools.get('dependencytree', {})
                if (len(dependency_roots) != 1 or Path(dependency_pin.get('path', '/')) != dependency_roots[0] / '.package-lock.json'
                        or Path(tree_pin.get('path', '/')).resolve() != dependency_roots[0]
                        or not any(entry['kind'] == 'dependency-lock' and entry['path'] == 'package-lock.json' for entry in plan['frozen_inputs'])):
                    raise RuntimeError('dependency mount requires one explicit node_modules root, pinned content tree, and installed/source lockfiles')
                if (candidate / 'node_modules').exists():
                    raise ValueError('dependency mount overlaps source')
                (candidate / 'node_modules').symlink_to(dependency_roots[0], target_is_directory=True)
            _base_copy(root, plan['base_commit'], base)
            layout = plan['policy']['layout']['path']
            if not (base / layout).is_file() or _sha(base / layout) != plan['policy']['layout']['sha256']:
                raise ValueError('baseline policy differs from approved policy')
            _preflight(candidate, scratch, trusted)
            counter = 0
            def execute(ident, kind, argv, cwd=candidate, outputs=(), timeout=60, reads=()):
                nonlocal counter
                fresh()
                counter += 1
                log = artifacts / (str(counter) + '.log')
                # Logs are controller-owned; names never derive from command output.
                command_scratch = temporary / ('command-' + str(counter))
                command_scratch.mkdir()
                row = _command(argv, cwd, command_scratch, outputs, trusted + [base, candidate, *reads], log, timeout,
                               list(dict.fromkeys(Path(tool['path']).parent for tool in tools.values())))
                fresh()
                row.update(id=ident, kind=kind)
                if row['status'] != 'pass':
                    row['recipe'] = 'Rerun this exact approved argv after correcting the reported ' + kind + ' failure.'
                evidence['gates'].append(row)
                return row, log
            produced_outputs = set()
            for ident in item['gates']:
                gate = definitions[ident]
                if gate['argv'][0] not in tools:
                    raise RuntimeError('gate executable missing from pinned tool map: ' + gate['argv'][0])
                outputs = []
                for name in gate.get('outputs', []):
                    path = checked_path(candidate, name)
                    if path.exists() and name not in produced_outputs:
                        raise ValueError('derived output already contains source: ' + name)
                    if not path.exists():
                        path.parent.mkdir(parents=True, exist_ok=True)
                        if name.endswith('/'):
                            path.mkdir()
                        else:
                            path.touch()
                    produced_outputs.add(name)
                    outputs.append(path)
                row, log = execute(ident, gate['kind'], [tools[gate['argv'][0]]['path'], *gate['argv'][1:]],
                                   outputs=outputs, timeout=gate['timeout_seconds'])
                cases = {fr['case_id'] for fr in item['fr'] if fr['gate_id'] == ident}
                if cases and row['status'] == 'pass':
                    try:
                        report = strict_json(log.read_text())
                        observed = report.get('case_ids')
                        if not isinstance(observed, list) or any(not isinstance(case, str) for case in observed):
                            raise ValueError('test report case_ids missing')
                        row['case_ids'] = sorted(set(observed))
                        if not cases <= set(observed):
                            raise ValueError('test report omits frozen FR cases')
                    except (ValueError, AttributeError) as error:
                        row.update(status='unsupported', reason=str(error), recipe='Use the approved frozen scenario runner to emit a JSON case_ids execution report.')
                criteria = [criterion for criterion in item.get('nfr', []) if criterion['gate_id'] == ident]
                if criteria and row['status'] == 'pass':
                    try:
                        measurements = strict_json(log.read_text()).get('nfr')
                        if not isinstance(measurements, dict):
                            raise TypeError('NFR measurement report missing')
                        row['nfr'] = []
                        for criterion in criteria:
                            value = measurements.get(criterion['id'])
                            if type(value) not in (int, float) or type(value) is float and not math.isfinite(value):
                                raise ValueError('NFR measurement missing or nonfinite: ' + criterion['id'])
                            row['nfr'].append({'id': criterion['id'], 'observed': value,
                                               'threshold': criterion['threshold'], 'operator': 'at_most'})
                        if any(value['observed'] > value['threshold'] for value in row['nfr']):
                            row.update(status='fail', reason='NFR measurement exceeds at_most threshold',
                                       recipe='Reduce the measured value to the frozen threshold and rerun the approved NFR argv.')
                    except (ValueError, AttributeError, TypeError) as error:
                        row.update(status='unsupported', reason=str(error),
                                   recipe='Emit finite JSON nfr measurements for every frozen NFR criterion using the approved runner.')
                if row['status'] != 'pass':
                    evidence['status'] = row['status']
                    evidence['reason'] = row.get('reason', 'approved ' + gate['kind'] + ' gate failed')
                    return evidence
            archgraph = tools['archgraph']['path']
            graphs = []
            for label, directory in (('base', base), ('candidate', candidate)):
                graph_directory = scratch / label
                graph_directory.mkdir()
                graph = graph_directory / 'graph.json'
                row, _ = execute('scan-' + label, 'architecture', [archgraph, 'scan', str(directory), '--engine', 'native',
                    '--language', language, '--symbols', '--rules', str(directory / layout), '--output', str(graph), '--no-daemon'], cwd=directory, outputs=[graph_directory])
                if row['status'] != 'pass' or not graph.is_file():
                    raise RuntimeError('archgraph scan unavailable')
                saved_graph = artifacts / (label + '.graph.json')
                with saved_graph.open('xb') as stream:
                    stream.write(graph.read_bytes())
                row['graph_sha256'] = _sha(saved_graph)
                graphs.append(graph)
            diff, diff_log = execute('architecture-diff', 'architecture', [archgraph, 'diff', *map(str, graphs), '--fail-on',
                              'new-forbidden,new-cycles', '--format', 'json', '--no-daemon'], reads=graphs)
            graph = strict_json(graphs[1].read_text())
            delta = strict_json(diff_log.read_text())
            if not all(isinstance(delta.get(key), list) for key in ('new_cycles', 'new_forbidden')):
                raise RuntimeError('new cycle/forbidden diff evidence missing')
            if not all(isinstance(graph.get(key), list) for key in ('cycles', 'edges', 'files')):
                raise RuntimeError('candidate architecture coverage missing')
            if graph.get('unresolved') or (graph.get('import_resolution') or {}).get('unresolved', 0):
                raise RuntimeError('candidate import resolution incomplete')
            typescript_sources = sorted(name for name in copied
                if (covered(name, item['owns']) or covered(name, contract['owns']))
                and Path(name).suffix in ('.ts', '.tsx', '.mts', '.cts'))
            if language == 'typescript':
                scanned = {entry['path'] for entry in graph['files']}
                missing = sorted(set(typescript_sources) - scanned)
                if missing:
                    raise RuntimeError('architecture scan missing source coverage: ' + ', '.join(missing))
            forbidden = [edge for edge in [*graph['edges'], *graph.get('external_edges', [])] if edge.get('verdict') == 'forbidden']
            evidence['architecture'] = {'status': 'pass' if diff['status'] == 'pass' and not delta['new_cycles'] and not delta['new_forbidden'] else 'fail',
                                        'cycles': graph['cycles'], 'forbidden': forbidden,
                                        'new_cycles': delta['new_cycles'], 'new_forbidden': delta['new_forbidden']}
            if final:
                check, check_log = execute('architecture-final', 'architecture', [archgraph, 'check', str(graphs[1]),
                    '--rules', str(candidate / layout), '--brief', '--no-daemon'], reads=graphs)
                current = strict_json(check_log.read_text())
                if isinstance(current, dict) and (current.get('schema'), current.get('kind')) == ('archgraph/brief/v1', 'check'):
                    current = current.get('result')
                if (not isinstance(current, dict) or current.get('schema') != 'archgraph/v1.2'
                        or current.get('kind') != 'check'
                        or not all(isinstance(current.get(key), list) for key in ('forbidden', 'cycles'))):
                    raise RuntimeError('final absolute architecture evidence incomplete')
                evidence['architecture'].update(forbidden=current['forbidden'], cycles=current['cycles'])
                if check['status'] != 'pass' or current['forbidden'] or current['cycles']:
                    evidence['architecture']['status'] = 'fail'
            row, log = execute('surface', 'surfaces', [archgraph, 'surface', str(graphs[1]), '--rules', str(candidate / layout), '--format', 'json', '--no-daemon'], reads=graphs)
            if row['status'] == 'pass':
                report = strict_json(log.read_text())
                report['files'] = graph.get('files', [])
                report['exports'] = [entry for module in report.get('modules', []) for entry in module.get('exported', [])]
                declarations = [*next(s for s in plan['slices'] if s['kind'] == 'contract')['interfaces'],
                                *item['interfaces'], *item['rules']['surfaces']]
                unique = {}
                for declaration in declarations:
                    key = declaration['path'], declaration['symbol']
                    if key in unique and unique[key] != declaration:
                        raise ValueError('surface conflicts with frozen contract: ' + declaration['path'])
                    unique[key] = declaration
                expected = list(unique.values())
                if language == 'typescript' and {'node', 'typescript', 'surfacehelper'} <= tools.keys():
                    expected_path, proof_path = scratch / 'expected.json', scratch / 'proof.json'
                    source_files = typescript_sources
                    # Include contract files as well as all owned source files, including undeclared files.
                    source_files = sorted(set(source_files) | {x['path'] for x in expected})
                    expected_path.write_text(json.dumps({'interfaces': expected, 'files': source_files}))
                    helper, _ = execute('surface-types', 'surfaces', [tools['node']['path'], tools['surfacehelper']['path'],
                        '--root', str(candidate), '--typescript', tools['typescript']['path'], '--expected', str(expected_path),
                        '--output', str(proof_path)], outputs=[proof_path], reads=[expected_path, Path(tools['typescript']['path']).parent])
                    saved_proof = artifacts / 'surface.proof.json'
                    with saved_proof.open('xb') as stream:
                        stream.write(proof_path.read_bytes())
                    helper['proof_sha256'] = _sha(saved_proof)
                    proof = strict_json(saved_proof.read_text())
                    if helper['exit_code'] == 2:
                        helper['status'] = 'unsupported'
                    if (proof.get('complete') is not True or proof.get('status') == 'unsupported'
                            or set(proof.get('files', [])) != set(source_files)):
                        evidence['surfaces'] = {'status': 'unsupported', 'reason': 'TypeScript surface proof incomplete'}
                    elif helper['exit_code'] != 0 or proof.get('status') != 'pass':
                        evidence['surfaces'] = {'status': 'fail', 'reason': 'TypeScript surface proof failed', 'errors': proof.get('errors', [])}
                    elif any(entry.get('compatible') is not True or not isinstance(entry.get('actual_signature'), str)
                             for entry in proof.get('exports', [])):
                        evidence['surfaces'] = {'status': 'unsupported', 'reason': 'TypeScript compatibility proof missing'}
                    elif not isinstance(report.get('complete'), bool):
                        evidence['surfaces'] = {'status': 'unsupported', 'reason': 'archgraph symbol coverage observation missing'}
                    else:
                        observed_exports = [entry for entry in report['exports'] if entry.get('file') in source_files]
                        arch_names = {(entry.get('file'), entry.get('name')) for entry in observed_exports}
                        type_names = {(entry.get('path'), entry.get('symbol')) for entry in proof.get('exports', [])}
                        evidence['surfaces'] = check_surfaces(expected, proof)
                        if not arch_names <= type_names or report['complete'] and arch_names != type_names:
                            evidence['surfaces'] = {'status': 'unsupported', 'reason': 'archgraph/compiler export coverage differs'}
                        evidence['surfaces']['archgraph'] = {'complete': report['complete'],
                            'limitations': report.get('limitations', []), 'observed_exports': observed_exports,
                            'global_observed_exports': report['exports']}
                else:
                    evidence['surfaces'] = check_surfaces(expected, report)
            fresh()
        statuses = [x['status'] for x in evidence['gates']] + [evidence[k]['status'] for k in ('scope', 'architecture', 'surfaces')]
        evidence['status'] = 'fail' if 'fail' in statuses else 'unsupported' if 'unsupported' in statuses else 'pass'
        if evidence['status'] == 'pass':
            verify_evidence(evidence, binding)
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError, KeyError, StopIteration, TypeError, AttributeError) as error:
        evidence['status'] = 'fail' if isinstance(error, ValueError) else 'unsupported'
        evidence['reason'] = str(error)
        evidence['recipe'] = 'Restore the approved binding and scope, or supply the missing pinned capability; rerun mechanical gates.'
    return evidence


def run_gates(worktree, plan, slice_id, binding, *, artifacts: Path, tools: dict,
              read_only: list[Path] = (), scope_base_commit=None, contract_inputs=()) -> dict:
    return _run_gates(worktree, plan, slice_id, binding, artifacts=artifacts, tools=tools,
                      read_only=read_only, scope_base_commit=scope_base_commit, contract_inputs=contract_inputs)


def run_final_gates(worktree, plan, binding, *, artifacts: Path, tools: dict,
                    read_only=(), contract_inputs=()) -> dict:
    return _run_gates(worktree, plan, None, binding, artifacts=artifacts, tools=tools,
                      read_only=read_only, contract_inputs=contract_inputs, final=True)
