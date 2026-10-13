# Checks: slice 04, hierarchy-360-names

Range: 8bc1ee596e055aa3b2188dd717a72c68113e2caa..d661d5c (red fb34e4c, green 8153397, polish d661d5c)
- Allowed files: pass for styles.css, index.html, app.js, test_dashboard.cjs. Extra file: `test_screens.cjs` (screenshot script, operator-requested; writes PNGs under `.tmp/shots/`, asserts only that files were written). No deviation entry: admitted by the operator's instruction for this step, noted here.
- Frozen contract: pass (no signatures changed; `store.js` and `tickets.js` untouched; stable names found by role and name by the slice-04 tests).
- Red tests unchanged: pass (`git diff --numstat fb34e4c HEAD -- test_dashboard.cjs` is empty; the red commit only added 194 lines, no deletions, so earlier tests are untouched).
- Red: fb34e4c checked out detached, `browser-check`: 43 tests, 39 pass, 4 fail (the 4 new tests: 360 compact rows, 1280 row hierarchy, ten rows in first viewport, one filled primary button). Every other test passed (17 store tests, 17 earlier browser tests, test_existing.cjs). Four new tests passed against the old markup because the old page already held those properties: no overflow at 360, status/priority as words, stable names, no remote URL. They are regression guards (red_exempt, kept by the executor, not rewritten).
- Green: d661d5c, `browser-check`: 45 tests, 45 pass (28 browser/screenshot-and-existing, 17 store), 0 fail; includes `test_existing.cjs` and the two `test_screens.cjs` tests. Run exactly as `/private/tmp/fb-neamoi0s/browser-check/browser-check`.
- Lint: skipped (`check_command` is empty).
- C-01: no `http` text in index.html, styles.css, app.js, store.js, tickets.js (grep, plus the slice-04 test).
- Recovery note: historical slice 01/02 git objects are unavailable (see `recovery.md`); slice 01/02 checks are the retained packets/checks plus the fresh full run above. No checks or commits were recreated for them. Slice 03 base/test are recovered checkpoints, not the original commits.

## Visual self-inspection (agent only, not user approval)
Screenshots in `/private/tmp/fb-neamoi0s/work/.tmp/shots/` (untracked): `desktop-list.png`, `desktop-details.png`, `desktop-create-errors.png`, `mobile-list.png`, `mobile-details.png`, `mobile-create-errors.png`.
Seen and fine:
- Desktop 1280x800: all 12 rows visible without scrolling, single-line grid under a ID/TITLE/CUSTOMER/STATUS/PRIORITY header; monospace muted ID, bold title, regular customer, outlined text badges; one filled `New ticket` in the header row.
- Dialogs: headings, bold labels, definition-style details block with badges, red text and red border under invalid fields, filled Save/Create beside a plain Cancel; focus ring visible on the first control.
- Mobile 360x740: no sideways scroll; rows wrap to two lines (ID + title, then customer + badges); both dialogs fit inside the viewport with controls fully visible.
Seen and fixed (commit d661d5c, `styles.css`):
- Filter controls had uneven heights, so the Search label sat a few pixels above the Status and Priority labels: set a common 40px control height (a 1px label offset on the search field remains).
- On mobile the three filters stacked, using about 220px before the list: Status and Priority now share a row, with Search and Reset filters full width.
Not changed: badges use a neutral gray tint and border, with the word carrying the meaning (DESIGN P2); no color tokens were added beyond those in DESIGN.md plus neutral grays `#5b6068` (muted text), `#f3f5f8` (hover/header tint), `#c4c7cc`, `#e1e3e6` (borders), `#6b7280`, `#9aa0a6` (control borders) and `#1d4aa2` (primary hover). DESIGN.md is a gate input and was not edited; these are recorded here for review.
The user has not seen or approved these screens; review must still show them.
