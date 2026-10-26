"""Matched historical PR trials. Private records never enter an actor workspace."""

import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from statistics import median

import benchmark
import diagnostics
import pr_fixtures
from browser_runtime import sandbox_policy

ARMS = ("bare", "claude-md", "factory")
ORDER = tuple(itertools.permutations(ARMS))
SAFE_ENV = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG", "LC_ALL", "TERM"}
PRIVATE = pr_fixtures.PRIVATE_DIRS | {"node_modules", ".venv", ".tmp", ".benchmark-runtime", "__pycache__"}


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shared_input_paths(case):
    paths = []
    for item in case.get("shared_inputs", []):
        path = pr_fixtures._relative(item["path"])
        if path in paths:
            raise ValueError("duplicate shared input path")
        paths.append(path)
    return paths


def verify_policy(case):
    if case.get("archgraph_rules"):
        policy = Path(case["archgraph_rules"])
        if (not policy.is_absolute() or not re.fullmatch(r"[a-f0-9]{64}", case.get("archgraph_rules_sha256", ""))
                or sha(policy) != case["archgraph_rules_sha256"]):
            raise ValueError("archgraph rules changed or missing pin")


def verify_files(case):
    verify_policy(case)
    paths = shared_input_paths(case)
    for item, relative in zip(case.get("shared_inputs", []), paths):
        source = Path(item["source"])
        if (not source.is_absolute() or not re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", ""))
                or sha(source) != item["sha256"]):
            raise ValueError(f"shared input source changed: {relative}")
        for tree in ("actor", "reference"):
            root = Path(case["prepared_dir"]) / tree
            target = root / relative
            pr_fixtures._inside(root, target)
            if target.is_symlink() or sha(target) != item["sha256"]:
                raise ValueError(f"shared input changed: {tree}/{relative}")
    for item in case.get("verification_files", []):
        path = Path(item["path"])
        if not path.is_absolute() or not re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", "")) or sha(path) != item["sha256"]:
            raise ValueError(f"pinned verification file changed: {path}")


def readonly_caches(case):
    paths = {str(Path(item["path"]).resolve().parent) for item in case.get("verification_files", [])}
    for environment in (case.get("runtime_env", {}), case.get("test_env", {})):
        for key in ("NODE_PATH", "GOMODCACHE"):
            for value in environment.get(key, "").split(os.pathsep):
                if value and Path(value).is_absolute():
                    paths.add(str(Path(value).resolve()))
    return sorted(paths)


def manifest_cases(path):
    data = json.loads(Path(path).read_text())
    cases = data["cases"] if isinstance(data, dict) else data
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest requires cases")
    ids = set()
    for case in cases:
        identity = case.get("id", "")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", identity) or identity in ids:
            raise ValueError("case ids must be unique safe directory names")
        ids.add(identity)
        for field in ("base_commit", "reference_commit"):
            if not re.fullmatch(r"[0-9a-f]{40}", case.get(field, "")):
                raise ValueError(f"{identity}: {field} must be a full commit")
        if not case.get("claude_md", "").strip() or not case.get("pr", {}).get("title"):
            raise ValueError(f"{identity}: frozen CLAUDE.md and real PR description required")
        if not case.get("pr", {}).get("url") or not case.get("prepared_dir"):
            raise ValueError(f"{identity}: PR URL and admitted prepared_dir required")
        pr_fixtures.acceptance_paths(case)
        verify_files(case)
    return cases


def requirements(case):
    return case["pr"]["title"] + "\n\n" + (case["pr"].get("body") or "")


def task_prompt(case):
    command = case.get("public_verify_command", case["test_command"])
    environment = {**case.get("runtime_env", {}), **case.get("test_env", {})}
    environment["GOCACHE"] = "<repository>/.benchmark-runtime/go-cache (absolute per trial)"
    if case.get("provide_acceptance"):
        tests = pr_fixtures.acceptance_paths(case) + pr_fixtures.support_paths(case)
        acceptance = ("Provided acceptance tests and support are immutable: " + ", ".join(map(str, tests))
                      + ". They are identical in every arm and intentionally RED on BASE. All must pass; "
                        "their failures are the feature's acceptance target, not unrelated baseline failures. "
                        "Implement production code to satisfy them; do not modify, delete or replace them. "
                        "Add and run your own relevant public tests as needed.")
    else:
        acceptance = ("Future held-out test files may be absent. Write and run relevant public tests yourself; "
                      "missing future tests are not an implementation failure.")
    return ("Implement the following approved feature requirements in this disposable repository. "
            "Read CLAUDE.md if present. Preserve existing behavior outside this request. "
            "Use local tools; external network and other repositories are unavailable. "
            "Do not seek historical PRs or reference implementations. Run relevant available checks. "
            "Local unsigned Git commits are authorized in this disposable repository. "
            "Return exactly one JSON object with state (complete, question, or blocked), "
            "question, recommended_answer, and summary (all strings). Ask only a decision "
            "the approved requirements do not resolve; do not invent approvals.\n\n"
            "APPROVED REQUIREMENTS (historical PR title/body, not its implementation):\n" + requirements(case)
            + "\n\nSHARED TEST SETUP (identical in every arm):\nCommand: " + shlex.join(command)
            + "\nWorking directory relative to repository: " + case.get("test_cwd", ".")
            + ("\nDECLARED EVALUATION SCOPE (identical in every arm): " + case["scope"] if case.get("scope") else "")
            + "\nPrepared environment: " + json.dumps(environment, sort_keys=True)
            + "\n" + acceptance + " Shared dependencies and the test wrapper are read-only."
            + ("\nSTANDING CONSTRAINTS AND HISTORY (identical immutable files in every arm): "
               + ", ".join(map(str, shared_input_paths(case)))
               + ". Read these before implementation and preserve their bytes." if case.get("shared_inputs") else ""))


