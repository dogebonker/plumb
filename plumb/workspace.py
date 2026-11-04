"""Bounded committed Git imports; source provenance never grants approval."""
import hashlib
import json
import os
import re
import selectors
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

from .core import _EXCLUDED, MAX_BYTES, MAX_FILE_BYTES, MAX_FILES, _relative

_CONFIG = '.plumb/source.json'
_CAPTURE = 'sources/decision.md'
_PREFIX = '<!-- plumb-source '


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'))


def _git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1',
               GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    command = ['git', '-c', 'core.hooksPath=' + os.devnull,
               '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never',
               '-C', str(repo), *args]
    output = bytearray()
    try:
        with tempfile.TemporaryFile() as errors, subprocess.Popen(
                command, env=env, stdout=subprocess.PIPE, stderr=errors) as process:
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    deadline = time.monotonic() + 15
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not selector.select(remaining):
                            raise ValueError('Git source timed out')
                        chunk = os.read(process.stdout.fileno(), min(65536, MAX_BYTES + 1 - len(output)))
                        if not chunk:
                            break
                        output.extend(chunk)
                        if len(output) > MAX_BYTES:
                            raise ValueError('Git output exceeds snapshot limit')
                if process.wait(timeout=max(0.01, deadline - time.monotonic())):
                    raise ValueError('Git source unavailable')
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError('Git source unavailable') from error
    return bytes(output)


def _identity(repo):
    root = _git(repo, 'rev-parse', '--show-toplevel').decode().strip()
    # Always pin the local checkout identity as well: an origin alone cannot distinguish clones.
    identity = {'local': 'local-git:' + str(Path(root).resolve())}
    try:
        origin = _git(repo, 'config', '--local', '--get', 'remote.origin.url').decode().strip()
    except ValueError:
        origin = ''
    match = re.fullmatch(r'git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?', origin)
    if match:
        identity['origin'] = 'https://github.com/' + '/'.join(match.groups())
    elif origin.startswith(('https://', 'http://', 'ssh://', 'git://')):
        parsed = urlsplit(origin)
        if parsed.hostname and parsed.path:
            identity['origin'] = 'https://' + parsed.hostname + parsed.path.removesuffix('.git')
    return identity


def _commit(repo, ref):
    if not isinstance(ref, str) or not ref or ref.startswith('-') or '\x00' in ref:
        raise ValueError('Invalid Git ref')
    return _git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()


def _entries(repo, commit, selections):
    selected = set()
    for name in selections:
        _relative(name)
        selected.add(name)
    if not selected:
        raise ValueError('Select at least one code path')
    result, found = {}, set()
    for record in _git(repo, 'ls-tree', '-rz', '--full-tree', commit, '--', *sorted(selected)).split(b'\0'):
        if not record:
            continue
        head, raw_path = record.split(b'\t', 1)
        path = raw_path.decode('utf-8')
        matching = [s for s in selected if path == s or path.startswith(s + '/')]
        if not matching:
            continue
        _relative(path)
        mode, kind, blob = head.decode().split()
        if mode not in ('100644', '100755') or kind != 'blob':
            raise ValueError('Only tracked regular files are allowed: ' + path)
        found.update(matching)
        result[path] = blob
        if len(result) > MAX_FILES:
            raise ValueError('Too many selected files')
    if found != selected:
        raise ValueError('Selected path is not a tracked regular file or directory')
    return result


def _blob(repo, blob):
    size = int(_git(repo, 'cat-file', '-s', blob))
    if size > MAX_FILE_BYTES:
        raise ValueError('File exceeds snapshot limit')
    data = _git(repo, 'cat-file', 'blob', blob)
    try:
        text = data.decode('utf-8')
    except UnicodeError as error:
        raise ValueError('Binary source file') from error
    if '\x00' in text:
        raise ValueError('Binary source file')
    return data


def _source(repo, config):
    commit = _commit(repo, config['ref'])
    entry = _entries(repo, commit, [config['path']])
    if set(entry) != {config['path']}:
        raise ValueError('Source must be one tracked regular file')
    blob = entry[config['path']]
    body = _blob(repo, blob)
    metadata = {'provider': 'git', 'repository': config['repository'], 'path': config['path'],
                'ref': config['ref'], 'commit': commit, 'blob': blob, 'version': blob,
                'body_sha256': _hash(body)}
    return metadata, body


