---
name: factory-slices
description: Slices gate of a factory change - vertical slices, tracer bullet first, each with tests, allowed files and verify commands.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory slices

Usage: [per-skill accounting](../factory-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). This gate cuts the agreed design into slices an executor can build one at a time.

## 1. Load

Load the change as gates.md describes, for the `slices` gate. Read every earlier gate document that is not `skipped`.

## 2. Gather

- Read the files in scope fully, with their tests, to name real test files, allowed files and verify commands.
- Track small: read the sessions in `pond_sessions`, from the end, and `.software-factory/system/constraints.md`.

Done when every slice can name existing or new files by path.

## 3. Draft `04-slices.md`

Track `small` has no earlier documents: write Goal, Requirements, Standing constraints and Interface here too. Other tracks start at Development, then Slices. New interactive plans include the explicit Development mandate below before approval, except on track standard, where `/factory-plan` leaves the Development section out; preserve explicit manual/one-step preferences. Headless plans keep their existing approval route.

For a small UI change, link the optional `<change>/visual-references.md` in its brief, or record `none`; apply [../factory-ui-ux/references.md](../factory-ui-ux/references.md) without asking again. Functional examples and DESIGN.md requirements remain required.

```markdown
# Slices: <slug>

## Goal
<one sentence>

## Requirements
- FR-01: WHEN <trigger>, the system SHALL <response>
  Example: <concrete input> -> <concrete outcome>

## Standing constraints
- SYS-NFR-01: <how this change touches it>   (or: none)

## Interface
<track small only: each signature the change adds or changes, in the repository's language, with its interface comment (what it promises, never how); "none" when the change adds or changes no signature. These are frozen like the interface gate's.>

## Development
Mode: autonomous-local
Repairs: approved-slice-files

## Slices
### 01 <name>
Milestone: 1
Depends on: <earlier slice numbers this slice needs, or none>
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
- Track standard, interactive: every slice is `Milestone: 1`. Otherwise slice 01 is milestone 1 on its own. Later slices form milestones of two to four slices, each ending where the user can try something new; independent review and completion under approved execution scope happen once per milestone; final interactive sign-off happens at reconcile (gates.md, Milestones and autopilot). A slice added after its milestone was completed gets a new milestone number. Headless mode: every slice is its own milestone, so its Milestone line is its own number.
- `Depends on` names the earlier slices whose code or data this slice needs; slice 01 has `none`. On track standard, cut slices so independent ones build in parallel (factory-build, Fast lane): slice 01 creates the files every later slice would otherwise edit (route table, schema, shared styles, shared test helpers, dependency manifest and lockfile), with an entry and a stub for each later slice's own file, and each later slice gets its own source and test files. Two slices that still share a file depend one on the other. Verify commands use a free port and their own temporary data, so slices can run side by side.
- Allowed files include every file that implements, fakes or constructs a type whose signature the slice adds or changes: test fakes, the composition root, other callers.
- Allowed files are exact paths, never wildcards like `web/**`, and every new file fits the Layout (gates.md, Layout). A file that fits no line is an open question.
- When a Layout Decision picks a checker, the first slice that touches that root installs it and creates its config verbatim from the Decision: the manifest, the lockfile and the config are in its Allowed files (a global install, as `tools.yaml` marks it, is the user's to run). Its Verify runs the checker. Unless the check is `none`, `compiler` or `cargo`, its packet also asks the executor, once before the green commit, to plant a violation of a layer or sibling rule in a new temporary file under the root, report the checker's failing output, and delete the file; the planted file is never committed.
- A slice touching more than two modules is a sign of a shallow interface: raise it as an open question.
- Slices are vertical. A slice that only adds a layer (all models, then all handlers) is replaced by one that cuts through.
- Every ID in Coverage of `03-interface.md` (track small: every FR and SYS ID above) is covered by a slice. When Coverage names a test, that slice writes it.

## 4. Walk the human through it

Track small: before the approval summary, run the scripted-only [Covers/SYS conformance check](../factory-shared/adr.md#draft-conformance) on the pending `04-slices.md`. Unknown standing IDs become Open questions and appear in that summary. This validates ID references, not semantic intent; it adds no architecture document or model call. Other tracks reuse their current draft-conformance evidence.

Use gates.md **Explain questions and decisions**: connect each slice to something the user can try, recommend the smallest useful tracer bullet, and show a short dependency flow when ordering or parallel work is unclear. A retained compatible slice plan needs reverification of affected proof, not another approval question.

Show the slice list with what each one proves. Ask whether the tracer bullet is thin enough, whether any slice is a layer in disguise, and whether each milestone ends where the user can try something. Then ask the open questions.

Done when Open questions is empty.

## 5. Approve

Include in the initial interactive approval question: "Approving this plan authorizes bounded local implementation, executable-test corrections under unchanged promises, evidence-backed negative-test exemptions, review repairs, automatic intermediate completion after independent review and passing checks, and derived corrections for independently reproduced acceptance defects against unchanged promises, confined to original approved slice paths including planned tests. The Development mandate is included in the approved bytes; completed parents and approval documents stay unchanged. Changed product/architecture/interface promises, waivers, unrelated scope, destructive actions, credentials and publication remain separate decisions. Final acceptance and reconciliation return together for your sign-off." Respect an explicit manual milestone pause/sign-off preference. Record the actual approval reference, never an invented signature or state-only authority. Only new interactive plans with this approved mandate use gates.md Autonomous local corrections; existing missing-mandate plans retain their genuine approval path. A later correction record never supplies initial approval. Headless mode retains its existing PR approvals.

Headless mode: make the updates below to `status.yaml` when you push the document for review, since the runner records only the gate, and name, in the comment that asks for approval, the slices that stay `done`: approving keeps their sign-offs, and the runner keeps no others. Otherwise approve the `slices` gate as gates.md describes; after its steps 1 and 2 and before its commit step, retain the current `sent_back` slice/reason and update `slices` in `status.yaml` from the document, matching by id, then clear `sent_back` only after those updates:

- every slice's `milestone` comes from the document
- a slice already `done` stays as it is
- the slice named in `sent_back` gets `state: rewind`; factory-build inspects and repairs retained work under the corrected approval; it never cleans or restores the repository by default
- every other non-done slice applies gates.md Development proof inputs: changed approved document hashes or criteria/budgets/signatures/rules invalidate checks/review and refresh its packet even when Covers IDs are unchanged; retained-work slices become `building`, without resetting commits or rebuilding code automatically. Missing input manifests are stale, not reusable proof
- a new slice is appended as `{ id, name, milestone, state: pending, base_commit: null, test_commit: null, head_commit: null }`

On track standard in interactive mode, `/factory-plan` asks its own fast-lane approval sentence and runs this step's `status.yaml` slice update.

Continue directly to `/factory-build` under the approved scope (gates.md, Milestones and autopilot). A fresh session is optional, not another approval or hand-off.
