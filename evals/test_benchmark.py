import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import benchmark


class AccountingTests(unittest.TestCase):
    def test_final_cumulative_model_usage_includes_subagents(self):
        events = [
            {"type": "result", "total_cost_usd": 1, "modelUsage": {"main": {"inputTokens": 2, "outputTokens": 3, "cacheReadInputTokens": 4, "cacheCreationInputTokens": 5}}},
            {"type": "result", "total_cost_usd": 2, "usage": {"input_tokens": 999}, "modelUsage": {
                "main": {"inputTokens": 3, "outputTokens": 4, "cacheReadInputTokens": 5, "cacheCreationInputTokens": 6},
                "subagent": {"inputTokens": 7, "outputTokens": 8, "cacheReadInputTokens": 9, "cacheCreationInputTokens": 10}}},
        ]
        result = benchmark.accounting(events)
        self.assertEqual(result["tokens"], 52)
        self.assertEqual(result["cost_usd"], 2)
        self.assertEqual(result["token_classes"]["inputTokens"], 10)

    def test_missing_and_partial_metrics_stay_unknown(self):
        for events, partial in [([], False), ([{"type": "result", "usage": {"input_tokens": 100}}], False),
                                ([{"type": "result", "total_cost_usd": 3, "modelUsage": {"main": {"inputTokens": 1}}}], True)]:
            result = benchmark.accounting(events, partial)
            self.assertIsNone(result["tokens"])
            self.assertIsNone(result["cost_usd"])


