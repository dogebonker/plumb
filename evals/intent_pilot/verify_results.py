"""Recheck raw receipts and describe citation failures without changing scores."""

import json
import math
import re
from pathlib import Path

import pilot

root = Path(__file__).resolve().parent
cases = {
    case["id"]: case for case in json.loads((root / "data/cases.json").read_text())
}
labels = json.loads((root / "data/answer-key.json").read_text())
protocol = pilot.digest(
    (root / "README.md").read_text()
    + (root / "pilot.py").read_text()
    + (root / "data/answer-key.json").read_text()
    + (root / "data/cases.json").read_text()
)
diagnostics = {"kind": "post-run diagnostics; original scores unchanged", "arms": {}}
verdicts = {}
for arm in ("raw", "bundle"):
    rows = []
    for case_id, case in cases.items():
        record = json.loads((root / "runs" / f"{case_id}-{arm}.json").read_text())
        assert record["protocol_sha256"] == protocol
        assert record["prompt_sha256"] == pilot.digest(pilot.packet(case, arm))
        provider = json.loads(record["stdout"])
        assert provider == record["provider"]
        assert not provider["is_error"] and provider["subtype"] == "success"
        assert set(provider["modelUsage"]) == {pilot.MODEL}
        assert provider["subagent_stats"]["spawned"] == 0
        assert provider["permission_denials"] == []
        cost = provider["total_cost_usd"]
        assert math.isfinite(cost) and cost >= 0
        response = provider["structured_output"]
        try:
            observation = pilot.validate(response, case, arm)
        except ValueError as error:
            observation = {"status": "invalid", "error": str(error)}
        assert observation == record["observation"]
        quote = response["intent_quote"]
        document = case["raw_intent" if arm == "raw" else "bundle_intent"]
        whitespace_match = bool(quote) and re.sub(r"\s+", " ", quote).strip() in re.sub(
            r"\s+", " ", document
        )
        code_quote = response["code_quote"]
        code = case["code"].get(response["code_path"], "")
        rows.append(
            {
                "id": case_id,
                "pair": labels[case_id]["pair"],
                "provisional_expected": labels[case_id]["expected"],
                "verdict": response["verdict"],
                "agrees_with_provisional_label": response["verdict"]
                == labels[case_id]["expected"],
                "strict_citations_valid": observation["status"] == "valid",
                "source_matches_after_whitespace_only_folding": whitespace_match,
                "code_quote_exact": len(code_quote.strip()) >= 12
                and code_quote in code,
                "provider_list_cost_usd": cost,
            }
        )
        verdicts.setdefault(case_id, {})[arm] = response["verdict"]
    diagnostics["arms"][arm] = {
        "evaluations": len(rows),
        "verdict_agreement_with_provisional_labels": sum(
            row["agrees_with_provisional_label"] for row in rows
        ),
        "known_defect_verdicts": sum(
            row["verdict"] == "mismatch"
            for row in rows
            if row["provisional_expected"] == "mismatch"
        ),
        "strict_citations_valid": sum(row["strict_citations_valid"] for row in rows),
        "whitespace_only_source_failures": sum(
            not row["strict_citations_valid"]
            and row["source_matches_after_whitespace_only_folding"]
            and row["code_quote_exact"]
            for row in rows
        ),
        "provider_list_cost_usd": sum(row["provider_list_cost_usd"] for row in rows),
        "rows": rows,
    }
diagnostics["arm_disagreements"] = [
    {"id": key, "pair": labels[key]["pair"], "verdicts": value}
    for key, value in verdicts.items()
    if value["raw"] != value["bundle"]
]
assert len(cases) == 10 and len(diagnostics["arms"]["raw"]["rows"]) == 10
pilot.write_json(root / "runs/diagnostics.json", diagnostics)
print(
    json.dumps(
        {
            arm: {key: value for key, value in row.items() if key != "rows"}
            for arm, row in diagnostics["arms"].items()
        },
        indent=2,
    )
)
