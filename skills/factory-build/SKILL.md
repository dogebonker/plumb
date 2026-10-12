---
name: factory-build
description: Build the slices of a factory change's next milestone - packet, fresh executor, red then green, mechanical checks per slice - then go on to its review.
disable-model-invocation: true
argument-hint: "[slug] [--one-step]"
---

# Factory build

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

A step agent, or a headless run, builds one slice: a fresh executor writes the code from the packet alone, and you prove the result mechanically.

Slice states: `pending` -> `building` -> `red` -> `green` -> `done` (review sets `done`). `rewind` means the slice's code must be undone before it is rebuilt. In interactive mode, `/factory-build` starts the autopilot: the session becomes a thin orchestrator, and each slice is built by a fresh step agent that follows this skill for that slice ([../factory-shared/gates.md](../factory-shared/gates.md), Milestones and autopilot).

## 0. Orchestrator or step agent

Interactive mode, not started as a factory step agent, and without `--one-step` in the arguments: you are the orchestrator. Follow [../factory-shared/gates.md](../factory-shared/gates.md), Milestones and autopilot, and do none of the steps below.

## 1. Check the gate

- Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes: the work is a slice not `done`. Checking out the branch also leaves a detached HEAD from an interrupted red check.
- The milestone in progress is the one holding the first slice not `done`. When every one of its slices that is not `done` is `green`, go to step 7. Otherwise take its first slice that is neither `done` nor `green` and resume by its state:
  - `pending`: step 2.
  - `rewind`: rewind (below, cause `sent_back`), then step 2.
  - `building`: an executor was interrupted. If `git log <base_commit>..HEAD` shows both `test(<slug>): slice NN red` and `feat(<slug>): slice NN`, go to step 4. If the slice's last `history` event is an `executor_stop` you were given the answer to, apply it (step 3) and dispatch a fresh executor that keeps the work already in the tree and any red commit. Otherwise rewind (cause `interrupted`), then step 3.
  - `red`: step 5.
- The working tree must be clean apart from `.factory/`.

**Rewind** undoes a slice's code without touching `.factory/` or rewriting history, and appends a `rewind` event with its cause (gates.md, History):

1. Show `git log --oneline <base_commit>..HEAD`, `git status --short` and `git clean -nd -- . ':!.factory'`, and ask the user to confirm.
2. `git restore --source=<base_commit> --staged --worktree -- . ':!.factory'` then `git clean -fd -- . ':!.factory'`.
3. If anything is staged, commit it as `revert(<slug>): slice NN`.
4. Set the slice to `{ state: pending, base_commit: null, test_commit: null, head_commit: null }`, and every later slice that is not `done` too: the restore removed their code as well.

## 2. Write the packet

Write `.factory/changes/<slug>/slices/NN/packet.md` from [packet.md](packet.md), replacing any older packet for this slice. Copy, never paraphrase:

- the slice's heading from `04-slices.md` as Goal
- the covered IDs with their fit criteria: each FR's Example line from `01-product.md` (track small: `04-slices.md`), each SYS ID's fit criterion from `.factory/system/constraints.md`
- the NFR budgets it covers and the Research facts it needs, with their `path:line`, from `02-architecture.md`
- the frozen signatures, interface comments and depth statements it touches, from `03-interface.md` (track small: the Interface section of `04-slices.md`), and the Stubs section of `~/.software-factory/adapters/<language>.md` for the module's language
- its tests, allowed files and verify commands, from `04-slices.md`; in a module with `bdd: native`, its scenarios verbatim from the Test plan of `03-interface.md` (track small: from `04-slices.md`), and the existing step definitions found with the adapter's BDD step search (`path:line` and step text)
- under Layout, the lines that admit each Allowed file (gates.md, Layout), with what lives there and what may not; a file admitted only because its folder already existed is listed as `existing`
- under Rules in scope, the active playbook entries whose scope matches the Allowed files, copied (gates.md, Load a change, step 7); then the paths of the profile's `packet` lenses (size `nano`) and of the module's language pack index and rules, each that passes the pin check in [../factory-shared/packs.md](../factory-shared/packs.md), and the simplification ladder from that file, copied

Done when an engineer who has never seen the gate documents could build the slice from the packet alone.

## 3. Dispatch the executor

Set the slice to `{ state: building, base_commit: <git rev-parse HEAD> }`. Start one fresh sub-agent in the foreground. It receives the packet path and these instructions, nothing else from this conversation:

