"""Freeze and evaluate a source-bound model workflow on an isolated replay."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY))

from plumb import apply, propose, reconcile
from plumb.model import ClaudeModel

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
RECEIPTS = ROOT / "receipts"
DECISION = (
    "For this controlled replay the operator identifies sources/decision.md as "
    "the governing current agreement for session restore. sources/proposal.md "
    "is an unapproved future proposal. knowledge/module.md is a potentially "
    "stale local summary. Inspect the imported encoder before judging the public "
    "restore_path behavior. This is a source-selection decision, not permission "
    "to apply edits."
)
FILES = {
    "README.md": """# Session restore module
This is a synthetic Python replay of a documented Pond adapter problem.
The public entry point is code/restore.py; follow its import to the encoder.
knowledge/module.md records local intent. sources/decision.md is the original
decision export; sources/proposal.md is a future proposal. Operator source
selection is supplied separately. No tests or expected answers are in this workspace.
""",
    "code/__init__.py": "",
    "code/restore.py": """from .slug import encode_project


def restore_path(project, session_id):
    return encode_project(project) + "/" + session_id + ".jsonl"
""",
    "code/slug.py": """def encode_project(project):
    return project.replace("/", "-").replace(".", "-")
""",
    "knowledge/module.md": """---
type: Module Contract
title: Session restore
sources:
  - id: previous-plan
    resource: ../sources/proposal.md
---

# Current intended behavior

Project slugs replace slashes and dots only. Normalize Unicode to NFC.

# Responsibility

The public restore_path function delegates project encoding to code/slug.py.
When revising this contract, preserve the governing decision's exact wording
as a quotation and link to its captured source. Generated knowledge is not a
new independent authority.
""",
    "sources/decision.md": """# Captured current decision

Origin: https://github.com/tenequm/pond/commit/a218ef33cb337b2ec8c41bb9b23b02fb76231559
This controlled replay adopts the following requirements from that public correction.

Claude Code's actual rule collapses every non-alphanumeric character.
The regex counts UTF-16 code units: an astral character collapses to two dashes.
NFC normalization does not apply. Claude Code normalizes the memory path,
not the session path. Restore must preserve the native session-path convention.

For this replay, alphanumeric means ASCII a-z, A-Z and 0-9. Each other UTF-16
code unit becomes one dash. Preserve ASCII letters and digits as given.
""",
    "sources/proposal.md": """# Unapproved future proposal

Proposal: add NFC normalization to restore paths and keep spaces readable.
This proposal has not been adopted. It does not change the current agreement.
""",
}
BEHAVIOR_PROGRAM = """import sys
sys.path.insert(0, sys.argv[1])
from code.restore import restore_path
checks = [
    ("/a_b c", "S", "-a-b-c/S.jsonl"),
    ("a\\U0001f600b", "S", "a--b/S.jsonl"),
    ("a\\u0301", "S", "a-/S.jsonl"),
    ("/tmp/project.v1", "S", "-tmp-project-v1/S.jsonl"),
    ("C:" + chr(92) + "dev" + chr(92) + "a_b", "S", "C--dev-a-b/S.jsonl"),
    ("AbC123", "S", "AbC123/S.jsonl"),
]
failures = []
for project, sid, expected in checks:
    actual = restore_path(project, sid)
    if actual != expected:
        failures.append((project, expected, actual))
