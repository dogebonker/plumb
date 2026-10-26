import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

import benchmark


class ClaudeCommandTests(unittest.TestCase):
    def test_unlimited_actor_omits_caps_on_initial_and_resume(self):
        args = argparse.Namespace(claude="claude", model="model", until_complete=True, effort="low")
        for resume in (False, True):
            cmd = benchmark.command(args, {"factory": Path("factory")}, "factory", Path("settings"), "session", resume, -1)
            self.assertNotIn("--max-turns", cmd)
            self.assertNotIn("--max-budget-usd", cmd)
            self.assertEqual(cmd[cmd.index("--effort") + 1], "low")

    def test_context_trial_protects_custom_operator_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = argparse.Namespace(out=root / "out", model="model", operator_policy=str(root / "external-policy.json"))
            Path(args.operator_policy).write_text('{"persona":"Operator","answers":[]}')
            paths = {name: root / name for name in ("factory", "superpowers", "context-mode")}
            with patch("benchmark.prepare_context", side_effect=ValueError("stop before invocation")) as prepare, \
                    self.assertRaisesRegex(ValueError, "stop before invocation"):
                benchmark.trial(args, benchmark.CASES / "csv-targets", "factory-context", 0, paths)
            protected = prepare.call_args.args[3]
            for secret in benchmark.secret_files(args.out, benchmark.policy_files(args)):
                self.assertIn(secret, protected)
            self.assertIn(args.out / "case-snapshots", protected)
            self.assertIn(args.out / "trials", protected)

    def test_bounded_defaults_and_adapter_effort(self):
        args = argparse.Namespace(claude="claude", model="model")
        cmd = benchmark.command(args, {"factory": Path("factory")}, "factory", Path("settings"), "session", False, 5)
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "60")
        self.assertEqual(cmd[cmd.index("--max-budget-usd") + 1], "5")
        self.assertEqual(cmd[cmd.index("--effort") + 1], "high")
        args.until_complete, args.effort = True, "medium"
        cmd = benchmark.command(args, {}, "adapter", Path("settings"), "session", False, 5)
        self.assertNotIn("--max-turns", cmd)
        self.assertIn("--max-budget-usd", cmd)
        self.assertEqual(cmd[cmd.index("--effort") + 1], "medium")


