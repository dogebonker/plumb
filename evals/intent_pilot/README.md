# Module-intent pilot

This is an initial, retrospective feasibility test, not a product release or a
customer-adoption study. It runs serially, without builds, indexing, browser
automation, tools or MCP access for the model.

## Frozen comparison

- Module: Pond's Claude Code transcript adapter, read from committed Git blobs.
- Evidence: five public corrective commits and their original explanations.
- Cases: the before/after implementation around each correction: ten historical
  snapshots, **five correlated pairs**, not ten independent defects or PRs.
- Task: audit the named behavior in the module snapshot. This is a consistency
  audit, not a changed-lines-only PR review. The original corrective diff is
  retained as grading evidence but is never sent to the reviewer.
- Baseline: original source explanation plus production code.
- Bundle: a curated OKF concept derived from that same explanation plus exactly
  the same production code. Both retain the same upstream source identity.
- Model: `claude-sonnet-5-5`, low effort, independent session per case/arm.
- Limits: one process/request at a time, 90 seconds per request, $0.25 provider
  list-cost ceiling per invocation and $3 cumulative admission budget.
- Ordering: fixed shuffled case order; alternate which arm runs first.
- No prompt or bundle tuning after examining model results.

The source explanations reveal the known bugs and corrections. Curated concepts
are written with that knowledge. This is deliberately an easy, **retrospective**
test and cannot establish prospective accuracy, novel discovery or superiority.
The five negative snapshots are known-defect implementations; the five controls
are expected to satisfy only the named behavior, not every requirement of Pond.
Labels are analyst judgments grounded in upstream changes, not maintainer labels
or newly executed Rust regressions.

## Scoring

Report target-behavior detection, false alarms on matched fixed controls,
uncertain/failed requests and mechanically valid source/code quotations. Keep
semantic decisions and quote validity separate. A missing or invalid response
is an unsuccessful review, never a clean result. Paired results show disagreement
between arms. Provider-reported token classes, list-cost and observed subprocess
wall time are retained separately; list-cost is not an invoice charge.

Curation effort is part of the product question. Human curation/review minutes
remain null until a maintainer actually supplies them. Agent preparation wall
time is not substituted for human effort. This run cannot prove that maintaining
bundles saves time or that anybody will adopt them.

## Commands

```sh
python3 evals/intent_pilot/pilot.py prepare --repo /path/to/pond
python3 -m unittest discover -s evals/intent_pilot -p 'test_*.py'
python3 evals/intent_pilot/pilot.py run --budget-usd 3
python3 evals/intent_pilot/pilot.py score
```

Preparation writes public excerpts, the OKF bundle, a source manifest and a
separate answer key under `data/`. Execution retains exact prompts, raw provider
JSON and validated observations under `runs/`. It never changes the source repo.
Re-running `run` reuses only receipts whose prompt and protocol hashes match;
incomplete/failed receipts remain visible instead of being retried automatically.

Next evidence gate: maintainer review of the questions, then prospective changes
using documents that existed before those changes. External-source connectors
and automatic code/doc updates are outside this experiment.
