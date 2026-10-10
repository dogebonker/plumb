---
name: factory-build
description: Build the next slice of a factory change - write its packet, run a fresh executor, prove red then green.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory build

Slug: $ARGUMENTS

You orchestrate. A fresh executor writes the code from the packet alone. You prove the result mechanically.

Slice states: `pending` -> `building` -> `red` -> `green` -> `done` (review sets `done`). `rewind` means the slice's code must be undone before it is rebuilt.

## 1. Check the gate

- Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes: the work is a slice not `done`. Checking out the branch also leaves a detached HEAD from an interrupted red check.
- Pick the first slice not `done` and resume by its state:
  - `pending`: step 2.
  - `rewind`: rewind (below), then step 2.
  - `building`: an executor was interrupted. If `git log <base_commit>..HEAD` shows both `test(<slug>): slice NN red` and `feat(<slug>): slice NN`, go to step 4. Otherwise rewind, then step 3.
  - `red`: step 5.
  - `green`: tell the user to run `/factory-review <slug>`. Stop.
- The working tree must be clean apart from `.factory/`.

**Rewind** undoes a slice's code without touching `.factory/` or rewriting history:

1. Show `git log --oneline <base_commit>..HEAD`, `git status --short` and `git clean -nd -- . ':!.factory'`, and ask the user to confirm.
2. `git restore --source=<base_commit> --staged --worktree -- . ':!.factory'` then `git clean -fd -- . ':!.factory'`.
3. If anything is staged, commit it as `revert(<slug>): slice NN`.
4. Set the slice to `{ state: pending, base_commit: null, test_commit: null, head_commit: null }`.

## 2. Write the packet

Write `.factory/changes/<slug>/slices/NN/packet.md` from [packet.md](packet.md), replacing any older packet for this slice. Copy, never paraphrase:

- the slice's heading from `04-slices.md` as Goal
- the covered IDs with their fit criteria: each FR's Example line from `01-product.md` (track small: `04-slices.md`), each SYS ID's fit criterion from `.factory/system/constraints.md`
- the NFR budgets it covers and the Research facts it needs, with their `path:line`, from `02-architecture.md`
- the frozen signatures, interface comments and depth statements it touches, from `03-interface.md`, and the Stubs section of `~/.software-factory/adapters/<language>.md` for the module's language
- its tests, allowed files and verify commands, from `04-slices.md`; in a module with `bdd: native`, its scenarios verbatim from the Test plan, and the existing step definitions found with the adapter's BDD step search (`path:line` and step text)
- under Rules in scope, the paths of the profile's `packet` lenses (size `nano`) and of the module's language pack index and rules, each that passes the pin check in [../factory-shared/packs.md](../factory-shared/packs.md)

Done when an engineer who has never seen the gate documents could build the slice from the packet alone.

## 3. Dispatch the executor

Set the slice to `{ state: building, base_commit: <git rev-parse HEAD> }`. Start one fresh sub-agent. It receives the packet path and these instructions, nothing else from this conversation:

> Read `<packet path>` and every allowed file it lists. Build the slice in two commits. Stage files by path, only files in Allowed files.
>
> 1. **Red.** Write the tests under "Tests first". Add each new frozen signature as a stub in the packet's stub form, so the code compiles. A changed signature keeps its old behavior behind the new signature, and existing tests are updated to the new signature and still pass. Run the tests: every new test fails, every other test passes except those in `<baseline_failures>`. List any new test that passes against the stub (a negative case, for example) in your report rather than changing it. Commit as `test(<slug>): slice NN red`.
> 2. **Green.** Implement until every Verify command passes. The tests from the red commit stay exactly as written, and every frozen signature stays exactly as written. Commit as `feat(<slug>): slice NN`.
>
> Stop and report, with the reason, when: a frozen signature cannot work as written, a file outside Allowed files must change, a red-commit test is wrong, or a pre-commit hook rejects the red commit.
>
> Report: both commit shas, the tail of the failing run from step 1, the tail of the passing run from step 2, and anything you stopped on.

When the executor stops:

- **Frozen signature or wrong test:** send the slice back.
- **File outside the list:** ask the user. Allowed: log `{ slice, file, reason }` in `deviations`, append the file to the packet's Allowed files, and continue the executor. Refused: send the slice back.
- **Pre-commit hook:** ask the user whether red commits may use `--no-verify`, and continue the executor with the answer.
- **A new test passes against the stub:** ask the user to keep it (record its name in the slice's `red_exempt`) or have the executor rewrite it.

**Send back** follows gates.md, which picks the target gate from the reason.

## 4. Prove red

1. Record `test_commit`: the sha of the `test(<slug>): slice NN red` commit. The test files are those listed in the packet's Tests first.
2. `git checkout --detach <test_commit>`
3. Run `test_file_command` once per test file (a feature file: the adapter's BDD run command), then `test_command`.
4. `git checkout <branch>`

Red means: it builds; every new test fails, on an assertion or an error raised through a stub, except those in `red_exempt`; and every other test passes except those in `baseline_failures`.

- Red: set the slice to `red`.
- Not red, first time: rewind and dispatch a fresh executor (step 3) with the output.
- Not red, second time: show the user the output and ask how to proceed.

## 5. Prove green

At the branch head, run every Verify command and `test_command`. Green means all pass, apart from tests in `baseline_failures`. On failure, continue the executor with the output, or dispatch a fresh one if it is gone. Record `head_commit` and set the slice to `green`.

## 6. Hand off

Set `notes_for_fresh_session` to "Slice NN green. Next: /factory-review <slug>." Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): slice NN built`. Tell the user to run `/factory-review <slug>`.
