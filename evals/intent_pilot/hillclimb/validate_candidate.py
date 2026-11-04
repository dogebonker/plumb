"""Replay identical saved actor inputs through the strengthened behavior gate."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from plumb.model import ClaudeModel

spec = importlib.util.spec_from_file_location(
    "validated_workflow_evaluator", ROOT / "evaluate.py"
)
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
verified = []


class NoInferenceReplay:
    def __init__(self, *args, **kwargs):
        self.ledger = ClaudeModel(*args, **kwargs)
        self.count = 0

    def usage(self):
        return self.ledger.usage()

    def __call__(self, system, payload):
        self.count += 1
        if self.count > 10:
            raise AssertionError(
                "Saved actor responses exhausted; inference is disabled"
            )
        path = ROOT / "receipts" / f"call-{self.count:04d}.json"
        record = json.loads(path.read_text())
        original = json.loads(path.with_suffix(".prompt.json").read_text())
        assert (
            original["system"]
            == system
            + "\nReturn only one JSON object matching response_schema. No Markdown fences."
        )
        assert original["payload"] == payload, "Candidate changed actor input"
        assert record["status"] == "completed"
        assert record["response"] == json.loads(record["provider"]["result"])
        verified.append(str(path))
        return copy.deepcopy(record["response"])


evaluation.ClaudeModel = NoInferenceReplay
try:
    evaluation.evaluate()
finally:
    (ROOT / "candidate-replay.json").write_text(
        json.dumps(
            {
                "reason": "Strengthen snapshot checks to inspect actual iteration workspace, not seed",
                "reused_receipts": verified,
                "new_model_calls": 0,
                "each_system_and_payload_compared_exactly": True,
                "original_evaluator_binding": "frozen-v1.json",
            },
            indent=2,
        )
        + "\n"
    )
