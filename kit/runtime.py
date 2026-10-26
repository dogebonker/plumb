"""Validate step routing evidence and run RED commands without moving the deliverable HEAD."""
import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                                    '-C', str(repo), *args], text=True).strip()


def validate_handoff(repo, report, slug, task_id, agent_id, slice_id, expected_state, completion=None):
    repo = Path(repo).resolve()
    # Parent supplies this envelope from the actual native return, never the child report.
    if not isinstance(completion, dict) or completion.get('task_id') != task_id or completion.get('agent_id') != agent_id:
        raise ValueError('observed native completion does not match dispatched task')
    if completion.get('state') != 'completed':
        raise ValueError('native step is still running or did not complete')
    if report.get('state') not in ('completed', 'question', 'blocked'):
        raise ValueError('step has not returned a terminal outcome')
    children = report.get('children')
    if not isinstance(children, list) or any(not isinstance(c, dict) or not c.get('id') or
                                          c.get('state') not in ('completed', 'question', 'blocked') for c in children):
        raise ValueError('child work is still running or lacks a terminal outcome')
    observed_children = completion.get('children')
    if not isinstance(observed_children, list) or any(not isinstance(c, dict) or not c.get('id') or
                                                   c.get('state') != 'completed' for c in observed_children):
        raise ValueError('native child completion has not been observed')
    if {c['id'] for c in children} != {c['id'] for c in observed_children}:
        raise ValueError('reported child list does not match observed native tasks')
    change = repo / '.plumb/changes' / slug
    if change.resolve().parent != (repo / '.plumb/changes').resolve():
        raise ValueError('invalid change slug')
    status = change / 'status.yaml'
    if report.get('status_sha256') != hashlib.sha256(status.read_bytes()).hexdigest():
        raise ValueError('handoff describes a different status.yaml snapshot')
    text = status.read_text()
    if report['state'] == 'completed':
        if any(c['state'] != 'completed' for c in children):
            raise ValueError('completed step has unresolved child questions or blockers')
        if git(repo, 'status', '--porcelain', '--', '.', ':!.plumb', ':!.factory', ':!.software-factory'):
            raise ValueError('completed step has dirty or untracked source')
        rows = re.findall(r'^\s*-\s*\{([^}\n]+)\}', text, re.MULTILINE)
        rows = [r for r in rows if re.search(r'\bid:\s*[\"\']?0*' + str(int(slice_id)) + r'\b', r)]
        if len(rows) != 1 or not re.search(r'\bstate:\s*' + re.escape(expected_state) + r'\b', rows[0]):
            raise ValueError('completed step has not written its expected slice state')
        if expected_state in ('green', 'done'):
            for name in ('test_commit', 'head_commit'):
                match = re.search(r'\b' + name + r':\s*([0-9a-f]{40})\b', rows[0])
                if not match:
                    raise ValueError('completed slice lacks a committed RED/GREEN checkpoint')
                git(repo, 'merge-base', '--is-ancestor', match[1], 'HEAD')
                if name == 'head_commit' and git(repo, 'diff', '--name-only', match[1], 'HEAD', '--', '.', ':!.plumb', ':!.factory', ':!.software-factory'):
                    raise ValueError('slice proof does not cover the current committed source')
    artifacts = report.get('artifacts')
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError('step must return exact artifact paths')
    paths = []
    for raw in artifacts:
        if not isinstance(raw, str):
            raise TypeError('artifact path must be text')
        path = Path(raw) if Path(raw).is_absolute() else repo / raw
        resolved = path.resolve()
        if not resolved.is_relative_to(change.resolve()) or not resolved.is_file() or path.is_symlink():
            raise ValueError(f'missing or out-of-change artifact: {raw}')
        paths.append(str(resolved))
    if report['state'] in ('question', 'blocked') and not report.get('question'):
        raise ValueError('question or blocker must include its complete text')
    return paths


def prepare_browser_red(repo, commit, checkpoint):
    repo = Path(repo).resolve()
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', checkpoint):
        raise ValueError('browser RED requires a full commit SHA and safe checkpoint slug')
    git(repo, 'rev-parse', '--verify', f'{commit}^{{commit}}')
    git(repo, 'merge-base', '--is-ancestor', commit, 'HEAD')
    request = repo / '.plumb/browser-red.json'
    if request.resolve() != request:
        raise ValueError('browser RED request must not be a symlink')
    request.parent.mkdir(parents=True, exist_ok=True)
    request.write_text(json.dumps({'commit': commit, 'checkpoint': checkpoint}, indent=2) + '\n')
    return request


