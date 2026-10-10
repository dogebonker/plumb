---
name: factory-product
description: Product gate of a factory change - problem, success metric, rules and examples, promises, constraints. No technology.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory product

Slug: $ARGUMENTS

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). This gate decides what the change does for its users. It names no technology: no frameworks, tables, endpoints or file names.

## 1. Load

Load the change as gates.md describes, for the `product` gate. If it is `skipped` (track small), point to `/factory-slices <slug>` and stop.

## 2. Gather

- The task in `status.yaml`, and the sessions in `pond_sessions`, read from the end (latest decisions win).
- Search Pond for earlier requests, complaints and decisions about the same behavior.
- Read the code in scope only far enough to describe today's behavior in user terms.

## 3. Draft `01-product.md`

```markdown
# Product: <slug>

## Problem
<in the user's words>

## Success metric
<observable after release>

## Announcement
<the short note you would publish when it ships, written before building>

## Mockups
<sketch, link or ASCII for any UI; "none" without UI>

## Rules and examples
### <business rule>
- FR-01: WHEN <trigger>, the system SHALL <response>
- Example: <concrete input> -> <concrete outcome>

## Promises
- NFR-01: <what the user can count on, in their words; numbers come in architecture>

## Constraints
- C-01: <budget, deadline, regulation, team, existing system>

## Non-goals

## Open questions
```

Work the Rules section as Example Mapping: every rule gets at least one requirement and one concrete example. A rule whose example you cannot write yet becomes an open question.

## 4. Walk the human through it

Go rule by rule. For each: read back the rule and its examples, ask for the missing or surprising case, and fold the answer in. Then ask the open questions one at a time.

Done when every rule has an example the user agreed to, Open questions is empty, and the document still names no technology.

## 5. Approve

Approve the `product` gate as gates.md describes. Next skill: `/factory-architecture`.
