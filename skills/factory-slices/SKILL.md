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

## 2. Draft `04-slices.md`

Track `small` has no earlier documents: write Goal and Requirements here too. Other tracks start at Slices.

```markdown
# Slices: <slug>

## Goal
<one sentence>

## Requirements
- FR-01: WHEN <trigger>, the system SHALL <response>
  Example: <concrete input> -> <concrete outcome>

## Slices
### 01 <name>
Covers: FR-01
Tests first: <test file> :: <test name> - <what it asserts>
Allowed files: <paths, test files included>
Verify: <commands>

## Open questions
```

Rules:

- Slice 01 is the tracer bullet: the thinnest path that runs end to end. Each later slice adds one capability and ends green.
- Slices are vertical. A slice that only adds a layer (all models, then all handlers) is replaced by one that cuts through.
- Every ID in Coverage of `03-interface.md` (track small: every FR above) is covered by a slice, with the test named there.
- Allowed files list every file a slice may touch, tests included.

## 3. Walk the human through it

Show the slice list with what each one proves. Ask whether the tracer bullet is thin enough and whether any slice is a layer in disguise. Then ask the open questions.

Done when every ID is covered and Open questions is empty.

## 4. Approve

Approve the `slices` gate as gates.md describes. Before its commit step, set `sent_back: null` and update `slices` in `status.yaml` from the document, matching by id:

- a slice already `done` stays as it is
- the slice named in `sent_back` gets `state: rewind`; factory-build undoes its code before rebuilding it
- any other slice that has a `base_commit` keeps its state unless this document changed what it covers; then it also gets `state: rewind`
- a new slice is appended as `{ id, name, state: pending, base_commit: null, test_commit: null, head_commit: null }`

Next skill: `/factory-build`, in a fresh session.
