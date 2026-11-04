# Plumb reconciliation prototype

“The decision changed. Did the code and module knowledge change with it?”

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
Source captures remain immutable. The prototype reads local exports; it does
not connect to Notion, Confluence, Jira or Linear yet. Source selection and
resolution are explicit operator input, not inferred authority from filenames.

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

Choose `code` to correct implementation to the selected intent, or `knowledge`
to keep implementation and update local knowledge under your explicit decision.
Review the proposed edit before invoking apply. Check and propose never edit
workspace files. Apply verifies all captured inputs, changes one file atomically,
and returns a receipt. Changed inputs invalidate the proposal. Repeating the
same apply after a successful application is idempotent.

Run check again after application. One correction may expose a second issue;
do not equate fixing code with reconciling all knowledge. Applying source-conflict
resolutions requires an explicit source/intent decision, not the model's guess.

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
  it does not lock out an unrelated editor racing that final operation.
- No automatic SaaS writes, repository builds, production actions or authority
  granted by a document claiming to be approved.

Run local boundary tests without model usage:

```sh
python3 -m unittest plumb.test_core plumb.test_model
```
