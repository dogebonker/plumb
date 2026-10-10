---
name: factory-architecture
description: Architecture gate of a factory change - research facts, fit with the system, NFR budgets, constraints, ADRs.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory architecture

Slug: $ARGUMENTS

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). This gate decides how the change fits the existing system. Interfaces come next, in `/factory-interface`.

## 1. Load

Load the change as gates.md describes, for the `architecture` gate. Read `01-product.md`.

## 2. Research

Research runs behind a firewall: the agent that answers never sees the task, so its facts carry no bias toward a solution.

1. Write `<change>/research.md` with a `## Questions` list: how the code in scope works today, what calls it, what data it touches, what Pond records about it. Each question asks about the system as it is; the planned change stays out of the wording. Resuming: keep the questions already answered.
2. Start one fresh sub-agent. It receives the path of `research.md` and these instructions, nothing else from this conversation:

   > Answer every question in `<research.md path>` from the repository at `<repo root>` and, when its tools are available, from Pond. Write the answers under `## Answers`, numbered like the questions. Facts only, each with `path:line` or a Pond session id; write "not found" where the code and Pond are silent.

3. Gaps become new questions, answered the same way.
4. Read the files the answers point to, and `.factory/system/`: earlier ADRs bind this change unless it supersedes them, and the rows of the SYS IDs listed in `01-product.md` give their current fit criteria.
5. Load the profile's `architecture` lenses as [../factory-shared/packs.md](../factory-shared/packs.md) describes, and draft with their rules.

Done when every question is answered or marked "not found", and every claim in the Research section of `02-architecture.md` cites an answer in `research.md`.

## 3. Draft `02-architecture.md`

```markdown
# Architecture: <slug>

## Research
Facts from `research.md`, each with its `path:line` or Pond session id.

## Fit
Where the change lives in the existing system, and what it reuses.

## Contracts and data
External contracts, data shapes, storage, migrations.

## Flow
The path of one request or event through the system, step by step.

## Budgets
- NFR-01: <promise from product> -> <measurable budget, e.g. p95 under 200 ms on <path>>

## Constraints
- C-01: <constraint> -> rules out <options>

## Decisions
### <title>
Supersedes: <earlier ADR, or none>
Context: <forces at play, with references>
Decision: <what was decided>
Consequences: <what gets easier, what gets harder>

## Open questions
```

- Each decision is an ADR kept inside this document, so the gate hash covers it. Reconcile moves shipped ADRs into `.factory/system/adr/` after merge.
- When `.factory/system/` records no domain-model decision, add one, starting from `domain_model` in `lenses.yaml`: rich domain model or transaction scripts. `keep` means record the model the code already uses. The decision writes its outcome back to `lenses.yaml`.
- Track critical: Budgets holds at least one NFR budget.

## 4. Walk the human through it

Present the Decisions first, each with the main alternative it rejects. Then the Budgets, then the open questions. Fold every answer into the document.

Done when Open questions is empty and every NFR and C, its own and the listed SYS ones, has a budget or the options it rules out.

## 5. Approve

Approve the `architecture` gate as gates.md describes. Next skill: `/factory-interface`.
