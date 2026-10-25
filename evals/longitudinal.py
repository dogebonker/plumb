"""Consecutive prepared PR trials, retaining each arm's own previous implementation."""
import argparse
import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from itertools import pairwise
from pathlib import Path

import pr_benchmark
import quality_report

DIMENSIONS = ('delivery', 'correctness', 'architecture', 'history', 'rule_compliance')
# What `git init` and the fixture setup write; host Git overrides the signing and hook keys anyway.
SAFE_CONFIG = {'core.repositoryformatversion', 'core.filemode', 'core.bare', 'core.logallrefupdates',
               'core.ignorecase', 'core.precomposeunicode', 'core.symlinks', 'core.hookspath',
               'extensions.objectformat', 'user.name', 'user.email', 'user.signingkey',
               'commit.gpgsign', 'tag.gpgsign'}


def validate_chain(manifest):
    cases = manifest.get('cases', [])
    if len(cases) < 2 or not manifest.get('shared_context', '').strip():
        raise ValueError('at least two cases and common standing decisions/policies/history required')
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('unique case IDs required')
    for previous, current in pairwise(cases):
        if previous['reference_commit'] != current['base_commit']:
            raise ValueError('historical PR reference/base commits must be consecutive')
    for case in cases:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', case['id']):
            raise ValueError('case IDs must be safe directory names')
        if any(not re.fullmatch(r'[a-f0-9]{40}', case.get(key, '')) for key in ('base_commit', 'reference_commit')):
            raise ValueError('full historical commit bindings required')
        if not case.get('pr', {}).get('title'):
            raise ValueError('real PR requirements required')
    return cases


def scores(result):
    return {'delivery': 'pass' if result.get('status') == 'complete' else 'fail',
            'correctness': ('pass' if result.get('tests', {}).get('status') == 'pass' else
                            'fail' if result.get('tests', {}).get('status') in {'fail', 'assertion_failure', 'candidate_error'} else 'unmeasured'),
            'architecture': 'unmeasured', 'history': 'unmeasured', 'rule_compliance': 'unmeasured'}


def _git(work, *args):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                             '-c', 'commit.gpgsign=false', '-c', 'core.attributesFile=/dev/null',
                             '-c', 'user.name=Benchmark handoff',
                             '-c', 'user.email=benchmark-handoff@localhost', '-C', str(work), *args],
                            env=env, capture_output=True, text=True, timeout=120, check=False)
    if result.returncode:
        raise ValueError('host workspace Git command failed: ' + result.stderr.strip())
    return result.stdout.rstrip('\n')


def _audit_metadata(metadata):
    """Reject actor-controlled redirects and command filters before invoking Git."""
    for path in metadata.rglob('*'):
        info = path.lstat()
        if (stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))
                or stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
            raise ValueError('unsafe workspace Git metadata link/type: ' + str(path.relative_to(metadata)))
    redirects = ('commondir', 'gitdir', 'config.worktree', 'worktrees', 'modules',
                 'objects/info/alternates', 'objects/info/http-alternates')
    if any((metadata / name).exists() for name in redirects) or any(metadata.rglob('*.promisor')):
        raise ValueError('workspace Git metadata redirect is not supported for host savepoints')
    config = metadata / 'config'
    if not config.is_file():
        raise ValueError('workspace Git metadata config missing')
    # Git parses the file itself (a regex misses syntax Git accepts, such as a leading BOM); --file never follows includes.
    # Allowlist, not denylist: new Git releases add command keys (hook.<name>.command in 2.54).
    keys = [entry.split('\n', 1)[0] for entry in
            _git(Path('/'), 'config', '--file', str(config), '--null', '--list').split('\0') if entry]
    unsupported = sorted({key for key in keys if key not in SAFE_CONFIG and not key.startswith('branch.')})
    if unsupported:
        raise ValueError('unsupported workspace Git configuration for host savepoints: ' + ', '.join(unsupported))


