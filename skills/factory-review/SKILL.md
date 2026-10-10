---
name: factory-review
description: Review a green factory slice - mechanical checks, /polish with lens rubrics, APoSD and Money reviewers, regression proofs, human sign-off into review.md.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory review

Slug: $ARGUMENTS

Scripts first, then `/polish`, then the human. Requires the `polish` skill. Below, `<base>`, `<test>` and `<head>` are the slice's own `base_commit`, `test_commit` and `head_commit`, and `<tmp>` is a new temp directory made at the start of the review and deleted at hand-off.

## 1. Load the slice

- Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes: the work is a `green` slice. Otherwise point to `/factory-build <slug>` and stop.
- Read the slice's `packet.md`.

## 2. Phase 1: mechanical checks

Run each check and record pass or fail with evidence. "The adapter" is `~/.software-factory/adapters/<language>.md` for the module's `language`. Rerun them whenever code changes later in this review; the `runtime` scan reruns only when the change touched files with that pack's `extensions`.

1. **Allowed files.** `git diff --name-only <base>..HEAD -- . ':!.factory'` is a subset of the packet's Allowed files. Each extra file needs an entry in `deviations`. An unlogged extra is a finding.
2. **Frozen contract.** Find each signature from the packet's Frozen contract in the code. Formatting may differ. A change to the name, parameters, types, return type, errors or visibility is a difference.
3. **Red tests unchanged.** `git diff <test>..HEAD -- <test files from Tests first>` is empty, or each change is logged in `deviations`.
4. **Green.** `test_command` passes at HEAD, apart from tests in `baseline_failures`.
5. **Lint.** `check_command`; each failure in the slice's changed files is a finding.
6. **Language checks.** For each module whose `~/.software-factory/languages/<pack>.yaml` has `checks`, `{files}` is the slice's changed files with the listed `extensions`: `git diff --name-only --diff-filter=d <base>..HEAD`, made relative to the module path. No such files: skip the module. Otherwise, from the module directory:
   - `static` on `{files}`. Each issue it reports is a finding.
   - `runtime`, on tracks standard and critical, when the module has a `dev_url` and the tool resolves (`npx --no-install <tool> --version`). If `dev_url` already answers, use that server and leave it running. Otherwise start the module's `dev_command` in the background, wait up to 60 seconds for `dev_url`, run the scan, and stop the server you started on every outcome. Each issue in the JSON is a finding.
   - A tool that is not installed, a server that never answers, or a scan that cannot start (for example, no browser) is reported as skipped, with the error or the `install` line.
7. **Dependency rule.** For each module with `layers` in `lenses.yaml` (globs relative to the module path), list the imports of the slice's changed files with the adapter's Import graph command. An import from a file in one layer into a later (outer) layer is a finding tagged `[clean-architecture/dependency rule]`. Files in no layer are not checked.
8. **Dead code.** The adapter's Dead code command; each result in the slice's changed files is a finding, except frozen signatures, step definitions a scenario uses, and code a constraint's enforcement names. A tool that is not installed is reported as skipped.

A frozen-contract difference sends the slice back, as gates.md describes.

## 3. Phase 2: /polish and lens reviewers

1. Committed mode: commit `.factory/changes/<slug>` first (`chore(factory): slice NN review`), so polish sees a clean tree.
2. On tracks standard and critical, start the lens reviewers in the background, one fresh sub-agent each, each lens checked as [../factory-shared/packs.md](../factory-shared/packs.md) describes:
   - **APoSD**, when the diff adds a public symbol that is not in the packet's Frozen contract: `a-philosophy-of-software-design.md` (full size) and the module's language pack index.
   - **Money**, on track critical when `money` is `true` in `lenses.yaml`: `fin-verification/SKILL.md`, the one domain skill that fits the slice (`fin-ledger`, `fin-payments`, `fin-onchain` or `fin-exchange-integration`), and `fin-money-core` only when the slice's risk is arithmetic or idempotency itself.

   Each receives:

   > Review `git diff <base>..HEAD -- . ':!.factory'` in `<repo>` through `<lens files>`. The agreed contract is `<packet path>`; judge what the code does behind it. Write at most three findings to `<tmp>/<lens>.md`, each as a challenge card (`<absolute path of factory-interface/challenge-card.md>`) read for code: Where quotes the changed line, Alternative is the code change, and Response will be fix or skip. Severity `block` or `fix` needs an anchor: a constraint ID in the packet's Covers, or the interface comment of a frozen signature the code contradicts; every other finding is a `note`.