assert not failures, repr(failures)
print("PASS: six public restore-path behaviors")
"""


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def hashes(workspace=None):
    workspace = workspace or WORKSPACE
    return {
        path.relative_to(workspace).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(workspace.rglob("*"))
        if path.is_file()
    }


def behavior(workspace=None):
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            BEHAVIOR_PROGRAM,
            str((workspace or WORKSPACE).resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return {
        "pass": process.returncode == 0,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def prepare():
    if WORKSPACE.exists():
        raise ValueError(
            "Workspace already exists; retain the existing trial rather than overwrite it"
        )
    for name, text in FILES.items():
        target = WORKSPACE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    baseline = behavior()
    assert not baseline["pass"] and "AssertionError" in baseline["stderr"]
    with tempfile.TemporaryDirectory(prefix="plumb-oracle-") as temporary:
        oracle = Path(temporary)
        for name, text in FILES.items():
            target = oracle / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        (oracle / "code/slug.py").write_text(
            "def encode_project(project):\n"
            '    return "".join(c if c.isascii() and c.isalnum() else "-" * '
            '(len(c.encode("utf-16-le")) // 2) for c in project)\n'
        )
        correct = behavior(oracle)
        assert correct["pass"], correct
    manifest = {
        "fixture_kind": "synthetic Python replay of a public historical Pond requirement",
        "files": hashes(),
        "decision": DECISION,
        "behavior_program_sha256": hashlib.sha256(
            BEHAVIOR_PROGRAM.encode()
        ).hexdigest(),
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "baseline_behavior": baseline,
        "known_good_calibration": correct,
        "human_curation_minutes": None,
    }
    write(ROOT / "frozen.json", manifest)
    print(
        json.dumps(
            {"workspace": str(WORKSPACE.resolve()), "baseline_behavior_pass": False}
        )
    )


def evaluate(prompt=None):
    global WORKSPACE
    frozen = json.loads((ROOT / "frozen.json").read_text())
    assert (
        frozen["evaluator_sha256"]
        == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    )
    assert hashes(WORKSPACE) == frozen["files"], "Frozen seed workspace changed"
    iterations = ROOT / "iterations"
    iterations.mkdir(exist_ok=True)
    out = iterations / f"{len(list(iterations.iterdir())) + 1:04d}"
    out.mkdir()
    shutil.copytree(WORKSPACE, out / "workspace")
    WORKSPACE = out / "workspace"
    source_hashes = {}
    for name in ["core.py", "model.py", "reconcile.md"]:
        source = REPOSITORY / "plumb" / name
        shutil.copy2(source, out / name)
        source_hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    model = ClaudeModel(
        RECEIPTS,
        max_calls=12,
        max_tokens=150000,
        list_cost_limit=3,
        tag="workflow:" + out.name,
        prompt=prompt,
    )
    steps = []
    try:
        before = hashes()
        report = reconcile(WORKSPACE.resolve(), model, decision=DECISION)
        write(out / "initial-report.json", report)
        assert hashes() == before, "check mutated inputs"
        assert report["outcome"] in {"code_wrong", "spec_stale"}, report
        assert report["question"].strip()
        assert any(
            link["from_path"] == "code/restore.py" and link["to_path"] == "code/slug.py"
            for link in report["links"]
        ), "dependency not traced"
        steps.append("diagnosed source/code disagreement with dependency evidence")

        proposal = propose(report, "code", model)
        write(out / "code-proposal.json", proposal)
        assert hashes() == before, "propose mutated inputs"
        assert proposal["edits"][0]["path"].startswith("code/")
        receipt = apply(proposal)
        write(out / "code-apply.json", receipt)
        assert behavior()["pass"], behavior()
        assert apply(proposal)["status"] == "already_applied"
        steps.append(
            "explicit code choice repairs six actual behaviors; repeat apply is safe"
        )

        report = reconcile(WORKSPACE.resolve(), model, decision=DECISION)
        write(out / "after-code-report.json", report)
        assert report["outcome"] == "spec_stale", report
        steps.append("recheck still detects stale module knowledge")

        before_knowledge = hashes()
        proposal = propose(report, "knowledge", model)
        write(out / "knowledge-proposal.json", proposal)
        assert hashes() == before_knowledge, "knowledge proposal mutated inputs"
        assert proposal["edits"][0]["path"].startswith("knowledge/")
        source = WORKSPACE / "sources/decision.md"
        original = source.read_text()
        source.write_text(original + "\nNew source revision after proposal.\n")
        try:
            try:
                apply(proposal)
            except ValueError:
                pass
            else:
                raise AssertionError("stale source accepted")
            assert (
                hashes()["knowledge/module.md"]
                == before_knowledge["knowledge/module.md"]
            )
        finally:
            source.write_text(original)
        write(out / "knowledge-apply.json", apply(proposal))
        assert behavior()["pass"]
        steps.append(
            "explicit knowledge choice updates only knowledge; changed sources block apply"
        )

        report = reconcile(WORKSPACE.resolve(), model, decision=DECISION)
        write(out / "final-report.json", report)
        assert report["outcome"] == "aligned", report
        assert behavior()["pass"]
        steps.append(
            "fresh final reconciliation agrees with current intent and behavior"
        )
        result = {
            "pass": True,
            "score": len(steps),
            "steps": steps,
            "usage": model.usage(),
        }
    except (
        AssertionError,
        RuntimeError,
        ValueError,
        OSError,
        KeyError,
        TypeError,
    ) as error:
        result = {
            "pass": False,
            "score": len(steps),
            "steps": steps,
            "error": str(error)[:3000],
            "usage": model.usage(),
        }
    result.update(iteration=str(out), implementation_hashes=source_hashes)
    write(out / "evaluation.json", result)
    write(ROOT / "evaluation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--prompt")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        evaluate(args.prompt)
