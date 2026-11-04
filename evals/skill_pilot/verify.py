"""Recheck frozen skill-test evidence with Python only; no agent/model calls."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / 'fixture'


def run(workspace):
    return subprocess.run([sys.executable, '-m', 'unittest', '-v'], cwd=workspace,
                          capture_output=True, text=True, timeout=15, check=False)


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == digest, name
    with tempfile.TemporaryDirectory(prefix='plumb-skill-recheck-') as temporary:
        workspace = Path(temporary)
        shutil.copyfile(FIXTURE / 'baseline/ingester.py', workspace / 'ingester.py')
        shutil.copyfile(FIXTURE / 'baseline/test_ingester.py', workspace / 'test_ingester.py')
        baseline = run(workspace)
        assert baseline.returncode == 0, baseline.stderr
        shutil.copyfile(FIXTURE / 'test_ingester.py', workspace / 'test_ingester.py')
        red = run(workspace)
        assert red.returncode == 1 and 'failures=4' in red.stderr, red.stderr
        shutil.copyfile(FIXTURE / 'ingester.py', workspace / 'ingester.py')
        shutil.rmtree(workspace / '__pycache__', ignore_errors=True)
        green = run(workspace)
        assert green.returncode == 0, green.stderr
    print('Fixture hashes match. Baseline passes; four rejection subcases fail before the change; all three tests pass after it.')
    print('No model calls. This rechecks controlled code behavior, not general skill effectiveness.')


if __name__ == '__main__':
    main()
