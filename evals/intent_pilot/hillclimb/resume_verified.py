"""Re-evaluate unchanged cached requests after fixing a controller boundary bug."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from plumb.model import ClaudeModel

spec = importlib.util.spec_from_file_location("frozen_workflow_evaluator", ROOT / "evaluate.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
prior = json.loads((ROOT / "evaluation.json").read_text())
assert not prior["pass"] and prior["score"] == 3
assert prior["error"] == "Unresolved outcome requires a human question"
assert prior["usage"]["calls"] == 8
verified = []


class ExactReplay:
    def __init__(self, *args, **kwargs):
        self.live = ClaudeModel(*args, **kwargs)
        self.count = 0

    def usage(self):
        return self.live.usage()

    def __call__(self, system, payload):
        self.count += 1
        if self.count > 8:
            return self.live(system, payload)
        path = ROOT / "receipts" / f"call-{self.count:04d}.json"
        receipt = json.loads(path.read_text())
        original = json.loads(path.with_suffix(".prompt.json").read_text())
        expected_system = system + "\nReturn only one JSON object matching response_schema. No Markdown fences."
        assert original["system"] == expected_system, "Reused system prompt changed"
        assert original["payload"] == payload, "Reused model input changed"
        assert receipt["status"] == "completed"
        assert receipt["response"] == json.loads(receipt["provider"]["result"])
        verified.append(str(path))
        return copy.deepcopy(receipt["response"])


evaluation.ClaudeModel = ExactReplay
try:
    evaluation.evaluate()
finally:
    (ROOT / "verified-replay.json").write_text(json.dumps({
        "reason": "Fix proposal-mode re-question requirement; evaluator and model outputs unchanged",
        "reused_receipts": verified, "new_inference_for_reused_receipts": 0,
        "each_system_and_payload_compared_exactly": True,
    }, indent=2) + "\n")
