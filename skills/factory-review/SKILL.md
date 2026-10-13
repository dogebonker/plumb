---
name: factory-review
description: Review a green factory milestone - mechanical checks, review agents with lens rubrics, APoSD, UI/UX, Security and Money reviewers, validated fixes applied, regression proofs, human sign-off into review.md.
disable-model-invocation: true
argument-hint: "[slug] [--one-step]"
---

# Factory review

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Scripts first, then the review agents, then the human. A review covers one milestone ([../factory-shared/gates.md](../factory-shared/gates.md), Milestones and autopilot), meaning its slices that are not `done`: `M` is its number as gates.md defines it, `<last>` the id of its last such slice, `<base>` the `base_commit` of its first and `<head>` the `head_commit` of its last. In headless mode a milestone is one slice. `<tmp>` is a new temp directory made at the start of the review and deleted at hand-off.

## 0. Orchestrator or step agent

Interactive mode, not started as a factory step agent, and without `--one-step` in the arguments: you are the orchestrator. Follow [../factory-shared/gates.md](../factory-shared/gates.md), Milestones and autopilot, and do none of the steps below.

## 1. Load the milestone

- Load the change as gates.md describes: the work is the first milestone with a slice not `done`, and every one of its slices that is not `done` must be `green`. Otherwise point to `/factory-build <slug>` and stop.
- Read each of its slices' `packet.md` and `checks.md`.
- Review only committed source. Require `git diff --quiet HEAD -- . ':!.software-factory' ':!.factory'` and `git diff --cached --quiet HEAD -- . ':!.software-factory' ':!.factory'` to succeed, and `git ls-files --others --exclude-standard -- . ':!.software-factory' ':!.factory'` to print nothing. Dirty source: if step 8 was interrupted, first run `git restore -s HEAD -SW -- <its files>`. Otherwise show `git status --short -- . ':!.software-factory' ':!.factory'` and ask the user to commit it to `<last>` (then set its `head_commit` to HEAD) or to discard it, and wait for the answer. Never review around uncommitted source.
- When `slices/<last>/review.md` exists with an empty Sign-off and its Range ends at `<last>`'s `head_commit`, resume at step 5 only when both `git diff --quiet <head> -- . ':!.software-factory' ':!.factory'` and `git diff --cached --quiet <head> -- . ':!.software-factory' ':!.factory'` succeed. Planning-only commits may pass. Otherwise set `<head>` and `<last>`'s `head_commit` to the current committed HEAD and rerun from step 2, replacing the old review and its Range before asking for sign-off.

## 2. Phase 1: mechanical checks

