---
name: factory-plan
description: Write and approve the combined plan for a factory change - product, research, architecture, interface, slices.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory plan

Slug: $ARGUMENTS

S1 has one combined plan document and one gate. The human owns the Interface section: you draft it, they decide it.

## 1. Load the change

- Slug empty: use the only folder in `.factory/changes/` whose plan gate is not `approved`. Several or none: ask.
- Read `status.yaml`. Check out its `branch`. If the plan gate is `approved`, say so and point to `/factory-build <slug>`.
- If `plan.md` exists, resume it. When `sent_back` is set, its reason is the first open question: start there.

## 2. Gather facts

- Read every file in scope fully, and their tests.
- Read the Pond sessions listed in `pond_sessions`, from the end (latest decisions win). Search Pond again for decisions, rejected designs and incidents touching these modules.

Done when every claim you are about to write in Research has a `path:line` or a Pond session id behind it.

## 3. Draft `.factory/changes/<slug>/plan.md`

Track `small`: write Goal, Requirements, Slices and Coverage only. Track `standard` or `critical`: write every section.

```markdown
# Plan: <slug>

## Goal
<one sentence>

## Product
Problem: <in the user's words>
Success metric: <observable>
Non-goals: <list>

## Requirements
- FR-01: WHEN <trigger>, the system SHALL <response>
  Example (fit criterion): <concrete input> -> <concrete outcome>
Open questions: <list; empty before approval>

## Research
Facts only, each with `path:line` or a Pond session id. No proposals.

## Architecture
Fit with the existing code, data, flow, external services.
NFR-01: <user promise> -> <measurable budget>   (only when one applies)
Decisions: <decision> - <one-line reason>

## Interface
Per module:
- Signatures, in the repository's language
- Interface comment: what it promises, never how
- Depth: what it hides, in one line
Status: DRAFT | approved by human

## Slices
Tracer bullet first: the thinnest path that runs end to end. Then one capability per slice, each ending green.
### 01 <name>
Covers: FR-01
Tests first: <test file> :: <test name> - <what it asserts>
Allowed files: <paths, test files included>
Verify: <commands>

## Coverage
| ID | Slice | Test, or "human-verified" |
```

Rules:

- Every FR and NFR appears in Coverage. An unmapped ID blocks approval.
- Slices are vertical. A slice that only adds a layer (all models, then all handlers) is replaced by one that cuts through.
- Allowed files list every file a slice may touch, tests included.

## 4. Walk the human through it

1. Standard and critical: show the Interface section and ask the user to accept, edit or rewrite each module. Apply their changes verbatim. Their wording of a signature wins over yours.
2. Ask the open questions. Fold each answer into the doc and remove it from the list.
3. Repeat until Open questions is empty, every ID is in Coverage, and (standard and critical) Interface reads `approved by human`.

## 5. Record the gate

Only after the user explicitly approves the plan in chat:

1. Hash: `shasum -a 256 .factory/changes/<slug>/plan.md | cut -d' ' -f1`
2. In `status.yaml`: `gates.plan` = `{ state: approved, approved_by: <git config user.name>, approved_at: <ISO time>, doc_sha256: <hash> }`
3. Update `slices` from the Slices section, matching by id:
   - a slice already `done` stays as it is
   - the slice named in `sent_back` gets `state: rewind`; factory-build undoes its code before rebuilding it
   - any other slice that has a `base_commit` keeps its state unless the plan changed what it covers; then it also gets `state: rewind`
   - a new slice is appended as `{ id, name, state: pending, base_commit: null, test_commit: null, head_commit: null }`
4. Set `sent_back: null` and `notes_for_fresh_session: "Plan approved. Next: /factory-build <slug>."`
5. Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): plan <slug>`.

Editing `plan.md` after approval reverts the gate: build and review refuse to run until the plan is approved again.

## 6. Hand off

Tell the user: start a fresh session and run `/factory-build <slug>`.
