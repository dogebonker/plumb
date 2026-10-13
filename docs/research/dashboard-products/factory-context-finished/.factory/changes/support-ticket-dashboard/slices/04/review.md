# Review: milestone 2, slices 02 to 04

Range: 7f0211614c6f45727e5f41e87cbd05bf89bf83ca..3cc2f41 (source diff, `-- . ':!.factory'`)

Range gap, recorded honestly: the milestone's own `<base>` is slice 02's `base_commit` f006d08, and slice 01/02 git objects (f006d08, 177e698, f3a9160, 354ee7c) do not exist in this repository (recovery.md: the original temporary repository was deleted). The earliest available commit is 7f02116, the recovered slice 03 RED checkpoint, so the commit-based Range covers slices 03 and 04 and the review fixes only. Slice 02's code (details dialog, `TicketRepo.update`) is in the root tree and was read in full at HEAD by the reviewers, but its diff, its Red proof and its Allowed-files proof cannot be recomputed from git; its checks are the retained `slices/02/checks.md` (written before the loss) plus the fresh full test run below. No check or commit was recreated for slices 01 or 02. Slice 01 (milestone 1, already green) is likewise only the retained `checks.md`.

The Range header ends at the review fix commit 3cc2f41, which is slice 04's new `head_commit`.

## Phase 1
- Per slice: `slices/01/checks.md` pass (retained, git objects unavailable), `slices/02/checks.md` pass (retained, git objects unavailable), `slices/03/checks.md` pass (recovered checkpoints), `slices/04/checks.md` pass with one logged deviation (below).
- Milestone checks 5 to 9, rerun at 3cc2f41 over the available Range:
  1. Allowed files: `app.js index.html store.js styles.css test_dashboard.cjs test_review.cjs test_screens.cjs` are in the union of packets 02/03/04, except `test_screens.cjs` (slice 04 packet admits it only under "Optional screenshots", operator instruction) and `test_review.cjs` (added by this review). Both are logged in `status.yaml` `deviations`; `test_review.cjs` is also appended to packet 04's Allowed files. Slice 04's checks.md had noted `test_screens.cjs` without a deviation entry; that is now fixed by logging it.
  2. Frozen contract: pass. No signature changed; `TicketRepo.create` and the DOM contract are exercised by the tests.
  3. Red tests unchanged: pass. `git diff 7f02116..HEAD` on `test_store.cjs` is empty; `test_dashboard.cjs` only gains 194 added lines (slice 04 red); the fix commit changes no file under any packet's Tests first.
  4. Green: `/private/tmp/fb-neamoi0s/browser-check/browser-check` at 3cc2f41: 47 tests, 47 pass, 0 fail (17 store, 28 browser/screens/existing, 2 review regression tests). Same wrapper at 083157e (before fixes): 45 of 45.
  5. Lint: skipped, `check_command` is empty.
  6. Language checks: skipped, module pack is `none` (no `checks`).
  7. Dependency rule: skipped, `layers` is empty.
  8. Dead code: skipped, no `javascript` adapter in the kit (`kit/adapters` has go, python, rust, typescript only). The Security reviewer and Correctness reviewer found no dead CSS selectors by reading.
  9. Layout: pass. `test_screens.cjs` and `test_review.cjs` sit in the flat root beside the existing `test*.cjs`; the Pattern is `existing`, check `none`.