Build ran checks 1 to 5 on each slice and wrote them to `slices/NN/checks.md`; take the results of checks 1 to 4, and run them now for a slice without that file. Run checks 5 to 9 once over the milestone, since a later slice can change what an earlier one's results mean. "The adapter" is `<kit>/adapters/<language>.md` for the module's `language`. Below, for one slice, `<b>` and `<test>` are its own `base_commit` and `test_commit` and "the packet" is its packet; over the milestone, `<b>` is `<base>` and the packet is the union of the milestone's packets. After a review fix commit `<fix>`, rerun every check over the milestone, except that Red tests unchanged diffs only that commit: `git diff <fix>~1 <fix> -- <every packet's Tests first files>`. The `runtime` scan reruns only when the change touched files with that pack's `extensions`.

1. **Allowed files.** `git diff --name-only <b>..HEAD -- . ':!.software-factory' ':!.factory'` is a subset of the packet's Allowed files. Each extra file needs an entry in `deviations`. An unlogged extra is a finding.
2. **Frozen contract.** Find each signature from the packet's Frozen contract in the code. Formatting may differ. A change to the name, parameters, types, return type, errors or visibility is a difference.
3. **Red tests unchanged.** `git diff <test>..HEAD -- <test files from Tests first>` is empty, or each change is logged in `deviations`.
4. **Green.** `test_command` passes at HEAD, apart from tests in `baseline_failures`.
5. **Lint.** `check_command`; each failure in the changed files is a finding. No `check_command`: skipped.
6. **Language checks.** For each module whose `<kit>/languages/<pack>.yaml` has `checks`, `{files}` is the changed files with the listed `extensions`: `git diff --name-only --diff-filter=d <b>..HEAD`, made relative to the module path. No such files: skip the module. Otherwise, from the module directory:
   - `static` on `{files}`. Each issue it reports is a finding.
   - `runtime`, on tracks standard and critical, when the module has a `dev_url` and the tool resolves (`npx --no-install <tool> --version`). If `dev_url` already answers, use that server and leave it running. Otherwise start the module's `dev_command` in the background, wait up to 60 seconds for `dev_url`, run the scan, and stop the server you started on every outcome. Each issue in the JSON is a finding.
   - A tool that is not installed, a server that never answers, or a scan that cannot start (for example, no browser) is reported as skipped, with the error or the `install` line.
7. **Dependency rule.** For each module with `layers` in `lenses.yaml` (globs relative to the module path, where `{a,b}` matches either), list the imports of the changed files with the Import graph command of the adapter for each file's language. An import the diff adds from a file in one layer into a later (outer) layer is a finding tagged `[clean-architecture/dependency rule]`; one the file already had at `<b>` is not. Files in no layer are not checked.
8. **Dead code.** The adapter's Dead code command; each result in the changed files is a finding, except frozen signatures, step definitions a scenario uses, and code a constraint's enforcement names. A tool that is not installed is reported as skipped.
9. **Layout.** Each file the diff adds (`git diff --name-only --no-renames --diff-filter=A <b>..HEAD -- . ':!.software-factory' ':!.factory'`) fits the Layout (gates.md, Layout). Each one that does not is a finding. For each `Pattern` line in `02-architecture.md` or `.software-factory/system/layout.md` whose `check` is not `none`, also run that tool's `command` from `<kit>/layouts/tools.yaml`, from its root. Each issue on a line the diff adds or changes, or about a file or folder the diff adds, is a finding; a tool that is not installed is reported as skipped with its `install` line.

A frozen-contract difference sends its slice back, as gates.md describes.

## 3. Phase 2: review agents and lens reviewers

1. Committed mode: `git add .software-factory/changes/<slug> .software-factory/system` and, when anything is staged, commit `chore(factory): milestone M review`, so the review starts from a clean tree. In interactive mode this commit also carries the planning state since the last one (gates.md, Commits).
2. On tracks standard and critical, start the lens reviewers in the background, one fresh sub-agent each, each lens checked as [../factory-shared/packs.md](../factory-shared/packs.md) describes:
   - **APoSD**, when the diff adds a public symbol in a non-test file that is not in any packet's Frozen contract: `a-philosophy-of-software-design.md` (full size) and the module's language pack index.
   - **UI/UX**, when `ui` is `true` and the milestone changed UI files: a sub-agent follows the `lens` mode of [../factory-ui-ux/SKILL.md](../factory-ui-ux/SKILL.md) for the routes the milestone touches, and writes its findings as cards anchored to the design file or WCAG.
   - **Security**, when `.software-factory/system/threat-model.md` exists and the milestone changed a file it lists under Trust boundaries or Entry points: a sub-agent follows the `lens` mode of [../factory-security/SKILL.md](../factory-security/SKILL.md) on the milestone diff, and writes its confirmed findings as cards.
   - **Money**, on track critical when `money` is `true` in `lenses.yaml`: `fin-verification/SKILL.md` with the one domain skill that fits the milestone (`fin-ledger`, `fin-payments`, `fin-onchain` or `fin-exchange-integration`), or with `fin-money-core` when none fits. `fin-money-core` joins a domain skill only when the risk is arithmetic or idempotency itself. Each pack is read through its `SKILL.md`.

   Each receives:

   > Review `git diff <base>..HEAD -- . ':!.software-factory' ':!.factory'` in `<repo>` through `<lens files>`. The agreed contracts are `<packet paths>`; judge what the code does behind them. Write at most three findings to `<tmp>/<lens>.md`, each as a challenge card (`<absolute path of factory-interface/challenge-card.md>`) read for code: Where quotes the changed line, Alternative is the code change, and Response will be fix or skip. Severity `block` or `fix` needs an anchor: a constraint ID in a packet's Covers, the interface comment of a frozen signature the code contradicts, a threat ID in `.software-factory/system/threat-model.md`, a principle, position or word of the design file, or a WCAG 2.2 A or AA criterion; every other finding is a `note`. A finding about a rendered screen quotes the changed line that renders the element.

3. Run the review agents through their report, as [review-agents.md](review-agents.md) describes, with these factory rules on top:
   - the packets' Covers and Frozen contracts are agreed and are not design findings
   - `check_command` failures are fixed only inside the Allowed files; failures elsewhere are findings
   - out-of-diff findings are recorded as follow-ups in `review.md`, not fixed in this milestone
   - track small: the small-diff fast path, whatever the diff size
   - findings from a rule under the merged Quiet rules of the principle layers ([../factory-shared/gates.md](../factory-shared/gates.md), Paths), money and security rules excepted, are recommended as skip
   - rubric for the agents, each finding from a rubric tagged `[lens/rule]`, each rubric pack checked as packs.md describes:
     - design and reuse: `refactoring-guru.mini.md` and the simplification ladder from packs.md
     - design and efficiency: the module's language pack index; only its CRITICAL and HIGH categories are findings, the rest are notes
     - cleanliness: each test under a packet's Tests first asserts the outcome its line names, and for an FR the outcome of its Example in Covers; a test that only calls the code, or only checks that it does not throw, is a finding tagged `[factory/example-asserted]`
     - cleanliness, in modules with `bdd: native`: duplicate steps, steps that name clicks, fields or URLs, and wording that differs from the product's rules

   Before running the review agents, perform one bounded missing-outcome pass over the milestone’s user-visible behavior: at most three reproducible violations of the product Problem, Success metric, agreed persistence decisions or standing promises. Each records the goal/promise quoted, concrete initial state and event sequence, expected and actual user outcome, changed code location, and reproduction evidence. Do not invent a requirement ID. Data loss or a false “saved” message is not downgraded merely because its precise scenario is absent from Covers. Record these separately as `[factory/missing-outcome]` held findings; a scenario already covered by an ID remains an ordinary conformance finding. Within-contract fixes follow the existing Allowed files and regression-test rules. An omitted promise or changed frozen contract is proposed for correction at sign-off and uses the existing send-back path after the user decides; never rewrite approved contracts or Tests first silently.

4. Interactive mode: fix, as review-agents.md's Fix step describes and without asking, every validated finding the report recommends fixing that stays inside the Allowed files and the frozen contracts and does not touch a file under any packet's Tests first. The rest are skipped, or held for the user's sign-off; the user sees all of them there. Then go on to step 5.

   Headless mode: the report is the question. Write its findings and the lens cards to `slices/<last>/proposed.md`, then wait for the user (gates.md), asking for the numbers to fix (`fix 1 3`, or `fix none`). The run that receives the reply applies those fixes from `proposed.md` as the Fix step describes, continues at step 6, and deletes `proposed.md` once `review.md` is written.
5. Wait until every lens reviewer has written its `<tmp>/<lens>.md`, then collect the cards. Drop a card whose quoted line is not in the diff; a `block` or `fix` card whose anchor does not exist, or whose lens and rule are under Quiet rules of the principle layers ([../factory-shared/gates.md](../factory-shared/gates.md), Paths), money and security rules excepted, becomes a `note`. Interactive mode: apply every remaining `block` and `fix` card after the review agents' fixes, without asking, and skip notes. A card is held for the user at sign-off instead when its Alternative changes a frozen signature (a possible send-back), touches a file outside the Allowed files, or touches a file under any packet's Tests first. Apply each card only if its quoted line still reads the same in the working tree; a card whose line changed is reported in `review.md` as stale.
6. A fix may add its regression test in a new test file beside the slice's tests: before writing it, log `{ slice, file, reason: "regression test for finding N" }` in `deviations` and append the file to that slice's packet's Allowed files. Any other fix the factory hook blocks (a file outside the Allowed files) is not applied: it becomes a follow-up.
7. If any fix changed code, stage by path only the changed files that are in the milestone's packets' Allowed files or in `deviations`; restore, or delete when untracked, any other changed file and record its finding as a follow-up. Commit them as `fix(<slug>): milestone M review`. Log each red-commit test the fix changes in `deviations`, with the finding that changed it.
8. Each test that commit adds or changes proves itself: `git restore -s <fix commit>~1 -SW -- <the commit's non-test files>`, run the test (it must fail), then `git restore -s HEAD -SW -- <the same files>`. After an interruption, that last command restores the fix. A commit with no non-test files has nothing to prove. A test that still passes is reported, not kept as proof.
9. Rerun Phase 1 over the milestone. All checks pass: record the fix commit as the `head_commit` of slice `<last>`. A check the fix commit broke: `git revert` it, tell the user which fix caused it, and keep `head_commit` as it was.

