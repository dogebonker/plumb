"""Fixed browser checks under the same native policy used by Context Mode."""
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path


def installed_browser(node):
    module = Path(os.environ.get("PLAYWRIGHT_MODULE", "")).resolve()
    cache = (Path.home() / "Library/Caches/ms-playwright").resolve()
    metadata = module / "package.json"
    core = module.parent / "playwright-core"
    if (not os.environ.get("PLAYWRIGHT_MODULE") or not metadata.is_file()
            or json.loads(metadata.read_text()).get("name") != "playwright" or not (core / "package.json").is_file()):
        raise ValueError("Browser trials require PLAYWRIGHT_MODULE pointing to an installed Playwright package")
    probe = subprocess.run([node, "-e", "console.log(require(process.argv[1]).chromium.executablePath())", str(module)],
                           capture_output=True, text=True, check=False, timeout=20)
    executable = Path(probe.stdout.strip()).resolve()
    if probe.returncode or not executable.is_relative_to(cache) or not os.access(executable, os.X_OK):
        raise ValueError("Browser trials require an already installed Chromium browser cache")
    return {"module": str(module), "core": str(core.resolve()), "cache": str(cache),
                       "version": json.loads(metadata.read_text())["version"], "executable": str(executable)}


def sandbox_policy(work, readable, writable, node, protected, browser_runtime=None, strict_reads=False):
    python = Path(sys.executable).resolve()
    readable = [work, *readable, Path(node).parent.parent, python.parent.parent,
                Path(sysconfig.get_path("stdlib")).resolve()]
    if browser_runtime:
        readable.extend(Path(browser_runtime[key]) for key in ("module", "core", "cache"))
    def subpath(path):
        return f"(subpath {json.dumps(str(path))})"

    network = "(deny network*)\n"
    if browser_runtime:
        network += ('(allow network-outbound (remote ip "localhost:*"))\n'
                    '(allow network-inbound (local ip "localhost:*"))\n'
                    '(allow network-bind (local ip "localhost:*"))\n')
    metadata_reads = ""
    if browser_runtime:
        ancestors = {parent for key in ("module", "core", "cache") for parent in Path(browser_runtime[key]).parents}
        metadata_reads = "".join(f"(allow file-read-metadata (literal {json.dumps(str(p))}))\n"
                                 for p in sorted(ancestors))
    policy = ("(version 1)\n(allow default)\n" + network
                       + "(deny file-write* (require-all " + " ".join(f"(require-not {subpath(p)})" for p in writable) + "))\n"
                       + "(deny file-read* (require-all " + subpath(Path.home().resolve()) + " "
                       + " ".join(f"(require-not {subpath(p)})" for p in readable) + "))\n"
                       + '(allow file-write* (literal "/dev/null"))\n'
                       + metadata_reads + "".join(f"(deny file-read* {subpath(p)})\n" for p in protected))
    if strict_reads:
        roots = [*readable, Path("/System"), Path("/usr"), Path("/bin"), Path("/sbin"),
                 Path("/dev"), Path("/private/var/db"), Path("/opt/homebrew"), Path("/Library"), Path("/private/etc")]
        policy += "(deny file-read-data (require-all (vnode-type REGULAR-FILE) " + " ".join(
            f"(require-not {subpath(path.resolve())})" for path in roots) + "))\n"
    return policy


_MCP_HELPER = r"""
import json
import subprocess
import sys

CAPABILITIES = CAPABILITIES_JSON

def reply(identity, result=None, error=None):
    value = {"jsonrpc": "2.0", "id": identity}
    value["error" if error else "result"] = error or result
    print(json.dumps(value), flush=True)

for line in sys.stdin:
    request = None
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            raise ValueError("Expected an object")
        if "id" not in request:
            continue
        identity = request["id"]
        method, params = request.get("method"), request.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("Parameters must be an object")
        if method == "initialize":
            reply(identity, {"protocolVersion": params.get("protocolVersion", "2025-03-26"),
                             "capabilities": {"tools": {}},
                             "serverInfo": {"name": "factory-browser-capability", "version": "1"}})
        elif method == "ping":
            reply(identity, {})
        elif method == "tools/list":
            reply(identity, {"tools": [{"name": name,
                "description": "Run the fixed isolated browser " + name + " and retain full logs.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}
                for name in CAPABILITIES]})
        elif method == "tools/call":
            name = params.get("name")
            if name not in CAPABILITIES or params.get("arguments", {}) != {}:
                reply(identity, error={"code": -32602, "message": "Only fixed zero-argument checks are allowed"})
                continue
            check = subprocess.run([CAPABILITIES[name]], capture_output=True, text=True, check=False)
            reply(identity, {"content": [{"type": "text", "text": json.dumps({
                "exit_code": check.returncode, "output": (check.stdout + check.stderr)[:12000]})}],
                "isError": check.returncode != 0})
        else:
            reply(identity, error={"code": -32601, "message": "Unsupported method"})
    except (ValueError, TypeError, OSError) as error:
        reply(request.get("id") if isinstance(request, dict) else None,
              error={"code": -32603, "message": str(error)})
"""



