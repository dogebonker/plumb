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

- Read every file in scope fully, with its tests, callers and the data it touches.
- Read `.factory/system/` when it exists: earlier ADRs bind this change unless it supersedes them.
- Search Pond for decisions, rejected designs and incidents touching these modules.

Done when every claim in the Research section has a `path:line` or a Pond session id behind it.

## 3. Draft `02-architecture.md`

```markdown
# Architecture: <slug>

## Research
Facts only, each with `path:line` or a Pond session id. No proposals.

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
- ADR-NNNN <title> - <one line>

## Open questions
```

Every NFR and C from `01-product.md` appears under Budgets or Constraints.

## 4. ADRs

Write each decision as `.factory/system/adr/NNNN-<kebab-title>.md`, numbered after the highest existing one:

```markdown
# NNNN <title>

Status: accepted | supersedes NNNN
Context: <forces at play, with references>
Decision: <what was decided>
Consequences: <what gets easier, what gets harder>
```

A decision that changes an earlier ADR supersedes it: mark the old one `superseded by NNNN`.

## 5. Walk the human through it

Present the Decisions first, each with the main alternative it rejects. Then the Budgets, then the open questions. Fold every answer into the document and the ADRs.

Done when Open questions is empty and every NFR and C has a budget or the options it rules out.

## 6. Approve

Approve the `architecture` gate as gates.md describes. Next skill: `/factory-interface`.