def verify_red(repo, commit, command, checkpoint, timeout, tests_from=None, test_files=None):
    repo, checkpoint = Path(repo).resolve(), Path(checkpoint).resolve()
    if not checkpoint.is_relative_to(repo / '.plumb/changes'):
        raise ValueError('checkpoint must live under .plumb/changes')
    if command and Path(command[0]).name == 'browser-check':
        raise ValueError('fixed live browser wrapper cannot prove RED; run red_test_command directly')
    if (tests_from is None) != (test_files is None) or tests_from == '' or test_files == []:
        raise ValueError('tests-from and test-file must be supplied together')
    commit = git(repo, 'rev-parse', '--verify', f'{commit}^{{commit}}')
    git(repo, 'merge-base', '--is-ancestor', commit, 'HEAD')
    overlays, file_hashes = {}, {}
    if tests_from:
        tests_from = git(repo, 'rev-parse', '--verify', f'{tests_from}^{{commit}}')
        git(repo, 'merge-base', '--is-ancestor', tests_from, 'HEAD')
        for name in test_files:
            if (not isinstance(name, str) or not name or '\\' in name or '\x00' in name or
                    any(part in ('', '.', '..') or part.casefold() in ('.git', '.plumb', '.factory', '.software-factory')
                        for part in name.split('/'))):
                raise ValueError(f'test file must be an exact repository-relative path: {name}')
            blobs = []
            for revision in (commit, tests_from):
                entry = None
                parts = name.split('/')
                for i in range(1, len(parts) + 1):
                    prefix = '/'.join(parts[:i])
                    raw = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-z', revision,
                                                   '--', prefix]).decode().rstrip('\x00')
                    entry = raw.split('\t', 1) if raw else None
                    if entry and (len(entry) != 2 or entry[1] != prefix):
                        raise ValueError(f'ambiguous test path: {name}')
                    mode = entry[0].split()[0] if entry else None
                    if mode and mode not in (('040000',) if i < len(parts) else ('100644', '100755')):
                        raise ValueError(f'test path contains a non-regular file or ancestor: {name}')
                if not entry:
                    if revision == tests_from:
                        raise ValueError(f'test file is not committed in tests-from: {name}')
                    blobs.append(None)
                else:
                    blobs.append(subprocess.check_output(['git', '-C', str(repo), 'show', f'{revision}:{name}']))
            overlays[name] = (blobs[1], mode)
            file_hashes[name] = {'original_sha256': hashlib.sha256(blobs[0]).hexdigest() if blobs[0] is not None else None,
                                'corrected_sha256': hashlib.sha256(blobs[1]).hexdigest()}
    record = {'deliverable_head': git(repo, 'rev-parse', 'HEAD'),
              'deliverable_branch': git(repo, 'symbolic-ref', '--short', 'HEAD'),
              'test_commit': commit, 'base_commit': commit, 'command': command, 'state': 'started', 'exit_code': None}
    if tests_from:
        record.update(tests_commit=tests_from, test_files=file_hashes)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    scratch = repo / '.plumb/scratch'
    if scratch.resolve() != scratch:
        raise ValueError('verification scratch must not be a symlink')
    scratch.mkdir(parents=True, exist_ok=True)
    exclude = Path(git(repo, 'rev-parse', '--git-path', 'info/exclude'))
    if not exclude.is_absolute():
        exclude = repo / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    ignored = exclude.read_text() if exclude.exists() else ''
    if '/.plumb/scratch/' not in ignored.splitlines():
        exclude.write_text(ignored + '\n/.plumb/scratch/\n')
    with tempfile.TemporaryDirectory(prefix='plumb-red-', dir=scratch) as tmp:
        work = Path(tmp) / 'work'
        record['verification_clone'] = str(work)
        checkpoint.write_text(json.dumps(record, indent=2) + '\n')
        try:
            subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '-q', '--no-hardlinks',
                            '--no-checkout', str(repo), str(work)], check=True)
            git(work, 'remote', 'remove', 'origin')
            git(work, 'checkout', '-q', '--detach', commit)
            for name, (content, mode) in overlays.items():
                path = work / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                path.chmod(0o755 if mode == '100755' else 0o644)
            with checkpoint.with_suffix('.log').open('wb') as log:
                proc = subprocess.Popen(command, cwd=work, stdout=log, stderr=subprocess.STDOUT,
                                        start_new_session=True)
                try:
                    code = proc.wait(timeout=timeout)
                except BaseException:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                    raise
            record.update(state='finished', exit_code=code)
            return code
        except subprocess.TimeoutExpired:
            record['state'] = 'timeout'
            return None
        except BaseException:
            record['state'] = 'interrupted'
            raise
        finally:
            checkpoint.write_text(json.dumps(record, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    handoff = sub.add_parser('handoff')
    for name in ('repo', 'report', 'completion', 'slug', 'task-id', 'agent-id', 'slice', 'expected-state'):
        handoff.add_argument('--' + name, required=True)
    browser_red = sub.add_parser('browser-red-request')
    for name in ('repo', 'commit', 'checkpoint'):
        browser_red.add_argument('--' + name, required=True)
    red = sub.add_parser('red')
    red.add_argument('--repo', required=True)
    red.add_argument('--commit', required=True)
    red.add_argument('--checkpoint', required=True)
    red.add_argument('--timeout', type=int, default=3600)
    red.add_argument('--tests-from')
    red.add_argument('--test-file', action='append')
    red.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == 'handoff':
        paths = validate_handoff(args.repo, json.loads(Path(args.report).read_text()), args.slug,
                                 args.task_id, args.agent_id, args.slice, args.expected_state,
                                 json.loads(Path(args.completion).read_text()))
        print(json.dumps({'artifacts': paths}))
    elif args.action == 'browser-red-request':
        print(prepare_browser_red(args.repo, args.commit, args.checkpoint))
    else:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command:
            parser.error('red requires a command after --')
        result = verify_red(args.repo, args.commit, command, args.checkpoint, args.timeout,
                            args.tests_from, args.test_file)
        raise SystemExit(124 if result is None else result)


if __name__ == '__main__':
    main()
