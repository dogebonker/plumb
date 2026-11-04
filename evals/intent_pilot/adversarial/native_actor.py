"""Drive the existing core with recorded native-model responses, without Claude."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY))

from plumb import propose, reconcile


class PendingResponse(Exception):
    pass


def canonical(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def run(workspace, output, brief, report=None, choice=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    calls = []

    def native(system, payload):
        number = len(calls) + 1
        request = {
            "actor": "native Codex reasoning, not Claude CLI",
            "system": system,
            "payload": payload,
        }
        request["sha256"] = canonical(request)
        path = output / f"request-{number:03d}.json"
        if path.exists():
            if json.loads(path.read_text()) != request:
                raise ValueError("Native replay inputs changed")
        else:
            path.write_text(json.dumps(request, indent=2) + "\n")
        response = output / f"response-{number:03d}.json"
        if not response.exists():
            print(
                json.dumps(
                    {
                        "status": "native_response_required",
                        "request": str(path),
                        "response": str(response),
                    }
                )
            )
            raise PendingResponse()
        value = json.loads(response.read_text())
        calls.append(
            {
                "request": str(path),
                "response": str(response),
                "request_sha256": request["sha256"],
            }
        )
        return value

    try:
        if report is None:
            result = reconcile(Path(workspace).resolve(), native, decision=brief)
        else:
            captured = json.loads(Path(report).read_text())
            if (
                Path(captured["workspace"]).resolve() != Path(workspace).resolve()
                or captured["decision"] != brief
            ):
                raise ValueError(
                    "Proposal must use its resolved workspace and explicit operator decision"
                )
            result = propose(captured, choice, native)
    except PendingResponse:
        return
    name = "report.json" if report is None else "proposal.json"
    (output / name).write_text(json.dumps(result, indent=2) + "\n")
    (output / "transcript.json").write_text(
        json.dumps(
            {"actor": "native Codex", "claude_calls": 0, "calls": calls}, indent=2
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "outcome": result.get("outcome"),
                "question": result.get("question"),
                "artifact": str(output / name),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace")
    parser.add_argument("output")
    briefs = parser.add_mutually_exclusive_group(required=True)
    briefs.add_argument("--brief")
    briefs.add_argument("--brief-file")
    parser.add_argument("--report")
    parser.add_argument("--choice", choices=["code", "knowledge"])
    args = parser.parse_args()
    if bool(args.report) != bool(args.choice):
        parser.error("--report and --choice are used together")
    brief = Path(args.brief_file).read_text() if args.brief_file else args.brief
    run(args.workspace, args.output, brief, args.report, args.choice)
