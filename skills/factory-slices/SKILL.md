---
name: factory-slices
description: Slices gate of a factory change - vertical slices, tracer bullet first, each with tests, allowed files and verify commands.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory slices

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). This gate cuts the agreed design into slices an executor can build one at a time.

## 1. Load

Load the change as gates.md describes, for the `slices` gate. Read every earlier gate document that is not `skipped`.

## 2. Gather

- Read the files in scope fully, with their tests, to name real test files, allowed files and verify commands.
- Track small: read the sessions in `pond_sessions`, from the end, and `.factory/system/constraints.md`.

Done when every slice can name existing or new files by path.

## 3. Draft `04-slices.md`

Track `small` has no earlier documents: write Goal, Requirements and Standing constraints here too. Other tracks start at Slices.

```markdown
# Slices: <slug>

## Goal
<one sentence>

## Requirements
- FR-01: WHEN <trigger>, the system SHALL <response>
  Example: <concrete input> -> <concrete outcome>

## Standing constraints
- SYS-NFR-01: <how this change touches it>   (or: none)

## Slices
### 01 <name>
Milestone: 1
Covers: FR-01
Modules: <module paths this slice touches>
Tests first: <test file or feature file> :: <test name or scenario> - <what it asserts>
Scenarios: <track small, bdd: native modules only: each scenario in full, written from its FR example>
Allowed files: <paths, test files included>
Verify: <commands>

## Open questions
```

Rules:

- Slice 01 is the tracer bullet: the thinnest path that runs end to end. Each later slice adds one capability and ends green.
- Slice 01 is milestone 1 on its own. Later slices form milestones of two to four slices, each ending where the user can try something new; review and sign-off happen once per milestone (gates.md, Milestones and autopilot). A slice added after its milestone was signed off gets a new milestone number. Headless mode: every slice is its own milestone, so its Milestone line is its own number.
- Allowed files include every file that implements, fakes or constructs a type whose signature the slice adds or changes: test fakes, the composition root, other callers.
- Allowed files are exact paths, never wildcards like `web/**`, and every new file fits the Layout (gates.md, Layout). A file that fits no line is an open question.
- When an FSD Decision lists an install, the first slice that touches that frontend adds it: `package.json`, the lockfile and `steiger.config.js` are in its Allowed files.
- A slice touching more than two modules is a sign of a shallow interface: raise it as an open question.
- Slices are vertical. A slice that only adds a layer (all models, then all handlers) is replaced by one that cuts through.
- Every ID in Coverage of `03-interface.md` (track small: every FR and SYS ID above) is covered by a slice. When Coverage names a test, that slice writes it.

## 4. Walk the human through it

Show the slice list with what each one proves. Ask whether the tracer bullet is thin enough, whether any slice is a layer in disguise, and whether each milestone ends where the user can try something. Then ask the open questions.

Done when Open questions is empty.

## 5. Approve

Headless mode: make the updates below to `status.yaml` when you push the document for review, since the runner records only the gate, and name, in the comment that asks for approval, the slices that stay `done`: approving keeps their sign-offs, and the runner keeps no others. Otherwise approve the `slices` gate as gates.md describes; after its steps 1 and 2 and before its commit step, set `sent_back: null` and update `slices` in `status.yaml` from the document, matching by id:

- every slice's `milestone` comes from the document
- a slice already `done` stays as it is
- the slice named in `sent_back` gets `state: rewind`; factory-build undoes its code before rebuilding it
- any other slice that has a `base_commit` keeps its state unless this document changed what it covers; then it also gets `state: rewind`
- a new slice is appended as `{ id, name, milestone, state: pending, base_commit: null, test_commit: null, head_commit: null }`

Next skill: `/factory-build`, in a fresh session; from there the factory runs on autopilot (gates.md, Milestones and autopilot).
