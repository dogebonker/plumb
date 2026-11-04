"""Evaluate one separately frozen holdout within the shared 12-call ledger."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from plumb import reconcile
from plumb.model import ClaudeModel

definition = json.loads((ROOT / "holdout.json").read_text())
binding = ROOT / "holdout.frozen.json"
digest = hashlib.sha256((ROOT / "holdout.json").read_bytes()).hexdigest()
if not binding.exists():
    raise RuntimeError("Holdout must be frozen before execution")
assert json.loads(binding.read_text())["sha256"] == digest
workspace = ROOT / "holdout-workspace"
if workspace.exists():
    raise RuntimeError(
        "Retain the existing holdout; do not overwrite or rerun it silently"
    )
for name, text in definition["files"].items():
    path = workspace / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
model = ClaudeModel(
    ROOT / "receipts", max_calls=12, max_tokens=150000, list_cost_limit=3, tag="holdout"
)
usage = model.usage()
if usage["unknown"] or usage["calls"] > 10:
    result = {
        "pass": False,
        "status": "not_run",
        "reason": "Fewer than two calls remain or usage is unknown",
        "usage": usage,
    }
else:
    try:
        report = reconcile(
            workspace.resolve(),
            model,
            decision=definition["decision"],
            max_rounds=min(6, 12 - usage["calls"]),
        )
        (ROOT / "holdout-report.json").write_text(json.dumps(report, indent=2) + "\n")
        expected_from, expected_to = definition["required_link"]
        linked = any(
            link["from_path"] == expected_from and link["to_path"] == expected_to
            for link in report["links"]
        )
        result = {
            "pass": report["outcome"] == definition["expected_outcome"] and linked,
            "outcome": report["outcome"],
            "dependency_proven": linked,
            "usage": model.usage(),
        }
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        result = {"pass": False, "error": str(error), "usage": model.usage()}
(ROOT / "holdout-evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
