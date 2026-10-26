#!/usr/bin/env python3
"""Claude Code PreToolUse hook: hard gates for Plumb changes.

Keeps approved gate documents and the active change's approved threat model frozen.
Blocks Edit/Write/MultiEdit/NotebookEdit on source files (anything outside
.plumb/ and the root DESIGN.md) in a repository with an active Plumb change
on the current branch, unless the change's gates allow it. Exit 2 blocks the tool call and
shows stderr to the agent; exit 0 allows it. Once an active change is found,
an unreadable state blocks too, so a broken status.yaml cannot open the gate.

ponytail: reads status.yaml with line regexes, which relies on the one-line
flow maps Plumb skills write; a real YAML parser if the format grows.
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
DESIGN_STAMP = "factory:design-schema"  # marks a design file Plumb made, not any DESIGN.md; kept from before the rename
LEGACY = (".factory", ".software-factory")  # state folders from before .plumb/; /plumb-init migrates them


def git(cwd, *args, raw=False):
    try:
        r = subprocess.run(["git", "--no-optional-locks", "-C", str(cwd), *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return (r.stdout if raw else r.stdout.strip()) if r.returncode == 0 else None


def common_dir(folder):
    """The shared .git of every worktree of folder's repository."""
    value = git(folder, "rev-parse", "--git-common-dir")
    return value and (folder / value).resolve()


def field(text, key):
    m = re.search(rf"\b{key}:\s*[\"']?([^,\"'}}\s]+)", text)
    return m.group(1) if m else None


def parse_status(text):
    status = {"branch": None, "stubbing": False, "gates": {}, "slices": [], "scalars": {},
              "threat_model_sha256": None}
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
                                              "doc_sha256": field(gate.group(2), "doc_sha256"),
                                              "approved_at": field(gate.group(2), "approved_at")}
        item = re.match(r"^\s*-\s*\{(.*)\}", line)
        if section == "slices" and item:
            status["slices"].append({"id": field(item.group(1), "id") or "?", "state": field(item.group(1), "state"),
                                     "head_commit": field(item.group(1), "head_commit"),
                                     "base_commit": field(item.group(1), "base_commit")})
        if section == "history" and item and field(item.group(1), "event") == "threat_model_approved":
            digest = re.search(r'\bdetail:\s*["\']?sha256 ([0-9a-f]{64})(?=["\',}\s]|$)', item.group(1))
            if not digest:
                raise ValueError("cannot read approved threat model digest")
            status["threat_model_sha256"] = digest.group(1)
    return status


def approved_document_problem(change, status, rel, content=None):
    root = change.parent.parent.parent
    digest = status["threat_model_sha256"] if rel == ".plumb/system/threat-model.md" else None
    for gate, doc in GATES:
        if rel == (change / doc).relative_to(root).as_posix() and status["gates"].get(gate, {}).get("state") == "approved":
            digest = status["gates"][gate]["doc_sha256"] or "invalid"
    if digest is None or isinstance(content, str) and hashlib.sha256(content.encode()).hexdigest() == digest:
        return None
    return (f"approved document is frozen: {rel}. Keep progress and supplemental evidence in separate files; "
            "reuse its approval and continue. Propose material decision changes separately before revising it. "
            "A full Write restoring the exact approved bytes is allowed.")


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


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=pairs)


def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError(f'expected exactly {keys}')


def strings(value):
    if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError('expected nonempty string array')
    if len(set(value)) != len(value):
        raise ValueError('duplicate values')
    return value


def source_path(path):
    return not (path == 'DESIGN.md' or path.split('/')[0] in {'.git', '.plumb', *LEGACY})


def safe_path(root, value, source=False, existing=False):
    """Literal paths only: brackets are route names, never expanded as patterns."""
    if (not isinstance(value, str) or not value or any(c in value for c in '\\*?\x00\r\n')
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(part in {'', '.', '..'} for part in value.split('/')) or value.startswith('/')):
        raise ValueError(f'unsafe path: {value!r}')
    if source and not source_path(value):
        raise ValueError(f'control path is not source: {value}')
    path = root
    for part in value.split('/'):
        path = path / part
        if path.is_symlink():
            raise ValueError(f'symlink path: {value}')
    if not path.resolve().is_relative_to(root.resolve()) or (existing and not path.is_file()):
        raise ValueError(f'missing or escaped file: {value}')
    return path


