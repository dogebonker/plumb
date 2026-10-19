"""Run isolated workflow trials; never infer human follow-up savings."""

import argparse
import ast
import difflib
import hashlib
import json
import os
import platform
import random
import re
import runpy
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from context_adapter import prepare as prepare_context

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"
BENCHMARK_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
IGNORED = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "node_modules", ".venv", ".pytest_cache")
TOKEN_FIELDS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def tree_hash(path):
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_file() and not any(part in {".git", "__pycache__", "node_modules", ".venv", ".benchmark-shadow", ".in_use"} for part in file.parts):
            digest.update(str(file.relative_to(path)).encode() + b"\0" + file.read_bytes() + b"\0")
    return digest.hexdigest()


def git_info(path):
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    status = subprocess.run(["git", "-C", str(path), "status", "--porcelain"], capture_output=True, text=True, check=False)
    return {"commit": result.stdout.strip() if result.returncode == 0 else None,
            "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None}


def comparison_inputs(args):
    mode = getattr(args, "comparison_mode", "legacy-recommended")
    operator = getattr(args, "operator", "policy")
    spec, policy = getattr(args, "approved_spec", None), getattr(args, "operator_policy", None)
    if mode == "execution" and not spec:
        raise ValueError("execution requires one approved spec shared by every arm")
    if mode == "discovery" and operator != "human" and not policy:
        raise ValueError("discovery requires a fixed operator policy or human operator")
    result = {"mode": mode, "operator": operator, "input_hashes": {}, "valid_decision_protocol": mode != "legacy-recommended"}
    for name, path in [("approved_spec", spec), ("policy", policy)]:
        if path:
            content = Path(path).read_bytes()
            result["input_hashes"][name] = hashlib.sha256(content).hexdigest()
            result[name] = json.loads(content) if name == "policy" else content.decode()
            if name == "approved_spec" and not result[name].strip():
                raise ValueError("approved spec must contain the agreed execution requirements")
    if "policy" in result:
        value = result["policy"]
        if not isinstance(value, dict) or not isinstance(value.get("persona"), str) or not value["persona"].strip():
            raise ValueError("operator policy requires a fixed persona")
        if not isinstance(value.get("answers", []), list) or not isinstance(value.get("default_answer", ""), str):
            raise ValueError("policy answers must be a list and default_answer a string")
        if not isinstance(value.get("combine", False), bool):
            raise ValueError("policy combine must be a boolean")
        for rule in value.get("answers", []):
            if not isinstance(rule, dict) or not isinstance(rule.get("match"), str) or not isinstance(rule.get("answer"), str) or not rule["answer"].strip():
                raise ValueError("policy answers must be nonempty strings")
            re.compile(rule["match"], re.IGNORECASE)
    return result


def public_comparison(comparison):
    """What may be written where actors could read it: everything but the owner's answers, whose hash stays in input_hashes."""
    return {key: value for key, value in comparison.items() if key != "policy"}


def policy_files(args):
    return [path for path in [getattr(args, "operator_policy", None)] if path]


def operator_answer(config, question):
    if config["mode"] == "legacy-recommended":
        return question["recommended_answer"]
    if config["operator"] == "human":
        answer = input(question["question"] + "\nOperator answer: ").strip()
        if not answer:
            raise ValueError("human answer cannot be empty")
        return answer
    policy = config.get("policy", {})
    matched = [rule["answer"] for rule in policy.get("answers", []) if re.search(rule["match"], question["question"], re.IGNORECASE)]
    if matched:
        return "\n\n".join(matched) if policy.get("combine") else matched[0]
    if policy.get("default_answer"):
        return policy["default_answer"]
    if config["mode"] == "execution":
        return "Proceed within the supplied approved specification. Do not add requirements or change its decisions; stop blocked if it cannot resolve this question."
    raise ValueError("no fixed policy answer for this question; record a human decision before resuming")


def retain_workspace(work, artifact, record):
    def git(*cmd):
        return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", str(work), *cmd],
                              capture_output=True, text=True, check=True).stdout.strip()
    head = git("rev-parse", "HEAD")
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD") if git("branch", "--show-current") else None
    record["checkout"] = {"head": head, "branch": branch, "dirty": git("status", "--porcelain"),
                          "label": "actual stopped checkout, including uncommitted work"}
    record["git_refs"] = git("show-ref", "--head").splitlines()
    record["checkpoints"] = [line for line in git("log", "--all", "--format=%H %s").splitlines()
                             if re.search(r"\b(red|green|test)\b", line, re.IGNORECASE)]
    record["slice_checkpoints"] = {str(path.relative_to(work)): re.findall(r"^\s*-.*(?:state:|head_commit:).*$", path.read_text(), re.MULTILINE)
                                   for path in work.glob(".software-factory/changes/*/status.yaml")}
    if (artifact / "workspace").exists():
        (artifact / "workspace").rename(artifact / f"workspace-before-resume-{len(list(artifact.glob('workspace-before-resume-*')))}")
    shutil.copytree(work, artifact / "workspace", symlinks=True)
    record["raw_workspace_retained"] = True
    if (artifact / "source").exists():
        shutil.rmtree(artifact / "source")
    copy_product(work, artifact / "source", source_only=True)
    record["source_sha256"] = tree_hash(artifact / "source")
    record["source_checkout"] = dict(record["checkout"])
    for key in ["committed_checkpoint", "committed_checkpoint_quality", "snapshot_quality", "snapshot_quality_checkout"]:
        record.pop(key, None)
    if (artifact / "committed-source").exists():
        shutil.rmtree(artifact / "committed-source")
    if branch is None:
        candidates = []
        for line in git("for-each-ref", "--format=%(refname:short) %(objectname) %(committerdate:unix)", "refs/heads/").splitlines():
            name, commit, stamp = line.split()
            ancestor = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(work), "merge-base", "--is-ancestor", head, commit], check=False)
            if commit != head and ancestor.returncode == 0:
                candidates.append((int(stamp), name, commit))
        if candidates:
            _, name, commit = max(candidates)
            with tempfile.TemporaryDirectory(prefix="benchmark-committed-") as tmp:
                subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "clone", "-q", "--no-checkout", str(work), tmp], check=True)
                subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", tmp, "checkout", "-q", "--detach", commit], check=True)
                copy_product(Path(tmp), artifact / "committed-source", source_only=True)
            record["committed_checkpoint"] = {"head": commit, "branch": name,
                                               "selection": "latest descendant local branch by commit timestamp; not a quality ranking",
                                               "label": "separate committed change-branch checkpoint; not the raw checkout or completed delivery"}


@contextmanager
def retained_runtime(artifact, record):
    root = Path(record.get("runtime_root") or tempfile.mkdtemp(prefix="fb-", dir="/tmp")).resolve()
    record["runtime_root"] = str(root)
    write_json(artifact / "progress.json", record)
    try:
        yield root
    finally:
        work = root / "work"
        if work.exists() and not record.get("raw_workspace_retained"):
            if (artifact / "workspace").exists():
                (artifact / "workspace").rename(artifact / f"workspace-before-resume-{len(list(artifact.glob('workspace-before-resume-*')))}")
            shutil.copytree(work, artifact / "workspace", symlinks=True)
        write_json(artifact / "progress.json", record)


def snapshots(args):
    support = args.out / "snapshots"
    support.mkdir()
    factory = support / "factory"
    (factory / ".claude-plugin").mkdir(parents=True)
    write_json(factory / ".claude-plugin" / "plugin.json", {"name": "factory", "version": "0.0.0", "description": "Pinned local Factory benchmark snapshot"})
    shutil.copytree(ROOT / "skills", factory / "skills", ignore=IGNORED)
    shutil.copytree(ROOT / "kit", factory / "kit", ignore=IGNORED)
    shutil.copytree(ROOT / "hooks", factory / "hooks", ignore=IGNORED)
    shutil.copytree(ROOT / "bin", factory / "bin", ignore=IGNORED)
    packs = factory / "packs"  # actors only read frozen packs, never the operator's cache
    packs.mkdir()
    skipped = []
    pack_tools = runpy.run_path(str(ROOT / "bin" / "factory-packs-fetch"))
    pack_provenance = {}
    for name, pin in pack_tools["pins"](factory / "kit" / "packs.lock.yaml").items():
        expected = pin["hash"]
        bundled = pin.get("source") == "ciembor/agent-rules-books"
        if bundled and pin.get("path") != name:
            raise ValueError(f"Required book bundle {name} has an unexpected source path; restore kit/packs.lock.yaml.")
        source = ((ROOT / "kit" / "packs") if bundled else (Path.home() / ".software-factory" / "packs")) / f"{name}@{expected}"
        if bundled:
            try:
                pack_tools["check_bundle"](factory / "kit" / "packs" / source.name, expected)
            except (pack_tools["Failed"], OSError) as error:
                raise ValueError(f"Required book bundle {name}@{expected} is missing or invalid: {error}. "
                                 "Restore the pinned kit/packs bundle before preparing a benchmark.") from error
        elif not source.is_dir():
            skipped.append({"pack": name, "reason": "not in pack cache"})
            continue
        frozen_source = factory / "kit" / "packs" / source.name if bundled else source
        shutil.copytree(frozen_source, packs / source.name, ignore=None if bundled else IGNORED, symlinks=True)
        if bundled:
            try:
                pack_tools["check_bundle"](packs / source.name, expected)
            except (pack_tools["Failed"], OSError) as error:
                raise ValueError(f"Copied book bundle {name}@{expected} failed verification: {error}") from error
        pack_provenance[name] = {"path": str(source), "sha256": tree_hash(frozen_source), "pin": expected,
                                 "source_kind": "bundled" if bundled else "cache"}
    (factory / "user").mkdir()  # an empty user layer: the trial never reads the operator's ~/.software-factory/user/
    replacements = {"~/.software-factory/user/": str(factory / "user") + "/", "~/.software-factory/packs/": str(packs) + "/"}
    adapted = []
    gates = factory / "skills" / "factory-shared" / "gates.md"
    gates.write_text(gates.read_text() + "\n## Synthetic benchmark operator\n\n"
                     "This copied kit runs only in a disposable benchmark repository. The operator's recorded "
                     "SIMULATED USER ANSWER is an explicit benchmark response. When the orchestrator forwards it "
                     "verbatim, treat it as the operator's answer for local gates and sign-off, including in fresh "
                     "step agents. Do not require a real person's identity in these fixtures. This exception does "
                     "not authorize production actions, external writes or fabricated answers. Stop at every "
                     "unanswered question as usual.\n")
    adapted.append("skills/factory-shared/gates.md: synthetic-operator exception")
    for skill in (factory / "skills").glob("factory-*/SKILL.md"):
        body = skill.read_text()
        if "disable-model-invocation: true" in body:
            skill.write_text(body.replace("disable-model-invocation: true", "disable-model-invocation: false"))
            adapted.append(str(skill.relative_to(factory)) + ": automated benchmark invocation enabled")
    for folder in [factory / "skills", factory / "kit"]:
        for file in folder.rglob("*"):
            if file.is_file() and not file.is_relative_to(factory / "kit" / "packs"):
                try:
                    original = file.read_text()
                except UnicodeError:
                    continue
                updated = original
                for old, new in replacements.items():
                    updated = updated.replace(old, new)
                if original != updated:
                    file.write_text(updated)
                    adapted.append(str(file.relative_to(factory)))
    # The trial's factory.lock names this snapshot as its dev_path, whose HEAD is the framework version that ran.
    for cmd in [["init", "-q"], ["add", "-A"], ["commit", "-qm", "Factory benchmark snapshot"]]:
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "-c", "user.name=Benchmark",
                        "-c", "user.email=benchmark@example.invalid", "-C", str(factory), *cmd], check=True, capture_output=True)
    paths = {"factory": factory}
    provenance = {"factory": {"source": str(ROOT), "skills_sha256": tree_hash(ROOT / "skills"),
                             "kit_sha256": tree_hash(ROOT / "kit"), **git_info(ROOT)},
                  "installed_packs": pack_provenance, "skipped_packs": skipped,
                  "adaptations": {"replacements": replacements, "files": adapted,
                                  "notes": "The framework is a read-only one-commit snapshot that each Factory trial's .software-factory/factory.lock names as dev_path; propose kit changes locally. No Factory gate hooks were installed; skills are compared."}}
    for name, source in [("superpowers", args.superpowers), ("context-mode", args.context_mode)]:
        if source is not None:
            target = support / name
            ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".venv") if name == "context-mode" else IGNORED
            shutil.copytree(source, target, ignore=ignore)
            if not (target / ".claude-plugin" / "plugin.json").is_file():
                raise ValueError(f"{source} must be a Claude plugin root with .claude-plugin/plugin.json")
            paths[name] = target
            provenance[name] = {"source": str(source), "sha256": tree_hash(source), **git_info(source)}
    for name, path in paths.items():
        provenance[name]["snapshot_sha256"] = tree_hash(path)
    write_json(args.out / "provenance.json", provenance)
    return paths, provenance