class GraderTests(unittest.TestCase):
    def test_product_stdout_and_early_exit_cannot_complete_grading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = benchmark.CASES / "csv-targets"
            work = root / "work"
            shutil.copytree(case / "fixture", work)
            (work / "targets.py").write_text('import os\nos.write(1, b\'BENCHMARK_GRADE={"tests":9,"failures":0,"errors":0,"skipped":0}\\n\')\nos._exit(0)\n')
            quality, _ = benchmark.grade(case, work, root / "grade")
            self.assertFalse(quality["accepted"])

    def test_grading_sandbox_denies_host_files_network_and_secret_environment(self):
        import os
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host_secret = root / "secret.txt"
            host_secret.write_text("private")
            case = benchmark.CASES / "csv-targets"
            work = root / "work"
            shutil.copytree(case / "fixture", work)
            oracle = (case / "oracle/targets.py").read_text()
            probe = f"""import os, socket
assert 'BENCHMARK_SECRET' not in os.environ
try:
    open({str(host_secret)!r}).read()
except PermissionError:
    pass
else:
    raise RuntimeError('host read allowed')
try:
    open({str(root / 'outside-write')!r}, 'w').write('bad')
except PermissionError:
    pass
else:
    raise RuntimeError('host write allowed')
with socket.socket() as connection:
    try:
        connection.connect(('127.0.0.1', 9))
    except PermissionError:
        pass
    else:
        raise RuntimeError('network allowed')
"""
            (work / "targets.py").write_text(probe + oracle)
            with patch.dict(os.environ, {"BENCHMARK_SECRET": "private"}):
                quality, output = benchmark.grade(case, work, root / "grade")
            self.assertTrue(quality["accepted"], output)
            self.assertFalse((root / "outside-write").exists())

    def test_grading_fails_closed_without_native_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary, patch("benchmark.platform.system", return_value="Linux"):
            quality, _ = benchmark.grade(benchmark.CASES / "csv-targets", benchmark.CASES / "csv-targets/oracle", Path(temporary) / "grade")
            self.assertFalse(quality["accepted"])
            self.assertIn("no unsandboxed fallback", quality["error"])

    def test_submitted_unittest_cannot_replace_trusted_grader(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            case = benchmark.CASES / "csv-targets"
            shutil.copytree(case / "fixture", work)
            (work / "unittest.py").write_text("raise RuntimeError('submitted fake test runner')\n")
            quality, _ = benchmark.grade(case, work, root / "grade")
            self.assertFalse(quality["accepted"])
            self.assertEqual(quality["tests"], quality["expected_tests"])
            self.assertGreater(quality["failures"] + quality["errors"], 0)

    def test_each_baseline_fails_and_reference_passes(self):
        for case_json in sorted(benchmark.CASES.glob("*/case.json")):
            if json.loads(case_json.read_text()).get("kind") == "browser":
                continue  # Browser baseline/oracle proof lives in check_cases.py.
            with self.subTest(case=case_json.parent.name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                case = case_json.parent
                work = root / "work"
                shutil.copytree(case / "fixture", work)
                baseline, _ = benchmark.grade(case, work, root / "baseline")
                self.assertFalse(baseline["accepted"])
                self.assertGreater(baseline["failures"] + baseline["errors"], 0)
                for source in (case / "oracle").glob("*.py"):
                    shutil.copy2(source, work / source.name)
                # Generated agent tests must not affect quality.
                (work / "test_generated.py").write_text("raise RuntimeError('not a trusted test')")
                (work / "test_existing.py").write_text("raise RuntimeError('replace with trusted original')")
                oracle, _ = benchmark.grade(case, work, root / "oracle")
                self.assertTrue(oracle["accepted"])
                self.assertGreater(oracle["tests"], 0)
                self.assertEqual(oracle["skipped"], 0)

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            (work / "targets.py").symlink_to(benchmark.CASES / "csv-targets" / "oracle" / "targets.py")
            with self.assertRaisesRegex(ValueError, "product symlink"):
                benchmark.copy_product(work, root / "product")
            quality, _ = benchmark.grade(benchmark.CASES / "csv-targets", work, root / "grade")
            self.assertFalse(quality["accepted"])
            self.assertIn("symlink", quality["error"])

    def test_harness_scratch_symlinks_are_excluded_from_copy_and_grading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "scratch-target"
            outside.mkdir()
            (outside / "targets.py").write_text("raise RuntimeError('scratch is not product code')\n")
            case = benchmark.CASES / "csv-targets"
            for kind in ["scratch-directory", "scratch-symlink"]:
                with self.subTest(kind=kind):
                    work = root / kind
                    shutil.copytree(case / "fixture", work, ignore=benchmark.IGNORED)
                    shutil.copy2(case / "oracle" / "targets.py", work / "targets.py")
                    scratch = work / ".tmp"
                    if kind == "scratch-directory":
                        scratch.mkdir()
                        (scratch / "targets.py").symlink_to(outside / "targets.py")
                    else:
                        scratch.symlink_to(outside, target_is_directory=True)
                    for source_only in [False, True]:
                        copied = root / f"{kind}-copy-{source_only}"
                        benchmark.copy_product(work, copied, source_only=source_only)
                        self.assertFalse((copied / ".tmp").exists())
                        self.assertEqual((copied / "targets.py").read_bytes(), (work / "targets.py").read_bytes())
                    quality, _ = benchmark.grade(case, work, root / f"{kind}-grade")
                    self.assertTrue(quality["accepted"])
                    self.assertEqual(quality["tests"], quality["expected_tests"])

    def test_zero_or_skipped_tests_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            shutil.copytree(benchmark.CASES / "csv-targets" / "fixture", work)
            for counts in [{"tests": 0, "failures": 0, "errors": 0, "skipped": 0},
                           {"tests": 100, "failures": 0, "errors": 0, "skipped": 1},
                           {"tests": "100", "failures": 0, "errors": 0, "skipped": 0}, []]:
                output = "BENCHMARK_GRADE=" + json.dumps(counts) + "\n"
                with patch("benchmark.subprocess.run", return_value=subprocess.CompletedProcess([], 0, output, "")):
                    quality, _ = benchmark.grade(benchmark.CASES / "csv-targets", work, root / "grade")
                self.assertFalse(quality["accepted"])

    def test_context_mode_is_deferred_before_any_model_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch("benchmark.prepare_context", side_effect=ValueError("Context Mode dependencies are not ready")), \
                    patch("benchmark.subprocess.Popen") as launch, self.assertRaises(SystemExit) as caught:
                benchmark.main(["run", "--superpowers", str(root), "--model", "claude-sonnet-5-5", "--out", str(root / "out"),
                                "--context-mode", str(root), "--cases", "csv-targets"])
            self.assertEqual(caught.exception.code, 2)
            launch.assert_not_called()
            self.assertFalse((root / "out").exists())


class SnapshotTests(unittest.TestCase):
    def test_synthetic_operator_exception_is_copied_and_recorded_without_changing_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            shared = repository / "skills" / "factory-shared"
            shared.mkdir(parents=True)
            original = shared / "gates.md"
            original.write_text("Original gate rules.\n")
            kit = repository / "kit"
            kit.mkdir()
            (kit / "packs.lock.yaml").write_text("packs:\n")
            superpowers = root / "superpowers"
            (superpowers / ".claude-plugin").mkdir(parents=True)
            (superpowers / ".claude-plugin" / "plugin.json").write_text('{"name":"superpowers"}')
            output = root / "out"
            output.mkdir()
            args = argparse.Namespace(out=output, superpowers=superpowers, context_mode=None)
            with patch("benchmark.ROOT", repository), patch("benchmark.Path.home", return_value=root / "home"), \
                    patch("benchmark.git_info", return_value={"commit": None, "dirty": None}):
                paths, provenance = benchmark.snapshots(args)
            copied = (paths["factory"] / "skills" / "factory-shared" / "gates.md").read_text()
            self.assertEqual(original.read_text(), "Original gate rules.\n")
            self.assertTrue(copied.startswith(original.read_text()))
            self.assertIn("## Synthetic benchmark operator", copied)
            self.assertIn("SIMULATED USER ANSWER", copied)
            self.assertIn("including in fresh step agents", copied)
            self.assertIn("Stop at every unanswered question", copied)
            marker = "skills/factory-shared/gates.md: synthetic-operator exception"
            self.assertIn(marker, provenance["adaptations"]["files"])
            self.assertIn(marker, json.loads((output / "provenance.json").read_text())["adaptations"]["files"])


class RegradeTests(unittest.TestCase):
    def saved_run(self, root, *, final_quality=None):
        out = root / "saved-run"
        case = out / "case-snapshots" / "csv-targets"
        artifact = out / "trials" / "csv-targets-factory-1"
        shutil.copytree(benchmark.CASES / "csv-targets", case, ignore=benchmark.IGNORED)
        shutil.copytree(case / "fixture", artifact / "workspace", ignore=benchmark.IGNORED)
        shutil.copy2(case / "oracle" / "targets.py", artifact / "workspace" / "targets.py")
        record = {"id": artifact.name, "case": case.name, "case_sha256": benchmark.tree_hash(case),
                  "status": "accepted" if final_quality else "incomplete", "initial_quality": {"accepted": False},
                  "final_quality": final_quality, "tokens": 20 if final_quality else None,
                  "cost_usd": 0.2 if final_quality else None, "time_to_first_result_seconds": None,
                  "time_to_accepted_seconds": None, "workflow_complete": False,
                  "measurement_valid": False, "comparative_valid": False, "manual_followup": None}
        benchmark.write_json(artifact / "result.json", record)
        benchmark.write_json(out / "summary.json", {"model": "claude-sonnet-5-5", "trials": [record], "provenance": {}})
        return out, artifact, case, record

    def test_incomplete_snapshot_pass_preserves_delivery_and_cumulative_lower_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            out, artifact, _, original = self.saved_run(Path(temporary))
            for turn, multiplier in enumerate([1, 2]):
                event = {"type": "result", "total_cost_usd": multiplier / 10, "modelUsage": {"claude-sonnet-5-5": {
                    "inputTokens": multiplier, "outputTokens": multiplier * 2,
                    "cacheReadInputTokens": multiplier * 3, "cacheCreationInputTokens": multiplier * 4}}}
                (artifact / f"turn-{turn:02d}.jsonl").write_text(json.dumps(event) + "\ntruncated-json\n")
            with patch("benchmark.invoke", side_effect=AssertionError("regrade must not run a model")) as model, \
                    patch("benchmark.report") as report:
                benchmark.regrade(out)
            regraded = json.loads((artifact / "result.json").read_text())
            self.assertTrue(regraded["snapshot_quality"]["accepted"])
            self.assertEqual(regraded["status"], "incomplete")
            self.assertEqual(regraded["initial_quality"], original["initial_quality"])
            self.assertIsNone(regraded["final_quality"])
            self.assertIsNone(regraded["time_to_first_result_seconds"])
            self.assertIsNone(regraded["time_to_accepted_seconds"])
            self.assertFalse(regraded["workflow_complete"])
            self.assertFalse(regraded["comparative_valid"])
            self.assertIsNone(regraded["manual_followup"])
            self.assertIsNone(regraded["tokens"])
            self.assertIsNone(regraded["cost_usd"])
            self.assertEqual(regraded["tokens_lower_bound"], 20)
            self.assertEqual(regraded["cost_usd_lower_bound"], 0.2)
            self.assertEqual(regraded["observed_token_classes"]["cacheReadInputTokens"], 6)
            model.assert_not_called()
            report.assert_called_once()

    def test_existing_final_grade_is_retained_without_reexecuting_tests(self):
        with tempfile.TemporaryDirectory() as temporary:
            final = {"accepted": True, "tests": 12, "failures": 0, "errors": 0, "skipped": 0}
            out, artifact, _, original = self.saved_run(Path(temporary), final_quality=final)
            with patch("benchmark.grade", side_effect=AssertionError("retain the final trusted grade")) as grade, \
                    patch("benchmark.invoke", side_effect=AssertionError("regrade must not run a model")) as model, \
                    patch("benchmark.report"):
                benchmark.regrade(out)
            regraded = json.loads((artifact / "result.json").read_text())
            self.assertEqual(regraded["snapshot_quality"], final)
            for field in ["initial_quality", "final_quality", "status", "tokens", "cost_usd"]:
                self.assertEqual(regraded[field], original[field])
            self.assertNotIn("tokens_lower_bound", regraded)
            grade.assert_not_called()
            model.assert_not_called()

    def test_interrupted_repair_grades_latest_snapshot_and_preserves_delivery_score(self):
        with tempfile.TemporaryDirectory() as temporary:
            failed = {"accepted": False, "tests": 9, "failures": 1, "errors": 0, "skipped": 0}
            out, artifact, _, record = self.saved_run(Path(temporary), final_quality=failed)
            record.update(status="incomplete", tokens=None, cost_usd=None, repair_rounds=1)
            benchmark.write_json(out / "summary.json", {"model": "claude-sonnet-5-5", "trials": [record], "provenance": {}})
            with patch("benchmark.report"), patch("benchmark.invoke", side_effect=AssertionError("no model run")):
                benchmark.regrade(out)
            regraded = json.loads((artifact / "result.json").read_text())
            self.assertTrue(regraded["snapshot_quality"]["accepted"])
            self.assertEqual(regraded["final_quality"], failed)
            self.assertEqual(regraded["status"], "incomplete")

    def test_changed_case_is_refused_before_grading_or_result_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            out, artifact, case, _ = self.saved_run(Path(temporary))
            original_result = (artifact / "result.json").read_bytes()
            original_summary = (out / "summary.json").read_bytes()
            (case / "fixture" / "targets.py").write_text("# changed grading input\n")
            with patch("benchmark.grade") as grade, patch("benchmark.invoke") as model, \
                    patch("benchmark.report") as report, self.assertRaisesRegex(ValueError, "grading inputs changed"):
                benchmark.regrade(out)
            grade.assert_not_called()
            model.assert_not_called()
            report.assert_not_called()
            self.assertEqual((artifact / "result.json").read_bytes(), original_result)
            self.assertEqual((out / "summary.json").read_bytes(), original_summary)


class ControllerTests(unittest.TestCase):
    def test_fixed_policy_does_not_adopt_bad_recommendation(self):
        answer = {"question": "Choose a storage backend?", "recommended_answer": "Install cloud DB"}
        config = {"mode": "discovery", "operator": "policy", "policy": {
            "persona": "Offline owner", "answers": [{"match": "storage", "answer": "Use local storage"}]}}
        self.assertEqual(benchmark.operator_answer(config, answer), "Use local storage")
        with self.assertRaisesRegex(ValueError, "no fixed policy answer"):
            benchmark.operator_answer(config, {"question": "Unspecified choice?", "recommended_answer": "Approve everything"})

    def test_comparison_inputs_are_required(self):
        with self.assertRaisesRegex(ValueError, "approved spec"):
            benchmark.comparison_inputs(argparse.Namespace(comparison_mode="execution", approved_spec=None,
                                                          operator="policy", operator_policy=None))
        with self.assertRaisesRegex(ValueError, "operator policy"):
            benchmark.comparison_inputs(argparse.Namespace(comparison_mode="discovery", approved_spec=None,
                                                          operator="policy", operator_policy=None))

    def test_context_observability_deduplicates_actual_tool_ids(self):
        call = {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "one", "name": "mcp__ctx_execute"}]}}
        result = benchmark.context_usage([call, call, {"type": "system", "subtype": "hook_response"}], True)
        self.assertTrue(result["enabled"] and result["used"])
        self.assertEqual(result["deduplicated_tool_call_count"], 1)
        self.assertEqual(len(result["hook_responses"]), 1)
        self.assertFalse(benchmark.context_usage([], True)["used"])

    def test_timeout_retains_runtime_and_resume_progress_without_rebuilding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugin"
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin/plugin.json").write_text('{"name":"factory"}')
            args = argparse.Namespace(out=root / "out", timeout=60, budget_usd=5, max_questions=1, repair_rounds=0,
                                      claude="unused", model="claude-sonnet-5-5")
            args.out.mkdir()
            init = {"type": "system", "subtype": "init", "model": args.model, "plugins": [{"name": "factory"}], "mcp_servers": []}
            def interrupted(cmd, work, artifact, timeout):
                (work / "dirty.txt").write_text("unfinished")
                return {"returncode": -9 if "--init-only" not in cmd else 0,
                        "timeout": "--init-only" not in cmd, "seconds": 0.1, "events": [init], "interrupted": False}
            with patch("benchmark.invoke", side_effect=interrupted):
                first = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, {"factory": plugin})
            artifact = args.out / "trials" / first["id"]
            self.assertTrue((artifact / "workspace/.git").is_dir())
            self.assertEqual((artifact / "workspace/dirty.txt").read_text(), "unfinished")
            self.assertEqual(first["progress"][0]["stage"], "interrupted")
            self.assertIsNone(first["progress"][0]["usage"]["tokens"])
            args.resume_trial = True
            complete = {"type": "result", "structured_output": {"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"}}
            quality = {"accepted": True, "tests": 1, "failures": 0, "errors": 0, "skipped": 0}
            calls = []
            def resumed(cmd, work, artifact, timeout):
                calls.append(cmd)
                self.assertEqual((work / "dirty.txt").read_text(), "unfinished")
                return {"returncode": 0, "timeout": False, "seconds": 0.1, "events": [init, complete]}
            with patch("benchmark.invoke", side_effect=resumed), patch("benchmark.grade", return_value=(quality, "pass")):
                final = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, {"factory": plugin})
            self.assertEqual(final["session_id"], first["session_id"])
            self.assertEqual(final["runtime_root"], first["runtime_root"])
            self.assertIn("--resume", calls[-1])
            self.assertEqual(len(final["progress"]), 2)
            self.assertEqual(final["status"], "accepted")
            self.assertTrue(list(artifact.glob("workspace-before-resume-*")))
            shutil.rmtree(first["runtime_root"])

    def test_detached_red_retains_git_dirty_state_and_separate_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work, artifact = root / "work", root / "trials/demo"
            work.mkdir()
            artifact.mkdir(parents=True)
            def git(*cmd):
                return subprocess.run(["git", "-C", str(work), *cmd], check=True, capture_output=True, text=True).stdout.strip()
            git("init", "-q", "-b", "factory/demo")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            git("config", "commit.gpgsign", "false")
            (work / "app.py").write_text("RED")
            git("add", ".")
            git("commit", "-qm", "RED checkpoint")
            red = git("rev-parse", "HEAD")
            (work / "app.py").write_text("GREEN")
            git("commit", "-qam", "GREEN implementation")
            green = git("rev-parse", "HEAD")
            git("checkout", "--detach", red)
            (work / "dirty.txt").write_text("unfinished")
            record = {}
            benchmark.retain_workspace(work, artifact, record)
            self.assertTrue((artifact / "workspace/.git").is_dir())
            self.assertEqual((artifact / "workspace/dirty.txt").read_text(), "unfinished")
            self.assertEqual(record["checkout"]["head"], red)
            self.assertIsNone(record["checkout"]["branch"])
            self.assertEqual((artifact / "source/app.py").read_text(), "RED")
            self.assertEqual((artifact / "committed-source/app.py").read_text(), "GREEN")
            self.assertEqual(record["committed_checkpoint"]["head"], green)
            self.assertEqual(git("rev-parse", "HEAD"), red)
            record["committed_checkpoint_quality"] = {"accepted": True}
            record["snapshot_quality"] = {"accepted": False}
            benchmark.retain_workspace(work, artifact, record)
            self.assertNotIn("committed_checkpoint_quality", record)
            self.assertNotIn("snapshot_quality", record)
            self.assertEqual((artifact / "committed-source/app.py").read_text(), "GREEN")
            git("checkout", "factory/demo")
            benchmark.retain_workspace(work, artifact, record)
            self.assertNotIn("committed_checkpoint", record)
            self.assertFalse((artifact / "committed-source").exists())
            git("checkout", "--detach", red)
            benchmark.retain_workspace(work, artifact, record)
            record.update(id="demo", case="csv-targets", arm="factory", repeat=1, status="incomplete",
                          case_sha256=benchmark.tree_hash(benchmark.CASES / "csv-targets"), tokens=None,
                          cost_usd=None, initial_quality=None, final_quality=None, repair_rounds=0,
                          time_to_first_result_seconds=None, wall_seconds=1, simulated_question_count=0,
                          workflow_complete=False, measurement_valid=False, comparative_valid=False)
            (root / "summary.json").write_text(json.dumps({"model": "test", "trials": [record], "provenance": {}}))
            def grade(case, product, output):
                return {"accepted": (product / "app.py").read_text() == "GREEN"}, "checkpoint grading"
            with patch("benchmark.grade", side_effect=grade):
                benchmark.regrade(root)
            regraded = json.loads((root / "summary.json").read_text())["trials"][0]
            self.assertFalse(regraded["snapshot_quality"]["accepted"])
            self.assertTrue(regraded["committed_checkpoint_quality"]["accepted"])
            self.assertEqual(regraded["status"], "incomplete")

    def test_protocol_json_accepts_one_fenced_block_with_outside_prose(self):
        protocol = {"state": "question", "question": "Approve the plan?", "recommended_answer": "Approve", "summary": "Plan ready"}
        body = json.dumps(protocol)
        for text in [body, f"```json\n{body}\n```", f"The draft is ready.\n\n```json\n{body}\n```\n\nWaiting for your answer.",
                     f"The draft is ready.\r\n```json\r\n{body}\r\n```\r\nWaiting."]:
            with self.subTest(text=text):
                self.assertEqual(benchmark.response([{"type": "result", "result": text}]), protocol)

    def test_protocol_json_rejects_ambiguous_invalid_and_provisional_responses(self):
        protocol = {"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"}
        block = "```json\n" + json.dumps(protocol) + "\n```"
        invalid = [block + "\n" + block, block + "\n```json\n{broken}\n```", "```json\n{broken}\n```",
                   "```json\n" + json.dumps(protocol), "Waiting for the subagent to finish.", None, 42,
                   json.dumps({**protocol, "state": "waiting"}), json.dumps({**protocol, "state": []}),
                   json.dumps({**protocol, "summary": None}), json.dumps({"state": "complete"})]
        for text in invalid:
            with self.subTest(text=text):
                self.assertIsNone(benchmark.response([{"type": "result", "result": text}]))
        child = {"type": "result", "parent_tool_use_id": "child", "result": block}
        self.assertIsNone(benchmark.response([child]))
        self.assertIsNone(benchmark.response([{"type": "result", "result": "Waiting for review."}, child]))
        self.assertIsNone(benchmark.response([{"type": "result", "is_error": True, "result": block}]))

    def test_report_distinguishes_unknown_usage_from_observed_lower_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            record = {"case": "csv-targets", "arm": "factory", "repeat": 1, "initial_quality": None,
                      "final_quality": None, "repair_rounds": 0, "tokens": None, "cost_usd": None,
                      "time_to_first_result_seconds": None, "wall_seconds": 1, "simulated_question_count": 0,
                      "workflow_complete": False, "measurement_valid": False, "comparative_valid": False}
            benchmark.report(argparse.Namespace(out=out, model="claude-sonnet-5-5"), [record], {})
            text = (out / "report.md").read_text()
            self.assertIn("| unknown | unknown |", text)
            self.assertNotIn(">=None", text)
            record.update(tokens_lower_bound=0, cost_usd_lower_bound=0.25)
            benchmark.report(argparse.Namespace(out=out, model="claude-sonnet-5-5"), [record], {})
            self.assertIn("| >=0 | >=0.25 |", (out / "report.md").read_text())

    def test_arm_order_alternates(self):
        self.assertEqual(benchmark.arm_order(0), ["factory", "superpowers"])
        self.assertEqual(benchmark.arm_order(1), ["superpowers", "factory"])
        self.assertEqual(benchmark.arm_order(1, True), ["factory-context", "superpowers", "factory"])

    def test_process_timeout_kills_group_and_launch_error_is_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = benchmark.invoke([sys.executable, "-c", "import time; time.sleep(30)"], root, root / "timeout", 0.05)
            self.assertTrue(run["timeout"])
            self.assertEqual(run["returncode"], -9)
            with patch("benchmark.subprocess.Popen", side_effect=FileNotFoundError("missing CLI")):
                run = benchmark.invoke(["missing"], root, root / "missing", 1)
                self.assertIsNone(run["returncode"])
                self.assertIn("missing CLI", run["error"])

    def test_root_result_finishes_turn_even_if_process_stays_alive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = "import json,time; print(json.dumps({'type':'result','subtype':'success','is_error':False,'structured_output':{'state':'question','question':'Approve?','recommended_answer':'Approve','summary':'Ready'}}),flush=True); time.sleep(30)"
            run = benchmark.invoke([sys.executable, "-c", script], root, root / "terminal", 5)
            self.assertFalse(run["timeout"])
            self.assertEqual(run["returncode"], 0)
            self.assertLess(run["seconds"], 3)
            self.assertEqual(run["events"][-1]["type"], "result")

    def test_forwarded_subagent_result_does_not_finish_root_turn(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = "import json,time; print(json.dumps({'type':'result','subtype':'success','parent_tool_use_id':'child'}),flush=True); time.sleep(30)"
            run = benchmark.invoke([sys.executable, "-c", script], root, root / "child", 0.1)
            self.assertTrue(run["timeout"])

    def test_structured_response_and_isolation(self):
        response = {"state": "question", "question": "Approve?", "recommended_answer": "Approve", "summary": "Ready"}
        self.assertEqual(benchmark.response([{"type": "result", "structured_output": response}]), response)
        self.assertIsNone(benchmark.response([{"type": "result", "result": "I am done"}]))
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary)
            (plugin / ".claude-plugin").mkdir()
            (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"factory"}')
            init = {"type": "system", "subtype": "init", "plugins": [{"name": "factory"}, {"name": "cc-plugin-telemetry"}], "mcp_servers": []}
            self.assertTrue(benchmark.isolation([init], [plugin])["verified"])
            init["plugins"].append({"name": "unrelated-plugin"})
            self.assertFalse(benchmark.isolation([init], [plugin])["verified"])
            self.assertFalse(benchmark.isolation([], [plugin])["verified"])

    def test_manifest_mcp_namespace_and_connected_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary)
            (plugin / ".claude-plugin").mkdir()
            (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"context-mode","mcpServers":{"context-mode":{}}}')
            init = {"type": "system", "subtype": "init", "plugins": [{"name": "context-mode"}],
                    "mcp_servers": [{"name": "plugin:context-mode:context-mode", "status": "connected"}]}
            self.assertTrue(benchmark.isolation([init], [plugin])["verified"])
            init["mcp_servers"][0]["name"] = "plugin_context-mode_context-mode"
            self.assertTrue(benchmark.isolation([init], [plugin])["verified"])
            init["mcp_servers"][0]["status"] = "failed"
            self.assertFalse(benchmark.isolation([init], [plugin])["verified"])
            init["mcp_servers"] = []
            self.assertFalse(benchmark.isolation([init], [plugin])["verified"])

    def test_failed_preflight_can_resume_with_persisted_initial_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = root / "factory"
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin/plugin.json").write_text('{"name":"factory"}')
            args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5, max_questions=1,
                                      repair_rounds=0, claude="claude", model="claude-sonnet-5-5")
            args.out.mkdir()
            paths = {"factory": plugin}
            failed = {"returncode": 1, "timeout": False, "seconds": 0.1, "events": []}
            complete = {"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"}
            good = {"returncode": 0, "timeout": False, "seconds": 0.1, "events": []}
            delivered = {**good, "events": [{"type": "result", "structured_output": complete}]}
            quality = {"accepted": True, "tests": 9, "failures": 0, "errors": 0, "skipped": 0}
            with patch("benchmark.invoke", return_value=failed), patch("benchmark.grade", return_value=(quality, "")):
                first = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
            artifact = args.out / "trials/csv-targets-factory-1"
            saved = json.loads((artifact / "progress.json").read_text())
            self.assertIn("same neutral requirements", saved["pending_prompt"])
            self.assertEqual(first["stop_reason"], "preflight failed")
            benchmark.write_json(args.out / "run-config.json", {"args": {**vars(args), "out": str(args.out)},
                                                               "paths": {"factory": str(plugin)}})
            benchmark.write_json(args.out / "summary.json", {"model": args.model, "trials": [first], "provenance": {}})
            with patch("benchmark.report"):
                benchmark.main(["followup", "--out", str(args.out), "--trial", first["id"], "--seconds", "42", "--rounds", "2"])
            measured = json.loads((artifact / "progress.json").read_text())["manual_followup"]
            self.assertEqual(measured["seconds"], 42)
            args.resume_trial = True
            with patch("benchmark.invoke", side_effect=[good, delivered]) as invoke, patch("benchmark.grade", return_value=(quality, "")):
                resumed = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
            self.assertEqual(resumed["status"], "accepted")
            self.assertEqual(resumed["manual_followup"], measured)
            self.assertIn(saved["pending_prompt"], invoke.call_args_list[-1].args[0])
            shutil.rmtree(resumed["runtime_root"])

    def test_trial_question_resume_and_repair_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = root / "factory"
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"factory"}')
            args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5, max_questions=1, repair_rounds=1,
                                      claude="claude", model="claude-sonnet-5-5")
            args.out.mkdir()
            paths = {"factory": plugin}
            init = {"type": "system", "subtype": "init", "model": args.model, "plugins": [{"name": "factory"}], "mcp_servers": []}
            question = {"state": "question", "question": "Approve local plan?", "recommended_answer": "Approve this plan", "summary": "Plan ready"}
            complete = {"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"}
            responses = [[], [init, {"type": "result", "structured_output": question}],
                         [{"type": "result", "structured_output": complete}], [{"type": "result", "structured_output": complete}]]
            calls = []

            def fake_invoke(cmd, work, artifact, timeout):
                calls.append(cmd)
                return {"returncode": 0, "timeout": False, "seconds": 0.1, "events": responses.pop(0)}

            quality = {"accepted": False, "tests": 3, "failures": 1, "errors": 0, "skipped": 0}
            with patch("benchmark.invoke", side_effect=fake_invoke), patch("benchmark.grade", return_value=(quality, "same failing test feedback")):
                result = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
            self.assertEqual(result["repair_rounds"], 1)
            self.assertEqual(result["simulated_question_count"], 1)
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(len(calls), 4)
            self.assertIn("--session-id", calls[1])
            self.assertIn("--resume", calls[2])
            self.assertEqual(calls[1][calls[1].index("--session-id") + 1], calls[2][calls[2].index("--resume") + 1])
            self.assertIn("SIMULATED USER ANSWER", calls[2][-1])
            self.assertIn("same failing test feedback", calls[3][-1])
            self.assertIsNone(result["manual_followup"])
            self.assertIsNotNone(result["time_to_first_result_seconds"])
            self.assertFalse(result["comparative_valid"])

    def test_browser_blocker_gets_one_scoped_reminder_then_stops(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/module"}):
            root = Path(temporary)
            plugin = root / "factory"
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin/plugin.json").write_text('{"name":"factory"}')
            runtime = {"command": str(root / "browser-check"), "profile": str(root / "sandbox.sb"), "sha256": {}}
            for key in ["command", "profile"]:
                Path(runtime[key]).write_text("fixed")
                runtime["sha256"][key] = benchmark.hashlib.sha256(b"fixed").hexdigest()
            args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5, max_questions=1, repair_rounds=1,
                                      claude="claude", model="claude-sonnet-5-5")
            args.out.mkdir()
            init = {"type": "system", "subtype": "init", "model": args.model, "plugins": [{"name": "factory"}], "mcp_servers": []}
            blocked = {"state": "blocked", "question": "", "recommended_answer": "", "summary": "wrapper failed"}
            responses = [[], [init, {"type": "result", "structured_output": blocked}],
                         [{"type": "result", "structured_output": blocked}]]
            calls = []

            def fake_invoke(cmd, work, artifact, timeout):
                calls.append(cmd)
                return {"returncode": 0, "timeout": False, "seconds": 0.1, "events": responses.pop(0)}

            with patch("browser_runtime.prepare_browser_check", return_value=runtime), \
                    patch("benchmark.invoke", side_effect=fake_invoke):
                result = benchmark.trial(args, benchmark.CASES / "support-dashboard", "factory", 0, {"factory": plugin})
            self.assertEqual(result["environment_recovery_rounds"], 1)
            self.assertEqual(result["repair_rounds"], 0)
            self.assertEqual(result["stop_reason"], "wrapper failed")
            self.assertEqual(len(calls), 3)
            self.assertIn(runtime["command"], calls[-1][-1])
            self.assertIn("Do not weaken any sandbox", calls[-1][-1])