_CHECK_HELPER = r"""
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {spawn} = require('node:child_process'), {constants} = require('node:os');
function run(work, logRoot, finished = () => {}) {
const log = path.join(logRoot, 'check-' + crypto.randomUUID() + '.log');
const fd = fs.openSync(log, 'wx');
let failures = '', summary = '', tail = '', failureLines = 0;
const states = new Map();
function line(text) {
  if (/^not ok\b/.test(text)) failureLines = 30;
  if (/^# (tests|suites|pass|fail|cancelled|skipped|todo|duration_ms)\b/.test(text)) {
    summary = (summary + text + '\n').slice(-1500);
  } else if (failureLines > 0 || /^\s+(failureType|error|code|expected|actual|operator):/.test(text)) {
    failures = (failures + text + '\n').slice(0, 6000);
    failureLines = Math.max(0, failureLines - 1);
    if (text.trim() === '...') failureLines = 0;
  }
}
function capture(stream, chunk) {
  for (let offset = 0; offset < chunk.length;) offset += fs.writeSync(fd, chunk, offset, chunk.length - offset);
  const text = chunk.toString();
  tail = (tail + text).slice(-1000);
  let state = states.get(stream) || {pending: '', dropping: false};
  for (const part of text.split(/(?<=\n)/)) {
    if (!state.dropping) state.pending += part;
    if (part.endsWith('\n')) {
      if (!state.dropping) line(state.pending.trimEnd());
      state = {pending: '', dropping: false};
    } else if (state.pending.length > 4096) {
      line(state.pending.slice(0, 4096));
      state = {pending: '', dropping: true};
    }
  }
  states.set(stream, state);
}
const tests = fs.readdirSync(work).filter(name => /^test.*\.cjs$/.test(name)).sort();
const child = spawn(process.execPath, ['--test', '--test-reporter=tap', ...(tests.length ? tests : [path.join(work, 'test*.cjs')])], {cwd: work, env: process.env, stdio: ['ignore', 'pipe', 'pipe']});
child.stdout.on('data', chunk => capture('stdout', chunk));
child.stderr.on('data', chunk => capture('stderr', chunk));
child.on('error', error => capture('stderr', Buffer.from(error.stack + '\n')));
child.on('close', (code, signal) => {
  for (const state of states.values()) if (state.pending) line(state.pending);
  fs.closeSync(fd);
  const status = code === null ? (signal ? 128 + (constants.signals[signal] || 0) : 1) : code;
  const diagnostic = !summary ? '\nDiagnostic tail:\n' + tail : '';
  process.stdout.write(('Browser check exit: ' + status + '\nRaw log: ' + log + '\n' + failures + summary + diagnostic).slice(0, 8500) + '\n');
  finished({exit_code: status, raw_log: log, test_command: [process.execPath, '--test', '--test-reporter=tap', ...tests]});
  process.exitCode = status;
});
}
module.exports = {run};
if (require.main === module) run(process.cwd(), path.join(process.cwd(), '.tmp', 'browser-check'));
"""


_RED_HELPER = r"""
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const work = process.cwd(), gitPath = GIT_PATH;
const env = {...process.env, GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null', GIT_TERMINAL_PROMPT: '0'};
function git(cwd, ...args) {
  return execFileSync(gitPath, ['-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
    '-c', 'init.templateDir=', '-C', cwd, ...args], {env, encoding: 'utf8', stdio: ['ignore','pipe','pipe']}).trim();
}
function directory(folder) {
  fs.mkdirSync(folder, {recursive: true});
  if (fs.realpathSync(folder) !== folder) throw new Error('Browser RED paths must not contain symlinks');
}
const factory = path.join(work, '.software-factory'), requestPath = path.join(factory, 'browser-red.json');
if (fs.realpathSync(factory) !== factory || fs.realpathSync(requestPath) !== requestPath) {
  throw new Error('Browser RED request must not contain symlinks');
}
const request = JSON.parse(fs.readFileSync(requestPath, 'utf8'));
if (!request || Object.keys(request).sort().join(',') !== 'checkpoint,commit' ||
    typeof request.commit !== 'string' || typeof request.checkpoint !== 'string' ||
    !/^[0-9a-f]{40}$/.test(request.commit) || !/^[A-Za-z0-9_-]{1,64}$/.test(request.checkpoint)) {
  throw new Error('Browser RED requires only a full commit SHA and safe checkpoint slug');
}
const commit = git(work, 'rev-parse', '--verify', request.commit + '^{commit}');
if (commit !== request.commit) throw new Error('Browser RED must name an actual commit');
git(work, 'merge-base', '--is-ancestor', commit, 'HEAD');
const deliverableHead = git(work, 'rev-parse', 'HEAD');
const scratch = path.join(factory, 'scratch'), evidence = path.join(factory, 'browser-red-evidence');
directory(scratch); directory(evidence);
let exclude = git(work, 'rev-parse', '--git-path', 'info/exclude');
if (!path.isAbsolute(exclude)) exclude = path.join(work, exclude);
const ignored = fs.readFileSync(exclude, 'utf8').split('\n');
const missing = ['/.software-factory/scratch/', '/.software-factory/browser-red.json', '/.software-factory/browser-red-evidence/']
  .filter(entry => !ignored.includes(entry));
if (missing.length) fs.appendFileSync(exclude, '\n' + missing.join('\n') + '\n');
const clone = fs.mkdtempSync(path.join(scratch, 'browser-red-' + request.checkpoint + '-'));
git(work, 'clone', '-q', '--no-hardlinks', '--no-checkout', '--', work, clone);
git(clone, 'remote', 'remove', 'origin');
git(clone, 'checkout', '-q', '--detach', commit);
const recordPath = path.join(evidence, request.checkpoint + '-' + crypto.randomUUID() + '.json');
const record = {state: 'started', test_commit: commit, source_tree: git(clone, 'rev-parse', 'HEAD^{tree}'),
  deliverable_head: deliverableHead, verification_clone: clone,
  command: path.join(__dirname, 'browser-check-red'),
  command_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname, 'browser-check-red'))).digest('hex'),
  helper_sha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex')};
fs.writeFileSync(recordPath, JSON.stringify(record, null, 2) + '\n', {flag: 'wx'});
require('./capture-check.cjs').run(clone, path.join(work, '.tmp', 'browser-check'), result => {
  Object.assign(record, result, {state: 'finished', deliverable_head_after: git(work, 'rev-parse', 'HEAD')});
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2) + '\n');
  process.stdout.write('RED checkpoint: ' + recordPath + '\n');
});
"""