- After review fixes: pass (all of the above rerun at 3cc2f41; C-01 grep for `http` in the five source files prints 0 matches).
- Red: slice 03 RED 7f02116 failed the 5 create tests and slice 04 RED fb34e4c failed its 4 new tests (per their checks.md; the original slice 01/02 RED commits are unavailable). Green: 3cc2f41 passes test_command.
- Optional lenses and tools: runtime scan (axe) skipped, pack `none` has no `checks`; Impeccable/axe/Lighthouse skipped, not installed and not to be installed. Money lens not applicable (`money: false`). Security lens (the skill's trigger) did not apply: no `.factory/system/threat-model.md`; the operator asked for a quick pass, which the Correctness reviewer did (below).

## Polish
`/polish` was not run as a separate skill: the operator asked for a lean, small panel with a time and cost cap, so its categories were folded into one correctness/cleanliness/accessibility/security reviewer and one UI/UX reviewer. This is a deviation from the skill, not a clean polish run.
1. [factory/example-asserted] note: tests were not re-audited by the panel; the packets' tests were reviewed by their slice's red/green checks. -> dropped (not a finding, recorded as not covered)
2. [lens/rule] none further: no `innerHTML` anywhere, every dynamic value uses `textContent`; `store.js` `read()` handles null, corrupt JSON, wrong shapes and a throwing storage; focus restore after save, cancel, Escape and create is right; no dead CSS; contrast of the palette passes. -> no finding

## Lens reviewers
Cards are in `.tmp/review/correctness-a11y.md` and `.tmp/review/uiux.md` (untracked scratch, deleted at hand-off; the cards are summarized here).
- C1. [correctness-a11y/WCAG 4.1.3, 3.3.1; NFR-02] fix `app.js`: a failed Create ticket left focus on the `Create ticket` button, so errors were not announced. Validated: the new test failed before the fix (focus was on `create-submit`). Alternative applied: `createFields.find(({name}) => errors[name])?.input.focus();` in `showErrors`. -> auto-fixed (3cc2f41)
- C2. [security/localStorage parsing] note `store.js`: `isTicket` accepts any string id, so a hand-edited id like `T1e999` makes `create` return `TInfinity` repeatedly (confirmed by the reviewer in node), breaking FR-16 for tampered data only. No anchor, outside the diff (`store.js` untouched by this milestone's later slices). -> auto-skipped, follow-up
- U1. [UI/UX/alignment, the known ~1px nit] note `styles.css`: `.filters input, .filters select { min-height: 40px }` plus `line-height: 1.4` made the search input 40.4px against the selects' 40px, so the Search label sat 0.4 px higher. Measured in a browser before the fix: control tops 103.98 / 104.38 / 104.38. Applied: `height: 2.5rem`. A one-line change with a failing-then-passing test, so it was fixed although the card was a note. After the fix the test passes and the re-rendered `desktop-list.png` shows the three labels on one line. -> auto-fixed (3cc2f41)
- U2. [UI/UX/scan alignment at 360px] note `styles.css`: mobile rows size their `auto` badge columns per row, so status/priority pills start at ragged x positions. Cosmetic, no information lost, no anchor. -> auto-skipped, follow-up
- What works (reviewer, reading screenshots and source, not human approval): P1 twelve rows with all five fields visible at 1280x800; P2 status and priority as words; P3 one filled primary per surface; title is the heaviest weight; only blue and red accents plus neutral grays; 360px no overflow or clipping. The no-match empty state was judged from the markup only (no screenshot of it).

## Fix commit
3cc2f41 `fix(support-ticket-dashboard): milestone 2 review`: `app.js` (focus first invalid field), `styles.css` (filter control height), new `test_review.cjs` (2 regression tests). Proofs: both new tests failed on the pre-fix tree (focus was `create-submit`; control tops 103.98 versus 104.38) and pass at 3cc2f41; the full wrapper is 47 of 47. No red-commit test was changed.

## Deviations
- `test_screens.cjs` (slice 04): not in the packet's Allowed files; admitted by the operator's instruction (packet "Optional screenshots"); logged in `status.yaml` `deviations`. It writes PNGs to `.tmp/shots/` only and asserts that files were written. It is committed (d661d5c) and is run by the wrapper, so each `browser-check` regenerates the screenshots.
- `test_review.cjs`: new review regression test file, logged and appended to packet 04.

## Follow-ups
- F1. `store.js` `isTicket`: require `/^T\d{3,}$/` on `id` and reject duplicate ids (C2). A small separate change.
- F2. Mobile row badges at 360px: fix the priority column width so pills align (U2). Cosmetic.
- F3. Slice 01 and 02 historical git objects are unavailable; their checks cannot be re-proved from git. Accepted as a recorded gap, not repairable.
- F4. The no-match empty state has no screenshot; add one to `test_screens.cjs` if wanted.
- F5. Palette greys beyond DESIGN.md's tokens (`#5b6068 #f3f5f8 #c4c7cc #e1e3e6 #6b7280 #9aa0a6 #1d4aa2`) are recorded in `slices/04/checks.md`; consider adding them to DESIGN.md in a design-file change.

## Screens for the human
`.tmp/shots/` (untracked): `desktop-list.png`, `desktop-details.png`, `desktop-create-errors.png`, `mobile-list.png`, `mobile-details.png`, `mobile-create-errors.png`, re-rendered at 3cc2f41. Agent-seen only; no human has seen or approved them.

## Sign-off
(not signed off; waiting for the user)
