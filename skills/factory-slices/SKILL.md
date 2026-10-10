---
name: factory-slices
description: Slices gate of a factory change - vertical slices, tracer bullet first, each with tests, allowed files and verify commands.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory slices

Slug: $ARGUMENTS

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
Covers: FR-01
Modules: <module paths this slice touches>
Tests first: <test file> :: <test name> - <what it asserts>
Allowed files: <paths, test files included>
Verify: <commands>

## Open questions
```

Rules:

- Slice 01 is the tracer bullet: the thinnest path that runs end to end. Each later slice adds one capability and ends green.
- A slice touching more than two modules is a sign of a shallow interface: raise it as an open question.
- Slices are vertical. A slice that only adds a layer (all models, then all handlers) is replaced by one that cuts through.
- Every ID in Coverage of `03-interface.md` (track small: every FR and SYS ID above) is covered by a slice. When Coverage names a test, that slice writes it.

## 4. Walk the human through it

Show the slice list with what each one proves. Ask whether the tracer bullet is thin enough and whether any slice is a layer in disguise. Then ask the open questions.

Done when Open questions is empty.

## 5. Approve

Approve the `slices` gate as gates.md describes. After its steps 1 and 2 and before its commit step, set `sent_back: null` and update `slices` in `status.yaml` from the document, matching by id:

- a slice already `done` stays as it is
- the slice named in `sent_back` gets `state: rewind`; factory-build undoes its code before rebuilding it
- any other slice that has a `base_commit` keeps its state unless this document changed what it covers; then it also gets `state: rewind`
- a new slice is appended as `{ id, name, state: pending, base_commit: null, test_commit: null, head_commit: null }`

Next skill: `/factory-build`, in a fresh session.
