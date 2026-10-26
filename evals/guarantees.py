"""Execute real Factory regression fixtures; never create approvals in live projects."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'scope': ('runner.test_v2_gates.GateTests.test_scope_includes_untracked_deleted_and_renamed_paths',
              ['kit/v2_gates.py', 'runner/test_v2_gates.py']),
    'frozen': ('runner.test_v2_gates.GateTests.test_frozen_mutation_and_links_fail_before_execution',
               ['kit/v2_gates.py', 'runner/test_v2_gates.py']),
    'frozen-scenarios': ('evals.test_guarantees.GuaranteeReportTests.test_frozen_bdd_and_test_writes_denied_by_real_hook',
                         ['hooks/plumb_v2_gate.py', 'evals/test_guarantees.py']),
    'write-guard': ('hooks.test_plumb_v2_gate.GuardTests.test_denials_preserve_sentinel',
                    ['hooks/plumb_v2_gate.py', 'hooks/test_plumb_v2_gate.py']),
    'compliant-writes': ('hooks.test_plumb_v2_gate.GuardTests.test_permitted_reads_edits_writes_and_searches',
                        ['hooks/plumb_v2_gate.py', 'hooks/test_plumb_v2_gate.py']),
    'stale-proof': ('runner.test_v2_gates.GateTests.test_stale_and_incomplete_evidence_rejected',
                    ['kit/v2_gates.py', 'runner/test_v2_gates.py']),
    'adr-conflict': ('kit.test_adr.ADRTests.test_conflict_opens_question_and_approval_summary_without_editing_approved',
                     ['kit/adr.py', 'kit/test_adr.py']),
    'approval-reuse': ('hooks/test_plumb_gate.py', ['hooks/plumb_gate.py', 'hooks/test_plumb_gate.py']),
    'imports': ('evals/checkers/archgraph/run.py', ['evals/checkers/archgraph/run.py', 'kit/layouts/tools.yaml']),
}


def execute(argv):
    env = dict(os.environ)
    env.pop('LAY01_ALLOW_SKIP', None)  # A skipped native checker cannot count as a pass.
    env['PYTHONPATH'] = os.pathsep.join(str(ROOT / p) for p in ('', 'runner', 'kit', 'hooks', 'evals'))
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300, check=False)
        return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
                'seconds': time.monotonic() - started}
    except subprocess.TimeoutExpired as error:
        return {'returncode': -1, 'stdout': str(error.stdout or ''), 'stderr': str(error.stderr or ''),
                'seconds': time.monotonic() - started, 'timeout': True}


def run(output, names=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError('evidence output must be empty; preserve previous runs')
    selected = list(CASES) if names is None else names
    sources, results = {'evals/guarantees.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, []
    for name in selected:
        target, paths = CASES[name]
        if name == 'imports':
            paths = paths + [str(p.relative_to(ROOT)) for p in (ROOT / 'evals/checkers/archgraph').rglob('*')
                             if p.is_file() and '__pycache__' not in p.parts]
        for path in paths:
            sources[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        argv = [sys.executable, str(ROOT / target)] if target.endswith('.py') else [sys.executable, '-m', 'unittest', target, '-v']
        evidence = execute(argv)
        if name == 'imports':
            for line in evidence['stdout'].splitlines():
                if line.startswith('archgraph logs: '):
                    logs = Path(line.removeprefix('archgraph logs: '))
                    if logs.is_dir() and logs.name.startswith('lay01-archgraph-'):
                        destination = output / 'imports-native-evidence'
                        shutil.copytree(logs, destination)
                        evidence['persistent_native_evidence'] = str(destination)
        status = ('pass' if evidence['returncode'] == 0 else
                  'unsupported' if name == 'imports' and evidence['returncode'] == 2 else 'fail')
        result = {'id': name, 'status': status, 'command': argv, 'evidence': evidence}
        (output / f'{name}.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
    report = {'schema': 1, 'scope': 'Executable regression fixtures; not live model or production assurance',
              'sources': sources, 'cases': results, 'passed': bool(results) and all(x['status'] == 'pass' for x in results)}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', action='append', choices=CASES)
    args = parser.parse_args()
    report = run(args.out, args.case)
    print(json.dumps({'passed': report['passed'], 'cases': [{k: v for k, v in row.items() if k != 'evidence'} for row in report['cases']]}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