## 4. Write `slices/<last>/review.md`

```markdown
# Review: milestone M, slices NN to <last>

Range: <base>..<head>

## Phase 1
- Per slice: `slices/NN/checks.md`, each pass | <its failures>
- Milestone checks 5 to 9: pass | <findings> | skipped: <reason>
- After review fixes: pass | <failures> | no fixes
- Red: each slice's test_commit failed on its new tests. Green: <head> passes test_command.

## Review agents
<one line per finding, numbered as the report numbered it: `N. [<tag>] <severity> <path>: <finding> -> <outcome>`, where the severity follows the report's recommendation: a finding it recommends fixing is `fix`, one it recommends skipping is `note`, and `block` comes only from lens cards, the outcome one of: `fix` or `skip` (the user's answer), `auto-fixed` (applied without asking), `auto-skipped` (left out of step 4's fixes), `undone` (auto-fixed, then undone by the user), `follow-up` or `dropped`. The tag is the rubric rule, written as interface cards write Lens / rule, or, without one, `review/<category>` (correctness, cleanliness, design, efficiency, gating). Findings dropped after validation get their own lines. Last, the report's coverage line.>

## Lens reviewers
<each card, with its outcome: `fix` or `skip` (the user's answer, a held card included), `auto-fixed`, `auto-skipped` (a note), `undone`, or `stale`; "not run" with the reason when a reviewer did not apply>

## Missing outcomes
<at most three held `[factory/missing-outcome]` findings with goal/promise, reproduction, evidence and proposed contract correction; none when no violation reproduced>

## Follow-ups
<out-of-diff findings>

## Sign-off
<name>, <ISO time>
```