def hash_file(root, entry, source=False):
    exact(entry, 'path sha256')
    if not isinstance(entry['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256']):
        raise ValueError('invalid SHA-256')
    path = safe_path(root, entry['path'], source=source, existing=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        raise ValueError(f'changed evidence/input: {entry["path"]}')
    return path


def original_slices(text):
    result = {}
    headings = list(re.finditer(r'^### (\d+)\s+[^\n]+$', text, re.MULTILINE))
    for i, heading in enumerate(headings):
        ident = int(heading[1])
        if ident < 1 or ident in result:
            raise ValueError('duplicate or malformed original slice ID')
        block = text[heading.end():headings[i + 1].start() if i + 1 < len(headings) else len(text)]
        covers = re.search(r'^Covers:\s*(.+)$', block, re.MULTILINE)
        paths = re.search(r'^Allowed files:\s*(.+)$', block, re.MULTILINE)
        if not covers or not paths:
            raise ValueError('original slice lacks Covers or Allowed files')
        result[ident] = (strings([x.strip().strip('`') for x in covers[1].split(',')]),
                         strings([x.strip().strip('`') for x in paths[1].split(',')]))
    if not result:
        raise ValueError('cannot read original slice headings')
    return result


def mandate(text):
    section = re.search(r'^## Development\s*\n(.*?)(?=^## |\Z)', text, re.MULTILINE | re.DOTALL)
    return bool(section and re.search(r'^Mode: autonomous-local\s*$', section[1], re.MULTILINE)
                and re.search(r'^Repairs: approved-slice-files\s*$', section[1], re.MULTILINE))


def criterion_texts(change, status):
    paths = [change / '04-slices.md'] if status['scalars'].get('track') == 'small' else [change / '01-product.md', change / '02-architecture.md']
    standing = change.parent.parent / 'system/constraints.md'
    if standing.is_file():
        paths.append(standing)
    result = {}
    for path in paths:
        root = change.parent.parent.parent
        text = safe_path(root, path.relative_to(root).as_posix(), existing=True).read_text()
        header, current_fr = None, None
        for line in text.splitlines():
            if line.startswith('|'):
                cells = [x.strip() for x in line.strip('|').split('|')]
                if 'ID' in cells and any(x in cells for x in ('Fit criterion', 'Budget')):
                    header = cells
                elif header and len(cells) == len(header):
                    ident = cells[header.index('ID')].strip('`')
                    column = 'Fit criterion' if 'Fit criterion' in header else 'Budget'
                    if re.fullmatch(r'(?:SYS-)?(?:FR|NFR)-\d+', ident):
                        result[ident] = cells[header.index(column)]
            else:
                match = re.match(r'^- (FR-\d+):\s*(.+)$', line)
                if match:
                    current_fr = match[1]
                example = re.match(r'^\s+Example:\s*(.+)$', line)
                if example and current_fr:
                    if current_fr in result:
                        raise ValueError('ambiguous approved criterion: multiple Examples')
                    result[current_fr] = example[1]
                budget = re.match(r'^- (NFR-\d+):\s*.+?\s*->\s*(.+)$', line)
                if budget:
                    result[budget[1]] = budget[2]
    return result


def git_paths(root, *args):
    value = git(root, *args, raw=True)
    if value is None:
        raise ValueError('cannot read Git source paths')
    return [path for path in value.split('\x00') if path]


def touched_commits(root, start, head):
    commits = git(root, 'rev-list', f'{start}..{head}')
    if commits is None:
        raise ValueError('cannot read Git commit range')
    paths = []
    for commit in commits.splitlines():
        parents = git(root, 'rev-list', '--parents', '-n', '1', commit)
        if parents is None:
            raise ValueError('cannot read Git commit parents')
        for parent in parents.split()[1:]:
            paths.extend(git_paths(root, 'diff', '--name-only', '--no-renames', '-z', parent, commit))
    return paths


def repair_check(root, change, status, ident, checkpoint):
    """Read-only structural/scope validation; receipts do not confer approval or review."""
    def commit(value):
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value) or git(root, 'rev-parse', '--verify', value + '^{commit}') != value:
            raise ValueError('invalid or missing commit')
        return value

    def ancestor(a, b):
        if git(root, 'merge-base', '--is-ancestor', a, b) is None:
            raise ValueError('commit is not an ancestor')

    def ids(value):
        if type(value) is not int or value < 1:
            raise ValueError('invalid slice ID')
        return value

    safe_path(root, change.relative_to(root).as_posix())
    if status['scalars'].get('mode') != 'interactive':
        raise ValueError('corrections require explicit interactive mode')
    doc = safe_path(change, '04-slices.md', existing=True)
    text = doc.read_text()
    if not mandate(text):
        raise ValueError('original approved slices lack Development mandate')
    originals = original_slices(text)
    rows = {}
    for row in status['slices']:
        if not re.fullmatch(r'[0-9]+', row['id']) or int(row['id']) < 1 or int(row['id']) in rows:
            raise ValueError('duplicate or malformed status slice ID')
        rows[int(row['id'])] = row
    if ident not in rows or ident in originals or ident != max(rows):
        raise ValueError('correction must be the next unused slice ID')
    record_path = safe_path(change, f'slices/{ident:02d}/repair.json', existing=True)
    record = strict_json(record_path)
    exact(record, 'id branch parents criteria approved_docs start_commit paths failure proof_inputs')
    if ids(record['id']) != ident:
        raise ValueError('record ID differs from slice')
    branch = git(root, 'symbolic-ref', '--short', 'HEAD')
    if not branch or record['branch'] != branch or status['branch'] != branch:
        raise ValueError('correction branch differs from attached/status branch')
    exact(record['approved_docs'], 'product architecture interface slices')
    for gate, filename in GATES:
        state = status['gates'].get(gate, {})
        claimed = record['approved_docs'][gate]
        if state.get('state') == 'skipped' and gate != 'slices' and status['scalars'].get('track') == 'small':
            if claimed is not None or state.get('doc_sha256') != 'null':
                raise ValueError('skipped gate requires null digest')
        elif state.get('state') == 'approved' and state.get('approved_at') not in {None, 'null'}:
            hash_file(change, {'path': filename, 'sha256': claimed})
            if claimed != state.get('doc_sha256'):
                raise ValueError('approved document digest differs from status')
        else:
            raise ValueError(f'{gate} gate is not genuinely approved or legitimately skipped')
    start = commit(record['start_commit'])
    if rows[ident]['base_commit'] != start:
        raise ValueError('correction base_commit differs from immutable repair start')
    head = commit(git(root, 'rev-parse', 'HEAD'))
    ancestor(start, head)
    if not isinstance(record['parents'], list) or not record['parents']:
        raise ValueError('missing original parents')
    parents, covers, allowed = set(), set(), set()
    for parent in record['parents']:
        exact(parent, 'id head_commit')
        parent_id = ids(parent['id'])
        if parent_id in parents or parent_id not in originals or parent_id not in rows:
            raise ValueError('duplicate or unknown original parent')
        parents.add(parent_id)
        row = rows[parent_id]
        fixed = commit(parent['head_commit'])
        if row['state'] != 'done' or row['head_commit'] != fixed:
            raise ValueError('original parent must remain done at recorded head')
        ancestor(fixed, start)
        covers.update(originals[parent_id][0])
        allowed.update(originals[parent_id][1])
    for path in allowed:
        safe_path(root, path, source=True)
    criteria = set(strings(record['criteria']))
    if not criteria <= covers:
        raise ValueError('unknown or widened repair criteria')
    paths = set(strings(record['paths']))
    for path in paths:
        safe_path(root, path, source=True)
    if not paths <= allowed:
        raise ValueError('repair paths widen original approved scope')
    packet = safe_path(change, f'slices/{ident:02d}/packet.md', existing=True)
    if allowed_files(packet) != paths:
        raise ValueError('packet widens or omits repair scope')
    failure = record['failure']
    exact(failure, 'path sha256 source_commit criteria')
    hash_file(change, {'path': failure['path'], 'sha256': failure['sha256']})
    if set(strings(failure['criteria'])) != criteria:
        raise ValueError('failure criteria differ')
    tested = commit(failure['source_commit'])
    ancestor(tested, start)
    if any(source_path(p) for p in touched_commits(root, tested, start)):
        raise ValueError('failure source changed before repair baseline')
    input_path = hash_file(change, record['proof_inputs'])
    inputs = strict_json(input_path)
    exact(inputs, 'criteria files commands environment')
    strings(inputs['commands'])
    if not isinstance(inputs['environment'], str) or not inputs['environment'].strip():
        raise ValueError('missing environment identity')
    known = criterion_texts(change, status)
    input_ids = []
    if not isinstance(inputs['criteria'], list) or not inputs['criteria']:
        raise ValueError('missing proof criteria')
    for criterion in inputs['criteria']:
        exact(criterion, 'id text')
        if not isinstance(criterion['id'], str) or not isinstance(criterion['text'], str) or not criterion['text'] or known.get(criterion['id']) != criterion['text']:
            raise ValueError('proof criterion is not verbatim approved criterion')
        input_ids.append(criterion['id'])
    if set(strings(input_ids)) != criteria:
        raise ValueError('proof criteria differ')
    if not isinstance(inputs['files'], list) or not inputs['files']:
        raise ValueError('missing effective inputs')
    input_files = []
    for entry in inputs['files']:
        path = hash_file(root, entry)
        if entry['path'] in paths or path == input_path:
            raise ValueError('effective inputs include mutable repair source or receipt')
        input_files.append(entry['path'])
    strings(input_files)
    dirty = (git_paths(root, 'diff', '--name-only', '--no-renames', '-z')
             + git_paths(root, 'diff', '--cached', '--name-only', '--no-renames', '-z')
             + git_paths(root, 'ls-files', '--others', '--exclude-standard', '-z'))
    for path in touched_commits(root, start, head) + dirty:
        if source_path(path):
            safe_path(root, path, source=True)
            if path not in paths:
                raise ValueError(f'source path outside repair scope: {path}')
    if checkpoint == 'complete':
        if any(source_path(path) for path in dirty):
            raise ValueError('completion requires clean source index/worktree')
        recorded_head = commit(rows[ident]['head_commit'])
        ancestor(start, recorded_head)
        ancestor(recorded_head, head)
        if any(source_path(path) for path in touched_commits(root, recorded_head, head)):
            raise ValueError('completion head proof is stale')
    return paths


