"""Run: python3 hooks/test_factory_gate.py"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from factory_gate import GATES

HOOK = Path(__file__).with_name("factory_gate.py")


def run(root, file_path, content=None):
    tool_input = {"file_path": str(root / file_path)}
    if content is not None:
        tool_input["content"] = content
    payload = json.dumps({"tool_name": "Write" if content is not None else "Edit", "tool_input": tool_input, "cwd": str(root)})
    return subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, check=False)


def status(gates, slices="slices: []", stubbing="false", branch="factory/demo"):
    lines = ["feature: demo", f"branch: {branch}", f"stubbing: {stubbing}", "gates:"]
    lines += [f"  {g}: {{ state: {s}, approved_by: me, approved_at: now, doc_sha256: {h} }}" for g, s, h in gates]
    return "\n".join([*lines, slices]) + "\n"


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    subprocess.run(["git", "init", "-q", "-b", "factory/demo", str(root)], check=True)
    change = root / ".software-factory" / "changes" / "demo"
    (change / "slices" / "01").mkdir(parents=True)
    docs = {}
    for gate, doc in GATES:
        (change / doc).write_text(f"# {gate}\n")
        docs[gate] = hashlib.sha256((change / doc).read_bytes()).hexdigest()
    (change / "slices" / "01" / "packet.md").write_text(
        "# Packet\n\n## Allowed files\n- `src/a.ts`, src/a.test.ts\n- src/c.ts (new)\n\n## Verify\n- `npm test`\n")
    approved = [(g, "approved", h) for g, h in docs.items()]
    pending_product = [("product", "pending", "null"), *approved[1:]]
    building = "slices:\n  - { id: 1, name: tracer, state: building, base_commit: abc }"
    st = change / "status.yaml"
    lock = root / ".software-factory" / "factory.lock"
    lock.write_text("framework: { commit: " + "a" * 40 + ", installed: 2026-10-13 }\n")

    # Pending gate documents remain editable; source edits wait for every gate.
    st.write_text(status(pending_product))
    assert run(root, ".software-factory/changes/demo/01-product.md").returncode == 0
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "product gate" in r.stderr, r.stderr

    # Stubbing passes only while the interface gate is pending.
    interface_pending = [*approved[:2], ("interface", "pending", "null"), ("slices", "pending", "null")]
    st.write_text(status(interface_pending, stubbing="true"))
    assert run(root, "src/a.ts").returncode == 0
    st.write_text(status(approved, slices=building, stubbing="true"))
    assert run(root, "src/elsewhere.ts").returncode == 2

    # All gates approved, no slice in progress: blocked.
    st.write_text(status(approved, slices="slices:\n  - { id: 1, name: tracer, state: pending }"))
    assert "no slice is being built" in run(root, "src/a.ts").stderr

    # Building slice: comma lists and notes in Allowed files work; other files are blocked.
    st.write_text(status(approved, slices=building))
    for allowed in ["src/a.ts", "src/a.test.ts", "src/c.ts"]:
        assert run(root, allowed).returncode == 0, allowed
    assert run(root, "src/b.ts").returncode == 2

    # Resuming cannot enrich an approved document and accidentally revoke its approval.
    approved_status = st.read_bytes()
    for gate, doc in GATES:
        path = f".software-factory/changes/demo/{doc}"
        original = (change / doc).read_text()
        r = run(root, path, original + "\nResume note: implementation continues.\n")
        assert r.returncode == 2 and "approved document" in r.stderr, r.stderr
        assert run(root, path).returncode == 2  # partial editing tools cannot redraft it either
        assert run(root, path, original).returncode == 0  # exact bytes are idempotent
        assert hashlib.sha256((change / doc).read_bytes()).hexdigest() == docs[gate]
    assert st.read_bytes() == approved_status
    assert run(root, "src/a.ts").returncode == 0
    for evidence in ["research.md", "review.md", "supplement.md", "status.yaml"]:
        assert run(root, f".software-factory/changes/demo/{evidence}").returncode == 0

    # A deliberate revision opens only after the gate is made pending; hashes still gate source.
    st.write_text(status([approved[0], *[(g, "pending", "null") for g, _ in GATES[1:]]], slices=building))
    assert run(root, ".software-factory/changes/demo/02-architecture.md").returncode == 0
    assert run(root, "src/a.ts").returncode == 2

    # Security approval is reusable: keep its model frozen, including during later stage resumes.
    model = root / ".software-factory/system/threat-model.md"
    model.parent.mkdir(exist_ok=True)
    model.write_text("# Threat model\nBoundary: authenticated API\n")
    model_hash = hashlib.sha256(model.read_bytes()).hexdigest()
    event = f'history:\n  - {{ at: now, step: factory-security, event: threat_model_approved, ref: "-", detail: "sha256 {model_hash}" }}\n'
    st.write_text(status(approved, slices=building) + event)
    r = run(root, ".software-factory/system/threat-model.md", model.read_text() + "\nResume note\n")
    assert r.returncode == 2 and "approved document" in r.stderr, r.stderr
    assert run(root, ".software-factory/system/threat-model.md", model.read_text()).returncode == 0
    assert run(root, "src/a.ts").returncode == 0

    # A genuinely approved security revision records its new digest before the exact full Write.
    revised_model = model.read_text() + "Boundary: approved worker\n"
    revised_hash = hashlib.sha256(revised_model.encode()).hexdigest()
    revision = f'  - {{ at: later, step: factory-security, event: threat_model_approved, ref: "-", detail: "sha256 {revised_hash}" }}\n'
    st.write_text(status(approved, slices=building) + event + revision)
    assert run(root, ".software-factory/system/threat-model.md", revised_model).returncode == 0
    assert run(root, ".software-factory/system/threat-model.md", model.read_text()).returncode == 2
    assert run(root, ".software-factory/system/threat-model.md").returncode == 2

    # Interactive impact checks can retain compatible architecture/security after a product correction.
    # The hook still waits for actual approval of each changed document, not another architecture approval.
    original_product = (change / "01-product.md").read_text()
    original_interface = (change / "03-interface.md").read_text()
    changed = [approved[0], approved[1], ("interface", "pending", "null"), approved[3]]
    changed[0] = ("product", "pending", "null")
    st.write_text(status(changed, slices=building) + event)
    assert run(root, ".software-factory/changes/demo/01-product.md").returncode == 0
    (change / "01-product.md").write_text(original_product + "Example: remainder is shown in the invoice currency.\n")
    changed[0] = ("product", "approved", hashlib.sha256((change / "01-product.md").read_bytes()).hexdigest())
    st.write_text(status(changed, slices=building) + event)
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "interface gate" in r.stderr and "architecture gate" not in r.stderr, r.stderr
    assert run(root, ".software-factory/changes/demo/02-architecture.md").returncode == 2
    assert run(root, ".software-factory/changes/demo/03-interface.md").returncode == 0
    (change / "03-interface.md").write_text(original_interface + "Response: remaining_invoice_amount\n")
    changed[2] = ("interface", "approved", hashlib.sha256((change / "03-interface.md").read_bytes()).hexdigest())
    st.write_text(status(changed, slices=building) + event)
    assert run(root, "src/a.ts").returncode == 0
    architecture_line = next(line for line in status(approved).splitlines() if line.startswith("  architecture:"))
    assert architecture_line in st.read_text() and st.read_text().endswith(event)
    assert hashlib.sha256(model.read_bytes()).hexdigest() == model_hash
    (change / "01-product.md").write_text(original_product)
    (change / "03-interface.md").write_text(original_interface)

    st.write_text(status(approved, slices=building, branch="factory/other") + event)
    assert run(root, ".software-factory/system/threat-model.md").returncode == 0  # another branch cannot freeze it
    st.write_text(status(approved, slices=building))
    assert run(root, ".software-factory/system/threat-model.md").returncode == 0  # initial draft
    st.write_text(status(approved, slices=building) + event + "reconciled: true\n")
    assert run(root, ".software-factory/system/threat-model.md").returncode == 0
    st.write_text(status(approved, slices=building))

    # A milestone: while slice 2 builds, green slice 1's files are closed; at review time, with nothing
    # building, the green slices' files are open.
    (change / "slices" / "02").mkdir(exist_ok=True)
    (change / "slices" / "02" / "packet.md").write_text("# Packet\n\n## Allowed files\n- src/b.ts\n")
    milestone = "slices:\n  - { id: 1, name: tracer, milestone: 1, state: green }\n  - { id: 2, name: next, milestone: 1, state: building }"
    st.write_text(status(approved, slices=milestone))
    assert run(root, "src/b.ts").returncode == 0 and run(root, "src/a.ts").returncode == 2
    st.write_text(status(approved, slices=milestone.replace("state: building", "state: green")))
    assert run(root, "src/a.ts").returncode == 0 and run(root, "src/b.ts").returncode == 0

    # The append-only history after slices changes nothing the hook reads.
    st.write_text(status(approved, slices=building) + 'history:\n  - { at: now, step: factory-build, event: step_start, ref: "1", detail: "state: done" }\n')
    assert run(root, "src/a.ts").returncode == 0 and run(root, "src/b.ts").returncode == 2

    # Track small: skipped gates count as passed.
    small = [(g, "skipped", "null") for g, _ in GATES[:3]] + [approved[3]]
    st.write_text(status(small, slices=building))
    assert run(root, "src/a.ts").returncode == 0

    # Another branch is not gated; unreadable state on this branch is.
    st.write_text(status(pending_product, branch="factory/other"))
    assert run(root, "src/a.ts").returncode == 0
    st.write_text("branch: factory/demo\ngates:\n  product:\n    state: approved\n")
    assert "cannot read all four gates" in run(root, "src/a.ts").stderr

    # A gate document edited after approval blocks source edits.
    st.write_text(status(approved, slices=building))
    (change / "03-interface.md").write_text("# interface, edited\n")
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "03-interface.md changed" in r.stderr, r.stderr
    # Accidental enrichment is recoverable from proven approved bytes, without new approval.
    assert run(root, ".software-factory/changes/demo/03-interface.md", "# interface\n").returncode == 0
    (change / "03-interface.md").write_text("# interface\n")
    assert run(root, "src/a.ts").returncode == 0

    # A change that touches UI needs the design file; DESIGN.md itself is always editable.
    st.write_text(status(approved, slices=building).replace("feature: demo", "feature: demo\nui: true"))
    (change / "03-interface.md").write_text("# interface\n")
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "no design file" in r.stderr, r.stderr
    assert run(root, "DESIGN.md").returncode == 0
    (root / "DESIGN.md").write_text("# Architecture\n")  # a DESIGN.md that is not a design file
    assert run(root, "src/a.ts").returncode == 2
    (root / "DESIGN.md").write_text("<!-- factory:design-schema 1 -->\n# Design\n")
    assert run(root, "src/a.ts").returncode == 0
    (root / "DESIGN.md").unlink()

    # A change whose slices are all done stays gated until it is reconciled: reconcile's acceptance step
    # sends defects back as new slices, never as edits.
    done = status(approved, slices="slices:\n  - { id: 1, name: tracer, state: done }")
    st.write_text(done)
    assert run(root, "src/z.ts").returncode == 2
    st.write_text(done + "reconciled: true\n")
    assert run(root, "src/z.ts").returncode == 0

    # An active change needs a lock that names a framework, as the skills' Resolve <kit> does.
    st.write_text(status(approved, slices=building))
    assert run(root, "src/a.ts").returncode == 0
    lock.write_text("packs: {}\n")
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "names no framework commit or dev_path" in r.stderr, r.stderr
    lock.unlink()
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "no .software-factory/factory.lock" in r.stderr, r.stderr
    assert run(root, ".software-factory/factory.lock").returncode == 0

# Fast lane parallel group: slices 2 and 3 build at once, each in its own worktree, gated by the checkout's live
# status.yaml. Each worktree admits only its own slice's files; the checkout admits neither while they build there.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp).resolve()

    def g(*args):
        subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)

    g("init", "-q", "-b", "factory/demo")
    change = root / ".software-factory" / "changes" / "demo"
    for n, files in [(1, "src/a.ts"), (2, "src/b.ts, src/b.test.ts, src/sub/b2.ts"), (3, "src/c.ts")]:
        (change / "slices" / f"0{n}").mkdir(parents=True)
        (change / "slices" / f"0{n}" / "packet.md").write_text(f"# Packet\n\n## Allowed files\n- {files}\n")
    for gate, doc in GATES:
        (change / doc).write_text(f"# {gate}\n")
    approved = [(g_, "approved", hashlib.sha256((change / d).read_bytes()).hexdigest()) for g_, d in GATES]
    (root / ".software-factory" / "factory.lock").write_text("framework: { commit: " + "a" * 40 + " }\n")
    st = change / "status.yaml"
    st.write_text(status(approved, slices="slices:\n  - { id: 1, name: tracer, state: pending }"))
    g("add", ".")
    g("commit", "-qm", "plan")
    (root / ".git" / "info" / "exclude").write_text("/.software-factory/worktrees/\n")
    group = ("slices:\n  - { id: 1, name: tracer, milestone: 1, state: green }\n"
             "  - { id: 2, name: two, milestone: 1, state: building }\n  - { id: 3, name: three, milestone: 1, state: building }")
    st.write_text(status(approved, slices=group))  # live and uncommitted: the worktrees' copies still say pending
    wt = {}
    for n in (2, 3):
        wt[n] = root / ".software-factory" / "worktrees" / f"0{n}"
        g("worktree", "add", "-q", "-b", f"factory/demo-0{n}", str(wt[n]), "HEAD")
    assert run(wt[2], "src/b.ts").returncode == 0 and run(wt[2], "src/b.test.ts").returncode == 0
    assert run(wt[3], "src/c.ts").returncode == 0
    (wt[2] / "src" / "sub").mkdir(parents=True)  # git prints a subfolder's common dir relative to it
    assert run(wt[2], "src/sub/b2.ts").returncode == 0
    for n, other in [(2, "src/c.ts"), (3, "src/b.ts"), (2, "src/a.ts")]:
        r = run(wt[n], other)
        assert r.returncode == 2 and f"Allowed files of slice {n}" in r.stderr, (n, other, r.stderr)
    for path in ["src/b.ts", "src/c.ts"]:
        r = run(root, path)
        assert r.returncode == 2 and "own worktree" in r.stderr, r.stderr
    for path in [".software-factory/changes/demo/status.yaml", "DESIGN.md"]:
        r = run(wt[2], path)
        assert r.returncode == 2 and "not in a slice worktree" in r.stderr, (path, r.stderr)
    assert run(root, ".software-factory/changes/demo/status.yaml").returncode == 0
    # Slice 3 checked and green: its worktree closes; slice 2's stays open.
    st.write_text(status(approved, slices=group.replace("three, milestone: 1, state: building", "three, milestone: 1, state: green")))
    r = run(wt[3], "src/c.ts")
    assert r.returncode == 2 and "slice 3 is not being built" in r.stderr, r.stderr
    assert run(wt[2], "src/b.ts").returncode == 0
    # A folder shaped like a slice worktree that is not a worktree of this checkout is closed.
    fake = root / ".software-factory" / "worktrees" / "04"
    subprocess.run(["git", "init", "-q", str(fake)], check=True)
    r = run(fake, "src/d.ts")
    assert r.returncode == 2 and "not a git worktree" in r.stderr, r.stderr
    # The checkout may itself be a linked worktree (a session's worktree): its slice worktrees share its .git.
    co = root / "co"
    g("worktree", "add", "-q", "-b", "factory/co", str(co), "HEAD")
    (co / ".software-factory" / "changes" / "demo" / "status.yaml").write_text(status(approved, slices=group, branch="factory/co"))
    g("worktree", "add", "-q", "-b", "factory/co-02", str(co / ".software-factory" / "worktrees" / "02"), "HEAD")
    assert run(co / ".software-factory" / "worktrees" / "02", "src/b.ts").returncode == 0
    r = run(co / ".software-factory" / "worktrees" / "02", "src/c.ts")
    assert r.returncode == 2 and "Allowed files of slice 2" in r.stderr, r.stderr
    g("worktree", "remove", "--force", str(co / ".software-factory" / "worktrees" / "02"))
    g("worktree", "remove", "--force", str(co))
    # Worktrees removed after the merge: the checkout admits the building slices' files again.
    for n in (2, 3):
        g("worktree", "remove", str(wt[n]))
    subprocess.run(["rm", "-rf", str(fake)], check=True)
    st.write_text(status(approved, slices=group))
    assert run(root, "src/b.ts").returncode == 0 and run(root, "src/c.ts").returncode == 0

# A repository with an unreconciled change in .factory/ is closed to source edits until /factory-init migrates
# it, whatever .software-factory/ already holds; .factory/ and .software-factory/ stay editable so init can run.
LEGACY = "still uses .factory/; run /factory-init"
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    subprocess.run(["git", "init", "-q", "-b", "factory/demo", str(root)], check=True)
    legacy = root / ".factory" / "changes" / "demo" / "status.yaml"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("branch: factory/demo\nreconciled: false\n")
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and LEGACY in r.stderr, r.stderr
    assert run(root, ".factory/changes/demo/status.yaml").returncode == 0
    assert run(root, ".software-factory/factory.lock").returncode == 0
    sf = root / ".software-factory"
    states = [("only the lock", sf / "factory.lock", "framework: { commit: " + "a" * 40 + " }\n"),
              ("only runs/", sf / "runs" / "ui" / "shot.png", "png"),
              ("another change", sf / "changes" / "other" / "status.yaml",
               status([(g, "skipped", "null") for g, _ in GATES]))]
    for name, path, text in states:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        r = run(root, "src/a.ts")
        assert r.returncode == 2 and LEGACY in r.stderr, (name, r.stderr)
    # Every .factory change reconciled: the repository is not blocked for them.
    legacy.write_text("branch: factory/demo\nreconciled: true\n")
    assert LEGACY not in run(root, "src/a.ts").stderr

# An ignored run folder left in .factory/ by a checkout does not count as a legacy change: the migrated branch's
# own change gates as usual.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    def g(*args):
        subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)

    g("init", "-q", "-b", "main")
    (root / ".git" / "info" / "exclude").write_text(".factory/ui/\n")
    (root / ".factory" / "changes" / "demo").mkdir(parents=True)
    (root / ".factory" / "changes" / "demo" / "status.yaml").write_text("branch: main\n")
    (root / ".factory" / "ui").mkdir()
    (root / ".factory" / "ui" / "shot.png").write_text("png")
    g("add", ".")
    g("commit", "-qm", "legacy")
    g("checkout", "-q", "-b", "factory/demo")
    g("rm", "-rq", ".factory")
    change = root / ".software-factory" / "changes" / "demo"
    change.mkdir(parents=True)
    (change / "status.yaml").write_text(status([("product", "pending", "null")] + [(gate, "pending", "null") for gate, _ in GATES[1:]]))
    (root / ".software-factory" / "factory.lock").write_text("framework: { commit: " + "a" * 40 + " }\n")
    g("add", ".")
    g("commit", "-qm", "migrated")
    assert (root / ".factory" / "ui" / "shot.png").exists() and not (root / ".factory" / "changes").exists()
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "product gate" in r.stderr and LEGACY not in r.stderr, r.stderr
    g("checkout", "-q", "main")  # the legacy branch itself is closed again
    assert LEGACY in run(root, "src/a.ts").stderr

    # A lock with two framework lines names no single framework.
    g("checkout", "-q", "factory/demo")
    (root / ".software-factory" / "factory.lock").write_text("framework: { commit: " + "a" * 40 + " }\nframework: { dev_path: /x }\n")
    assert "names no framework commit" in run(root, "src/a.ts").stderr

print("factory_gate: all checks passed")

# Autonomous corrections use frozen original slices, never their mutable packets.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    def g(*args):
        r = subprocess.run(['git', '-C', str(root), '-c', 'user.name=t', '-c', 'user.email=t@t',
                            '-c', 'commit.gpgsign=false', *args], capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def cli(checkpoint='edit'):
        return subprocess.run([sys.executable, HOOK, 'repair-check', '--repo', str(root), '--change', 'demo',
                               '--slice', '03', '--checkpoint', checkpoint], capture_output=True, text=True, check=False)

    g('init', '-q', '-b', 'factory/demo')
    change = root / '.software-factory/changes/demo'
    correction = change / 'slices/03'
    correction.mkdir(parents=True)
    (root / '.software-factory/factory.lock').write_text('framework: { commit: ' + 'a' * 40 + ' }\n')
    (root / 'src').mkdir()
    (root / 'src/a.py').write_text('a = 1\n')
    (root / 'src/b.py').write_text('b = 1\n')
    route = 'app/tickets/[id]/page.tsx'
    (root / route).parent.mkdir(parents=True)
    (root / route).write_text('export default function Page() {}\n')
    (root / 'config.txt').write_text('effective input\n')
    (change / '04-slices.md').write_text(
        '# Slices\n## Development\nMode: autonomous-local\nRepairs: approved-slice-files\n'
        '## Requirements\n- FR-01: promised one\n  Example: return one\n- FR-02: promised two\n  Example: return two\n## Slices\n'
        '### 01 A\nCovers: FR-01\nAllowed files: src/a.py, app/tickets/[id]/page.tsx\n'
        '### 02 B\nCovers: FR-02\nAllowed files: src/b.py\n')
    h = digest(change / '04-slices.md')
    g('add', '.')
    g('commit', '-qm', 'original source and approved plan')
    start = g('rev-parse', 'HEAD')
    st = change / 'status.yaml'
    rows = ('slices:\n  - { id: 1, state: done, head_commit: ' + start + ' }\n'
            '  - { id: 2, state: done, head_commit: ' + start + ' }\n'
            '  - { id: 3, state: building, head_commit: ' + start + ', base_commit: ' + start + ' }')
    st.write_text(status([(x, 'skipped', 'null') for x, _ in GATES[:3]] + [('slices', 'approved', h)], rows)
                  + 'mode: interactive\ntrack: small\n')
    (correction / 'packet.md').write_text('## Allowed files\n- src/a.py\n- app/tickets/[id]/page.tsx\n')
    failure = change / 'acceptance/failure.md'
    failure.parent.mkdir()
    failure.write_text('FR-01 fails independently\n')
    inputs = correction / 'inputs.json'
    inputs.write_text(json.dumps({'criteria': [{'id': 'FR-01', 'text': 'return one'}],
                                 'files': [{'path': 'config.txt', 'sha256': digest(root / 'config.txt')}],
                                 'commands': ['python test.py'], 'environment': 'python fixture'}))
    record = {'id': 3, 'branch': 'factory/demo', 'parents': [{'id': 1, 'head_commit': start}],
              'criteria': ['FR-01'], 'approved_docs': {'product': None, 'architecture': None, 'interface': None, 'slices': h},
              'start_commit': start, 'paths': ['src/a.py', route],
              'failure': {'path': 'acceptance/failure.md', 'sha256': digest(failure), 'source_commit': start, 'criteria': ['FR-01']},
              'proof_inputs': {'path': 'slices/03/inputs.json', 'sha256': digest(inputs)}}

    def save():
        (correction / 'repair.json').write_text(json.dumps(record))

    save()
    # Creation stages the exact candidate packet and pending row before validation/dispatch.
    building_status = st.read_text()
    pending_status = building_status.replace(
        'id: 3, state: building, head_commit: ' + start + ', base_commit: ' + start,
        'id: 3, state: pending, head_commit: null, test_commit: null, base_commit: ' + start)
    parent_rows = [line for line in building_status.splitlines() if 'state: done' in line]
    approved_bytes = (change / '04-slices.md').read_bytes()
    gate_rows = [line for line in building_status.splitlines() if 'doc_sha256:' in line]
    st.write_text(pending_status)
    assert cli().returncode == 0 and 'repair scope valid' in cli().stdout, cli().stderr
    for path in ('src/a.py', route, 'src/b.py'):
        denied = run(root, path)
        assert denied.returncode == 2 and 'no slice is being built' in denied.stderr, denied.stderr
    st.write_text(pending_status.replace('id: 3, state: pending', 'id: 3, state: building'))
    assert cli().returncode == 0, cli().stderr
    assert run(root, 'src/a.py').returncode == 0 and run(root, route).returncode == 0
    assert run(root, 'src/b.py').returncode == 2
    assert [line for line in st.read_text().splitlines() if 'state: done' in line] == parent_rows
    assert [line for line in st.read_text().splitlines() if 'doc_sha256:' in line] == gate_rows
    assert (change / '04-slices.md').read_bytes() == approved_bytes
    st.write_text(building_status)
    before = {path: path.read_bytes() for path in root.rglob('*') if path.is_file()}
    assert cli().returncode == 0 and 'repair scope valid' in cli().stdout, cli().stderr
    after = {path: path.read_bytes() for path in root.rglob('*') if path.is_file()}
    assert before == after, 'validator must not mutate Git/config/status/source'
    assert cli('complete').returncode == 0, cli('complete').stderr
    assert run(root, 'src/a.py').returncode == 0
    assert run(root, route).returncode == 0
    assert cli().returncode == 0 and cli('complete').returncode == 0
    assert run(root, 'src/b.py').returncode == 2
    (correction / 'packet.md').write_text('## Allowed files\n- src/a.py\n')
    assert cli().returncode == 2 and run(root, route).returncode == 2
    (correction / 'packet.md').write_text('## Allowed files\n- src/a.py\n- src/b.py\n')
    assert run(root, 'src/b.py').returncode == 2
    (correction / 'packet.md').write_text('## Allowed files\n- src/a.py\n- app/tickets/[id]/page.tsx\n')
    (correction / 'repair.json').unlink()
    assert run(root, 'src/a.py').returncode == 2
    save()
    (root / 'src/a.py').write_text('a = 2\n')
    assert cli().returncode == 0, cli().stderr
    assert cli('complete').returncode == 2
    (root / 'src/b.py').write_text('b = 2\n')
    assert cli().returncode == 2
    g('checkout', '--', 'src/a.py', 'src/b.py')
    for key, value in [('approval', True), ('criteria', ['FR-99']), ('paths', ['src/b.py'])]:
        old = record.get(key)
        record[key] = value
        save()
        assert cli().returncode == 2, key
        if old is None:
            del record[key]
        else:
            record[key] = old
    save()
    (root / 'config.txt').write_text('changed\n')
    assert cli().returncode == 2
    g('checkout', '--', 'config.txt')
    # Strict receipt schemas and provenance reject forged authority and stale inputs.
    baseline = json.loads(json.dumps(record))
    mutations = [
        ('boolean ID', lambda r: r.update(id=True)),
        ('duplicate parents', lambda r: r['parents'].append(dict(r['parents'][0]))),
        ('repair as parent', lambda r: r['parents'][0].update(id=3)),
        ('duplicate paths', lambda r: r['paths'].append(r['paths'][0])),
        ('traversal', lambda r: r.update(paths=['src/../src/a.py'])),
        ('star pattern', lambda r: r.update(paths=['app/tickets/*/page.tsx'])),
        ('question pattern', lambda r: r.update(paths=['app/tickets/?/page.tsx'])),
        ('control source', lambda r: r.update(paths=['.git/config'])),
        ('foreign branch', lambda r: r.update(branch='factory/other')),
        ('false skipped approval', lambda r: r['approved_docs'].update(product='a' * 64)),
        ('null approved slices', lambda r: r['approved_docs'].update(slices=None)),
        ('stale document', lambda r: r['approved_docs'].update(slices='a' * 64)),
        ('unknown failure criterion', lambda r: r['failure'].update(criteria=['FR-02'])),
        ('missing evidence', lambda r: r['failure'].update(path='acceptance/missing.md')),
        ('escaping evidence', lambda r: r['failure'].update(path='../failure.md')),
        ('missing receipt', lambda r: r['proof_inputs'].update(path='slices/03/missing.json')),
        ('unknown receipt field', lambda r: r['proof_inputs'].update(review='approved')),
        ('unknown commit', lambda r: r.update(start_commit='a' * 40)),
    ]
    for name, mutate in mutations:
        record = json.loads(json.dumps(baseline))
        mutate(record)
        save()
        assert cli().returncode == 2 and run(root, 'src/a.py').returncode == 2, name
    record = json.loads(json.dumps(baseline))
    save()
    repair_path = correction / 'repair.json'
    repair_path.write_text(repair_path.read_text().replace('"id": 3', '"id": 3, "id": 3', 1))
    assert cli().returncode == 2 and 'duplicate' in cli().stderr
    save()
    original_inputs = inputs.read_text()
    for key, value in [('review', 'approved'), ('commands', []), ('environment', True),
                       ('criteria', [{'id': 'FR-01', 'text': 'forged promise'}]),
                       ('files', [{'path': 'src/a.py', 'sha256': digest(root / 'src/a.py')}])]:
        mutated = json.loads(original_inputs)
        mutated[key] = value
        inputs.write_text(json.dumps(mutated))
        record['proof_inputs']['sha256'] = digest(inputs)
        save()
        assert cli().returncode == 2, key
    inputs.write_text(original_inputs)
    record = json.loads(json.dumps(baseline))
    save()
    original_status = st.read_text()
    for text in [original_status.replace('mode: interactive', 'mode: headless'),
                 original_status.replace('base_commit: ' + start, 'base_commit: ' + 'a' * 40),
                 original_status.replace(', base_commit: ' + start, ''),
                 original_status.replace('state: skipped', 'state: pending', 1),
                 original_status.replace('id: 2', 'id: 1'),
                 original_status.replace('id: 1, state: done', 'id: 1, state: building')]:
        st.write_text(text)
        assert cli().returncode == 2 and run(root, 'src/a.py').returncode == 2
    st.write_text(original_status)
    for path in (failure, inputs, change / '04-slices.md', root / 'config.txt', root / 'src/a.py'):
        contents = path.read_bytes()
        outside = root.parent / (root.name + '-outside')
        outside.write_bytes(contents)
        path.unlink()
        path.symlink_to(outside)
        assert cli().returncode == 2, path
        path.unlink()
        path.write_bytes(contents)
        outside.unlink()
    (root / 'src/untracked.py').write_text('unowned\n')
    assert cli().returncode == 2
    (root / 'src/untracked.py').unlink()
    (root / 'src/a.py').write_text('owned staged\n')
    g('add', 'src/a.py')
    assert cli().returncode == 0 and cli('complete').returncode == 2
    g('reset', '-q', 'HEAD', '--', 'src/a.py')
    g('checkout', '--', 'src/a.py')
    g('checkout', '-q', '--detach')
    assert cli().returncode == 2
    g('checkout', '-q', 'factory/demo')
    # Valid owned committed changes need a current completion head receipt.
    (root / 'src/a.py').write_text('a = 2\n')
    g('add', 'src/a.py')
    g('commit', '-qm', 'owned correction')
    fixed_head = g('rev-parse', 'HEAD')
    assert cli().returncode == 0 and cli('complete').returncode == 2
    st.write_text(original_status.replace('id: 3, state: building, head_commit: ' + start,
                                          'id: 3, state: building, head_commit: ' + fixed_head))
    assert cli('complete').returncode == 0
    # Resetting start to corrected source cannot reuse old failure source evidence.
    record['start_commit'] = fixed_head
    save()
    assert cli().returncode == 2
    record = json.loads(json.dumps(baseline))
    save()
    (root / 'src/b.py').write_text('b = 2\n')
    g('add', 'src/b.py')
    g('commit', '-qm', 'forbidden')
    g('revert', '--no-edit', 'HEAD')
    assert cli().returncode == 2, 'reverted forbidden source edit must remain denied'
    g('reset', '--hard', fixed_head)
    g('checkout', '-q', '-b', 'side', start)
    (root / 'src/b.py').write_text('b = 3\n')
    g('add', 'src/b.py')
    g('commit', '-qm', 'foreign merge source')
    g('checkout', '-q', 'factory/demo')
    g('merge', '--no-edit', 'side')
    assert cli().returncode == 2, 'each merge parent diff must stay within scope'

print('factory_gate: correction checks passed')