## 5. Human sign-off

Ask the user to read `git diff <base>..<head> -- . ':!.software-factory' ':!.factory'` and `review.md`. In the same question, list each fix applied without asking, numbered, and each held finding or card with fix or skip. The user may name fixes to undo: undo them, with any test those fixes added, in one commit `fix(<slug>): milestone M undo <numbers>`, record it as the `head_commit` of `<last>`, mark them `undone` in `review.md`, rerun Phase 1 and ask again. A held missing-outcome item the user answers fix sends the change back to product when the promise or example was omitted, architecture when the agreed strategy cannot meet it, or interface when a frozen signature must change (track small: slices). Use the existing send-back invalidation and stop; no sign-off while that correction is unresolved. A held item the user answers fix sends its slice back when it changes a frozen signature. Otherwise, when it touches a file outside the Allowed files, first log `{ slice, file, reason: "review finding N, user approved" }` in `deviations` and append the file to that slice's packet; then apply it as in step 3. Only after an explicit sign-off in chat: fill the Sign-off line and set every slice of the milestone to `done`.

Headless mode: commit and push `review.md`, then wait for the user (gates.md) with the comment "Slice NN reviewed: `review.md`. Sign off with a pull-request review whose first line is `sign off slice NN`." The runner records the sign-off.

## 6. Hand off

Interactive mode only: a headless run stops at step 5's wait, and the runner records the sign-off.

1. Delete `<tmp>`. Nothing is committed here (gates.md, Commits).
2. Set `notes_for_fresh_session` to "Milestone M done. Next: /factory-build <slug>." or, when all slices are done, "All slices done. Next: /factory-reconcile <slug>.", and report to the orchestrator (gates.md, Milestones and autopilot); with `--one-step`, tell the user the next skill and stop.
