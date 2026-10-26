"""Host-only durable boundaries. Checkpoints are evidence, never approval authority."""
import hashlib
import inspect
import json
import os
import tempfile
from pathlib import Path

from v2_contract import strict_json


def strict_events(path):
    path = Path(path)
    if not path.exists():
        return []
    data = path.read_text()
    if data and not data.endswith('\n'):
        raise ValueError('truncated durable journal: ' + str(path))
    rows = []
    for line in data.splitlines():
        value = strict_json(line)
        if not isinstance(value, dict):
            raise TypeError('non-object durable journal: ' + str(path))
        rows.append(value)
    return rows


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    parent_existed = path.parent.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not parent_existed:
        directory = os.open(path.parent.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def append(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        stream.write(json.dumps(value, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def save(run_dir, state):
    """Journal first: an interruption between writes recovers the durable journal tail."""
    root = Path(run_dir)
    rows = strict_events(root / 'checkpoint.jsonl')
    record = {'sequence': len(rows), 'previous': sha(rows[-1]) if rows else None, 'state': state}
    append(root / 'checkpoint.jsonl', record)
    atomic_json(root / 'checkpoint.json', record)


def load(run_dir):
    root = Path(run_dir)
    rows = strict_events(root / 'checkpoint.jsonl')
    if not rows:
        raise ValueError('durable checkpoint missing; cannot recover historical runs')
    previous = None
    for index, row in enumerate(rows):
        if set(row) != {'sequence', 'previous', 'state'} or row['sequence'] != index or row['previous'] != previous:
            raise ValueError('durable checkpoint chain corrupted')
        previous = sha(row)
    if (root / 'checkpoint.json').exists():
        checkpoint = strict_json((root / 'checkpoint.json').read_text())
        if checkpoint not in rows[-2:]:
            raise ValueError('checkpoint does not match durable journal')
    return rows[-1]['state']


def file_binding(path):
    path = Path(path).resolve()
    if not path.exists():
        raise ValueError('runtime/read-only binding missing: ' + str(path))
    if path.is_file():
        return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'mode': path.stat().st_mode & 0o777}
    from v2_gates import tree_sha256
    return {'path': str(path), 'sha256': tree_sha256(path)}


def host_binding(repo, tools, read_only, callbacks, runtime):
    callback_sources = []
    for callback in callbacks:
        if callback is None:
            callback_sources.append(None)
            continue
        # Host callbacks must be supplied again; this identifies their implementation,
        # not an authority inferred from serialized Python names.
        try:
            callback_sources.append(inspect.getsource(callback))
        except (TypeError, OSError):
            raise ValueError('host callback must have inspectable implementation') from None
    return {'repo': str(repo), 'tools': tools,
            'tool_files': [file_binding(value['path']) for value in tools.values() if isinstance(value, dict) and 'path' in value],
            'read_only': [file_binding(path) for path in read_only], 'callbacks': callback_sources,
            'runtime': [file_binding(path) for path in runtime]}


def register(common, plan_digest, run_dir):
    """Caller holds the repository common-dir lock before registration or paid work."""
    path = Path(common) / 'plumb-v2-runs' / (plan_digest + '.json')
    if path.exists():
        if json.loads(path.read_text()) != {'run_dir': str(run_dir)}:
            raise ValueError('plan already registered to another run_dir; resume its original run')
    else:
        atomic_json(path, {'run_dir': str(run_dir)})
