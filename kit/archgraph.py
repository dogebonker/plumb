"""Pinned native Archgraph context and regression evidence, outside the source tree.

Paths supplied in --root, --rules and --files are repository-relative. Exit 0 means
prepared / gate passed, 1 means architectural regressions, 2 means skipped/error.
Native evidence orders reads; it never proves semantic or complete conformance.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

PIN = '49464a7ec19fe8402b4258e751f7ba050c6eff19'
INSTALL = f'cargo install --git https://github.com/dogebonker/archgraph --rev {PIN} --locked'
LIMIT = 16 * 1024 * 1024


class Unavailable(Exception):
    pass


def resolve_binary():
    supplied = os.environ.get('ARCHGRAPH_BIN')
    cargo = Path(os.environ.get('CARGO_HOME', Path.home() / '.cargo'))
    found = supplied or shutil.which('archgraph') or (str(cargo / 'bin/archgraph') if (cargo / 'bin/archgraph').is_file() else None)
    if not found:
        raise Unavailable('binary absent')
    binary = Path(found).resolve()
    if not binary.is_file():
        raise Unavailable('binary absent')
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    expected = os.environ.get('ARCHGRAPH_SHA256')
    if supplied:
        if not expected:
            raise Unavailable('explicit binary requires ARCHGRAPH_SHA256')
        if digest != expected:
            raise ValueError('ARCHGRAPH_SHA256 does not match supplied binary')
        provenance = 'caller-supplied hash; pinned build provenance not independently verified'
    else:
        receipt = Path(os.environ.get('CARGO_HOME', Path.home() / '.cargo')) / '.crates2.json'
        installs = json.loads(receipt.read_text()).get('installs', {}) if receipt.exists() else {}
        matches = [key for key, value in installs.items()
                   if f'git+https://github.com/dogebonker/archgraph?rev={PIN}#{PIN}' in key
                   and 'archgraph' in value.get('bins', [])]
        if len(matches) != 1 or (receipt.parent / 'bin/archgraph').resolve() != binary:
            raise Unavailable('PATH binary has no matching pinned Cargo installation receipt')
        provenance = matches[0]
    return {'binary': str(binary), 'binary_sha256': digest, 'source_pin': PIN,
            'provenance': provenance, 'install': INSTALL}


def run(argv, cwd, output, allowed=(0,)):
    """Bound command runtime and disk output; never invoke a shell or a daemon."""
    output = Path(output)
    stderr = output.with_suffix(output.suffix + '.stderr')
    with output.open('wb') as out, stderr.open('wb') as err:
        process = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + 120
            while process.poll() is None:
                if time.monotonic() > deadline or output.stat().st_size + stderr.stat().st_size > LIMIT:
                    raise ValueError('command exceeded 120 seconds or 16 MiB output limit')
                time.sleep(0.02)
            if output.stat().st_size + stderr.stat().st_size > LIMIT:
                raise ValueError('command exceeded 16 MiB output limit')
            if process.returncode not in allowed:
                raise ValueError(f'command exited {process.returncode}: {argv[1:3]}; see {stderr}')
            return process.returncode
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args], timeout=30, stderr=subprocess.PIPE)


def relative(repo, value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'expected repository-relative path: {value}')
    resolved = (repo / path).resolve()
    if not resolved.is_relative_to(repo):
        raise ValueError(f'path escapes repository: {value}')
    return resolved


def binding(repo):
    """Hash tracked and nonignored working files without executing repository code."""
    digest = hashlib.sha256()
    files = sorted(set(git(repo, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0')) - {b''})
    for name in files:
        path = repo / os.fsdecode(name)
        digest.update(name + b'\0')
        if path.is_symlink():
            digest.update(b'link:' + os.fsencode(os.readlink(path)))
        elif path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b'deleted')
        digest.update(b'\0')
    return {'commit': git(repo, 'rev-parse', 'HEAD').decode().strip(),
            'tree': git(repo, 'rev-parse', 'HEAD^{tree}').decode().strip(),
            'working_sha256': digest.hexdigest(),
            'dirty': bool(git(repo, 'status', '--porcelain', '--untracked-files=normal'))}


def document(path, required):
    if Path(path).stat().st_size > LIMIT:
        raise ValueError(f'native artifact exceeds 16 MiB: {path}')
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict) or any(not isinstance(value.get(key), list) for key in required):
        raise ValueError(f'unexpected native schema in {path}')
    return value


def execute(args):
    report = {'status': 'error', 'source_pin': PIN, 'install': INSTALL,
              'limitations': ['Native engine is experimental; evidence does not prove semantic conformance or complete import/symbol coverage.'],
              'artifacts': {}}
    out = None
    try:
        report['tool'] = resolve_binary()
        if args.command == 'doctor':
            report['status'] = 'available'
            print(json.dumps(report, indent=2))
            return 0
        repo = Path(args.repo).resolve()
        out = Path(args.out)
        if not out.is_absolute() or out.resolve().is_relative_to(repo):
            out = None
            raise ValueError('--out must be absolute and outside repository')
        out = out.resolve()
        if out.exists() and any(out.iterdir()):
            out = None
            raise ValueError('--out must be a new or empty evidence directory')
        out.mkdir(parents=True, exist_ok=True)
        if Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != repo:
            raise ValueError('--repo must be the resolved Git top-level; select a module with --root')
        root = relative(repo, args.root)
        if not root.is_dir():
            raise ValueError('module root does not exist')
        if args.base:
            report['base_commit'] = git(repo, 'rev-parse', '--verify', '--end-of-options', args.base + '^{commit}').decode().strip()
        before = binding(repo)
        report['source'] = before
        package = getattr(args, 'package', None)
        if package and args.language != 'python':
            raise ValueError('--package is supported only for Python')
        files = args.files
        if args.command == 'check' and not files:
            changed = git(repo, 'diff', '--name-only', '-z', report['base_commit'], '--')
            untracked = git(repo, 'ls-files', '--others', '--exclude-standard', '-z')
            files = sorted({os.fsdecode(path) for path in (changed + untracked).split(b'\0') if path})
        report['changed_files'] = files
        selected = [relative(repo, value) for value in files]
        seeds = [str(path.relative_to(root)) for path in selected if path.is_relative_to(root)]
        report['outside_module'] = [value for value, path in zip(files, selected) if not path.is_relative_to(root)]
        report['missing_files'] = [value for value, path in zip(files, selected) if not path.is_file()]
        rules_name = args.rules if args.rules else str((root / 'layout.yaml').relative_to(repo))
        rules = relative(repo, rules_name)
        report['inputs'] = {
            'repo': str(repo), 'root': str(root.relative_to(repo)),
            'language': args.language, 'engine': 'native', 'symbols': True,
            'include_tests': True, 'rules': str(rules.relative_to(repo)) if rules.is_file() else None,
            'budget': args.budget, 'task': args.task, 'files': files, 'package': package,
            'module_files': seeds, 'base': report.get('base_commit'),
        }
        options = ['--engine', 'native', '--language', args.language, '--symbols', '--include-tests']
        if package:
            options += ['--package', package]
        if rules.is_file():
            policy = out / 'current-layout.yaml'
            shutil.copyfile(rules, policy)
            options += ['--rules', str(policy)]
            report['rules_sha256'] = hashlib.sha256(policy.read_bytes()).hexdigest()
        elif args.rules:
            raise ValueError('requested rules file does not exist')
        else:
            report['limitations'].append('No layout.yaml: forbidden/unplanned policy coverage is incomplete.')
        binary = report['tool']['binary']

        def native(arguments, cwd, name, allowed=(0,)):
            output = out / name
            report['artifacts'][name] = str(output)
            return run([binary, '--no-daemon', *arguments], cwd, output, allowed)

        head = out / 'head.json'
        native(['scan', '.', *options, '-o', str(head)], root, 'head-scan.log')
        report['artifacts']['head.json'] = str(head)
        head_document = document(head, ['files', 'edges', 'modules', 'cycles'])
        indexed = {entry['path'] for entry in head_document['files']}
        report['unscanned_files'] = [value for value, path in zip(files, selected)
                                    if path.is_relative_to(root) and str(path.relative_to(root)) not in indexed]
        if args.command == 'prepare':
            if not seeds:
                raise ValueError('no changed-file seeds inside module; provide --files')
            native(['context', '--graph', str(head), '--root', '.', '--task', args.task,
                    '--files', *seeds, '--budget', args.budget, '--format', 'json'], root, 'context.json')
            context = document(out / 'context.json', ['entries', 'omitted', 'limitations'])
            report['context'] = context
            report['limitations'] += context['limitations']
            source = next((str(path.relative_to(root)) for path in selected if path.is_relative_to(root) and path.is_file() and str(path.relative_to(root)) in indexed and path.suffix in {'.ts', '.tsx', '.js', '.jsx', '.py', '.go'}), None)
            if source:
                native(['--brief', 'explain', source, '--graph', str(head)], root, 'explain.json')
                report['explain'] = document(out / 'explain.json', [])
            report['status'] = 'prepared'
        else:
            base = report['base_commit']
            with tempfile.TemporaryDirectory(prefix='plumb-archgraph-base-') as temporary:
                temporary = Path(temporary)
                archive = temporary / 'base.tar'
                with archive.open('wb') as stream:
                    subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), 'archive', '--format=tar', base], stdout=stream, check=True, timeout=30)
                tree = (temporary / 'tree').resolve()
                tree.mkdir()
                with tarfile.open(archive) as contents:
                    # Git trees can contain symlinks; never follow one outside snapshot.
                    for member in contents.getmembers():
                        if member.issym() or member.islnk():
                            raise ValueError('base snapshot contains links; unsupported safe snapshot scope')
                        if not (tree / member.name).resolve().is_relative_to(tree):
                            raise ValueError('unsafe base archive path')
                    for member in contents.getmembers():
                        target = tree / member.name
                        if member.isdir():
                            target.mkdir(parents=True, exist_ok=True)
                        elif member.isfile():
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with contents.extractfile(member) as source, target.open('wb') as destination:
                                shutil.copyfileobj(source, destination)
                        else:
                            raise ValueError('unsupported base archive entry')
                # Archive attributes can omit or rewrite blobs. Compare the module's
                # complete tracked blob set against Git objects before trusting it.
                for row in git(repo, 'ls-tree', '-rz', base).split(b'\0'):
                    if not row:
                        continue
                    header, name = row.split(b'\t', 1)
                    _, kind, object_id = header.split()
                    archived = tree / os.fsdecode(name)
                    if not archived.is_relative_to(tree / root.relative_to(repo)):
                        continue
                    if kind != b'blob' or not archived.is_file():
                        raise ValueError('base archive omitted a tracked module file (export-ignore/submodule unsupported)')
                    data = archived.read_bytes()
                    actual = hashlib.new('sha1' if len(object_id) == 40 else 'sha256', b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                    if actual != object_id.decode():
                        raise ValueError('base archive rewrote a tracked blob (export-subst unsupported)')
                base_root = tree / root.relative_to(repo)
                if not base_root.is_dir():
                    raise ValueError('module root absent from base')
                native(['scan', '.', *options, '-o', str(out / 'base.json')], base_root, 'base-scan.log')
                report['artifacts']['base.json'] = str(out / 'base.json')
                base_document = document(out / 'base.json', ['files', 'edges', 'modules', 'cycles'])
                base_indexed = {entry['path'] for entry in base_document['files']}
                suffixes = {'python': {'.py'}, 'typescript': {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts'}, 'go': {'.go'}}[args.language]
                gaps = [value for value, path in zip(files, selected)
                        if path.is_relative_to(root) and path.suffix in suffixes
                        and str(path.relative_to(root)) not in (indexed if path.exists() else base_indexed)]
                if gaps:
                    report['unscanned_files'] = gaps
                    raise ValueError('changed source coverage incomplete; unscanned files require another module/package or checker')
                code = native(['diff', str(out / 'base.json'), str(head), '--fail-on',
                               'new-forbidden,new-cycles,new-unplanned', '--format', 'json'], root, 'diff.json', (0, 1))
                diff = document(out / 'diff.json', ['new_forbidden', 'new_cycles', 'new_unplanned'])
                report['diff'] = diff
                failed = any(diff[key] for key in ('new_forbidden', 'new_cycles', 'new_unplanned'))
                if bool(code) != failed:
                    raise ValueError('native diff verdict contradicts JSON findings')
                report['status'] = 'fail' if failed else 'pass'
        if before != binding(repo):
            raise ValueError('source changed during evidence collection; rerun with fresh output')
        result = int(report['status'] == 'fail')
    except (Unavailable, OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as error:
        report['status'] = 'skipped' if isinstance(error, Unavailable) else 'error'
        report['reason'] = str(error)
        result = 2
        # Missing tools still leave a receipt if the requested location is safe.
        if out is None and getattr(args, 'out', None):
            candidate = Path(args.out)
            if candidate.is_absolute() and not candidate.resolve().is_relative_to(Path(args.repo).resolve()) and not candidate.exists():
                candidate.mkdir(parents=True)
                out = candidate
    if out:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor')
    for name in ('prepare', 'check'):
        command = commands.add_parser(name)
        command.add_argument('--repo', required=True)
        command.add_argument('--root', default='.')
        command.add_argument('--base', required=name == 'check')
        command.add_argument('--files', nargs='*', default=[])
        command.add_argument('--task', default='Review change against approved intent')
        command.add_argument('--budget', default='8k')
        command.add_argument('--language', choices=['typescript', 'python', 'go'], required=True)
        command.add_argument('--rules')
        command.add_argument('--package', help='Explicit Python package; identical at both scan endpoints')
        command.add_argument('--out', required=True)
    return execute(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