def prepare_browser_check(destination, work, protected, codex_sandbox=False):
    """Create a fixed, argument-free runner for this trial's test*.cjs files."""
    sandbox, node, git = shutil.which("sandbox-exec"), shutil.which("node"), shutil.which("git")
    if platform.system() != "Darwin" or not sandbox or not node or not git:
        raise ValueError("Browser checks require macOS sandbox-exec and node")
    destination, work = Path(destination).resolve(), Path(work).resolve()
    protected = [Path(p).resolve() for p in protected]
    if (destination.exists() or not work.is_dir() or destination == work
            or work in destination.parents or destination in work.parents):
        raise ValueError("Browser-check runtime must be new and outside trial work")
    if any(p == destination or p in destination.parents or p == work or p in work.parents for p in protected):
        raise ValueError("Protected cases must not contain browser runtime or work")
    node = str(Path(node).resolve())
    runtime = installed_browser(node)
    destination.mkdir(parents=True)
    data = work / ".tmp" / "browser-check"
    data.mkdir(parents=True)
    profile = destination / "sandbox.sb"
    profile.write_text(sandbox_policy(work, [destination], [work, data], node, protected, runtime,
                                      strict_reads=codex_sandbox))
    command = destination / "browser-check"
    env = {"PLAYWRIGHT_MODULE": runtime["module"], "TMPDIR": str(data),
           "PATH": os.pathsep.join([str(Path(node).parent), str(Path(sys.executable).resolve().parent), os.defpath])}
    helper = destination / "capture-check.cjs"
    helper.write_text(_CHECK_HELPER)
    prefix = [sandbox, "-f", str(profile)]
    cmd = shlex.join([*prefix, "/usr/bin/env", "-i",
                      *(f"{key}={value}" for key, value in env.items()), node, str(helper)])
    command.write_text('#!/bin/sh -p\n[ "$#" -eq 0 ] || exit 64\ncd ' + shlex.quote(str(work)) + '\nexec ' + cmd + '\n')
    command.chmod(0o555)
    profile.chmod(0o444)
    helper.chmod(0o444)
    red_helper = destination / "capture-red.cjs"
    red_helper.write_text(_RED_HELPER.replace("GIT_PATH", json.dumps(str(Path(git).resolve()))))
    red_command = destination / "browser-check-red"
    red_cmd = shlex.join([*prefix, "/usr/bin/env", "-i",
                          *(f"{key}={value}" for key, value in env.items()), node, str(red_helper)])
    red_command.write_text('#!/bin/sh -p\n[ "$#" -eq 0 ] || exit 64\ncd ' + shlex.quote(str(work)) + '\nexec ' + red_cmd + '\n')
    red_helper.chmod(0o444)
    red_command.chmod(0o555)
    files = [("command", command), ("profile", profile), ("helper", helper),
             ("red_command", red_command), ("red_helper", red_helper)]
    result = {"command": str(command), "profile": str(profile), "helper": str(helper),
              "red_command": str(red_command), "red_helper": str(red_helper), "runtimeproof": runtime,
              "enforcement": "native_seatbelt_mcp_capability" if codex_sandbox else "native_seatbelt_wrapper"}
    if codex_sandbox:
        bridge = destination / "browser-mcp.py"
        bridge.write_text(_MCP_HELPER.replace("CAPABILITIES_JSON", json.dumps({
            "check": str(command), "red_check": str(red_command)})))
        bridge.chmod(0o444)
        result["mcp_bridge"] = str(bridge)
        files.append(("mcp_bridge", bridge))
    result["sha256"] = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in files}
    return result
