"""Exercise scanner selection without installed scanners or network access."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCAN = Path(__file__).resolve().parents[1] / 'skills/factory-code-review/scripts/scan.sh'


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.calls = self.root / 'calls'
        self.env = {**os.environ, 'PATH': str(self.bin), 'SCAN_CALLS': str(self.calls), 'UNTRUSTED': ''}
        for name in ('git', 'mktemp', 'rm', 'grep'):
            (self.bin / name).symlink_to(shutil.which(name))
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'commit.gpgsign', 'false')
        self.write('initial.txt', 'initial\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output([shutil.which('git'), *args], cwd=self.repo, text=True)

    def write(self, name, data):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        return path

    def stub(self, name, status=0):
        path = self.bin / name
        path.write_text('#!/bin/bash\nprintf "%s\\0" "${0##*/}" "$@" >> "$SCAN_CALLS"\n'
                        f'[[ ${{1:-}} != --version ]] || exit 0\nexit {status}\n')
        path.chmod(0o755)

    def scan(self, base=None, **env):
        result = subprocess.run(['/bin/bash', str(SCAN), base or self.base], cwd=self.repo,
                                env={**self.env, **env}, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout + result.stderr

    def test_committed_staged_unstaged_untracked_and_odd_names(self):
        for name in ('committed.py', 'staged.py', 'unstaged.py'):
            self.write(name, 'old\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'files')
        self.write('committed.py', 'new\n')
        self.git('add', 'committed.py')
        self.git('commit', '-qm', 'committed change')
        self.write('staged.py', 'new\n')
        self.git('add', 'staged.py')
        self.write('unstaged.py', 'new\n')
        self.write('-odd name\nnext.py', 'new\n')
        self.stub('ruff', 1)
        output = self.scan()
        calls = self.calls.read_bytes().split(b'\0')
        for name in ('committed.py', 'staged.py', 'unstaged.py', '-odd name\nnext.py'):
            self.assertIn(('./' + name).encode(), calls)
        self.assertIn('ruff exited 1', output)
        self.assertIn('leads', output)

    def test_staged_change_cancelled_in_worktree_is_still_selected(self):
        self.write('same.py', 'old\n')
        self.git('add', 'same.py')
        self.git('commit', '-qm', 'tracked')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.write('same.py', 'new\n')
        self.git('add', 'same.py')
        self.write('same.py', 'old\n')
        self.stub('ruff')
        output = self.scan()
        self.assertIn(b'./same.py', self.calls.read_bytes().split(b'\0'))
        self.assertIn('gap: index differs from working tree', output)
        self.assertIn('staged bytes are not scanned', output)

    def test_staged_added_file_missing_from_worktree_is_a_gap(self):
        path = self.write('missing.py', 'new\n')
        self.git('add', 'missing.py')
        path.unlink()
        self.stub('ruff')
        output = self.scan()
        self.assertIn('gap: selected file missing from working tree', output)
        self.assertNotIn('no changed files', output)
        self.assertFalse(self.calls.exists())

    def test_invalid_base_and_no_changes_do_not_call_scanners(self):
        self.stub('gitleaks')
        self.assertIn('gap:', self.scan('--help'))
        self.assertFalse(self.calls.exists())
        self.assertIn('no changed files', self.scan())
        self.assertFalse(self.calls.exists())

    def test_untrusted_skips_executable_repo_tools_and_go_config(self):
        for name in ('x.rs', 'x.ts', 'x.go'):
            self.write(name, 'new\n')
        self.write('go.mod', 'module example.invalid/test\n')
        self.write('Cargo.toml', '[package]\nname="test"\nversion="0.1.0"\n')
        for name in ('cargo', 'golangci-lint'):
            self.stub(name)
        local = self.write('node_modules/.bin/eslint', '#!/bin/bash\nexit 99\n')
        local.chmod(0o755)
        output = self.scan(UNTRUSTED='1')
        calls = self.calls.read_bytes().split(b'\0')
        self.assertNotIn(b'cargo', calls)
        self.assertIn(b'--no-config', calls)
        self.assertIn('UNTRUSTED', output)

    def test_scanner_hits_are_leads_not_a_passing_gate(self):
        self.write('x.sh', 'true\n')
        self.stub('shellcheck', 2)
        self.assertIn('shellcheck exited 2', self.scan())

    def test_symlink_target_is_not_scanned_as_repository_source(self):
        outside = self.root / 'outside.py'
        outside.write_text('private = "outside repository"\n')
        (self.repo / 'linked.py').symlink_to(outside)
        self.stub('gitleaks')
        output = self.scan(UNTRUSTED='1')
        self.assertIn('gap: symlink target not scanned', output)
        self.assertFalse(self.calls.exists())

    def test_missing_merge_base_is_a_gap_without_scanning(self):
        self.git('checkout', '-q', '--orphan', 'other')
        self.git('commit', '-qm', 'unrelated')
        self.stub('gitleaks')
        self.assertIn('gap: no merge-base', self.scan())
        self.assertFalse(self.calls.exists())


if __name__ == '__main__':
    unittest.main()
