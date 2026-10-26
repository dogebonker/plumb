"""P0: where the 2026-10-19 Factory arm spent its time, from the retained native transcripts.

    python3 p0_measure.py <report.md>    # prints a markdown table and summary lines

Planning is everything before the first build step; delivery is everything after.
"""
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / ".claude/projects"
PLANNING = {"triage", "product", "architecture", "security", "interface", "slices", "plan", "ui-ux"}
STEP = re.compile(r"step:\s*factory-([a-z-]+)\s*,\s*event:\s*step_start")
TRACK = re.compile(r"track\W{0,3}:\s*\W{0,2}(trivial|small|standard|critical)\b")
BUILD_AGENT = re.compile(r"executor|implementation|\bslice \d+\b|\bbuild\b|write slice packets", re.I)
GATE_AGENT = [(re.compile(p, re.I), s) for p, s in [
    (r"product gate", "product"), (r"architecture gate", "architecture"), (r"threat model", "security"),
    (r"interface gate", "interface"), (r"slices gate", "slices")]]
REVIEW_AGENT = re.compile(r"review|acceptance|confirmation", re.I)


def seconds(event):
    return datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).timestamp()


def timed(path):
    return [e for e in map(json.loads, path.open()) if e.get("type") in ("user", "assistant") and e.get("timestamp")]


def report_rows(report):
    rows = {}
    for line in Path(report).read_text().splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 10 and cells[2] == "factory":
            rows[cells[1]] = {"outcome": cells[3], "review": cells[6], "seconds": float(cells[9])}
    titles = dict(re.findall(r"^\| ([a-z0-9-]+) \| \[([^\]]+(?:\][^\]]*)?)\]\(", Path(report).read_text(), re.M))
    return rows, titles


def route(title, track):
    """D1: the critical check first (triage's critical track stands in for it), then the work type."""
    if track == "critical":
        return "critical"
    kind = re.match(r"\s*(?:\[[^\]]+\]\s*)?(feat|fix|refactor|chore|docs)?", title, re.I)[1]
    return {"fix": "bug", "refactor": "refactor"}.get((kind or "feat").lower(), "feature")


def measure(folder, row):
    # The scored attempt is the last task session; isolation probes start with "Isolation test only".
    tasks = [(timed(p), p) for p in Path(folder).glob("*.jsonl")]
    tasks = [(e, p) for e, p in tasks if not str(e[0]["message"]["content"]).startswith("Isolation test only")]
    events, main = max(tasks, key=lambda item: seconds(item[0][0]))
    attempts = len(tasks)
    start, end = seconds(events[0]), seconds(events[-1])
    helpers = [seconds(e) for p in (Path(folder) / main.stem / "subagents").glob("*.jsonl") for e in timed(p)]
    span_all = max([end, *helpers]) - start
    stage, track, build_at, turns, asks = "triage", None, None, 0, 0
    cuts = []  # (offset, stage)
    for e in events:
        at = seconds(e) - start
        content = (e.get("message") or {}).get("content")
        if e["type"] == "user" and isinstance(content, str):
            turns += 1
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            text = json.dumps(block["input"])
            track = track or (TRACK.search(text) or [None, None])[1]
            name, new = block["name"], None
            if name == "AskUserQuestion":
                asks += 1
            if name == "Skill":
                m = re.search(r"factory-([a-z-]+)", block["input"].get("skill", ""))
                new = m and m[1]
            elif name == "Agent":
                description = block["input"].get("description", "")
                new = next((s for p, s in GATE_AGENT if p.search(description)), None)
                if not new and BUILD_AGENT.search(description):
                    new = "build"
                elif not new and REVIEW_AGENT.search(description) and stage not in PLANNING:
                    new = "review"
            elif name in ("Edit", "Write", "MultiEdit"):
                path = block["input"].get("file_path", "")
                if "/work/" in path and ".software-factory/" not in path and stage in PLANNING and build_at is None:
                    new = "build"  # the conductor edits source itself (small or trivial work)
            for m in STEP.finditer(text):
                if m[1] != "triage":  # triage writes its marker when it commits, at its end
                    new = m[1]
            if new and new != stage:
                cuts.append((at, new))
                stage = new
                if new not in PLANNING and build_at is None:
                    build_at = at
    total = row["seconds"]
    edges = [(0.0, "triage"), *cuts, (total, None)]
    per_stage = {}
    for (a, s), (b, _) in zip(edges, edges[1:]):
        per_stage[s] = per_stage.get(s, 0.0) + max(0.0, min(b, total) - a)
    planning = sum(v for k, v in per_stage.items() if k in PLANNING)
    return {"main_span": end - start, "span_all": span_all, "track": track, "per_stage": per_stage,
            "planning": planning, "build_at": build_at, "turns": turns, "attempts": attempts, "asks": asks, "last_stage": stage}


def main():
    rows, titles = report_rows(sys.argv[1])
    out, sums = [], {"planning": 0.0, "total": 0.0}
    by_stage, timeout_stages = {}, {}
    for folder in sorted(glob.glob(str(ROOT / "*pr-benchmark-actors-azzaa964-*-factory-work"))):
        task = re.search(r"azzaa964-(.+)-factory-work", folder)[1]
        row = rows[task]
        m = measure(folder, row)
        span = m["main_span"] if row["outcome"] == "complete" else m["span_all"]
        match = span / row["seconds"]
        sums["planning"] += m["planning"]
        sums["total"] += row["seconds"]
        for k, v in m["per_stage"].items():
            by_stage[k] = by_stage.get(k, 0.0) + v
        if row["outcome"] == "timeout":
            timeout_stages[m["last_stage"]] = timeout_stages.get(m["last_stage"], 0) + 1
        stages = ", ".join(f"{k} {v:.0f}" for k, v in sorted(m["per_stage"].items(), key=lambda kv: -kv[1]))
        out.append(f"| {task} | {route(titles.get(task, ''), m['track'])} | {m['track']} | {row['outcome']} | {row['review']} "
                   f"| {row['seconds']:.0f} | {span:.0f} ({match:.0%}) | {m['planning']:.0f} ({m['planning'] / row['seconds']:.0%}) "
                   f"| {m['turns']} | {m['asks']} | {m['last_stage'] if row['outcome'] == 'timeout' else ''} | {stages} |")
    print("| Task | D1 route | Triage track | Outcome | Blind review | Report s | Transcript s (match) | Planning s (share) "
          "| Turns | AskUserQuestion | Stage at timeout | Seconds by stage |")
    print("| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    print("\n".join(out))
    print(f"\nPlanning share of all Factory time: {sums['planning'] / sums['total']:.1%} "
          f"({sums['planning']:.0f} of {sums['total']:.0f} s)")
    print("Seconds by stage: " + ", ".join(f"{k} {v:.0f} ({v / sums['total']:.0%})"
                                        for k, v in sorted(by_stage.items(), key=lambda kv: -kv[1])))
    print("Stage at timeout: " + ", ".join(f"{k} {v}" for k, v in sorted(timeout_stages.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
