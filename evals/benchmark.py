"""Run isolated Claude Code workflow trials; never infer human follow-up savings."""

import argparse
import ast
import hashlib
import json
import os
import platform
import random
import re
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
        for rule in value.get("answers", []):
            if not isinstance(rule, dict) or not isinstance(rule.get("match"), str) or not isinstance(rule.get("answer"), str) or not rule["answer"].strip():
                raise ValueError("policy answers must be nonempty strings")
            re.compile(rule["match"], re.IGNORECASE)
    return result


def operator_answer(config, question):
    if config["mode"] == "legacy-recommended":
        return question["recommended_answer"]
    if config["operator"] == "human":
        answer = input(question["question"] + "\nOperator answer: ").strip()
        if not answer:
            raise ValueError("human answer cannot be empty")
        return answer
    policy = config.get("policy", {})
    for rule in policy.get("answers", []):
        if re.search(rule["match"], question["question"], re.IGNORECASE):
            return rule["answer"]
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
                                   for path in work.glob(".factory/changes/*/status.yaml")}
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
    installed = factory / "installed"
    (installed / "skills").mkdir(parents=True)
    lock_path = Path.home() / ".agents" / ".skill-lock.json"
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {"skills": {}}
    write_json(installed / ".skill-lock.json", lock)
    skipped = []
    pack_hashes = re.findall(r"^  ([\w-]+):.*?hash: ([\w]+)", (factory / "kit" / "packs.lock.yaml").read_text(), re.MULTILINE)
    pack_provenance = {}
    for name, expected in pack_hashes:
        source = Path.home() / ".agents" / "skills" / name
        if not source.is_dir() or lock.get("skills", {}).get(name, {}).get("skillFolderHash") != expected:
            skipped.append({"pack": name, "reason": "missing or installed pin differs"})
            continue
        shutil.copytree(source, installed / "skills" / name, ignore=IGNORED)
        pack_provenance[name] = {"path": str(source), "sha256": tree_hash(source), "installed_pin": expected}
    replacements = {"~/.software-factory": str(factory / "kit"), "~/.agents/skills/": str(installed / "skills") + "/",
                    "~/.agents/.skill-lock.json": str(installed / ".skill-lock.json")}
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
            if file.is_file():
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
    paths = {"factory": factory}
    provenance = {"factory": {"source": str(ROOT), "skills_sha256": tree_hash(ROOT / "skills"),
                             "kit_sha256": tree_hash(ROOT / "kit"), **git_info(ROOT)},
                  "installed_packs": pack_provenance, "skipped_packs": skipped,
                  "adaptations": {"replacements": replacements, "files": adapted,
                                  "notes": "Kit is a read-only snapshot, not a git repository; propose kit changes locally. No Factory gate hooks were installed; skills are compared."}}
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


def settings(work, paths, arm, out, browser=False, browser_command=None, red_command=None):
    denied_plugins = [str(path) for name, path in paths.items()
                      if name not in ({"factory", "context-mode"} if arm == "factory-context" else {arm})]
    active = [path for name, path in paths.items()
              if name in ({"factory", "context-mode"} if arm == "factory-context" else {arm})]
    protected = [CASES, out / "case-snapshots", out / "trials", *(Path(path) for path in denied_plugins)]
    read_rule = lambda path: f"Read(/{path}/**)"  # absolute paths require two leading slashes
    edit_rule = lambda path: f"Edit(/{path}/**)"  # Edit rules also govern Write and NotebookEdit
    return {"autoMemoryEnabled": False, "disableBundledSkills": True, "claudeMdExcludes": ["**"],
            "permissions": {"allow": [read_rule(work), edit_rule(work), *(read_rule(path) for path in active),
                                       "Glob", "Grep", "Skill", "Agent", "Bash", "ToolSearch",
                                       *(f"Bash({command})" for command in [browser_command, red_command] if command),
                                       *(["mcp__plugin_context-mode_context-mode__*"] if arm == "factory-context" else []),
                                       *([read_rule(Path(os.environ["PLAYWRIGHT_MODULE"]))] if browser else [])],
                            "deny": ["AskUserQuestion", "WebFetch", "WebSearch", *(read_rule(path) for path in protected),
                                     edit_rule(ROOT), edit_rule(out), *(edit_rule(path) for path in active),
                                     *([edit_rule(Path(browser_command).parent)] if browser_command else []),
                                     *([edit_rule(Path(os.environ["PLAYWRIGHT_MODULE"]))] if browser else [])]},
            "sandbox": {"enabled": True, "failIfUnavailable": True, "autoAllowBashIfSandboxed": True,
                        "allowUnsandboxedCommands": False,
                        "excludedCommands": [str(command) for command in [browser_command, red_command] if command],
                        "filesystem": {"allowWrite": [str(work)], "denyWrite": [str(ROOT), str(out),
                                                              *([str(Path(browser_command).parent)] if browser_command else [])],
                                       "denyRead": [str(path) for path in protected] + [
                                                    str(Path.home() / ".agents" / "skills"), str(Path.home() / ".claude" / "skills")]},
                        "network": {"allowedDomains": ["127.0.0.1", "localhost"] if browser else [],
                                    "allowLocalBinding": browser, "strictAllowlist": True}}}


