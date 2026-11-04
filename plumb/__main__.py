"""Use Plumb's spec-driven skill and module reconciliation tools."""

import argparse
import json
import sys
from pathlib import Path

from .artifacts import write_json
from .core import apply, propose, reconcile
from .model import ClaudeModel
from .workspace import initialize, is_connected, refresh, verify_binding
from .workspace import status as source_status


def _connection(workspace, repo, binding=None, *, require_binding=False):
    if not is_connected(workspace):
        if binding is not None or repo is not None:
            raise ValueError('No matching Git source connection; initialize or restore it first')
        return None, None
    if repo is None:
        raise ValueError('Supply --source-repo explicitly to verify this connected Git source')
    current = source_status(workspace, repo)
    if current['status'] != 'current':
        raise ValueError('Git source is ' + current['status'] + ': ' + current.get('error', 'refresh the capture and recheck'))
    if require_binding and binding is None:
        raise ValueError('Report/proposal has no connected-source binding; run a fresh connected check')
    expected = current['binding'] if binding is None else binding
    verify_binding(workspace, repo, expected)
    return expected, lambda value: verify_binding(workspace, repo, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    skill = sub.add_parser('skill', help='Print the reusable Plumb skill without making model calls')
    skill.add_argument('--path', action='store_true', help='Print its local entrypoint path instead')
    setup = sub.add_parser('init', help='Initialize one selected Git module and a draft OKF bundle')
    setup.add_argument('workspace')
    setup.add_argument('--repo', required=True)
    setup.add_argument('--module', required=True)
    setup.add_argument('--code', action='append', required=True, help='Tracked file or directory; repeat to include dependencies')
    setup.add_argument('--source', required=True, help='One tracked source document in the selected repository')
    setup.add_argument('--ref', default='HEAD')
    setup.add_argument('--section', help='Exact Markdown heading to import verbatim with its descendants')
    for name in ['status', 'refresh']:
        source_command = sub.add_parser(name)
        source_command.add_argument('workspace')
        source_command.add_argument('--source-repo', '--repo', dest='source_repo', required=True)
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
    commit.add_argument('--source-repo', '--repo', dest='source_repo')
    for command in [check, proposal]:
        command.add_argument('--source-repo', '--repo', dest='source_repo')
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
        if args.command == 'skill':
            entrypoint = Path(__file__).resolve().parent.parent / 'skills/plumb/SKILL.md'
            if args.path:
                if not entrypoint.is_file():
                    raise ValueError('Plumb skill is missing from this checkout')
                print(entrypoint)
            else:
                print(entrypoint.read_text(), end='')
            return 0
        if args.command == 'init':
            result = initialize(args.workspace, args.repo, args.module, args.code, args.source,
                                ref=args.ref, section=args.section)
            result['workspace'] = str(Path(args.workspace).resolve())
        elif args.command == 'status':
            result = source_status(args.workspace, args.source_repo)
        elif args.command == 'refresh':
            result = refresh(args.workspace, args.source_repo)
        elif args.command == "apply":
            proposal = json.loads(Path(args.proposal).read_text())
            _, verifier = _connection(Path(proposal['workspace']).resolve(), args.source_repo,
                                      proposal.get('source_binding'), require_binding=True)
            result = apply(proposal, verify_sources=verifier)
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
            binding, verifier = _connection(workspace, args.source_repo,
                                             report.get('source_binding') if report else None,
                                             require_binding=report is not None)
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
                    source_binding=binding,
                    verify_sources=verifier,
                )
            else:
                result = propose(
                    report,
                    args.choice,
                    model,
                    max_rounds=args.max_rounds,
                    verify_sources=verifier,
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
                        "scope",
                        "upstream_freshness",
                        "source_scope",
                        "workspace",
                        "source",
                        "latest",
                        "capture",
                        "knowledge_updated",
                        "review_required",
                        "error",
                    ]
                    if key in result
                },
                indent=2,
            )
        )
        if args.command in ('status', 'init'):
            return 0 if result['status'] == 'current' else 1 if result['status'] == 'changed' else 3
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
