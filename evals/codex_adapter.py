"""Codex CLI commands, fail-closed local policy probes, and observer-side accounting."""
import hashlib
import http.server
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"state": {"type": "string", "enum": ["complete", "question", "blocked"]},
                   "summary": {"type": "string"}, "question": {"type": "string"},
                   "recommended_answer": {"type": "string"}},
    "required": ["state", "summary", "question", "recommended_answer"],
}


def role_fields(text):
    try:
        import tomllib as toml_reader
    except ImportError:
        try:
            import tomli as toml_reader
        except ImportError as error:
            raise ValueError("Role pinning requires Python 3.11+ or an already installed tomli parser") from error
    return toml_reader.loads(text)


def pin_role_text(text, model, effort):
    before = role_fields(text)
    pinned = text
    for key, value in (("model", model), ("model_reasoning_effort", effort)):
        line = key + " = " + json.dumps(value)
        if key in before:
            pinned, count = re.subn(r"(?m)^[ \t]*" + key + r"[ \t]*=.*$", lambda _, replacement=line: replacement, pinned, count=1)
            if count != 1:
                raise ValueError("Cannot safely replace role field: " + key)
        else:
            pinned = line + "\n" + pinned
    expected = dict(before, model=model, model_reasoning_effort=effort)
    if role_fields(pinned) != expected:
        raise ValueError("Role pinning changed fields outside model/effort")
    return pinned


def installed_role_sources(home):
    directory = Path(home) / "agents"
    sources = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Cannot resolve installed role preset symlink: " + str(path))
        if path.suffix != ".toml":
            continue
        if not path.is_file():
            raise ValueError("Installed role preset must be a file: " + str(path))
        fields = role_fields(path.read_bytes().decode("utf-8"))
        name = fields.get("name")
        description = fields.get("description")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise ValueError("Installed role preset has an unsupported/missing name: " + str(path))
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Installed role preset has no description: " + str(path))
        if name in sources:
            raise ValueError("Duplicate installed role preset: " + name)
        sources[name] = path
    return sources


def freeze_role_sources(runtime, sources, model, effort):
    destination = Path(runtime) / "roles"
    destination.mkdir()
    pins = {}
    for name, source in sorted(sources.items()):
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise ValueError("Unsupported role name: " + name)
        path = Path(source)
        original = path.read_bytes().decode("utf-8")
        fields = role_fields(original)
        if fields.get("name") != name or not isinstance(fields.get("description"), str) or not fields["description"].strip():
            raise ValueError("Installed role preset metadata changed before freezing: " + name)
        pinned = destination / (name + ".toml")
        with pinned.open("x") as file:
            file.write(pin_role_text(original, model, effort))
        pinned.chmod(0o444)
        pins[name] = {"config_file": str(pinned), "source": str(path),
                      "source_sha256": hashlib.sha256(original.encode()).hexdigest(),
                      "sha256": hashlib.sha256(pinned.read_bytes()).hexdigest()}
    destination.chmod(0o555)
    return pins


def verify_role_pins(prepared):
    for role, pin in prepared.get("role_pins", {}).items():
        path = Path(pin["config_file"])
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o222:
            raise ValueError("Frozen role is writable or missing: " + role)
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
            raise ValueError("Frozen role was modified: " + role)


