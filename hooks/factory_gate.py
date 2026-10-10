#!/usr/bin/env python3
"""Claude Code PreToolUse hook: hard gates for factory changes.

Blocks Edit/Write/MultiEdit/NotebookEdit on source files (anything outside
.factory/) in a repository whose current branch has an active factory change,
unless the change's gates allow it. Exit 2 blocks the tool call and shows
stderr to the agent; exit 0 allows it.

ponytail: reads status.yaml with line regexes, which relies on the flow-map
lines the factory skills write; a real YAML parser if the format grows.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

GATES = [("product", "01-product.md"), ("architecture", "02-architecture.md"),
         ("interface", "03-interface.md"), ("slices", "04-slices.md")]
EDITING = {"building", "red", "green"}


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def field(text, key):
    m = re.search(rf"\b{key}:\s*\"?([^,\"}}\s]+)", text)
    return m.group(1) if m else None


def parse_status(text):
    status = {"branch": None, "stubbing": False, "gates": {}, "slices": [], "deviations": []}
    section = None
    for line in text.splitlines():
        top = re.match(r"^(\w+):\s*(.*)$", line)
        if top:
            section, value = top.group(1), top.group(2)
            if section == "branch":
                status["branch"] = value.split("#")[0].strip().strip('"')
            elif section == "stubbing":
                status["stubbing"] = value.split("#")[0].strip() == "true"
            continue
        gate = re.match(r"^\s+(\w+):\s*\{(.*)\}", line)
        if section == "gates" and gate:
            status["gates"][gate.group(1)] = {"state": field(gate.group(2), "state"),
                                              "doc_sha256": field(gate.group(2), "doc_sha256")}
        item = re.match(r"^\s*-\s*\{(.*)\}", line)
        if section == "slices" and item:
            status["slices"].append({"id": field(item.group(1), "id"), "state": field(item.group(1), "state")})
        if section == "deviations" and item:
            status["deviations"].append({"slice": field(item.group(1), "slice"), "file": field(item.group(1), "file")})
    return status


def allowed_files(packet):
    if not packet.exists():
        return set()
    files, inside = set(), False
    for line in packet.read_text().splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Allowed files"
        elif inside and line.lstrip().startswith("- "):
            files.add(line.lstrip()[2:].strip().strip("`"))
    return files


def check(change, status, rel):
    """Return a reason to block, or None to allow."""
    if status["stubbing"]:
        return None
    for gate, doc in GATES:
        g = status["gates"].get(gate, {})
        if g.get("state") == "approved":
            path = change / doc
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if digest != g.get("doc_sha256"):
                return f"{doc} changed after the {gate} gate was approved. Run /factory-{gate} to approve it again."
    for gate, _ in GATES:
        if status["gates"].get(gate, {}).get("state") not in ("approved", "skipped"):
            return f"source edits wait for the slices gate; the {gate} gate is not approved yet. Run /factory-{gate}."
    active = [s for s in status["slices"] if s["state"] in EDITING]
    if not active:
        return "no slice is being built. Run /factory-build to start the next slice."
    for s in active:
        nn = f"{int(s['id']):02d}"
        ok = allowed_files(change / "slices" / nn / "packet.md")
        ok |= {d["file"] for d in status["deviations"] if d["slice"] and int(d["slice"]) == int(s["id"])}
        if rel in ok:
            return None
    ids = ", ".join(s["id"] for s in active)
    return f"{rel} is not in the Allowed files of slice {ids}. Ask the user; if they allow it, log a deviation and add it to the packet."


def main():
    data = json.load(sys.stdin)
    tool_input = data.get("tool_input", {})
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return 0
    path = Path(target)
    if not path.is_absolute():
        path = Path(data.get("cwd", ".")) / path
    probe = path.parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    root = git(probe, "rev-parse", "--show-toplevel")
    if not root:
        return 0
    root = Path(root)
    rel = path.resolve().relative_to(root.resolve()).as_posix() if path.resolve().is_relative_to(root.resolve()) else None
    changes = root / ".factory" / "changes"
    if rel is None or rel.startswith(".factory/") or not changes.is_dir():
        return 0
    branch = git(root, "symbolic-ref", "--short", "HEAD")
    for status_file in sorted(changes.glob("*/status.yaml")):
        status = parse_status(status_file.read_text())
        if status["branch"] != branch:
            continue
        if status["slices"] and all(s["state"] == "done" for s in status["slices"]):
            continue
        reason = check(status_file.parent, status, rel)
        if reason:
            print(f"factory gate ({status_file.parent.name}): {reason}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
