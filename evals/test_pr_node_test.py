import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pr_node_test


class NodeAdapterTests(unittest.TestCase):
    def test_dependency_link_only_exists_during_child_and_is_removed_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, work = Path(tmp) / 'cache', Path(tmp) / 'work'
            cache.mkdir()
            (cache / 'dependency').mkdir()
            (cache / '.vite-temp').mkdir()
            work.mkdir()
            (work / 'source.ts').write_text('original source')
            (work / '.tmp').mkdir()
            (work / '.tmp/private-output').write_text('runtime data')
            copies = []
            def child(command, **kwargs):
                copied = kwargs['cwd']
                copies.append(copied)
                self.assertTrue(copied.is_relative_to(work.resolve() / '.benchmark-runtime'))
                self.assertFalse((work / 'node_modules').exists())
                self.assertFalse((copied / 'node_modules').is_symlink())
                self.assertEqual((copied / 'node_modules/dependency').resolve(), (cache / 'dependency').resolve())
                self.assertFalse((copied / '.tmp').exists())
                self.assertFalse((copied / '.benchmark-runtime').exists())
                self.assertFalse((copied / 'node_modules/.vite-temp').exists())
                (copied / 'node_modules/.vite-temp').mkdir()
                (copied / 'source.ts').write_text('test mutation')
                return Mock(returncode=1)
            with patch.object(pr_node_test.subprocess, 'run', side_effect=child):
                self.assertEqual(pr_node_test.run(cache, 'jest', ['--runInBand'], work), 1)
            self.assertFalse((work / 'node_modules').exists())
            self.assertTrue(all(not copied.exists() for copied in copies))
            self.assertEqual((work / 'source.ts').read_text(), 'original source')

    def test_typechain_uses_workspace_abis_before_tests_and_stops_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, work = Path(tmp) / 'cache', Path(tmp) / 'work'
            cache.mkdir()
            (work / 'src/abi').mkdir(parents=True)
            (work / 'src/abi/example.json').write_text('[]')
            with patch.object(pr_node_test.subprocess, 'run', return_value=Mock(returncode=1)) as child:
                self.assertEqual(pr_node_test.run(cache, 'jest', [], work, typechain=True), 1)
            self.assertEqual(child.call_count, 1)
            self.assertEqual(child.call_args.args[0][-1], 'src/abi/example.json')
            self.assertFalse((work / 'node_modules').exists())

    def test_existing_dependency_directory_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, work = Path(tmp) / 'cache', Path(tmp) / 'work'
            cache.mkdir()
            (work / 'node_modules').mkdir(parents=True)
            (work / 'node_modules/marker').write_text('original dependencies')
            with patch.object(pr_node_test.subprocess, 'run', return_value=Mock(returncode=0)):
                self.assertEqual(pr_node_test.run(cache, 'vp', [], work), 0)
            self.assertEqual((work / 'node_modules/marker').read_text(), 'original dependencies')


if __name__ == '__main__':
    unittest.main()
