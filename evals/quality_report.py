"""Separate observed quality dimensions and costs; existing PR report owns acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

import pr_benchmark
import pr_fixtures

METRICS = ("delivery", "supplied_tests", "blind_correctness", "pinned_policy_architecture",
           "acceptance_integrity", "shared_input_integrity", "semantic_history", "blind_rule_compliance")
DIMENSIONS = {"blind_correctness": "correctness", "semantic_history": "history", "blind_rule_compliance": "rule_compliance"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def immutable_status(record, paths):
    if not paths:
        return "unmeasured"
    receipt = record.get("acceptance_integrity", {})
    if set(paths) & set(receipt.get("changed", [])):
        return "fail"
    files = receipt.get("files", {})
    return "pass" if receipt.get("verified") is True and all(files.get(path) for path in paths) else "unmeasured"


def metrics(case, record, review):
    result = dict.fromkeys(METRICS, "unmeasured")
    status = record.get("status")
    if status == "complete":
        result["delivery"] = "pass"
    elif status in {"timeout", "interrupted", "question_limit", "question", "blocked", "execution_failed"}:
        result["delivery"] = "fail"
    test_status = record.get("tests", {}).get("status")
    if case.get("provide_acceptance"):
        if test_status == "pass":
            result["supplied_tests"] = "pass"
        elif test_status in {"fail", "candidate_error", "assertion_failure"}:
            result["supplied_tests"] = "fail"
        paths = pr_fixtures.acceptance_paths(case) + pr_fixtures.support_paths(case)
        result["acceptance_integrity"] = immutable_status(record, list(map(str, paths)))
    result["shared_input_integrity"] = immutable_status(record, [item["path"] for item in case.get("shared_inputs", [])])
    graph = record.get("archgraph", {})
    if (case.get("archgraph_rules") and case.get("archgraph_rules_sha256")
            and graph.get("rules_sha256") == case["archgraph_rules_sha256"]):
        result["pinned_policy_architecture"] = {"no_new_violations": "pass", "failed": "fail"}.get(graph.get("status"), "unmeasured")
    dimensions = review.get("dimensions")
    dimensions = dimensions if isinstance(dimensions, dict) else {}
    for metric, dimension in DIMENSIONS.items():
        row = dimensions.get(dimension, {})
        row = row if isinstance(row, dict) else {}
        if row.get("status") in {"pass", "fail"} and isinstance(row.get("evidence"), list) and row["evidence"]:
            result[metric] = row["status"]
    return result


def known(value):
    return value if pr_benchmark.numeric(value) else None


def costs(record):
    final = record.get("attempts", [])[-1].get("usage", {}) if record.get("attempts") else {}
    probe = record.get("probe_usage", {})
    return {"task": {"tokens": known(final.get("tokens")), "native_usd": known(final.get("cost_usd")),
                     "seconds": known(record.get("task_seconds"))},
            "probe": {"tokens": known(probe.get("tokens")), "native_usd": known(probe.get("cost_usd")),
                      "seconds": known(record.get("probe_seconds"))}}


def summarize(rows):
    result = {}
    for metric in METRICS:
        values = [row["metrics"].get(metric, "unmeasured") for row in rows]
        counts = {state: values.count(state) for state in ("pass", "fail", "unmeasured")}
        result[metric] = {**counts, "measured": counts["pass"] + counts["fail"], "total": len(values)}
    return result


def summarize_costs(rows):
    output = {}
    for field in ("tokens", "native_usd", "seconds"):
        values = [row.get(field) for row in rows]
        measured = [value for value in values if pr_benchmark.numeric(value)]
        output[field] = {"total": sum(measured) if values and len(measured) == len(values) else None,
                         "measured_sum": sum(measured) if measured else None,
                         "measured": len(measured), "observations": len(values)}
    return output


def frozen_reviews(root):
    if not (root / "verdicts.json").exists():
        return {}, {}
    key = load(root / "blind-key.json")
    frozen = load(root / "verdicts.json")
    # pr_benchmark.report already verifies packet, result and frozen-key hashes.
    reviews, identities = {}, {}
    for identity, binding in key.items():
        record = load(root / "trials" / binding["case"] / binding["arm"] / "result.json")
        if binding.get("source_sha256") != record.get("source_sha256"):
            raise ValueError("frozen source binding changed")
        review = frozen["verdicts"][identity]
        # Old/partial verdicts may omit dimensions: absence remains unmeasured.
        from blind_quality import evidence_line
        valid = {}
        dimensions = review.get("dimensions")
        dimensions = dimensions if isinstance(dimensions, dict) else {}
        for name, row in dimensions.items():
            if not isinstance(row, dict) or row.get("status") not in ("pass", "fail"):
                continue
            try:
                paths = [evidence_line(item, root / "blind" / identity) for item in row.get("evidence", [])]
                standing = any(path == "TASK.md" or path.startswith("base/") for path in paths)
                if (any(path.startswith("source/") for path in paths) and standing
                        and (name != "history" or any(path.startswith("base/") for path in paths))):
                    valid[name] = row
            except (ValueError, TypeError):
                continue
        reviews[binding["case"], binding["arm"]] = {"dimensions": valid}
        identities[identity] = (binding["case"], binding["arm"])
    return reviews, identities


def build_report(root, judges=None):
    root = Path(root).resolve()
    authority = pr_benchmark.report(root)  # Existing validation/scoring remains authoritative.
    config, manifest = load(root / "run.json"), load(root / "manifest.json")
    cases = manifest["cases"] if isinstance(manifest, dict) else manifest
    reviews, identities = frozen_reviews(root)
    receipts = {name: sha(root / name) for name in ("run.json", "manifest.json", "blind-key.json", "verdicts.json") if (root / name).exists()}
    rows = []
    for case in cases:
        for arm in pr_benchmark.ARMS:
            path = root / "trials" / case["id"] / arm / "result.json"
            record = load(path) if path.exists() else {}
            if path.exists():
                receipts[str(path.relative_to(root))] = sha(path)
            rows.append({"case": case["id"], "arm": arm, "delivery_status": record.get("status", "missing"),
                         "source_sha256": record.get("source_sha256"),
                         "metrics": metrics(case, record, reviews.get((case["id"], arm), {})), **costs(record)})
    overhead = []
    if judges:
        for index, path in enumerate(sorted(Path(judges).glob("*/result.json"))):
            record = load(path)
            native = record.get("evaluator_overhead", {})
            usage = native.get("usage", {})
            binding = identities.get(record.get("packet_id"))
            overhead.append({"case": binding[0] if binding else None, "arm": binding[1] if binding else None,
                             "status": record.get("status", "unknown"), "tokens": known(usage.get("tokens")),
                             "native_usd": known(usage.get("cost_usd")), "seconds": known(native.get("seconds"))})
            receipts[f"evaluator/{index}/result.json"] = sha(path)
    summaries = {}
    for arm in pr_benchmark.ARMS:
        selected = [row for row in rows if row["arm"] == arm]
        summaries[arm] = {"quality": summarize(selected), "task": summarize_costs([row["task"] for row in selected]),
                          "probe": summarize_costs([row["probe"] for row in selected])}
    return {"schema_version": 1, "reporter_sha256": sha(__file__), "model": config.get("model"),
            "input_receipts": receipts, "rows": rows, "arms": summaries, "evaluator_runs": overhead,
            "evaluator_overhead": summarize_costs(overhead), "acceptance_authority": "pr_benchmark.report",
            "authoritative_accepted": authority.get("accepted"),
            "limits": ["No composite quality score or new winner rule; original PR report owns acceptance.",
                       "Architecture means no new violations under pinned policy; it does not prove zero baseline debt.",
                       "Blind dimensions are static judgments; absent intent/history/evidence remains unmeasured.",
                       "Integrity verifies recorded immutable bytes; it does not establish semantic history quality.",
                       "Task usage uses the final cumulative native receipt, never summed resume snapshots.",
                       "Native USD is CLI-reported, not invoice cost. Missing values remain unknown.",
                       "Probe and evaluator costs are separate from actor task costs; evaluator retries count separately."]}


def cell(value):
    return str(value if value is not None else "unknown").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def markdown(report):
    lines = ["# Separate quality observations", "", "Cells show pass/fail/unmeasured; arm summaries use measured denominators.", "",
             "| Case | Arm | Delivery | Supplied tests | Blind correctness | Policy architecture | Acceptance integrity | Shared integrity | Semantic history | Blind rules |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for row in report["rows"]:
        lines.append("| " + " | ".join(map(cell, [row["case"], row["arm"], *[row["metrics"][name] for name in METRICS]])) + " |")
    lines += ["", "| Arm | Dimension | Pass / measured | Fail | Unmeasured / total |", "|---|---|---:|---:|---:|"]
    for arm, summary in report["arms"].items():
        for name, counts in summary["quality"].items():
            lines.append(f'| {arm} | {name} | {counts["pass"]}/{counts["measured"]} | {counts["fail"]} | {counts["unmeasured"]}/{counts["total"]} |')
    lines += ["", "| Case | Arm | Task tokens | Native USD | Task seconds | Probe tokens | Probe USD | Probe seconds |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in report["rows"]:
        values = [row["case"], row["arm"], *[row[group][field] for group in ("task", "probe") for field in ("tokens", "native_usd", "seconds")]]
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines += ["", "| Arm | Cost scope | Field | Total | Observed subtotal | Measured / observations |",
              "|---|---|---|---:|---:|---:|"]
    for arm, summary in report["arms"].items():
        for scope in ("task", "probe"):
            for field, aggregate in summary[scope].items():
                lines.append(f'| {arm} | {scope} | {field} | {cell(aggregate["total"])} | {cell(aggregate["measured_sum"])} | {aggregate["measured"]}/{aggregate["observations"]} |')
    lines += ["", "Evaluator overhead (separate native calls, including failed attempts):"]
    for field, receipt in report["evaluator_overhead"].items():
        lines.append(f'- {field}: total {cell(receipt["total"])}; observed subtotal {cell(receipt["measured_sum"])} from {receipt["measured"]}/{receipt["observations"]} runs.')
    return "\n".join([*lines, "", *["- " + limit for limit in report["limits"]], ""]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Existing study output")
    parser.add_argument("--judges", type=Path, help="Native blind judge receipt parent")
    args = parser.parse_args()
    report = build_report(args.out, args.judges)
    (args.out / "quality.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "quality.md").write_text(markdown(report))


if __name__ == "__main__":
    main()
