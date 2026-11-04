"""Local Git integration checks; no providers, clones, or network."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from secrets import token_urlsafe
from unittest.mock import patch
from urllib.parse import urlunsplit

from plumb.workspace import initialize, is_connected, refresh, status, verify_binding


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.workspace = self.root / 'workspace'
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/main.py').write_text('value = 1\n')
        self.source = '# Design\r\n\r\n## Wanted\r\nExact text.\r\n```md\r\n## Fake\r\n```\r\n### Child\r\nMore.\r\n## Other\r\nExcluded.\r\n'
        (self.repo / 'decision.md').write_bytes(self.source.encode())
        self.commit()

    def git(self, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        return subprocess.check_output(['git', '-c', 'core.hooksPath=' + os.devnull,
            '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args], env=env,
            stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def init(self, **kwargs):
        return initialize(self.workspace, self.repo, 'Example', ['src'], 'decision.md', **kwargs)

    def visible(self):
        return {p.relative_to(self.workspace).as_posix(): p.read_bytes()
                for p in self.workspace.rglob('*') if p.is_file() and 'sources' not in p.parts}

    def test_committed_snapshot_and_exact_typed_section(self):
        (self.repo / 'src/main.py').write_text('dirty code\n')
        (self.repo / 'decision.md').write_text('dirty decision\n')
        result = self.init(section='Wanted')
        self.assertEqual(result['status'], 'current')
        self.assertTrue(is_connected(self.workspace))
        self.assertEqual((self.workspace / 'code/src/main.py').read_text(), 'value = 1\n')
        self.assertEqual((self.workspace / 'sources/decision.md').read_bytes().split(b'\n', 1)[1], self.source.encode())
        intent = (self.workspace / 'knowledge/intent.md').read_bytes()
        selected = self.source[self.source.index('## Wanted'):self.source.index('## Other')]
        self.assertTrue(intent.endswith(selected.encode()))
        self.assertIn(b'type: Module Contract', intent)
        self.assertIn(b'type: Software Module', (self.workspace / 'knowledge/module.md').read_bytes())
        self.assertIn(b'okf_version: "0.2"', (self.workspace / 'knowledge/index.md').read_bytes())
        self.assertIn('local-git:', intent.decode())
        self.assertEqual(result['capture']['body_start_line'], 2)
        verify_binding(self.workspace, self.repo, result['binding'])

    def test_refresh_and_binding_ignore_unrelated_commit(self):
        original = self.init()
        before = self.visible()
        capture = self.workspace / 'sources/decision.md'
        first_bytes, first_stat = capture.read_bytes(), capture.stat()
        (self.repo / 'src/main.py').write_text('value = 2\n')
        self.commit()
        self.assertEqual(status(self.workspace, self.repo)['binding'], original['binding'])
        self.assertEqual(refresh(self.workspace, self.repo)['status'], 'unchanged')
        self.assertEqual(capture.read_bytes(), first_bytes)
        self.assertEqual(capture.stat().st_mtime_ns, first_stat.st_mtime_ns)
        (self.repo / 'decision.md').write_text('# New source\n')
        self.commit()
        self.assertEqual(status(self.workspace, self.repo)['status'], 'changed')
        with self.assertRaises(ValueError):
            verify_binding(self.workspace, self.repo, original['binding'])
        result = refresh(self.workspace, self.repo)
        self.assertEqual(result['status'], 'updated')
        self.assertFalse(result['knowledge_updated'])
        self.assertTrue(result['review_required'])
        self.assertEqual(self.visible(), before)
        self.assertEqual(status(self.workspace, self.repo)['status'], 'current')
        self.assertTrue(capture.read_bytes().endswith(b'# New source\n'))

    def test_existing_workspace_and_missing_section_do_not_write(self):
        with self.assertRaises(ValueError):
            self.init(section='Missing')
        self.assertFalse(self.workspace.exists())
        self.workspace.mkdir()
        (self.workspace / 'note').write_text('keep')
        with self.assertRaises(ValueError):
            self.init()
        self.assertEqual(list(self.workspace.iterdir()), [self.workspace / 'note'])

    def test_tampered_capture_and_metadata_refused(self):
        original = self.init()
        capture = self.workspace / 'sources/decision.md'
        old = capture.read_bytes()
        capture.write_bytes(old + b'manual note\n')
        self.assertEqual(status(self.workspace, self.repo)['status'], 'unavailable')
        with self.assertRaises(ValueError):
            refresh(self.workspace, self.repo)
        self.assertTrue(capture.read_bytes().endswith(b'manual note\n'))
        capture.write_bytes(old.replace(b'"commit":"', b'"commit":"bad'))
        with self.assertRaises(ValueError):
            verify_binding(self.workspace, self.repo, original['binding'])

    def test_wrong_repository_and_unavailable_source(self):
        self.init()
        other = self.root / 'other'
        other.mkdir()
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        self.assertEqual(status(self.workspace, other)['status'], 'unavailable')
        before = (self.workspace / 'sources/decision.md').read_bytes()
        self.git('rm', '-q', 'decision.md')
        self.commit()
        self.assertEqual(status(self.workspace, self.repo)['status'], 'unavailable')
        with self.assertRaises(ValueError):
            refresh(self.workspace, self.repo)
        self.assertEqual((self.workspace / 'sources/decision.md').read_bytes(), before)

    def test_unsafe_symlink_binary_missing_and_size_rejected(self):
        (self.repo / 'src/link').symlink_to('main.py')
        self.commit()
        for selections in (['../repo'], ['/src'], ['src/./main.py'], ['missing'], ['src']):
            with self.subTest(selections=selections), self.assertRaises(ValueError):
                initialize(self.workspace, self.repo, 'Example', selections, 'decision.md')
        self.git('rm', '-q', 'src/link')
        (self.repo / 'src/binary').write_bytes(b'abc\x00def')
        self.commit()
        with self.assertRaises(ValueError):
            self.init()
        self.git('rm', '-q', 'src/binary')
        self.commit()
        with patch('plumb.workspace.MAX_FILE_BYTES', 10), self.assertRaises(ValueError):
            self.init()
        self.assertFalse(self.workspace.exists())

    def test_setext_section_and_fenced_false_heading(self):
        source = '# Top\n```\nWrong\n-----\n```\nWanted\n------\nExact.\n### Child\nMore.\nPeer\n----\nExcluded.\n'
        (self.repo / 'decision.md').write_text(source)
        self.commit()
        self.init(section='Wanted')
        intent = (self.workspace / 'knowledge/intent.md').read_text()
        self.assertTrue(intent.endswith('Wanted\n------\nExact.\n### Child\nMore.\n'))

    def test_source_symlink_and_submodule_rejected(self):
        (self.repo / 'source-link').symlink_to('decision.md')
        self.commit()
        with self.assertRaises(ValueError):
            initialize(self.workspace, self.repo, 'Example', ['src'], 'source-link')
        commit = self.git('rev-parse', 'HEAD')
        self.git('update-index', '--add', '--cacheinfo', '160000,' + commit + ',submodule')
        self.git('commit', '-qm', 'submodule fixture')
        with self.assertRaises(ValueError):
            initialize(self.workspace, self.repo, 'Example', ['submodule'], 'decision.md')

    def test_github_origin_is_credential_free(self):
        password = token_urlsafe(24)
        origin = urlunsplit(('https', f'fixture-user:{password}@github.com',
                            '/example/project.git', 'secret=yes', ''))
        self.git('remote', 'add', 'origin', origin)
        self.init()
        config = (self.workspace / '.plumb/source.json').read_text()
        intent = (self.workspace / 'knowledge/intent.md').read_text()
        self.assertNotIn('secret', config)
        self.assertNotIn(password, config)
        self.assertNotIn(password, intent)
        self.assertNotIn('fixture-user', config)
        self.assertIn('https://github.com/example/project/blob/', intent)

    def test_literal_hash_heading_cannot_select_a_different_section(self):
        from plumb.workspace import _section
        source = '# C\nWrong.\n# C#\nExact.\n# Next ##\nOther.\n'
        self.assertEqual(_section(source, 'C#'), '# C#\nExact.\n')
        self.assertEqual(_section(source, '# C#'), '# C#\nExact.\n')
        self.assertEqual(_section(source, 'Next'), '# Next ##\nOther.\n')
        with self.assertRaises(ValueError):
            _section('# C\nWrong.\n', 'C#')

    def test_excluded_code_paths_are_rejected_instead_of_silently_skipped(self):
        for name in ('src/build/rules.py', 'src/.hidden/rules.py', 'src/.rules.py'):
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('selected = True\n')
        self.commit()
        for name in ('src/build/rules.py', 'src/.hidden', 'src/.rules.py'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'excluded from review'):
                initialize(self.workspace, self.repo, 'Example', [name], 'decision.md')
        self.assertFalse(self.workspace.exists())

    def test_managed_fifo_is_unavailable_without_blocking(self):
        self.init()
        capture = self.workspace / 'sources/decision.md'
        capture.unlink()
        os.mkfifo(capture)
        result = status(self.workspace, self.repo)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIn('regular file', result['error'])

    def test_ref_moving_during_refresh_does_not_report_current_success(self):
        from plumb.workspace import _atomic
        self.init()
        (self.repo / 'decision.md').write_text('# Updated\n')
        self.commit()

        def move_ref(path, data):
            _atomic(path, data)
            self.git('rm', '-q', 'decision.md')
            self.commit()

        with patch('plumb.workspace._atomic', side_effect=move_ref), \
                self.assertRaisesRegex(ValueError, 'Capture updated, but Git source is unavailable'):
            refresh(self.workspace, self.repo)
        self.assertTrue((self.workspace / 'sources/decision.md').read_bytes().endswith(b'# Updated\n'))


if __name__ == '__main__':
    unittest.main()
