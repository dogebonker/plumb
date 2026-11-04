"""Bounded, read-only reconciliation with separately invoked single-file edits."""
import copy
import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path, PurePosixPath

MAX_FILES = 256
MAX_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 256 * 1024
MAX_OUTPUT = 64 * 1024
OUTCOMES = ('aligned', 'code_wrong', 'spec_stale', 'sources_conflict', 'unknown')
ACTIONABLE = ('code_wrong', 'spec_stale')
_FIELDS = ('action', 'reads', 'searches', 'outcome', 'explanation', 'question', 'evidence', 'links', 'edits')
RESPONSE_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': list(_FIELDS),
    'properties': {
        'action': {'type': 'string', 'enum': ['inspect', 'finish']},
        'reads': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['path', 'start_line', 'end_line'], 'properties': {
                'path': {'type': 'string'}, 'start_line': {'type': 'integer'}, 'end_line': {'type': 'integer'}}}},
        'searches': {'type': 'array', 'items': {'type': 'string'}},
        'outcome': {'type': 'string', 'enum': ['', *OUTCOMES]},
        'explanation': {'type': 'string'}, 'question': {'type': 'string'},
        'evidence': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['path', 'quote'], 'properties': {'path': {'type': 'string'}, 'quote': {'type': 'string'}}}},
        'links': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['from_path', 'to_path', 'quote'], 'properties': {
                'from_path': {'type': 'string'}, 'to_path': {'type': 'string'}, 'quote': {'type': 'string'}}}},
        'edits': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['path', 'old', 'new', 'reason'], 'properties': {
                key: {'type': 'string'} for key in ('path', 'old', 'new', 'reason')}}},
    },
}
_EXCLUDED = {'node_modules', '__pycache__', 'venv', 'env', 'dist', 'build', 'evals', 'evaluation', 'evaluations'}