def repair_cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--change', required=True)
    parser.add_argument('--slice', required=True)
    parser.add_argument('--checkpoint', choices=['edit', 'complete'], required=True)
    args = parser.parse_args(sys.argv[2:])
    try:
        root = Path(args.repo)
        if not root.is_absolute() or git(root, 'rev-parse', '--show-toplevel') != str(root.resolve()):
            raise ValueError('repo must be an absolute Git repository root')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.change) or not re.fullmatch(r'\d+', args.slice):
            raise ValueError('invalid change or slice identifier')
        change = safe_path(root, f'.plumb/changes/{args.change}')
        status_path = safe_path(change, 'status.yaml', existing=True)
        reason = lock_problem(root) or ('legacy Plumb change remains active' if legacy_active(root) else None)
        if reason:
            raise ValueError(reason)
        repair_check(root, change, parse_status(status_path.read_text()), int(args.slice), args.checkpoint)
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print('repair scope valid')
    return 0


def check(change, status, rel, worktree=None):
    """Return a reason to block, or None to allow. worktree: the slice number whose worktree holds rel."""
    gates = status["gates"]
    if len(gates) < len(GATES):
        return "cannot read all four gates in status.yaml; keep each gate as a one-line { } map (gates.md)."
    root = change.parent.parent.parent
    if status["scalars"].get("ui") == "true" and not any(
            (root / f).exists() and DESIGN_STAMP in (root / f).read_text(errors="replace")
            for f in ("DESIGN.md", ".plumb/system/design.md")):
        return "this change touches UI and the repository has no design file. Run /plumb-ui-ux design-md."
    if status["stubbing"] and gates["interface"]["state"] == "pending":
        return None
    for gate, doc in GATES:
        if gates[gate]["state"] == "approved":
            path = safe_path(root, (change / doc).relative_to(root).as_posix())
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if digest != gates[gate]["doc_sha256"]:
                return (f"{doc} changed after the {gate} gate was approved. Compare with the approved snapshot; "
                        "restore only your own incidental edits from proven approved bytes, or propose the actual "
                        "decision change through /plumb-" + gate + ". Do not reapprove unchanged decisions.")
    for gate, _ in GATES:
        if gates[gate]["state"] not in ("approved", "skipped"):
            return f"source edits wait for the slices gate; the {gate} gate is not approved yet. Run /plumb-{gate}."
    if status["slices"] and all(s["state"] == "done" for s in status["slices"]):
        return "every slice is done. Run /plumb-reconcile; a defect comes back as a new slice."
    building = [s for s in status["slices"] if s["state"] in EDITING - {"green"}]
    if worktree is not None:
        # A slice worktree (plumb-build, Fast lane) edits only its own slice's files, while it builds.
        active = [s for s in building if re.fullmatch(r"[0-9]+", s["id"]) and int(s["id"]) == worktree]
        if not active:
            return f"slice {worktree} is not being built, so its worktree is closed."
    else:
        # A slice building in its own worktree is edited there, never in the checkout.
        folder = root / ".plumb" / "worktrees"
        away = {int(p.name) for p in folder.iterdir() if re.fullmatch(r"[0-9]+", p.name)} if folder.is_dir() else set()
        here = [s for s in building if not (re.fullmatch(r"[0-9]+", s["id"]) and int(s["id"]) in away)]
        if building and not here:
            return "every slice being built has its own worktree under .plumb/worktrees/; edit there."
        # While a slice is being built, only its packet counts; green slices waiting for their milestone's
        # review are editable only at review time, when nothing is being built.
        active = here or [s for s in status["slices"] if s["state"] == "green"]
        if not active:
            return "no slice is being built. Run /plumb-build to start the next slice."
    original = original_slices((change / "04-slices.md").read_text()) if mandate((change / "04-slices.md").read_text()) else None
    if original is not None:
        ids = [s["id"] for s in status["slices"]]
        if any(not re.fullmatch(r"[0-9]+", ident) or int(ident) < 1 for ident in ids) or len({int(ident) for ident in ids}) != len(ids):
            return "duplicate or malformed status slice ID"
    repairs = {}
    for s in active:
        record = change / "slices" / s["id"].zfill(2) / "repair.json"
        if record.exists() or (original is not None and (not s["id"].isdigit() or int(s["id"]) not in original)):
            try:
                repairs[s["id"]] = repair_check(root, change, status, int(s["id"]), "edit")
            except (ValueError, OSError, TypeError, KeyError) as error:
                return f"invalid correction: {error}"
    for s in active:
        if s["id"] in repairs:
            if rel in repairs[s["id"]]:
                safe_path(root, rel, source=True)
                return None
            continue
        packet = change / "slices" / s["id"].zfill(2) / "packet.md"
        if packet.exists() and rel in allowed_files(packet):
            return None
    ids = ", ".join(s["id"] for s in active)
    return f"{rel} is not in the Allowed files of slice {ids}. Ask the user; if they allow it, log a deviation and add it to the packet."


