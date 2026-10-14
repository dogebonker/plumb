---
name: factory-build
description: Build the slices of a factory change's next milestone - packet, fresh executor, red then green, mechanical checks per slice - then go on to its review.
disable-model-invocation: true
argument-hint: "[slug] [--one-step]"
---

# Factory build

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

The conductor prepares the packet, dispatches one implementation executor per slice, and verifies its commits and mechanical evidence. It follows these steps directly; no additional build step agent is required. Resume the same executor for local repairs while its context remains usable.

Slice states: `pending` -> `building` -> `red` -> `green` -> `done` (review sets `done`). Legacy `rewind` requests mean inspect and repair the retained work, not restore or clean the repository. Interactive mode continues through build and review under the real approved execution scope ([../factory-shared/gates.md](../factory-shared/gates.md), Milestones and autopilot); `--one-step` stops after one slice.

## 1. Check the gate

- Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes: the work is a slice not `done`. Legacy detached RED state must be recovered to the recorded deliverable branch without discarding dirty work; new RED verification never detaches that checkout.
- For any derived correction, run gates.md's `repair-check --checkpoint edit` on load/resume and immediately before edits/dispatch; an undeclared active ID on a mandated plan requires valid repair metadata even without a repair flag. Preserve the fixed start baseline and stop on invalid scope/provenance.
- Before selecting the milestone or skipping any `green` slice, apply gates.md **Development proof inputs** to every non-done slice. Refresh stale packets and invalidate old receipts while retaining work/commits; changed promises require fresh verification, not automatic code replacement.
- The milestone in progress is the one holding the first slice not `done`. When every one of its slices that is not `done` is `green`, go to step 7. Otherwise take its first slice that is neither `done` nor `green` and resume by its state:
  - `pending`: step 2, unless the slice's `packet.md` exists and its Written from line and complete Inputs manifest match current approved gates and effective inputs; then step 3 with that packet.
  - `rewind`: inspect the send-back reason and retained commits/edits. Once the corrected gate is genuinely approved, update the packet and repair locally; preserve previous tests, commits and proof.
  - `building`: inspect the executor's native task state, commits and pending edits. Resume that executor with the observed failure or interruption. If both RED and GREEN commits exist, continue at step 4. Use a fresh executor only if the old one is unavailable or its context cannot safely continue, keeping all existing work.
  - `red`: step 5.
- Inspect `git status --short` before edits. Unrelated dirty, staged or untracked source blocks unattended execution; preserve it and report the exact paths. Do not commit someone else's work or discard it to get a clean tree. Slice-owned interrupted edits may be continued with their provenance recorded.

## 2. Write the packet

Write `.software-factory/changes/<slug>/slices/NN/packet.md` from [packet.md](packet.md), replacing any older packet for this slice, with Written from and the Inputs manifest recording current approved gate hashes and all referenced proof inputs (gates.md, Development proof inputs). Retain the previous packet as historical evidence instead of overwriting its proof context. Before ordinary generation, use the candidate packet already staged with a correction and validate its record/packet together via `repair-check --checkpoint edit`; when refreshing that control-only packet, derive Goal from its independently reproduced unchanged criterion/defect, Covers and Frozen contract from original approved documents, and exact Allowed files from `repair.json`. Copy applicable approved commands and parent planned tests restricted to those paths; record the repair record/input snapshot and original completed parents. Do not search frozen `04-slices.md` for a nonexistent correction heading. Retain its own base/test/head receipts; parents and original approved bytes stay untouched. No new-test/typecheck deviation widens a correction; use the genuine slice approval path instead. The remaining ordinary packet rules apply where relevant.

For an original slice, copy, never paraphrase:

- the slice's heading from `04-slices.md` as Goal
- the covered IDs with their fit criteria: each FR's Example line from `01-product.md` (track small: `04-slices.md`), each SYS ID's fit criterion from `.software-factory/system/constraints.md`
- the NFR budgets it covers and the Research facts it needs, with their `path:line`, from `02-architecture.md`
- the frozen signatures, interface comments and depth statements it touches, from `03-interface.md` (track small: the Interface section of `04-slices.md`), and the Stubs section of `<kit>/adapters/<language>.md` for the module's language
- its tests, allowed files and verify commands, from `04-slices.md`; in a module with `bdd: native`, its scenarios verbatim from the Test plan of `03-interface.md` (track small: from `04-slices.md`), and the existing step definitions found with the adapter's BDD step search (`path:line` and step text)
- under Layout, the lines that admit each Allowed file (gates.md, Layout), with what lives there and what may not; a file admitted only because its folder already existed is listed as `existing`
- UI slices: under Visual direction, the relevant approved DESIGN.md brand/component/state rules, branded mockup paths and selected feature-reference notes/artifacts ([../factory-ui-ux/references.md](../factory-ui-ux/references.md)); carry only this slice's applicable examples, or `none`, without another question or unapproved scope expansion
- under Rules in scope, the active playbook entries whose scope matches the Allowed files, copied (gates.md, Load a change, step 7); the Principles of the principle layers (gates.md, Paths), merged and copied; then the resolved pack paths (packs.md, Load) of the profile's `packet` lenses (size `nano`) and of the module's language pack index and rules, each that passes the pin check in [../factory-shared/packs.md](../factory-shared/packs.md), and the simplification ladder from that file, copied

