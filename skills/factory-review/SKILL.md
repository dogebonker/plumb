---
name: factory-review
description: Review a green factory slice - contract, file and test checks, then /polish, then human sign-off into review.md.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory review

Slug: $ARGUMENTS

Scripts first, then `/polish`, then the human. Requires the `polish` skill. Below, `<base>`, `<test>` and `<head>` are the slice's own `base_commit`, `test_commit` and `head_commit`.

## 1. Load the slice

- Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes: the work is a `green` slice. Otherwise point to `/factory-build <slug>` and stop.
- Read the slice's `packet.md`.

## 2. Phase 1: mechanical checks

Run each check and record pass or fail with evidence. Rerun all of them whenever code changes later in this review.

1. **Allowed files.** `git diff --name-only <base>..HEAD -- . ':!.factory'` is a subset of the packet's Allowed files. Each extra file needs an entry in `deviations`. An unlogged extra is a finding.
2. **Frozen contract.** Find each signature from the packet's Frozen contract in the code. Formatting may differ. A change to the name, parameters, types, return type, errors or visibility is a difference.
3. **Red tests unchanged.** `git diff <test>..HEAD -- <test files from Tests first>` is empty, or each change is logged in `deviations`.
4. **Green.** `test_command` passes at HEAD, apart from tests in `baseline_failures`.
5. **Language checks.** For each module whose `~/.software-factory/languages/<pack>.yaml` has `checks`, `{files}` is the slice's changed files with the listed `extensions`: `git diff --name-only --diff-filter=d <base>..HEAD`, made relative to the module path. No such files: skip the module. Otherwise, from the module directory:
   - `static` on `{files}`. Each issue it reports is a finding.
   - `runtime`, on tracks standard and critical, when the module has a `dev_url`. If `dev_url` already answers, use that server and leave it running. Otherwise start the module's `dev_command` in the background, wait up to 60 seconds for `dev_url`, run the scan, and stop the server you started. Each issue in the JSON is a finding.
   - A tool that is not installed, a server that never answers, or a scan that cannot start (for example, no browser) is reported as skipped, with the error or the `install` line.

A frozen-contract difference sends the slice back, as gates.md describes.

## 3. Phase 2: /polish

1. Committed mode: commit `.factory/changes/<slug>` first (`chore(factory): slice NN review`), so polish sees a clean tree.
2. Tell the user, in your own message before the call:
   - the slice's Covers and Frozen contract are agreed and are not design findings
   - `.factory/` is planning state, outside the review: write the diff with `-- . ':!.factory'`
   - the check command is `check_command`. Fix its failures only inside the Allowed files; failures elsewhere are findings
   - out-of-diff findings are recorded as follow-ups in `review.md`, not fixed in this slice
   - fixes land as a new commit, never amended into an earlier one
3. Invoke the `polish` skill with the bare sha `<base>` as its argument.
4. If polish changed code, commit the fixes as a new commit `fix(<slug>): slice NN review`, rerun Phase 1, and record the new `head_commit`. If that commit breaks a Phase 1 check, `git revert` it, tell the user which fix caused it, and keep the slice.

When polish ends, clean or not, continue at step 4.

## 4. Write `slices/NN/review.md`

```markdown
# Review: slice NN, <name>

Range: <base>..<head>

## Phase 1
- Allowed files: pass | <extra files and their deviation entries>
- Frozen contract: pass
- Red tests unchanged: pass | <deviation entries>
- Red: <test> failed on the new tests. Green: <head> passes test_command.
- Language checks: pass | <issues> | skipped: <reason>

## Polish
<each validated finding, numbered as polish numbered it, with the user's answer (fix / skip) and the outcome>

## Follow-ups
<out-of-diff findings>

## Sign-off
<name>, <ISO time>
```

## 5. Human sign-off

Ask the user to read `git diff <base>..<head> -- . ':!.factory'` and `review.md`, then sign off. Only after an explicit sign-off in chat: fill the Sign-off line and set the slice to `done`.

## 6. Hand off

1. More slices left: set `notes_for_fresh_session` to "Slice NN done. Next: /factory-build <slug>." All done: "All slices done."
2. Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): slice NN signed off`.
3. Tell the user to start a fresh session for the next slice, or that the change is ready to merge from `<branch>`.