def actor_settings(work, snapshot, denied, arm, write_denied=(), protected_files=(), *, factory_hooks=False):
    read = lambda path: f"Read(/{Path(path).resolve()}/**)"
    edit = lambda path: f"Edit(/{Path(path).resolve()}/**)"
    write = lambda path: f"Write(/{Path(path).resolve()}/**)"
    blocked = sorted({str(Path(path).resolve()) for path in denied})
    readonly = sorted({str(Path(path).resolve()) for path in write_denied})
    immutable = sorted({str(Path(path).resolve()) for path in protected_files})
    allowed = [work] + ([snapshot] if arm == "factory" else [])
    excluded_memory = [str(Path.home() / ".claude" / "**"),
                       *(str(parent / "CLAUDE.md") for parent in work.resolve().parents)]
    settings = {"autoMemoryEnabled": False, "disableBundledSkills": True,
            "claudeMdExcludes": ["**"] if arm == "bare" else excluded_memory, "enabledPlugins": {},
            "permissions": {"allow": [*(read(path) for path in allowed), edit(work),
                                       "Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill", "Agent"],
                            "deny": ["AskUserQuestion", "WebFetch", "WebSearch", "ToolSearch", "mcp__*",
                                     *(read(path) for path in blocked), *(edit(path) for path in blocked), edit(snapshot),
                                     *(edit(path) for path in readonly), *(write(path) for path in blocked), write(snapshot),
                                     *(write(path) for path in readonly), f"Write(/{work.resolve()}/node_modules/**)",
                                     *(f"{tool}(/{path})" for path in blocked for tool in ("Read", "Edit", "Write")),
                                     *(f"{tool}(/{path})" for path in [*readonly, str(snapshot.resolve())] for tool in ("Edit", "Write")),
                                     f"Write(/{work.resolve()}/node_modules)", f"Edit(/{work.resolve()}/node_modules/**)",
                                     f"Edit(/{work.resolve()}/node_modules)",
                                     *(f"{tool}(/{path})" for path in immutable for tool in ("Edit", "Write"))]},
            "sandbox": {"enabled": True, "failIfUnavailable": True, "autoAllowBashIfSandboxed": True,
                        "allowUnsandboxedCommands": False,
                        "filesystem": {"allowWrite": [str(work)], "denyWrite": [*blocked, *readonly, *immutable, str(snapshot)],
                                       "denyRead": blocked},
                        "network": {"allowedDomains": ["localhost", "127.0.0.1", "::1"],
                                    "strictAllowlist": True, "allowLocalBinding": True}}}
    if factory_hooks and arm == "factory":
        hook = Path(snapshot).resolve() / "hooks" / "plumb_gate.py"
        settings["hooks"] = {"PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [
            {"type": "command", "command": shlex.join([sys.executable, str(hook)])}]}]}
    return settings


def hook_preflight(snapshot, work):
    hook = Path(snapshot).resolve() / "hooks" / "plumb_gate.py"
    if not hook.is_file():
        return {"ready": False, "reason": "factory gate hook missing"}
    try:
        result = subprocess.run([sys.executable, str(hook)], cwd=work, input="{}", capture_output=True,
                                text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        return {"ready": False, "reason": str(error)}
    return {"ready": result.returncode == 0, "sha256": sha(hook), "returncode": result.returncode,
            "coverage": "installation preflight only; enforcement requires native hook observations"}


def invoke_actor(config, command, work, artifact, timeout):
    if config.get("diagnostics"):
        return benchmark.invoke(command, work, artifact, timeout, observe_events=True)
    return benchmark.invoke(command, work, artifact, timeout)


@contextmanager
def clean_environment(extra=None):
    old = dict(os.environ)
    env = {key: value for key, value in old.items() if key in SAFE_ENV}
    for key, value in (extra or {}).items():
        if key not in {"GOCACHE", "GOMODCACHE", "GOPATH", "GOPROXY", "GOTOOLCHAIN", "PYTHONPATH", "NODE_PATH", "NODE_ENV", "TZ", "VIRTUAL_ENV", "PATH", "npm_config_cache"}:
            raise ValueError(f"unapproved runtime environment variable: {key}")
        env[key] = str(value)
    try:
        os.environ.clear()
        os.environ.update(env)
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


def command(config, arm, settings, session, prompt, resume=False, probe=False):
    argv = [config["claude"], "--print", "--model", config["model"], "--effort", config["effort"],
            "--setting-sources", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--settings", str(settings), "--permission-mode", "dontAsk", "--output-format", "stream-json",
            "--verbose", "--forward-subagent-text", "--include-hook-events", "--no-chrome",
            "--resume" if resume else "--session-id", session]
    if arm == "factory":
        argv += ["--plugin-dir", config["snapshot"], "--add-dir", config["snapshot"]]
        if not probe:
            argv += ["--append-system-prompt", ("Use the pinned factory workflow for this approved feature. "
                                               "Start with factory triage and follow its gates. No other workflow plugins are available.")]
    return argv + ["--", prompt]


def actor_environment(config):
    environment = {"CLAUDE_CODE_SUBAGENT_MODEL": config["model"], "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1",
            "CLAUDE_CODE_EFFORT_LEVEL": config["effort"]}
    if config.get("factory_hooks") or config.get("diagnostics"):
        environment["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] = "1"
    return environment


def xcode_environment():
    root = Path("/Applications/Xcode.app/Contents/Developer")
    compiler = root / "Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
    sdk = root / "Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk"
    return {"CC": str(compiler), "SDKROOT": str(sdk)} if compiler.is_file() and sdk.is_dir() else {}


def actor_runtime_environment(config, work):
    cache = Path(work).resolve() / ".benchmark-runtime" / "go-cache"
    cache.mkdir(parents=True, exist_ok=True)
    return {**config.get("toolchain_environment", xcode_environment()), **actor_environment(config), "GOCACHE": str(cache)}


def verify_model_usage(usage, model):
    return {"verified": usage.get("models") == [model] and usage.get("model_usage") is not None
                        and usage.get("tokens") is not None,
            "models": usage.get("models"), "required_model": model,
            "reason": "complete native usage from the pinned root/subagent model only"}


def verify_inventory(events, arm, model):
    observed = benchmark.isolation(events, [])
    initial = [e for e in events if e.get("type") == "system" and e.get("subtype") == "init"]
    if not initial:
        return {"verified": False, "reason": "missing native init inventory"}
    native = initial[-1]
    plugins = native.get("plugins")
    names = {p.get("name") if isinstance(p, dict) else p for p in plugins} if isinstance(plugins, list) else None
    expected = {"factory"} if arm == "factory" else set()
    bundled = {name for name in names or set() if isinstance(name, str) and name.startswith("cc-plugin-")}
    observed.update(verified=names is not None and names - bundled == expected and native.get("mcp_servers") == [] and native.get("model") == model,
                    reason="exact plugin, MCP and model inventory required", model=native.get("model"))
    return observed


def isolation_probe(events, canary, secret):
    """Require native failed tool results for BOTH read routes, never model assurances."""
    calls, results = {}, {}
    for event in events:
        message = event.get("message", {})
        for block in message.get("content", []) if isinstance(message.get("content"), list) else []:
            if block.get("type") == "tool_use":
                calls[block.get("id")] = block
            elif block.get("type") == "tool_result":
                results[block.get("tool_use_id")] = block
    denied = set()
    for identity, call in calls.items():
        name, inputs = call.get("name"), call.get("input", {})
        targeted = name == "Read" and inputs.get("file_path") == str(canary)
        targeted |= name == "Bash" and inputs.get("command") == f"cat {canary}"
        result = results.get(identity, {})
        body = json.dumps(result)
        if targeted and result.get("is_error") and re.search(r"denied|not permitted|permission|sandbox|not allowed", body, re.IGNORECASE):
            denied.add(name)
    leaked = secret in json.dumps([e for e in events if e.get("type") != "system"])
    return {"verified": denied == {"Read", "Bash"} and not leaked,
            "denied_tools": sorted(denied), "canary_leaked": leaked}


def copy_dependencies(case, work):
    for relative, source in case.get("dependency_dirs", {}).items():
        relative = pr_fixtures._relative(relative)
        source = Path(source).resolve()
        repo = Path(case["repo"]).resolve()
        if source == repo or repo in source.parents:
            raise ValueError("dependency cache cannot be source repository content")
        pr_fixtures.snapshot_hash(source)  # Reject escaping source symlinks.
        target = work / str(relative)
        pr_fixtures._inside(work, target)
        if target.exists():
            raise ValueError(f"dependency destination already exists: {target}")
        shutil.copytree(source, target, symlinks=False)


def _tool_version(binary):
    result = subprocess.run([str(binary), "--version"], capture_output=True, text=True, check=True)
    resolved = Path(binary).resolve()
    info = {"path": str(resolved), "sha256": sha(resolved), "version": result.stdout.strip()}
    if (resolved.parents[2] / ".git").exists():
        info["source"] = benchmark.git_info(resolved.parents[2])
    return info


def input_fingerprints(out, cases):
    prepared = {}
    for case in cases:
        root = Path(case["prepared_dir"])
        if any(not (root / name).is_dir() or (root / name).is_symlink() for name in ("actor", "reference")):
            raise ValueError("prepared actor/reference directories missing or replaced by symlinks")
        prepared[case["id"]] = {"actor": pr_fixtures.snapshot_hash(root / "actor"),
                                "reference": pr_fixtures.snapshot_hash(root / "reference"),
                                "admission": sha(root / "admission.json")}
    return {"manifest": sha(out / "manifest.json"), "prepared": prepared}


def verify_inputs(out, config):
    cases = manifest_cases(out / "manifest.json")
    if config.get("frozen_inputs") != input_fingerprints(out, cases):
        raise ValueError("frozen manifest, prepared source or admission evidence changed; start a new benchmark")
    for case in cases:
        instruction = hashlib.sha256(case["claude_md"].encode()).hexdigest()
        approved = hashlib.sha256(requirements(case).encode()).hexdigest()
        if (config.get("instruction_hashes", {}).get(case["id"]) != instruction
                or config.get("requirements_hashes", {}).get(case["id"]) != approved):
            raise ValueError("frozen requirements or CLAUDE.md changed")
    return cases


def private_input_roots(cases, public_paths):
    roots = {Path(case["prepared_dir"]).resolve().parent for case in cases}
    roots.update(Path(item["source"]).resolve().parent for case in cases for item in case.get("shared_inputs", []))
    public = [Path(path).resolve() for path in public_paths]
    if any(root == path or root in path.parents or path in root.parents for root in roots for path in public):
        raise ValueError("private input corpus root overlaps actor/framework; use isolated corpus storage")
    return sorted(map(str, roots))


def persistent_runtime_home(state_root, out, prefix):
    if state_root is not None:
        state_root = Path(state_root).resolve()
        if state_root == out.resolve() or out.resolve() in state_root.parents:
            raise ValueError("state root cannot be inside denied benchmark output")
        state_root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=state_root)).resolve()


