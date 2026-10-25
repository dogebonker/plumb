"""Offline, additive native-trajectory diagnostics; never changes benchmark scoring."""
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

CASES = ("goldengate-1038", "limitless-4798", "bot-10", "limitless-4795")
ARTIFACTS = {"product": "product", "architecture": "architecture", "security": "security",
             "interface": "interface", "plan": "plan", "review": "review", "acceptance": "acceptance",
             "reconcile": "reconcile", "drift": "reconcile"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(path):
    return {"file": path.name, "sha256": digest(path), "bytes": path.stat().st_size}


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def timestamp(value):
    if numeric(value):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.timestamp() if parsed.tzinfo else None
        except ValueError:
            pass
    return None


def read_events(path):
    events, native_indices = [], []
    for line in path.read_text().splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            native_indices.append(len(events))
        events.append(value if isinstance(value, dict) else {"type": "unparsed"})
    receipts = [receipt(path)]
    timing = path.with_suffix(".timings.jsonl")
    if timing.exists():
        receipts.append(receipt(timing))
        for line in timing.read_text().splitlines():
            try:
                observation = json.loads(line)
                index = observation["event_index"]
                if type(index) is int and 0 <= index < len(native_indices) and timestamp(observation.get("timestamp")) is not None:
                    events[native_indices[index]]["_receipt_timestamp"] = observation["timestamp"]
            except (ValueError, KeyError, TypeError):
                continue
    return events, receipts


def stage_for(name, arguments):
    if name == "Skill":
        skill = arguments.get("skill", "")
        match = re.fullmatch(r"(?:factory:)?(factory-[a-z-]+)", skill) if isinstance(skill, str) else None
        if match:
            return match[1], "explicit Skill invocation"
    return None, None


def artifact_for(arguments):
    path = arguments.get("file_path", "")
    if isinstance(path, str) and ".software-factory" in Path(path).parts:
        stem = Path(path).stem
        numbered = {"01-product": "product", "02-architecture": "architecture",
                    "03-interface": "interface", "04-slices": "slices"}
        stage = numbered.get(stem, ARTIFACTS.get(stem))
        if stage:
            return "factory-" + stage
    return None


def profile_events(events):
    tools, stages, signatures = Counter(), Counter(), Counter()
    times, sources, evidence, seen = Counter(), set(), [], set()
    observations, hook_events = [], Counter()
    artifacts, mentions = [], []
    active, previous, global_previous, total, questions = {}, None, None, 0, 0
    unparsed = 0
    for index, event in enumerate(events):
        parent = event.get("parent_tool_use_id")
        context = "root" if parent is None else "child:" + hashlib.sha256(json.dumps(parent, sort_keys=True).encode()).hexdigest()[:16]
        native = timestamp(event.get("timestamp"))
        stamp = native if native is not None else timestamp(event.get("_receipt_timestamp"))
        if event.get("type") == "system" and str(event.get("subtype", "")).startswith("hook_"):
            hook_events[event["subtype"]] += 1
        if stamp is not None:
            observations.append({"event_index": index, "timestamp": stamp,
                                 "source": "native" if native is not None else "receipt", "context": context})
            sources.add("native" if native is not None else "receipt")
            if global_previous is not None and stamp >= global_previous:
                total += stamp - global_previous
            global_previous = max(global_previous, stamp) if global_previous is not None else stamp
            if context == "root":
                if previous is not None and stamp >= previous[0]:
                    times[previous[1]] += stamp - previous[0]
                if previous is None or stamp >= previous[0]:
                    previous = (stamp, active.get(context, "unknown"))
        if event.get("type") == "unparsed":
            unparsed += 1
            if previous is not None:
                previous = (previous[0], "unknown")
        content = event.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            identity = block.get("id")
            if identity and identity in seen:
                continue
            if identity:
                seen.add(identity)
            name = block.get("name", "unknown")
            arguments = block.get("input", {})
            arguments = arguments if isinstance(arguments, dict) else {}
            stage, reason = stage_for(name, arguments)
            if stage:
                active[context] = stage
                evidence.append({"event_index": index, "stage": stage, "basis": reason, "context": context})
                if context == "root":
                    if stamp is not None and (previous is None or stamp >= previous[0]):
                        previous = (stamp, stage)
                    elif previous is not None:
                        previous = (previous[0], "unknown")
            artifact = artifact_for(arguments)
            if artifact:
                artifacts.append({"event_index": index, "stage_hint": artifact, "tool": name, "context": context,
                                  "basis": "artifact access only; not an active-stage claim"})
            if name == "Bash" and isinstance(arguments.get("command"), str):
                for skill in sorted(set(re.findall(r"(factory-[a-z-]+)/SKILL\.md", arguments["command"]))):
                    mentions.append({"event_index": index, "skill": skill, "context": context,
                                     "basis": "literal skill-file mention; not invocation or execution proof"})
            tools[name] += 1
            stages[active.get(context, "unknown")] += 1
            fingerprint = hashlib.sha256(json.dumps(arguments, sort_keys=True).encode()).hexdigest()
            signatures[(name, fingerprint)] += 1
            if name == "AskUserQuestion":
                values = arguments.get("questions")
                questions += len(values) if isinstance(values, list) else 1
    return {"tool_calls": dict(tools), "stage_tool_calls": dict(stages), "stage_evidence": evidence,
            "stage_attribution": "last explicit Skill invocation per context; document access and file mentions are separate evidence",
            "artifact_accesses": artifacts, "skill_file_mentions": mentions,
            "question_items": questions, "unparsed_lines": unparsed,
            "repeated_inputs": [{"tool": tool, "input_sha256": key, "count": count}
                                for (tool, key), count in signatures.items() if count > 1],
            "observed_seconds": total if global_previous is not None else None,
            "stage_observed_seconds": dict(times) if previous is not None else None,
            "timestamp_sources": sorted(sources), "timestamp_observations": observations,
            "hook_events": dict(hook_events),
            "time_scope": "observed_seconds spans event observations; stage_observed_seconds uses root intervals by last explicit Skill; child stages never relabel root; not model time",
            "stage_token_cost_scope": "full per-stage token and USD attribution unknown; cumulative task receipts only"}


def usage_deltas(attempts, session):
    previous, rows = {"tokens": 0, "cost_usd": 0}, []
    for index, attempt in enumerate(attempts):
        current = attempt.get("usage", {})
        row = {"attempt": index, "basis": "native cumulative session receipts; missing/decreasing values remain unknown"}
        for field in ("tokens", "cost_usd"):
            value, prior = current.get(field), previous.get(field)
            row[field] = value - prior if session and numeric(value) and numeric(prior) and value >= prior else None
        previous = current
        rows.append(row)
    return rows


def delivery(record):
    status = record.get("status", "unknown")
    reasons = {"timeout": "execution guard elapsed; stage cause unknown",
               "interrupted": "execution interrupted; stage cause unknown",
               "question_limit": "configured attempt/question limit reached",
               "complete": "actor reported completion; quality scored separately",
               "question": "actor requested a decision", "blocked": "actor reported blocked"}
    return {"status": status, "reason": reasons.get(status, "see retained trial status; root cause unproven")}


def build_report(root, cases=CASES):
    root = Path(root)
    config_path = root / "run.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    rows, present = [], set()
    for path in sorted((root / "trials").glob("*/*/result.json")):
        case, arm = path.parent.parent.name, path.parent.name
        if case not in cases:
            continue
        present.add(case)
        record = json.loads(path.read_text())
        attempts, receipts = [], [receipt(path)]
        for index, (attempt, delta) in enumerate(zip(record.get("attempts", []), usage_deltas(record.get("attempts", []), record.get("session")))):
            trajectory = path.parent / f"turn-{index:03d}.jsonl"
            events, files = read_events(trajectory) if trajectory.exists() else ([], [])
            receipts.extend(files)
            profile = profile_events(events)
            profile.update(attempt=index, wall_seconds=attempt.get("seconds"), usage_delta=delta,
                           response_questions=int((attempt.get("response") or {}).get("state") == "question"),
                           trajectory_retained=trajectory.exists())
            attempts.append(profile)
        rows.append({"case": case, "arm": arm, "bindings": {
            "model": config.get("model"), "session": record.get("session"),
            "framework_sha256": config.get("framework_sha256"),
            "controller_sha256": config.get("controller_sha256"), "source_sha256": record.get("source_sha256"),
            "profiler_sha256": digest(Path(__file__)), "configured_profiler_sha256": config.get("diagnostics_sha256"),
            "factory_hooks": config.get("factory_hooks", False)},
            "hook_installation": record.get("hook_installation"),
            "delivery": delivery(record), "quality": {"tests": record.get("tests", {}).get("status", "unknown"),
            "architecture": record.get("archgraph", {}).get("status", "unknown"),
            "review": "unknown"}, "attempts": attempts, "receipts": receipts})
    return {"schema_version": 1, "run_receipt": receipt(config_path) if config_path.exists() else None,
            "requested_cases": list(cases), "missing_cases": sorted(set(cases) - present), "trials": rows,
            "limits": ["Diagnostic subset; no scoring or winner changes.",
                       "Stage attribution follows observed evidence, not inferred thinking.",
                       "Native cumulative receipts exclude separately recorded isolation probes.",
                       "No blind review verdict inferred from actor output; consult frozen verdict report.",
                       "Repeated inputs are evidence of repetition, not proof of wasted work."]}


def markdown(report):
    lines = ["# Diagnostic observations", "", "| Case | Arm | Delivery | Tests | Tool calls | Questions | Wall seconds |", "|---|---|---|---|---:|---:|---:|"]
    for row in report["trials"]:
        attempts = row["attempts"]
        wall = [a["wall_seconds"] for a in attempts]
        wall_total = sum(wall) if wall and all(numeric(v) for v in wall) else "unknown"
        lines.append(f'| {row["case"]} | {row["arm"]} | {row["delivery"]["status"]} | {row["quality"]["tests"]} | '
                     f'{sum(sum(a["tool_calls"].values()) for a in attempts)} | '
                     f'{sum(a["question_items"] + a["response_questions"] for a in attempts)} | {wall_total} |')
    lines += ["", "Questions count observed tool items and structured response requests separately; these may overlap.",
              "Missing trajectories do not establish zero tool use. Stage timing and usage deltas are in the JSON; unknown values remain unknown.",
              "", *["- " + limit for limit in report["limits"]]]
    return "\n".join(lines) + "\n"


def save_report(root, cases=CASES):
    report = build_report(root, cases)
    for name, body in (("diagnostics.json", json.dumps(report, indent=2) + "\n"),
                       ("diagnostics.md", markdown(report))):
        target = Path(root) / name
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(body)
        temporary.replace(target)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--case", action="append", help="Default: the four preselected diagnostic cases")
    args = parser.parse_args()
    save_report(args.out, args.case or CASES)


if __name__ == "__main__":
    main()
