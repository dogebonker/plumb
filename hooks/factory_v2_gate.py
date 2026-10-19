#!/usr/bin/env python3
"""Fail-closed wildcard PreToolUse hook; invoke with --policy /trusted/outside.json.

The orchestrator supplies this policy outside the candidate worktree. This guards
model tool calls only, not OS execution or concurrent filesystem replacement.
"""
import argparse
import json
import sys
from pathlib import Path
from unicodedata import normalize

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
from v2_contract import (
    checked_path,
    covered,
    exact,
    overlaps,
    relative_path,
    slug,
    strict_json,
    string,
    strings,
    validate_review,
)


def validate_policy(policy):
    exact(policy, 'schema_version run_id slice_id root owns reads frozen')
    if type(policy['schema_version']) is not int or policy['schema_version'] != 1:
        raise ValueError('unsupported policy schema_version')
    slug(policy['run_id'])
    slug(policy['slice_id'])
    if not isinstance(policy['root'], str):
        raise TypeError('policy root must be absolute')
    root = Path(policy['root'])
    if not root.is_absolute() or str(root) != policy['root'] or '..' in root.parts:
        raise ValueError('policy root must be absolute and normalized')
    checked_path(root, '')
    if not root.is_dir():
        raise ValueError('policy root must exist')
    spellings = {}
    for field in ('owns', 'reads', 'frozen'):
        for path in strings(policy[field]):
            relative_path(path, directory=True, controls=field == 'frozen')
            prefix = ''
            for part in path.rstrip('/').split('/'):
                prefix += part + '/'
                if prefix.casefold() in spellings and spellings[prefix.casefold()] != prefix:
                    raise ValueError('case alias in policy scope')
                spellings[prefix.casefold()] = prefix
    return root


def write_problem(policy, tool_name, tool_input):
    """Return a denial reason for reads or writes; None permits this tool call."""
    try:
        root = validate_policy(policy)
        # Native --json-schema reports data through this tool; it performs no I/O.
        if tool_name == 'StructuredOutput':
            if isinstance(tool_input, dict) and 'state' in tool_input:
                exact(tool_input, 'state summary')
                if tool_input['state'] not in ('complete', 'blocked'):
                    raise ValueError('invalid worker state')
                string(tool_input['summary'])
            else:
                validate_review(tool_input, tool_input.get('binding') if isinstance(tool_input, dict) else None)
            return None
        fields = {
            'Read': ('file_path', {'offset', 'limit', 'pages'}),
            'Grep': ('path', {'pattern', 'glob', 'output_mode', '-B', '-A', '-C', '-n', '-i',
                              'type', 'head_limit', 'offset', 'multiline'}),
            'Glob': ('path', {'pattern'}),
            'Edit': ('file_path', {'old_string', 'new_string', 'replace_all'}),
            'Write': ('file_path', {'content'}),
        }
        if not isinstance(tool_name, str) or tool_name not in fields:
            raise ValueError('tool is not allowed')
        key, optional = fields[tool_name]
        exact(tool_input, key, ' '.join(optional))
        required = {'Grep': ('pattern',), 'Glob': ('pattern',),
                    'Edit': ('old_string', 'new_string'), 'Write': ('content',)}
        for field in required.get(tool_name, ()):
            if not isinstance(tool_input.get(field), str):
                raise TypeError(f'{tool_name} requires string {field}')
        for field, value in tool_input.items():
            if field in ('replace_all', '-n', '-i', 'multiline'):
                if type(value) is not bool:
                    raise ValueError(f'{field} must be boolean')
            elif field in ('offset', 'limit', '-B', '-A', '-C', 'head_limit'):
                if type(value) is not int or value < 0:
                    raise ValueError(f'{field} must be nonnegative integer')
            elif not isinstance(value, str):
                raise ValueError(f'{field} must be string')
        raw = tool_input[key]
        if not isinstance(raw, str):
            raise TypeError('missing tool path')
        path = Path(raw)
        if path.is_absolute():
            try:
                raw = path.relative_to(root).as_posix()
            except ValueError as exc:
                raise ValueError('tool path is outside root') from exc
        relative_path(raw, directory=True)
        relative = raw.rstrip('/')
        # Directory traversal through pattern fields is independent of the path.
        for field in ('glob', 'pattern') if tool_name == 'Glob' else ('glob',):
            if field in tool_input:
                pattern = tool_input[field]
                if (pattern.startswith('/') or '\\' in pattern
                        or any(part in ('.', '..') for part in pattern.split('/'))
                        or any(ord(c) < 32 or ord(c) == 127 for c in pattern)):
                    raise ValueError('unsafe search pattern')
        scopes = policy['owns'] if tool_name in ('Edit', 'Write') else policy['owns'] + policy['reads']
        target = checked_path(root, relative)
        scoped = relative + '/' if target.is_dir() or raw.endswith('/') else relative
        if not covered(scoped, scopes):
            raise ValueError('tool path is outside permitted scope')
        if tool_name in ('Edit', 'Write'):
            if target.is_dir():
                raise ValueError('mutation target must be a file')
            if any(overlaps(relative, frozen) for frozen in policy['frozen']):
                raise ValueError('mutation target is frozen')
        elif not target.exists():
            raise ValueError('read target does not exist')
        # Recursive search must not encounter links or protected nested trees.
        if tool_name in ('Grep', 'Glob') and target.is_dir():
            for entry in target.rglob('*'):
                rel = normalize('NFC', entry.relative_to(root).as_posix())
                relative_path(rel)
                checked_path(root, rel)
        return None
    except (ValueError, TypeError, OSError, OverflowError) as exc:
        return f'Factory v2 denied: {exc}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', required=True, type=Path)
    args = parser.parse_args()
    try:
        policy_path = args.policy
        if not policy_path.is_absolute():
            raise ValueError('policy path must be explicit and absolute')
        checked_path(Path(policy_path.anchor), policy_path.relative_to(policy_path.anchor).as_posix())
        policy = strict_json(policy_path.read_text())
        root = validate_policy(policy)
        if policy_path.is_relative_to(root):
            raise ValueError('trusted policy must be outside worktree')
        request = strict_json(sys.stdin.read())
        if not isinstance(request, dict) or not {'tool_name', 'tool_input'} <= request.keys():
            raise ValueError('malformed PreToolUse request')
        problem = write_problem(policy, request['tool_name'], request['tool_input'])
        if problem:
            raise ValueError(problem)
    except (ValueError, TypeError, OSError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow'}}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
