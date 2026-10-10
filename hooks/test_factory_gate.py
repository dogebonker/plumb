"""Run: python3 hooks/test_factory_gate.py"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("factory_gate.py")


def run(root, file_path):
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(root / file_path)}, "cwd": str(root)})
    return subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True)


def status(gates, slices="slices: []", stubbing="false", deviations="deviations: []"):
    lines = ["feature: demo", "branch: factory/demo", f"stubbing: {stubbing}", "gates:"]
    lines += [f"  {g}: {{ state: {s}, approved_by: me, approved_at: now, doc_sha256: {h} }}" for g, s, h in gates]
    return "\n".join(lines + [slices, deviations]) + "\n"


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    subprocess.run(["git", "init", "-q", "-b", "factory/demo", str(root)], check=True)
    change = root / ".factory" / "changes" / "demo"
    (change / "slices" / "01").mkdir(parents=True)
    docs = {}
    for gate, doc in [("product", "01-product.md"), ("architecture", "02-architecture.md"),
                      ("interface", "03-interface.md"), ("slices", "04-slices.md")]:
        (change / doc).write_text(f"# {gate}\n")
        docs[gate] = hashlib.sha256((change / doc).read_bytes()).hexdigest()
    (change / "slices" / "01" / "packet.md").write_text("# Packet\n\n## Allowed files\n- `src/a.ts`\n\n## Verify\n- `npm test`\n")
    approved = [(g, "approved", h) for g, h in docs.items()]
    st = change / "status.yaml"

    # Gate documents are always editable.
    st.write_text(status([("product", "pending", "null")] + approved[1:]))
    assert run(root, ".factory/changes/demo/01-product.md").returncode == 0

    # Source edits wait for every gate.
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "product gate" in r.stderr, r.stderr

    # Interface stubbing is allowed before approval.
    st.write_text(status([("product", "pending", "null")] + approved[1:], stubbing="true"))
    assert run(root, "src/a.ts").returncode == 0

    # All gates approved, no slice in progress: blocked.
    st.write_text(status(approved, slices="slices:\n  - { id: 1, name: tracer, state: pending }"))
    assert "no slice is being built" in run(root, "src/a.ts").stderr

    # Building slice: allowed file passes, other files are blocked until a deviation is logged.
    building = "slices:\n  - { id: 1, name: tracer, state: building, base_commit: abc }"
    st.write_text(status(approved, slices=building))
    assert run(root, "src/a.ts").returncode == 0
    assert run(root, "src/b.ts").returncode == 2
    st.write_text(status(approved, slices=building, deviations="deviations:\n  - { slice: 1, file: src/b.ts, reason: shared type }"))
    assert run(root, "src/b.ts").returncode == 0

    # A gate document edited after approval blocks source edits.
    (change / "03-interface.md").write_text("# interface, edited\n")
    r = run(root, "src/a.ts")
    assert r.returncode == 2 and "03-interface.md changed" in r.stderr, r.stderr

    # A finished change is not gated.
    st.write_text(status(approved, slices="slices:\n  - { id: 1, name: tracer, state: done }"))
    assert run(root, "src/z.ts").returncode == 0

print("factory_gate: all checks passed")