def initialize(args):
    cases = manifest_cases(args.manifest)
    if args.model in {"opus", "sonnet", "haiku", "default"} or "latest" in args.model:
        raise ValueError("pin a full model ID, not a moving alias")
    args.out.mkdir(parents=True, exist_ok=False)
    snapshot_home = persistent_runtime_home(getattr(args, "state_root", None), args.out, "pr-benchmark-framework-")
    paths, provenance = benchmark.snapshots(argparse.Namespace(out=snapshot_home, superpowers=None, context_mode=None))
    if getattr(args, "factory_hooks", False):
        provenance["adaptations"]["notes"] = (
            "Read-only one-commit framework snapshot named by each Factory trial plumb.lock. "
            "The Factory arm installs the actual pinned plumb_gate.py PreToolUse hook through trial settings. "
            "Hook installation preflight and native events are retained; this is the sequential workflow, not v2. "
            "Background agent tasks are disabled for all arms; helpers run in the foreground before completion.")
    runtime_home = persistent_runtime_home(getattr(args, "state_root", None), args.out, "pr-benchmark-actors-")
    schedule = []
    for index, case in enumerate(cases):
        for arm in ORDER[index % len(ORDER)]:
            runtime = runtime_home / case["id"] / arm
            runtime.mkdir(parents=True)
            schedule.append({"case": case["id"], "arm": arm, "runtime": str(runtime)})
    config = {"model": args.model, "effort": args.effort, "claude": str(Path(shutil.which(args.claude) or args.claude).resolve()),
              "snapshot": str(paths["factory"]), "framework": provenance, "schedule": schedule,
              "manifest_sha256": sha(args.manifest), "controller_sha256": sha(__file__),
              "fixture_sha256": sha(pr_fixtures.__file__), "framework_sha256": benchmark.tree_hash(paths["factory"]),
              "tools": {"claude": _tool_version(shutil.which(args.claude) or args.claude), "archgraph": _tool_version(args.archgraph)},
              "comparison": "quality only; cost and wall time reported separately", "margin_percentage_points": args.margin,
              "source_repositories": sorted({str(Path(case["repo"]).resolve()) for case in cases}),
              "timeout_seconds": args.timeout, "max_questions": args.max_questions,
              "instruction_hashes": {case["id"]: hashlib.sha256(case["claude_md"].encode()).hexdigest() for case in cases},
              "requirements_hashes": {case["id"]: hashlib.sha256(requirements(case).encode()).hexdigest() for case in cases}}
    if getattr(args, "state_root", None) is not None:
        config["state_root"] = str(args.state_root.resolve())
    for option in ("diagnostics", "factory_hooks"):
        if getattr(args, option, False):
            config[option] = True
    if config.get("diagnostics"):
        config["diagnostics_sha256"] = sha(diagnostics.__file__)
    if any(case.get("shared_inputs") for case in cases):
        config["private_input_roots"] = private_input_roots(cases, [runtime_home, *paths.values()])
    config["actor_environment"] = actor_environment(config)
    config["toolchain_environment"] = xcode_environment()
    config["runtime_tools"] = {}
    for name, arguments in (("node", ["--version"]), ("go", ["version"]), ("git", ["--version"]), ("python3", ["--version"])):
        binary = shutil.which(name)
        if binary:
            resolved = Path(binary).resolve()
            result = subprocess.run([str(resolved), *arguments], capture_output=True, text=True, check=True)
            config["runtime_tools"][name] = {"path": str(resolved), "sha256": sha(resolved), "version": result.stdout.strip()}
    xcode = Path("/Applications/Xcode.app/Contents/Developer")
    if xcode.is_dir():
        config["xcode_developer_root"] = str(xcode.resolve())
        config["xcode_bundle_root"] = str(xcode.parents[1].resolve())
        xcodebuild = xcode / "usr" / "bin" / "xcodebuild"
        result = subprocess.run([str(xcodebuild), "-version"], capture_output=True, text=True, check=False)
        config["runtime_tools"]["xcodebuild"] = {"path": str(xcodebuild.resolve()), "sha256": sha(xcodebuild),
                                                 "version": result.stdout.strip(), "version_returncode": result.returncode}
    if compiler := config["toolchain_environment"].get("CC"):
        config["runtime_tools"]["clang"] = _tool_version(compiler)
    write(args.out / "manifest.json", {"cases": cases})
    config["frozen_inputs"] = input_fingerprints(args.out, cases)
    write(args.out / "run.json", config)
    return config, cases


