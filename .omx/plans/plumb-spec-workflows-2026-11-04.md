# Plumb skill-first replan

Updated 2026-11-04. M1 is implemented following the user's request to build the
skill-first version. The remaining milestones are proposed; this document does
not grant authority for new provider spending or external actions.

## Requirements summary

Build a reusable spec-driven development skill around the existing coding agent.
Use per-service/module OKF knowledge, sources selected from the user's actual
project, and Kiro-style change specs when the change warrants them. OpenProse
may describe reusable workflows later; it is not a prerequisite.

## Starting evidence

- [CLI](../../plumb/__main__.py#L32) implements init/status/refresh/check/propose/apply.
- [Module initialization](../../plumb/workspace.py#L246) copies committed code and a
  source into a new workspace with draft knowledge. It is not automatic curation.
- [Freshness](../../plumb/workspace.py#L303) checks a selected local Git source.
  This does not establish live SaaS freshness or current upstream code.
- [Reconciliation](../../plumb/core.py#L256) asks a model to inspect bounded text.
- [Application](../../plumb/core.py#L347) changes one file after validation.
  Multi-file coding remains a host-agent operation.
- [Pilot](../../evals/intent_pilot/RESULTS.md) establishes no detection advantage
  for curated bundles. Human curation effort and adoption remain unmeasured.
- [OpenProse investigation](../../docs/research/openprose-for-plumb-2026-11-04.md)
  identifies an optional workflow language, with untested host compatibility.

## Implementation steps and acceptance criteria

### M1. One skill, one complete workflow — implemented

Delivered `skills/plumb/SKILL.md` with conditional references for substantial
changes and examples. `python3 -m plumb skill` prints it; `skill --path` locates it.
The old factory skills remain unchanged. Structural validation and independent
review pass. A [controlled forward test](../../evals/skill_pilot/RESULTS.md) checks
one code change and a source conflict. It does not complete M2 or M3.

The skill must tell the agent to:

1. Select relevant module bundles, source material, and affected code.
2. Distinguish current commitments from the requested delta and unresolved intent.
3. Use a brief plan for small changes; requirements/design/tasks for substantial ones.
4. Implement under existing host permissions, preserving caller/API/event contracts.
5. Run targeted behavior checks and examine the actual diff.
6. Update module knowledge only with supporting evidence and the user's governing decision.
7. Report remaining uncertainty and consumed observable resources.

Done when the instructions have an example for a direct edit, a behavioral change,
a conflicting source, and a source becoming stale. They must not claim unimplemented CLI
commands, hard host spend limits, or live SaaS adapters exist. A read-only reviewer
must be able to identify the expected stop or continuation for each example.
Rollback: stop invoking the skill; existing commands and project files still work.

### M2. One real change, end to end

Use the next actual requested change on Plumb itself, in an isolated worktree.
Use original requirements available before the change. Do not plant a defect or
write an oracle after examining the result. Record the skill version, selected
inputs, question resolutions, code diff, tests actually run, and knowledge diff.

Done when the requested behavior works, relevant preservation checks pass,
source records remain unchanged unless explicitly part of the request, and all
knowledge assertions can be traced to sources or actual observations. Missing
verification stays visible. Completion must not depend solely on agent self-report.
Rollback: preserve the evidence and leave the worktree unintegrated.

### M3. Reuse without rewriting the workflow

Run the same skill version on one real change in a second project. Change only
project inputs, scoped instructions, source selections, and verification commands.
Compare with the same agent given the same source material without the skill.
Track useful findings, wrong conclusions, repeated explanation, human maintenance
minutes, total completion time, and observable model usage. Small samples do not
establish general accuracy or a business case.

Done when the same workflow works on both projects without project-specific rules
being added to the shared skill. Keep it only if it provides recurring practical
value after maintenance cost. Split project policy from shared instructions if reuse fails.
Rollback: retain each project's ordinary documents and agent workflow.

### M4. Optional OpenProse trial

Only after workflow reuse creates a concrete need for composition, phase/session
control, or resume, translate one workflow to a pinned OpenProse package. Keep the
plain skill as the comparison. Do not adopt Reactor as an incidental dependency.

Done when the same inputs produce inspectable artifacts, serial implementation
and separate review contexts, a genuine decision checkpoint, and safe resume
without repeating application. Record actual usage and input/workflow revisions.
If any required capability is unavailable in the host, use the plain skill.
No real model run proceeds without available, explicit inference allocation.
Rollback: invoke the plain skill with the same documents.

### M5. Add only demonstrated missing machinery

A live source adapter, deterministic module selector, source-binding improvement,
or reusable verification command needs a repeated observed failure first. Choose
one source integration at a time. Verify that provider's actual revision and
concurrency behavior; retain draft output when safe writeback is unavailable.
No automatic external writes or subscriptions are part of this plan.

Done when a regression reproduces the failure before the addition and proves the
new observable behavior, with existing tests preserved. Rollback each addition
independently. Do not treat a bundle link as a proven dependency graph.

## Risks and mitigations

- Documentation maintenance costs more than it saves: measure total human work in M2/M3.
- A summary weakens a requirement: retain exact source wording and mark interpretation.
- A workflow hides uncertainty: preserve unknowns and require evidence for completion.
- The host bypasses a CLI guard: rely on actual permissions and isolated worktrees,
  not an assertion that skill text is a sandbox.
- Retry duplicates a side effect: inspect existing outputs and receipts before resume.
- Hidden model usage exceeds the allowance: distinguish host invocations from provider
  calls. Preserve the exhausted 12-call Claude allocation; do not infer new approval.

## Verification for this planning milestone

The [skill release record](../../evals/skill_pilot/RESULTS.md) separates structural
skill checks, controlled native behavior, real CLI tests, and artwork validation.
Live SaaS connectors, OpenProse, cross-project adoption, and additional Claude
inference remain outside this implementation.