def _capture(metadata, body):
    return (_PREFIX + _json(metadata) + ' -->\n').encode() + body


def _read(root, name, limit=MAX_FILE_BYTES):
    _relative(name)
    path = root
    for part in name.split('/'):
        path = path / part
        if path.is_symlink():
            raise ValueError('Workspace aliases are not allowed')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Managed source must be a regular file')
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Workspace file exceeds limit')
    return data


def _load(workspace):
    root = Path(workspace).absolute()
    if root.resolve() != root or not root.is_dir():
        raise ValueError('Workspace must be a real directory without symlinks')
    config = json.loads(_read(root, _CONFIG))
    if not isinstance(config, dict):
        raise TypeError('Invalid Git connection config')
    if config.get('format') != 1 or config.get('provider') != 'git':
        raise ValueError('Invalid Git connection config')
    for key in ('repository', 'ref', 'path', 'module', 'section', 'code', 'initial_commit'):
        if key not in config:
            raise ValueError('Incomplete Git connection config')
    data = _read(root, _CAPTURE, MAX_FILE_BYTES + 16384)
    header, separator, body = data.partition(b'\n')
    if not separator or not header.startswith(_PREFIX.encode()) or not header.endswith(b' -->'):
        raise ValueError('Invalid managed source capture')
    metadata = json.loads(header[len(_PREFIX):-4])
    if not isinstance(metadata, dict):
        raise TypeError('Invalid managed source metadata')
    if metadata.get('body_sha256') != _hash(body):
        raise ValueError('Managed source body was edited; refusing to overwrite')
    if any(metadata.get(key) != config[key] for key in ('repository', 'path', 'ref')):
        raise ValueError('Capture does not match connection config')
    if metadata.get('provider') != 'git' or metadata.get('blob') != metadata.get('version'):
        raise ValueError('Invalid managed source metadata')
    return root, config, metadata, body, data


def _section(text, title):
    if title is None:
        return text
    if not isinstance(title, str) or not title.strip():
        raise ValueError('Section must name a Markdown heading')
    wanted = re.sub(r'^#{1,6}\s+', '', title).strip()
    wanted = re.sub(r'[ \t]+#+[ \t]*$', '', wanted)
    lines, headings, fence = text.splitlines(keepends=True), [], None
    for index, line in enumerate(lines):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        heading = re.match(r'^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*$', line.rstrip('\r\n'))
        if heading:
            headings.append((index, len(heading[1]), re.sub(r'[ \t]+#+[ \t]*$', '', heading[2])))
        elif index and re.fullmatch(r' {0,3}(=+|-+)[ \t]*', line.rstrip('\r\n')):
            previous = lines[index - 1].strip()
            if previous and not lines[index - 1].startswith(('    ', '\t')):
                headings.append((index - 1, 1 if line.lstrip().startswith('=') else 2, previous))
    matches = [(i, depth) for i, depth, name in headings if name == wanted]
    if len(matches) != 1:
        raise ValueError('Section heading must match exactly once')
    start, depth = matches[0]
    stop = next((i for i, d, _ in headings if i > start and d <= depth), len(lines))
    return ''.join(lines[start:stop])