class CodexIntegrationTests(unittest.TestCase):
    def test_unlimited_invocation_does_not_read_controller_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = ("import json,sys,time; assert sys.stdin.read()==''; time.sleep(.15); "
                      "print(json.dumps({'type':'turn.completed','usage':{}}))")
            run = benchmark.invoke([sys.executable, "-c", script], root, root / "turn", None)
            self.assertEqual(run["returncode"], 0)
            self.assertFalse(run["timeout"])
            self.assertEqual(run["events"][-1]["type"], "turn.completed")

    def test_only_completed_root_agent_message_is_structured_response(self):
        message = json.dumps({"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"})
        raw = [{"type": "thread.started", "thread_id": "actual-id"},
               {"type": "item.completed", "item": {"type": "agent_message", "text": "Intermediate"}},
               {"type": "item.completed", "item": {"type": "command_execution", "text": message}},
               {"type": "item.completed", "item": {"type": "agent_message", "text": message}},
               {"type": "turn.completed", "usage": {"input_tokens": 99}}]
        adapted, session = benchmark.codex_events(raw)
        self.assertEqual(session, "actual-id")
        self.assertEqual(benchmark.response(adapted)["summary"], "Done")
        self.assertEqual(raw[-1]["type"], "turn.completed")
        self.assertIsNone(benchmark.response(benchmark.codex_events(raw[:-1])[0]))
        self.assertIsNone(benchmark.response(benchmark.codex_events(raw + [{"type": "turn.failed"}])[0]))

    def test_codex_browser_surface_uses_only_declared_mcp_capabilities(self):
        prompt = benchmark.codex_prompt(benchmark.CASES / "support-dashboard", "factory",
                                        {"factory": Path("/factory"), "superpowers": Path("/superpowers")},
                                        "/immutable/check", "/immutable/red")
        self.assertIn("mcp__benchmark_browser__check with zero arguments", prompt)
        self.assertIn("mcp__benchmark_browser__red_check with zero arguments", prompt)
        self.assertIn("Never run /immutable/check or /immutable/red through the shell", prompt)
        self.assertIn("Pass this mapping to every child", prompt)
        paths = {"factory": Path("/factory"), "superpowers": Path("/superpowers")}
        pinned = {("initial_prompt", "factory"): "e4d7a8a1e94fba3dc8122c90d0062e41b83f8ba8c6be0cbe3c4a16fc6e652d1b",
                  ("initial_prompt", "superpowers"): "5303eabe788f593fd826abb6fe1c3460ca7512f07be377d2cb9ed31a3963dce3",
                  ("codex_prompt", "factory"): "e1324fd2ace8830270d9ce0b620d93eb655d3dabac544459ec292ed8a19aaf46",
                  ("codex_prompt", "superpowers"): "3e45a3541c785a872614d2b2e29c2d4baddcc9e1ec788ca4a5bb1db482358c80"}
        for (name, arm), digest in pinned.items():
            build = getattr(benchmark, name)
            text = build(benchmark.CASES / "support-fullstack", arm, paths, "/immutable/check", "/immutable/red")
            self.assertEqual(benchmark.hashlib.sha256(text.encode()).hexdigest(), digest, f"{name}/{arm} changed for a non-discovery case")
            text = build(benchmark.CASES / "gloam-chat", arm, paths, "/immutable/check", "/immutable/red")
            for coaching in ("same neutral requirements", "DECISIONS.md", "FR/NFR", "negotiated away", "for fixture checks"):
                self.assertNotIn(coaching, text, f"{name}/{arm} coaches a discovery arm")
            self.assertIn((benchmark.CASES / "gloam-chat" / "task.md").read_text(), text)

    def test_codex_unknown_coverage_is_not_free(self):
        record = benchmark.codex_accounting({"accounting_complete": False, "totals": {"input_tokens": 9}, "modeled_api_usd": None})
        self.assertIsNone(record["tokens"])
        self.assertIsNone(record["cost_usd"])
        self.assertIsNone(record["actual_invoice_usd"])

    def test_codex_policy_failure_never_invokes_model(self):
        self.run_codex_trial(admission_failure=True)

    def test_codex_until_complete_resumes_actual_thread_and_ignores_repair_cap(self):
        self.run_codex_trial(admission_failure=False)

    def test_factory_product_acceptance_waits_for_reconcile_without_repair_charge(self):
        self.run_codex_trial(admission_failure=False, finishing=True)

    def test_changed_prepared_policy_is_rejected_on_every_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = {name: root / name for name in ("factory", "superpowers")}
            for path in paths.values():
                path.mkdir()
            args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5,
                                      max_questions=0, repair_rounds=0, harness="codex", until_complete=True,
                                      codex="codex", effort="high", model="gpt-6.1-sol")
            args.out.mkdir()
            def prepare(binary, work, runtime, *unused, **kwargs):
                runtime.mkdir()
                prepared = {"binary": "trusted", "isolation_evidence": [{"passed": True}], "limitations": []}
                benchmark.write_json(runtime / "codex-prepared.json", prepared)
                return prepared
            failed = {"returncode": 1, "timeout": False, "seconds": .1, "events": []}
            with patch("codex_adapter.prepare", side_effect=prepare), patch("codex_adapter.command", return_value=["unused"]), patch("benchmark.invoke", return_value=failed):
                first = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
            trusted_hash = first["codex_prepared_sha256"]
            prepared_file = Path(first["runtime_root"]) / "codex/codex-prepared.json"
            changed = json.loads(prepared_file.read_text())
            changed["binary"] = "tampered"
            benchmark.write_json(prepared_file, changed)
            args.resume_trial = True
            for _ in range(2):
                with patch("benchmark.invoke") as invoke, patch("codex_adapter.command") as command:
                    resumed = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
                invoke.assert_not_called()
                command.assert_not_called()
                self.assertEqual(resumed["codex_prepared_sha256"], trusted_hash)
                self.assertFalse(resumed["measurement_valid"])
            shutil.rmtree(first["runtime_root"])

    def test_accepted_product_mutated_during_finish_resume_needs_fresh_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = {name: root / name for name in ("factory", "superpowers")}
            for path in paths.values():
                path.mkdir()
            args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5,
                                      max_questions=0, repair_rounds=0, harness="codex", until_complete=True,
                                      codex="codex", effort="high", model="gpt-6.1-sol")
            args.out.mkdir()
            def prepare(binary, work, runtime, *unused, **kwargs):
                runtime.mkdir()
                prepared = {"binary": "trusted", "isolation_evidence": [{"passed": True}], "limitations": []}
                benchmark.write_json(runtime / "codex-prepared.json", prepared)
                return prepared
            def event(state):
                body = {"state": state, "question": "", "recommended_answer": "", "summary": "Done"}
                return {"returncode": 0, "timeout": False, "seconds": .1, "events": [
                    {"type": "thread.started", "thread_id": "actual-thread"},
                    {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(body)}},
                    {"type": "turn.completed"}]}
            quality = {"accepted": True, "tests": 9, "failures": 0, "errors": 0, "skipped": 0}
            with patch("codex_adapter.prepare", side_effect=prepare), patch("codex_adapter.command", return_value=["unused"]), \
                 patch("codex_adapter.collect_usage", return_value={}), patch("benchmark.invoke", return_value=event("complete")), \
                 patch("benchmark.grade", return_value=(quality, "")):
                first = benchmark.trial(args, benchmark.CASES / "csv-targets", "superpowers", 0, paths)
            self.assertEqual(first["status"], "accepted")
            args.resume_trial = True
            def mutate_and_block(cmd, work, artifact, timeout):
                (work / "targets.py").write_text("raise RuntimeError('unfinished change')")
                return event("blocked")
            with patch("codex_adapter.command", return_value=["unused"]), patch("codex_adapter.collect_usage", return_value={}), \
                 patch("benchmark.invoke", side_effect=mutate_and_block), patch("benchmark.grade") as grade:
                resumed = benchmark.trial(args, benchmark.CASES / "csv-targets", "superpowers", 0, paths)
            grade.assert_not_called()
            self.assertEqual(resumed["status"], "incomplete")
            self.assertIsNone(resumed["final_quality"])
            self.assertIsNone(resumed["manual_workflow_review"])
            self.assertIsNone(resumed["price_per_accepted_application_estimate"])
            self.assertEqual(resumed["initial_quality"], quality)
            self.assertEqual(resumed["acceptance_history"][0]["quality"], quality)
            self.assertEqual(len(resumed["invocations"]), 2)
            self.assertFalse(resumed["workflow_complete"])
            shutil.rmtree(first["runtime_root"])

    def run_codex_trial(self, admission_failure, finishing=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = {name: root / name for name in ("factory", "superpowers")}
            for path in paths.values():
                path.mkdir()
            args = argparse.Namespace(out=root / "output", timeout=.001, budget_usd=.001,
                                      max_questions=0, repair_rounds=0, harness="codex", until_complete=True,
                                      codex="codex", effort="high", model="gpt-6.1-sol")
            args.out.mkdir()
            prepared = {"isolation_evidence": [{"passed": True}], "limitations": []}
            complete = json.dumps({"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"})
            raw = [{"type": "thread.started", "thread_id": "actual-thread"},
                   {"type": "item.completed", "item": {"type": "agent_message", "text": complete}},
                   {"type": "turn.completed"}]
            run = {"returncode": 0, "timeout": False, "seconds": .1, "events": raw}
            quality = {"accepted": True, "tests": 9, "failures": 0, "errors": 0, "skipped": 0}
            usage = {"accounting_complete": True, "totals": {"input_tokens": 100, "output_tokens": 10},
                     "modeled_api_usd": .1, "records": [{"model": args.model, "effort": "high"}], "problems": []}
            with patch("codex_adapter.prepare", side_effect=ValueError("denied") if admission_failure else None, return_value=prepared), \
                 patch("codex_adapter.command", return_value=["codex", "exec"]) as command, \
                 patch("codex_adapter.collect_usage", return_value=usage), \
                 patch("benchmark.invoke", side_effect=[dict(run), dict(run)]) as invoke, \
                 patch("benchmark.grade", side_effect=[(quality if finishing else {**quality, "accepted": False}, "repair"), (quality, "")]), \
                 patch("benchmark.workflow_evidence", side_effect=[{"workflow_complete": False}, {"workflow_complete": True}, {"workflow_complete": True}] if finishing else None, return_value={"workflow_complete": True}):
                record = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
            if admission_failure:
                invoke.assert_not_called()
                self.assertFalse(record["measurement_valid"])
                self.assertEqual(record["stop_reason"], "preflight failed")
            else:
                self.assertEqual(record["status"], "accepted")
                self.assertEqual(record["repair_rounds"], 0 if finishing else 1)
                self.assertEqual(record["workflow_finish_rounds"], 1 if finishing else 0)
                if finishing:
                    self.assertIn("WORKFLOW FINISH REQUEST", command.call_args_list[1].args[1])
                self.assertEqual(command.call_args_list[1].args[2], "actual-thread")
                self.assertEqual(invoke.call_args_list[0].args[3], float("inf"))
                self.assertEqual(record["cost_usd"], .1)
            shutil.rmtree(record["runtime_root"])


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
            if json.loads(case_json.read_text()).get("kind") in {"browser", "fullstack"}:
                continue  # Browser/fullstack baseline and oracle proof lives in check_cases.py.
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
    def framework(self, root):
        repository = root / "repository"
        shared = repository / "skills" / "plumb-shared"
        shared.mkdir(parents=True)
        (shared / "gates.md").write_text("Gate rules.\n")
        (repository / "bin").mkdir()
        shutil.copy2(benchmark.ROOT / "bin" / "plumb-packs-fetch", repository / "bin")
        shutil.copytree(benchmark.ROOT / "hooks", repository / "hooks", ignore=benchmark.IGNORED)
        kit = repository / "kit"
        kit.mkdir()
        name = "a-philosophy-of-software-design"
        staging = root / "book"
        staging.mkdir()
        for tier in ["full", "mini", "nano"]:
            folder = staging / tier
            folder.mkdir()
            (folder / "SKILL.md").write_text(tier + " ~/.plumb/user/ ~/.plumb/packs/\n")
        (staging / "full" / "SKILL.md").chmod(0o755)
        for command in [["init", "-q"], ["add", "-f", "."]]:
            subprocess.run(["git", "-C", str(staging), *command], check=True, capture_output=True)
        pin = subprocess.check_output(["git", "-C", str(staging), "write-tree"], text=True).strip()
        shutil.rmtree(staging / ".git")
        bundle = kit / "packs" / f"{name}@{pin}"
        bundle.parent.mkdir()
        shutil.copytree(staging, bundle)
        (kit / "packs.lock.yaml").write_text(
            f"packs:\n  {name}: {{ source: ciembor/agent-rules-books, path: {name}, hash: {pin} }}\n")
        output = root / "out"
        output.mkdir()
        return repository, bundle, pin, argparse.Namespace(out=output, superpowers=None, context_mode=None)

    def test_book_bundle_available_with_empty_cache_and_unchanged_bytes_and_modes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository, bundle, pin, args = self.framework(root)
            with patch("benchmark.ROOT", repository), patch("benchmark.Path.home", return_value=root / "empty-home") as home:
                paths, provenance = benchmark.snapshots(args)
                home.assert_not_called()  # bundled books never consult global skills or pack caches
            snapshot = paths["factory"]
            for relative in ("hooks/plumb_gate.py", "bin/plumb-packs-fetch"):
                self.assertEqual((snapshot / relative).read_bytes(), (repository / relative).read_bytes())
            self.assertFalse((snapshot / "hooks/hooks.json").exists(), "runtime files must not auto-register gates")
            help_run = subprocess.run([sys.executable, str(snapshot / "hooks/plumb_gate.py"), "repair-check", "--help"],
                                      cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(help_run.returncode, 0, help_run.stderr)
            self.assertIn("--checkpoint {edit,complete}", help_run.stdout)
            fetch = benchmark.runpy.run_path(str(snapshot / "bin/plumb-packs-fetch"))
            self.assertIn("pins", fetch)
            with patch.dict("os.environ", {"HOME": str(root / "empty-home")}):
                fetched = subprocess.run([sys.executable, str(snapshot / "bin/plumb-packs-fetch"),
                                          str(snapshot / "kit/packs.lock.yaml")], cwd=root,
                                         capture_output=True, text=True, check=False)
            self.assertEqual(fetched.returncode, 0, fetched.stderr)
            self.assertIn("bundled", fetched.stdout)
            copied = paths["factory"] / "packs" / bundle.name
            for tier in ["full", "mini", "nano"]:
                original = bundle / tier / "SKILL.md"
                self.assertEqual((copied / tier / "SKILL.md").read_bytes(), original.read_bytes())
                self.assertEqual((paths["factory"] / "kit" / "packs" / bundle.name / tier / "SKILL.md").read_bytes(),
                                 original.read_bytes())
            self.assertEqual((copied / "full" / "SKILL.md").stat().st_mode & 0o777, 0o755)
            entry = provenance["installed_packs"]["a-philosophy-of-software-design"]
            self.assertEqual(entry["source_kind"], "bundled")
            self.assertEqual(entry["pin"], pin)
            self.assertEqual(Path(entry["path"]), bundle)
            self.assertEqual(provenance["skipped_packs"], [])

    def test_required_book_missing_or_corrupt_aborts_preparation(self):
        for defect in ["missing", "changed"]:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repository, bundle, _pin, args = self.framework(root)
                if defect == "missing":
                    shutil.rmtree(bundle)
                else:
                    (bundle / "nano" / "SKILL.md").write_text("corrupt")
                with patch("benchmark.ROOT", repository), patch("benchmark.Path.home", return_value=root / "empty-home"), \
                        self.assertRaisesRegex(ValueError, "book bundle.*a-philosophy-of-software-design"):
                    benchmark.snapshots(args)

    def test_synthetic_operator_exception_is_copied_and_recorded_without_changing_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            shared = repository / "skills" / "plumb-shared"
            shared.mkdir(parents=True)
            original = shared / "gates.md"
            original.write_text("Original gate rules.\n")
            (repository / "bin").mkdir()
            shutil.copy2(benchmark.ROOT / "bin" / "plumb-packs-fetch", repository / "bin")
            shutil.copytree(benchmark.ROOT / "hooks", repository / "hooks", ignore=benchmark.IGNORED)
            kit = repository / "kit"
            kit.mkdir()
            (kit / "packs.lock.yaml").write_text("packs:\n  lens: { source: o/r, path: lens, hash: " + "a" * 40 + " }\n"
                                                 "  gone: { source: o/r, path: gone, hash: " + "b" * 40 + " }\n")
            (shared / "packs.md").write_text("Load `~/.plumb/packs/<name>@<hash>/`.\n")
            cached = root / "home" / ".plumb" / "packs" / ("lens@" + "a" * 40)
            cached.mkdir(parents=True)
            (cached / "SKILL.md").write_text("lens rules\n")
            superpowers = root / "superpowers"
            (superpowers / ".claude-plugin").mkdir(parents=True)
            (superpowers / ".claude-plugin" / "plugin.json").write_text('{"name":"superpowers"}')
            output = root / "out"
            output.mkdir()
            args = argparse.Namespace(out=output, superpowers=superpowers, context_mode=None)
            with patch("benchmark.ROOT", repository), patch("benchmark.Path.home", return_value=root / "home"), \
                    patch("benchmark.git_info", return_value={"commit": None, "dirty": None}):
                paths, provenance = benchmark.snapshots(args)
            copied = (paths["factory"] / "skills" / "plumb-shared" / "gates.md").read_text()
            self.assertEqual(original.read_text(), "Original gate rules.\n")
            self.assertTrue(copied.startswith(original.read_text()))
            self.assertIn("## Synthetic benchmark operator", copied)
            self.assertIn("SIMULATED USER ANSWER", copied)
            self.assertIn("including in fresh step agents", copied)
            self.assertIn("Stop at every unanswered question", copied)
            # Pinned packs come from the operator's pack cache into the snapshot, and the skills point there.
            snapshot_pack = paths["factory"] / "packs" / ("lens@" + "a" * 40)
            self.assertEqual((snapshot_pack / "SKILL.md").read_text(), "lens rules\n")
            self.assertEqual(provenance["installed_packs"]["lens"]["pin"], "a" * 40)
            self.assertEqual(provenance["skipped_packs"], [{"pack": "gone", "reason": "not in pack cache"}])
            self.assertIn(str(paths["factory"] / "packs") + "/<name>@<hash>/",
                          (paths["factory"] / "skills" / "plumb-shared" / "packs.md").read_text())
            marker = "skills/plumb-shared/gates.md: synthetic-operator exception"
            self.assertIn(marker, provenance["adaptations"]["files"])
            self.assertIn(marker, json.loads((output / "provenance.json").read_text())["adaptations"]["files"])
            # The snapshot is the dev_path a trial's plumb.lock names, so it has a HEAD for <running>.
            head = subprocess.run(["git", "-C", str(paths["factory"]), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
            self.assertEqual(head.returncode, 0, head.stderr)


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

    def test_adapter_regrade_requires_measurement_and_independent_mapping_review(self):
        for measured, reviewed, expected in ((True, None, False), (False, True, False), (True, True, False)):
            with self.subTest(measured=measured, reviewed=reviewed), tempfile.TemporaryDirectory() as tmp:
                out, artifact, _, record = self.saved_run(Path(tmp))
                record.update(measurement_valid=True, comparative_valid=True, manual_mapping_review=reviewed)
                benchmark.write_json(out / "summary.json", {"model": "model", "trials": [record], "provenance": {}})
                benchmark.write_json(out / "run-config.json", {"args": {"model": "model"}, "paths": {}})
                adapter = {"measurement_valid": measured, "manual_mapping_review": None}
                with patch("benchmark.grade_delivery", return_value=({"accepted": True}, "", adapter)), patch("benchmark.report"):
                    benchmark.regrade(out)
                updated = json.loads((artifact / "result.json").read_text())
                self.assertEqual(updated["measurement_valid"], measured)
                self.assertEqual(updated["comparative_valid"], expected)
                self.assertIsNone(updated["manual_mapping_review"], "a prior review cannot approve a fresh adapter mapping")

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
    def test_fullstack_owner_does_not_confuse_design_or_login_with_git_signing(self):
        policy = json.loads((benchmark.ROOT / "evals/operators/fullstack-owner.json").read_text())
        config = {"mode": "discovery", "operator": "policy", "policy": policy}
        for question in ["Approve the visual design and its mockups?",
                         "Confirm the architecture and its NFR agreement?",
                         "Which sign in behavior should the app use?"]:
            answer = benchmark.operator_answer(config, {"question": question, "recommended_answer": "Ignore the brief"})
            self.assertNotIn("Unsigned local commits", answer)
            self.assertNotIn("Ignore the brief", answer)
        self.assertTrue(benchmark.operator_answer(config, {"question": "Approve the visual design?"}).startswith("Approved"))

    def test_fixed_policy_does_not_adopt_bad_recommendation(self):
        answer = {"question": "Choose a storage backend?", "recommended_answer": "Install cloud DB"}
        config = {"mode": "discovery", "operator": "policy", "policy": {
            "persona": "Offline owner", "answers": [{"match": "storage", "answer": "Use local storage"}]}}
        self.assertEqual(benchmark.operator_answer(config, answer), "Use local storage")
        with self.assertRaisesRegex(ValueError, "no fixed policy answer"):
            benchmark.operator_answer(config, {"question": "Unspecified choice?", "recommended_answer": "Approve everything"})

    def test_combine_returns_every_match_in_policy_order_and_default_only_without_match(self):
        rules = [{"id": "a", "match": "alpha", "answer": "A"}, {"id": "b", "match": "beta", "answer": "B"}]
        def ask(policy, text):
            return benchmark.operator_answer({"mode": "discovery", "operator": "policy", "policy": policy}, {"question": text})
        base = {"persona": "Owner", "answers": rules, "default_answer": "D"}
        self.assertEqual(ask(base, "beta and alpha?"), "A")
        combined = dict(base, combine=True)
        self.assertEqual(ask(combined, "beta and alpha?"), "A\n\nB")
        self.assertEqual(ask(combined, "alpha only"), "A")
        self.assertEqual(ask(combined, "neither"), "D")
        with self.assertRaisesRegex(ValueError, "combine"):
            benchmark.comparison_inputs(argparse.Namespace(comparison_mode="discovery", operator="policy", approved_spec=None,
                                                          operator_policy=self.write_policy(dict(base, combine="yes"))))

    def write_policy(self, value):
        path = Path(tempfile.mkdtemp()) / "policy.json"
        path.write_text(json.dumps(value))
        return str(path)

    def test_gloam_score_maps_combined_answers_to_rule_ids(self):
        import gloam_score
        policy = {"answers": [{"id": "L03-whispers", "answer": "Whisper rule."}, {"id": "N01-dice", "answer": "No dice."},
                              {"id": "stack", "answer": "Your call."}]}
        policy["answers"].append({"id": "L05-xcard", "answer": "X-card rule."})
        decisions = [{"question": "whispers and dice?", "answer": "Whisper rule.\n\nNo dice.", "after_delivery": False},
                     {"question": "stack?", "answer": "Your call.", "after_delivery": False},
                     {"question": "x-card, now that it is built?", "answer": "X-card rule.", "after_delivery": True}]
        result = gloam_score.score_trial(policy, decisions)
        self.assertEqual(result["revealed"], ["L03-whispers", "N01-dice"], "a question after delivery is not discovery")
        self.assertEqual((result["revealed_count"], result["questions"], result["questions_before_delivery"], result["questions_per_rule"]), (2, 3, 2, 1.0))
        self.assertEqual(result["question_log"][1]["rules"], ["stack"])
        self.assertEqual(result["question_log"][2], {"question": "x-card, now that it is built?", "rules": ["L05-xcard"], "after_delivery": True})

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

    def test_opt_in_receipt_times_preserve_native_event_indexes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = "import json,time; print('not-json',flush=True); print(json.dumps({'type':'system','subtype':'init'}),flush=True); time.sleep(.06); print(json.dumps({'type':'result','subtype':'success','structured_output':{'state':'complete','question':'','recommended_answer':'','summary':'Done'}}),flush=True)"
            run = benchmark.invoke([sys.executable, '-c', script], root, root / 'observed', 5, observe_events=True)
            rows = [json.loads(line) for line in (root / 'observed.timings.jsonl').read_text().splitlines()]
            self.assertEqual([row['event_index'] for row in rows], list(range(len(run['events']))))
            self.assertTrue(all(type(row['timestamp']) in (int, float) for row in rows))
            self.assertLessEqual(rows[0]['timestamp'], rows[-1]['timestamp'])
            self.assertEqual(run['invalid_lines'], 1)
            benchmark.invoke([sys.executable, '-c', 'print(1)'], root, root / 'unobserved', 5)
            self.assertFalse((root / 'unobserved.timings.jsonl').exists())

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
            lock = (artifact / "workspace/.plumb/plumb.lock").read_text()
            self.assertIn(f"dev_path: {plugin.resolve()}", lock)
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

    def test_discovery_arm_never_sees_owner_answers_or_test_feedback(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/module"}):
            root = Path(temporary)
            plugin = root / "factory"
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin/plugin.json").write_text('{"name":"factory"}')
            runtime = {"command": str(root / "browser-check"), "sha256": {}}
            args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5, max_questions=1, repair_rounds=3,
                                      claude="claude", model="claude-sonnet-5-5", until_complete=True)
            policy = root / "operator-policy.json"
            policy.write_text("owner-only answers")
            args.operator_policy = str(policy)
            args.comparison = {"mode": "discovery", "operator": "policy", "input_hashes": {}, "valid_decision_protocol": True,
                               "policy": {"persona": "Wren", "answers": [{"match": "voice", "answer": "OWNER-ONLY ANSWER"}]}}
            args.out.mkdir()
            init = {"type": "system", "subtype": "init", "model": args.model, "plugins": [{"name": "factory"}], "mcp_servers": []}
            complete = {"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"}
            responses = [[], [init, {"type": "result", "structured_output": complete}]]
            calls = []

            def fake_invoke(cmd, work, artifact, timeout):
                calls.append(cmd)
                return {"returncode": 0, "timeout": False, "seconds": 0.1, "events": responses.pop(0)}

            failing = {"accepted": False, "tests": 22, "failures": 3, "errors": 0, "skipped": 0}
            adapter = {"valid": True, "seconds": 0.5, "cost_usd": 0.2}
            with patch("browser_runtime.prepare_browser_check", return_value=runtime) as browser_prepare, patch("benchmark.invoke", side_effect=fake_invoke), \
                    patch("benchmark.grade_delivery", return_value=(failing, "HIDDEN CHECK: tapper email leaked", adapter)):
                result = benchmark.trial(args, benchmark.CASES / "gloam-chat", "factory", 0, {"factory": plugin})
            self.assertEqual(result["repair_rounds"], 0)
            self.assertIn(str(policy), browser_prepare.call_args.args[2])
            self.assertFalse(result["measurement_valid"], "unverified adapter accounting cannot yield a valid comparison")
            self.assertIsNone(result["manual_mapping_review"])
            self.assertFalse(result["comparative_valid"])
            self.assertIn("forced to 0", result["repair_policy"])
            self.assertIn("no test feedback", result["stop_reason"])
            self.assertEqual(len(calls), 2)
            prompts = " ".join(" ".join(cmd) for cmd in calls)
            for leaked in ("OWNER-ONLY ANSWER", "FIXED OPERATOR PERSONA", "HIDDEN CHECK", "same neutral requirements"):
                self.assertNotIn(leaked, prompts)
            self.assertEqual(result["adapter_runs"], [adapter])
            self.assertIsNone(result["cost_usd"])  # the arm reported none; adapter cost never joins the arm's


    def discovery_trial(self, root, responses, deliveries, evidence=None):
        plugin = root / "factory"
        (plugin / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (plugin / ".claude-plugin/plugin.json").write_text('{"name":"factory"}')
        args = argparse.Namespace(out=root / "output", timeout=60, budget_usd=5, max_questions=5, repair_rounds=3,
                                  claude="claude", model="claude-sonnet-5-5", until_complete=True)
        args.comparison = {"mode": "discovery", "operator": "policy", "input_hashes": {}, "valid_decision_protocol": True,
                           "policy": {"persona": "Wren", "answers": [{"match": "x-card", "answer": "OWNER-ONLY ANSWER"}]}}
        args.out.mkdir()
        calls = []

        def fake_invoke(cmd, work, artifact, timeout):
            calls.append(cmd)
            return {"returncode": 0, "timeout": False, "seconds": 0.1, "events": responses.pop(0)}

        with patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/module"}), \
                patch("browser_runtime.prepare_browser_check", return_value={"command": str(root / "browser-check"), "sha256": {}}), \
                patch("benchmark.invoke", side_effect=fake_invoke), patch("benchmark.grade_delivery", side_effect=deliveries), \
                patch("benchmark.workflow_evidence", side_effect=evidence, return_value={"workflow_complete": True}):
            return benchmark.trial(args, benchmark.CASES / "gloam-chat", "factory", 0, {"factory": plugin}), calls

    def test_discovery_finish_request_hides_acceptance_and_tags_later_questions(self):
        init = {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5", "plugins": [{"name": "factory"}], "mcp_servers": []}
        result = lambda state, question="": {"type": "result", "structured_output": {
            "state": state, "question": question, "recommended_answer": "", "summary": "Done"}}
        responses = [[], [init, result("question", "Is the x-card anonymous?")], [result("complete")],
                     [result("question", "Should the x-card show who tapped?")], [result("complete")]]
        accepted = {"accepted": True, "tests": 23, "failures": 0, "errors": 0, "skipped": 0}
        with tempfile.TemporaryDirectory() as temporary:
            record, calls = self.discovery_trial(Path(temporary), responses, [(accepted, "", None)] * 2,
                                                 [{"workflow_complete": False}, {"workflow_complete": True}, {"workflow_complete": True}])
        self.assertEqual(record["status"], "accepted")
        finish = calls[3][-1]
        self.assertIn("SHARED WORKFLOW FINISH REQUEST", finish)
        self.assertNotIn("acceptance", finish)
        self.assertEqual([d["after_delivery"] for d in record["decisions"]], [False, True])

    def test_failed_adapter_stops_without_charging_the_arm(self):
        init = {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5", "plugins": [{"name": "factory"}], "mcp_servers": []}
        complete = {"type": "result", "structured_output": {"state": "complete", "question": "", "recommended_answer": "", "summary": "Done"}}
        failed = {"accepted": False, "adapter_failed": True, "attributable_to_arm": False, "reason": "adapter timed out"}
        with tempfile.TemporaryDirectory() as temporary:
            record, calls = self.discovery_trial(Path(temporary), [[], [init, complete]], [(failed, "unused", {"seconds": 1})])
        self.assertEqual(len(calls), 2)
        self.assertEqual(record["stop_reason"], "adapter failed; grading is not attributable to the arm: adapter timed out")
        self.assertEqual(record["repair_rounds"], 0)

    def test_arm_cannot_read_the_owner_policy_or_run_records(self):
        policy = benchmark.ROOT / "evals/operators/gloam-owner.json"
        out = Path("/runs/out")
        with patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/module"}):
            config = benchmark.settings(Path("/work"), {"factory": Path("/factory")}, "factory", out, browser=True, hidden=[str(policy)])
        denied_reads = config["sandbox"]["filesystem"]["denyRead"]
        for path in [policy, benchmark.ROOT / "docs", out / "run-config.json", out / "provenance.json", out / "summary.json"]:
            self.assertTrue(any(str(path).startswith(denied) for denied in denied_reads), path)
        self.assertIn(f"Read(/{policy})", config["permissions"]["deny"])
        self.assertIn(f"Read(/{benchmark.ROOT / 'docs'}/**)", config["permissions"]["deny"])
        self.assertIn(f"Read(/{out / 'run-config.json'})", config["permissions"]["deny"])
        codex_protected = []

        def capture(binary, work, runtime, active, protected, *rest, **options):
            codex_protected.append(protected)
            raise ValueError("captured")

        with tempfile.TemporaryDirectory() as temporary, patch("codex_adapter.prepare", side_effect=capture), \
                patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/module"}):
            root = Path(temporary)
            paths = {name: root / name for name in ("factory", "superpowers")}
            for path in paths.values():
                path.mkdir()
            args = argparse.Namespace(out=root / "out", timeout=60, budget_usd=5, max_questions=0, repair_rounds=0, harness="codex",
                                      codex="codex", effort="high", model="gpt-6.1-sol", operator_policy=str(policy))
            args.out.mkdir()
            record = benchmark.trial(args, benchmark.CASES / "csv-targets", "factory", 0, paths)
            shutil.rmtree(record["runtime_root"])
            work = root / "delivered"
            work.mkdir()
            benchmark.grade_delivery(args, benchmark.CASES / "gloam-chat", work, root / "grade-0", paths)
        self.assertEqual(len(codex_protected), 2, "the Codex arm and the Codex adapter")
        for protected in codex_protected:
            for path in [policy.resolve(), args.out / "run-config.json", args.out / "provenance.json", args.out / "summary.json",
                         args.out / "blind-review-key.json"]:
                self.assertIn(path, protected)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "superpowers/.claude-plugin").mkdir(parents=True)
            out = root / "out"
            with patch("benchmark.snapshots", return_value=({}, {})), patch("benchmark.trial", return_value={"interrupted": False}), \
                    patch("benchmark.report"), patch("benchmark.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "1.0", "")):
                benchmark.main(["run", "--superpowers", str(root / "superpowers"), "--model", "claude-sonnet-5-5", "--out", str(out),
                                "--cases", "csv-targets", "--repeats", "1", "--operator-policy", str(policy)])
            answers = [rule["answer"] for rule in json.loads(policy.read_text())["answers"]]
            for name in ["run-config.json", "provenance.json"]:
                text = (out / name).read_text()
                self.assertIn(benchmark.hashlib.sha256(policy.read_bytes()).hexdigest(), text)
                self.assertFalse([answer for answer in answers if answer in text], name + " leaks owner answers")


class AdapterTests(unittest.TestCase):
    COMPLETE: ClassVar[dict] = {"returncode": 0, "timeout": False, "seconds": 0.1,
                "events": [{"type": "system", "subtype": "init", "model": "claude-sonnet-5-5", "plugins": [], "mcp_servers": []},
                           {"type": "result", "structured_output": {"state": "complete", "question": "", "recommended_answer": "", "summary": "Mapped"}}]}

    def run_adapter(self, edits, run=COMPLETE):
        with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", {"PLAYWRIGHT_MODULE": "/module"}):
            root = Path(temporary)
            work = root / "work"
            shutil.copytree(benchmark.CASES / "gloam-chat" / "oracle", work)
            for path in ["qa/mapping.py", "qa/ui.json", "benchmark.sh"]:
                (work / path).unlink()
            (work / "node_modules/pkg").mkdir(parents=True)
            (work / "node_modules/pkg/index.js").write_text("module.exports = 1")
            args = argparse.Namespace(out=root / "out", timeout=60, budget_usd=5, claude="claude", model="claude-sonnet-5-5")
            seen = {}

            def adapter_agent(cmd, copy, artifact, timeout):
                seen["prompt"], seen["contract"], seen["max_turns"] = cmd[-1], (copy / "qa/contract.md").is_file(), "--max-turns" in cmd
                for path, text in edits.items():
                    (copy / path).parent.mkdir(parents=True, exist_ok=True)
                    (copy / path).write_text(text)
                return json.loads(json.dumps(run))

            def graded(case, product, artifact):
                seen["graded"] = (product / "qa/mapping.py").read_text()
                return {"accepted": True}, ""

            with patch("benchmark.invoke", side_effect=adapter_agent), patch("benchmark.grade", side_effect=graded) as grade:
                quality, _, adapter = benchmark.grade_delivery(args, benchmark.CASES / "gloam-chat", work, root / "trial/grade-0", {"factory": root / "factory"})
            self.assertEqual(seen["prompt"], (benchmark.CASES / "gloam-chat/grading/adapter-prompt.md").read_text())
            self.assertTrue(seen["contract"])
            self.assertFalse(seen["max_turns"], "Claude and Codex adapters share one cap: time, not turns")
            self.assertEqual(sorted(str(path.relative_to(work)) for path in work.rglob("*") if path.is_file()),
                             ["DECISIONS.md", "index.html", "node_modules/pkg/index.js", "server.py"],
                             "the adapter works on a copy; the delivered product is untouched")
            return quality, adapter, seen, (root / "trial/grade-0-adapter/adapter.diff").read_text() if adapter.get("diff") else "", grade

    def assert_not_attributable(self, quality, adapter, grade, reason):
        grade.assert_not_called()
        self.assertFalse(quality["accepted"])
        self.assertTrue(quality["adapter_failed"])
        self.assertFalse(quality["attributable_to_arm"])
        self.assertIn(reason, quality["reason"])
        self.assertEqual(adapter["adapter_failed"], quality["reason"])

    def test_adapter_writing_only_qa_files_is_graded_on_its_copy(self):
        quality, adapter, seen, diff, grade = self.run_adapter({"qa/mapping.py": "def handle(request, product): pass\n", "benchmark.sh": "#!/bin/sh\n"})
        self.assertTrue(quality["accepted"])
        self.assertIsNone(adapter["adapter_failed"])
        self.assertEqual(adapter["changed_paths"], ["benchmark.sh", "qa/mapping.py"])
        self.assertIn("+def handle(request, product): pass", diff)
        self.assertEqual(seen["graded"], "def handle(request, product): pass\n")
        grade.assert_called_once()

    def test_unverified_or_contaminated_adapter_is_not_graded(self):
        for init in (None, {"type": "system", "subtype": "init", "plugins": ["foreign"], "mcp_servers": []}):
            run = {**self.COMPLETE, "events": ([init] if init else []) + [self.COMPLETE["events"][-1]]}
            quality, adapter, _, _, grade = self.run_adapter({"qa/mapping.py": "pass\n"}, run)
            self.assert_not_attributable(quality, adapter, grade, "isolation")

    def test_unknown_adapter_accounting_is_not_zero_or_valid(self):
        quality, adapter, _, _, _ = self.run_adapter({"qa/mapping.py": "pass\n"})
        self.assertTrue(quality["accepted"])
        self.assertIsNone(adapter["cost_usd"])
        self.assertFalse(adapter["measurement_valid"])
        self.assertFalse(adapter["model_policy_valid"])
        self.assertIsNone(adapter["manual_mapping_review"])

    def test_observed_adapter_model_and_accounting_control_measurement(self):
        usage = {field: 1 for field in benchmark.TOKEN_FIELDS}
        for model, expected in (("claude-sonnet-5-5", True), ("unexpected-model", False)):
            events = json.loads(json.dumps(self.COMPLETE["events"]))
            events[-1].update(modelUsage={model: usage}, total_cost_usd=.05)
            quality, adapter, _, _, _ = self.run_adapter({"qa/mapping.py": "pass\n"}, {**self.COMPLETE, "events": events})
            self.assertTrue(quality["accepted"])
            self.assertEqual(adapter["measurement_valid"], expected)
            self.assertEqual(adapter["model_policy_valid"], expected)
            self.assertEqual(adapter["cost_usd"], .05)
            self.assertIn("provider effort is not observed", adapter["effort_policy_evidence"])

    def test_adapter_diff_guard_rejects_a_product_file_change(self):
        quality, adapter, _seen, diff, grade = self.run_adapter({"qa/mapping.py": "def handle(request, product): pass\n",
                                                                "server.py": "print('patched product')\n"})
        self.assert_not_attributable(quality, adapter, grade, "changed product files: server.py")
        self.assertIn("+print('patched product')", diff)

    def test_adapter_diff_guard_rejects_a_dependency_change(self):
        quality, adapter, _seen, diff, grade = self.run_adapter({"node_modules/pkg/index.js": "module.exports = 2"})
        self.assert_not_attributable(quality, adapter, grade, "node_modules/pkg/index.js")
        self.assertIn("Dependency file node_modules/pkg/index.js changed", diff)

    def test_failed_or_blocked_adapter_is_not_the_arms_failure(self):
        blocked = {**self.COMPLETE, "events": [self.COMPLETE["events"][0], {"type": "result", "structured_output": {
            "state": "blocked", "question": "", "recommended_answer": "", "summary": "cannot seed"}}]}
        does_not_start = json.dumps({"product_starts": False, "evidence": "$ sh benchmark.sh start\nError: Cannot find module 'express'"})
        starts = json.dumps({"product_starts": True, "evidence": ""})
        for run, report, reason in [({**self.COMPLETE, "returncode": 1}, does_not_start, "exited 1"),
                                    ({**self.COMPLETE, "timeout": True}, does_not_start, "timed out"),
                                    (blocked, None, "reported blocked: cannot seed"), (blocked, starts, "reported blocked: cannot seed"),
                                    (blocked, json.dumps({"product_starts": False, "evidence": " "}), "reported blocked")]:
            edits = {"qa/mapping.py": "def handle(request, product): pass\n", **({"qa/report.json": report} if report else {})}
            quality, adapter, _, _, grade = self.run_adapter(edits, run)
            self.assert_not_attributable(quality, adapter, grade, reason)

    def test_product_that_does_not_start_is_the_arms_failure(self):
        blocked = {**self.COMPLETE, "events": [self.COMPLETE["events"][0], {"type": "result", "structured_output": {
            "state": "blocked", "question": "", "recommended_answer": "", "summary": "the product does not start"}}]}
        report = json.dumps({"product_starts": False, "evidence": "$ sh benchmark.sh start\nError: Cannot find module 'express'"})
        quality, adapter, _, _, grade = self.run_adapter({"benchmark.sh": "#!/bin/sh\n", "qa/report.json": report}, blocked)
        grade.assert_not_called()
        self.assertIsNone(adapter["adapter_failed"])
        self.assertFalse(quality["accepted"])
        self.assertTrue(quality["attributable_to_arm"])
        self.assertIn("Cannot find module", quality["evidence"])
        self.assertEqual((quality["tests"], quality["failures"]), (23, 23))
        self.assertFalse(any(row["passed"] for row in quality["requirements"].values()))
        self.assertFalse(any(outcome["accepted"] for outcome in quality["outcomes"]))


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
            names = ["index.html", "styles.css", "app.js", "tickets.json", "logo.svg", "requirements-dev.txt", "uv.lock"]
            for name in [*names, "test_generated.cjs", "test_existing.cjs"]:
                (work / name).write_text(name)
            cache = work / ".mypy_cache"
            cache.mkdir()
            (cache / "source.json").write_text("generated cache")
            benchmark.copy_product(work, root / "source", source_only=True)
            self.assertEqual(sorted(path.name for path in (root / "source").iterdir()), sorted(names))

    def test_grading_prerequisite_failure_retains_nested_artifact_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            artifact = root / "nested/grade"
            with patch("benchmark.grading_sandbox", side_effect=ValueError("missing grading runtime")):
                quality, text = benchmark.grade(benchmark.CASES / "support-dashboard", work, artifact)
            self.assertFalse(quality["accepted"])
            self.assertIsNone(quality["tests"])
            self.assertEqual(text, "missing grading runtime")
            self.assertEqual(artifact.with_suffix(".txt").read_text(), text)
            self.assertEqual(json.loads(artifact.with_suffix(".json").read_text()), quality)

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