def graph_check(config, case, work, artifact):
    verify_policy(case)
    binary = config["tools"]["archgraph"]["path"]
    if sha(binary) != config["tools"]["archgraph"]["sha256"]:
        raise ValueError("archgraph binary changed")
    outputs = []
    graphs = []
    for name, root in (("base", Path(case["prepared_dir"]) / "actor"), ("candidate", work)):
        relative = case.get("archgraph_root", ".")
        target = root / relative
        pr_fixtures._inside(root, target)
        graph = artifact / f"{name}-graph.json"
        argv = [binary, "scan", str(target), "--engine", "native", "--language", case.get("archgraph_language", "typescript"),
                "--no-daemon", "-o", str(graph)]
        if case.get("archgraph_rules"):
            argv += ["--rules", case["archgraph_rules"]]
        run = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
        outputs.append({"command": argv, "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
        if run.returncode != 0:
            return {"status": "scan_error", "commands": outputs}
        graphs.append(graph)
    argv = [binary, "diff", *map(str, graphs), "--fail-on", "new-forbidden,new-cycles,new-unplanned", "--format", "json", "--no-daemon"]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
    outputs.append({"command": argv, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    status = "no_new_violations" if result.returncode == 0 else "failed" if result.returncode == 1 else "scan_error"
    return {"status": status, "commands": outputs,
            "scope": ("pinned policy: new forbidden edges, unplanned edges and cycles; baseline debt retained in base-graph.json"
                      if case.get("archgraph_rules") else
                      "cycle-only: no policies supplied, so forbidden/unplanned gates are inert; baseline debt retained in base-graph.json"),
            **({"rules_sha256": case["archgraph_rules_sha256"]} if case.get("archgraph_rules") else {})}


def test_counts(output):
    unittest_count = re.search(r"Ran (\d+) tests?\b", output)
    jest = re.search(r"Tests:\s+([^\n]+)", output)
    if unittest_count:
        skipped = re.search(r"skipped=(\d+)", output)
        return {"total": int(unittest_count[1]), "skipped": int(skipped[1]) if skipped else 0}
    if jest and (total := re.search(r"(\d+) total", jest[1])):
        skipped = re.search(r"(\d+) skipped", jest[1])
        return {"total": int(total[1]), "skipped": int(skipped[1]) if skipped else 0}
    pytest = re.findall(r"(\d+) (passed|failed|skipped|xfailed|xpassed|error)\b", output)
    if pytest:
        # Only the final summary line is authoritative; do not double-count progress output.
        summary = next((line for line in reversed(output.splitlines()) if re.search(r"\d+ (passed|failed|skipped)", line)), "")
        counts = re.findall(r"(\d+) (passed|failed|skipped|xfailed|xpassed|error)\b", summary)
        return {"total": sum(int(number) for number, _ in counts),
                "skipped": sum(int(number) for number, kind in counts if kind in {"skipped", "xfailed", "xpassed"})}
    go = re.findall(r"^\s*--- (PASS|FAIL|SKIP):", output, re.MULTILINE)
    if go:
        return {"total": len(go), "skipped": go.count("SKIP")}
    return None


def loopback_test_policy(policy):
    return policy + ('(allow network-outbound (remote ip "localhost:*"))\n'
                     '(allow network-inbound (local ip "localhost:*"))\n'
                     '(allow network-bind (local ip "localhost:*"))\n')


def test_coverage_matches(counts, expected, calibration=False):
    return bool(counts and counts["total"] > 0 and counts["skipped"] == 0
                and (counts == expected or (calibration and expected is None)))


def isolated_grader(config, case, artifact, admission, *, calibration=False):
    """Callback receives only the fixture helper's disposable test-injected copy."""
    def run(work, command, timeout=300, test_cwd=".", test_env=None):
        verify_files(case)
        sandbox, node = shutil.which("sandbox-exec"), shutil.which("node")
        if platform.system() != "Darwin" or not sandbox or not node:
            return {"status": "not_run", "output": "Native macOS grading sandbox unavailable; no unsafe fallback"}
        work = Path(work).resolve()
        scratch = work / ".benchmark-grading-runtime"
        scratch.mkdir()
        readable = [work, *(Path(path) for path in readonly_caches(case))]
        xcode = Path(config.get("xcode_bundle_root", "/Applications/Xcode.app"))
        if xcode.is_dir():
            readable.append(xcode.resolve())
        runtime_env = case.get("runtime_env", {})
        for key in ("NODE_PATH", "GOMODCACHE", "GOPATH", "PYTHONPATH", "VIRTUAL_ENV", "PATH"):
            for item in runtime_env.get(key, "").split(os.pathsep):
                if item and Path(item).is_absolute():
                    readable.append(Path(item).resolve())
        protected = [Path(case["prepared_dir"]).resolve(), artifact.parents[2].resolve(), benchmark.ROOT,
                     *(Path(path) for path in config.get("source_repositories", [])),
                     *(Path(entry["runtime"]) for entry in config["schedule"])]
        policy = loopback_test_policy(sandbox_policy(work, readable, [work], Path(node).resolve(), protected, strict_reads=True))
        profile = artifact / "grading.sb"
        profile.write_text(policy)
        canary = artifact / "grading-canary"
        canary.write_text(uuid.uuid4().hex)
        probe_script = ("from pathlib import Path; import socket,sys\n"
                        "try: Path(sys.argv[1]).read_bytes()\n"
                        "except PermissionError: pass\n"
                        "else: raise SystemExit(7)\n"
                        "sock=socket.socket(); sock.settimeout(1)\n"
                        "try: sock.connect(('192.0.2.1',443))\n"
                        "except PermissionError: pass\n"
                        "else: raise SystemExit(8)\n")
        prefix = [sandbox, "-f", str(profile)]
        with clean_environment(runtime_env):
            os.environ.update(config.get("toolchain_environment", xcode_environment()))
            os.environ.update(HOME=str(scratch), TMPDIR=str(scratch), GOCACHE=str(scratch / "go-cache"))
            probe = subprocess.run([*prefix, sys.executable, "-I", "-S", "-c", probe_script, str(canary)],
                                   cwd=work, capture_output=True, text=True, timeout=30, check=False)
            inventory = {"verified": probe.returncode == 0, "returncode": probe.returncode,
                         "output": probe.stdout + probe.stderr, "profile_sha256": sha(profile)}
            if not inventory["verified"]:
                return {"status": "not_run", "isolation": inventory, "output": "Grading isolation probe failed"}
            grader_env = {**(test_env or {}), **config.get("toolchain_environment", xcode_environment()), "HOME": str(scratch), "TMPDIR": str(scratch),
                          "GOCACHE": str(scratch / "go-cache")}
            result = pr_fixtures.run_tests(work, [*prefix, *command], timeout, test_cwd, grader_env)
        counts = test_counts(result["output"])
        expected = test_counts(admission.get("reference_result", {}).get("output", ""))
        result.update(isolation=inventory, counts=counts, expected_counts=expected,
                      coverage_limit="Runner counts plus immutable acceptance files; not proof against deliberate in-process test-runner tampering")
        if result["status"] == "pass" and not test_coverage_matches(counts, expected, calibration):
            result["status"] = "coverage_missing"
        return result
    return run


def grade_candidate(config, case, work, prepared, artifact, admission):
    result = pr_fixtures.grade_case(case, work, prepared / "reference", timeout=300,
                                   runner=isolated_grader(config, case, artifact, admission))
    if result["status"] == "setup_error":
        control_artifact = artifact.with_name(artifact.name + "-reference-control")
        control_artifact.mkdir(parents=True, exist_ok=True)
        try:
            control = pr_fixtures.grade_case(case, prepared / "reference", prepared / "reference", timeout=300,
                                            runner=isolated_grader(config, case, control_artifact, admission))
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            control = {"status": "setup_error", "output": str(error)}
        result["reference_control"] = control
        if control["status"] == "pass":
            result.update(status="candidate_error", original_status="setup_error")
    return result


def provided_acceptance(case, work):
    paths = pr_fixtures.acceptance_paths(case) + pr_fixtures.support_paths(case) if case.get("provide_acceptance") else []
    return [Path(work) / path for path in paths + shared_input_paths(case)]


def acceptance_integrity(case, work, baseline):
    files, changed = {}, []
    for path in provided_acceptance(case, work):
        relative = path.relative_to(work)
        try:
            pr_fixtures._inside(work, path)
            if path.is_symlink() or any((work / parent).is_symlink() for parent in relative.parents):
                raise ValueError("immutable test path replaced by symlink")
            files[str(relative)] = sha(path)
            if files[str(relative)] != sha(baseline / relative):
                changed.append(str(relative))
        except (OSError, ValueError):
            changed.append(str(relative))
    return {"verified": not changed, "files": files, "changed": changed}


def seed_factory(work, snapshot):
    pins = snapshot / "kit" / "packs.lock.yaml"
    pins = pins.read_text().partition("\npacks:\n")[2] if pins.is_file() else ""
    (work / ".plumb").mkdir(exist_ok=True)
    (work / ".plumb" / "plumb.lock").write_text(
        f"framework: {{ dev_path: {snapshot.resolve()} }}\npacks:\n{pins}\nskills_linked: []\n")


def commit_arm_setup(work):
    (work / ".git" / "info").mkdir(exist_ok=True)
    with (work / ".git" / "info" / "exclude").open("a") as exclusions:
        exclusions.write("\n.benchmark-runtime/\n.tmp/\n__pycache__/\n*.py[cod]\n")
    git = ["git", "-C", str(work), "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
           "-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost"]
    subprocess.run([*git, "add", "--all"], capture_output=True, text=True, check=True)
    subprocess.run([*git, "commit", "--quiet", "--allow-empty", "-m", "Benchmark arm setup"], capture_output=True, text=True, check=True)


def trial(config, case, entry, out, resume_incomplete=False):
    verify_files(case)
    artifact = out / "trials" / case["id"] / entry["arm"]
    artifact.mkdir(parents=True, exist_ok=True)
    record_path = artifact / "result.json"
    if record_path.exists():
        stopped = json.loads(record_path.read_text())
        if not resume_incomplete or stopped.get("status") not in {"timeout", "interrupted"}:
            return stopped
        if (out / "blind-key.json").exists():
            raise ValueError("cannot resume after blind packets were frozen")
        write(artifact / f"stopped-{len(stopped.get('attempts', []))}.json", stopped)
    progress = artifact / "progress.json"
    record = json.loads(progress.read_text()) if progress.exists() else {
        "case": case["id"], "arm": entry["arm"], "attempts": [], "seconds": 0, "task_seconds": 0}
    work = Path(entry["runtime"]) / "work"
    prepared = Path(case["prepared_dir"]).resolve()
    admission = json.loads((prepared / "admission.json").read_text())
    if admission.get("admitted") is not True:
        record.update(status="admission_failed", admission=admission)
        write(record_path, record)
        return record
    snapshot = Path(config["snapshot"])
    if not work.exists():
        shutil.copytree(prepared / "actor", work, symlinks=True)
        copy_dependencies(case, work)
        if entry["arm"] != "bare":
            (work / "CLAUDE.md").write_text(case["claude_md"])
        if entry["arm"] == "factory":
            seed_factory(work, snapshot)
        commit_arm_setup(work)
    denied = [out, benchmark.ROOT, Path.home() / "Work", Path.home() / ".claude" / "projects",
              Path.home() / ".claude" / "skills", Path.home() / ".codex", Path.home() / ".agents",
              Path.home() / ".plumb", Path.home() / "Library" / "Caches" / "go-build",
              Path.home() / ".cache" / "go-build", prepared]
    for environment in (case.get("runtime_env", {}), case.get("test_env", {})):
        if (cache := environment.get("GOCACHE")) and Path(cache).is_absolute() and not Path(cache).resolve().is_relative_to(work.resolve()):
            denied.append(Path(cache))
    denied += [Path(item["runtime"]) for item in config["schedule"] if item != entry]
    denied += [Path(path) for path in config.get("source_repositories", [])]
    denied += [Path(path) for path in config.get("private_input_roots", [])]
    denied += [Path(item["source"]) for item in case.get("shared_inputs", [])]
    if entry["arm"] != "factory":
        denied.append(snapshot)
    settings = artifact / "settings.json"
    hook_options = {"factory_hooks": True} if config.get("factory_hooks") else {}
    write(settings, actor_settings(work, snapshot, denied, entry["arm"], readonly_caches(case),
                                   provided_acceptance(case, work), **hook_options))
    if config.get("factory_hooks") and entry["arm"] == "factory":
        record["hook_installation"] = hook_preflight(snapshot, work)
        if not record["hook_installation"]["ready"]:
            record["status"] = "infrastructure_error"
            write(record_path, record)
            return record
    session = record.setdefault("session", str(uuid.uuid4()))
    write(progress, record)
    if not record.get("isolation_probe", {}).get("verified"):
        canary = out / "read-isolation-canary"
        secret = uuid.uuid4().hex
        canary.write_text(secret)
        prompt = (f"Isolation test only: invoke Read with file_path {canary} and Bash with exactly command `cat {canary}`. "
                  "Both should be denied. Do not try alternate routes. Return JSON with state blocked, "
                  "question empty, recommended_answer empty, summary isolation probe.")
        with clean_environment(case.get("runtime_env")):
            os.environ.update(actor_runtime_environment(config, work))
            probe = invoke_actor(config, command(config, entry["arm"], settings, str(uuid.uuid4()), prompt, probe=True), work, artifact / "probe", config["timeout_seconds"])
        record["isolation_probe"] = isolation_probe(probe["events"], canary, secret)
        record["probe_inventory"] = verify_inventory(probe["events"], entry["arm"], config["model"])
        record["probe_usage"] = benchmark.accounting(probe["events"], probe["timeout"])
        record["probe_model_usage"] = verify_model_usage(record["probe_usage"], config["model"])
        record["probe_seconds"] = probe["seconds"]
        record["seconds"] += probe["seconds"]
        record["interrupted"] = bool(probe.get("interrupted"))
        if (record["interrupted"] or not record["isolation_probe"]["verified"] or not record["probe_inventory"]["verified"]
                or not record["probe_model_usage"]["verified"]):
            record["status"] = ("interrupted" if record["interrupted"] else
                                "isolation_failed" if not record["isolation_probe"]["verified"] or not record["probe_inventory"]["verified"]
                                else "model_evidence_failed")
            record["observed_tokens"] = record["probe_usage"]["tokens"]
            write(record_path, record)
            return record
        write(progress, record)
    prompt = record.get("next_prompt", task_prompt(case))
    if record.get("status") in {"timeout", "interrupted"}:
        prompt = "Continue the existing task within the same approved requirements; retain completed work.\n\n" + task_prompt(case)
    comparison = {"mode": "execution", "operator": "policy", "approved_spec": requirements(case)}
    for _ in range(config["max_questions"] - len(record["attempts"])):
        attempt = len(record["attempts"])
        with clean_environment(case.get("runtime_env")):
            os.environ.update(actor_runtime_environment(config, work))
            run = invoke_actor(config, command(config, entry["arm"], settings, session, prompt, attempt > 0), work,
                                   artifact / f"turn-{attempt:03d}", config["timeout_seconds"])
        result = benchmark.response(run["events"])
        inventory = verify_inventory(run["events"], entry["arm"], config["model"])
        record["attempts"].append({"returncode": run["returncode"], "timeout": run["timeout"], "seconds": run["seconds"],
                                   "usage": benchmark.accounting(run["events"], run["timeout"]), "inventory": inventory,
                                   "response": result})
        model_usage = verify_model_usage(record["attempts"][-1]["usage"], config["model"])
        record["attempts"][-1]["model_usage_verification"] = model_usage
        record["seconds"] += run["seconds"]
        record["task_seconds"] += run["seconds"]
        record["interrupted"] = bool(run.get("interrupted"))
        if run.get("interrupted"):
            record["status"] = "interrupted"
        elif not inventory["verified"]:
            record["status"] = "isolation_failed"
        elif run["timeout"]:
            record["status"] = "timeout"
        elif not model_usage["verified"]:
            record["status"] = "model_evidence_failed"
        elif run["returncode"] or result is None:
            record["status"] = "execution_failed"
        elif result["state"] == "question":
            answer = benchmark.operator_answer(comparison, result)
            record["attempts"][-1]["operator_answer"] = answer
            prompt = "SIMULATED USER ANSWER (fixed execution policy):\n" + answer
            record["next_prompt"] = prompt
            write(progress, record)
            continue
        else:
            record["status"] = result["state"]
        break
    else:
        record["status"] = "question_limit"
    write(progress, record)
    # Grade every stopped outcome, including errors, without promoting it to completed delivery.
    try:
        verify_files(case)
        record["acceptance_integrity"] = acceptance_integrity(case, work, prepared / "actor")
        if not record["acceptance_integrity"]["verified"]:
            record["status"] = "acceptance_tampered"
        record["tests"] = grade_candidate(config, case, work, prepared, artifact, admission)
        record["archgraph"] = graph_check(config, case, work, artifact)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        record["grading_error"] = str(error)
    record["workspace"] = str(work)
    try:
        record["source_sha256"] = pr_fixtures.snapshot_hash(work)
    except ValueError as error:
        record.update(status="invalid_workspace", workspace_error=str(error), source_sha256=None)
    record["observed_tokens"] = observation_usage(record)
    write(record_path, record)
    return record


def product_copy(source, target):
    """Blind source excludes workflow metadata, instructions, caches and all history."""
    target.mkdir(parents=True)
    for current, directories, files in os.walk(source, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in PRIVATE and not (Path(current) / name).is_symlink())
        for name in sorted(files):
            if name in pr_fixtures.INSTRUCTION_FILES:
                continue
            origin = Path(current) / name
            if origin.is_symlink():
                continue
            destination = target / origin.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, destination)


def blind_packets(out):
    config = json.loads((out / "run.json").read_text())
    cases = {case["id"]: case for case in verify_inputs(out, config)}
    key_path = out / "blind-key.json"
    if key_path.exists():
        raise ValueError("blind packets already frozen; never regenerate after verdicts")
    entries = []
    for entry in config["schedule"]:
        result_path = out / "trials" / entry["case"] / entry["arm"] / "result.json"
        if result_path.exists():
            result = json.loads(result_path.read_text())
            if result.get("workspace") and result.get("source_sha256"):
                if pr_fixtures.snapshot_hash(Path(result["workspace"])) != result["source_sha256"]:
                    raise ValueError("workspace changed after grading")
                entries.append((entry, result))
    random.SystemRandom().shuffle(entries)
    key = {}
    packets = out / "blind"
    packets.mkdir(exist_ok=False)
    for entry, result in entries:
        identity = uuid.uuid4().hex[:16]
        packet = packets / identity
        packet.mkdir()
        case = cases[entry["case"]]
        (packet / "TASK.md").write_text(requirements(case))
        product_copy(Path(case["prepared_dir"]) / "actor", packet / "base")
        product_copy(Path(result["workspace"]), packet / "source")
        diff = subprocess.run(["git", "diff", "--no-index", "--", "base", "source"], cwd=packet, capture_output=True, text=True, check=False)
        if diff.returncode not in (0, 1):
            raise ValueError(diff.stderr)
        (packet / "change.diff").write_text(diff.stdout)
        key[identity] = {"case": entry["case"], "arm": entry["arm"], "packet_sha256": benchmark.tree_hash(packet),
                         "source_sha256": result["source_sha256"],
                         "result_sha256": sha(out / "trials" / entry["case"] / entry["arm"] / "result.json")}
    write(key_path, key)
    return key


def freeze_verdicts(out, source):
    target = out / "verdicts.json"
    if target.exists():
        raise ValueError("verdicts already frozen")
    key = json.loads((out / "blind-key.json").read_text())
    verdicts = json.loads(Path(source).read_text())
    if set(verdicts) != set(key):
        raise ValueError("review every anonymous packet exactly once")
    for identity, verdict in verdicts.items():
        if verdict.get("verdict") not in {"accept", "reject"} or not verdict.get("reason", "").strip():
            raise ValueError("each verdict requires accept/reject and a reason")
        if benchmark.tree_hash(out / "blind" / identity) != key[identity]["packet_sha256"]:
            raise ValueError("blind packet changed")
    write(target, {"verdicts": verdicts, "input_sha256": sha(source), "key_sha256": sha(out / "blind-key.json"),
                   "frozen_at": time.time()})


def usage(record):
    # Resume results are cumulative for the TASK session. Its separate preflight is not task work.
    attempts = record.get("attempts", [])
    return attempts[-1].get("usage", {}).get("tokens") if attempts else None


def observation_usage(record):
    tokens = [usage(record), record.get("probe_usage", {}).get("tokens")]
    return sum(tokens) if tokens and all(isinstance(value, (int, float)) for value in tokens) else None


def total_and_median(values, decimals):
    if not values or not all(numeric(value) for value in values):
        return "unknown"
    return f"{sum(values):.{decimals}f} / {median(values):.{decimals}f}"


def quality_covered(record, case, config, review):
    attempts = record.get("attempts", [])
    tests = record.get("tests", {})
    if (record.get("status") not in {"complete", "blocked", "question_limit", "acceptance_tampered", "timeout"}
            or review not in {"accept", "reject"} or not attempts
            or any(record.get(key) for key in ("interrupted", "error", "grading_error", "workspace_error"))
            or tests.get("status") not in {"pass", "assertion_failure", "candidate_error", "timeout"}
            or record.get("archgraph", {}).get("status") not in {"no_new_violations", "failed"}
            or tests.get("isolation", {}).get("verified") is not True
            or record.get("isolation_probe", {}).get("verified") is not True
            or record.get("probe_inventory", {}).get("verified") is not True
            or record.get("probe_model_usage", {}).get("verified") is not True
            or not verify_model_usage(record.get("probe_usage", {}), config["model"])["verified"]
            or (case.get("provide_acceptance") and not isinstance(record.get("acceptance_integrity", {}).get("verified"), bool))):
        return False
    if tests["status"] == "candidate_error":
        control = tests.get("reference_control", {})
        if control.get("status") != "pass" or control.get("isolation", {}).get("verified") is not True:
            return False
    for index, attempt in enumerate(attempts):
        if attempt.get("inventory", {}).get("verified") is not True:
            return False
        verified = (attempt.get("model_usage_verification", {}).get("verified") is True
                    and verify_model_usage(attempt.get("usage", {}), config["model"])["verified"])
        if record["status"] == "timeout" and index == len(attempts) - 1:
            # The execution guard proves non-delivery; an interrupted native usage receipt may be absent.
            guard = (attempt.get("timeout") is True and attempt.get("returncode") == -9
                     and numeric(attempt.get("seconds")) and numeric(config.get("timeout_seconds"))
                     and config["timeout_seconds"] > 0 and attempt["seconds"] >= config["timeout_seconds"])
            observed = attempt.get("usage", {})
            if (not guard or observed.get("models") not in (None, [], [config["model"]])
                    or (observed.get("model_usage") is not None and not verified)):
                return False
        elif (attempt.get("timeout") or not verified or attempt.get("returncode") != 0
              or not isinstance(attempt.get("response"), dict)
              or attempt["response"].get("state") not in {"complete", "blocked", "question"}):
            return False
    return True


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def report(out):
    config = json.loads((out / "run.json").read_text())
    cases = verify_inputs(out, config)
    reviews = {}
    if (out / "verdicts.json").exists():
        key = json.loads((out / "blind-key.json").read_text())
        frozen = json.loads((out / "verdicts.json").read_text())
        if frozen.get("key_sha256") != sha(out / "blind-key.json"):
            raise ValueError("blind key changed after verdict freeze")
        verdicts = frozen["verdicts"]
        for identity, item in key.items():
            if benchmark.tree_hash(out / "blind" / identity) != item["packet_sha256"]:
                raise ValueError("reviewed blind packet changed")
            result_path = out / "trials" / item["case"] / item["arm"] / "result.json"
            if sha(result_path) != item["result_sha256"]:
                raise ValueError("graded result changed after blind packet freeze")
            reviews[item["case"], item["arm"]] = verdicts[identity]["verdict"]
    lines = ["# Historical feature PR benchmark", "", f"Model: `{config['model']}`; effort: `{config['effort']}`.",
             "Quality determines the comparison. Tokens and time are separate. Archgraph is **cycle-only**: no policies are supplied, so forbidden/unplanned gates are inert. It checks new cycles, not zero baseline debt.",
             "", "| Task | Arm | Outcome | Tests | Archgraph | Blind review | Task tokens | Task USD | Task seconds | Probe tokens | Probe USD | Probe seconds |",
             "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    if any(case.get("archgraph_rules") for case in cases):
        lines[3] = ("Task-specific pinned architecture policies check new forbidden/unplanned edges and cycles where supplied; "
                    "tasks without policies remain cycle-only. Baseline debt is retained.")
    if config.get("factory_hooks"):
        lines.insert(4, "Factory arm installs the actual Edit/Write PreToolUse hook; installation preflight is not proof of enforcement coverage. This is the sequential workflow, not v2.")
    provided_contract = all(case.get("provide_acceptance") for case in cases)
    lines.insert(4, "Acceptance contract: provided immutable tests and support, identical in every arm." if provided_contract else
                 "Legacy or mixed hidden-test pilot: archived diagnostic evidence, not the corrected provided-test experiment.")
    accepted = dict.fromkeys(ARMS, 0)
    costs = {arm: {"tokens": [], "usd": [], "seconds": []} for arm in ARMS}
    complete = 20 <= len(cases) <= 30 and provided_contract
    quality_coverage = dict.fromkeys(ARMS, 0)
    observed = {arm: {"tokens": [], "usd": []} for arm in ARMS}
    for case in cases:
        for arm in ARMS:
            path = out / "trials" / case["id"] / arm / "result.json"
            record = json.loads(path.read_text()) if path.exists() else {}
            review = reviews.get((case["id"], arm), "missing")
            tests = record.get("tests", {}).get("status", "missing")
            graph = record.get("archgraph", {}).get("status", "missing")
            tokens = usage(record)
            task_usd = record.get("attempts", [])[-1].get("usage", {}).get("cost_usd") if record.get("attempts") else None
            costs[arm]["tokens"].append(tokens)
            costs[arm]["usd"].append(task_usd)
            costs[arm]["seconds"].append(record.get("task_seconds"))
            terminal = record.get("status")
            covered = quality_covered(record, case, config, review)
            quality_coverage[arm] += int(covered)
            complete &= covered
            accepted[arm] += int(covered and terminal == "complete" and tests == "pass"
                                 and graph == "no_new_violations" and review == "accept"
                                 and record.get("acceptance_integrity", {}).get("verified") is True)
            for metric, field in (("tokens", "tokens"), ("usd", "cost_usd")):
                values = [attempt.get("usage", {}).get(field) for attempt in record.get("attempts", [])]
                known = [value for value in values if numeric(value)]
                observed[arm][metric].append(max(known) if known else None)
            seconds = f"{record['task_seconds']:.1f}" if "task_seconds" in record else "unknown"
            probe_tokens = record.get("probe_usage", {}).get("tokens")
            probe_usd = record.get("probe_usage", {}).get("cost_usd")
            probe_seconds = f"{record['probe_seconds']:.1f}" if "probe_seconds" in record else "unknown"
            task_dollars = f"{task_usd:.6f}" if isinstance(task_usd, (int, float)) else "unknown"
            probe_dollars = f"{probe_usd:.6f}" if isinstance(probe_usd, (int, float)) else "unknown"
            lines.append(f"| {case['id']} | {arm} | {terminal or 'missing'} | {tests} | {graph} | {review} | {tokens if tokens is not None else 'unknown'} | {task_dollars} | {seconds} | {probe_tokens if probe_tokens is not None else 'unknown'} | {probe_dollars} | {probe_seconds} |")
    lines += ["", "| Arm | Task tokens total / median | Task USD total / median | Task seconds total / median |",
              "| --- | ---: | ---: | ---: |"]
    for arm in ARMS:
        lines.append(f"| {arm} | {total_and_median(costs[arm]['tokens'], 0)} | {total_and_median(costs[arm]['usd'], 6)} | {total_and_median(costs[arm]['seconds'], 1)} |")
    accounting_coverage = {arm: {metric: sum(numeric(value) for value in values)
                                  for metric, values in costs[arm].items()} for arm in ARMS}
    accounting_complete = all(count == len(cases) for counts in accounting_coverage.values() for count in counts.values())
    lines += ["", "| Arm | Quality coverage | Token coverage | USD coverage | Seconds coverage | Observed task token lower bound | Observed task USD lower bound |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for arm in ARMS:
        counts = accounting_coverage[arm]
        bounds = []
        for metric, decimals in (("tokens", 0), ("usd", 6)):
            known = [value for value in observed[arm][metric] if numeric(value)]
            bounds.append(f"{sum(known):.{decimals}f} ({len(known)}/{len(cases)} tasks observed)" if known else "unknown (0 tasks observed)")
        lines.append(f"| {arm} | {quality_coverage[arm]}/{len(cases)} | {counts['tokens']}/{len(cases)} | {counts['usd']}/{len(cases)} | {counts['seconds']}/{len(cases)} | {' | '.join(bounds)} |")
    lines += ["", "Observed lower bounds use the largest known cumulative task-session value per task, never summed across resumes. They are not complete totals; wholly unobserved tasks remain unknown.",
              "A verified execution-guard timeout is failure to deliver, even when final native usage is missing. This exception does not establish exhaustive native model-call accounting.",
              "Acceptance requires completed delivery, passing acceptance tests, no new archgraph violations and blind acceptance.",
              "Task tokens and USD use the final cumulative task-session usage; task seconds sum its turns. USD is the native CLI-reported value, not an invoice claim; missing values and incomplete aggregates stay unknown. Separate isolation probes are shown explicitly and excluded from task metrics. Raw records retain total observed tokens and seconds, including failed probes."]
    delta = (accepted["factory"] - accepted["claude-md"]) / len(cases) * 100
    if complete:
        verdict = "Factory beats CLAUDE.md by the predeclared quality margin" if delta >= config["margin_percentage_points"] else "Factory does not beat CLAUDE.md by the predeclared quality margin"
        lines += ["", f"Accepted: {accepted}. Factory minus CLAUDE.md: {delta:+.1f} percentage points.",
                  f"{verdict} ({config['margin_percentage_points']:g} percentage points)."]
    else:
        lines += ["", "**Incomplete evidence: no winner.** All 20–30 tasks × 3 arms need test, architecture, blind-review and valid treatment/isolation coverage. Accounting gaps are reported separately."]
    lines += ["", "This single paired 20–30-task trial is descriptive; it does not establish statistical superiority."]
    text = "\n".join(lines) + "\n"
    (out / "REPORT.md").write_text(text)
    return {"complete": complete, "accounting_complete": accounting_complete,
            "quality_coverage": quality_coverage, "accounting_coverage": accounting_coverage, "accepted": accepted, "delta_percentage_points": delta, "report": text}


def record_run_error(artifact, entry, error):
    artifact.mkdir(parents=True, exist_ok=True)
    path = artifact / "result.json"
    if path.exists():
        path = artifact / f"run-error-{uuid.uuid4().hex}.json"
    write(path, {"case": entry["case"], "arm": entry["arm"], "status": "infrastructure_error", "error": str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--manifest", type=Path)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--state-root", type=Path, help="Persistent parent for isolated framework and actor directories")
    run.add_argument("--model")
    run.add_argument("--effort", choices=("low", "medium", "high", "max"), default="high")
    run.add_argument("--claude", default="claude")
    run.add_argument("--archgraph", type=Path)
    run.add_argument("--timeout", type=int, default=1800)
    run.add_argument("--max-questions", type=int, default=20)
    run.add_argument("--margin", type=float, default=10)
    run.add_argument("--case")
    run.add_argument("--arm", choices=ARMS)
    run.add_argument("--resume-incomplete", action="store_true", help="Resume timed-out/interrupted sessions; retain stopped records")
    run.add_argument("--diagnostics", action="store_true", help="Capture native observation timings and write additive offline diagnostics")
    run.add_argument("--factory-hooks", action="store_true", help="Install actual Factory PreToolUse gates in the Factory arm")
    for name in ("report", "blind-packets", "blind-verdict"):
        sub = commands.add_parser(name)
        sub.add_argument("--out", type=Path, required=True)
        if name == "blind-verdict":
            sub.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    args.out = args.out.resolve()
    if args.command == "run":
        if (args.out / "run.json").exists():
            config = json.loads((args.out / "run.json").read_text())
            cases = verify_inputs(args.out, config)
            if args.state_root is not None and str(args.state_root.resolve()) != config.get("state_root"):
                parser.error("cannot change state root on resume")
            if (args.diagnostics and not config.get("diagnostics")) or (args.factory_hooks and not config.get("factory_hooks")):
                parser.error("cannot enable diagnostics/hooks on resume; start a new benchmark")
            if config.get("diagnostics_sha256") and sha(diagnostics.__file__) != config["diagnostics_sha256"]:
                parser.error("diagnostic profiler changed; start a new benchmark")
            if args.model and args.model != config["model"]:
                parser.error("cannot change model on resume")
            if sha(__file__) != config["controller_sha256"] or sha(pr_fixtures.__file__) != config["fixture_sha256"]:
                parser.error("controller or fixture changed; start a new benchmark")
        else:
            if not all((args.manifest, args.model, args.archgraph)):
                parser.error("new run requires --manifest, --model and --archgraph")
            config, cases = initialize(args)
        verify_inputs(args.out, config)
        if args.resume_incomplete and (args.out / "blind-key.json").exists():
            parser.error("cannot resume after blind packets were frozen")
        if benchmark.tree_hash(Path(config["snapshot"])) != config["framework_sha256"]:
            parser.error("pinned framework changed")
        for tool in [*config["tools"].values(), *config.get("runtime_tools", {}).values()]:
            if sha(tool["path"]) != tool["sha256"]:
                parser.error("pinned tool changed")
        by_id = {case["id"]: case for case in cases}
        for entry in config["schedule"]:
            if (args.case is None or args.case == entry["case"]) and (args.arm is None or args.arm == entry["arm"]):
                verify_inputs(args.out, config)
                try:
                    result = trial(config, by_id[entry["case"]], entry, args.out, args.resume_incomplete)
                    print(entry["case"], entry["arm"], result["status"], flush=True)
                    if result["status"] == "interrupted" or result.get("interrupted"):
                        break
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    artifact = args.out / "trials" / entry["case"] / entry["arm"]
                    record_run_error(artifact, entry, error)
        report(args.out)
        if config.get("diagnostics"):
            diagnostics.save_report(args.out, [args.case] if args.case else diagnostics.CASES)
    elif args.command == "blind-packets":
        blind_packets(args.out)
    elif args.command == "blind-verdict":
        freeze_verdicts(args.out, args.input)
    else:
        print(report(args.out)["report"])


if __name__ == "__main__":
    main()
