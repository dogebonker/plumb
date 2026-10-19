"""Factory v2 contracts. Files ending in .yaml contain strict JSON (a YAML subset).

Validation is structural, not approval authority. Review bindings compare exactly;
callers must also compare gate_evidence_sha256 to their actual evidence digest.
"""
import hashlib
import json
import math
import re
import stat
from pathlib import Path
from unicodedata import normalize

CONTROL_DIRS = {'.git', '.claude', '.software-factory', '.factory'}
CONTROL_FILES = {'AGENTS.md', 'CLAUDE.md', 'DESIGN.md', 'factory.yaml', 'factory.json'}


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    def constant(value):
        raise ValueError(f'nonfinite JSON number: {value}')
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f'nonfinite JSON number: {value}')
        return result
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)


def exact(value, required, optional=''):
    if not isinstance(value, dict) or not set(required.split()) <= value.keys() or value.keys() - set((required + ' ' + optional).split()):
        raise ValueError(f'expected fields: {required}; optional: {optional}')


def string(value):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('expected nonempty string without control characters')
    return value


def slug(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:[-_][a-z0-9]+)*', value):
        raise ValueError('expected safe slug')
    return value


def array(value):
    if not isinstance(value, list):
        raise ValueError('expected array')  # noqa: TRY004 - contract validation uses ValueError
    return value


def strings(value):
    values = [string(x) for x in array(value)]
    if len(set(values)) != len(values):
        raise ValueError('duplicate values')
    return values


def integer(value, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(f'expected integer >= {minimum}')


def number(value):
    if type(value) not in (int, float) or type(value) is float and not math.isfinite(value):
        raise ValueError('expected finite number')


def sha(value, length=64):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{' + str(length) + '}', value):
        raise ValueError('invalid digest')


def relative_path(value, directory=False, controls=False):
    string(value)
    if value != normalize('NFC', value):
        raise ValueError(f'path must use NFC Unicode spelling: {value}')
    path = value[:-1] if directory and value.endswith('/') else value
    if (not path or path.startswith('/') or any(c in path for c in '\\*?')
            or any(part in ('', '.', '..') for part in path.split('/'))):
        raise ValueError(f'unsafe relative path: {value}')
    parts = path.split('/')
    if not controls and (any(p.casefold() in CONTROL_DIRS for p in parts)
                         or parts[0].casefold() in {x.casefold() for x in CONTROL_FILES}):
        raise ValueError(f'control path: {value}')
    return value


def overlaps(a, b):
    a, b = normalize('NFC', a).casefold(), normalize('NFC', b).casefold()
    return a == b or a.endswith('/') and b.startswith(a) or b.endswith('/') and a.startswith(b)


def covered(path, scopes):
    return any(path == scope or scope.endswith('/') and path.startswith(scope) for scope in scopes)


def checked_path(root, value):
    """Check existing ancestors without following links, including case aliases."""
    root = Path(root)
    if str(root) != normalize('NFC', str(root)):
        raise ValueError('root must use NFC Unicode spelling')
    if value:
        relative_path(value, directory=True, controls=True)
    if not root.is_absolute() or root != Path(str(root)) or '..' in root.parts:
        raise ValueError('root must be an absolute lexical path')
    current = Path(root.anchor)
    for part in (*root.parts[1:], *value.rstrip('/').split('/')):
        matches = []
        if current.exists():
            matches = [p.name for p in current.iterdir()
                       if normalize('NFC', p.name).casefold() == part.casefold()]
            if len(matches) > 1 or any(normalize('NFC', name) != part for name in matches):
                raise ValueError(f'case alias: {part}')
        # APFS may return NFD names even when the requested path is NFC.
        current /= matches[0] if matches else part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f'symlink path: {current}')
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            raise ValueError(f'hardlinked file: {current}')
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise ValueError(f'unsupported file type: {current}')
    return root / value.rstrip('/')


def digest(value):
    # allow_nan=False rejects nonfinite values even for inline fixtures.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def load_plan(path):
    path = Path(path).absolute()
    checked_path(Path(path.anchor), path.relative_to(path.anchor).as_posix())
    plan = strict_json(path.read_text())
    if isinstance(plan, dict) and isinstance(plan.get('slices'), list):
        slices = []
        for item in plan['slices']:
            if isinstance(item, str):
                relative_path(item, controls=True)
                if not item.endswith('.yaml'):
                    raise ValueError('slice manifests must end in .yaml')
                item = strict_json(checked_path(path.parent, item).read_text())
            slices.append(item)
        plan['slices'] = slices
    validate_plan(plan)
    return plan


