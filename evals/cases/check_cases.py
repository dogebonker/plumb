"""Prove public baselines pass, hidden baselines fail, and reference solutions pass."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_tests(workspace, command):
    return subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=120, check=False)


def check_case(case):
    metadata = json.loads((case / "case.json").read_text())
    command = metadata["verify"]
    with tempfile.TemporaryDirectory(prefix="factory-case-") as temporary:
        workspace = Path(temporary) / "fixture"
        shutil.copytree(case / "fixture", workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        public = run_tests(workspace, command)
        if public.returncode:
            raise AssertionError(f"{case.name}: public baseline failed\n{public.stdout}{public.stderr}")
        if metadata.get("kind") in {"browser", "fullstack"}:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from benchmark import grade
            baseline, _ = grade(case, workspace, Path(temporary) / "baseline")
            if baseline["accepted"] or (metadata["kind"] == "browser" and baseline["tests"] != metadata["test_count"]):
                raise AssertionError(f"{case.name}: hidden baseline must fail real browser assertions: {baseline}")
            for reference in (case / "oracle").iterdir():
                if reference.is_dir():
                    shutil.copytree(reference, workspace / reference.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(reference, workspace / reference.name)
            oracle, output = grade(case, workspace, Path(temporary) / "oracle")
            if not oracle["accepted"]:
                raise AssertionError(f"{case.name}: browser oracle failed\n{output}")
            if case.name == "support-dashboard":
                app = workspace / "app.js"
                source = app.read_text()
                faulty = source.replace("        current[name] = value;",
                    '        if (name === "status" && current.priority !== editing.priority) continue;\n'
                    '        current[name] = value;')
                assert faulty != source, "stale-save calibration must mutate the reference"
                app.write_text(faulty)
                mutant, output = grade(case, workspace, Path(temporary) / "stale-status-drop")
                stale = next(row for row in mutant.get("checks", [])
                             if row["name"] == "stale_editor_preserves_other_fields_or_reports_conflict")
                assert not mutant["accepted"] and not stale["passed"], "grader must reject silently dropped stale edits"
            print(f"{metadata['id']}: public baseline PASS; hidden baseline FAIL; oracle PASS")
            return
        shutil.copy2(case / "grading" / "test_acceptance.py", workspace / "test_acceptance.py")
        baseline = run_tests(workspace, command)
        if baseline.returncode != 1 or not ("FAIL:" in baseline.stderr or "ERROR:" in baseline.stderr):
            raise AssertionError(f"{case.name}: hidden baseline must fail assertions\n{baseline.stdout}{baseline.stderr}")
        for reference in (case / "oracle").glob("*.py"):
            shutil.copy2(reference, workspace / reference.name)
        # Force fresh imports even if source sizes and timestamps happen to match.
        for cache in workspace.rglob("__pycache__"):
            shutil.rmtree(cache)
        oracle = run_tests(workspace, command)
        if oracle.returncode:
            raise AssertionError(f"{case.name}: oracle failed\n{oracle.stdout}{oracle.stderr}")
    print(f"{metadata['id']}: public baseline PASS; hidden baseline FAIL; oracle PASS")


def main():
    cases = sorted(Path(__file__).parent.glob("*/case.json"))
    if not cases:
        raise AssertionError("no benchmark cases found")
    for metadata in cases:
        check_case(metadata.parent)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