def arm_order(repeat, context=False):
    arms = ["factory", "superpowers"] + (["factory-context"] if context else [])
    return arms if repeat % 2 == 0 else list(reversed(arms))


def secret_files(out, hidden=()):
    """Run records, the operator policy and the blind key stay out of every actor's reach, in every harness."""
    return [out / name for name in ("run-config.json", "provenance.json", "summary.json", "blind-review-key.json")] + [
        Path(path).resolve() for path in hidden]


def settings(work, paths, arm, out, browser=False, browser_command=None, red_command=None, hidden=()):
    denied_plugins = [str(path) for name, path in paths.items()
                      if name not in ({"factory", "context-mode"} if arm == "factory-context" else {arm})]
    active = [path for name, path in paths.items()
              if name in ({"factory", "context-mode"} if arm == "factory-context" else {arm})]
    protected = [CASES, out / "case-snapshots", out / "trials", ROOT / "docs", ROOT / "evals" / "operators",
                 *(Path(path) for path in denied_plugins)]
    secrets = secret_files(out, hidden)
    read_rule = lambda path: f"Read(/{path}/**)"  # absolute paths require two leading slashes
    edit_rule = lambda path: f"Edit(/{path}/**)"  # Edit rules also govern Write and NotebookEdit
    return {"autoMemoryEnabled": False, "disableBundledSkills": True, "claudeMdExcludes": ["**"],
            "permissions": {"allow": [read_rule(work), edit_rule(work), *(read_rule(path) for path in active),
                                       "Glob", "Grep", "Skill", "Agent", "Bash", "ToolSearch",
                                       *(f"Bash({command})" for command in [browser_command, red_command] if command),
                                       *(["mcp__plugin_context-mode_context-mode__*"] if arm == "factory-context" else []),
                                       *([read_rule(Path(os.environ["PLAYWRIGHT_MODULE"]))] if browser else [])],
                            "deny": ["AskUserQuestion", "WebFetch", "WebSearch", *(read_rule(path) for path in protected),
                                     *(f"Read(/{path})" for path in secrets),
                                     edit_rule(ROOT), edit_rule(out), *(edit_rule(path) for path in active),
                                     *([edit_rule(Path(browser_command).parent)] if browser_command else []),
                                     *([edit_rule(Path(os.environ["PLAYWRIGHT_MODULE"]))] if browser else [])]},
            "sandbox": {"enabled": True, "failIfUnavailable": True, "autoAllowBashIfSandboxed": True,
                        "allowUnsandboxedCommands": False,
                        "excludedCommands": [str(command) for command in [browser_command, red_command] if command],
                        "filesystem": {"allowWrite": [str(work)], "denyWrite": [str(ROOT), str(out),
                                                              *([str(Path(browser_command).parent)] if browser_command else [])],
                                       "denyRead": [str(path) for path in [*protected, *secrets]] + [str(Path.home() / ".software-factory"),
                                                    str(Path.home() / ".agents" / "skills"), str(Path.home() / ".claude" / "skills")]},
                        "network": {"allowedDomains": ["127.0.0.1", "localhost"] if browser else [],
                                    "allowLocalBinding": browser, "strictAllowlist": True}}}


def command(args, paths, arm, config, session, resume, remaining_budget, prompt=None, init=False):
    plugins = [] if arm == "adapter" else [paths["factory"] if arm.startswith("factory") else paths["superpowers"]]
    servers = {}
    if arm == "factory-context":
        plugins.append(paths["context-mode"])
        servers = json.loads((paths["context-mode"] / ".claude-plugin/plugin.json").read_text())["mcpServers"]
        for server in servers.values():
            server["args"] = [argument.replace("${CLAUDE_PLUGIN_ROOT}", str(paths["context-mode"])) for argument in server["args"]]
            server.setdefault("env", {})["CLAUDE_PLUGIN_ROOT"] = str(paths["context-mode"])
        servers = {f"plugin_context-mode_{name}": server for name, server in servers.items()}
    unlimited_actor = arm != "adapter" and getattr(args, "until_complete", False)
    cmd = [args.claude, "--print", "--model", args.model, "--setting-sources", "", "--strict-mcp-config",
           "--mcp-config", json.dumps({"mcpServers": servers}), "--settings", str(config), "--permission-mode", "dontAsk",
           "--output-format", "stream-json", "--verbose", "--forward-subagent-text", "--include-hook-events",
           *([] if arm == "adapter" or unlimited_actor else ["--max-turns", "60"]),
           *([] if unlimited_actor else ["--max-budget-usd", str(max(0, remaining_budget))]),
           "--effort", getattr(args, "effort", "high"), "--no-chrome",
           "--resume" if resume else "--session-id", session]
    for plugin in plugins:
        cmd.extend(["--plugin-dir", str(plugin), "--add-dir", str(plugin)])
    if init:
        cmd.append("--init-only")
    if prompt is not None:
        cmd.extend(["--", prompt])  # end --add-dir's variadic arguments before the prompt
    return cmd


def invoke(cmd, work, artifact, timeout):
    started = time.monotonic()
    timed_out = False
    interrupted = False
    env = dict(os.environ)
    scratch = work / ".tmp"
    scratch.mkdir(exist_ok=True)
    env["CLAUDE_CODE_TMPDIR"] = str(scratch)
    for key in ["CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE"]:
        env.pop(key, None)
    try:
        with (artifact.with_suffix(".jsonl")).open("w") as stdout, (artifact.with_suffix(".stderr")).open("w") as stderr:
            process = subprocess.Popen(cmd, cwd=work, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, text=True, env=env, start_new_session=True)
            try:
                pending = b""
                terminal = None
                with artifact.with_suffix(".jsonl").open("rb") as reader:
                    while True:
                        pending += reader.read()
                        lines = pending.split(b"\n")
                        pending = lines.pop()
                        for line in lines:
                            try:
                                event = json.loads(line)
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                continue
                            if (isinstance(event, dict) and event.get("type") == "result"
                                    and event.get("parent_tool_use_id") is None
                                    and (event.get("is_error") or event.get("subtype") != "success" or response([event]) is not None)):
                                terminal = event
                        if terminal is not None:
                            # Print turns can finish while the CLI retains agent/background handles.
                            try:
                                process.wait(timeout=1)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGTERM)
                                try:
                                    process.wait(timeout=1)
                                except subprocess.TimeoutExpired:
                                    os.killpg(process.pid, signal.SIGKILL)
                                    process.wait()
                            code = 0 if terminal.get("subtype") == "success" and not terminal.get("is_error") else 1
                            break
                        if process.poll() is not None:
                            code = process.returncode
                            break
                        if timeout is not None and time.monotonic() - started >= timeout:
                            timed_out = True
                            os.killpg(process.pid, signal.SIGKILL)
                            code = process.wait()
                            break
                        time.sleep(0.05)
            except KeyboardInterrupt:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                code = process.returncode
                interrupted = True
    except OSError as error:
        artifact.with_suffix(".stderr").write_text(str(error))
        return {"returncode": None, "timeout": False, "seconds": time.monotonic() - started, "events": [], "error": str(error)}
    events = []
    invalid_lines = 0
    for line in artifact.with_suffix(".jsonl").read_text().splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except json.JSONDecodeError:
            invalid_lines += 1
    return {"returncode": code, "timeout": timed_out, "seconds": time.monotonic() - started,
            "events": events, "invalid_lines": invalid_lines, "interrupted": interrupted}


def codex_events(events):
    """Adapt only root CLI messages in memory; retain the original JSONL unchanged."""
    session, message, failed, terminal = None, None, False, False
    for event in events:
        if event.get("type") == "thread.started":
            session = event.get("thread_id")
        elif event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message":
            message = event["item"].get("text")
        elif event.get("type") in {"turn.failed", "error"}:
            failed = True
        elif event.get("type") == "turn.completed":
            terminal = True
    adapted = [{"type": "result", "result": message or "", "is_error": failed,
                "subtype": "success" if terminal and not failed else "error"}] if terminal or failed else []
    return adapted, session


def codex_accounting(observed, partial=False):
    known = observed.get("accounting_complete", False) and not partial
    totals = observed.get("totals", {})
    classes = {"inputTokens": totals.get("input_tokens"), "outputTokens": totals.get("output_tokens"),
               "cacheReadInputTokens": totals.get("cached_input_tokens"),
               "cacheCreationInputTokens": totals.get("cache_write_input_tokens")}
    models = sorted({r.get("model") for r in observed.get("records", []) if r.get("model")})
    return {"models": models, "model_usage": {model: {"canonicalModel": model} for model in models},
            "token_classes": classes if known else {key: None for key in classes},
            "tokens": totals.get("input_tokens", 0) + totals.get("output_tokens", 0) if known else None,
            "cost_usd": observed.get("modeled_api_usd") if known else None,
            "estimated_api_usd": observed.get("modeled_api_usd") if known else None,
            "actual_invoice_usd": None, "accounting_scope": "deduplicated per-response root and child usage; API price estimate, not invoice",
            "usage_coverage": observed.get("problems", [])}


