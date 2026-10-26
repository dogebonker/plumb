import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pr_benchmark as bench


def case(identity="feature"):
    return {"id": identity, "repo": "/private/source", "base_commit": "a" * 40,
            "reference_commit": "b" * 40, "prepared_dir": "/private/prepared",
            "pr": {"title": "Add feature", "body": "Accept the new value.", "url": "https://example.org/pr/1"},
            "claude_md": "Run tests. Preserve contracts.", "test_command": ["python3", "test_feature.py"],
            "acceptance_files": ["test_feature.py"]}


class ProtocolTests(unittest.TestCase):
    def test_counterbalanced_order_has_every_permutation(self):
        self.assertEqual(len(set(bench.ORDER)), 6)
        for position in range(3):
            self.assertEqual({arm: sum(order[position] == arm for order in bench.ORDER) for arm in bench.ARMS},
                             dict.fromkeys(bench.ARMS, 2))

    def test_manifest_rejects_duplicate_or_unsafe_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            for cases in ([case(), case()], [case("../escape")]):
                path.write_text(json.dumps(cases))
                with self.assertRaises(ValueError):
                    bench.manifest_cases(path)

    def test_same_task_prompt_and_pinned_model_effort(self):
        config = {"claude": "claude", "model": "claude-opus-4-6", "effort": "high", "snapshot": "/public/factory"}
        for arm in bench.ARMS:
            command = bench.command(config, arm, Path("settings"), "session", bench.task_prompt(case()))
            self.assertEqual(command[-1], bench.task_prompt(case()))
            self.assertEqual(command[command.index("--model") + 1], config["model"])
            self.assertEqual(command[command.index("--effort") + 1], "high")
            self.assertNotIn("--dangerously-skip-permissions", command)
            self.assertEqual("--plugin-dir" in command, arm == "factory")
        feature = {**case(), "runtime_env": {"NODE_PATH": "/tmp/shared/cache"}, "test_cwd": "app"}
        prompt = bench.task_prompt(feature)
        self.assertIn("python3 test_feature.py", prompt)
        self.assertIn("Working directory relative to repository: app", prompt)
        self.assertIn("/tmp/shared/cache", prompt)
        self.assertIn("Future held-out test files may be absent", prompt)

    def test_provided_acceptance_prompt_and_file_integrity_are_trusted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, work = root / "baseline", root / "work"
            feature = {**case(), "provide_acceptance": True, "acceptance_support_files": ["tests/fixtures/payload.json"]}
            for folder in (baseline, work):
                for relative in feature["acceptance_files"] + feature["acceptance_support_files"]:
                    path = folder / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("immutable acceptance bytes")
            prompt = bench.task_prompt(feature)
            self.assertIn("Provided acceptance tests and support are immutable", prompt)
            self.assertIn("intentionally RED on BASE. All must pass", prompt)
            self.assertNotIn("Future held-out test files may be absent", prompt)
            self.assertIn("Local unsigned Git commits are authorized", prompt)
            files = bench.provided_acceptance(feature, work)
            settings = bench.actor_settings(work, root / "snapshot", [], "bare", protected_files=files)
            for file in files:
                self.assertIn(str(file.resolve()), settings["sandbox"]["filesystem"]["denyWrite"])
                self.assertIn(f"Edit(/{file.resolve()})", settings["permissions"]["deny"])
                self.assertIn(f"Write(/{file.resolve()})", settings["permissions"]["deny"])
            self.assertTrue(bench.acceptance_integrity(feature, work, baseline)["verified"])
            (work / feature["acceptance_files"][0]).write_text("changed by actor")
            check = bench.acceptance_integrity(feature, work, baseline)
            self.assertFalse(check["verified"])
            self.assertEqual(check["changed"], feature["acceptance_files"])

    def test_factory_hook_installation_is_explicit_and_factory_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hook = root / "snapshot" / "hooks" / "plumb_gate.py"
            hook.parent.mkdir(parents=True)
            hook.write_text("import json, sys; json.load(sys.stdin)\n")
            work = root / "work"
            work.mkdir()
            for arm in bench.ARMS:
                settings = bench.actor_settings(work, root / "snapshot", [], arm, factory_hooks=True)
                self.assertEqual("hooks" in settings, arm == "factory")
                self.assertNotIn("hooks", bench.actor_settings(work, root / "snapshot", [], arm))
                if arm == "factory":
                    entry = settings["hooks"]["PreToolUse"][0]
                    self.assertEqual(entry["matcher"], "Edit|Write|MultiEdit|NotebookEdit")
                    self.assertIn(str(hook), entry["hooks"][0]["command"])
            self.assertTrue(bench.hook_preflight(root / "snapshot", work)["ready"])
            hook.write_text("raise RuntimeError('broken installation')\n")
            self.assertFalse(bench.hook_preflight(root / "snapshot", work)["ready"])
            hook.unlink()
            self.assertFalse(bench.hook_preflight(root / "snapshot", work)["ready"])

    def test_broken_factory_hook_stops_trial_before_any_paid_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actor = root / "prepared" / "actor"
            actor.mkdir(parents=True)
            bench.pr_fixtures._init_git(actor)
            bench.write(root / "prepared" / "admission.json", {"admitted": True})
            runtime = root / "runtime"
            runtime.mkdir()
            entry = {"case": "feature", "arm": "factory", "runtime": str(runtime)}
            config = {"factory_hooks": True, "snapshot": str(root / "missing-snapshot"), "schedule": [entry]}
            feature = {**case(), "prepared_dir": str(root / "prepared")}
            with patch("pr_benchmark.benchmark.invoke") as invoke:
                result = bench.trial(config, feature, entry, root / "out")
            invoke.assert_not_called()
            self.assertEqual(result["status"], "infrastructure_error")
            self.assertFalse(result["hook_installation"]["ready"])
            settings = json.loads((root / "out" / "trials" / "feature" / "factory" / "settings.json").read_text())
            self.assertIn("PreToolUse", settings["hooks"])

    def test_shared_policy_inputs_are_pinned_immutable_and_disclosed_in_all_arms(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "policy.md"
            source.write_text("Money is never float.")
            feature = {**case(), "prepared_dir": str(root / "prepared"), "shared_inputs": [
                {"path": ".plumb/system/adr/0007.md", "source": str(source), "sha256": bench.sha(source)}]}
            for tree in ("actor", "reference"):
                target = root / "prepared" / tree / feature["shared_inputs"][0]["path"]
                target.parent.mkdir(parents=True)
                target.write_bytes(source.read_bytes())
            bench.verify_files(feature)
            self.assertIn(feature["shared_inputs"][0]["path"], bench.task_prompt(feature))
            paths = bench.provided_acceptance(feature, root / "prepared" / "actor")
            self.assertEqual(len(paths), 1)
            for arm in bench.ARMS:
                settings = bench.actor_settings(root / "work", root / "snapshot", [], arm, protected_files=paths)
                self.assertIn(str(paths[0].resolve()), settings["sandbox"]["filesystem"]["denyWrite"])
            paths[0].write_text("actor rewrote policy")
            with self.assertRaisesRegex(ValueError, "shared input"):
                bench.verify_files(feature)
            feature["shared_inputs"][0]["path"] = "../escape"
            with self.assertRaises(ValueError):
                bench.provided_acceptance(feature, root / "work")

    def test_policy_graph_uses_identical_pinned_rules_on_both_scans(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rules = root / "layout.yaml"
            rules.write_text("layers: {}\n")
            feature = {**case(), "archgraph_rules": str(rules), "archgraph_rules_sha256": bench.sha(rules)}
            config = {"tools": {"archgraph": {"path": "/fake/archgraph", "sha256": "pinned"}}}
            actual_sha = bench.sha
            with patch("pr_benchmark.sha", side_effect=lambda path: "pinned" if str(path) == "/fake/archgraph" else actual_sha(path)), \
                    patch("pr_benchmark.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
                result = bench.graph_check(config, feature, root / "work", root / "artifact")
            for call in run.call_args_list[:2]:
                argv = call.args[0]
                self.assertEqual(argv[argv.index("--rules") + 1], str(rules))
            self.assertIn("forbidden", result["scope"])
            self.assertNotIn("cycle-only", result["scope"])
            rules.write_text("tampered")
            with self.assertRaisesRegex(ValueError, "rules changed"):
                bench.graph_check(config, feature, root / "work", root / "artifact")

    def test_private_corpus_roots_cover_sibling_prepared_trees_without_public_overlap(self):
        cases = [{**case("one"), "prepared_dir": "/private/corpus/one"},
                 {**case("two"), "prepared_dir": "/private/corpus/two"}]
        roots = bench.private_input_roots(cases, ["/private/actors", "/private/framework"])
        self.assertEqual(roots, [str(Path("/private/corpus").resolve())])
        for path in ("/private/corpus/runtime", "/private"):
            with self.assertRaisesRegex(ValueError, "overlaps"):
                bench.private_input_roots(cases, [path])

    def test_opt_in_runtime_storage_is_persistent_and_outside_denied_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            out = root / "results"
            path = bench.persistent_runtime_home(root, out, "actors-")
            self.assertEqual(path.parent, root.resolve())
            self.assertTrue(path.is_dir())
            for forbidden in (out, out / "state"):
                with self.assertRaisesRegex(ValueError, "inside denied"):
                    bench.persistent_runtime_home(forbidden, out, "actors-")
        with patch("pr_benchmark.tempfile.mkdtemp", return_value="/tmp/legacy") as temporary:
            bench.persistent_runtime_home(None, Path("/tmp/out"), "actors-")
            temporary.assert_called_once_with(prefix="actors-", dir=None)

    def test_new_profile_discloses_scope_and_joins_helpers_in_all_arms(self):
        feature = {**case(), "scope": "Offline email-domain unit contract only; not full request handler."}
        self.assertIn(feature["scope"], bench.task_prompt(feature))
        self.assertIn("identical in every arm", bench.task_prompt(feature))
        legacy = {"model": "pinned", "effort": "high"}
        self.assertNotIn("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", bench.actor_environment(legacy))
        for flag in ("diagnostics", "factory_hooks"):
            self.assertEqual(bench.actor_environment({**legacy, flag: True})["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"], "1")
        feature["shared_inputs"] = [{"source": "/private/standing/0007.md"}]
        roots = bench.private_input_roots([{**feature, "prepared_dir": "/private/corpus/one"}], ["/private/actors"])
        self.assertIn(str(Path("/private/standing").resolve()), roots)
        settings = bench.actor_settings(Path("/private/actor"), Path("/private/framework"), [Path("/private/standing")], "factory", ["/private/deps"])
        for denied in ("/private/standing", "/private/framework", "/private/deps"):
            self.assertIn(f"Write(/{Path(denied).resolve()}/**)", settings["permissions"]["deny"])

    def test_diagnostic_native_invocation_is_opt_in_only(self):
        with patch("pr_benchmark.benchmark.invoke", return_value={}) as invoke:
            bench.invoke_actor({}, ["cli"], Path("work"), Path("turn"), 3)
            invoke.assert_called_once_with(["cli"], Path("work"), Path("turn"), 3)
            invoke.reset_mock()
            bench.invoke_actor({"diagnostics": True}, ["cli"], Path("work"), Path("turn"), 3)
            invoke.assert_called_once_with(["cli"], Path("work"), Path("turn"), 3, observe_events=True)

    def test_shared_caches_are_readable_but_cannot_be_edited_or_written(self):
        settings = bench.actor_settings(Path("/tmp/work"), Path("/tmp/snapshot"), [], "bare", ["/tmp/deps"])
        filesystem = settings["sandbox"]["filesystem"]
        cache = Path("/tmp/deps").resolve()
        work = Path("/tmp/work").resolve()
        self.assertIn(str(cache), filesystem["denyWrite"])
        self.assertNotIn(str(cache), filesystem["denyRead"])
        self.assertIn(f"Edit(/{cache}/**)", settings["permissions"]["deny"])
        self.assertIn(f"Edit(/{work}/node_modules/**)", settings["permissions"]["deny"])

    def test_private_file_and_directory_rules_deny_exact_and_recursive_tools(self):
        settings = bench.actor_settings(Path("/tmp/work"), Path("/tmp/snapshot"),
                                        [Path("/private/receipt.json"), Path("/private/corpus")], "bare",
                                        ["/private/cache"])
        for target in ("/private/receipt.json", "/private/corpus"):
            target = Path(target).resolve()
            for tool in ("Read", "Edit", "Write"):
                self.assertIn(f"{tool}(/{target})", settings["permissions"]["deny"])
                self.assertIn(f"{tool}(/{target}/**)", settings["permissions"]["deny"])
        for target in ("/private/cache", "/tmp/snapshot"):
            target = Path(target).resolve()
            for tool in ("Edit", "Write"):
                self.assertIn(f"{tool}(/{target})", settings["permissions"]["deny"])
                self.assertIn(f"{tool}(/{target}/**)", settings["permissions"]["deny"])

    def test_verification_files_are_pinned_and_cache_paths_include_wrapper_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            wrapper = Path(temporary) / "wrapper.py"
            wrapper.write_text("print(1)")
            feature = {**case(), "verification_files": [{"path": str(wrapper), "sha256": bench.sha(wrapper)}],
                       "test_env": {"NODE_PATH": "/tmp/shared/deps"}}
            bench.verify_files(feature)
            self.assertIn(str(wrapper.parent.resolve()), bench.readonly_caches(feature))
            self.assertIn(str(Path("/tmp/shared/deps").resolve()), bench.readonly_caches(feature))
            wrapper.write_text("print(2)")
            with self.assertRaisesRegex(ValueError, "verification file changed"):
                bench.verify_files(feature)

    def test_both_read_routes_external_network_memory_and_secrets_are_blocked(self):
        settings = bench.actor_settings(Path("/tmp/actor"), Path("/tmp/factory"), [Path("/private/heldout")], "bare")
        self.assertIn("/private/heldout", settings["sandbox"]["filesystem"]["denyRead"])
        self.assertIn("Read(//private/heldout/**)", settings["permissions"]["deny"])
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        self.assertEqual(settings["sandbox"]["network"]["allowedDomains"], ["localhost", "127.0.0.1", "::1"])
        self.assertTrue(settings["sandbox"]["network"]["allowLocalBinding"])
        self.assertTrue(settings["sandbox"]["network"]["strictAllowlist"])
        self.assertFalse(settings["autoMemoryEnabled"])
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret", "GITHUB_TOKEN": "secret"}), \
                bench.clean_environment({"NODE_PATH": "/tmp/cache"}):
            self.assertNotIn("ANTHROPIC_API_KEY", os.environ)
            self.assertNotIn("GITHUB_TOKEN", os.environ)
            self.assertEqual(os.environ["NODE_PATH"], "/tmp/cache")
        with self.assertRaises(ValueError), bench.clean_environment({"GITHUB_TOKEN": "secret"}):
            pass

    def test_native_probe_needs_both_error_results_and_rejects_leak(self):
        path = Path("/private/canary")
        calls = [{"type": "tool_use", "id": "read", "name": "Read", "input": {"file_path": str(path)}},
                 {"type": "tool_use", "id": "bash", "name": "Bash", "input": {"command": f"cat {path}"}}]
        errors = [{"type": "tool_result", "tool_use_id": identity, "is_error": True,
                   "content": "Permission denied by sandbox"} for identity in ("read", "bash")]
        events = [{"type": "assistant", "message": {"content": calls}}, {"type": "user", "message": {"content": errors}}]
        self.assertTrue(bench.isolation_probe(events, path, "SECRET")["verified"])
        events[-1]["message"]["content"].pop()
        self.assertFalse(bench.isolation_probe(events, path, "SECRET")["verified"])
        events[-1]["message"]["content"] = errors + [{"type": "text", "text": "SECRET"}]
        self.assertFalse(bench.isolation_probe(events, path, "SECRET")["verified"])

    def test_inventory_rejects_unexpected_plugin_mcp_and_model(self):
        event = {"type": "system", "subtype": "init", "plugins": [], "mcp_servers": [], "model": "pinned"}
        self.assertTrue(bench.verify_inventory([event], "bare", "pinned")["verified"])
        self.assertFalse(bench.verify_inventory([event], "factory", "pinned")["verified"])
        event["plugins"] = [{"name": "factory"}]
        self.assertTrue(bench.verify_inventory([event], "factory", "pinned")["verified"])
        event["plugins"].append({"name": "cc-plugin-bundled"})
        self.assertTrue(bench.verify_inventory([event], "factory", "pinned")["verified"])
        event["mcp_servers"] = [{"name": "pond"}]
        self.assertFalse(bench.verify_inventory([event], "factory", "pinned")["verified"])
        self.assertFalse(bench.verify_inventory([event], "factory", "different")["verified"])

    def test_subagents_are_forced_to_root_model_and_usage_drift_is_rejected(self):
        config = {"model": "claude-opus-5-5", "effort": "high"}
        self.assertEqual(bench.actor_environment(config), {"CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-5-5",
                                                         "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1",
                                                         "CLAUDE_CODE_EFFORT_LEVEL": "high"})
        usage = {"models": [config["model"]], "model_usage": {config["model"]: {}}, "tokens": 123}
        self.assertTrue(bench.verify_model_usage(usage, config["model"])["verified"])
        self.assertFalse(bench.verify_model_usage({**usage, "models": [config["model"], "sonnet"]}, config["model"])["verified"])
        self.assertFalse(bench.verify_model_usage({**usage, "tokens": None}, config["model"])["verified"])
        self.assertFalse(bench.verify_model_usage({**usage, "model_usage": None}, config["model"])["verified"])

    def test_actor_build_cache_is_local_and_never_inherits_reference_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            config = {"model": "pinned", "effort": "high"}
            with patch.dict(os.environ, {"GOCACHE": "/private/reference-object-cache"}), \
                    bench.clean_environment({"GOCACHE": "/private/reference-object-cache"}):
                os.environ.update(bench.actor_runtime_environment(config, work))
                self.assertEqual(Path(os.environ["GOCACHE"]), work.resolve() / ".benchmark-runtime" / "go-cache")
                self.assertTrue(Path(os.environ["GOCACHE"]).is_dir())
                self.assertEqual(os.environ["CLAUDE_CODE_SUBAGENT_MODEL_FORCE"], "1")

    def test_pinned_compiler_and_sdk_are_identical_for_actor_and_calibration_fallback(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch("pr_benchmark.xcode_environment", return_value={"CC": "/installed/clang", "SDKROOT": "/installed/sdk"}):
            config = {"model": "pinned", "effort": "high", "toolchain_environment": {"CC": "/frozen/clang", "SDKROOT": "/frozen/sdk"}}
            self.assertEqual(bench.actor_runtime_environment(config, temporary)["CC"], "/frozen/clang")
            del config["toolchain_environment"]
            self.assertEqual(bench.actor_runtime_environment(config, temporary)["CC"], "/installed/clang")

    def test_task_usage_excludes_probe_and_does_not_double_count_cumulative_resume(self):
        record = {"probe_usage": {"tokens": 5}, "attempts": [{"usage": {"tokens": 10}}, {"usage": {"tokens": 25}}]}
        self.assertEqual(bench.usage(record), 25)
        self.assertEqual(bench.observation_usage(record), 30)
        record["attempts"][-1]["usage"]["tokens"] = None
        self.assertIsNone(bench.usage(record))
        self.assertIsNone(bench.observation_usage(record))
        self.assertIsNone(bench.usage({"probe_usage": {"tokens": 5}}))

    def test_cost_aggregates_use_native_values_and_missing_values_stay_unknown(self):
        self.assertEqual(bench.total_and_median([1.25, 2.75, 3], 2), "7.00 / 2.75")
        self.assertEqual(bench.total_and_median([1.25, None], 2), "unknown")
        self.assertEqual(bench.total_and_median([], 2), "unknown")

    def test_counts_require_known_runner_summary_and_record_skips(self):
        self.assertEqual(bench.test_counts("Ran 12 tests in 0.01s\nOK (skipped=1)"), {"total": 12, "skipped": 1})
        self.assertEqual(bench.test_counts("Tests: 2 skipped, 4 passed, 6 total"), {"total": 6, "skipped": 2})
        self.assertEqual(bench.test_counts("===RUN test\n--- PASS: TestOne (0s)\n--- SKIP: TestTwo (0s)"), {"total": 2, "skipped": 1})
        self.assertEqual(bench.test_counts("================ 4 passed, 1 skipped in 0.1s ================"), {"total": 5, "skipped": 1})
        self.assertIsNone(bench.test_counts("all good"))

    def test_grader_fails_closed_without_native_sandbox(self):
        runner = bench.isolated_grader({}, case(), Path("artifact"), {})
        with patch("pr_benchmark.platform.system", return_value="Linux"):
            result = runner(Path("work"), ["dangerous-test"])
        self.assertEqual(result["status"], "not_run")

    def test_only_calibration_accepts_positive_counts_without_oracle(self):
        counts = {"total": 3, "skipped": 0}
        self.assertFalse(bench.test_coverage_matches(counts, None))
        self.assertTrue(bench.test_coverage_matches(counts, None, calibration=True))
        self.assertFalse(bench.test_coverage_matches({"total": 0, "skipped": 0}, None, calibration=True))
        self.assertFalse(bench.test_coverage_matches({"total": 3, "skipped": 1}, None, calibration=True))
        self.assertFalse(bench.test_coverage_matches(counts, {"total": 4, "skipped": 0}, calibration=True))
        self.assertTrue(bench.test_coverage_matches(counts, counts))

    def test_candidate_setup_failure_is_quality_failure_only_when_reference_control_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for control_status, expected in (("pass", "candidate_error"), ("setup_error", "setup_error"),
                                             ("coverage_missing", "setup_error")):
                candidate = {"status": "setup_error", "output": "candidate did not compile", "returncode": 1}
                control = {"status": control_status, "output": "immutable reference control"}
                with patch("pr_benchmark.pr_fixtures.grade_case", side_effect=[candidate, control]) as grade:
                    result = bench.grade_candidate({}, case(), root / "candidate", root / "prepared", root / "artifact", {})
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["output"], "candidate did not compile")
                self.assertEqual(result["reference_control"], control)
                self.assertEqual(grade.call_args_list[1].args[1:3], (root / "prepared" / "reference", root / "prepared" / "reference"))

    def test_passing_candidate_does_not_run_extra_reference_control(self):
        with patch("pr_benchmark.pr_fixtures.grade_case", return_value={"status": "pass"}) as grade:
            result = bench.grade_candidate({}, case(), Path("candidate"), Path("prepared"), Path("artifact"), {})
        self.assertEqual(result["status"], "pass")
        self.assertEqual(grade.call_count, 1)

    def test_archgraph_execution_error_is_not_a_quality_violation(self):
        config = {"tools": {"archgraph": {"path": "/fake/archgraph", "sha256": "pinned"}}}
        for code, expected in ((0, "no_new_violations"), (1, "failed"), (2, "scan_error"), (9, "scan_error")):
            runs = [subprocess.CompletedProcess([], 0, "", ""), subprocess.CompletedProcess([], 0, "", ""),
                    subprocess.CompletedProcess([], code, "", "")]
            with patch("pr_benchmark.sha", return_value="pinned"), \
                    patch("pr_benchmark.subprocess.run", side_effect=runs):
                result = bench.graph_check(config, case(), Path("work"), Path("artifact"))
            self.assertEqual(result["status"], expected)
            self.assertIn("cycle-only", result["scope"])
            self.assertIn("no policies supplied", result["scope"])

    def test_reference_control_exception_preserves_candidate_failure_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch("pr_benchmark.pr_fixtures.grade_case", side_effect=[{"status": "setup_error", "output": "candidate output"}, OSError("control unavailable")]):
                result = bench.grade_candidate({}, case(), root / "candidate", root / "prepared", root / "artifact", {})
        self.assertEqual(result["status"], "setup_error")
        self.assertEqual(result["output"], "candidate output")
        self.assertEqual(result["reference_control"], {"status": "setup_error", "output": "control unavailable"})

    def test_native_test_policy_allows_loopback_only_and_keeps_external_deny(self):
        policy = bench.loopback_test_policy('(version 1)\n(allow default)\n(deny network*)\n')
        self.assertIn('(deny network*)', policy)
        self.assertIn('(allow network-outbound (remote ip "localhost:*"))', policy)
        self.assertIn('(allow network-inbound (local ip "localhost:*"))', policy)
        self.assertIn('(allow network-bind (local ip "localhost:*"))', policy)
        self.assertNotIn('(allow network*)', policy)


class BlindAndReportTests(unittest.TestCase):
    def test_factory_seed_contains_only_existing_lock_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, snapshot = root / "work", root / "snapshot"
            work.mkdir()
            (snapshot / "kit").mkdir(parents=True)
            (snapshot / "kit" / "packs.lock.yaml").write_text("version: 1\npacks:\n  stack: pinned\n")
            bench.seed_factory(work, snapshot)
            lock = (work / ".plumb" / "plumb.lock").read_text()
            self.assertEqual(lock, f"framework: {{ dev_path: {snapshot.resolve()} }}\npacks:\n  stack: pinned\n\nskills_linked: []\n")
            self.assertFalse((work / ".claude").exists())
            self.assertEqual(list((work / ".plumb").iterdir()), [work / ".plumb" / "plumb.lock"])

    def test_arm_setup_commits_guide_and_lock_before_actor_and_ignores_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bench.pr_fixtures._init_git(root)
            (root / "CLAUDE.md").write_text("frozen guidance")
            bench.seed_factory(root, root / "snapshot")
            bench.commit_arm_setup(root)
            status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout, "")
            for directory in (".tmp", ".benchmark-runtime"):
                (root / directory).mkdir()
                (root / directory / "generated").write_text("runtime cache")
            status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout, "")

    def test_driver_stops_before_next_paid_arm_after_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = {"controller_sha256": bench.sha(bench.__file__), "fixture_sha256": bench.sha(bench.pr_fixtures.__file__),
                      "framework_sha256": "frozen", "snapshot": "snapshot", "tools": {},
                      "schedule": [{"case": "feature", "arm": arm} for arm in bench.ARMS]}
            bench.write(root / "run.json", config)
            with patch.object(sys, "argv", ["pr_benchmark.py", "run", "--out", str(root)]), \
                    patch("pr_benchmark.verify_inputs", return_value=[case()]), \
                    patch("pr_benchmark.benchmark.tree_hash", return_value="frozen"), \
                    patch("pr_benchmark.trial", return_value={"status": "interrupted"}) as trial, \
                    patch("pr_benchmark.report") as report:
                bench.main()
            self.assertEqual(trial.call_count, 1)
            report.assert_called_once_with(root.resolve())

    def test_diagnostics_are_explicit_and_do_not_replace_scoring(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config = {"controller_sha256": bench.sha(bench.__file__), "fixture_sha256": bench.sha(bench.pr_fixtures.__file__),
                          "framework_sha256": "frozen", "snapshot": "snapshot", "tools": {}, "schedule": []}
                if enabled:
                    config["diagnostics"] = True
                bench.write(root / "run.json", config)
                argv = ["pr_benchmark.py", "run", "--out", str(root), "--case", "goldengate1038"]
                if enabled:
                    argv.append("--diagnostics")
                with patch.object(sys, "argv", argv), \
                        patch("pr_benchmark.verify_inputs", return_value=[case()]), \
                        patch("pr_benchmark.benchmark.tree_hash", return_value="frozen"), \
                        patch("pr_benchmark.report") as report, \
                        patch("pr_benchmark.diagnostics.save_report") as diagnostics:
                    bench.main()
                report.assert_called_once_with(root.resolve())
                if enabled:
                    diagnostics.assert_called_once_with(root.resolve(), ["goldengate1038"])
                else:
                    diagnostics.assert_not_called()

    def test_error_after_refused_resume_preserves_immutable_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = {"status": "timeout", "attempts": [{"usage": {"tokens": 123}}]}
            bench.write(root / "result.json", original)
            before = (root / "result.json").read_bytes()
            bench.record_run_error(root, {"case": "feature", "arm": "bare"}, ValueError("blind packets frozen"))
            self.assertEqual((root / "result.json").read_bytes(), before)
            self.assertEqual(len(list(root.glob("run-error-*.json"))), 1)

    def test_frozen_inputs_reject_manifest_source_and_admission_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = root / "prepared"
            (prepared / "actor").mkdir(parents=True)
            (prepared / "reference").mkdir()
            files = [prepared / "actor" / "main.py", prepared / "reference" / "main.py"]
            for file in files:
                file.write_text("print(1)")
            bench.write(prepared / "admission.json", {"admitted": True})
            feature = {**case(), "prepared_dir": str(prepared)}
            bench.write(root / "manifest.json", {"cases": [feature]})
            config = {"instruction_hashes": {feature["id"]: bench.hashlib.sha256(feature["claude_md"].encode()).hexdigest()},
                      "requirements_hashes": {feature["id"]: bench.hashlib.sha256(bench.requirements(feature).encode()).hexdigest()}}
            config["frozen_inputs"] = bench.input_fingerprints(root, [feature])
            self.assertEqual(bench.verify_inputs(root, config), [feature])
            for file in [*files, prepared / "admission.json", root / "manifest.json"]:
                content = file.read_text()
                file.write_text(content + "\n")
                with self.assertRaisesRegex(ValueError, "changed"):
                    bench.verify_inputs(root, config)
                file.write_text(content)
            config["instruction_hashes"][feature["id"]] = "tampered"
            with self.assertRaisesRegex(ValueError, "CLAUDE.md changed"):
                bench.verify_inputs(root, config)

    def test_trial_keeps_matched_instructions_and_finished_trials_do_not_rerun(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = root / "prepared"
            (prepared / "actor").mkdir(parents=True)
            (prepared / "reference").mkdir()
            (prepared / "actor" / "main.py").write_text("print(1)")
            bench.pr_fixtures._init_git(prepared / "actor")
            bench.write(prepared / "admission.json", {"admitted": True})
            out = root / "out"
            out.mkdir()
            entries = [{"case": "feature", "arm": arm, "runtime": str(root / arm)} for arm in bench.ARMS]
            for entry in entries:
                Path(entry["runtime"]).mkdir()
            config = {"snapshot": str(root / "snapshot"), "schedule": entries, "model": "pinned", "effort": "high",
                      "claude": "claude", "timeout_seconds": 10, "max_questions": 2}
            feature = {**case(), "prepared_dir": str(prepared)}
            events = [{"type": "result", "subtype": "success",
                       "modelUsage": {"pinned": {"inputTokens": 1, "outputTokens": 1, "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0}},
                       "result": json.dumps({"state": "complete", "question": "",
                                                                                     "recommended_answer": "", "summary": "Done"})}]
            run = {"events": events, "seconds": 2, "timeout": False, "returncode": 0}
            with patch("pr_benchmark.benchmark.invoke", return_value=run) as invoke, \
                    patch("pr_benchmark.isolation_probe", return_value={"verified": True}), \
                    patch("pr_benchmark.verify_inventory", return_value={"verified": True}), \
                    patch("pr_benchmark.pr_fixtures.grade_case", return_value={"status": "pass"}), \
                    patch("pr_benchmark.graph_check", return_value={"status": "no_new_violations"}):
                for entry in entries:
                    result = bench.trial(config, feature, entry, out)
                    self.assertEqual(result["status"], "complete")
                    self.assertEqual(result["task_seconds"], 2)
                    self.assertEqual(result["probe_seconds"], 2)
                    self.assertEqual(result["seconds"], 4)
                    instructions = Path(result["workspace"]) / "CLAUDE.md"
                    self.assertEqual(instructions.exists(), entry["arm"] != "bare")
                    if instructions.exists():
                        self.assertEqual(instructions.read_text(), feature["claude_md"])
                    self.assertEqual((Path(result["workspace"]) / ".plumb" / "plumb.lock").exists(), entry["arm"] == "factory")
                    count = invoke.call_count
                    self.assertEqual(bench.trial(config, feature, entry, out), result)
                    self.assertEqual(invoke.call_count, count)

    def test_blind_copy_strips_nested_history_instructions_and_caches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input"
            source.mkdir()
            for filename in ("main.py", "docs/guide.md", "nested/CLAUDE.md", "nested/AGENTS.md", ".git/config", ".plumb/state", "node_modules/pkg/index.js"):
                file = source / filename
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("content")
            bench.product_copy(source, root / "packet")
            self.assertEqual(sorted(str(path.relative_to(root / "packet")) for path in (root / "packet").rglob("*") if path.is_file()),
                             ["docs/guide.md", "main.py"])

    def test_missing_evidence_never_passes_or_declares_winner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bench.write(root / "run.json", {"model": "pinned", "effort": "high", "margin_percentage_points": 10})
            bench.write(root / "manifest.json", {"cases": [case(f"task{i}") for i in range(24)]})
            with patch("pr_benchmark.verify_inputs", return_value=[case(f"task{i}") for i in range(24)]):
                report = bench.report(root)
            self.assertFalse(report["complete"])
            self.assertEqual(report["accepted"], dict.fromkeys(bench.ARMS, 0))
            self.assertIn("no winner", report["report"])
            self.assertEqual(report["report"].count("| missing | missing | missing | missing | unknown | unknown | unknown | unknown | unknown | unknown |"), 72)
            self.assertIn("| Task tokens | Task USD | Task seconds | Probe tokens | Probe USD | Probe seconds |", report["report"])
            self.assertIn("| bare | unknown | unknown | unknown |", report["report"])

    def test_report_shows_native_task_and_probe_cost_separately(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = case()
            bench.write(root / "run.json", {"model": "pinned", "effort": "high", "margin_percentage_points": 10})
            path = root / "trials" / feature["id"] / "bare" / "result.json"
            path.parent.mkdir(parents=True)
            bench.write(path, {"status": "complete", "task_seconds": 4, "probe_seconds": 1,
                              "probe_usage": {"tokens": 5, "cost_usd": .01},
                              "attempts": [{"usage": {"tokens": 10, "cost_usd": .02}},
                                           {"usage": {"tokens": 30, "cost_usd": .07}}]})
            with patch("pr_benchmark.verify_inputs", return_value=[feature]):
                report = bench.report(root)["report"]
            self.assertIn("| 30 | 0.070000 | 4.0 | 5 | 0.010000 | 1.0 |", report)
            self.assertIn("| bare | 30 / 30 | 0.070000 / 0.070000 | 4.0 / 4.0 |", report)
            self.assertIn("no winner", report)

    def test_verdicts_freeze_before_join_and_packet_mutation_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / "blind" / "anonymous"
            packet.mkdir(parents=True)
            (packet / "main.py").write_text("print(1)")
            bench.write(root / "blind-key.json", {"anonymous": {"case": "feature", "arm": "bare",
                                                               "packet_sha256": bench.benchmark.tree_hash(packet)}})
            source = root / "review.json"
            bench.write(source, {"anonymous": {"verdict": "accept", "reason": "Meets requirements."}})
            (packet / "main.py").write_text("print(2)")
            with self.assertRaisesRegex(ValueError, "changed"):
                bench.freeze_verdicts(root, source)
            (packet / "main.py").write_text("print(1)")
            bench.freeze_verdicts(root, source)
            with self.assertRaisesRegex(ValueError, "already frozen"):
                bench.freeze_verdicts(root, source)


if __name__ == "__main__":
    unittest.main()
