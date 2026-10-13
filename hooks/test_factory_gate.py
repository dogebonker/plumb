"""Run: python3 hooks/test_factory_gate.py"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from factory_gate import GATES

HOOK = Path(__file__).with_name("factory_gate.py")


def run(root, file_path):
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(root / file_path)}, "cwd": str(root)})
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

    # Gate documents are always editable; source edits wait for every gate.
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
