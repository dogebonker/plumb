#!/usr/bin/env python3
"""Claude Code PreToolUse hook: hard gates for factory changes.

Blocks Edit/Write/MultiEdit/NotebookEdit on source files (anything outside
.factory/) in a repository with an active factory change on the current
branch, unless the change's gates allow it. Exit 2 blocks the tool call and
shows stderr to the agent; exit 0 allows it. Once an active change is found,
an unreadable state blocks too, so a broken status.yaml cannot open the gate.

ponytail: reads status.yaml with line regexes, which relies on the one-line
flow maps the factory skills write; a real YAML parser if the format grows.
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
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def field(text, key):
    m = re.search(rf"\b{key}:\s*[\"']?([^,\"'}}\s]+)", text)
    return m.group(1) if m else None


def parse_status(text):
    status = {"branch": None, "stubbing": False, "gates": {}, "slices": [], "scalars": {}}
    section = None
    for line in text.splitlines():
        top = re.match(r"^(\w+):\s*(.*)$", line)
        if top:
            section, value = top.group(1), top.group(2).split("#")[0].strip().strip("\"'")
            status["scalars"][section] = None if value in ("", "null") else value
            if section == "branch":
                status["branch"] = value
            elif section == "stubbing":
                status["stubbing"] = value == "true"
            continue
        gate = re.match(r"^\s+(\w+):\s*\{(.*)\}", line)
        if section == "gates" and gate:
            status["gates"][gate.group(1)] = {"state": field(gate.group(2), "state"),
                                              "doc_sha256": field(gate.group(2), "doc_sha256")}
        item = re.match(r"^\s*-\s*\{(.*)\}", line)
        if section == "slices" and item:
            status["slices"].append({"id": field(item.group(1), "id") or "?", "state": field(item.group(1), "state"),
                                     "head_commit": field(item.group(1), "head_commit")})
    return status


def allowed_files(packet):
    files, inside = set(), False
    for line in packet.read_text().splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Allowed files"
        elif inside and line.lstrip().startswith("- "):
            for part in line.lstrip()[2:].split(","):
                if part.split():
                    files.add(part.split()[0].strip("`"))
    return files


def check(change, status, rel):
    """Return a reason to block, or None to allow."""
    gates = status["gates"]
    if len(gates) < len(GATES):
        return "cannot read all four gates in status.yaml; keep each gate as a one-line { } map (gates.md)."
    if status["stubbing"] and gates["interface"]["state"] == "pending":
        return None
    for gate, doc in GATES:
        if gates[gate]["state"] == "approved":
            path = change / doc
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if digest != gates[gate]["doc_sha256"]:
                return f"{doc} changed after the {gate} gate was approved. Run /factory-{gate} to approve it again."
    for gate, _ in GATES:
        if gates[gate]["state"] not in ("approved", "skipped"):
            return f"source edits wait for the slices gate; the {gate} gate is not approved yet. Run /factory-{gate}."
    active = [s for s in status["slices"] if s["state"] in EDITING]
    if not active:
        return "no slice is being built. Run /factory-build to start the next slice."
    for s in active:
        packet = change / "slices" / s["id"].zfill(2) / "packet.md"
        if packet.exists() and rel in allowed_files(packet):
            return None
    ids = ", ".join(s["id"] for s in active)
    return f"{rel} is not in the Allowed files of slice {ids}. Ask the user; if they allow it, log a deviation and add it to the packet."


def find_changes(start):
    for folder in [start, *start.parents]:
        if (folder / ".factory" / "changes").is_dir():
            return folder
    return None


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input") or {}
        target = tool_input.get("file_path") or tool_input.get("notebook_path")
    except (ValueError, AttributeError):
        return 0
    if not target:
        return 0
    path = Path(target)
    if not path.is_absolute():
        path = Path(data.get("cwd") or ".") / path
    probe = path.parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if not find_changes(probe.resolve()):
        return 0
    root = git(probe, "rev-parse", "--show-toplevel")
    if not root:
        return 0
    root = Path(root).resolve()
    try:
        rel = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return 0
    changes = root / ".factory" / "changes"
    if rel.startswith(".factory/") or not changes.is_dir():
        return 0
    branch = git(root, "symbolic-ref", "--short", "HEAD")
    for status_file in sorted(changes.glob("*/status.yaml")):
        try:
            status = parse_status(status_file.read_text())
            if branch and status["branch"] != branch:
                continue
            if status["slices"] and all(s["state"] == "done" for s in status["slices"]):
                continue
            reason = check(status_file.parent, status, rel)
        except Exception as e:  # noqa: BLE001 - an active change with unreadable state stays closed
            reason = f"cannot read the change's state ({type(e).__name__}: {e}). Fix {status_file.relative_to(root)}."
        if reason:
            print(f"factory gate ({status_file.parent.name}): {reason}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
