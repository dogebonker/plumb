# Improvement log

## Candidate 0001 — guided top-tier reconciliation

Implemented a fresh small core and a serial Claude CLI model boundary. Strong
model guidance supplies read/search operations, actual source selection, source
strength/applicability rules, dependency tracing and exact edit proposals.
Python owns scope, evidence, snapshot integrity and separate apply.

Claude Fable 5.1 inspected the imported encoder, diagnosed the code mismatch,
proposed a correction that repaired six actual behaviors, and then detected the
remaining stale knowledge. Eight real model calls completed. The knowledge
proposal was rejected by the host because its human question was empty.

The host demanded a question for a known mismatch even in propose mode after an
explicit operator choice. The model's empty question was appropriate there.
Fix the controller condition, preserving the question requirement for check
mode and for unresolved unknowns. Add a regression test; do not force the model
to invent another permission request.

## Candidate 0002 — controller correction

Reused calls 1–8 only after exact equality checks on each saved system prompt
and payload. Model outputs were unchanged. The corrected host accepted the
existing knowledge proposal, enforced the stale-source guard and applied the
single knowledge edit. Two additional real calls performed a fresh final check.
The final outcome was aligned and the six actual behavior checks passed.

Ten real model calls used so far. Calls 11–12 are reserved for the separately
frozen caller-guard/future-proposal holdout. No silent retry or model fallback.

## Measurement repair — inspect the actual workspace

Review caught a grader helper with a default argument bound to the seed path.
After creating an iteration copy, the no-mutation hash checks still read the
seed, although runtime behavior and apply checks used the actual iteration.
The original evaluator and binding are retained in iterations/0001 and 0002
and frozen-v1.json. Correct the helper to use the active workspace at call time.
No expected outcomes or behavior checks change; this strengthens the gate.

Re-evaluate all ten cached actor responses with exact input equality and live
workspace/apply/behavior checks. Inference is disabled in this verification;
any changed model input refuses reuse. Preserve the first failed attempt and
its error rather than rewriting history.

## Remaining interpretation limits

These are controlled operator decisions on an isolated Python replay, not a
Pond maintainer's approval or customer deployment. The public historical pilots
remain separate evidence. Live external connectors, production concurrency,
long-term bundle maintenance and adoption are not established by this gate.
