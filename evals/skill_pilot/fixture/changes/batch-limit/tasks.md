# Tasks and evidence

| Task | Requirement | Work | State | Verification |
| --- | --- | --- | --- | --- |
| T1 | R1 | Ingress batch-size validation | Complete | PASS: rejection test, sizes 6/9 as list/iterator, zero append calls |
| T2 | R2 | Preserve existing cases and all sizes 0–5 | Complete | PASS: original test plus new list/iterator coverage |
| T3 | R1/R2 | Update module knowledge from results/source | Complete | PASS: observed contracts, provenance and limits recorded in module entry |

`python3 -m unittest -v` evidence:
- Baseline: one existing test passes (`../../evidence/baseline.txt`).
- Before implementation: four rejection subcases fail with ValueError not raised;
  preservation passes (`../../evidence/red.txt`).
- After implementation: three tests pass (`../../evidence/green.txt`).

Direct execution verifies counts and stored values for 0–5, unchanged existing
store for rejected 6/9 (`../../evidence/runtime.json`). AST parse passes for both
Python files (`../../evidence/syntax.txt`). `git diff --check` passes; diff inspected
against R1/R2 and the only local caller. No project lint/typecheck configuration;
external integration checks not run because no integration target exists.

Resources: native reasoning and local Python/Git only; zero model CLI/provider
calls, no network, no builds. Host token accounting unavailable. No unresolved
batch-limit decision. Retention documents are a separate unresolved scenario.