def _atomic(path, data):
    descriptor, temporary = tempfile.mkstemp(prefix='.plumb-source-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def is_connected(workspace):
    config = Path(workspace) / _CONFIG
    return config.exists() or config.is_symlink()


def initialize(workspace, repo, module, paths, source_path, *, ref='HEAD', section=None):
    """Create a new workspace from a single resolved committed Git tree."""
    root = Path(workspace).absolute()
    if root.exists() or root.is_symlink():
        raise ValueError('Initialization requires a new workspace')
    if root.parent.resolve() != root.parent or not root.parent.is_dir():
        raise ValueError('Workspace parent must be a real directory')
    if not isinstance(module, str) or not module.strip() or '\n' in module or '\r' in module:
        raise ValueError('Module must be a nonempty single line')
    _relative(source_path)
    commit = _commit(repo, ref)
    entries = _entries(repo, commit, paths)
    for name in entries:
        parts = name.split('/')
        if any(p.startswith('.') for p in parts) or any(p in _EXCLUDED for p in parts[:-1]):
            raise ValueError('Selected code path is excluded from review: ' + name)
    code = {name: _blob(repo, blob) for name, blob in entries.items()}
    config = {'format': 1, 'provider': 'git', 'repository': _identity(repo),
              'module': module, 'ref': ref, 'path': source_path, 'section': section,
              'initial_commit': commit, 'code': {name: 'code/' + name for name in code}}
    # Pin initialization to the same commit used for code, then retain the configured ref.
    metadata, body = _source(repo, {**config, 'ref': commit})
    metadata['ref'] = ref
    selected = _section(body.decode('utf-8'), section)
    origin = config['repository'].get('origin', '')
    link = (origin + '/blob/' + commit + '/' + source_path if origin.startswith('https://github.com/')
            else config['repository']['local'] + '@' + commit + ':' + source_path)
    files = {'code/' + name: data for name, data in code.items()}
    files[_CAPTURE] = _capture(metadata, body)
    files['knowledge/index.md'] = ('---\nokf_version: "0.2"\n---\n\n# ' + module +
        '\n\nUnreviewed import. No agreement or verification is implied.\n\n'
        '- [Module](module.md)\n- [Imported intent](intent.md)\n').encode()
    files['knowledge/module.md'] = ('---\ntype: Software Module\nstatus: draft\n---\n\n# ' + module +
        '\n\nUnreviewed committed code snapshot.\n\n' + ''.join('- `' + name + '` → `' + target + '`\n'
        for name, target in config['code'].items())).encode()
    files['knowledge/intent.md'] = ('---\ntype: Module Contract\nstatus: draft\n---\n\n'
        'Unreviewed verbatim source import; no agreed intent is inferred from code.\n\n'
        'Source: ' + link + '\n\n' + selected).encode()
    if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_BYTES or any(len(v) > MAX_FILE_BYTES for v in files.values()):
        raise ValueError('Generated workspace exceeds snapshot limits')
    staging = Path(tempfile.mkdtemp(prefix='.plumb-init-', dir=root.parent))
    try:
        for name, data in files.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (staging / '.plumb').mkdir()
        (staging / _CONFIG).write_text(_json(config) + '\n')
        # mkdir is exclusive even if another initializer races us.
        root.mkdir()
        for entry in staging.iterdir():
            os.rename(entry, root / entry.name)
    finally:
        shutil.rmtree(staging)
    return status(root, repo)


def status(workspace, repo):
    """Check the explicit repository and current ref without changing any files."""
    try:
        _root, config, captured, body, data = _load(workspace)
        if _identity(repo) != config['repository']:
            raise ValueError('Explicit repository does not match the connection')
        latest, _latest_body = _source(repo, config)
        # Verify captured bytes against the recorded Git object, including metadata edits.
        recorded = _blob(repo, captured['blob'])
        if body != recorded or _commit(repo, captured['commit']) != captured['commit']:
            raise ValueError('Captured source does not match Git provenance')
        old_entry = _entries(repo, captured['commit'], [config['path']])
        if old_entry.get(config['path']) != captured['blob']:
            raise ValueError('Captured source version does not match its commit')
        current = latest['blob'] == captured['blob']
        result = {'status': 'current' if current else 'changed', 'source': captured,
                  'latest': latest, 'capture': {'path': _CAPTURE, 'sha256': _hash(data), 'body_start_line': 2}}
        if current:
            result['binding'] = {'scope': 'local_git_ref', 'connection': _hash(_json(config).encode()),
                                 'version': captured['blob'], 'capture_sha256': _hash(data)}
        return result
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        return {'status': 'unavailable', 'error': str(error)}


def refresh(workspace, repo):
    current = status(workspace, repo)
    if current['status'] == 'unavailable':
        raise ValueError(current['error'])
    if current['status'] == 'current':
        return {**current, 'status': 'unchanged', 'knowledge_updated': False, 'review_required': False}
    root, config, _metadata, _body, _data = _load(workspace)
    latest, latest_body = _source(repo, config)
    updated = _capture(latest, latest_body)
    if len(updated) > MAX_FILE_BYTES:
        raise ValueError('Source capture exceeds snapshot limit')
    _atomic(root / _CAPTURE, updated)
    verified = status(workspace, repo)
    if verified['status'] != 'current':
        raise ValueError('Capture updated, but Git source is ' + verified['status'] + '; recheck source status')
    return {**verified, 'status': 'updated', 'knowledge_updated': False, 'review_required': True}


def verify_binding(workspace, repo, binding):
    current = status(workspace, repo)
    if current['status'] != 'current' or current.get('binding') != binding:
        raise ValueError('Git source binding is stale, unavailable, or modified')
