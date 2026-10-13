# Review: milestone 1, slices 01 to 01

Range: 1aacda467e4c1597aaf46e5234084c365c233812..db4736139efcc99d5d4c1b8004f14f3a4769c22d

## Phase 1
- Per slice: `slices/01/checks.md`, pass (allowed files, frozen contract, red tests unchanged, green)
- Milestone checks 5 to 9: pass | 5 lint skipped (`check_command: none`; `node --check store.js app.js` passes) | 6 language checks skipped (pack `none`, no `kit/languages` file for the module) | 7 dependency rule skipped (`layers: []`) | 8 dead code skipped (no javascript adapter in the kit; manual read found none) | 9 layout pass (store.js, test_store.cjs, test_dashboard.cjs are named by the Layout lines)
- After review fixes: no fixes
- Red: slice 01's test_commit 29fdf6b failed on its 14 new tests that can fail; 4 passed against the stub and are in `red_exempt` by the user's answer. Green: db47361 passes test_command (browser-check 19 of 19; `node --test test_store.cjs` 13 of 13), rerun at review.

## Polish
Local fix mode, small-diff fast path (source diff under 50 lines), all four lenses read directly. Correctness 0 (traced: DOM writes in app.js and storage reads in store.js; nothing is written to storage; stored data is validated before use), cleanliness 0, efficiency 0.
1. [polish/design] note store.js:16: `readStored` accepts a stored `[]`, so the page shows "0 tickets" and no seeds -> follow-up for slice 04 or 05 (user's answer: reject a stored empty array and fall back to the seeds; app cannot produce `[]`; architecture rule is "every item valid"; decided at sign-off)
2. [polish/design] note index.html:24 (pre-existing): hard-coded "12 tickets" duplicates the count app.js now sets -> skip (user's answer; slice 02's re-render owns the count)
- Dropped after validation: store.js `open(undefined)` falls back to `localStorage` through the default parameter; the result is the seeds and the test passes, nothing to act on.
- Review's `fix` answer: `fix none`.

## Lens reviewers
- APoSD: not run (the diff adds no public symbol outside the frozen contract).
- UI/UX: 0 cards (code-level read only; screens not seen, as Chromium is only reachable through the repo test runner). What works: rows keep the design's disclosure, the count is visible text in the `role=status` region, no new element, color or action.
- Security: not run (no `.factory/system/threat-model.md`).
- Money: not run (track standard, `money: false`).

## Follow-ups
- DESIGN.md Typography asks for ID and title at weight 600 and customer and meta in a muted tone; `styles.css` has no such rule (unchanged here, not an Allowed file of slice 01). Per the user's sign-off answer, slice 05 (honest-storage-and-layout) takes it. Not added to 04-slices.md, since editing it would reopen the slices gate.
- A valid stored `[]` renders zero rows with "0 tickets" and the empty-state text hidden (see Polish 1): per the user's sign-off answer, slice 04 or 05 makes the store reject a stored empty array and fall back to the seeds (FR-18). Kept here only, for the same reason.

## Sign-off
Benchmark, 2026-10-13T01:30:00Z (simulated user answer: sign off milestone 1; polish 1 follow-up, polish 2 skip, typography follow-up in slice 05)
