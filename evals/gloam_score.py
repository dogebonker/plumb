#!/usr/bin/env python3
"""Score Gloam discovery from a benchmark out dir: out/trials/<id>/decisions.json against the owner policy."""
import argparse
import json
from pathlib import Path

POLICY = Path(__file__).parent / "operators/gloam-owner.json"
DISCOVERY = ("L", "N", "V")


def score_trial(policy, decisions):
    """Discovery counts only questions asked before the first delivery; later ones stay listed and in the question count."""
    rules = policy["answers"]
    log = [{"question": d["question"], "rules": [r["id"] for r in rules if r["answer"] in d["answer"]],
            "after_delivery": bool(d.get("after_delivery"))} for d in decisions]
    discovery = [entry for entry in log if not entry["after_delivery"]]
    found = {rule for entry in discovery for rule in entry["rules"]}
    revealed = [r["id"] for r in rules if r["id"] in found and r["id"][0] in DISCOVERY and r["id"][1:3].isdigit()]
    return {"revealed": revealed, "revealed_count": len(revealed), "of": 16, "questions": len(log),
            "questions_before_delivery": len(discovery),
            "questions_per_rule": round(len(discovery) / len(revealed), 2) if revealed else None, "question_log": log}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path, help="benchmark out dir, or one trial dir")
    parser.add_argument("--policy", type=Path, default=POLICY)
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text())
    files = [args.out / "decisions.json"] if (args.out / "decisions.json").exists() else sorted(args.out.glob("trials/*/decisions.json"))
    print(json.dumps({f.parent.name: score_trial(policy, json.loads(f.read_text())) for f in files}, indent=2))


if __name__ == "__main__":
    main()