class CommandTests(unittest.TestCase):
    def test_blind_browser_review_copies_images_and_preserves_labels_and_notes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trial = root / "trials/demo"
            (trial / "source").mkdir(parents=True)
            (trial / "source/index.html").write_text("Product")
            (trial / "desktop.png").write_bytes(b"image")
            quality = {"accepted": True, "screenshots": {"desktop": str(trial / "desktop.png")}}
            record = {"id": "demo", "case": "support-dashboard", "arm": "factory", "repeat": 1,
                      "initial_quality": quality, "final_quality": quality, "repair_rounds": 0,
                      "tokens": 1, "cost_usd": 0.1, "time_to_first_result_seconds": 1,
                      "wall_seconds": 1, "simulated_question_count": 0, "workflow_complete": True,
                      "measurement_valid": True, "comparative_valid": False}
            args = argparse.Namespace(out=root, model="claude-sonnet-5-5")
            benchmark.report(args, [record], {}, blind=True)
            self.assertEqual((root / "blind-review/submission-001/desktop.png").read_bytes(), b"image")
            key = (root / "blind-review-key.json").read_bytes()
            notes = root / "blind-review/review.md"
            notes.write_text("My human review notes")
            (trial / "mobile.png").write_bytes(b"later snapshot")
            quality["screenshots"]["mobile"] = str(trial / "mobile.png")
            benchmark.report(args, [record], {}, blind=True)
            self.assertEqual((root / "blind-review/submission-001/mobile.png").read_bytes(), b"later snapshot")
            self.assertEqual(notes.read_text(), "My human review notes")
            self.assertEqual((root / "blind-review-key.json").read_bytes(), key)

    def test_browser_only_allows_local_network_and_installed_runtime_reads(self):
        with patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/installed/playwright"}):
            config = benchmark.settings(Path("/work"), {"factory": Path("/factory")}, "factory", Path("/out"),
                                        browser=True, browser_command="/immutable/browser-check", red_command="/immutable/browser-check-red")
        self.assertEqual(config["sandbox"]["network"]["allowedDomains"], ["127.0.0.1", "localhost"])
        self.assertTrue(config["sandbox"]["network"]["strictAllowlist"])
        self.assertIn("Read(//installed/playwright/**)", config["permissions"]["allow"])
        self.assertIn("Edit(//installed/playwright/**)", config["permissions"]["deny"])
        self.assertIn("Bash", config["permissions"]["allow"])
        self.assertIn("Bash(/immutable/browser-check)", config["permissions"]["allow"])
        self.assertIn("Bash(/immutable/browser-check-red)", config["permissions"]["allow"])
        prompt = benchmark.initial_prompt(benchmark.CASES / "support-dashboard", "factory",
                                          {"factory": Path("/factory")}, "/immutable/browser-check", "/immutable/browser-check-red")
        self.assertIn("Set status red_test_command to /immutable/browser-check-red", prompt)
        self.assertIn('"commit":"FULL_40_CHARACTER_ANCESTOR_COMMIT_SHA"', prompt)
        self.assertNotIn("kit/runtime.py browser-red-request", prompt)
        self.assertIn("worktrees are permitted only under this workspace’s .tmp", prompt)
        self.assertEqual(config["sandbox"]["excludedCommands"], ["/immutable/browser-check", "/immutable/browser-check-red"])
        self.assertFalse(config["sandbox"]["allowUnsandboxedCommands"])
        self.assertIn("/immutable", config["sandbox"]["filesystem"]["denyWrite"])
        self.assertIn("Edit(//immutable/**)", config["permissions"]["deny"])

    def test_browser_product_snapshot_keeps_assets_and_data_without_generated_tests(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            names = ["index.html", "styles.css", "app.js", "tickets.json", "logo.svg"]
            for name in [*names, "test_generated.cjs", "test_existing.cjs"]:
                (work / name).write_text(name)
            benchmark.copy_product(work, root / "source", source_only=True)
            self.assertEqual(sorted(path.name for path in (root / "source").iterdir()), sorted(names))

    def test_browser_oracle_can_write_artifacts_under_home(self):
        with tempfile.TemporaryDirectory(prefix="factory-grade-home-", dir=Path.home()) as output, tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = benchmark.CASES / "support-dashboard"
            work = root / "work"
            shutil.copytree(case / "fixture", work)
            shutil.copytree(case / "oracle", work, dirs_exist_ok=True)
            artifact = Path(output) / "nested/grade"
            quality, text = benchmark.grade(case, work, artifact)
            self.assertTrue(quality["accepted"], text)
            self.assertEqual(quality["tests"], 21)
            self.assertTrue((artifact / "desktop.png").is_file())
            self.assertTrue((artifact / "mobile.png").is_file())

    def test_browser_grader_uses_trusted_script_and_fixed_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = root / "case"
            (case / "grading").mkdir(parents=True)
            (case / "case.json").write_text('{"kind":"browser","test_count":2}')
            trusted = case / "grading/browser_acceptance.cjs"
            trusted.write_text('console.log(\'BENCHMARK_GRADE={"tests":2,"failures":0,"errors":0,"skipped":0}\');')
            work = root / "work"
            work.mkdir()
            (work / "index.html").write_text("<h1>Product</h1>")
            (work / "test_generated.cjs").write_text("throw Error('must not run');")
            quality, _ = benchmark.grade(case, work, root / "grade")
            self.assertTrue(quality["accepted"])
            self.assertEqual(quality["tests"], 2)
            trusted.write_text('console.log(\'BENCHMARK_GRADE={"tests":0,"failures":0,"errors":0,"skipped":0}\');')
            quality, _ = benchmark.grade(case, work, root / "zero-grade")
            self.assertFalse(quality["accepted"])

    def test_only_context_arm_loads_adapted_mcp_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary) / "context-plugin"
            (plugin / ".claude-plugin").mkdir(parents=True)
            manifest = {"name": "context-mode", "mcpServers": {"context-mode": {
                "command": "/usr/bin/sandbox-exec", "args": ["-f", "/policy", "node", "${CLAUDE_PLUGIN_ROOT}/start.mjs"],
                "env": {"CLAUDE_CONFIG_DIR": "/isolated/config"}}}}
            (plugin / ".claude-plugin/plugin.json").write_text(json.dumps(manifest))
            paths = {"factory": Path("/factory"), "superpowers": Path("/superpowers"), "context-mode": plugin}
            args = argparse.Namespace(claude="claude", model="claude-sonnet-5-5")
            for arm in ["factory", "superpowers", "factory-context"]:
                cmd = benchmark.command(args, paths, arm, "/config", "session", False, 5, "prompt")
                servers = json.loads(cmd[cmd.index("--mcp-config") + 1])["mcpServers"]
                allowed = benchmark.settings(Path("/work"), paths, arm, Path("/out"))["permissions"]["allow"]
                if arm == "factory-context":
                    self.assertEqual(servers["plugin_context-mode_context-mode"]["args"][-1], str(plugin / "start.mjs"))
                    self.assertEqual(servers["plugin_context-mode_context-mode"]["env"]["CLAUDE_PLUGIN_ROOT"], str(plugin))
                    self.assertEqual(servers["plugin_context-mode_context-mode"]["env"]["CLAUDE_CONFIG_DIR"], "/isolated/config")
                    self.assertIn("mcp__plugin_context-mode_context-mode__*", allowed)
                else:
                    self.assertEqual(servers, {})
                    self.assertNotIn("mcp__plugin_context-mode_context-mode__*", allowed)
            self.assertEqual(json.loads((plugin / ".claude-plugin/plugin.json").read_text()), manifest)


if __name__ == "__main__":
    unittest.main()
