import io
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import pr_fixtures as fixtures


class PRFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        self.git("init", "--quiet", "--template=")
        (self.repo / "feature.py").write_text("def value():\n    return 0\n")
        (self.repo / "CLAUDE.md").write_text("secret instructions")
        (self.repo / "nested").mkdir()
        (self.repo / "nested/AGENTS.md").write_text("more instructions")
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude/secret").write_text("not for actors")
        self.commit()
        base = self.git("rev-parse", "HEAD")
        (self.repo / "feature.py").write_text("def value():\n    return 1\n")
        (self.repo / "test_acceptance.py").write_text(
            "import unittest\nfrom feature import value\n"
            "class Acceptance(unittest.TestCase):\n"
            "    def test_value(self): self.assertEqual(value(), 1)\n")
        self.commit()
        self.case = {"id": "feature", "repo": str(self.repo), "base_commit": base,
                     "reference_commit": self.git("rev-parse", "HEAD"),
                     "acceptance_files": ["test_acceptance.py"],
                     "test_command": [sys.executable, "-m", "unittest", "discover", "-v"]}

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True,
                              check=True, text=True).stdout.strip()

    def commit(self):
        self.git("add", "--all")
        self.git("-c", "user.name=Test", "-c", "user.email=test@localhost", "-c",
                 "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")

    def test_admission_ground_truth_and_actor_isolation(self):
        before = self.git("status", "--porcelain")
        result = fixtures.admit_case(self.case, self.root / "prepared")
        self.assertTrue(result["admitted"], result)
        self.assertEqual(result["baseline"]["status"], "assertion_failure")
        self.assertEqual(result["reference_result"]["status"], "pass")
        actor = result["actor"]
        for hidden in ("CLAUDE.md", "nested/AGENTS.md", ".claude", "test_acceptance.py"):
            self.assertFalse((actor / hidden).exists(), hidden)
        for args, expected in ((["rev-list", "--count", "HEAD"], "1"), (["remote"], "")):
            run = subprocess.run(["git", "-C", str(actor), *args], capture_output=True, text=True, check=True)
            self.assertEqual(run.stdout.strip(), expected)
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertIn("secret instructions", (self.repo / "CLAUDE.md").read_text())
        self.assertEqual(fixtures.snapshot_hash(actor), result["baseline_hash"])
        (actor / "feature.py").write_text("def value():\n    return 1\n")
        self.assertNotEqual(fixtures.snapshot_hash(actor), result["baseline_hash"])
        self.assertEqual(fixtures.grade_case(self.case, actor, result["reference"])["status"], "pass")
        self.assertFalse((actor / "test_acceptance.py").exists())

    def test_existing_public_test_bytes_preserved_in_actor_and_synthetic_history(self):
        old_test = "# existing public test before the PR\n"
        (self.repo / "test_acceptance.py").write_text(old_test)
        self.commit()
        self.case["base_commit"] = self.git("rev-parse", "HEAD")
        (self.repo / "test_acceptance.py").write_text("# future hidden test\n")
        self.commit()
        self.case["reference_commit"] = self.git("rev-parse", "HEAD")
        result = fixtures.prepare_case(self.case, self.root / "prepared")
        self.assertEqual((result["actor"] / "test_acceptance.py").read_text(), old_test)
        history = subprocess.run(["git", "-C", str(result["actor"]), "show", "HEAD:test_acceptance.py"],
                                 capture_output=True, text=True, check=True).stdout
        self.assertEqual(history, old_test)
        self.assertEqual((result["reference"] / "test_acceptance.py").read_text(), "# future hidden test\n")

    def test_test_cwd_and_env_apply_inside_grading_copy(self):
        (self.repo / "apps/api").mkdir(parents=True)
        (self.repo / "apps/api/placeholder").write_text("tracked directory")
        self.commit()
        case = dict(self.case, base_commit=self.git("rev-parse", "HEAD"),
                    reference_commit=self.git("rev-parse", "HEAD"), test_cwd="apps/api",
                    test_env={"PYTHONPATH": ".", "FIXTURE_VALUE": "configured"},
                    test_command=[sys.executable, "-c",
                                  ("import os; from pathlib import Path; import feature; "
                                  "assert Path.cwd().parts[-2:] == ('apps', 'api'); "
                                  "assert os.environ['FIXTURE_VALUE'] == 'configured'; "
                                  "assert 'source' not in os.environ['PYTHONPATH']; print('checks passed')")])
        result = fixtures.admit_case(case, self.root / "env-prepared")
        self.assertEqual(result["baseline"]["status"], "pass", result)
        for invalid in ("../source", "/tmp", "apps/../api"):
            with self.assertRaises(ValueError):
                fixtures.grade_case(dict(case, test_cwd=invalid), result["actor"], result["reference"])
        with self.assertRaises(ValueError):
            fixtures.grade_case(dict(case, test_env={"INVALID": 12}), result["actor"], result["reference"])

    def test_subtree_export_excludes_siblings_and_preserves_provenance(self):
        module = self.repo / "apps/api"
        module.mkdir(parents=True)
        (module / "feature.py").write_text("def value():\n    return 0\n")
        (self.repo / "sibling-oracle.txt").write_text("future answer outside selected module")
        (self.repo / "api-link").symlink_to("apps/api")
        self.commit()
        base = self.git("rev-parse", "HEAD")
        (module / "feature.py").write_text("def value():\n    return 1\n")
        (module / "test_acceptance.py").write_text((self.repo / "test_acceptance.py").read_text())
        self.commit()
        reference = self.git("rev-parse", "HEAD")
        case = dict(self.case, base_commit=base, reference_commit=reference, source_subdir="apps/api")
        result = fixtures.admit_case(case, self.root / "subtree")
        self.assertTrue(result["admitted"], result)
        self.assertEqual(result["base_commit"], base)
        self.assertEqual(result["reference_commit"], reference)
        self.assertEqual(result["source_subdir"], "apps/api")
        self.assertTrue((result["actor"] / "feature.py").exists())
        for hidden in ("test_acceptance.py", "sibling-oracle.txt", "apps"):
            self.assertFalse((result["actor"] / hidden).exists())
        history = subprocess.run(["git", "-C", str(result["actor"]), "rev-list", "--count", "HEAD"],
                                 capture_output=True, text=True, check=True).stdout
        self.assertEqual(history.strip(), "1")
        for invalid in ("../apps/api", "/apps/api", "api-link", "feature.py"):
            with self.assertRaises(ValueError):
                fixtures.export_commit(self.repo, reference, self.root / "invalid-export", subdir=invalid)
            self.assertFalse((self.root / "invalid-export").exists())

    def test_runner_callback_gets_disposable_copy_and_reference_tests(self):
        calls = []
        def isolated_runner(work, command, timeout, test_cwd, test_env):
            calls.append(work)
            self.assertTrue((work / "test_acceptance.py").is_file())
            self.assertEqual(command, self.case["test_command"])
            self.assertEqual((timeout, test_cwd, test_env), (12, ".", {"MODE": "isolated"}))
            self.assertFalse((work / ".git").exists())
            status = "assertion_failure" if "return 0" in (work / "feature.py").read_text() else "pass"
            return {"status": status, "output": "isolated check", "returncode": int(status != "pass"),
                    "duration_seconds": 0}
        case = dict(self.case, test_env={"MODE": "isolated"})
        result = fixtures.admit_case(case, self.root / "callback", timeout=12, runner=isolated_runner)
        self.assertTrue(result["admitted"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(not path.exists() for path in calls))
        self.assertFalse((result["actor"] / "test_acceptance.py").exists())

    def test_setup_failure_and_arbitrary_exit_one_are_not_admitted(self):
        for command in ([sys.executable, "-c", "import nonexistent_third_party_dependency"],
                        [sys.executable, "-c", "raise SystemExit(1)"]):
            case = dict(self.case, test_command=command)
            result = fixtures.admit_case(case, self.root / f"prepared-{len(list(self.root.iterdir()))}")
            self.assertFalse(result["admitted"])
            self.assertEqual(result["baseline"]["status"], "setup_error")

    def test_declared_missing_feature_symbol_is_explicit_and_bounded(self):
        (self.repo / "feature.py").write_text("def new_feature():\n    return 1\n")
        (self.repo / "test_acceptance.py").write_text(
            "import unittest\nfrom feature import new_feature\n"
            "class Acceptance(unittest.TestCase):\n"
            "    def test_value(self): self.assertEqual(new_feature(), 1)\n")
        self.commit()
        declaration = {"pattern": "cannot import name 'new_feature'", "symbol": "new_feature",
                       "reference_file": "feature.py"}
        case = dict(self.case, reference_commit=self.git("rev-parse", "HEAD"),
                    expected_feature_failure=declaration)
        result = fixtures.admit_case(case, self.root / "declared-feature")
        self.assertTrue(result["admitted"], result)
        self.assertEqual(result["baseline"]["status"], "expected_feature_failure")
        for invalid in ({**declaration, "pattern": ".*"}, {**declaration, "symbol": "missing"},
                        {**declaration, "reference_file": "test_acceptance.py"}):
            with self.assertRaises(ValueError):
                fixtures._expected_feature_failure(dict(case, expected_feature_failure=invalid), result["reference"])
        case["test_command"] = [sys.executable, "-c",
                                "print(\"cannot import name 'new_feature'\"); import missing_package"]
        blocked = fixtures.admit_case(case, self.root / "missing-package")
        self.assertFalse(blocked["admitted"])
        self.assertEqual(blocked["baseline"]["status"], "setup_error")

    def test_declared_new_relative_module_is_bounded_to_reference_and_heldout_importer(self):
        (self.repo / 'utils').mkdir()
        (self.repo / 'tests').mkdir()
        (self.repo / 'utils/new-feature.ts').write_text('export function newFeature() { return 1; }')
        (self.repo / 'tests/feature.spec.ts').write_text("import { newFeature } from '../utils/new-feature';")
        self.commit()
        message = "Cannot find module '../utils/new-feature' from 'tests/feature.spec.ts'"
        declaration = {'pattern': re.escape("Cannot find module '../utils/new-feature'"),
                       'symbol': 'newFeature', 'reference_file': 'utils/new-feature.ts',
                       'missing_module': '../utils/new-feature', 'importing_test': 'tests/feature.spec.ts'}
        case = dict(self.case, reference_commit=self.git('rev-parse', 'HEAD'),
                    acceptance_files=['tests/feature.spec.ts'], expected_feature_failure=declaration)
        def runner(work, *unused):
            reference = (work / 'utils/new-feature.ts').exists()
            return {'status': 'pass' if reference else 'setup_error', 'returncode': 0 if reference else 1,
                    'output': 'tests passed' if reference else message, 'duration_seconds': 0}
        result = fixtures.admit_case(case, self.root / 'local-module', runner=runner)
        self.assertTrue(result['admitted'])
        self.assertEqual(result['baseline']['status'], 'expected_feature_failure')
        self.assertFalse(fixtures.expected_feature_matches(case, result['reference'], result['actor'],
                         message + "\nCannot find module 'third-party' from 'tests/feature.spec.ts'"))
        self.assertFalse(fixtures.expected_feature_matches(case, result['reference'], result['actor'],
                         message + '\nSyntaxError: broken dependency'))
        for module, importer in (('third-party', 'tests/feature.spec.ts'),
                                 ('../../outside', 'tests/feature.spec.ts'),
                                 ('../utils/new-feature', 'unconfigured.spec.ts')):
            invalid = dict(case, expected_feature_failure={**declaration, 'missing_module': module,
                           'importing_test': importer})
            with self.assertRaises(ValueError):
                fixtures._expected_feature_failure(invalid, result['reference'], result['actor'])
        existing = dict(case, base_commit=case['reference_commit'])
        with self.assertRaises(ValueError):
            fixtures.prepare_case(existing, self.root / 'existing-module')

    def test_runtime_directories_do_not_change_hash_or_enter_grading_copy(self):
        prepared = fixtures.prepare_case(self.case, self.root / 'runtime-exclusions')
        for name in ('.benchmark-runtime', '.benchmark-grading-runtime', '.tmp'):
            runtime = prepared['actor'] / name
            runtime.mkdir()
            (runtime / 'private-output').write_text('not part of the product')
            output = runtime / ('claude-501/tasks/native-agent.output' if name == '.tmp' else 'external-link')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.symlink_to(self.repo)
        self.assertEqual(fixtures.snapshot_hash(prepared['actor']), prepared['baseline_hash'])
        def runner(work, *unused):
            for name in ('.benchmark-runtime', '.benchmark-grading-runtime', '.tmp'):
                self.assertFalse((work / name).exists())
            return {'status': 'pass'}
        self.assertEqual(fixtures.grade_case(self.case, prepared['actor'], prepared['reference'], runner=runner)['status'], 'pass')

    def test_future_test_support_is_grader_only_and_cannot_copy_production(self):
        (self.repo / 'tests/fixtures').mkdir(parents=True)
        (self.repo / 'tests/fixtures/required.json').write_text('{"expected": 1}')
        (self.repo / 'test_acceptance.py').write_text(
            'import json,unittest\nfrom pathlib import Path\nfrom feature import value\n'
            'class Acceptance(unittest.TestCase):\n'
            '    def test_value(self):\n'
            '        expected = json.loads(Path("tests/fixtures/required.json").read_text())["expected"]\n'
            '        self.assertEqual(value(), expected)\n')
        self.commit()
        case = dict(self.case, reference_commit=self.git('rev-parse', 'HEAD'),
                    acceptance_support_files=['tests/fixtures/required.json'])
        result = fixtures.admit_case(case, self.root / 'test-support')
        self.assertTrue(result['admitted'], result)
        self.assertEqual(result['baseline']['status'], 'assertion_failure')
        self.assertEqual(result['reference_result']['status'], 'pass')
        self.assertFalse((result['actor'] / 'tests/fixtures/required.json').exists())
        self.assertFalse((result['actor'] / 'test_acceptance.py').exists())
        provided = fixtures.prepare_case(dict(case, provide_acceptance=True), self.root / 'provided-tests')
        self.assertEqual((provided['actor'] / 'test_acceptance.py').read_bytes(),
                         (provided['reference'] / 'test_acceptance.py').read_bytes())
        self.assertEqual((provided['actor'] / 'tests/fixtures/required.json').read_bytes(),
                         (provided['reference'] / 'tests/fixtures/required.json').read_bytes())
        self.assertIn('return 0', (provided['actor'] / 'feature.py').read_text())
        self.assertEqual(fixtures.snapshot_hash(provided['actor']), provided['baseline_hash'])
        for args, expected in ((['rev-list', '--count', 'HEAD'], '1'),
                               (['config', '--local', 'user.name'], 'Benchmark'),
                               (['config', '--local', 'commit.gpgsign'], 'false'),
                               (['config', '--local', 'tag.gpgsign'], 'false'),
                               (['config', '--local', 'core.hooksPath'], '/dev/null')):
            value = subprocess.check_output(['git', '-C', str(provided['actor']), *args], text=True).strip()
            self.assertEqual(value, expected)
        committed = subprocess.check_output(['git', '-C', str(provided['actor']), 'show', 'HEAD:test_acceptance.py'])
        self.assertEqual(committed, (provided['reference'] / 'test_acceptance.py').read_bytes())
        for invalid in ('src/feature.ts', 'tests/fixtures/secret.py', '../tests/fixtures/required.json',
                        '.codex/tests/fixtures/secret.json'):
            with self.assertRaises(ValueError):
                fixtures.support_paths(dict(case, acceptance_support_files=[invalid]))

    def test_timeout_and_missing_binary(self):
        result = fixtures.run_tests(self.repo, [sys.executable, "-c", "import time; time.sleep(5)"], .05)
        self.assertEqual(result["status"], "timeout")
        result = fixtures.run_tests(self.repo, [str(self.root / "no-binary")])
        self.assertEqual(result["status"], "setup_error")

    def test_safe_archive_and_escape_rejection(self):
        def archive(name, link=None):
            output = io.BytesIO()
            with tarfile.open(fileobj=output, mode="w") as tar:
                member = tarfile.TarInfo(name)
                if link is not None:
                    member.type, member.linkname = tarfile.SYMTYPE, link
                    tar.addfile(member)
                else:
                    member.size = 4
                    tar.addfile(member, io.BytesIO(b"test"))
            return output.getvalue()
        for index, (name, link) in enumerate((("../escape", None), ("/escape", None),
                                             (".git/config", None), ("link", "../../escape"),
                                             ("link", "/tmp/escape"))):
            destination = self.root / f"archive-{index}"
            destination.mkdir()
            with self.assertRaises(ValueError):
                fixtures._extract(archive(name, link), destination, False)
        destination = self.root / "safe-archive"
        destination.mkdir()
        fixtures._extract(archive("file"), destination, False)
        fixtures._extract(archive("link", "file"), destination, False)
        self.assertEqual((destination / "link").read_text(), "test")

    def test_actor_symlink_escape_and_test_parent_redirect_rejected(self):
        prepared = fixtures.prepare_case(self.case, self.root / "prepared")
        (prepared["actor"] / "escape").symlink_to(self.repo)
        with self.assertRaises(ValueError):
            fixtures.grade_case(self.case, prepared["actor"], prepared["reference"])

    def test_acceptance_paths_never_copy_production_or_globs(self):
        for path in ("feature.py", "../test_feature.py", "tests/*.py", "/test_feature.py",
                     ".git/test_feature.py", ".claude/test_feature.py", "test_feature.py/../feature.py"):
            with self.assertRaises(ValueError, msg=path):
                fixtures.acceptance_paths(dict(self.case, acceptance_files=[path]))
        with self.assertRaises(ValueError):
            fixtures.prepare_case(self.case, self.repo)
        with self.assertRaises(ValueError):
            fixtures.prepare_case(self.case, self.repo / "must-not-create")
        self.assertFalse((self.repo / "must-not-create").exists())

    def test_jest_executed_runtime_failure_counts_but_suite_setup_stays_infrastructure(self):
        report = ("FAIL src/feature.spec.ts\n  ● calls the new API\n"
                  "TypeError: service.newFeature is not a function\n"
                  "Tests: 1 failed, 2 passed, 3 total\n")
        self.assertEqual(fixtures.classify_result(1, report), 'assertion_failure')
        for setup in ("Test suite failed to run", "Cannot find module './fixtures/required.json'",
                      "SyntaxError: invalid source", "ModuleNotFoundError: missing_dependency", "[build failed]"):
            self.assertEqual(fixtures.classify_result(1, report + setup), 'setup_error')
        self.assertEqual(fixtures.classify_result(1, 'TypeError: service.newFeature is not a function'), 'setup_error')

    def test_supported_assertion_formats_and_setup_precedence(self):
        reports = ["FAIL: test_thing (test_feature.Acceptance)\nFAILED (failures=1)",
                   "E   assert 0 == 1\n1 failed in 0.2s",
                   "Expected: 1\nTests: 1 failed, 2 passed, 3 total",
                   "--- FAIL: TestFeature (0.0s)\n    feature_test.go:2: got 0, want 1\nFAIL\texample/module\t0.1s"]
        for report in reports:
            self.assertEqual(fixtures.classify_result(1, report), "assertion_failure", report)
            self.assertEqual(fixtures.classify_result(1, report + "\nModuleNotFoundError: dependency"), "setup_error")
        self.assertEqual(fixtures.classify_result(1, "TypeError: broken setup"), "setup_error")
        self.assertEqual(fixtures.classify_result(0, "Ran 0 tests\nOK"), "setup_error")


if __name__ == "__main__":
    unittest.main()
