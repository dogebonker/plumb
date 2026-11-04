# Mission: make module-intent reconciliation work end to end

Requested 2026-11-03. Preserve the earlier frozen pilots. This run implements a
small usable command and improves its model guidance against a fixed evaluator.
It does not claim to solve arbitrary software verification or product adoption.

## Target workflow

1. Inspect one selected module's code, OKF knowledge and captured external
   decisions progressively, following relevant imports and callers.
2. Compare actual behavior with applicable agreed intent, keeping observed
   behavior, intended behavior, source conflicts and missing evidence distinct.
3. Return a concrete question with source/code citations and dependency evidence.
4. Given an explicit operator choice, propose the corresponding code or
   knowledge correction; never invent that choice.
5. Apply only a separately invoked, source-bound proposal in the selected
   workspace. Preserve changed user inputs and record the decision.
6. Recheck the result. Code corrections must satisfy actual small fixture
   behavior tests, not just change a status field or please an LLM judge.

## Agentic engineering approach

Use a top-tier model for source interpretation, code navigation, scoped
dependency reasoning, questions and proposed edits. Give it bounded read/search
operations and an explicit objective, evidence rubric and stop conditions.
Deterministic code owns file scope, quotation/proposal integrity, budgets and
application. No new framework, parser stack, GPU work, browser or repository
build is needed. Calls run serially through the existing Claude CLI.

## Evaluation and mutation boundary

Freeze development and held-out scenario definitions before actor calls. Keep
labels/behavior tests outside the workspace visible to the actor. Evaluate:
known defects, already-correct behavior, caller guards, conflicting active
sources, proposals versus current decisions, missing evidence, both correction
choices, stale-proposal rejection and repeat-apply behavior. Include a read-only
public Pond module replay. Controlled fixtures are explicitly synthetic; they
do not substitute for prospective customer validation.

Only change model guidance and implementation to address observed failures;
never weaken the evaluator to pass. Store each version, prompts, tool trace,
provider receipts, cost observations and decisions. Stop on the fixed behavior
gate passing, cancellation, or the declared spend/runtime ceiling. A ceiling
stop is incomplete, not success.

The user clarified that inference consumes the Claude subscription allowance and
approved **up to 12 top-tier Claude calls, then reassess**. That allocation is
now exhausted: no additional Claude calls without reassessment. The secondary
$3 reported list-cost guard is an accounting limit, not an invoice budget or a
percentage of the subscription quota.
The first bounded pass has a 30-minute execution ceiling after its evaluator
is ready. Planning/implementation time and native assistant usage are not
provider-bill measurements. Human curation/adoption remain unmeasured.
