"""Run project tests with an immutable external Node dependency cache."""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(cache, runner, args, workspace=None, typechain=False):
    cache = Path(cache).resolve(strict=True)
    workspace = Path(workspace or Path.cwd()).resolve()
    runtime = workspace / '.benchmark-runtime'
    if runtime.is_symlink():
        raise ValueError('benchmark runtime directory must not be a symlink')
    runtime.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='node-tests-', dir=runtime) as temporary:
        copied = Path(temporary) / 'work'
        shutil.copytree(workspace, copied, symlinks=True,
                        ignore=shutil.ignore_patterns('.git', 'node_modules', '.tmp', '__pycache__',
                                                    '.benchmark-runtime', '.benchmark-grading-runtime'))
        return _run_in_copy(cache, runner, args, copied, typechain)


def _run_in_copy(cache, runner, args, workspace, typechain):
    link = workspace / 'node_modules'
    if link.exists() or link.is_symlink():
        raise ValueError('node_modules must be absent before the trusted test adapter runs')
    link.mkdir()
    identity = link.stat().st_ino
    for dependency in cache.iterdir():
        if dependency.name in {'.vite-temp', '.vite', '.cache'}:
            continue
        (link / dependency.name).symlink_to(dependency, target_is_directory=dependency.is_dir())
    command = (['node', str(cache / 'jest/bin/jest.js')] if runner == 'jest'
               else [str(cache / '.bin/vp'), 'test', 'run'])
    try:
        if typechain and not (workspace / 'src/typechain').exists():
            inputs = sorted(str(path.relative_to(workspace)) for path in (workspace / 'src/abi').glob('*.json'))
            if not inputs:
                raise ValueError('declared TypeChain setup has no source ABI files')
            setup = subprocess.run([str(cache / '.bin/typechain'), '--out-dir', 'src/typechain',
                                    '--target', 'ethers-v6', *inputs], cwd=workspace,
                                   env=dict(os.environ, NODE_PATH=str(cache)), check=False)
            if setup.returncode:
                return setup.returncode
        return subprocess.run([*command, *args], cwd=workspace,
                              env=dict(os.environ, NODE_PATH=str(cache)), check=False).returncode
    finally:
        if link.is_symlink() or not link.is_dir() or link.stat().st_ino != identity:
            raise ValueError('test adapter dependency directory was changed during execution')
        shutil.rmtree(link)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--runner', choices=('jest', 'vp'), required=True)
    parser.add_argument('--typechain', action='store_true', help='run the existing project ABI build before tests')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    extra = args.args[1:] if args.args[:1] == ['--'] else args.args
    return run(args.cache, args.runner, extra, typechain=args.typechain)


if __name__ == '__main__':
    raise SystemExit(main())