def accounting(events, partial=False):
    results = [event for event in events if event.get("type") == "result" and event.get("parent_tool_use_id") is None]
    last = results[-1] if results else {}
    usage = last.get("modelUsage")
    known = not partial and isinstance(usage, dict) and bool(usage)
    totals = {field: sum(model[field] for model in usage.values()) if known and all(isinstance(model.get(field), (int, float)) for model in usage.values()) else None
              for field in TOKEN_FIELDS}
    tokens = sum(totals.values()) if all(value is not None for value in totals.values()) else None
    return {"models": list(usage) if isinstance(usage, dict) else [], "model_usage": usage if known else None,
            "token_classes": totals, "tokens": tokens,
            "cost_usd": last.get("total_cost_usd") if not partial else None,
            "accounting_scope": "final cumulative result.modelUsage, includes subagents; never summed across resumes" if known else "unknown"}


def response(events):
    results = [event for event in events if event.get("type") == "result" and event.get("parent_tool_use_id") is None]
    if not results or results[-1].get("is_error"):
        return None
    result = results[-1]
    value = result.get("structured_output")
    if value is None:
        body = result.get("result", "")
        if not isinstance(body, str):
            return None
        body = body.strip()
        openings = re.findall(r"(?m)^[ \t]*```json[ \t]*\r?$", body)
        if openings:
            if len(openings) != 1:
                return None
            block = re.search(r"(?ms)^[ \t]*```json[ \t]*\r?\n(.*?)^[ \t]*```[ \t]*\r?$", body)
            if block is None:
                return None
            body = block.group(1)
        try:
            value = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return None
    if not isinstance(value, dict) or value.get("state") not in ("question", "complete", "blocked"):
        return None
    return value if all(isinstance(value.get(key), str) for key in ["question", "recommended_answer", "summary"]) else None


def isolation(events, plugins):
    initializations = [event for event in events if event.get("type") == "system" and event.get("subtype") == "init"]
    if not initializations:
        return {"verified": False, "reason": "init event absent", "plugins": None, "mcp_servers": None}
    init = initializations[-1]
    loaded, servers = init.get("plugins"), init.get("mcp_servers")
    if not isinstance(loaded, list) or not isinstance(servers, list):
        return {"verified": False, "reason": "init plugin/MCP fields absent", "plugins": loaded, "mcp_servers": servers}
    expected = {json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())["name"] for plugin in plugins}
    names = {plugin.get("name") if isinstance(plugin, dict) else plugin for plugin in loaded}
    unexpected = [name for name in names if not isinstance(name, str) or (name not in expected and not name.startswith("cc-plugin-"))]
    allowed_mcp = set()
    required_mcp = []
    for plugin in plugins:
        manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
        declared = manifest.get("mcpServers", {})
        if isinstance(declared, str):
            declared = json.loads((plugin / declared).read_text()).get("mcpServers", {})
        declared = dict(declared) if isinstance(declared, dict) else {}
        config = plugin / ".mcp.json"
        if config.is_file():
            declared.update(json.loads(config.read_text()).get("mcpServers", {}))
        for name in declared:
            aliases = {name, f"plugin_{manifest['name']}_{name}"}
            allowed_mcp.update(aliases)
            required_mcp.append(aliases)
    observed_mcp = {server.get("name", "").split(":")[-1] for server in servers if isinstance(server, dict)}
    unexpected_mcp = [server for server in servers if not isinstance(server, dict)
                      or server.get("name", "").split(":")[-1] not in allowed_mcp or server.get("status") != "connected"]
    missing_mcp = any(aliases.isdisjoint(observed_mcp) for aliases in required_mcp)
    return {"verified": not unexpected and not unexpected_mcp and not missing_mcp and expected.issubset(names),
            "reason": "expected session plugins and MCP only" if not unexpected and not unexpected_mcp and not missing_mcp else "unexpected plugins/MCP",
            "plugins": loaded, "mcp_servers": servers, "builtin_plugins": sorted(name for name in names if isinstance(name, str) and name.startswith("cc-plugin-")),
            "model": init.get("model"), "default_skills": init.get("skills")}


def copy_product(work, destination, source_only=False):
    destination.mkdir(parents=True)
    for file in work.rglob("*"):
        relative = file.relative_to(work)
        if any(part in {".git", ".software-factory", ".factory", ".claude", ".codex", ".tmp", ".benchmark-data", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "node_modules", ".venv", "docs"} for part in relative.parts):
            continue
        if file.is_symlink():
            raise ValueError(f"product symlink cannot be graded safely: {relative}")
        if file.is_file() and not file.name.startswith("test") and (file.suffix in {
                ".py", ".html", ".css", ".js", ".mjs", ".cjs", ".json", ".ts", ".tsx", ".jsx", ".sh", ".sql", ".toml", ".lock", ".svg", ".png", ".jpg", ".webp", ".woff2"} or
                (file.name.startswith("requirements") and file.suffix in {".txt", ".in"}) or
                (not source_only and file.suffix not in {".md", ".yaml", ".yml", ".pyc"})):
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)


