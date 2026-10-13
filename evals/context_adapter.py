"""Confine the optional Context Mode benchmark plugin to one macOS trial."""
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from browser_runtime import installed_browser, sandbox_policy


def prepare(source, destination, work, protected_cases, browser=False):
    """Copy an already prepared plugin and isolate every MCP/hook subprocess."""
    if platform.system() != "Darwin":
        raise ValueError("Context Mode isolation currently requires macOS sandbox-exec")
    sandbox, node = shutil.which("sandbox-exec"), shutil.which("node")
    if not sandbox or not node:
        raise ValueError("Context Mode isolation requires sandbox-exec and node")
    source, destination, work = (Path(p).resolve() for p in (source, destination, work))
    if (destination.exists() or not work.is_dir() or destination == source or source in destination.parents
            or work == source or source in work.parents or work in source.parents):
        raise ValueError("Use a new plugin destination outside source and an existing trial work directory")
    protected = [Path(p).resolve() for p in protected_cases]
    if any(p == destination or p in destination.parents or p == work or p in work.parents for p in protected):
        raise ValueError("Protected cases must not contain trial work or plugin directories")
    browser_runtime = installed_browser(node) if browser else None
    manifest = json.loads((source / ".claude-plugin/plugin.json").read_text())
    hooks = json.loads((source / "hooks/hooks.json").read_text())
    dependencies = json.loads((source / "package.json").read_text()).get("dependencies", {})
    installed = {}
    for name in dependencies:
        metadata = (source / "node_modules" / name / "package.json").resolve()
        if not metadata.is_relative_to(source / "node_modules") or not metadata.is_file():
            raise ValueError(f"Context Mode dependencies are not ready: {name} must be installed locally")
        installed[name] = json.loads(metadata.read_text())["version"]
    sqlite_backend = None
    if "better-sqlite3" in dependencies:
        sqlite = subprocess.run([node, "-e", ("try { const {DatabaseSync}=require('node:sqlite');"
                                 "const db=new DatabaseSync(':memory:');db.exec('CREATE VIRTUAL TABLE probe USING fts5(x)');"
                                 "db.close();console.log('node:sqlite'); } catch(e) {"
                                 "const r=require('module').createRequire(process.argv[1]);"
                                 "const db=new (r('better-sqlite3'))(':memory:');"
                                 "db.exec('CREATE VIRTUAL TABLE probe USING fts5(x)');db.close();console.log('better-sqlite3'); }"),
                                 str(source / "package.json")], capture_output=True, text=True, check=False, timeout=20)
        if sqlite.returncode:
            raise ValueError("Context Mode SQLite/FTS5 runtime is not ready; no plugin started: " + sqlite.stderr.strip())
        sqlite_backend = sqlite.stdout.strip()
    servers = manifest.get("mcpServers", {})
    if not isinstance(servers, dict) or not servers:
        raise ValueError("Expected inline Context Mode mcpServers")
    for server in servers.values():
        if server.get("command") != "node" or not isinstance(server.get("args"), list):
            raise ValueError("Expected a node Context Mode MCP server")
    commands = [hook for groups in hooks["hooks"].values() for group in groups for hook in group["hooks"]]
    if any(hook.get("type") != "command" or not isinstance(hook.get("command"), str) for hook in commands):
        raise ValueError("Every Context Mode hook must be a command hook")

    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git"))
    shadow = destination / ".benchmark-shadow"
    config, data = shadow / "config", shadow / "data"
    config.mkdir(parents=True)
    data.mkdir()
    scratch = data / "tmp"
    scratch.mkdir()
    adapted_temp_paths = []
    bundle_path = destination / "server.bundle.mjs"
    if bundle_path.exists():
        # shortcut: v1.0.169 bundle anchors; recheck these adapters when the plugin pin changes.
        if manifest.get("version") != "1.0.169":
            raise ValueError("Recheck Context Mode temporary-path adaptation for this plugin version")
        bundle = bundle_path.read_text()
        temporary = re.search(r'\((\w+),"\.ctx-mode-"\)', bundle)
        if not temporary:
            raise ValueError("Context Mode executor temporary-path anchor changed")
        variable = temporary.group(1)
        start = re.search(rf'\b{variable}=\(\(\)=>', bundle)
        end = bundle.find("})();", start.start() if start else 0)
        if not start or end < 0 or "DARWIN_USER_TEMP_DIR" not in bundle[start.start():end]:
            raise ValueError("Context Mode OS temporary-path resolver changed")
        bundle = bundle[:start.start()] + f"{variable}=process.env.TMPDIR;" + bundle[end + 5:]
        sentinel = r'process\.platform==="win32"\?[\w$]+\(\):"/tmp"(?=,[\w$]+=[\w$]+\([\w$]+,`context-mode-mcp-ready-)'
        bundle, count = re.subn(sentinel, "process.env.TMPDIR", bundle)
        if count != 1:
            raise ValueError("Context Mode readiness temporary-path anchor changed")
        bundle_path.write_text(bundle)
        readiness = destination / "hooks/core/mcp-ready.mjs"
        old = 'return process.platform === "win32" ? tmpdir() : "/tmp";'
        text = readiness.read_text()
        if text.count(old) != 1:
            raise ValueError("Context Mode hook readiness temporary-path anchor changed")
        readiness.write_text(text.replace(old, "return process.env.TMPDIR;"))
        adapted_temp_paths = ["server.bundle.mjs", "hooks/core/mcp-ready.mjs"]
    profile = shadow / "sandbox.sb"
    env = {"CLAUDE_CONFIG_DIR": str(config), "CONTEXT_MODE_PROJECT_DIR": str(work), "CONTEXT_MODE_DIR": str(data),
           "TMPDIR": str(scratch)}
    node = str(Path(node).resolve())
    python = Path(sys.executable).resolve()
    env["PATH"] = os.pathsep.join([str(python.parent), str(Path(node).parent), "/opt/homebrew/bin", os.defpath])
    if browser_runtime:
        env["PLAYWRIGHT_MODULE"] = browser_runtime["module"]
    profile.write_text(sandbox_policy(work, [destination], [work, config, data], node, protected, browser_runtime))
    for server in servers.values():
        server["command"] = sandbox
        server["args"] = ["-f", str(profile), node, *server["args"]]
        server["env"] = {**server.get("env", {}), **env}
    for hook in commands:
        original = hook["command"]
        # The upstream command is trusted plugin code; trial prompts never enter this shell command.
        hook["command"] = shlex.join([sandbox, "-f", str(profile), "/usr/bin/env",
                                       *(f"{key}={value}" for key, value in env.items()), "/bin/sh", "-c", original])
    (destination / ".claude-plugin/plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (destination / "hooks/hooks.json").write_text(json.dumps(hooks, indent=2) + "\n")
    return destination, {"source": str(source), "runtime_dependencies": dependencies, "node": node,
                         "installed_versions": installed,
                         "sqlite_backend": sqlite_backend,
                         "browser_runtime": browser_runtime,
                         "temporary_path_adaptations": adapted_temp_paths,
                         "sandbox_profile": str(profile), "shadow_config": str(config),
                         "shadow_data": str(data), "wrapped_hooks": len(commands),
                         "protected_reads": [str(p) for p in protected]}
