"""Calibrate real merged-PR tasks before any model outcome is observed."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from pr_benchmark import isolated_grader
from pr_fixtures import (
    _expected_feature_failure,
    _missing_module_reports,
    _module_aliases,
    _reported_test,
    admit_case,
    expected_feature_matches,
    is_test_support,
)


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                                   text=True).strip()


def make_case(source, pr):
    repo, reference = source['repo'], pr['mergeCommit']['oid']
    base = git(repo, 'rev-parse', reference + '^1')
    prefix = source.get('source_subdir', '').strip('/')
    prefix = prefix + '/' if prefix else ''
    changed = [f['path'][len(prefix):] for f in pr['files'] if f['path'].startswith(prefix)]
    kind = source['kind']
    if kind == 'go':
        tests = [p for p in changed if p.endswith('_test.go') and 'integration' not in p and 'e2e' not in p]
        names = set()
        for path in tests:
            text = git(repo, 'show', reference + ':' + prefix + path)
            names.update(re.findall(r'^func (Test\w+)\(t \*testing\.T\)', text, re.MULTILINE))
        packages = sorted({'./' + str(Path(p).parent) for p in tests})
        if not names:
            raise ValueError('no offline Go feature-test functions')
        command = ['go', 'test', '-v', '-count=1', '-run', '^(' + '|'.join(sorted(names)) + ')$', *packages]
    elif kind == 'jest':
        tests = [p for p in changed if p.endswith('.spec.ts') and not p.startswith('test/integration/')]
        cache = source['node_modules']
        command = [sys.executable, source['node_adapter'], '--cache', cache, '--runner', 'jest',
                   *(['--typechain'] if source.get('typechain') else []), '--', '--runInBand', '--runTestsByPath', *tests]
    else:
        tests = [p for p in changed if p.endswith(('.test.ts', '.test.tsx'))]
        command = [sys.executable, source['node_adapter'], '--cache', source['node_modules'],
                   '--runner', 'vp', '--', *tests]
    if not tests:
        raise ValueError('no held-out unit-test files')
    language = 'go' if kind == 'go' else 'typescript'
    command_text = ' '.join(command)
    context = source['claude_md'].strip() + '\n\n## Verification\n' + command_text + '\n'
    case = {
        'id': f"{source['id']}-{pr['number']}", 'repo': repo,
        'base_commit': base, 'reference_commit': reference,
        'source_subdir': source.get('source_subdir'),
        'pr': {k: pr[k] for k in ('number', 'title', 'body', 'url', 'mergedAt')},
        'requirements': pr['title'] + '\n\n' + pr['body'],
        'claude_md': context, 'claude_md_sha256': hashlib.sha256(context.encode()).hexdigest(),
        'provide_acceptance': True, 'acceptance_files': tests, 'acceptance_support_files': [p for p in changed if p not in tests and is_test_support(p)],
        'test_command': command,
        'test_env': source.get('test_env', {}), 'runtime_env': source.get('runtime_env', {}),
        'archgraph_root': '.', 'archgraph_language': language,
        'scope': 'Offline unit behavior of the historical feature PR; integration checks are excluded explicitly.',
    }
    if source.get('node_adapter'):
        path = source['node_adapter']
        case['verification_files'] = [{'path': path, 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}]
    return case


def _go_declarations(text, symbol, diagnostic, owner=None):
    name = re.escape(symbol)
    if diagnostic == 'field':
        structs = re.finditer(r'\btype\s+(\w+)\s+struct\s*\{([^}]+)\}', text, re.DOTALL)
        declarations = []
        for match in structs:
            if owner and match[1] != owner:
                continue
            declarations.extend(match[1] + ':' + field[0] for field in
                                re.finditer(r'^\s*' + name + r'\s+[^\n]+', match[2], re.MULTILINE))
    else:
        function = r'^func\s+(?:\([^)]*\)\s*)?' + name + r'\s*(?:\[[^]]*\]\s*)?\([^{}]*?\)[^{]*\{'
        declarations = [match[0] for match in re.finditer(function, text, re.MULTILINE)]
        if diagnostic == 'undefined':
            declarations.extend(match[0] for match in re.finditer(
                r'^(?:type|var|const)\s+' + name + r'\b[^\n]*', text, re.MULTILINE))
    return {' '.join(declaration.split()) for declaration in declarations}


def go_feature_failure(case, pr, result):
    """Recognize exact missing Go APIs only when the PR changes their production declaration."""
    baseline = result['baseline']
    if (baseline['status'] not in {'setup_error', 'expected_feature_failure'}
            or result['reference_result']['status'] != 'pass'):
        return None
    output = baseline.get('output', '')
    if re.search(r'no required module provides|cannot find (?:module|package|GOROOT)|missing go.sum|'
                 r'failed to download|requires go >=|toolchain not available|command not found|'
                 r'module lookup disabled|no matching versions|is not in std|errors parsing go.mod|'
                 r'cannot find module providing|missing module for import|GOPROXY=off|'
                 r'No such file or directory|syntax error|could not import|imported and not used|'
                 r'undefined reference|pkg-config|ModuleNotFoundError', output, re.IGNORECASE):
        return None
    diagnostics = []
    for line in output.splitlines():
        field = re.search(r'type \*?(?:[\w]+\.)?(\w+) has no field or method (\w+)', line)
        arity = re.search(r'(?:too many|not enough) arguments in call to (?:\w+\.)?(\w+)', line)
        undefined = re.search(r'undefined: ([A-Za-z_]\w*)\b', line)
        if field:
            diagnostics.append(('field', field[2], field[0], field[1]))
        elif arity:
            diagnostics.append(('arity', arity[1], arity[0], None))
        elif undefined:
            diagnostics.append(('undefined', undefined[1], undefined[0], None))
    prefix = case.get('source_subdir') or ''
    prefix = prefix.rstrip('/') + '/' if prefix else ''
    for diagnostic, symbol, message, owner in diagnostics:
        for item in pr['files']:
            path = item['path']
            if not path.startswith(prefix) or not path.endswith('.go') or path.endswith('_test.go'):
                continue
            if re.search(r'(?:^|[/_.-])(?:tests?|testdata|mocks?|fixtures?|testhelpers?|testutils?)(?:[/_.-]|$)', path, re.IGNORECASE):
                continue
            reference = git(case['repo'], 'show', case['reference_commit'] + ':' + path)
            declarations = _go_declarations(reference, symbol, diagnostic, owner)
            if not declarations:
                continue
            old = subprocess.run(['git', '-C', case['repo'], 'show', case['base_commit'] + ':' + path],
                                 capture_output=True, text=True, check=False)
            if getattr(old, 'returncode', 0) and not re.search(
                    r'does not exist in|exists on disk, but not in', getattr(old, 'stderr', '')):
                continue
            previous = _go_declarations(old.stdout, symbol, diagnostic, owner)
            if declarations == previous or (diagnostic == 'undefined' and previous):
                continue
            expected = {'pattern': re.escape(message), 'symbol': symbol, 'reference_file': path[len(prefix):]}
            _expected_feature_failure({**case, 'expected_feature_failure': expected}, result['reference'])
            return expected
    return None


def module_feature_failure(case, pr, result):
    """Calibrate a missing relative module only against a genuinely new PR production file."""
    baseline = result['baseline']
    if (baseline['status'] not in {'setup_error', 'expected_feature_failure'}
            or result['reference_result']['status'] != 'pass'):
        return None
    reference = Path(result['reference'])
    actor = Path(result.get('actor', reference.parent / 'actor'))
    prefix = case.get('source_subdir') or ''
    prefix = prefix.rstrip('/') + '/' if prefix else ''
    production = {item['path'][len(prefix):] for item in pr['files'] if item['path'].startswith(prefix)
                  and not re.search(r'(?:^|[/_.-])(?:tests?|testdata|mocks?|fixtures?|testhelpers?|testutils?)(?:[/_.-]|$)', item['path'], re.IGNORECASE)}
    for report in _missing_module_reports(baseline.get('output', '')):
        module, reported_importer = report[1], _reported_test(case, report[2])
        if not module.startswith(('./', '../')):
            continue
        for importer in case['acceptance_files']:
            if reported_importer != importer:
                continue
            target = reference / Path(importer).parent / module
            candidates = [target, *(Path(str(target) + suffix) for suffix in ('.ts', '.tsx', '.js')),
                          *(target / ('index' + suffix) for suffix in ('.ts', '.tsx', '.js'))]
            for candidate in candidates:
                try:
                    relative = candidate.resolve().relative_to(reference.resolve()).as_posix()
                except (ValueError, RuntimeError):
                    continue
                if relative not in production or not candidate.is_file() or candidate.is_symlink():
                    continue
                exported = re.findall(r'\bexport\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+([A-Za-z_]\w{2,})\b', candidate.read_text())
                for symbol in exported:
                    quote = report[0][len('Cannot find module ')]
                    expected = {'pattern': re.escape(f'Cannot find module {quote}{module}{quote}'),
                                'symbol': symbol, 'reference_file': relative,
                                'missing_module': module, 'importing_test': importer,
                                'module_aliases': _module_aliases(reference, actor, Path(relative))}
                    declared = {**case, 'expected_feature_failure': expected}
                    try:
                        if expected_feature_matches(declared, reference, actor, baseline['output']):
                            return expected
                    except ValueError:
                        continue
    return None


def prepare(catalog, out, target=24, timeout=300):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    selected, excluded, queues = [], [], []
    for source in catalog['sources']:
        rows = json.loads(Path(source['metadata']).read_text())
        by_number = {r['number']: r for r in rows}
        queues.append((source, list(source['pr_numbers']), by_number))
    # Round-robin admission is fixed before agent results; infrastructure failures stay in the audit.
    while any(numbers for _, numbers, _ in queues) and len(selected) < target:
        for source, numbers, by_number in queues:
            if not numbers or len(selected) >= target:
                continue
            number = numbers.pop(0)
            case_id = f"{source['id']}-{number}"
            destination = out / 'cases' / case_id
            try:
                pr = by_number[number]
                case = make_case(source, pr)
                if destination.exists():
                    recorded = json.loads((destination / 'case.json').read_text())
                    expected = recorded.get('expected_feature_failure')
                    comparable = {k: v for k, v in recorded.items() if k != 'expected_feature_failure'}
                    if comparable != case:
                        raise ValueError('candidate inputs changed since calibration')
                    result = json.loads((destination / 'admission.json').read_text())
                    if expected:
                        case['expected_feature_failure'] = expected
                        _expected_feature_failure(case, destination / 'reference', destination / 'actor')
                        classifier = module_feature_failure if expected.get('missing_module') else go_feature_failure
                        if classifier(case, pr, result) != expected:
                            raise ValueError('recorded feature-failure declaration no longer validates')
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    artifact = out / 'calibration' / case_id / 'run'
                    artifact.mkdir(parents=True, exist_ok=True)
                    config = {'source_repositories': [s['repo'] for s in catalog['sources']], 'schedule': []}
                    runner = isolated_grader(config, {**case, 'prepared_dir': str(destination)}, artifact, {}, calibration=True)
                    result = admit_case(case, destination, timeout, runner=runner)
                    classifier = go_feature_failure if source.get('kind') == 'go' else module_feature_failure
                    expected = classifier(case, pr, result)
                    if expected:
                        case['expected_feature_failure'] = expected
                        result['baseline']['status'] = 'expected_feature_failure'
                        result['admitted'] = True
                    (destination / 'case.json').write_text(json.dumps(case, indent=2) + '\n')
                    result = {k: str(v) if isinstance(v, Path) else v for k, v in result.items()}
                    (destination / 'admission.json').write_text(json.dumps(result, indent=2) + '\n')
                if result['admitted']:
                    selected.append({**case, 'prepared_dir': str(destination)})
                    print(f"ADMIT {case_id}: baseline feature failure; actual PR tests pass", flush=True)
                else:
                    excluded.append({'id': case_id, 'reason': 'calibration failed',
                                     'baseline': result['baseline']['status'],
                                     'reference': result['reference_result']['status'],
                                     'evidence': str(destination / 'admission.json')})
                    print(f"EXCLUDE {case_id}: {result['baseline']['status']} / {result['reference_result']['status']}", flush=True)
            except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
                excluded.append({'id': case_id, 'reason': str(error)})
                print(f'EXCLUDE {case_id}: {error}', flush=True)
            audit = {'target': target, 'selected': [c['id'] for c in selected], 'excluded': excluded}
            (out / 'admission-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
            manifest = {'schema': 1, 'target': target, 'quality_only': True,
                        'minimum_quality_margin_pp': 10, 'cases': selected}
            (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'selected': len(selected), 'target': target, 'excluded': len(excluded),
            'manifest': str(out / 'manifest.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--target', type=int, default=24)
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if not 20 <= args.target <= 30:
        parser.error('the real-feature benchmark requires 20–30 tasks')
    result = prepare(json.loads(args.catalog.read_text()), args.out, args.target, args.timeout)
    print(json.dumps(result))
    return 0 if result['selected'] == args.target else 2


if __name__ == '__main__':
    raise SystemExit(main())