def command(args, paths, arm, config, session, resume, remaining_budget, prompt=None, init=False):
    plugins = [paths["factory"] if arm.startswith("factory") else paths["superpowers"]]
    servers = {}
    if arm == "factory-context":
        plugins.append(paths["context-mode"])
        servers = json.loads((paths["context-mode"] / ".claude-plugin/plugin.json").read_text())["mcpServers"]
        for server in servers.values():
            server["args"] = [argument.replace("${CLAUDE_PLUGIN_ROOT}", str(paths["context-mode"])) for argument in server["args"]]
            server.setdefault("env", {})["CLAUDE_PLUGIN_ROOT"] = str(paths["context-mode"])
        servers = {f"plugin_context-mode_{name}": server for name, server in servers.items()}
    cmd = [args.claude, "--print", "--model", args.model, "--setting-sources", "", "--strict-mcp-config",
           "--mcp-config", json.dumps({"mcpServers": servers}), "--settings", str(config), "--permission-mode", "dontAsk",
           "--output-format", "stream-json", "--verbose", "--forward-subagent-text", "--include-hook-events",
           "--max-turns", "60", "--max-budget-usd", str(remaining_budget), "--effort", "high", "--no-chrome",
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
            process = subprocess.Popen(cmd, cwd=work, stdout=stdout, stderr=stderr, text=True, env=env, start_new_session=True)
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
                        if time.monotonic() - started >= timeout:
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
        if any(part in {".git", ".factory", ".claude", ".tmp", "__pycache__", "node_modules", ".venv", "docs"} for part in relative.parts):
            continue
        if file.is_symlink():
            raise ValueError(f"product symlink cannot be graded safely: {relative}")
        if file.is_file() and not file.name.startswith("test") and (file.suffix in {
                ".py", ".html", ".css", ".js", ".mjs", ".cjs", ".json", ".svg", ".png", ".jpg", ".webp", ".woff2"} or
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
    artifact.with_suffix(".txt").write_text(output)
    write_json(artifact.with_suffix(".json"), result)
    return result, output


def workflow_evidence(work, arm, case):
    if arm.startswith("factory"):
        statuses = list(work.glob(".factory/changes/*/status.yaml"))
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
        browser_note += f'Set status red_test_command to {red_command}. For RED proof, write exactly two fields to .factory/browser-red.json: {{"commit":"FULL_40_CHARACTER_ANCESTOR_COMMIT_SHA","checkpoint":"SAFE_TOKEN"}}. Replace the placeholders; commit must match [0-9a-f]{{40}} and checkpoint must match [A-Za-z0-9_-]{{1,64}}. Then run exactly {red_command} without arguments via Bash. It checks an isolated clone and leaves the live GREEN checkout unchanged.\n'
    context_note = ("For large non-browser repository or command outputs, use Context Mode ctx_execute, ctx_batch_execute, "
                    "ctx_index and ctx_search when available; ToolSearch may discover deferred tools. Preserve raw test evidence: "
                    "a retrieval summary is not verification proof. The exact browser checker still runs directly through Bash.\n") if arm == "factory-context" else ""
    return f"""This is an isolated, synthetic local benchmark with a recorded operator, not production approval.
Task (the same neutral requirements are given to every workflow):
{(case / 'task.md').read_text()}
Start by invoking Skill {entry}; if the skill is unavailable, read {skill}. Follow its full applicable workflow and all handoffs until local completion, including review and, for Factory, reconcile. Do not replace this with a code-only pass.
Operator policy: no external network, remote git operations, dependency installations, production changes. Local research worktrees are permitted only under this workspace’s .tmp directory; keep research read-only and remove them when finished. Localhost serving and browser checks are permitted for browser cases. This fresh repository is already isolated. Unsigned synthetic local commits are permitted. Keep workflow documents locally; never alter skill/kit snapshots or original source directories. Report unavailable optional lenses/tools as skipped; do not install them. Propose any kit updates locally. All subagents must inherit the requested model. Use {verify} for fixture checks. There is no extra linter/typechecker configured. For browser cases, an installed Playwright module is provided through PLAYWRIGHT_MODULE; use the provided browser verification command without installing dependencies. Browser imports in Context Mode's Bun JavaScript runtime are not supported by this adapter.
{browser_note}{context_note}
Whenever the workflow requires a user choice or approval, stop and return the question plus a specific recommended answer; never answer it yourself. Do not use AskUserQuestion (print mode). Return exactly ONE JSON object, without commentary outside it, with these keys: {{"state":"question|complete|blocked","question":"...","recommended_answer":"...","summary":"..."}}. Complete means the full local workflow has finished; blocked means a bounded obstruction, not a pending agent. Wait for every agent you start to finish before returning. A handoff to the next skill continues automatically unless it requires a user answer. Every controller reply is a simulated operator answer, valid only inside this synthetic repository; the copied Factory gate rules explicitly permit forwarding it verbatim to step agents.
"""


def trial(args, case, arm, repeat, paths):
    browser = json.loads((case / "case.json").read_text()).get("kind") == "browser"
    trial_id = f"{case.name}-{arm}-{repeat + 1}"
    artifact = args.out / "trials" / trial_id
    artifact.mkdir(parents=True, exist_ok=getattr(args, "resume_trial", False))
    session = str(uuid.uuid4())
    started = time.monotonic()
    record = {"id": trial_id, "case": case.name, "arm": arm, "repeat": repeat + 1, "session_id": session,
              "manual_followup": None, "simulated_questions": [], "repair_rounds": 0, "initial_quality": None,
              "environment_recovery_rounds": 0,
              "final_quality": None, "status": "incomplete", "invocations": [], "requested_model": args.model,
              "time_to_first_result_seconds": None, "manual_workflow_review": None}
    resuming = getattr(args, "resume_trial", False)
    if resuming:
        record = json.loads((artifact / "progress.json").read_text())
        session = record["session_id"]
        if record["case_sha256"] != tree_hash(case):
            raise ValueError("Cannot resume after grading inputs changed")
    record["comparison"] = args.comparison if hasattr(args, "comparison") else comparison_inputs(args)
    previous_wall = record.get("wall_seconds", 0) if resuming else 0
    record["interrupted"] = False
    record.setdefault("decisions", [])
    record.setdefault("progress", [])
    record["raw_workspace_retained"] = False
    record["case_sha256"] = tree_hash(case)
    record["benchmark_sha256"] = BENCHMARK_SHA256
    events, partial = [], False
    with retained_runtime(artifact, record) as temporary:
        work = (Path(temporary) / "work").resolve()
        if not resuming:
            shutil.copytree(case / "fixture", work, ignore=IGNORED)
        browser_runtime = record.get("browser_verification")
        if browser and not resuming:
            from browser_runtime import prepare_browser_check
            browser_runtime = prepare_browser_check(Path(temporary) / "browser-check", work, [ROOT, args.out])
            record["browser_verification"] = browser_runtime
        if resuming:
            paths = {name: Path(path) for name, path in record["runtime_paths"].items()}
        if arm == "factory-context" and not resuming:
            paths = dict(paths)
            paths["context-mode"], record["context_isolation"] = prepare_context(
                paths["context-mode"], Path(temporary) / "context-plugin", work,
                [CASES, args.out / "case-snapshots", args.out / "trials", paths["superpowers"]], browser=browser)
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
        write_json(config, settings(work, paths, arm, args.out, browser=browser, browser_command=browser_command, red_command=red_command))
        prompt = initial_prompt(case, arm, paths, browser_command=browser_command, red_command=red_command)
        comparison = record["comparison"]
        if comparison.get("approved_spec"):
            prompt += "\nSHARED APPROVED SPECIFICATION (execution input):\n" + comparison["approved_spec"]
        if comparison.get("policy"):
            prompt += "\nFIXED OPERATOR PERSONA AND PREFERENCES:\n" + json.dumps(comparison["policy"])
        if resuming:
            prompt = record.get("pending_prompt", prompt)
            if getattr(args, "resume_answer", None):
                if not record.get("pending_question"):
                    raise ValueError("--answer requires a retained unanswered question")
                record["decisions"].append({"question": record.pop("pending_question")["question"],
                                             "answer": args.resume_answer, "operator": "human", "mode": record["comparison"]["mode"],
                                             "elapsed_seconds": previous_wall})
                write_json(artifact / "decisions.json", record["decisions"])
                prompt = "SIMULATED USER ANSWER (actual human benchmark response, local repository only):\n" + args.resume_answer
            for trajectory in sorted(artifact.glob("turn-*.jsonl")):
                for line in trajectory.read_text().splitlines():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        record["runtime_paths"] = {name: str(path) for name, path in paths.items()}
        plugins = [paths["factory"] if arm.startswith("factory") else paths["superpowers"]] + ([paths["context-mode"]] if arm == "factory-context" else [])
        snapshot_hashes = record.get("plugin_snapshot_hashes") if resuming else {str(plugin): tree_hash(plugin) for plugin in plugins}
        if not snapshot_hashes or any(tree_hash(Path(path)) != digest for path, digest in snapshot_hashes.items()):
            raise ValueError("Cannot run/resume after pinned plugin snapshots changed")
        record["plugin_snapshot_hashes"] = snapshot_hashes
        record["pending_prompt"] = prompt
        write_json(artifact / "progress.json", record)
        preflight = invoke(command(args, paths, arm, config, str(uuid.uuid4()), False, args.budget_usd, init=True), work, artifact / "preflight", min(args.timeout, 60))
        record["preflight"] = {key: value for key, value in preflight.items() if key != "events"}
        record["interrupted"] = preflight.get("interrupted", False)
        if preflight["returncode"] != 0 or preflight["timeout"]:
            record["stop_reason"] = "preflight failed"
        elif isolation(preflight["events"], plugins)["reason"] == "unexpected plugins/MCP":
            record["stop_reason"] = "preflight found unrelated plugins/MCP"
        else:
            while True:
                remaining_time = args.timeout - (time.monotonic() - started)
                cost = accounting(events)["cost_usd"] or 0
                if remaining_time <= 0 or cost >= args.budget_usd:
                    record["stop_reason"] = "trial time/budget cap"
                    partial = remaining_time <= 0
                    break
                number = len(record["invocations"])
                record["pending_prompt"] = prompt
                write_json(artifact / "progress.json", record)
                (artifact / f"turn-{number:02d}.prompt.txt").write_text(prompt)
                run = invoke(command(args, paths, arm, config, session, number > 0, args.budget_usd - cost, prompt),
                             work, artifact / f"turn-{number:02d}", remaining_time)
                events.extend(run.pop("events"))
                run["stage"] = "execution"
                run["turn"] = number
                run["elapsed_seconds"] = previous_wall + time.monotonic() - started
                run["observed_usage"] = accounting(events, partial=run["timeout"])
                record["invocations"].append(run)
                record["progress"].append({"turn": number, "elapsed_seconds": run["elapsed_seconds"],
                                           "stage": (response(events) or {}).get("state", "interrupted"),
                                           "usage": run["observed_usage"]})
                if run["timeout"] or run["returncode"] != 0:
                    partial = True
                    record["interrupted"] = run.get("interrupted", False)
                    record["stop_reason"] = "model process timeout/error"
                    break
                if isolation(events, plugins)["reason"] == "unexpected plugins/MCP":
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
                    if len(record["simulated_questions"]) > args.max_questions:
                        record["stop_reason"] = "question cap"
                        break
                    try:
                        decision_started = time.monotonic()
                        decision = operator_answer(record["comparison"], answer)
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
                                                 "elapsed_seconds": previous_wall + time.monotonic() - started})
                    write_json(artifact / "decisions.json", record["decisions"])
                    prompt = "SIMULATED USER ANSWER (recorded benchmark operator, synthetic local repository only; no production, remote, dependency, or external-source authority):\n" + decision + "\nContinue the same workflow/session; return the structured question/completion schema again."
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
                        continue
                    record["stop_reason"] = answer["summary"]
                    break
                if record["time_to_first_result_seconds"] is None:
                    record["time_to_first_result_seconds"] = previous_wall + time.monotonic() - started
                quality, feedback = grade(case, work, artifact / f"grade-{record['repair_rounds']}")
                if record["initial_quality"] is None:
                    record["initial_quality"] = quality
                record["final_quality"] = quality
                if quality["accepted"]:
                    record["status"] = "accepted"
                    record["stop_reason"] = "trusted acceptance tests passed"
                    break
                if record["repair_rounds"] >= args.repair_rounds:
                    record["stop_reason"] = "repair cap with failing acceptance"
                    break
                record["repair_rounds"] += 1
                prompt = "SHARED BENCHMARK TEST FAILURE FEEDBACK (same policy for all arms). Repair the product and complete the workflow again; preserve the structured response schema.\n" + feedback
        record.update(workflow_evidence(work, arm, case))
        record["isolation"] = isolation(events or preflight["events"], plugins)
        record.update(accounting(events, partial=partial))
        record["context_usage"] = context_usage(events, arm == "factory-context")
        record["model_policy_valid"] = bool(record["models"]) and all(
            name == args.model or usage.get("canonicalModel") == args.model
            for name, usage in (record["model_usage"] or {}).items())
        record["measurement_valid"] = (record["isolation"]["verified"] and not partial and record["tokens"] is not None
                                       and record["isolation"].get("model") == args.model and record["model_policy_valid"])
        record["plugin_snapshot_hashes"] = snapshot_hashes
        record["snapshots_unchanged"] = all(tree_hash(Path(path)) == digest for path, digest in snapshot_hashes.items())
        if browser_runtime:
            record["browser_verification_unchanged"] = all(
                hashlib.sha256(Path(browser_runtime[key]).read_bytes()).hexdigest() == digest
                for key, digest in browser_runtime["sha256"].items())
            record["snapshots_unchanged"] = record["snapshots_unchanged"] and record["browser_verification_unchanged"]
        record["measurement_valid"] = record["measurement_valid"] and record["snapshots_unchanged"]
        try:
            retain_workspace(work, artifact, record)
        except ValueError as error:
            record["source_snapshot_error"] = str(error)
            record["measurement_valid"] = False
    record["wall_seconds"] = previous_wall + time.monotonic() - started
    record["time_to_accepted_seconds"] = record["wall_seconds"] if record["status"] == "accepted" else None
    record["simulated_question_count"] = len(record["simulated_questions"])
    record["workflow_complete"] = record.get("workflow_complete") if record["status"] == "accepted" else False
    record["comparative_valid"] = record["measurement_valid"] and record["workflow_complete"] is True and record["manual_workflow_review"] is True and record["comparison"]["valid_decision_protocol"]
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
    write_json(args.out / "summary.json", {"model": args.model, "trials": records, "operator": getattr(args, "comparison", None), "manual_followup": None,
                                           "provenance": provenance, "interpretation": "No automatic ranking. Partial or isolation-unverified runs are not valid comparisons."})
    lines = ["# Workflow benchmark", "", "Recorded operator decisions; actual human follow-up remains null until manually recorded. Legacy recommended-answer simulations are diagnostic only. Quality is trusted post-execution acceptance, not agent claims. Tokens include cache classes and subagents from the final cumulative result; resume records are never added together.", "",
             "| Case | Arm | Repeat | Initial quality | Final quality | Raw snapshot quality | Committed checkpoint quality | Context calls | Repairs | Environment reminders | Tokens | USD | First result seconds | Total seconds | Operator questions | Workflow | Measurement valid | Full comparison valid |",
             "|---|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
    for record in records:
        quality = lambda value: "pass" if value and value["accepted"] else "fail" if value else "unmeasured"
        tokens = record['tokens'] if record['tokens'] is not None else (
            f">={record['tokens_lower_bound']}" if record.get('tokens_lower_bound') is not None else "unknown")
        dollars = record['cost_usd'] if record['cost_usd'] is not None else (
            f">={record['cost_usd_lower_bound']}" if record.get('cost_usd_lower_bound') is not None else "unknown")
        lines.append(f"| {record['case']} | {record['arm']} | {record['repeat']} | {quality(record['initial_quality'])} | {quality(record['final_quality'])} | {quality(record.get('snapshot_quality'))} | {quality(record.get('committed_checkpoint_quality'))} | {record.get('context_usage', {}).get('deduplicated_tool_call_count', 0)} | {record['repair_rounds']} | {record.get('environment_recovery_rounds', 0)} | {tokens} | {dollars} | {record['time_to_first_result_seconds']} | {record['wall_seconds']:.1f} | {record['simulated_question_count']} | {record['workflow_complete']} | {record['measurement_valid']} | {record['comparative_valid']} |")
    lines += ["", "Snapshot quality grades even unfinished products; it does not establish workflow completion or delivery time. >= values are the last observed cumulative usage before an interrupted invocation, not exact totals. Measurement validity covers recorded model/isolation/accounting only. Full comparison validity additionally needs confirmed workflow completion and manual trajectory review (unmeasured until reviewed). Do not infer real human follow-up savings. Builtin cc-plugin components may remain active even with bundled skills disabled. Blind source review below excludes workflow documents."]
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
    """Grade unfinished snapshots without pretending the workflow finished or rerunning a model."""
    data = json.loads((out / "summary.json").read_text())
    for record in data["trials"]:
        artifact = out / "trials" / record["id"]
        case = out / "case-snapshots" / record["case"]
        if not case.exists():
            case = CASES / record["case"]
        if record.get("case_sha256") != tree_hash(case):
            raise ValueError(f"{record['id']}: grading inputs changed; retain the original result")
        record["snapshot_quality"] = record["final_quality"] if record["status"] != "incomplete" else None
        if record["snapshot_quality"] is None:
            record["snapshot_quality"], _ = grade(case, artifact / "workspace", artifact / "grade-snapshot")
        record["snapshot_quality_checkout"] = record.get("checkout", {"label": "historical checkout identity unavailable; not proven latest code"})
        if record.get("committed_checkpoint"):
            record["committed_checkpoint_quality"], _ = grade(case, artifact / "committed-source", artifact / "grade-committed-checkpoint")
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
    rescore = commands.add_parser("regrade", help="grade partial products without another model run")
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
    run.add_argument("--comparison-mode", choices=["execution", "discovery", "legacy-recommended"], default="discovery")
    run.add_argument("--approved-spec", type=Path)
    run.add_argument("--operator", choices=["policy", "human"], default="policy")
    run.add_argument("--operator-policy", type=Path)
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
            if args.timeout is not None:
                options.timeout = args.timeout
            if args.budget_usd is not None:
                options.budget_usd = args.budget_usd
            if not Path(record["runtime_root"]).is_dir() or record["status"] == "accepted":
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
    if not args.model.startswith("claude-") or args.model.endswith("-latest"):
        parser.error("--model requires a full versioned Claude model ID, not an alias/latest")
    if args.repeats <= 0 or args.timeout <= 0 or args.budget_usd <= 0 or args.max_questions < 0 or args.repair_rounds < 0:
        parser.error("positive repeat/time/budget and nonnegative question/repair limits required")
    for case in args.cases:
        if case not in {path.parent.name for path in CASES.glob("*/case.json")}:
            parser.error(f"unknown case: {case}")
    args.out = args.out.resolve()
    args.superpowers = args.superpowers.resolve()
    args.context_mode = args.context_mode.resolve() if args.context_mode else None
    browser = any(json.loads((CASES / name / "case.json").read_text()).get("kind") == "browser" for name in args.cases)
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
                prepare_context(args.context_mode, Path(temporary) / "plugin", work, [CASES], browser=browser)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                parser.error(str(error))
    args.out.mkdir(parents=True, exist_ok=False)
    paths, provenance = snapshots(args)
    write_json(args.out / "run-config.json", {"args": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
                                             "paths": {name: str(path) for name, path in paths.items()}})
    provenance["comparison"] = args.comparison
    version = subprocess.run([args.claude, "--version"], capture_output=True, text=True, check=True)
    provenance["claude_version"] = version.stdout.strip()
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
            for arm in arm_order(repeat, bool(args.context_mode)):
                print(f"Running {case} / {arm} / {repeat + 1}", flush=True)
                records.append(trial(args, case_snapshots / case, arm, repeat, paths))
                report(args, records, provenance)
                if records[-1].get("interrupted"):
                    return 130
    report(args, records, provenance, blind=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