def prepare(binary, work, runtime, active, protected, model, effort, browser_runtime=None, dependency_setup=False):
    work, runtime = Path(work).resolve(), Path(runtime).resolve()
    active = [Path(p).resolve() for p in active]
    protected = [Path(p).resolve() for p in protected]
    runtime.mkdir(parents=True, exist_ok=True)
    role_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    role_pins = freeze_role_sources(runtime, installed_role_sources(role_home), model, effort)
    role_preset = {"source_directory": str(role_home / "agents"), "covered_roles": sorted(role_pins),
                   "complete_effective_inventory_verified": False, "uniform_effort_enforced": False,
                   "builtin_source_version": "0.162.1",
                   "builtin_defaults": "default/worker have no config; explorer has an empty config. Their original descriptions are retained by leaving built-ins untouched."}
    filesystem = {":minimal": "read", str(Path.home().resolve()): "none", str(runtime): "none",
                  str(work): "write", str(work / ".git"): "write", **{str(p): "read" for p in active},
                  **{str(p): "none" for p in protected}}
    filesystem["/System/Library/OpenSSL"] = "read"
    node = shutil.which("node")
    if node:
        filesystem[str(Path(node).resolve().parent.parent)] = "read"
    filesystem[str(Path(sys.executable).resolve().parent.parent)] = "read"
    if browser_runtime:
        proof = browser_runtime.get("runtimeproof", browser_runtime)
        readable = [Path(browser_runtime["command"]).parent, Path(shutil.which("node")).resolve().parent.parent,
                    Path(sys.executable).resolve().parent.parent]
        readable.extend(Path(proof[key]) for key in ("module", "core", "cache") if key in proof)
        filesystem.update({str(p): "read" for p in readable})
        filesystem.update({str(p): "none" for p in protected})
    scratch = work / ".tmp"
    scratch.mkdir(exist_ok=True)
    environment = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
                   "GIT_TERMINAL_PROMPT": "0", "TMPDIR": str(scratch),
                   "PATH": os.pathsep.join(([str(Path(node).parent)] if node else [])
                                           + ["/usr/bin", "/bin", "/opt/homebrew/bin", "/usr/sbin", "/sbin"])}
    if dependency_setup:
        environment.update({"NPM_CONFIG_USERCONFIG": "/dev/null", "NPM_CONFIG_CACHE": str(scratch / "npm"),
                            "NPM_CONFIG_PREFIX": str(scratch / "npm-prefix"),
                            "PIP_CONFIG_FILE": "/dev/null", "PIP_CACHE_DIR": str(scratch / "pip"),
                            "PYTHONPYCACHEPREFIX": str(scratch / "pycache"), "PYTHONNOUSERSITE": "1"})
    domains = ["localhost", "127.0.0.1"]
    if dependency_setup:
        domains.extend(["registry.npmjs.org", "pypi.org", "files.pythonhosted.org"])
    config = ["default_permissions=\"bench\"", "approval_policy=\"never\"",
              "permissions.bench.filesystem=" + "{" + ",".join(
                  json.dumps(k) + "=" + json.dumps(v) for k, v in filesystem.items()) + "}",
              'permissions.bench.network={enabled=true,allow_local_binding=true,domains={'
              + ','.join(json.dumps(domain) + '="allow"' for domain in domains) + '}}',
              'shell_environment_policy.inherit="core"',
              'shell_environment_policy.set={' + ','.join(json.dumps(k) + '=' + json.dumps(v)
                                                         for k, v in environment.items()) + '}',
              'project_doc_max_bytes=0', 'web_search="disabled"', 'features.hooks=false', 'features.memories=false',
              'features.apps=false', 'features.plugins=false',
              'features.skip_host_skill_discovery=true',
              'skills.include_instructions=false', 'skills.bundled.enabled=false',
              'agents.max_depth=3', 'agents.max_concurrent_threads_per_session=6',
              'model_reasoning_effort=' + json.dumps(effort)]
    config.extend("agents." + name + ".config_file=" + json.dumps(pin["config_file"])
                  for name, pin in sorted(role_pins.items()))
    if browser_runtime and browser_runtime.get("mcp_bridge"):
        config.append('mcp_servers.benchmark_browser={command=' + json.dumps(sys.executable)
                      + ',args=[' + json.dumps(browser_runtime["mcp_bridge"]) + '],enabled=true,'
                      + 'enabled_tools=["check","red_check"],tools={'
                      + 'check={approval_mode="approve"},red_check={approval_mode="approve"}}}')
    config_args = [arg for setting in config for arg in ("-c", setting)]
    evidence = probe_isolation(binary, work, runtime, active, protected, config_args)
    evidence.extend(probe_network(binary, work, config_args, dependency_setup))
    if browser_runtime:
        for key in ("command", "mcp_bridge"):
            if key in browser_runtime:
                result = subprocess.run([str(binary), "sandbox", "-P", "bench", "-C", str(work),
                                         *config_args, "--", "/usr/bin/touch", browser_runtime[key]],
                                        capture_output=True, timeout=30, check=False)
                evidence.append({"probe": "immutable_" + key + "_write_denied",
                                 "passed": result.returncode != 0, "exit_code": result.returncode})
                if not result.returncode:
                    raise ValueError("Codex immutable browser runtime write was allowed")
        evidence.append(probe_browser(binary, work, runtime, browser_runtime, config_args))
        (runtime / "isolation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (runtime / "isolation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    schema = runtime / "response-schema.json"
    schema.write_text(json.dumps(RESPONSE_SCHEMA, indent=2) + "\n")
    prepared = {"binary": str(binary), "work": str(work), "runtime": str(runtime),
                "model": model, "effort": effort, "config_args": config_args, "shell_environment": environment,
                "role_pins": role_pins, "role_preset": role_preset,
                "schema_path": str(schema), "response_path": str(runtime / "response.json"),
                "isolation_evidence": evidence,
                "limitations": ["Installed role presets are deliberately frozen; project, managed/higher-priority declarations, unseen roots and full forks are not hard-locked. Every observed model/effort must still pass the final benchmark guard.",
                                "Policy probes cover shell filesystem access; managed configuration and non-shell tool surfaces require independent admission review.",
                                "Network admission probes cover loopback, one denied external domain and (when enabled) npm; other allowed registries are configured but not individually probed."]}
    (runtime / "codex-prepared.json").write_text(json.dumps(prepared, indent=2) + "\n")
    return prepared


def probe_isolation(binary, work, runtime, active, protected, config_args):
    evidence = []
    with tempfile.TemporaryDirectory(prefix="factory-codex-guard-", dir=Path.home()) as guard_dir:
        guard = Path(guard_dir) / "guard.txt"
        guard.write_text("benchmark private guard\n")
        own = work / ".codex-policy-probe"
        outside = Path(guard_dir) / "outside.txt"
        tests = [("home_read_denied", ["/bin/cat", str(guard)], False),
                 ("outside_write_denied", ["/usr/bin/touch", str(outside)], False),
                 ("own_write_allowed", ["/usr/bin/touch", str(own)], True),
                 ("own_read_allowed", ["/bin/cat", str(own)], True),
                 ("observer_runtime_write_denied", ["/usr/bin/touch", str(runtime / ".actor-write-probe")], False)]
        for directory in active:
            candidate = next((p for p in directory.rglob("*") if p.is_file()), None) if directory.is_dir() else directory
            if candidate:
                tests.append(("active_workflow_read_allowed", ["/bin/cat", str(candidate)], True))
        for directory in protected:
            candidate = next((p for p in directory.rglob("*") if p.is_file()), None) if directory.is_dir() else directory
            if candidate:
                tests.append(("protected_read_denied", ["/bin/cat", str(candidate)], False))
        try:
            for name, argv, allowed in tests:
                result = subprocess.run([str(binary), "sandbox", "-P", "bench", "-C", str(work),
                                         *config_args, "--", *argv], capture_output=True, timeout=30, check=False)
                passed = (result.returncode == 0) == allowed
                evidence.append({"probe": name, "passed": passed, "exit_code": result.returncode})
                if not passed:
                    raise ValueError(f"Codex policy admission failed: {name}")
        finally:
            own.unlink(missing_ok=True)
    (runtime / "isolation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


def probe_network(binary, work, config_args, dependency_setup):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"codex-loopback-probe")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    urls = [("loopback_allowed", f"http://127.0.0.1:{server.server_port}", True),
            ("external_domain_denied", "https://example.com", False)]
    if dependency_setup:
        urls.append(("dependency_registry_allowed", "https://registry.npmjs.org/react", True))
    evidence = []
    try:
        for name, url, allowed in urls:
            result = subprocess.run([str(binary), "sandbox", "-P", "bench", "-C", str(work),
                                     *config_args, "--", "/usr/bin/curl", "--max-time", "5", "-sS",
                                     "-o", "/dev/null", "-w", "%{http_code}", url],
                                    capture_output=True, timeout=15, check=False)
            passed = (result.returncode == 0 and result.stdout == b"200") if allowed else (
                result.returncode != 0 and b"403" in result.stderr)
            evidence.append({"probe": name, "passed": passed, "exit_code": result.returncode})
            if not passed:
                raise ValueError("Codex network admission failed: " + name)
    finally:
        server.shutdown()
        server.server_close()
    return evidence


def probe_browser(binary, work, runtime, browser_runtime, config_args):
    if browser_runtime.get("enforcement") != "native_seatbelt_mcp_capability":
        raise ValueError("Codex browser capability admission failed: native MCP broker required")
    marker = "codex-admission-" + uuid.uuid4().hex
    script = work / ("test_" + marker + ".cjs")
    with tempfile.TemporaryDirectory(prefix="factory-browser-guard-", dir=Path.home()) as directory:
        guard = Path(directory) / "guard.txt"
        guard.write_text("private benchmark guard")
        script.write_text("const fs=require('node:fs'),assert=require('node:assert');\n"
                          + "require('node:test')(" + json.dumps(marker) + ",async()=>{"
                          + "assert.throws(()=>fs.readFileSync(" + json.dumps(str(guard)) + "));"
                          + "assert.throws(()=>fs.writeFileSync(" + json.dumps(str(guard)) + ",'bad'));"
                          + "const p=require(process.env.PLAYWRIGHT_MODULE);"
                          + "const b=await p.chromium.launch({headless:true});"
                          + "try{const page=await b.newPage();await page.setContent('<button>probe</button>');"
                          + "assert.equal(await page.getByRole('button').textContent(),'probe');}"
                          + "finally{await b.close();}});\n")
        requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "factory-admission", "version": "1"}}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "check", "arguments": {}}}]
        try:
            result = subprocess.run([sys.executable, browser_runtime["mcp_bridge"]],
                                    input="\n".join(map(json.dumps, requests)) + "\n",
                                    capture_output=True, timeout=60, check=False, text=True)
            (runtime / "browser-admission.log").write_text(result.stdout + result.stderr)
            responses = {event["id"]: event for line in result.stdout.splitlines()
                         if "id" in (event := json.loads(line))}
            tools = {tool["name"] for tool in responses[2]["result"]["tools"]}
            payload = json.loads(responses[3]["result"]["content"][0]["text"])
            match = re.search(r"^Raw log: (.+)$", payload["output"], re.MULTILINE)
            if tools != {"check", "red_check"} or not match:
                raise ValueError("unexpected browser broker response")
            log = Path(match[1]).resolve()
            if not log.is_relative_to(work / ".tmp" / "browser-check"):
                raise ValueError("browser broker log escaped owned scratch")
            raw = log.read_text()
            passed = bool(re.search(r"^ok \d+ - " + re.escape(marker) + r"$", raw, re.MULTILINE))
            passed = passed and not re.search(r"^not ok \d+ - " + re.escape(marker) + r"$", raw, re.MULTILINE)
            (runtime / "browser-admission-tap.log").write_text(raw)
            if not passed:
                raise ValueError("real browser/guard probe did not pass")
            return {"probe": "real_browser_and_guard_denials", "passed": True,
                    "enforcement": "native_seatbelt_mcp_capability", "public_test_exit": payload["exit_code"],
                    "log": str(runtime / "browser-admission-tap.log")}
        except (KeyError, OSError, json.JSONDecodeError, ValueError) as error:
            raise ValueError("Codex browser capability admission failed: " + str(error)) from error
        finally:
            script.unlink(missing_ok=True)