GRADER = '''import json, sys, unittest
sys.path.insert(0, sys.argv[1])
suite = unittest.TestLoader().loadTestsFromNames(["test_existing", "test_acceptance"])
result = unittest.TextTestRunner(verbosity=2).run(suite)
with open(sys.argv[2], "x") as receipt:
    json.dump({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped)}, receipt)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def grading_sandbox(product, temporary, case, artifact, browser):
    from browser_runtime import installed_browser, sandbox_policy
    sandbox, node = shutil.which("sandbox-exec"), shutil.which("node")
    if platform.system() != "Darwin" or not sandbox or not node:
        raise ValueError("Grading requires macOS sandbox-exec and node; no unsandboxed fallback")
    runtime = installed_browser(node) if browser else None
    data = temporary / "runtime"
    data.mkdir()
    readable = [product, temporary, case / "grading", Path(node).resolve().parent.parent,
                Path(sys.executable).resolve().parent.parent]
    if runtime:
        readable.extend(Path(runtime[key]) for key in ("module", "core", "cache"))
    writable = [product, data, temporary / "completion.json"]
    if browser:
        artifact.mkdir(parents=True, exist_ok=True)
        writable.append(artifact.resolve())
        readable.append(artifact.resolve())
    policy = sandbox_policy(product, readable, writable, node, [], runtime)
    # Keep product execution out of host files even when they live outside HOME.
    roots = [*readable, Path("/System"), Path("/usr"), Path("/bin"), Path("/sbin"), Path("/dev"),
             Path("/private/var/db"), Path("/opt/homebrew"), Path("/Library"), Path("/private/etc")]
    policy += "(deny file-read-data (require-all (vnode-type REGULAR-FILE) " + " ".join(
        f"(require-not (subpath {json.dumps(str(path.resolve()))}))" for path in roots) + "))\n"
    ancestors = {parent for path in readable for parent in path.parents}
    policy += "".join(f"(allow file-read-metadata (literal {json.dumps(str(path))}))\n" for path in sorted(ancestors))
    profile = temporary / "grading.sb"
    profile.write_text(policy)
    env = {"PATH": os.pathsep.join([str(Path(node).resolve().parent), os.defpath]),
           "HOME": str(data), "TMPDIR": str(data)}
    if runtime:
        env["PLAYWRIGHT_MODULE"] = runtime["module"]
        env["PLAYWRIGHT_BROWSERS_PATH"] = runtime["cache"]
    if browser:
        env["BROWSER_ARTIFACTS"] = str(artifact.resolve())
    return [sandbox, "-f", str(profile)], env


def grade(case, work, artifact):
    metadata = json.loads((case / "case.json").read_text())
    if metadata.get("kind") == "fullstack":
        from fullstack_runtime import grade_fullstack
        return grade_fullstack(case, work, artifact)
    browser = metadata.get("kind") == "browser"
    trusted = [] if browser else [case / "fixture" / "test_existing.py", case / "grading" / "test_acceptance.py"]
    expected = metadata["test_count"] if browser else sum(sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        for node in ast.walk(ast.parse(file.read_text()))) for file in trusted)
    result = {"accepted": False, "tests": None, "failures": None, "errors": None, "skipped": None, "expected_tests": expected}
    with tempfile.TemporaryDirectory(prefix="factory-grade-") as temporary:
        product = Path(temporary) / "product"
        try:
            copy_product(work, product)
            for file in trusted:
                shutil.copy2(file, product / file.name)
            temporary = Path(temporary).resolve()
            receipt = temporary / "completion.json"
            prefix, env = grading_sandbox(product.resolve(), temporary, case, artifact, browser)
            if browser:
                artifact.mkdir(parents=True, exist_ok=True)
                env["BROWSER_ARTIFACTS"] = str(artifact.resolve())
                with subprocess.Popen([*prefix, shutil.which("node"), str(case / "grading/browser_acceptance.cjs")], cwd=product,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                      env=env, start_new_session=True) as process:
                    try:
                        stdout, stderr = process.communicate(timeout=120)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.communicate()
                        raise
                    check = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
            else:
                check = subprocess.run([*prefix, sys.executable, "-I", "-B", "-c", GRADER, str(product), str(receipt)], cwd=product, capture_output=True, text=True,
                                       timeout=30, env=env, check=False, start_new_session=True)
            output = check.stdout + check.stderr
            lines = [line.removeprefix("BENCHMARK_GRADE=") for line in check.stdout.splitlines() if line.startswith("BENCHMARK_GRADE=")]
            # shortcut: same-interpreter receipts prove ordinary completion, not malicious import isolation.
            if (browser and len(lines) == 1) or (not browser and receipt.is_file()):
                counts = json.loads(lines[0]) if browser else json.loads(receipt.read_text())
                if isinstance(counts, dict) and all(type(counts.get(field)) is int and counts[field] >= 0
                                                   for field in ["tests", "failures", "errors", "skipped"]):
                    result.update(counts)
                    result["accepted"] = check.returncode == 0 and result["tests"] == expected > 0 and all(result[field] == 0 for field in ["failures", "errors", "skipped"])
            result["returncode"] = check.returncode
        except (ValueError, subprocess.TimeoutExpired, OSError) as error:
            output = str(error)
            result["error"] = output
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.with_suffix(".txt").write_text(output)
    write_json(artifact.with_suffix(".json"), result)
    return result, output



def graded_files(work):
    """The product exactly as the grader copies it, path -> bytes."""
    with tempfile.TemporaryDirectory(prefix="factory-graded-") as temporary:
        root = Path(temporary) / "product"
        copy_product(work, root)
        return {str(file.relative_to(root)): file.read_bytes() for file in root.rglob("*") if file.is_file()}


def dependency_files(work):
    """Installed dependency trees the grader copies beside the product, path -> digest or link target."""
    found = {}
    for directory, names, files in os.walk(work):
        names[:] = [name for name in names if name not in {".git", ".tmp", ".benchmark-data", "__pycache__", ".cache", ".vite"}]
        if not {"node_modules", ".venv"} & set(Path(directory).relative_to(work).parts):
            continue
        for name in files + [name for name in names if (Path(directory) / name).is_symlink()]:
            path = Path(directory) / name
            found[str(path.relative_to(work))] = "link:" + os.readlink(path) if path.is_symlink() else hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def run_adapter(args, case, work, root, artifact, paths):
    """A fresh agent maps a copy of the delivered product to the QA contract; it may write only qa/** and benchmark.sh."""
    metadata = json.loads((case / "case.json").read_text())
    codex = getattr(args, "harness", "claude") == "codex"
    started = time.monotonic()
    copy = root / "work"
    shutil.copytree(work, copy, symlinks=True, ignore=shutil.ignore_patterns(".tmp"))
    (copy / "qa").mkdir(exist_ok=True)
    for name in ("contract.md", "qa_proxy.py"):
        shutil.copy2(case / "grading" / name, copy / "qa" / name)
    prompt = (case / metadata["adapter"]).read_text()
    artifact.mkdir(parents=True, exist_ok=True)
    record = {"prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "harness": getattr(args, "harness", "claude"),
              "model": args.model, "effort": getattr(args, "effort", "high"), "artifact": str(artifact),
              "manual_mapping_review": None}
    try:
        before, dependencies = graded_files(copy), dependency_files(copy)
    except ValueError as error:
        return copy, {**record, "error": str(error), "measurement_valid": False, "seconds": time.monotonic() - started}
    events = []
    if codex:
        from codex_adapter import collect_usage, prepare
        from codex_adapter import command as codex_command
        protected = [ROOT, args.out / "case-snapshots", args.out / "trials", *paths.values(), *secret_files(args.out, policy_files(args))]
        try:
            prepared = prepare(args.codex, copy, root / "codex", [], protected, args.model, args.effort)
            run = invoke(codex_command(prepared, prompt), copy, artifact / "adapter", args.timeout)
            events, session = codex_events(run.pop("events"))
            observed = collect_usage(session, artifact / "adapter-usage") if session else {}
            record["effort_policy_valid"] = bool(observed.get("records")) and all(r.get("effort") == record["effort"] for r in observed["records"])
            record.update(run, isolation={"verified": bool(prepared["isolation_evidence"]) and all(p["passed"] for p in prepared["isolation_evidence"]),
                                          "model": args.model, "probes": prepared["isolation_evidence"]},
                          **codex_accounting(observed, partial=run["timeout"]))
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            record["error"] = f"adapter policy admission failed: {error}"
    else:
        config = artifact / "adapter-settings.json"
        write_json(config, settings(copy, paths, "adapter", args.out, browser=True, hidden=policy_files(args)))
        run = invoke(command(args, paths, "adapter", config, str(uuid.uuid4()), False, args.budget_usd, prompt), copy, artifact / "adapter", args.timeout)
        events = run.pop("events")
        record.update(run, isolation=isolation(events, []), **accounting(events, partial=run["timeout"]))
        record["effort_policy_valid"] = True
        record["effort_policy_evidence"] = "configured CLI --effort; provider effort is not observed"
    record["model_policy_valid"] = bool(record.get("model_usage")) and all(
        name == args.model or usage.get("canonicalModel") == args.model
        for name, usage in (record.get("model_usage") or {}).items())
    record["measurement_valid"] = (record.get("isolation", {}).get("verified") is True
                                   and record["isolation"].get("model") == args.model
                                   and record["model_policy_valid"] and record.get("effort_policy_valid", not codex)
                                   and record.get("tokens") is not None and record.get("cost_usd") is not None
                                   and not record.get("timeout") and not record.get("interrupted") and not record.get("error"))
    record["response"] = response(events)
    try:  # The adapter's verdict on the product, in a file so both harnesses' fixed response schemas stay unchanged.
        report = json.loads((copy / "qa" / "report.json").read_text())
        record["report"] = report if isinstance(report, dict) else None
    except (OSError, ValueError):
        record["report"] = None
    try:
        after, dependencies_after = graded_files(copy), dependency_files(copy)
    except ValueError as error:
        return copy, {**record, "error": str(error), "measurement_valid": False, "seconds": time.monotonic() - started}
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    changed_dependencies = sorted(path for path in dependencies.keys() | dependencies_after.keys()
                                  if dependencies.get(path) != dependencies_after.get(path))
    patch = []
    for path in changed:
        old, new = before.get(path, b""), after.get(path, b"")
        try:
            patch.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                              f"a/{path}" if path in before else "/dev/null", f"b/{path}" if path in after else "/dev/null"))
        except UnicodeDecodeError:
            patch.append(f"Binary file {path} changed\n")
    patch.extend(f"Dependency file {path} changed\n" for path in changed_dependencies)
    (artifact / "adapter.diff").write_text("".join(line if line.endswith("\n") else line + "\n" for line in patch))
    outside = [path for path in changed if path != "benchmark.sh" and not path.startswith("qa/")] + changed_dependencies
    record.update(changed_paths=changed + changed_dependencies, product_paths_changed=outside,
                  diff=str(artifact / "adapter.diff"), seconds=time.monotonic() - started)
    record["measurement_valid"] = record["measurement_valid"] and not outside
    return copy, record


def product_does_not_start(adapter):
    """The adapter's evidence that the delivered product cannot start, or None."""
    report = adapter.get("report") or {}
    evidence = report.get("evidence")
    return evidence.strip() if report.get("product_starts") is False and isinstance(evidence, str) and evidence.strip() else None


def adapter_failure(adapter):
    """Why an adapter run cannot stand for the arm's product, or None."""
    state = (adapter.get("response") or {}).get("state")
    if adapter.get("error"):
        return adapter["error"]
    if adapter.get("timeout"):
        return "adapter timed out"
    if adapter.get("returncode"):
        return f"adapter exited {adapter['returncode']}"
    if adapter.get("isolation", {}).get("verified") is not True:
        return "adapter isolation unverified or contaminated: " + adapter.get("isolation", {}).get("reason", "policy probes absent or failed")
    if adapter["product_paths_changed"]:
        return "adapter changed product files: " + ", ".join(adapter["product_paths_changed"])
    if state != "complete" and not product_does_not_start(adapter):
        return f"adapter reported {state or 'no valid response'}: " + (adapter.get("response") or {}).get("summary", "")
    return None


def grade_delivery(args, case, work, artifact, paths):
    """Grade what the arm delivered. Adapter cases grade a copy after a fresh agent writes the QA adapter."""
    metadata = json.loads((case / "case.json").read_text())
    if not metadata.get("adapter"):
        return (*grade(case, work, artifact), None)
    root = Path(tempfile.mkdtemp(prefix="fb-adapter-", dir="/tmp")).resolve()
    try:
        copy, adapter = run_adapter(args, case, work, root, artifact.with_name(artifact.name + "-adapter"), paths)
        adapter["adapter_failed"] = adapter_failure(adapter)
        if adapter["adapter_failed"]:
            feedback = "Adapter failed; grading is not attributable to the arm: " + adapter["adapter_failed"]
            quality = {"accepted": False, "adapter_failed": True, "attributable_to_arm": False, "reason": adapter["adapter_failed"],
                       "tests": 0, "failures": 0, "errors": 0, "skipped": 0, "expected_tests": metadata["test_count"]}
            artifact.with_suffix(".txt").write_text(feedback)
            return quality, feedback, adapter
        if evidence := product_does_not_start(adapter):
            # The arm delivered a product that does not start: every check fails, and that is the arm's result.
            feedback = "The delivered product does not start: " + evidence
            ids = metadata.get("requirement_ids", [])
            quality = {"accepted": False, "attributable_to_arm": True, "product_starts": False, "evidence": evidence,
                       "tests": metadata["test_count"], "failures": metadata["test_count"], "errors": 0, "skipped": 0,
                       "expected_tests": metadata["test_count"],
                       "requirements": {identifier: {"passed": False, "checks": []} for identifier in ids},
                       "outcomes": [{**outcome, "accepted": False} for outcome in metadata.get("outcomes", [])]}
            artifact.with_suffix(".txt").write_text(feedback)
            return quality, feedback, adapter
        return (*grade(case, copy, artifact), adapter)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def workflow_evidence(work, arm, case):
    if arm.startswith("factory"):
        statuses = list(work.glob(".software-factory/changes/*/status.yaml"))
        details = []
        for path in statuses:
            text = path.read_text()
            gates = [bool(re.search(rf"^\s+{gate}:\s*\{{[^\n}}]*state:\s*(approved|skipped)\b", text, re.MULTILINE))
                     for gate in ["product", "architecture", "interface", "slices"]]
            details.append({"status": str(path.relative_to(work)), "reconciled": bool(re.search(r"^reconciled:\s*true\b", text, re.MULTILINE)), "gates_complete": all(gates)})
        return {"workflow_complete": len(details) == 1 and details[0]["reconciled"] and details[0]["gates_complete"], "evidence": details,
                "unverified_paths": ["gate approval provenance and document hashes require manual review"]}
    specs = [str(path.relative_to(work)) for path in work.glob("docs/superpowers/specs/*.md")]
    plans = [str(path.relative_to(work)) for path in work.glob("docs/superpowers/plans/*.md")]
    return {"workflow_complete": None, "evidence": {"specs": specs, "plans": plans},
            "unverified_paths": ["Review the selected Superpowers path in the trajectory; bounded work need not create spec/plan files"]}


def initial_prompt(case, arm, paths, browser_command=None, red_command=None):
    entry = "factory:factory-triage" if arm.startswith("factory") else "superpowers:using-superpowers"
    skill = paths["factory"] / "skills" / "factory-triage" / "SKILL.md" if arm.startswith("factory") else paths["superpowers"] / "skills" / "using-superpowers" / "SKILL.md"
    discovery = json.loads((case / "case.json").read_text()).get("track") == "discovery"
    verify = str(browser_command) if browser_command else shlex.join(json.loads((case / "case.json").read_text())["verify"])
    browser_note = (f"Browser verification command: run exactly {browser_command}, with no arguments, prefixes, suffixes, pipes or redirects. "
                    "It runs node --test over test*.cjs in this workspace inside a separate native sandbox. "
                    "Write new Node/Playwright checks and screenshot scripts as test*.cjs files here, then use that command. "
                    "Direct Chromium launch inside the normal Bash sandbox is unavailable. The wrapper and policy are immutable; "
                    "do not request a sandbox bypass. Run this exact command directly with Bash in every arm, including Context Mode; "
                    "nested sandbox-exec inside its MCP executor is unavailable. Keep dev serving on 127.0.0.1. "
                    "Keep every scratch file and review-panel file under this workspace's .tmp directory. "
                    "Pass these paths and operator constraints to every agent; do not use a shared /tmp/claude-UID path "
                    "or wait for files that a reviewer could not write.\n") if browser_command else ""
    if red_command:
        browser_note += f'Set status red_test_command to {red_command}. For RED proof, write exactly two fields to .software-factory/browser-red.json: {{"commit":"FULL_40_CHARACTER_ANCESTOR_COMMIT_SHA","checkpoint":"SAFE_TOKEN"}}. Replace the placeholders; commit must match [0-9a-f]{{40}} and checkpoint must match [A-Za-z0-9_-]{{1,64}}. Then run exactly {red_command} without arguments via Bash. It checks an isolated clone and leaves the live GREEN checkout unchanged.\n'
    context_note = ("For large non-browser repository or command outputs, use Context Mode ctx_execute, ctx_batch_execute, "
                    "ctx_index and ctx_search when available; ToolSearch may discover deferred tools. Preserve raw test evidence: "
                    "a retrieval summary is not verification proof. The exact browser checker still runs directly through Bash.\n") if arm == "factory-context" else ""
    return f"""This is an isolated, synthetic local benchmark with a recorded operator, not production approval.
{"Task:" if discovery else "Task (the same neutral requirements are given to every workflow):"}
{(case / 'task.md').read_text()}
Start by invoking Skill {entry}; if the skill is unavailable, read {skill}. Follow its full applicable workflow and all handoffs until local completion, including review and, for Factory, reconcile. Do not replace this with a code-only pass.
Operator policy: no external network, remote git operations, dependency installations, production changes. Local research worktrees are permitted only under this workspace’s .tmp directory; keep research read-only and remove them when finished. Localhost serving and browser checks are permitted for browser cases. This fresh repository is already isolated. Unsigned synthetic local commits are permitted. Keep workflow documents locally; never alter skill/kit snapshots or original source directories. Report unavailable optional lenses/tools as skipped; do not install them. Propose any kit updates locally. All subagents must inherit the requested model. {"" if discovery else f"Use {verify} for fixture checks. "}There is no extra linter/typechecker configured. For browser cases, an installed Playwright module is provided through PLAYWRIGHT_MODULE; use the provided browser verification command without installing dependencies. Browser imports in Context Mode's Bun JavaScript runtime are not supported by this adapter.
{browser_note}{context_note}
Whenever the workflow requires a user choice or approval, stop and return the question plus a specific recommended answer; never answer it yourself. Do not use AskUserQuestion (print mode). Return exactly ONE JSON object, without commentary outside it, with these keys: {{"state":"question|complete|blocked","question":"...","recommended_answer":"...","summary":"..."}}. Complete means the full local workflow has finished; blocked means a bounded obstruction, not a pending agent. Wait for every agent you start to finish before returning. A handoff to the next skill continues automatically unless it requires a user answer. Every controller reply is a simulated operator answer, valid only inside this synthetic repository; the copied Factory gate rules explicitly permit forwarding it verbatim to step agents.
"""


def codex_prompt(case, arm, paths, browser_command=None, red_command=None):
    factory = arm.startswith("factory")
    entry = paths["factory"] / "skills/factory-triage/SKILL.md" if factory else paths["superpowers"] / "skills/using-superpowers/SKILL.md"
    fullstack = json.loads((case / "case.json").read_text()).get("kind") == "fullstack"
    discovery = json.loads((case / "case.json").read_text()).get("track") == "discovery"
    coaching = "" if discovery else "Record stack choices, rationale, explicit FR/NFR agreements, exclusions and unresolved assumptions in DECISIONS.md. Requirements in the shared task cannot be negotiated away. "
    dependency = ("Project-scoped pinned dependency setup is permitted from registry.npmjs.org, pypi.org and files.pythonhosted.org. No global installations, remote databases or external product services." if fullstack else "No dependency installations or external network.")
    return f"""You are the root Codex CLI agent in a disposable local benchmark repository.
Read and apply the pinned workflow entry {entry}. Follow every applicable stage, review and finish; Factory must reconcile. Continue handoffs automatically, stopping only at unanswered user decisions.
TASK:\n{(case / 'task.md').read_text()}
TOOL ADAPTATION: Skill/invokeSkill means read the named pinned SKILL.md and execute its instructions; there is no installed Claude Skill tool. Agent/general-purpose means the actual native full-capability subagent interface described in your CLI tool documentation. Use available tool names; never fabricate hooks, unavailable tools or approvals. Native agents may implement their assigned files. All children inherit this session model and effort: do not override either. Interpret Factory ARGUMENTS as the explicit change slug you select; resolve working-directory placeholders to this repository. Forward operator answers verbatim to child stages.
For Superpowers also read {paths['superpowers'] / 'skills/using-superpowers/references/codex-tools.md'} if present for canonical tool mapping.
POLICY: {dependency} Local unsigned commits, local read-only research worktrees under .tmp, localhost application serving, and browser verification are allowed. Keep scratch and reviewer artifacts inside .tmp. No remote git, production actions, or changes to pinned workflow snapshots. Report unavailable optional capabilities as skipped. Never bypass the configured sandbox.
BROWSER: invoke mcp__benchmark_browser__check with zero arguments for browser verification. Write Node/Playwright test*.cjs checks in this workspace; PLAYWRIGHT_MODULE names the installed module. This declared fixed MCP capability invokes the immutable native Seatbelt wrapper outside the actor sandbox. Never run {browser_command} or {red_command} through the shell: nested sandbox-exec cannot launch Chromium. Whenever a workflow/status test_command names {browser_command}, execute the check MCP capability instead, preserving the recorded command identity and full evidence. For RED proof keep red_test_command {red_command}; write .software-factory/browser-red.json with exactly commit (full ancestor SHA) and checkpoint (safe token), then invoke mcp__benchmark_browser__red_check with zero arguments. This changes only the execution surface; all RED/GREEN proof requirements remain. The live GREEN checkout must remain unchanged. Pass this mapping to every child.
{coaching}Completion includes applicable workflow review, fixes and finish. Await every child and close completed child handles before the root terminal response, so descendant usage is observable.
Whenever a human choice is required return one JSON object matching the response schema, state question, question text and recommended_answer. Do not answer it yourself or use a blocking user-question tool. Controller replies are recorded synthetic operator answers valid only here. Return complete only after the full workflow finishes, or blocked for a bounded obstruction with evidence. An unfinished child is not a blocker. Final response must have exactly state, question, recommended_answer, summary, all strings; state is question|complete|blocked.
"""


def trial(args, case, arm, repeat, paths):
    codex = getattr(args, "harness", "claude") == "codex"
    unlimited = getattr(args, "until_complete", False)
    browser = json.loads((case / "case.json").read_text()).get("kind") in {"browser", "fullstack"}
    discovery = json.loads((case / "case.json").read_text()).get("track") == "discovery"
    trial_id = f"{case.name}-{arm}-{repeat + 1}"
    artifact = args.out / "trials" / trial_id
    artifact.mkdir(parents=True, exist_ok=getattr(args, "resume_trial", False))
    session = None if codex else str(uuid.uuid4())
    observed = {}
    started = time.monotonic()
    record = {"id": trial_id, "case": case.name, "arm": arm, "repeat": repeat + 1, "session_id": session,
              "manual_followup": None, "manual_mapping_review": None, "simulated_questions": [], "repair_rounds": 0, "initial_quality": None,
              "environment_recovery_rounds": 0,
              "final_quality": None, "status": "incomplete", "invocations": [], "requested_model": args.model,
              "time_to_first_result_seconds": None, "manual_workflow_review": None,
              "requested_effort": getattr(args, "effort", "high")}
    resuming = getattr(args, "resume_trial", False)
    if resuming:
        record = json.loads((artifact / "progress.json").read_text())
        session = record["session_id"]
        if record["case_sha256"] != tree_hash(case):
            raise ValueError("Cannot resume after grading inputs changed")
        if record["status"] == "accepted":
            record.setdefault("acceptance_history", []).append({"quality": record.get("final_quality"),
                                                               "wall_seconds": record.get("wall_seconds"),
                                                               "workflow_complete": record.get("workflow_complete"),
                                                               "manual_workflow_review": record.get("manual_workflow_review")})
            record["status"] = "incomplete"
            record["final_quality"] = None
            record["manual_workflow_review"] = None
            record["workflow_finish_requested"] = True
    comparison = args.comparison if hasattr(args, "comparison") else comparison_inputs(args)
    record["comparison"] = public_comparison(comparison)
    previous_wall = record.get("wall_seconds", 0) if resuming else 0
    record["interrupted"] = False
    record.setdefault("decisions", [])
    record.setdefault("progress", [])
    record.setdefault("workflow_finish_rounds", 0)
    record["raw_workspace_retained"] = False
    record["case_sha256"] = tree_hash(case)
    record["benchmark_sha256"] = BENCHMARK_SHA256
    if discovery:
        record["repair_policy"] = "discovery track: hidden test feedback never reaches the arm; repair rounds forced to 0"
    events, partial = [], False
    with retained_runtime(artifact, record) as temporary:
        work = (Path(temporary) / "work").resolve()
        if not resuming:
            shutil.copytree(case / "fixture", work, ignore=IGNORED)
        browser_runtime = record.get("browser_verification")
        if browser and not resuming:
            from browser_runtime import prepare_browser_check
            browser_runtime = prepare_browser_check(Path(temporary) / "browser-check", work, [ROOT, args.out, *policy_files(args)], **({"codex_sandbox": True} if codex else {}))
            record["browser_verification"] = browser_runtime
        if resuming:
            paths = {name: Path(path) for name, path in record["runtime_paths"].items()}
        if arm == "factory-context" and not resuming:
            paths = dict(paths)
            paths["context-mode"], record["context_isolation"] = prepare_context(
                paths["context-mode"], Path(temporary) / "context-plugin", work,
                [CASES, args.out / "case-snapshots", args.out / "trials", paths["superpowers"],
                 *secret_files(args.out, policy_files(args))], browser=browser)
        if arm.startswith("factory") and not resuming:
            pins = paths["factory"] / "kit" / "packs.lock.yaml"
            pins = pins.read_text().partition("\npacks:\n")[2] if pins.is_file() else ""
            (work / ".software-factory").mkdir(exist_ok=True)
            (work / ".software-factory" / "factory.lock").write_text(
                f"framework: {{ dev_path: {Path(paths['factory']).resolve()} }}\npacks:\n{pins}\nskills_linked: []\n")
        for cmd in [["git", "init", "-q", "-b", "main"], ["git", "config", "user.name", "Benchmark"], ["git", "config", "user.email", "benchmark@example.invalid"],
                    ["git", "config", "commit.gpgsign", "false"], ["git", "config", "tag.gpgsign", "false"],
                    ["git", "config", "core.hooksPath", os.devnull],
                    ["git", "add", "."], ["git", "commit", "-qm", "Synthetic benchmark baseline"]]:
            if not resuming:
                subprocess.run(cmd, cwd=work, check=True, capture_output=True, text=True)
        with (work / ".git/info/exclude").open("a") as exclusions:
            exclusions.write("\n.tmp/\n__pycache__/\n*.py[cod]\n")
        config = artifact / "settings.json"
        browser_command = browser_runtime["command"] if browser_runtime else None
        red_command = browser_runtime.get("red_command") if browser_runtime else None
        write_json(config, settings(work, paths, arm, args.out, browser=browser, browser_command=browser_command, red_command=red_command,
                                    hidden=policy_files(args)))
        prompt = initial_prompt(case, arm, paths, browser_command=browser_command, red_command=red_command)
        prepared = None
        if codex:
            from codex_adapter import prepare
            active = [paths["factory"] if arm.startswith("factory") else paths["superpowers"]]
            protected = [ROOT, args.out / "case-snapshots", args.out / "trials", paths["superpowers"] if arm.startswith("factory") else paths["factory"],
                         *secret_files(args.out, policy_files(args))]
            prepared_path = Path(temporary) / "codex" / "codex-prepared.json"
            admission_error = None
            try:
                if resuming and record.get("codex_prepared_sha256") != hashlib.sha256(prepared_path.read_bytes()).hexdigest():
                    raise ValueError("Cannot resume after prepared Codex policy changed")
                prepared = json.loads(prepared_path.read_text()) if resuming else prepare(
                    args.codex, work, Path(temporary) / "codex", active, protected,
                    args.model, args.effort, browser_runtime, dependency_setup=json.loads((case / "case.json").read_text()).get("kind") == "fullstack")
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                admission_error = str(error)
                prepared = {"isolation_evidence": [{"passed": False, "error": admission_error}], "limitations": ["Policy admission failed; no model invocation permitted"]}
            record["codex_prepared"] = prepared
            if not resuming and not admission_error and prepared_path.is_file():
                record["codex_prepared_sha256"] = hashlib.sha256(prepared_path.read_bytes()).hexdigest()
            prompt = codex_prompt(case, arm, paths, browser_command, red_command)
        if comparison.get("approved_spec"):
            prompt += "\nSHARED APPROVED SPECIFICATION (execution input):\n" + comparison["approved_spec"]
        if comparison.get("policy") and not discovery:  # a discovery arm learns the owner's answers only by asking
            prompt += "\nFIXED OPERATOR PERSONA AND PREFERENCES:\n" + json.dumps(comparison["policy"])
        if resuming:
            prompt = record.get("pending_prompt", prompt)
            if getattr(args, "resume_answer", None):
                if not record.get("pending_question"):
                    raise ValueError("--answer requires a retained unanswered question")
                record["decisions"].append({"question": record.pop("pending_question")["question"],
                                             "answer": args.resume_answer, "operator": "human", "mode": record["comparison"]["mode"],
                                             "elapsed_seconds": previous_wall,
                                             "after_delivery": record.get("time_to_first_result_seconds") is not None})
                write_json(artifact / "decisions.json", record["decisions"])
                prompt = "SIMULATED USER ANSWER (actual human benchmark response, local repository only):\n" + args.resume_answer
            for trajectory in sorted(artifact.glob("turn-*.jsonl")):
                for line in trajectory.read_text().splitlines():
                    try:
                        raw = json.loads(line)
                        if not codex:
                            events.append(raw)
                    except json.JSONDecodeError:
                        continue
        record["runtime_paths"] = {name: str(path) for name, path in paths.items()}
        plugins = [paths["factory"] if arm.startswith("factory") else paths["superpowers"]] + ([paths["context-mode"]] if arm == "factory-context" else [])
        snapshot_hashes = record.get("plugin_snapshot_hashes") if resuming else {str(plugin): tree_hash(plugin) for plugin in plugins}
        if not snapshot_hashes or any(tree_hash(Path(path)) != digest for path, digest in snapshot_hashes.items()):
            raise ValueError("Cannot run/resume after pinned plugin snapshots changed")
        record["plugin_snapshot_hashes"] = snapshot_hashes
        if resuming and record.get("workflow_finish_requested"):
            prompt = ("SHARED WORKFLOW FINISH REQUEST: complete" if discovery else "SHARED WORKFLOW FINISH REQUEST: independent product acceptance already passed. Complete") + " the remaining applicable review, sign-off and finish/reconcile steps without changing agreed requirements. Keep the structured question/completion protocol."
        record["pending_prompt"] = prompt
        write_json(artifact / "progress.json", record)
        preflight = ({"returncode": 1 if admission_error else 0, "timeout": False, "events": [], "seconds": 0,
                      "policy_evidence": prepared["isolation_evidence"]} if codex else
                     invoke(command(args, paths, arm, config, str(uuid.uuid4()), False, args.budget_usd, init=True), work, artifact / "preflight", min(args.timeout, 60)))
        record["preflight"] = {key: value for key, value in preflight.items() if key != "events"}
        record["interrupted"] = preflight.get("interrupted", False)
        if preflight["returncode"] != 0 or preflight["timeout"]:
            record["stop_reason"] = "preflight failed"
        elif not codex and isolation(preflight["events"], plugins)["reason"] == "unexpected plugins/MCP":
            record["stop_reason"] = "preflight found unrelated plugins/MCP"
        else:
            while True:
                remaining_time = float("inf") if unlimited else args.timeout - (time.monotonic() - started)
                cost = accounting(events)["cost_usd"] or 0
                if not unlimited and (remaining_time <= 0 or cost >= args.budget_usd):
                    record["stop_reason"] = "trial time/budget cap"
                    partial = remaining_time <= 0
                    break
                number = len(record["invocations"])
                record["pending_prompt"] = prompt
                write_json(artifact / "progress.json", record)
                (artifact / f"turn-{number:02d}.prompt.txt").write_text(prompt)
                if codex:
                    from codex_adapter import collect_usage
                    from codex_adapter import command as codex_command
                    argv = codex_command(prepared, prompt, session)
                else:
                    argv = command(args, paths, arm, config, session, number > 0, args.budget_usd - cost, prompt)
                run = invoke(argv,
                             work, artifact / f"turn-{number:02d}", remaining_time)
                raw_events = run.pop("events")
                if codex:
                    adapted, new_session = codex_events(raw_events)
                    session = new_session or session
                    record["session_id"] = session
                    events.extend(adapted)
                    observed = collect_usage(session, artifact / f"usage-{number:02d}") if session else {}
                else:
                    events.extend(raw_events)
                run["stage"] = "execution"
                run["turn"] = number
                run["elapsed_seconds"] = previous_wall + time.monotonic() - started
                run["observed_usage"] = codex_accounting(observed, partial=run["timeout"]) if codex else accounting(events, partial=run["timeout"])
                record["invocations"].append(run)
                record["progress"].append({"turn": number, "elapsed_seconds": run["elapsed_seconds"],
                                           "stage": (response(events) or {}).get("state", "interrupted"),
                                           "usage": run["observed_usage"]})
                if run["timeout"] or run["returncode"] != 0:
                    partial = True
                    record["interrupted"] = run.get("interrupted", False)
                    record["stop_reason"] = "model process timeout/error"
                    break
                if not codex and isolation(events, plugins)["reason"] == "unexpected plugins/MCP":
                    record["stop_reason"] = "initialization found unrelated plugins/MCP"
                    break
                answer = response(events)
                if answer is None:
                    record["stop_reason"] = "missing/invalid structured response"
                    partial = True
                    break
                if answer["state"] == "question":
                    record["simulated_questions"].append(answer)
                    write_json(artifact / "questions.json", record["simulated_questions"])
                    if not unlimited and len(record["simulated_questions"]) > args.max_questions:
                        record["stop_reason"] = "question cap"
                        break
                    try:
                        decision_started = time.monotonic()
                        decision = operator_answer(comparison, answer)
                    except KeyboardInterrupt:
                        partial = True
                        record["interrupted"] = True
                        record["pending_question"] = answer
                        record["stop_reason"] = "human operator interrupted"
                        break
                    except (ValueError, EOFError) as error:
                        record["stop_reason"] = str(error)
                        record["pending_question"] = answer
                        break
                    record["decisions"].append({"question": answer["question"], "answer": decision,
                                                 "operator": record["comparison"]["operator"],
                                                 "mode": record["comparison"]["mode"],
                                                 "human_answer_seconds": time.monotonic() - decision_started if record["comparison"]["operator"] == "human" else None,
                                                 "elapsed_seconds": previous_wall + time.monotonic() - started,
                                                 "after_delivery": record["time_to_first_result_seconds"] is not None})
                    write_json(artifact / "decisions.json", record["decisions"])
                    prompt = "SIMULATED USER ANSWER (recorded benchmark operator, synthetic local repository only; no production or remote git authority):\n" + decision + "\nContinue the same workflow/session; return the structured question/completion schema again."
                    continue
                if answer["state"] == "blocked":
                    if browser_command and not record["environment_recovery_rounds"]:
                        record["environment_recovery_rounds"] = 1
                        prompt = ("SHARED BROWSER CAPABILITY REMINDER (one per trial, recorded separately from product repairs): "
                                  f"the native browser checker is verified. Call Bash with command EXACTLY {browser_command}. "
                                  "Do not add a prefix, pipe, redirect, argument, semicolon or echo. Those additions keep the command "
                                  "inside the ordinary Bash sandbox, where Chromium and nested sandbox-exec cannot run. Bash reports "
                                  "the exit status itself. Do not weaken any sandbox or permission. If this exact call fails, return "
                                  "blocked with its actual output; otherwise continue the applicable full workflow and JSON protocol.")
                        if codex:
                            prompt = "SHARED BROWSER CAPABILITY REMINDER: invoke mcp__benchmark_browser__check with zero arguments. The declared fixed MCP bridge runs the immutable native Seatbelt wrapper outside the actor sandbox. Do not launch the wrapper through the shell. For isolated RED proof invoke mcp__benchmark_browser__red_check after writing the validated request JSON. If the capability fails return blocked with actual output; otherwise continue the full workflow and structured response."
                        continue
                    record["stop_reason"] = answer["summary"]
                    break
                if record["time_to_first_result_seconds"] is None:
                    record["time_to_first_result_seconds"] = previous_wall + time.monotonic() - started
                quality, feedback, adapter = grade_delivery(args, case, work, artifact / f"grade-{record['repair_rounds']}", paths)
                if adapter:
                    record.setdefault("adapter_runs", []).append(adapter)
                    record["manual_mapping_review"] = None
                    started += adapter["seconds"]  # adapter time is reported separately, never as arm time
                if record["initial_quality"] is None:
                    record["initial_quality"] = quality
                record["final_quality"] = quality
                if quality.get("adapter_failed"):
                    record["stop_reason"] = "adapter failed; grading is not attributable to the arm: " + quality["reason"]
                    break
                if quality["accepted"]:
                    if unlimited and arm.startswith("factory") and workflow_evidence(work, arm, case).get("workflow_complete") is not True:
                        record["workflow_finish_rounds"] += 1
                        prompt = ("SHARED WORKFLOW FINISH REQUEST: Factory gate/reconcile evidence is incomplete." if discovery else "SHARED WORKFLOW FINISH REQUEST: independent product acceptance passed, but Factory gate/reconcile evidence is incomplete.") + " Finish the full applicable workflow including review, user sign-off and reconcile. Do not change agreed requirements. This is workflow completion, not a product repair; return the structured question/completion protocol."
                        record["pending_prompt"] = prompt
                        continue
                    record["workflow_finish_requested"] = False
                    record["status"] = "accepted"
                    record["stop_reason"] = "trusted acceptance tests passed"
                    break
                if discovery:
                    record["stop_reason"] = "hidden acceptance failed; discovery cases return no test feedback"
                    break
                if not unlimited and record["repair_rounds"] >= args.repair_rounds:
                    record["stop_reason"] = "repair cap with failing acceptance"
                    break
                record["repair_rounds"] += 1
                prompt = "SHARED BENCHMARK TEST FAILURE FEEDBACK (same policy for all arms). Repair the product and complete the workflow again; preserve the structured response schema.\n" + feedback
        record.update(workflow_evidence(work, arm, case))
        record["isolation"] = ({"verified": all(p["passed"] for p in prepared["isolation_evidence"]),
                                "model": args.model, "reason": "local policy probes passed",
                                "limitations": prepared["limitations"]} if codex else isolation(events or preflight["events"], plugins))
        record.update(codex_accounting(observed, partial=partial) if codex else accounting(events, partial=partial))
        if codex:
            record["codex_usage"] = observed
            record["effort_policy_valid"] = bool(observed.get("records")) and all(r.get("effort") == args.effort for r in observed["records"])
            decisions = work / "DECISIONS.md"
            record["product_decisions"] = decisions.read_text() if decisions.is_file() else None
            quality = record.get("final_quality") or {}
            record["requirement_outcomes"] = quality
            record["price_per_accepted_application_estimate"] = record["cost_usd"] if record["status"] == "accepted" else None
            record["price_per_predefined_journey_estimate"] = record["cost_usd"] / len(quality["outcomes"]) if record["cost_usd"] is not None and quality.get("accepted") and quality.get("outcomes") else None
        record["context_usage"] = context_usage(events, arm == "factory-context")
        record["model_policy_valid"] = bool(record["models"]) and all(
            name == args.model or usage.get("canonicalModel") == args.model
            for name, usage in (record["model_usage"] or {}).items())
        record["measurement_valid"] = (record["isolation"]["verified"] and not partial and record["tokens"] is not None
                                       and record["isolation"].get("model") == args.model and record["model_policy_valid"] and record.get("effort_policy_valid", True))
        record["plugin_snapshot_hashes"] = snapshot_hashes
        record["snapshots_unchanged"] = all(tree_hash(Path(path)) == digest for path, digest in snapshot_hashes.items())
        if browser_runtime:
            record["browser_verification_unchanged"] = all(
                hashlib.sha256(Path(browser_runtime[key]).read_bytes()).hexdigest() == digest
                for key, digest in browser_runtime["sha256"].items())
            record["snapshots_unchanged"] = record["snapshots_unchanged"] and record["browser_verification_unchanged"]
        if codex and prepared_path.is_file():
            record["prepared_policy_unchanged"] = hashlib.sha256(prepared_path.read_bytes()).hexdigest() == record.get("codex_prepared_sha256")
            record["snapshots_unchanged"] = record["snapshots_unchanged"] and record["prepared_policy_unchanged"]
        record["measurement_valid"] = (record["measurement_valid"] and record["snapshots_unchanged"]
                                       and all(adapter.get("measurement_valid") is True for adapter in record.get("adapter_runs", [])))
        try:
            retain_workspace(work, artifact, record)
        except ValueError as error:
            record["source_snapshot_error"] = str(error)
            record["measurement_valid"] = False
    record["wall_seconds"] = previous_wall + time.monotonic() - started
    record["time_to_accepted_seconds"] = record["wall_seconds"] if record["status"] == "accepted" else None
    record["simulated_question_count"] = len(record["simulated_questions"])
    record["workflow_complete"] = record.get("workflow_complete") if record["status"] == "accepted" else False
    record["comparative_valid"] = record["measurement_valid"] and record["workflow_complete"] is True and record["manual_workflow_review"] is True and record["comparison"]["valid_decision_protocol"] and (not record.get("adapter_runs") or record.get("manual_mapping_review") is True)
    write_json(artifact / "result.json", record)
    write_json(artifact / "progress.json", record)
    return record


def context_usage(events, enabled):
    calls, hooks = {}, []
    for event in events:
        for block in (event.get("message") or {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use" and "ctx_" in block.get("name", ""):
                calls[block.get("id", json.dumps(block, sort_keys=True))] = block["name"]
        if event.get("type") == "system" and "hook" in event.get("subtype", ""):
            hooks.append(event)
    return {"enabled": enabled, "used": bool(calls), "tool_calls": list(calls.values()),
            "deduplicated_tool_call_count": len(calls), "hook_responses": hooks,
            "hook_scope": "all observed hook responses; attribution to Context Mode is not inferred",
            "interpretation": "Usage is observed; no savings inferred without matched trials."}


def copy_screenshots(record, source, destination):
    links = []
    quality = record.get("snapshot_quality") or record.get("final_quality") or {}
    for name, value in quality.get("screenshots", {}).items():
        path = Path(value)
        if name in {"desktop", "mobile"} and path.is_file() and path.is_relative_to(source.parent):
            destination.mkdir(exist_ok=True)
            target = destination / f"{name}.png"
            if not target.exists():
                shutil.copy2(path, target)
            links.append(f"[{name}]({destination.name}/{name}.png)")
    return links


def report(args, records, provenance, blind=False):
    write_json(args.out / "summary.json", {"model": args.model, "trials": records, "operator": public_comparison(getattr(args, "comparison", None) or {}), "manual_followup": None,
                                           "provenance": provenance, "interpretation": "No automatic ranking. Partial or isolation-unverified runs are not valid comparisons."})
    lines = ["# Workflow benchmark", "", "Recorded operator decisions; actual human follow-up remains null until manually recorded. Legacy recommended-answer simulations are diagnostic only. Quality is trusted post-execution acceptance, not agent claims. Tokens include cache classes and subagents from the final cumulative result; resume records are never added together.", "",
             "| Case | Arm | Repeat | Initial quality | Final quality | Raw snapshot quality | Committed checkpoint quality | Context calls | Repairs | Environment reminders | Tokens | USD | First result seconds | Total seconds | Operator questions | Workflow | Measurement valid | Full comparison valid |",
             "|---|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
    for record in records:
        quality = lambda value: "pass" if value and value["accepted"] else "fail" if value else "unmeasured"
        tokens = record['tokens'] if record['tokens'] is not None else (
            f">={record['tokens_lower_bound']}" if record.get('tokens_lower_bound') is not None else "unknown")
        dollars = (str(record['cost_usd']) + (' estimated' if record.get('estimated_api_usd') is not None else '')) if record['cost_usd'] is not None else (
            f">={record['cost_usd_lower_bound']}" if record.get('cost_usd_lower_bound') is not None else "unknown")
        lines.append(f"| {record['case']} | {record['arm']} | {record['repeat']} | {quality(record['initial_quality'])} | {quality(record['final_quality'])} | {quality(record.get('snapshot_quality'))} | {quality(record.get('committed_checkpoint_quality'))} | {record.get('context_usage', {}).get('deduplicated_tool_call_count', 0)} | {record['repair_rounds']} | {record.get('environment_recovery_rounds', 0)} | {tokens} | {dollars} | {record['time_to_first_result_seconds']} | {record['wall_seconds']:.1f} | {record['simulated_question_count']} | {record['workflow_complete']} | {record['measurement_valid']} | {record['comparative_valid']} |")
    lines += ["", "Snapshot quality grades even unfinished products; it does not establish workflow completion or delivery time. >= values are the last observed cumulative usage before an interrupted invocation, not exact totals. Measurement validity covers recorded model/isolation/accounting only. Full comparison validity additionally needs confirmed workflow completion and manual trajectory review (unmeasured until reviewed). Do not infer real human follow-up savings. Codex USD is an API-rate estimate, actual invoice cost is unknown. Legacy Claude builtin cc-plugin components may remain active even with bundled skills disabled. Blind source review below excludes workflow documents."]
    for record in records:
        lines.append(f"\n{record.get('id', record['case'])}: raw snapshot checkout {record.get('checkout', 'unknown historical checkout')}; "
                     f"separate committed checkpoint {record.get('committed_checkpoint', 'none')}; "
                     f"Context enabled/used {record.get('context_usage', {}).get('enabled', False)}/{record.get('context_usage', {}).get('used', False)}; "
                     f"human follow-up {record.get('manual_followup')}. No checkpoint is assumed to be the latest completed code.")
    (args.out / "report.md").write_text("\n".join(lines) + "\n")
    if not blind:
        return
    anonymous = args.out / "blind-review"
    if anonymous.is_dir() and (args.out / "blind-review-key.json").is_file():
        retained = json.loads((args.out / "blind-review-key.json").read_text())
        by_id = {record["id"]: record for record in records}
        for label, trial_id in retained.items():
            if trial_id in by_id:
                copy_screenshots(by_id[trial_id], args.out / "trials" / trial_id / "source", anonymous / label)
        return  # Regrading retained products preserves blind labels and human notes.
    anonymous.mkdir(exist_ok=True)
    shuffled = list(records)
    random.SystemRandom().shuffle(shuffled)
    mapping, review = {}, ["# Blind source review", "", "Grade correctness, maintainability, unnecessary complexity, and regression risk before opening the key. Workflow documents are excluded.", ""]
    for number, record in enumerate(shuffled, 1):
        label = f"submission-{number:03d}"
        source = args.out / "trials" / record["id"] / "source"
        if source.exists():
            shutil.copytree(source, anonymous / label, dirs_exist_ok=True)
        images = copy_screenshots(record, source, anonymous / label)
        mapping[label] = record["id"]
        review.append(f"- {label}: source `{label}/`; correctness __/5; clarity __/5; regression risk __/5; notes: ___")
        if images:
            review.append("  " + ", ".join(images) + "; visual quality ___; changes needed before shipping: ___")
    (anonymous / "review.md").write_text("\n".join(review) + "\n")
    write_json(args.out / "blind-review-key.json", mapping)


def regrade(out):
    """Grade unfinished snapshots without pretending the workflow finished or rerunning an arm.

    Adapter cases still run their fixed adapter agent on a copy, exactly as a trial's grade does."""
    data = json.loads((out / "summary.json").read_text())
    saved = json.loads((out / "run-config.json").read_text()) if (out / "run-config.json").is_file() else None
    for record in data["trials"]:
        artifact = out / "trials" / record["id"]
        def graded(case, source, target, record=record):
            if saved is None:
                return grade(case, source, target)[0]
            options = argparse.Namespace(**{**saved["args"], "out": out})
            quality, _, adapter = grade_delivery(options, case, source, target, {name: Path(path) for name, path in saved["paths"].items()})
            if adapter:
                record.setdefault("adapter_runs", []).append(adapter)
                record["manual_mapping_review"] = None
                record["measurement_valid"] = record.get("measurement_valid", False) and adapter.get("measurement_valid") is True
                record["comparative_valid"] = (record.get("comparative_valid", False) and record["measurement_valid"]
                                               and record.get("manual_mapping_review") is True)
            return quality
        case = out / "case-snapshots" / record["case"]
        if not case.exists():
            case = CASES / record["case"]
        if record.get("case_sha256") != tree_hash(case):
            raise ValueError(f"{record['id']}: grading inputs changed; retain the original result")
        record["snapshot_quality"] = record["final_quality"] if record["status"] != "incomplete" else None
        if record["snapshot_quality"] is None:
            record["snapshot_quality"] = graded(case, artifact / "workspace", artifact / "grade-snapshot")
        record["snapshot_quality_checkout"] = record.get("checkout", {"label": "historical checkout identity unavailable; not proven latest code"})
        if record.get("committed_checkpoint"):
            record["committed_checkpoint_quality"] = graded(case, artifact / "committed-source", artifact / "grade-committed-checkpoint")
        if record["tokens"] is None:
            events = []
            for trajectory in sorted(artifact.glob("turn-*.jsonl")):
                for line in trajectory.read_text().splitlines():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            observed = accounting(events)
            record["tokens_lower_bound"] = observed["tokens"]
            record["cost_usd_lower_bound"] = observed["cost_usd"]
            record["observed_token_classes"] = observed["token_classes"]
        write_json(artifact / "result.json", record)
    data["provenance"]["offline_regrader_sha256"] = BENCHMARK_SHA256
    write_json(out / "provenance.json", data["provenance"])
    report(argparse.Namespace(out=out, model=data["model"]), data["trials"], data["provenance"], blind=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    rescore = commands.add_parser("regrade", help="grade partial products; adapter cases invoke a potentially billable grader agent")
    rescore.add_argument("--out", type=Path, required=True)
    resume = commands.add_parser("resume", help="resume an interrupted retained trial without rebuilding its repository")
    resume.add_argument("--out", type=Path, required=True)
    resume.add_argument("--trial", required=True)
    resume.add_argument("--timeout", type=float)
    resume.add_argument("--budget-usd", type=float)
    resume.add_argument("--answer", help="actual human answer to the retained unanswered question")
    followup = commands.add_parser("followup", help="record measured human follow-up; omitted values remain null")
    followup.add_argument("--out", type=Path, required=True)
    followup.add_argument("--trial", required=True)
    followup.add_argument("--seconds", type=float)
    followup.add_argument("--rounds", type=int)
    run = commands.add_parser("run")
    run.add_argument("--superpowers", type=Path, required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--cases", nargs="+", default=[path.parent.name for path in sorted(CASES.glob("*/case.json"))])
    run.add_argument("--repeats", type=int, default=3)
    run.add_argument("--timeout", type=float, default=1800)
    run.add_argument("--budget-usd", type=float, default=5)
    run.add_argument("--max-questions", type=int, default=12)
    run.add_argument("--repair-rounds", type=int, default=1)
    run.add_argument("--context-mode", type=Path)
    run.add_argument("--claude", default="claude")
    run.add_argument("--harness", choices=["claude", "codex"], default="claude")
    run.add_argument("--codex", default="codex")
    run.add_argument("--effort", choices=["low", "medium", "high", "xhigh"], default="high")
    run.add_argument("--until-complete", action="store_true", help="No time, cost, question or repair caps; interrupt retains resumable work")
    run.add_argument("--comparison-mode", choices=["execution", "discovery", "legacy-recommended"], default="discovery")
    run.add_argument("--approved-spec", type=Path)
    run.add_argument("--operator", choices=["policy", "human"], default="policy")
    run.add_argument("--operator-policy", type=Path)
    run.add_argument("--arms", nargs="+", choices=["factory", "superpowers", "factory-context"], help="run only these arms; a split run reports each arm separately")
    args = parser.parse_args(argv)
    if args.command == "regrade":
        regrade(args.out.resolve())
        return 0
    if args.command in {"resume", "followup"}:
        saved = json.loads((args.out / "run-config.json").read_text())
        options = argparse.Namespace(**saved["args"])
        options.out = args.out.resolve()
        if (options.out / "summary.json").exists():
            data = json.loads((options.out / "summary.json").read_text())
        else:
            data = {"model": options.model, "trials": [], "provenance": json.loads((options.out / "provenance.json").read_text())}
        if not any(r["id"] == args.trial for r in data["trials"]):
            progress = options.out / "trials" / args.trial / "progress.json"
            if progress.is_file():
                data["trials"].append(json.loads(progress.read_text()))
        matching = [r for r in data["trials"] if r["id"] == args.trial]
        if len(matching) != 1:
            parser.error("--trial must identify exactly one retained trial")
        record = matching[0]
        if args.command == "followup":
            if (args.seconds is not None and args.seconds < 0) or (args.rounds is not None and args.rounds < 0):
                parser.error("follow-up measurements must be nonnegative")
            record["manual_followup"] = {"seconds": args.seconds, "rounds": args.rounds, "source": "manual human measurement"}
            artifact = options.out / "trials" / record["id"]
            write_json(artifact / "result.json", record)
            progress = artifact / "progress.json"
            if progress.is_file():
                retained = json.loads(progress.read_text())
                retained["manual_followup"] = record["manual_followup"]
                write_json(progress, retained)
        else:
            options.resume_trial = True
            options.resume_answer = args.answer
            if "comparison" in saved["args"]:  # the policy is reread, never stored; it must still match its recorded hash
                options.comparison = comparison_inputs(options)
                if options.comparison["input_hashes"] != saved["args"]["comparison"]["input_hashes"]:
                    parser.error("operator policy or approved spec changed since the run started")
            if args.timeout is not None:
                options.timeout = args.timeout
            if args.budget_usd is not None:
                options.budget_usd = args.budget_usd
            if not Path(record["runtime_root"]).is_dir() or (record["status"] == "accepted" and record.get("workflow_complete") is True and record.get("manual_workflow_review") is True):
                parser.error("resume requires an unfinished trial's retained runtime directory")
            updated = trial(options, options.out / "case-snapshots" / record["case"], record["arm"], record["repeat"] - 1,
                            {name: Path(path) for name, path in saved["paths"].items()})
            data["trials"][data["trials"].index(record)] = updated
        report(options, data["trials"], data["provenance"])
        return 0
    try:
        args.comparison = comparison_inputs(args)
    except (ValueError, OSError, re.error) as error:
        parser.error(str(error))
    if args.harness == "codex" and args.context_mode:
        parser.error("Context arm is not supported by the Codex adapter")
    if args.harness == "claude" and (not args.model.startswith("claude-") or args.model.endswith("-latest")):
        parser.error("--model requires a full versioned Claude model ID, not an alias/latest")
    if args.repeats <= 0 or args.timeout <= 0 or args.budget_usd <= 0 or args.max_questions < 0 or args.repair_rounds < 0:
        parser.error("positive repeat/time/budget and nonnegative question/repair limits required")
    for case in args.cases:
        if case not in {path.parent.name for path in CASES.glob("*/case.json")}:
            parser.error(f"unknown case: {case}")
    args.out = args.out.resolve()
    args.superpowers = args.superpowers.resolve()
    args.context_mode = args.context_mode.resolve() if args.context_mode else None
    browser = any(json.loads((CASES / name / "case.json").read_text()).get("kind") in {"browser", "fullstack"} for name in args.cases)
    browser_runtime = None
    if browser:
        module = os.environ.get("PLAYWRIGHT_MODULE")
        if not module or not (Path(module) / "package.json").is_file():
            parser.error("Browser cases require PLAYWRIGHT_MODULE pointing to an installed Playwright module")
        check = subprocess.run(["node", "-e", ("const fs=require('fs');const p=require(process.argv[1]);"
                                "const executable=p.chromium.executablePath();if(!fs.existsSync(executable))process.exit(1);"
                                "console.log(JSON.stringify({version:require(process.argv[1]+'/package.json').version,executable}));"), module],
                               capture_output=True, text=True, timeout=20, check=False)
        if check.returncode:
            parser.error("Browser cases require an already installed Chromium runtime: " + check.stderr.strip())
        browser_runtime = {"module": str(Path(module).resolve()), **json.loads(check.stdout)}
        os.environ["PLAYWRIGHT_MODULE"] = browser_runtime["module"]
    if args.context_mode:
        with tempfile.TemporaryDirectory(prefix="factory-context-check-") as temporary:
            work = Path(temporary) / "work"
            work.mkdir()
            try:
                prepare_context(args.context_mode, Path(temporary) / "plugin", work, [CASES, *policy_files(args)], browser=browser)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                parser.error(str(error))
    args.out.mkdir(parents=True, exist_ok=False)
    paths, provenance = snapshots(args)
    write_json(args.out / "run-config.json", {"args": {key: str(value) if isinstance(value, Path) else public_comparison(value) if key == "comparison" else value
                                                      for key, value in vars(args).items()},
                                             "paths": {name: str(path) for name, path in paths.items()}})
    provenance["comparison"] = public_comparison(args.comparison)
    version = subprocess.run([args.codex if args.harness == "codex" else args.claude, "--version"], capture_output=True, text=True, check=True)
    provenance[args.harness + "_version"] = version.stdout.strip()
    provenance["benchmark_sha256"] = BENCHMARK_SHA256
    provenance["python_version"] = sys.version
    if browser_runtime:
        provenance["browser_runtime"] = browser_runtime
    case_snapshots = args.out / "case-snapshots"
    case_snapshots.mkdir()
    for name in args.cases:
        shutil.copytree(CASES / name, case_snapshots / name, ignore=IGNORED)
    write_json(args.out / "provenance.json", provenance)
    records = []
    for case in args.cases:
        for repeat in range(args.repeats):
            for arm in [a for a in arm_order(repeat, bool(args.context_mode)) if not args.arms or a in args.arms]:
                print(f"Running {case} / {arm} / {repeat + 1}", flush=True)
                records.append(trial(args, case_snapshots / case, arm, repeat, paths))
                report(args, records, provenance)
                if records[-1].get("interrupted"):
                    return 130
    report(args, records, provenance, blind=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
