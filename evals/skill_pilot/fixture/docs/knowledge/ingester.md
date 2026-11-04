---
type: Software Module
---
# Ingester

## Scope and code paths
`ingester.py:accept(items, store)` ingests finite iterable items into an append-capable store.

## Verified contracts
Zero through five items are appended in order, preserve existing store entries,
and return their count. Requests over five raise ValueError identifying the
five-item limit before any store.append call. Verified for lists and iterators.

## Dependencies
Python iteration and caller-provided `store.append`. `test_ingester.py` is the only
local caller. All project Python files were inspected; no external services,
exports, configuration or persistent stores exist in this controlled fixture.

## Sources and governing request
Baseline observation: all items were appended; original tests covered 0, 1 and 5
without a request-size commitment. That implementation is superseded by the
current user-requested delta, preserved in `../../sources/selected-requirement.md`
(selected passage, version unknown, captured 2026-11-04) and
`../../changes/batch-limit/requirements.md` R1/R2. No independent approval is implied.

## Verification
`python3 -m unittest -v`: three tests pass; preservation covers 0–5 as lists and
iterators, rejection covers 6 and 9 as lists and iterators with zero storage calls.
Evidence: `../../evidence/baseline.txt`, `../../evidence/red.txt`,
`../../evidence/green.txt`, direct execution `../../evidence/runtime.json`.
Syntax: `../../evidence/syntax.txt`. No linter/typechecker configured.

## Unknowns and limits
Real storage adapters and external callers are unavailable; compatibility claims
are limited to this fixture. Finite requests are materialized, so memory grows
with request size. Existing partial-write behavior on storage errors is unchanged;
transaction semantics are outside this requested change.
