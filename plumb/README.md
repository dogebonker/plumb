# Plumb command guide

“The decision changed. Did the code and module knowledge change with it?”

The reusable [Plumb skill](../skills/plumb/SKILL.md) runs through your current
coding agent. This guide covers the optional Python reconciliation tools.
`python3 -m plumb skill` prints the skill; add `--path` to locate its entrypoint.
Neither command makes a model request.

Plumb lets a strong model inspect a selected module's code, knowledge and source
captures, then produces a cited question when they disagree. The model can ask
for more text and follow dependencies. Python handles bounded file access,
evidence checks, usage limits and separately invoked application.

This is a local prototype, run from the repository with `python3 -m plumb`.
It uses the installed Claude CLI and its existing login. It has no new Python
dependencies. Claude subscription calls consume Claude allowance; reported
list-price equivalents are not confirmed charges or a percentage of that quota.

## A small selected workspace

```text
module-workspace/
  README.md
  code/                 # or src/
  knowledge/            # OKF module documents
  sources/              # captured decisions, tickets or other original material
```

Use one bounded workspace, not a repository containing dependencies/builds.
Check/propose/apply preserve source captures. A separate refresh command updates
the connected Git capture. The prototype also reads local exports; it does
not connect to Notion, Confluence, Jira or Linear yet. Source selection and
resolution are explicit operator input, not inferred authority from filenames.

## Initialize one Git module

Select committed code and one committed source document. Use a **new** destination:

```sh
python3 -m plumb init /path/to/module-workspace \
  --repo /path/to/checkout --module 'Orders' --code src/orders \
  --source docs/decisions.md --section 'Order cancellation'

python3 -m plumb status /path/to/module-workspace --source-repo /path/to/checkout
python3 -m plumb refresh /path/to/module-workspace --source-repo /path/to/checkout
```

Repeat `--code` to include known dependencies. `--section` must match exactly one
Markdown heading; its subtree is imported verbatim. Omit it to import the whole
document. Init copies committed Git blobs into `code/`, captures the full source
in `sources/decision.md`, and creates a draft OKF 0.2 root, module and contract in
`knowledge/`. It does not read dirty worktree contents or change the original
repository. A draft imports a stated requirement; it establishes no agreement
or verified behavior. Review its scope and intent before using it.

Status checks the configured local ref (`HEAD` by default). Source blob changes
are `changed`; unrelated commits with identical source bytes remain `current`.
Refresh updates only the managed capture, leaving code and knowledge untouched.
An update requires review and a fresh check. A repeated refresh changes nothing.
Missing/tampered sources fail rather than being replaced. Keep your notes in
knowledge; do not edit the managed capture manually.

Supply `--source-repo /path/to/checkout` on connected check/propose/apply commands.
The path is explicit each time; workspace metadata never authorizes an upstream
read. Checks run before and after inference, and before application. A changed
source or refreshed capture invalidates old reports/proposals. The Python core
also requires a source binding and verification callback for connected workspaces.

The [real Pond example](../examples/pond-claude-code/knowledge/index.md) imports
its Claude Code adapter and the committed adapter-integrity specification.
Its connection records this machine's checkout identity; initialize your own
workspace to use another checkout. [Milestone evidence](../evals/intent_pilot/module_source_milestone/RESULTS.md).

## Read, decide, propose, apply, recheck

Keep reports and receipts outside the reviewed workspace:

```sh
python3 -m plumb check /path/to/module-workspace \
  --decision 'sources/current.md is the selected current agreement; proposal.md is future work' \
  --output /path/to/review/report.json --receipts /path/to/review/receipts

python3 -m plumb propose /path/to/review/report.json --choice code \
  --output /path/to/review/proposal.json --receipts /path/to/review/receipts

python3 -m plumb apply /path/to/review/proposal.json
```

For a Git-connected workspace, add `--source-repo /path/to/checkout` to all three
commands above. The commands shown without it operate on unconnected captures.

Choose `code` to correct implementation to the selected intent, or `knowledge`
to keep implementation and update local knowledge under your explicit decision.
Review the proposed edit before invoking apply. Check and propose never edit
workspace files. Apply verifies all captured inputs, changes one file atomically,
and returns a receipt. Changed inputs invalidate the proposal. Repeating the
same apply after a successful application is idempotent.

Run check again after application. One correction may expose a second issue;
do not equate fixing code with reconciling all knowledge. Applying source-conflict
resolutions requires an explicit source/intent decision, not the model's guess.
An `unknown`, `sources_conflict`, or already-`aligned` check cannot start a
correction. Resolve the source/evidence question through explicit operator input
and run check again; only an actionable `code_wrong` or `spec_stale` result can
proceed. The proposed result must also remain actionable. Old diagnostic
proposal formats without these provenance fields must be regenerated.

Unreadable, oversized or symlinked selected inputs make the check `unknown`
before inference. Adding such an input after proposal also blocks apply. This
is a deliberate text-workspace boundary; skipped evidence cannot become a clean
result. Init rejects selected code paths hidden by the workspace scanner.
Reports and receipts say `scope: captured_workspace`. Unconnected inputs say
`upstream_freshness: not_checked`; connected inputs say `version_checked` with
`source_scope: local_git_ref`. This checks the explicitly selected local Git ref,
without fetching origin. Neither establishes remote/SaaS freshness. An aligned
result applies to the captured bytes under the operator's decision.

## Model and usage control

The default is `claude-fable-5-1` at high effort, with model-side tools disabled.
The host exposes read/search operations only over captured workspace text.
`--model`, `--max-calls`, `--max-tokens` and `--list-cost-limit` select bounded
inference. Share one receipts directory across the experiment: it counts prior
calls and preserves raw responses, prompts and reported usage. Unknown usage
stops further requests. There are no automatic retries or model fallbacks.

## Current limits

- Selected text workspaces: 256 files / 2 MiB total, 256 KiB per file.
- Source/code quotations establish provenance, not semantic truth.
- One file edit per proposal; use a fresh reconciliation for the next correction.
- Apply is for an isolated workspace. It rechecks inputs before atomic replace;
  it does not lock out an unrelated editor or Git ref movement racing that final
  operation. Source refresh and apply must run serially.
- Code is an initialization snapshot. Source refresh does not resync upstream
  code or propagate a correction back to the original repository.
- No automatic SaaS writes, repository builds, production actions or authority
  granted by a document claiming to be approved.

Run local boundary tests without model usage:

```sh
python3 -m unittest discover -s plumb -p 'test_*.py'
```
