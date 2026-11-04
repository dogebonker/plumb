"""Read, propose and separately apply module-intent corrections."""

import argparse
import json
import sys
from pathlib import Path

from .artifacts import write_json
from .core import apply, propose, reconcile
from .model import ClaudeModel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("workspace")
    check.add_argument(
        "--decision",
        help="Explicit operator source/intent decision; never inferred from documents",
    )
    proposal = sub.add_parser("propose")
    proposal.add_argument("report")
    proposal.add_argument("--choice", choices=["code", "knowledge"], required=True)
    commit = sub.add_parser("apply")
    commit.add_argument("proposal")
    for command in [check, proposal]:
        command.add_argument("--output", required=True)
        command.add_argument(
            "--receipts",
            required=True,
            help="Usage ledger shared across this experiment",
        )
        command.add_argument("--model", default="claude-fable-5-1")
        command.add_argument("--max-calls", type=int, default=12)
        command.add_argument("--max-tokens", type=int, default=150000)
        command.add_argument("--list-cost-limit", type=float, default=3)
        command.add_argument("--max-rounds", type=int, default=6)
    args = parser.parse_args()
    try:
        if args.command == "apply":
            result = apply(json.loads(Path(args.proposal).read_text()))
        else:
            report = (
                json.loads(Path(args.report).read_text())
                if args.command == "propose"
                else None
            )
            workspace = Path(
                report["workspace"] if report else args.workspace
            ).resolve()
            for name in (args.output, args.receipts):
                if Path(name).resolve().is_relative_to(workspace):
                    raise ValueError(
                        "Reports and receipts must be outside the reviewed workspace"
                    )
            model = ClaudeModel(
                args.receipts,
                model=args.model,
                max_calls=args.max_calls,
                max_tokens=args.max_tokens,
                list_cost_limit=args.list_cost_limit,
                tag=args.command,
            )
            if args.command == "check":
                result = reconcile(
                    workspace,
                    model,
                    decision=args.decision,
                    max_rounds=args.max_rounds,
                )
            else:
                result = propose(
                    report,
                    args.choice,
                    model,
                    max_rounds=args.max_rounds,
                )
            if args.command == "check":
                result["usage"] = model.usage()
                result["last_receipt"] = model.last_receipt
            write_json(args.output, result)
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in [
                        "outcome",
                        "question",
                        "status",
                        "path",
                        "proposal_id",
                        "usage",
                    ]
                    if key in result
                },
                indent=2,
            )
        )
        if args.command == "check":
            return (
                0
                if result["outcome"] == "aligned"
                else 3
                if result["outcome"] == "unknown"
                else 1
            )
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