def _workspace_root(work):
    work = Path(work)
    if work.is_symlink():
        raise ValueError('host savepoint requires the exact workspace Git root')
    work = work.resolve()
    metadata = work / '.git'
    if not metadata.is_dir() or metadata.is_symlink():
        raise ValueError('host savepoint requires private workspace Git metadata')
    _audit_metadata(metadata)
    if (Path(_git(work, 'rev-parse', '--show-toplevel')).resolve() != work
            or Path(_git(work, 'rev-parse', '--absolute-git-dir')).resolve() != metadata
            or Path(_git(work, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve() != metadata):
        raise ValueError('host savepoint requires the exact workspace Git root and private metadata')
    return work


def _dirty_paths(work):
    return sorted(row[3:] for row in _git(work, 'status', '--porcelain=v1', '-z',
                                        '--untracked-files=all', '--no-renames', '--ignore-submodules=all').split('\0') if row)


def host_savepoint(work, *, phase, paths=None):
    """Local candidate/overlay provenance only; never approval or actor completion proof."""
    if phase not in ('candidate', 'acceptance_overlay') or (phase == 'candidate' and paths is not None):
        raise ValueError('invalid host handoff phase/path scope')
    work = _workspace_root(work)
    changed = _dirty_paths(work)
    allowed = {str(pr_benchmark.pr_fixtures._relative(path)) for path in paths or []}
    if phase == 'acceptance_overlay' and not set(changed) <= allowed:
        raise ValueError('dirty files outside approved acceptance overlay; candidate preserved')
    before = pr_benchmark.pr_fixtures.snapshot_hash(work)
    previous = _git(work, 'rev-parse', 'HEAD')
    if changed:
        stage = sorted(allowed) if phase == 'acceptance_overlay' else ['.']
        _git(work, 'add', '--all', '--', *stage)
        _git(work, 'commit', '-m', 'Benchmark host ' + phase + ' savepoint')
    commit = _git(work, 'rev-parse', 'HEAD')
    if _dirty_paths(work) or pr_benchmark.pr_fixtures.snapshot_hash(work) != before:
        raise ValueError('host savepoint did not preserve a clean candidate snapshot')
    committed = _git(work, 'diff', '--no-ext-diff', '--no-textconv', '--name-only', '-z', previous, commit).split('\0')
    committed = sorted(path for path in committed if path)
    if phase == 'acceptance_overlay' and not set(committed) <= allowed:
        raise ValueError('host overlay commit escaped approved acceptance paths')
    return {'phase': phase, 'previous_commit': previous, 'commit': commit, 'created': commit != previous,
            'changed_files': committed, 'source_sha256': before,
            'authority': 'host local Git provenance; not approval or native actor completion proof'}


def _replace_overlay(target, data):
    """Replace the directory entry rather than writing through an existing inode."""
    mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.benchmark-overlay-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            os.fchmod(stream.fileno(), mode)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)


def run(manifest, config, output, *, trial_fn=pr_benchmark.trial, score_fn=None):
    """score_fn(case,result,workspace) may provide measured verdicts plus evidence.

    A host scorer must validate semantic history reuse with a fresh actor and source
    citations; this harness never infers quality from history-file existence.
    """
    cases = validate_chain(manifest)
    output = Path(output).resolve()
    # Later acceptance files stay hidden from every earlier step.
    overlay_roots = {Path(item['source']).resolve().parent for case in cases for item in case.get('acceptance_overlays', [])}
    # Actor runtimes, the framework and every tree trials copy into a workspace.
    public = [output.parent / (output.name + '-actors'), *([Path(config['snapshot']).resolve()] if config.get('snapshot') else []),
              *(Path(case['prepared_dir']).resolve() / 'actor' for case in cases),
              *(Path(source).resolve() for case in cases for source in case.get('dependency_dirs', {}).values())]
    if any(root == path or root in path.parents or path in root.parents for root in overlay_roots for path in public):
        raise ValueError('acceptance overlay root overlaps actor/framework; use isolated corpus storage')
    private_roots = sorted({*config.get('private_input_roots', []), *map(str, overlay_roots)})
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError('use an empty persistent output directory')
    report = {'schema': 1, 'scope': 'consecutive feature maintenance; not production deployment',
              'shared_context_sha256': hashlib.sha256(manifest['shared_context'].encode()).hexdigest(),
              'manifest_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
              'config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
              'sources': {name: pr_benchmark.sha(Path(__file__).with_name(name))
                          for name in ('longitudinal.py', 'pr_benchmark.py', 'benchmark.py', 'quality_report.py')},
              'arms': {}, 'failure_policy': 'halt that arm; later steps inherit failure, never restore historical reference'}
    # Manifest/reference metadata remains outside the actor roots; only public facts enter prompts.
    pr_benchmark.write(output / 'manifest.json', manifest)
    for arm in pr_benchmark.ARMS:
        rows, halted, sessions = [], False, set()
        runtime = output.parent / (output.name + '-actors') / arm
        if runtime.exists():
            raise FileExistsError(f'actor workspace already exists: {runtime}')
        for index, original in enumerate(cases):
            if halted:
                rows.append({'case': original['id'], 'status': 'not_run_inherited_failure',
                             'scores': {key: 'not_run_inherited_failure' for key in DIMENSIONS}})
                continue
            case = copy.deepcopy(original)
            handoff = {}
            case['pr']['body'] = (case['pr'].get('body') or '') + '\n\nSHARED STANDING DECISIONS, POLICIES AND HISTORICAL FACTS:\n' + manifest['shared_context']
            if index:
                case['pr']['body'] += ('\nThis follows your arm\'s previous implementation in this workspace. '
                                       'Read retained project decisions/history before extending it. Preserve those decisions. '
                                       'Do not replace the workspace with a historical reference.')
                # Approved acceptance changes only: immutable overlays from admitted preparation.
                allowed = {str(p) for p in pr_benchmark.pr_fixtures.acceptance_paths(case) + pr_benchmark.pr_fixtures.support_paths(case)}
                overlays = case.get('acceptance_overlays', [])
                if case.get('provide_acceptance') and {item['path'] for item in overlays} != allowed:
                    raise ValueError('every later immutable acceptance/support file requires a pinned overlay')
                work = _workspace_root(runtime / 'work')
                if _dirty_paths(work):
                    raise ValueError('retained candidate changed after its host savepoint; next trial held')
                replacements = []
                for overlay in overlays:
                    if overlay['path'] not in allowed:
                        raise ValueError('only admitted immutable acceptance/support paths may be overlaid')
                    source = Path(overlay['source'])
                    relative = Path(overlay['path'])
                    if relative.is_absolute() or '..' in relative.parts:
                        raise ValueError('acceptance overlay path must stay inside actor workspace')
                    data = source.read_bytes()
                    if hashlib.sha256(data).hexdigest() != overlay['sha256']:
                        raise ValueError('acceptance overlay binding changed')
                    target = work / relative
                    pr_benchmark.pr_fixtures._inside(work, target)
                    if target.is_symlink() or any(p.is_symlink() for p in target.parents):
                        raise ValueError('symlink overlay destination denied')
                    if target.exists():
                        info = target.lstat()
                        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                            raise ValueError('hardlinked or nonregular overlay destination denied; next trial held')
                    replacements.append((target, data))
                for target, data in replacements:
                    _replace_overlay(target, data)
                handoff['acceptance_overlay'] = host_savepoint(work, phase='acceptance_overlay', paths=sorted(allowed))
            entry = {'arm': arm, 'runtime': str(runtime)}
            step_out = output / f'step-{index + 1}'
            step_out.mkdir(exist_ok=True)
            step_config = {**config, 'source_repositories': [*config.get('source_repositories', []), str(output)],
                           'private_input_roots': private_roots,
                           'schedule': [{'arm': a, 'runtime': str(output.parent / (output.name + '-actors') / a)} for a in pr_benchmark.ARMS]}
            result = trial_fn(step_config, case, entry, step_out)
            if result.get('status') == 'complete':
                session = result.get('session')
                if not session or session in sessions:
                    result = {**result, 'status': 'fresh_session_unverified'}
                else:
                    sessions.add(session)
            measured = scores(result)
            judgments = score_fn(case, result, runtime / 'work') if score_fn else {}
            for dimension, judgment in judgments.items():
                if dimension not in DIMENSIONS or judgment.get('verdict') not in {'pass', 'fail', 'unmeasured'}:
                    raise ValueError('invalid scoring dimension/verdict')
                if judgment['verdict'] != 'unmeasured' and not judgment.get('evidence'):
                    raise ValueError('measured score requires semantic/mechanical evidence')
                measured[dimension] = judgment['verdict']
            halted = result['status'] != 'complete' or measured['correctness'] != 'pass' or any(v == 'fail' for v in measured.values())
            if not halted:
                handoff['candidate_savepoint'] = host_savepoint(runtime / 'work', phase='candidate')
            cost = quality_report.costs(result)
            rows.append({'case': case['id'], 'status': result['status'], 'result': result,
                         'scores': measured, 'judgments': judgments, 'host_handoff': handoff,
                         'tokens': cost['task']['tokens'], 'cost_usd': cost['task']['native_usd'],
                         'seconds': cost['task']['seconds'], 'costs': cost,
                         'probe_usage': {'tokens': cost['probe']['tokens'], 'cost_usd': cost['probe']['native_usd']},
                         'probe_seconds': cost['probe']['seconds']})
            report['arms'][arm] = rows
            pr_benchmark.write(output / 'report.json', report)
        report['arms'][arm] = rows
    pr_benchmark.write(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--execute', action='store_true', help='Invoke paid actors with prepared benchmark settings')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validate_chain(manifest)
    if not args.execute:
        print(json.dumps({'valid': True, 'steps': len(manifest['cases']), 'execution': 'not requested'}))
        return
    if not args.config or not args.out:
        parser.error('--execute requires --config and --out')
    config = json.loads(args.config.read_text())
    # Reuse normal admission, verification pins and acceptance validation before model spend.
    pr_benchmark.manifest_cases(args.manifest)
    report = run(manifest, config, args.out)
    print(json.dumps({'report': str(args.out / 'report.json'), 'arms': list(report['arms'])}))


if __name__ == '__main__':
    main()