Done when an engineer who has never seen the gate documents could build the slice from the packet alone.

## 3. Dispatch the executor

For a derived correction, rerun `repair-check --checkpoint edit` immediately before dispatch and pass its exact record paths, immutable inputs and failure evidence with the packet. Routine repair batches go to this same executor, not the conductor or reviewers.

For a retained-work repair, first record the original owned span/head and `Repair start: <current HEAD>` in the packet without changing the original base/test history. The executor reports each exact correction commit span. Later slices already present at repair start are preserved; their commits are not attributed to this slice.

Set the slice to `building`, setting `base_commit` to HEAD only when unset; retain the original base on continuation. Start one implementation executor in the foreground (resume the existing one for repairs). It receives the packet path and these instructions, nothing else from this conversation:

> Read `<packet path>` and every allowed file it lists. Build the slice with recorded RED and GREEN commits, retaining any supplementary correction commits. Stage files by path, only files in Allowed files.
>
> 1. **Red.** Write the tests under "Tests first", each asserting the outcome its line names, not only that the call returns; in a BDD module, the feature file and every step definition its scenarios need. Add each new frozen signature as a stub in the packet's stub form, so the code compiles. A changed signature keeps its old behavior behind the new signature, and existing tests are updated to the new signature and still pass. Run the tests: every new test fails, every other test passes except those in `<baseline_failures>`. List any new test that passes against the stub (a negative case, for example) in your report rather than changing it. Commit as `test(<slug>): slice NN red`.
> 2. **Green.** Implement until every Verify command passes. Tests retain their semantic expectations and every frozen signature stays exactly as written. A wrong executable test under an unambiguous approved promise may be corrected with a deviation, retained original history and supplementary isolated RED proof; never weaken coverage. Commit as `feat(<slug>): slice NN`.
>
> Stop and report, with the reason, when: a frozen signature cannot work as written, a file outside Allowed files must change, the approved promise is ambiguous, a pre-commit hook rejects the red commit, or a commit fails to sign. Never commit unsigned.
>
> Wait for every child you started and report its outcome. The conductor observes native terminal results; do not infer task identities or report conductor-owned green status as your own completion. A still-running executor is not a finished build. Report: both commit shas, the tail of the failing run from step 1, the tail of the passing run from step 2, and anything you stopped on.

When the executor stops, append an `executor_stop` event with the reason. Diagnose repairable failures and resume the same executor with the evidence. Retry counts are diagnostics, not an automatic permission question. Repeated identical failures require a bounded root-cause diagnosis; stop with a precise blocker only when no authorized recovery remains.

- **Frozen signature or ambiguous requirement:** send back to the appropriate gate.
- **Wrong executable test, unchanged promise:** correct locally; log the reason, old/new test commits and exact paths in `deviations`, retain both versions, and obtain supplementary RED and GREEN proof as step 4 describes. Independent review must confirm the unchanged semantic expectation.
- **File outside the list:** a derived correction cannot expand its repair record or packet through deviations, typecheck callers/fakes or new regression files; follow the genuine scope approval path. For ordinary slices, when the adapter's Typecheck proves a packet signature requires a caller/fake/composition-root change, log `{ slice, file, reason: "typecheck: <error>" }`, append that exact path to the packet and continue. A new regression test beside the slice tests follows review's deviation rule. Otherwise hold the scope decision for the user; a deviation alone never authorizes an unrelated edit.
- **Pre-commit hook or signing:** repair local setup within existing authority. Bypassing a hook, changing Git/global configuration or unlocking credentials needs the actual user's authority; never silently commit unsigned.
- **New negative test passes against the stub:** retain it, record its name in `red_exempt` with the actual output and unchanged fit criterion, and require independent review. Do not rewrite a valid assertion merely to force RED.

**Send back** follows gates.md, which picks the target gate from the reason.

## 4. Prove red

