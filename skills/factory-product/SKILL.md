---
name: factory-product
description: Product gate of a factory change - problem, success metric, rules and examples, promises, constraints. No technology.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory product

Slug: $ARGUMENTS

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). This gate decides what the change does for its users, in their vocabulary: behavior, rules and outcomes. Technology enters at architecture.

## 1. Load

Load the change as gates.md describes, for the `product` gate.

## 2. Gather

- The task in `status.yaml`, and the sessions in `pond_sessions`, read from the end (latest decisions win).
- Read `.factory/system/constraints.md`.
- Search Pond for earlier requests, complaints and decisions about the same behavior.
- Read the code in scope only far enough to describe today's behavior in user terms.

Done when you can state today's behavior and the requested change in the user's words.

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
<ui true: screenshot paths from /factory-ui-ux mockups, or a sketch or ASCII when the user declined screenshots, following the design file's principles and primary-action table; "none" without UI>

## Rules and examples
### <business rule>
- FR-01: WHEN <trigger>, the system SHALL <response>
  (EARS: `The system SHALL`, `WHEN`, `WHILE <state>`, `WHERE <feature>`, `IF <unwanted> THEN`)
- Example: <concrete input> -> <concrete outcome>

## Promises
- NFR-01: <what the user can count on, in their words; numbers come in architecture>

## Constraints
- C-01: <budget, deadline, regulation, team, existing system>

## Standing constraints
- SYS-NFR-01: <how this change touches it>   (or: none)

## Non-goals

## Open questions
```

Work the Rules section as Example Mapping: every rule gets at least one requirement and one concrete example. A rule whose example you cannot write yet becomes an open question.

When `ui` is `true` in `status.yaml`, ask the user once whether this change needs mockup screenshots: worth it for a new screen or flow, rarely for a tweak to an existing one. A yes also agrees to the one-time Playwright download that capturing needs. Yes: once Rules and examples are drafted, follow the `mockups` mode of [../factory-ui-ux/SKILL.md](../factory-ui-ux/SKILL.md) for this slug. No: a sketch or ASCII under Mockups, with "screenshots declined".

## 4. Walk the human through it

Go rule by rule. For each: read back the rule and its examples, with the mockup screenshots that show them, ask for the missing or surprising case, and fold the answer in. A change to a rule that a mockup shows updates the mockup. Then ask the open questions one at a time.

Done when every rule has an example the user agreed to and Open questions is empty.

## 5. Approve

Approve the `product` gate as gates.md describes. Next skill: `/factory-architecture`.