def command(prepared, prompt, session_id=None):
    verify_role_pins(prepared)
    argv = [prepared["binary"], "exec"]
    if session_id:
        argv.extend(["resume", session_id])
    argv.extend(["--strict-config", "--ignore-user-config", "--ignore-rules", "--json", "--output-schema",
                 prepared["schema_path"], "-o", prepared["response_path"], "-m", prepared["model"],
                 *prepared["config_args"]])
    if not session_id:
        argv.extend(["-C", prepared["work"]])
    return [*argv, prompt]


def normalize_usage(root_id, rollout_paths, expected_threads=None):
    """Only response usage is additive; turn/thread counters include previous responses."""
    records, seen, problems, contexts, discovered = [], set(), [], {}, set()
    for path in rollout_paths:
        try:
            lines = Path(path).read_text().splitlines()
        except OSError:
            problems.append("missing_rollout:" + str(path))
            continue
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                problems.append("invalid_rollout_line:" + str(path))
                continue
            payload = event.get("payload", {})
            if event.get("type") == "turn_context":
                contexts[payload.get("turn_id")] = {"model": payload.get("model"), "effort": payload.get("effort")}
            if event.get("type") != "token_usage_record" or payload.get("session_id") != root_id:
                continue
            thread, response = payload.get("thread_id"), payload.get("response_id")
            if not thread or not response:
                problems.append("missing_response_identity")
                continue
            discovered.add(thread)
            # Forks copy response identities: counting the response twice inflates cost.
            identity = (thread, response)
            if identity in seen:
                continue
            seen.add(identity)
            usage = payload.get("usage", {})
            fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens")
            if any(not isinstance(usage.get(k), int) or usage[k] < 0 for k in fields):
                problems.append("incomplete_usage:" + response)
                records.append({"thread_id": thread, "response_id": response, "turn_id": payload.get("turn_id"), "usage": usage, "complete": False})
                continue
            if usage["cached_input_tokens"] + usage["cache_write_input_tokens"] > usage["input_tokens"]:
                problems.append("invalid_cache_subsets:" + response)
                continue
            records.append({"thread_id": thread, "response_id": response, "turn_id": payload.get("turn_id"), "usage": usage, "complete": True})
    for thread in set(expected_threads or []) - discovered:
        problems.append("missing_thread_usage:" + thread)
    totals = {k: 0 for k in ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens")}
    cost = 0.0
    for record in records:
        record.update(contexts.get(record["turn_id"], {"model": None, "effort": None}))
        if record.get("effort") is None:
            problems.append("missing_effort:" + record["response_id"])
        if not record["complete"]:
            continue
        usage = record["usage"]
        for key in totals:
            totals[key] += usage[key]
        if record["model"] != "gpt-6.1-sol":
            problems.append("unpriced_model:" + str(record["model"]))
            continue
        long = usage["input_tokens"] > 272000
        ordinary = usage["input_tokens"] - usage["cached_input_tokens"] - usage["cache_write_input_tokens"]
        estimate = (ordinary * (4 if long else 2)
                    + usage["cached_input_tokens"] * (.2 if long else .1)
                    + usage["cache_write_input_tokens"] * (5 if long else 2.5)
                    + usage["output_tokens"] * (15 if long else 10)) / 1_000_000
        record["modeled_api_usd"] = estimate
        cost += estimate
    if not records:
        problems.append("no_response_usage")
    return {"root_thread_id": root_id, "records": records, "totals": totals,
            "response_count": len(records), "problems": sorted(set(problems)),
            "accounting_complete": not problems, "modeled_api_usd": cost if not problems else None,
            "observed_priced_usd": cost, "actual_invoice_usd": None,
            "price_basis": "GPT-6.1-Sol standard API rates; observed model/effort are client turn context, backend rerouting is unknown."}


def lifecycle_status(thread_id, path):
    """Open/closed edges describe resumability; owned turn events describe completion."""
    try:
        events = [json.loads(line) for line in Path(path).read_text().splitlines()]
    except (OSError, json.JSONDecodeError):
        return {"state": "missing_or_truncated", "turn_id": None}
    meta = next((e.get("payload", {}) for e in events if e.get("type") == "session_meta"
                 and e.get("payload", {}).get("id") == thread_id), None)
    if not meta:
        return {"state": "missing_ownership", "turn_id": None}
    try:
        created = int(datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00")).timestamp())
    except (KeyError, ValueError, TypeError):
        return {"state": "missing_ownership_time", "turn_id": None}
    owned_turns, inherited_turns = set(), set()
    for event in events:
        payload = event.get("payload", {})
        if event.get("type") == "token_usage_record":
            target = owned_turns if payload.get("thread_id") == thread_id else inherited_turns
            target.add(payload.get("turn_id"))
    current, state, start_index = None, "missing_start", None
    for index, event in enumerate(events):
        if event.get("type") == "token_usage_record":
            payload = event.get("payload", {})
            if payload.get("thread_id") == thread_id and (not payload.get("turn_id") or payload["turn_id"] != current):
                current, state, start_index = payload.get("turn_id"), "missing_start_metadata", index
            continue
        if event.get("type") != "event_msg":
            continue
        payload = event.get("payload", {})
        kind, turn = payload.get("type"), payload.get("turn_id")
        if kind == "task_started":
            started = payload.get("started_at")
            if (turn and turn in inherited_turns) or (type(started) in (int, float) and started < created):
                continue
            if not turn or type(started) not in (int, float):
                current, state, start_index = turn, "missing_start_metadata", index
                continue
            current, state, start_index = turn, "running", index
        elif start_index is not None and kind in ("error", "turn_aborted", "task_failed"):
            if turn is None or turn == current:
                state = "error" if kind in ("error", "task_failed") else "interrupted"
        elif kind == "task_complete" and turn == current and current in owned_turns and state == "running":
            state = "complete"
    return {"state": state, "turn_id": current, "owned_response_evidence": current in owned_turns}


def collect_usage(thread_id, artifact, codex_home=None):
    """Final totals require an exited root process and no CLI persistence/save failures."""
    home = Path(codex_home or os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    paths, threads, problems, lifecycle = [], {thread_id}, [], {}
    try:
        with sqlite3.connect(f"file:{home / 'state_5.sqlite'}?mode=ro", uri=True) as db:
            edges = db.execute("SELECT parent_thread_id,child_thread_id,status FROM thread_spawn_edges").fetchall()
            root = db.execute("SELECT created_at FROM threads WHERE id=?", (thread_id,)).fetchone()
            if root:
                for child, path in db.execute("SELECT id,rollout_path FROM threads WHERE created_at>=?", root):
                    try:
                        with Path(path).open() as rollout:
                            meta = json.loads(rollout.readline()).get("payload", {})
                        source = meta.get("source", {})
                        parent = source.get("subagent", {}).get("thread_spawn", {}).get("parent_thread_id") if isinstance(source, dict) else None
                        if parent and not any(edge[1] == child for edge in edges):
                            edges.append((parent, child, "unknown"))
                    except (OSError, json.JSONDecodeError):
                        continue
            changed = True
            while changed:
                changed = False
                for parent, child, status in edges:
                    if parent in threads and child not in threads:
                        threads.add(child)
                        changed = True
            for thread in threads:
                row = db.execute("SELECT rollout_path FROM threads WHERE id=?", (thread,)).fetchone()
                if row:
                    paths.append(row[0])
                    lifecycle[thread] = lifecycle_status(thread, row[0])
                    if lifecycle[thread]["state"] != "complete":
                        problems.append("thread_lifecycle:" + thread + ":" + lifecycle[thread]["state"])
                else:
                    problems.append("missing_thread:" + thread)
    except sqlite3.Error as error:
        problems.append("state_db:" + str(error))
    result = normalize_usage(thread_id, paths, threads)
    result["lifecycle"] = lifecycle
    result["completion_basis"] = "Owned latest task_started/task_complete with matching response turn identity and no subsequent error/interruption/start. Edge status is resumability only; final collection requires root process exit and no CLI persistence/save/shutdown failures; product acceptance requires separate controller evidence."
    result["problems"] = sorted(set(result["problems"] + problems))
    result["accounting_complete"] = not result["problems"]
    if result["problems"]:
        result["modeled_api_usd"] = None
    artifact = Path(artifact)
    artifact.mkdir(parents=True, exist_ok=True)
    observed = artifact / "rollout-accounting.jsonl"
    with observed.open("w") as destination:
        for path in paths:
            try:
                for line in Path(path).read_text().splitlines():
                    event = json.loads(line)
                    if event.get("type") in ("session_meta", "turn_context", "token_usage_record") or (
                            event.get("type") == "event_msg" and event.get("payload", {}).get("type") in (
                                "task_started", "task_complete", "error", "turn_aborted", "task_failed")):
                        destination.write(json.dumps(event) + "\n")
            except (OSError, json.JSONDecodeError):
                pass
    (artifact / "usage.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