def _digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _identity(value):
    return _digest(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')))


def _verify_sources(binding, verifier, workspace):
    if binding is None:
        connection = Path(workspace) / '.plumb/source.json'
        if connection.exists() or connection.is_symlink():
            raise ValueError('Connected workspace requires a bound source check')
        return
    if not isinstance(binding, dict) or not binding or not callable(verifier):
        raise ValueError('Connected source requires a source verifier before proceeding')
    verifier(copy.deepcopy(binding))


def _relative(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Expected a workspace-relative POSIX path')
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError('Unsafe path: ' + name)
    return path


def _path(root, name):
    relative = _relative(name)
    target = root
    for part in relative.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('Symlinks are not allowed: ' + name)
    if not target.is_file():
        raise ValueError('Missing regular file: ' + name)
    return target


def _read(root, name):
    target = _path(root, name)
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Not a regular file: ' + name)
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('File exceeds snapshot limit: ' + name)
    text = data.decode('utf-8')
    if '\x00' in text:
        raise ValueError('Binary file: ' + name)
    return text


def _snapshot(workspace):
    root = Path(workspace).absolute()
    if root.is_symlink() or root.resolve() != root or not root.is_dir():
        raise ValueError('Workspace must be a real absolute directory without symlinks')
    files, skipped, size = {}, [], 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            if not name.startswith('.') and name not in _EXCLUDED and (Path(directory) / name).is_symlink():
                skipped.append({'path': (Path(directory) / name).relative_to(root).as_posix(),
                                'reason': 'Symlink directory was not captured'})
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in _EXCLUDED
                         and not (Path(directory) / d).is_symlink())
        for name in sorted(names):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if name.startswith('.'):
                continue
            if path.is_symlink():
                skipped.append({'path': relative, 'reason': 'Symlink file was not captured'})
                continue
            try:
                content = _read(root, relative)
            except (ValueError, UnicodeError, OSError) as error:
                skipped.append({'path': relative, 'reason': str(error)})
                continue
            if len(files) >= MAX_FILES or size + len(content.encode()) > MAX_BYTES:
                raise ValueError('Workspace exceeds bounded snapshot; select a smaller workspace')
            files[relative] = content
            size += len(content.encode())
    return root, files, skipped


def _validate(response, schema=RESPONSE_SCHEMA):
    """Validate the small exposed JSON schema without an extra dependency."""
    kind = schema['type']
    expected = {'object': dict, 'array': list, 'string': str, 'integer': int}[kind]
    if not isinstance(response, expected) or (kind == 'integer' and isinstance(response, bool)):
        raise ValueError('Model response has invalid ' + kind)
    if 'enum' in schema and response not in schema['enum']:
        raise ValueError('Model response has invalid enum')
    if kind == 'object':
        if set(response) != set(schema['required']):
            raise ValueError('Model response has missing or unexpected fields')
        for key, value in response.items():
            _validate(value, schema['properties'][key])
    elif kind == 'array':
        if len(response) > 32:
            raise ValueError('Too many model requests or findings')
        for value in response:
            _validate(value, schema['items'])


def _citation(snapshot, path, quote, seen):
    if path not in snapshot or not quote or len(quote) > MAX_OUTPUT:
        raise ValueError('Citation needs a known path and nonempty bounded quote')
    content = snapshot[path]
    matches = list(re.finditer(re.escape(quote), content))
    if not matches and path.endswith('.md'):
        words = re.split(r'\s+', quote.strip())
        matches = list(re.finditer(r'\s+'.join(re.escape(w) for w in words), content))
    match = next((match for match in matches if any(
        a <= match.start() and match.end() <= b for a, b in seen.get(path, []))), None)
    if match is None:
        raise ValueError('Citation must quote inspected snapshot text: ' + path)
    start, quote = match.start(), match.group()
    return {'path': path, 'quote': quote, 'line': content.count('\n', 0, start) + 1,
            'end_line': content.count('\n', 0, start + len(quote)) + 1}


def _inspect(snapshot, response, seen):
    results, used = [], 0
    for request in response['reads']:
        path = request['path']
        if path not in snapshot:
            raise ValueError('Read outside snapshot: ' + path)
        lines = snapshot[path].splitlines(keepends=True)
        first, last = request['start_line'], request['end_line']
        if first == last == 0:
            first, last = 1, max(1, len(lines))
        if first < 1 or last < first or last > max(1, len(lines)):
            raise ValueError('Invalid read line range')
        start = sum(map(len, lines[:first - 1]))
        text = ''.join(lines[first - 1:last])
        used += len(text.encode())
        if used > MAX_OUTPUT:
            raise ValueError('Inspection output limit exceeded; request smaller line ranges')
        seen.setdefault(path, []).append((start, start + len(text)))
        results.append({'path': path, 'start_line': first, 'end_line': last, 'text': text,
                        'sha256': _digest(snapshot[path])})
    searches = []
    for query in response['searches']:
        if not query or len(query) > 512:
            raise ValueError('Search must be a bounded nonempty literal string')
        hits = []
        for path, content in snapshot.items():
            offset = 0
            for number, line in enumerate(content.splitlines(keepends=True), 1):
                if query.casefold() in line.casefold():
                    used += len(line.encode())
                    if used > MAX_OUTPUT:
                        raise ValueError('Search output limit exceeded; narrow the search')
                    hits.append({'path': path, 'line': number, 'text': line})
                    seen.setdefault(path, []).append((offset, offset + len(line)))
                offset += len(line)
        searches.append({'query': query, 'hits': hits})
    return {'reads': results, 'searches': searches}


def _run(snapshot, model, *, mode, decision, max_rounds, trace=None):
    if not isinstance(max_rounds, int) or not 1 <= max_rounds <= 12:
        raise ValueError('max_rounds must be between 1 and 12')
    prompt = Path(__file__).with_name('reconcile.md').read_text()
    seen = {}
    if trace is None:
        trace = []
    payload = {'mode': mode, 'decision': decision, 'files': sorted(snapshot),
               'response_schema': RESPONSE_SCHEMA, 'results': {'reads': [], 'searches': []}}
    for number in range(1, max_rounds + 1):
        response = copy.deepcopy(model(prompt, copy.deepcopy(payload)))
        if len(json.dumps(response).encode()) > MAX_OUTPUT:
            raise ValueError('Model response exceeds output limit')
        entry = {'round': number, 'response': response}
        trace.append(entry)
        _validate(response)
        if response['action'] == 'inspect':
            if any(response[key] for key in ('outcome', 'explanation', 'question', 'evidence', 'links', 'edits')):
                raise ValueError('Inspect response must leave terminal fields empty')
            if not response['reads'] and not response['searches']:
                raise ValueError('Inspect must request text')
            results = _inspect(snapshot, response, seen)
            entry['results'] = results
            payload = {**payload, 'results': results, 'round': number + 1, 'history': copy.deepcopy(trace)}
            continue
        if response['reads'] or response['searches'] or response['outcome'] not in OUTCOMES:
            raise ValueError('Finish requires a terminal outcome and no inspection requests')
        evidence = [_citation(snapshot, item['path'], item['quote'], seen) for item in response['evidence']]
        links = []
        for link in response['links']:
            if link['to_path'] not in snapshot:
                raise ValueError('Link destination outside snapshot')
            citation = _citation(snapshot, link['from_path'], link['quote'], seen)
            links.append({**link, 'quote': citation['quote'], 'line': citation['line']})
        if mode == 'check' and response['edits']:
            raise ValueError('Check cannot propose edits')
        if response['outcome'] in ('aligned', 'code_wrong', 'spec_stale') and (
                not any(e['path'].startswith(('code/', 'src/')) for e in evidence) or not any(
                    e['path'].startswith(('knowledge/', 'sources/')) for e in evidence)):
            raise ValueError('Outcome requires inspected implementation and knowledge/source evidence')
        if response['outcome'] == 'sources_conflict':
            spans = {(e['path'], e['line'], e['quote']) for e in evidence if e['path'].startswith(('knowledge/', 'sources/'))}
            if len(spans) < 2 or not response['question'].strip():
                raise ValueError('Source conflict requires two cited spans and a human question')
        if (response['outcome'] == 'unknown' or mode == 'check' and response['outcome'] in ('code_wrong', 'spec_stale')) and not response['question'].strip():
            raise ValueError('Unresolved outcome requires a human question')
        return {**response, 'evidence': evidence, 'links': links, 'trace': trace}
    return {'outcome': 'unknown', 'explanation': 'Inspection round budget exhausted.',
            'question': 'Which source and implementation rule should govern this module?',
            'evidence': [], 'links': [], 'edits': [], 'trace': trace}


def reconcile(workspace: Path, model: callable, *, decision: str | None = None, max_rounds: int = 6,
              source_binding=None, verify_sources=None) -> dict:
    """Snapshot a workspace and ask the model to reconcile it without changing files."""
    if decision is not None and (not isinstance(decision, str) or not decision.strip()):
        raise ValueError('Decision must be explicit nonempty operator text')
    _verify_sources(source_binding, verify_sources, workspace)
    root, snapshot, skipped = _snapshot(workspace)
    hashes = {path: _digest(text) for path, text in snapshot.items()}
    trace = []
    if skipped:
        missing = ', '.join(item['path'] for item in skipped)
        result = {'outcome': 'unknown', 'explanation': 'Selected workspace is not fully readable: ' + missing,
                  'question': 'Can current readable captures be supplied for ' + missing + '?',
                  'evidence': [], 'links': [], 'edits': [], 'trace': trace, 'error': 'incomplete snapshot'}
    else:
        try:
            result = _run(snapshot, model, mode='check', decision=decision, max_rounds=max_rounds, trace=trace)
        except (ValueError, TypeError, KeyError) as error:
            result = {'outcome': 'unknown', 'explanation': 'Invalid model response: ' + str(error),
                      'question': 'What evidence or corrected response resolves this failed inspection?',
                      'evidence': [], 'links': [], 'edits': [], 'trace': trace, 'error': str(error)}
    for entry in result['trace']:
        entry['snapshot_id'] = _identity(hashes)
    _verify_sources(source_binding, verify_sources, workspace)
    report = {**result, 'workspace': str(root), 'snapshot': snapshot, 'hashes': hashes,
            'snapshot_id': _identity(hashes), 'decision': decision, 'skipped': skipped,
            'scope': 'captured_workspace', 'upstream_freshness': 'not_checked'}
    if source_binding is not None:
        report.update(source_binding=copy.deepcopy(source_binding), upstream_freshness='version_checked',
                      source_scope=source_binding.get('scope', 'connected_source'))
    return report


def _bound(report):
    snapshot, hashes = report['snapshot'], report['hashes']
    if not isinstance(snapshot, dict) or not snapshot or set(snapshot) != set(hashes):
        raise ValueError('Invalid bound snapshot')
    for path, text in snapshot.items():
        _relative(path)
        if not isinstance(text, str) or hashes[path] != _digest(text):
            raise ValueError('Snapshot hash mismatch: ' + path)
    return snapshot, hashes


def _edit(snapshot, choice, edits):
    if choice not in ('code', 'knowledge') or not isinstance(edits, list) or len(edits) != 1:
        raise ValueError('Explicit code/knowledge choice and exactly one edit required')
    edit = edits[0]
    if set(edit) != {'path', 'old', 'new', 'reason'} or not all(isinstance(v, str) for v in edit.values()):
        raise ValueError('Invalid edit fields')
    path = edit['path']
    _relative(path)
    prefixes = ('code/', 'src/') if choice == 'code' else ('knowledge/',)
    if path not in snapshot or not path.startswith(prefixes):
        raise ValueError('Edit outside chosen scope')
    old, new = edit['old'], edit['new']
    if not old or old == new or snapshot[path].count(old) != 1:
        raise ValueError('Edit requires one unambiguous changed text span')
    content = snapshot[path].replace(old, new, 1)
    if len(content.encode()) > MAX_FILE_BYTES:
        raise ValueError('Proposed file exceeds snapshot limit')
    return path, content


def propose(report: dict, choice: str, model: callable, *, max_rounds: int = 6, verify_sources=None) -> dict:
    """Generate one correction against the captured snapshot after an explicit choice."""
    if choice not in ('code', 'knowledge'):
        raise ValueError('Choose code or knowledge explicitly')
    if report.get('outcome') not in ACTIONABLE or report.get('skipped'):
        raise ValueError('A resolved actionable check is required; resolve intent/evidence and recheck first')
    binding = report.get('source_binding')
    _verify_sources(binding, verify_sources, report['workspace'])
    snapshot, hashes = _bound(report)
    result = _run(snapshot, model, mode='propose', decision={'choice': choice,
                  'operator_decision': report.get('decision'), 'finding': report.get('explanation'),
                  'question': report.get('question')}, max_rounds=max_rounds)
    if result.get('outcome') not in ACTIONABLE:
        raise ValueError('A resolved actionable proposal result is required before an edit')
    _edit(snapshot, choice, result['edits'])
    _verify_sources(binding, verify_sources, report['workspace'])
    proposal = {'workspace': report['workspace'], 'choice': choice, 'snapshot': copy.deepcopy(snapshot),
                'hashes': copy.deepcopy(hashes), 'edits': result['edits'], 'rationale': result['explanation'],
                'decision': report.get('decision'), 'trace': result['trace'],
                'evidence': result['evidence'], 'links': result['links'],
                'check_outcome': report['outcome'], 'proposal_outcome': result['outcome']}
    if binding is not None:
        proposal['source_binding'] = copy.deepcopy(binding)
    proposal['proposal_id'] = _identity(proposal)
    return proposal


def apply(proposal: dict, *, verify_sources=None) -> dict:
    """Apply one explicit proposal, checking all captured inputs before atomic replacement."""
    proposal = copy.deepcopy(proposal)
    ident = proposal.pop('proposal_id', None)
    if ident != _identity(proposal):
        raise ValueError('Proposal identity mismatch')
    if proposal.get('check_outcome') not in ACTIONABLE or proposal.get('proposal_outcome') not in ACTIONABLE:
        raise ValueError('Proposal has no resolved actionable provenance; recheck and regenerate it')
    binding = proposal.get('source_binding')
    _verify_sources(binding, verify_sources, proposal['workspace'])
    snapshot, hashes = _bound(proposal)
    name, content = _edit(snapshot, proposal['choice'], proposal['edits'])
    root = Path(proposal['workspace'])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError('Workspace must be absolute and contain no symlinks')
    # Re-snapshot also rejects added inputs, which may change the model's conclusion.
    _, current, skipped = _snapshot(root)
    if skipped:
        raise ValueError('Workspace is not fully readable since proposal')
    if set(current) != set(snapshot):
        raise ValueError('Workspace inputs changed since proposal')
    already = current[name] == content
    for path, text in current.items():
        expected = content if already and path == name else snapshot[path]
        if text != expected:
            raise ValueError('Workspace input changed since proposal: ' + path)
    target = _path(root, name)
    before, after = hashes[name], _digest(content)
    if not already:
        mode = stat.S_IMODE(target.stat().st_mode)
        fd, temporary = tempfile.mkstemp(prefix='.plumb-', dir=target.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content.encode('utf-8'))
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, mode)
            for path, text in snapshot.items():
                if _read(root, path) != text:
                    raise ValueError('Workspace input changed during apply: ' + path)
            # shortcut: local ref checks cannot lock Git; add conditional writes before shared-workspace use.
            _verify_sources(binding, verify_sources, root)
            _path(root, name)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    receipt = {'proposal_id': ident, 'choice': proposal['choice'], 'workspace': str(root), 'path': name,
            'before': before, 'after': after, 'status': 'already_applied' if already else 'applied',
            'scope': 'captured_workspace', 'upstream_freshness': 'not_checked'}
    if binding is not None:
        receipt.update(source_binding=copy.deepcopy(binding), upstream_freshness='version_checked',
                       source_scope=binding.get('scope', 'connected_source'))
    return receipt