> Read `<packet path>` and every allowed file it lists. Build the slice in two commits. Stage files by path, only files in Allowed files.
>
> 1. **Red.** Write the tests under "Tests first", each asserting the outcome its line names, not only that the call returns; in a BDD module, the feature file and every step definition its scenarios need. Add each new frozen signature as a stub in the packet's stub form, so the code compiles. A changed signature keeps its old behavior behind the new signature, and existing tests are updated to the new signature and still pass. Run the tests: every new test fails, every other test passes except those in `<baseline_failures>`. List any new test that passes against the stub (a negative case, for example) in your report rather than changing it. Commit as `test(<slug>): slice NN red`.
> 2. **Green.** Implement until every Verify command passes. The tests from the red commit stay exactly as written, and every frozen signature stays exactly as written. Commit as `feat(<slug>): slice NN`.
>
> Stop and report, with the reason, when: a frozen signature cannot work as written, a file outside Allowed files must change, a red-commit test is wrong, a pre-commit hook rejects the red commit, or a commit fails to sign. Never commit unsigned.
>
> Report: both commit shas, the tail of the failing run from step 1, the tail of the passing run from step 2, and anything you stopped on.

When the executor stops, append an `executor_stop` event with the reason. To continue the executor after an answer: apply the answer first (the deviation and packet entry, the `--no-verify` permission), then continue it, or dispatch a fresh one that keeps the work in the tree if it is gone. The reasons:

- **Frozen signature or wrong test:** send the slice back.
- **File outside the list:** run the adapter's Typecheck on the working tree. When it reports an error in that file caused by a signature this slice adds or changes in the packet's Frozen contract (a fake, a caller, the composition root), allow the file without asking: log `{ slice, file, reason: "typecheck: <the error, one line>" }` in `deviations`, append it to the packet's Allowed files, and continue the executor. Otherwise ask the user. Allowed: log `{ slice, file, reason }` in `deviations`, append the file to the packet's Allowed files, and continue the executor. Refused: send the slice back.
- **Pre-commit hook:** ask the user whether red commits may use `--no-verify`, and continue the executor with the answer.
- **Signing** (detail `signing`): ask the user to unlock their signing agent, then continue the executor.
- **A new test passes against the stub:** ask the user to keep it (record its name in the slice's `red_exempt`) or have the executor rewrite it.

**Send back** follows gates.md, which picks the target gate from the reason.

## 4. Prove red

1. Record `test_commit`: the sha of the `test(<slug>): slice NN red` commit. The test files are those listed in the packet's Tests first.
2. `git checkout --detach <test_commit>`
3. Run `test_file_command` once per test file (a feature file: the adapter's BDD run command), then `test_command`.
4. `git checkout <branch>`

Red means: it builds; every new test fails, on an assertion or an error raised through a stub, except those in `red_exempt` (an undefined or pending step is not red: the red commit defines every step); and every other test passes except those in `baseline_failures`.

- Red: set the slice to `red`.
- Not red, first time: append a `red_retry` event, rewind (cause `red_retry`) and dispatch a fresh executor (step 3) with the output.
- Not red, second time: show the user the output and ask how to proceed.

## 5. Prove green

At the branch head, run every Verify command and `test_command`. Green means all pass, apart from tests in `baseline_failures`. On a first failure, append a `green_retry` event and continue the executor with the output, or dispatch a fresh one if it is gone; on a second, show the user the output and ask how to proceed. Record `head_commit`; the slice stays `red` until step 6 passes.

## 6. Check the slice

Run Phase 1 of [../factory-review/SKILL.md](../factory-review/SKILL.md) (checks 1 to 5) on this slice alone: its `base_commit`, `test_commit` and packet. Write `slices/NN/checks.md`:

```markdown
# Checks: slice NN, <name>

Range: <base_commit>..<head_commit>
- Allowed files: pass | <extra files and their deviation entries>
- Frozen contract: pass
- Red tests unchanged: pass | <deviation entries>
- Red: <test_commit> failed on the new tests. Green: <head_commit> passes test_command.
- Lint: pass | <findings> | skipped
```

- A frozen-contract difference sends the slice back (gates.md).
- Allowed files, Red tests unchanged, Green and Lint must pass. On a first failure, append a `check_retry` event and continue the executor with it, or dispatch a fresh one if it is gone, then go back to step 5. On a second, ask the user.

When the checks pass, set the slice to `green`.

## 7. Next

- Headless mode: `git add .factory/changes/<slug>`, commit `chore(factory): slice NN built`, push, and stop; the runner starts the review.
- Otherwise set `notes_for_fresh_session` to "Slice NN green. Next: /factory-build <slug>." or, when every open slice of the milestone is `green`, "Milestone M green. Next: /factory-review <slug>.", and report to the orchestrator (gates.md, Milestones and autopilot); with `--one-step`, tell the user the next skill and stop.