1. Record `test_commit`: the sha of the `test(<slug>): slice NN red` commit. The test files are those listed in the packet's Tests first.
2. When the module's test uses a fixed browser-check capability, require `red_test_command` in the status/packet. First write its fixed request with `python3 <kit>/runtime.py browser-red-request --repo <absolute repo> --commit <test_commit full 40-hex SHA> --checkpoint <slug>-NN-red-<attempt>`; the checkpoint token uses only letters, digits, underscore or hyphen and at most 64 characters. This writes `.software-factory/browser-red.json` with exactly `{"commit": "<SHA>", "checkpoint": "<token>"}` (no commands or paths). Then invoke the prepared `red_test_command` directly as one bare command, once: it runs every cloned `test*.cjs` including existing tests, returning actual exit, bounded summary and raw log path. Do not pass the live browser wrapper to `runtime.py red`: it ignores cwd and can test GREEN instead. A missing isolated browser capability is a bounded verification blocker, not RED proof.
3. Otherwise keep the deliverable branch and pending edits in place. For each `test_file_command` (BDD: the adapter's feature run) and then `test_command`, invoke `python3 <kit>/runtime.py red --repo <absolute repo> --commit <test_commit> --checkpoint <absolute change>/slices/NN/red-check-<number>.json --timeout <test budget seconds> -- <command and arguments>`. The helper creates an ignored temporary local clone under the repository's `.software-factory/scratch/` (so standard Node dependency lookup reaches the existing root `node_modules`) with no push remote, checks out RED there and records the live GREEN head/branch plus the command and exit code; output is in the adjacent `.log`. No worktree permission is needed. Commands run with that verification clone as cwd; use its relative paths, never absolute source paths into the live checkout.
4. For corrected or added regression tests, use the generic isolated helper with `--commit <pre-implementation source commit> --tests-from <corrected test commit> --test-file <exact test path>` (repeat `--test-file` for each file). Record both commits, original/corrected test hashes, command and assertion failures; run those exact corrected tests against the current implementation for GREEN. Preserve original RED evidence. The fixed browser request remains exactly two fields and cannot overlay tests: use a valid recorded commit containing the corrected tests and pre-implementation source through its existing capability, or report a bounded verification blocker. Never substitute a live browser wrapper.
5. Read the recorded log and compare each failure with Tests first; a nonzero command alone is not RED proof. For a fixed browser capability, copy the returned checkpoint JSON and its raw log into this slice's directory, record the copied log path alongside the original checkpoint, and return these exact artifact paths. The helper ignores its ephemeral request, scratch and runtime evidence through Git's local exclude file; the copied slice evidence ships with the committed change. Timeout, setup failure or interruption is inconclusive, never an assertion failure. The generic helper removes only its temporary verification clone; the deliverable Git/dirty/untracked state is retained. Rerun from the same test commit when interrupted.

Red means: it builds; every new test fails, on an assertion or an error raised through a stub, except those in `red_exempt` (an undefined or pending step is not red: the red commit defines every step); and every other test passes except those in `baseline_failures`.

- Red: set the slice to `red`.
- Not red: append a `red_retry` event, classify assertion/test/setup/contract failure, and continue the same executor with a bounded local repair and supplementary proof. Preserve work and history. Only an unresolved requirement, authority or verification blocker stops progress.

## 5. Prove green

At the branch head, run every Verify command and `test_command`. Green means all pass, apart from tests in `baseline_failures`. On failure, append a `green_retry` event, diagnose and continue the executor with the output; use a fresh executor only when necessary. Preserve work and stop only on an actual blocker. Record `head_commit`; the slice stays `red` until step 6 passes.

## 6. Check the slice

Run Phase 1 of [../factory-review/SKILL.md](../factory-review/SKILL.md) (checks 1 to 5) on this slice alone: its recorded original owned span, exact repair spans, `test_commit` and refreshed packet. Check each owned span separately; do not use original base through current HEAD as its edit range when that includes later slices. Contract and GREEN checks still inspect current HEAD. Write `slices/NN/checks.md`:

```markdown
# Checks: slice NN, <name>

Range: <base_commit>..<head_commit>
Inputs: <exact refreshed packet Inputs manifest; checks are invalid when any effective input changes>
Owned spans: <original base..original slice head, plus each repair start..correction head; original history retained>
- Allowed files: pass | <extra files and their deviation entries>
- Frozen contract: pass
- Red tests unchanged: pass | <deviation entries>
- Red: <test_commit> failed on the new tests. Green: <head_commit> passes test_command.
- Lint: pass | <findings> | skipped
```

- A frozen-contract difference sends the slice back (gates.md).
- Allowed files, Red tests unchanged, Green and Lint must pass. On failure, append a `check_retry` event, diagnose and continue the executor, then go back to step 5. Retry counts alone do not require user permission.

When the checks pass, set the slice to `green`.

## 7. Next

- Headless mode: `git add .software-factory/changes/<slug>`, commit `chore(factory): slice NN built`, push unless `FACTORY_RUNNER_MANAGED=1` (gates.md), and stop; the runner starts the review.
- Otherwise set `notes_for_fresh_session` to "Slice NN green. Next: /factory-build <slug>." or, when every open slice of the milestone is `green`, "Milestone M green. Next: /factory-review <slug>.", and continue directly to that skill under the approved scope (gates.md, Milestones and autopilot); with `--one-step` or a manual pause, tell the user the next skill and stop.
