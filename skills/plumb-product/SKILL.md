---
name: plumb-product
description: Product gate of a Plumb change - problem, success metric, rules and examples, promises, constraints. No technology.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Plumb product

Usage: [per-skill accounting](../plumb-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../plumb-shared/gates.md](../plumb-shared/gates.md). This gate decides what the change does for its users, in their vocabulary: behavior, rules and outcomes. Technology enters at architecture.

Track standard, interactive mode: `/plumb-plan` drafts this document.

## 1. Load

Load the change as gates.md describes, for the `product` gate.

## 2. Gather

- The task in `status.yaml`, and the sessions in `pond_sessions`, read from the end (latest decisions win).
- Read `.plumb/system/constraints.md`.
- Search Pond for earlier requests, complaints and decisions about the same behavior.
- Read the code in scope only far enough to describe today's behavior in user terms.
- UI: reuse the optional feature examples captured at triage, following [../plumb-ui-ux/references.md](../plumb-ui-ux/references.md). Only when no references were supplied and the invitation was not already offered or declined, include its one optional 2–3-example invitation with the existing discovery questions; missing examples never become an Open question or block approval.

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
<ui true: screenshot paths from /plumb-ui-ux mockups and sketches for the screens it did not render, or a sketch or ASCII when the user declined screenshots, following the design file's principles and primary-action table; "none" without UI>

## Visual references (optional)
<link to visual-references.md and the selected feature patterns, or "none — proceed with DESIGN.md and the brief"; these do not replace the functional examples below>

## Rules and examples
### <business rule>
- FR-01: WHEN <trigger>, the system SHALL <response>
  Example: <concrete input> -> <concrete outcome>
  (EARS: `The system SHALL`, `WHEN`, `WHILE <state>`, `WHERE <feature>`, `IF <unwanted> THEN`)

## Glossary
| Term | Meaning | Never on screen |
| --- | --- | --- |
| <the users' word> | <one line, in their words> | <words the product must not show for it> |

## Promises
- NFR-01: <what the user can count on, in their words; numbers come in architecture>

## Constraints
- C-01: <budget, deadline, regulation, team, existing system>

## Standing constraints
- SYS-NFR-01: <how this change touches it>   (or: none)

## Non-goals

## Assumptions
- <what was assumed where the user did not answer> (rejected: <the alternative>)

## Open questions
```

For a capability that saves user data, make four decisions explicit in Promises and its examples, reusing applicable standing IDs: what “saved” guarantees (including reload and the supported failure boundary); what happens to the draft and success message when a write fails; how invalid existing data is preserved and recovered without silently replacing it with defaults; and how a stale writer or open editor avoids overwriting another writer’s changes. Record deliberate limits as user-agreed non-goals, not implied implementation defaults. Use `<kit>/nfr-catalog/stateful-data.md` for failure sequences. Revisit these decisions when the capability changes, even with an existing registry.

Work the Rules section as Example Mapping: every rule gets at least one requirement and one concrete example. A rule whose example you cannot write yet becomes an open question.

When `ui` is `true` in `status.yaml`, ask the user once whether this change needs mockup screenshots: worth it for a new screen or flow, rarely for a tweak to an existing one. A yes also agrees to the one-time Playwright download that capturing needs. Yes: once Rules and examples are drafted, follow the `mockups` mode of [../plumb-ui-ux/SKILL.md](../plumb-ui-ux/SKILL.md) for this slug. No: a sketch or ASCII under Mockups, with "screenshots declined".

## 4. Walk the human through it

Use gates.md **Explain questions and decisions**: recap the goal and relevant answers, then show each behavior choice with an existing mockup, access table or small flow sketch beside the question. Use everyday words and one user example, with a recommended outcome and drawback. Keep open questions one at a time. A corrected example does not automatically reopen unchanged architecture/security; apply Change impact.

Go rule by rule. For each: read back the rule and its examples, with the mockup screenshots that show them, ask for the missing or surprising case, and fold the answer in. A change to a rule that a mockup shows updates the mockup. Then ask the open questions one at a time.

Done when every rule has an example the user agreed to and Open questions is empty.

## 5. Approve

Approve the `product` gate as gates.md describes. Next skill: `/plumb-architecture`.