3. Tell the user, in your own message before the call:
   - the slice's Covers and Frozen contract are agreed and are not design findings
   - `.factory/` is planning state, outside the review: write the diff with `-- . ':!.factory'`
   - the check command is `check_command`. Fix its failures only inside the Allowed files; failures elsewhere are findings
   - out-of-diff findings are recorded as follow-ups in `review.md`, not fixed in this slice
   - fixes land as a new commit, never amended into an earlier one
   - track small: use your small-diff fast path, without agent fan-out, whatever the diff size
   - findings from a rule under Quiet rules in `~/.software-factory/principles.md` are recommended as skip
   - rubric for its agents, each finding from a rubric tagged `[lens/rule]`, each rubric pack checked as packs.md describes:
     - design and reuse: `refactoring-guru.mini.md` and the simplification ladder (does it need to exist; is it already in the codebase; does the standard library, the platform or an installed dependency do it; can it be one line; only then the minimum code)
     - design and efficiency: the module's language pack index; only its CRITICAL and HIGH categories are findings, the rest are notes
     - cleanliness, in modules with `bdd: native`: duplicate steps, steps that name clicks, fields or URLs, and wording that differs from the product's rules
4. Invoke the `polish` skill with the bare sha `<base>` as its argument.
5. Collect the lens reviewers' cards. Drop a card whose quoted line is not in the diff; a `block` or `fix` card whose anchor does not exist, or whose lens and rule are under Quiet rules in `~/.software-factory/principles.md`, becomes a `note`. Present the rest to the user beside polish's report, `block` first, each with fix or skip. Apply approved card fixes after polish's own fixes, each only if its quoted line still reads the same in the working tree.
6. A fix the factory hook blocks (a file outside the Allowed files) is not applied: it becomes a follow-up.
7. If any fix changed code, stage the changed source files by path and commit them as `fix(<slug>): slice NN review`. Log each red-commit test the fix changes in `deviations`, with the finding that changed it.
8. Each test that commit adds or changes proves itself: `git checkout <fix commit>~1 -- <the commit's non-test files that existed before it>` and delete the non-test files it added, run the test (it must fail), then `git checkout HEAD -- <all of those files>`. After an interruption, that last command restores the fix. A test that still passes is reported, not kept as proof.
9. Rerun Phase 1. All checks pass: record the fix commit as `head_commit`. A check the fix commit broke: `git revert` it, tell the user which fix caused it, and keep `head_commit` as it was.

When polish ends, clean or not, continue with step 5 below.

## 4. Write `slices/NN/review.md`

```markdown
# Review: slice NN, <name>

Range: <base>..<head>

## Phase 1
- Allowed files: pass | <extra files and their deviation entries>
- Frozen contract: pass
- Red tests unchanged: pass | <deviation entries>
- Red: <test> failed on the new tests. Green: <head> passes test_command.
- Lint: pass | <findings>
- Language checks: pass | <issues> | skipped: <reason>
- Dependency rule: pass | <findings> | no layers
- Dead code: pass | <findings> | skipped: <reason>

## Polish
<each validated finding, numbered as polish numbered it, tagged [lens/rule] when a rubric produced it, with the user's answer (fix / skip) and the outcome>

## Lens reviewers
<each card, with the user's answer (fix / skip) and the outcome; "not run" with the reason when a reviewer did not apply>

## Follow-ups
<out-of-diff findings>

## Sign-off
<name>, <ISO time>
```

## 5. Human sign-off

Ask the user to read `git diff <base>..<head> -- . ':!.factory'` and `review.md`, then sign off. Only after an explicit sign-off in chat: fill the Sign-off line and set the slice to `done`.

## 6. Hand off

1. Delete `<tmp>`. More slices left: set `notes_for_fresh_session` to "Slice NN done. Next: /factory-build <slug>." All done: "All slices done. Next: /factory-reconcile <slug>."
2. Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): slice NN signed off`.
3. Tell the user to start a fresh session for the next slice, or, when all slices are done, to run `/factory-reconcile <slug>` before merging.