def find_changes(start):
    for folder in [start, *start.parents]:
        if any((folder / name / "changes").is_dir() for name in (".plumb", *LEGACY)):
            return folder
    return None


def lock_problem(root):
    """The skills' Resolve <kit> refusal for a missing or empty lock; the cache itself is not checked per edit."""
    lock = root / ".plumb" / "plumb.lock"
    if not lock.is_file():
        return "no .plumb/plumb.lock. Run /plumb-init."
    lines = re.findall(r"^framework:(.*)$", lock.read_text(errors="replace"), re.MULTILINE)
    if len(lines) != 1 or not (field(lines[0], "commit") or field(lines[0], "dev_path")):
        return ".plumb/plumb.lock names no framework commit or dev_path. Run /plumb-init."
    return None


def legacy_active(root):
    """The legacy folder whose changes include one not reconciled: the repository still needs /plumb-init."""
    for name in LEGACY:
        for status_file in (root / name / "changes").glob("*/status.yaml"):
            try:
                if parse_status(status_file.read_text())["scalars"].get("reconciled") != "true":
                    return name
            except Exception:  # noqa: BLE001 - unreadable legacy state stays closed
                return name
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
    # A slice worktree (plumb-build, Fast lane) is <checkout>/.plumb/worktrees/NN (or under a legacy folder),
    # gated by the checkout's live state; its own copy of Plumb files is not the conductor's and stays closed.
    worktree = None
    if (re.fullmatch(r"[0-9]+", root.name) and root.parent.name == "worktrees"
            and root.parent.parent.name in (".plumb", *LEGACY)):
        common = common_dir(probe)
        root, worktree = root.parents[2], int(root.name)
        if not common or common != common_dir(root):
            print(f"plumb gate: slice worktree {worktree} is not a git worktree of {root}", file=sys.stderr)
            return 2
        if rel.startswith(tuple(f"{name}/" for name in (".plumb", *LEGACY))) or rel == "DESIGN.md":
            print("plumb gate: Plumb files change in the checkout, not in a slice worktree", file=sys.stderr)
            return 2
    # Decided before any .plumb logic: a lock, runs/ or another change there must not open the gate.
    if legacy := legacy_active(root):
        frozen = any(rel == f"{name}/system/threat-model.md" or any(
            re.fullmatch(re.escape(name) + r"/changes/[^/]+/" + re.escape(doc), rel) for _, doc in GATES)
            for name in LEGACY)
        if frozen:
            print(f"plumb gate: gate documents under {legacy}/ stay closed until /plumb-init migrates them", file=sys.stderr)
            return 2
        if rel.startswith(tuple(f"{name}/" for name in (".plumb", *LEGACY))):
            return 0
        print(f"plumb gate: this repository still uses {legacy}/; run /plumb-init to migrate it", file=sys.stderr)
        return 2
    changes = root / ".plumb" / "changes"
    metadata = rel.startswith(".plumb/")
    protected = rel == ".plumb/system/threat-model.md" or any(
        re.fullmatch(r"\.plumb/changes/[^/]+/" + re.escape(doc), rel) for _, doc in GATES)
    if rel == "DESIGN.md" or not changes.is_dir() or metadata and not protected:
        return 0
    branch = git(root, "symbolic-ref", "--short", "HEAD")
    for status_file in sorted(changes.glob("*/status.yaml")):
        try:
            status = parse_status(status_file.read_text())
            if branch and status["branch"] != branch:
                continue
            if status["scalars"].get("reconciled") == "true":
                continue
            if metadata:
                content = tool_input.get("content") if data.get("tool_name") == "Write" else None
                reason = approved_document_problem(status_file.parent, status, rel, content)
            else:
                reason = lock_problem(root) or check(status_file.parent, status, rel, worktree)
        except Exception as e:  # noqa: BLE001 - an active change with unreadable state stays closed
            reason = f"cannot read the change's state ({type(e).__name__}: {e}). Fix {status_file.relative_to(root)}."
        if reason:
            print(f"plumb gate ({status_file.parent.name}): {reason}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(repair_cli() if sys.argv[1:2] == ["repair-check"] else main())