def validate_plan(plan):
    exact(plan, 'schema_version change_id base_commit policy frozen_inputs budget slices', 'replan_budget')
    if type(plan['schema_version']) is not int or plan['schema_version'] != 1:
        raise ValueError('unsupported schema_version')
    slug(plan['change_id'])
    sha(plan['base_commit'], 40)
    policy = plan['policy']
    exact(policy, 'layout permitted_rule_ids gate_definitions', 'final_test_gate')
    exact(policy['layout'], 'path sha256')
    relative_path(policy['layout']['path'], controls=True)
    sha(policy['layout']['sha256'])
    permitted = strings(policy['permitted_rule_ids'])
    gates = {}
    for gate in array(policy['gate_definitions']):
        exact(gate, 'id kind argv timeout_seconds', 'outputs')
        ident = string(gate['id'])
        if ident in gates or gate['kind'] not in ('tests', 'typecheck', 'lint', 'nfr'):
            raise ValueError('duplicate gate ID or invalid gate kind')
        if not [string(x) for x in array(gate['argv'])]:
            raise ValueError('gate argv must not be empty')
        integer(gate['timeout_seconds'])
        for output in strings(gate.get('outputs', [])):
            relative_path(output, directory=True)
        gates[ident] = gate
    if 'final_test_gate' in policy:
        final_test = string(policy['final_test_gate'])
        if final_test not in gates or gates[final_test]['kind'] != 'tests':
            raise ValueError('final_test_gate must reference an approved test gate')
    frozen = []
    for entry in array(plan['frozen_inputs']):
        exact(entry, 'path sha256 kind')
        relative_path(entry['path'], controls=True)
        sha(entry['sha256'])
        string(entry['kind'])
        if any(overlaps(entry['path'], p) for p in frozen):
            raise ValueError('duplicate frozen input')
        frozen.append(entry['path'])
    for gate in gates.values():
        if any(overlaps(output, path) for output in gate.get('outputs', [])
               for path in [*frozen, policy['layout']['path']]):
            raise ValueError('gate output overlaps frozen input or layout')
    exact(plan['budget'], 'tokens seconds opus_share_limit')
    for key in ('tokens', 'seconds'):
        integer(plan['budget'][key])
    share = plan['budget']['opus_share_limit']
    number(share)
    if not 0 < share <= .25:
        raise ValueError('opus_share_limit must be > 0 and <= 0.25')
    if 'replan_budget' in plan:
        allocation = plan['replan_budget']
        exact(allocation, 'tokens seconds max_calls')
        for value in allocation.values():
            integer(value)
        if allocation['tokens'] > plan['budget']['tokens'] or allocation['seconds'] > plan['budget']['seconds']:
            raise ValueError('replan allocation must fit whole-feature budget')
    spellings = {}
    def register_path(path):
        prefix = ''
        for part in path.rstrip('/').split('/'):
            prefix += part + '/'
            alias = prefix.casefold()
            if alias in spellings and spellings[alias] != prefix:
                raise ValueError(f'case alias: {path}')
            spellings[alias] = prefix
    for path in [policy['layout']['path'], *frozen,
                 *(p for gate in gates.values() for p in gate.get('outputs', []))]:
        register_path(path)
    slices = {}
    for item in array(plan['slices']):
        exact(item, 'id kind depends_on owns reads interfaces fr rules budget gates', 'nfr')
        ident = slug(item['id'])
        if ident in slices or item['kind'] not in ('contract', 'feature'):
            raise ValueError('duplicate slice ID or invalid slice kind')
        slices[ident] = item
        strings(item['depends_on'])
        for key in ('owns', 'reads'):
            for path in strings(item[key]):
                relative_path(path, directory=True)
                register_path(path)
            for i, path in enumerate(item[key]):
                if any(overlaps(path, other) for other in item[key][i + 1:]):
                    raise ValueError(f'overlapping {key} paths')
        protected = [*frozen, policy['layout']['path']]
        if any(overlaps(p, f) for p in item['owns'] for f in protected):
            raise ValueError('ownership overlaps frozen input or layout')
        refs = strings(item['gates'])
        if policy.get('final_test_gate') in refs:
            raise ValueError('final integration gate cannot run in an isolated slice')
        if any(ref not in gates for ref in refs):
            raise ValueError('unknown gate reference')
        if not {'tests', 'typecheck', 'lint'} <= {gates[x]['kind'] for x in refs}:
            raise ValueError('each slice requires tests, typecheck and lint gates')
        exact(item['rules'], 'ids surfaces')
        if not set(strings(item['rules']['ids'])) <= set(permitted):
            raise ValueError('unknown rule ID')
        signatures = {}
        for surface in [*array(item['interfaces']), *array(item['rules']['surfaces'])]:
            exact(surface, 'path symbol signature')
            relative_path(surface['path'])
            register_path(surface['path'])
            string(surface['symbol'])
            string(surface['signature'])
            if not covered(surface['path'], item['owns']):
                raise ValueError('surface path must be owned by its slice')
            key = (surface['path'], surface['symbol'])
            if key in signatures and signatures[key] != surface['signature']:
                raise ValueError('conflicting surface signatures')
            signatures[key] = surface['signature']
        criteria = set()
        for fr in array(item['fr']):
            exact(fr, 'id given when then gate_id case_id')
            for value in fr.values():
                string(value)
            if fr['id'] in criteria or fr['gate_id'] not in refs or gates[fr['gate_id']]['kind'] != 'tests':
                raise ValueError('duplicate FR or invalid FR test gate')
            criteria.add(fr['id'])
        if item['fr'] and not any(x['kind'] == 'fr' for x in plan['frozen_inputs']):
            raise ValueError('FR scenarios require frozen_inputs of kind fr')
        for nfr in array(item.get('nfr', [])):
            exact(nfr, 'id gate_id threshold')
            string(nfr['id'])
            string(nfr['gate_id'])
            number(nfr['threshold'])
            if nfr['id'] in criteria or nfr['gate_id'] not in refs or gates[nfr['gate_id']]['kind'] != 'nfr':
                raise ValueError('duplicate criterion or invalid NFR gate')
            criteria.add(nfr['id'])
        exact(item['budget'], 'tokens retries review_passes review_tokens seconds')
        for key, value in item['budget'].items():
            integer(value, 0 if key == 'retries' else 1)
    contracts = [x for x in slices.values() if x['kind'] == 'contract']
    if len(contracts) != 1 or contracts[0]['depends_on']:
        raise ValueError('exactly one contract slice without dependencies required')
    ancestors = {}
    def visit(ident, visiting):
        if ident not in slices:
            raise ValueError(f'missing dependency: {ident}')
        if ident in visiting:
            raise ValueError('dependency cycle')
        if ident not in ancestors:
            ancestors[ident] = set()
            for dep in slices[ident]['depends_on']:
                ancestors[ident].add(dep)
                ancestors[ident].update(visit(dep, visiting | {ident}))
        return ancestors[ident]
    for ident, item in slices.items():
        if item['kind'] == 'feature' and contracts[0]['id'] not in visit(ident, set()):
            raise ValueError('feature must transitively depend on contract')
        visit(ident, set())
    rows = list(slices.values())
    for i, left in enumerate(rows):
        for right in rows[i + 1:]:
            if any(overlaps(a, b) for a in left['owns'] for b in right['owns']):
                raise ValueError('overlapping ownership across slices')
            conflict = (any(overlaps(a, b) for a in left['owns'] for b in right['reads'])
                        or any(overlaps(a, b) for a in right['owns'] for b in left['reads']))
            if conflict and left['id'] not in ancestors[right['id']] and right['id'] not in ancestors[left['id']]:
                raise ValueError('read/write conflict requires dependency ordering')
    digest(plan)


def ready_slices(plan, accepted, running):
    validate_plan(plan)
    ids = {item['id'] for item in plan['slices']}
    if not isinstance(accepted, set) or not isinstance(running, set) or not (accepted | running) <= ids or accepted & running:
        raise ValueError('invalid accepted/running slice IDs')
    return [item['id'] for item in plan['slices'] if item['id'] not in accepted | running
            and set(item['depends_on']) <= accepted]


def validate_review(value, expected_binding):
    exact(value, 'binding gate_evidence_sha256 decision findings')
    if not isinstance(expected_binding, dict) or not isinstance(value['binding'], dict) or digest(value['binding']) != digest(expected_binding):
        raise ValueError('review binding mismatch')
    sha(value['gate_evidence_sha256'])
    if value['decision'] not in ('accept', 'reject', 'spec_defect'):
        raise ValueError('invalid review decision')
    findings = array(value['findings'])
    if value['decision'] != 'accept' and not findings:
        raise ValueError('reject/spec_defect requires findings')
    for finding in findings:
        exact(finding, 'criterion_id path message')
        integer(finding['criterion_id'])
        if finding['criterion_id'] > 3:
            raise ValueError('criterion_id must be 1..3')
        relative_path(finding['path'], controls=True)
        string(finding['message'])
