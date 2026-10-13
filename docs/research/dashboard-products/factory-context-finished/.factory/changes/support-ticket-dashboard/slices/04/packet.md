# Packet: slice 04, hierarchy-360-names

Written from: 04-slices.md c76bed07883e0b17c6c4023b7c1c1832c6a1fc0a9e88e5a4955679e1c770847e, 03-interface.md 1beada6addd868a7b96847b6dccfd3c5508387fce307c7baf8b688afc9f04c54

## Goal
04 Hierarchy, 360 px fit and stable names

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-21 | WHEN the viewport is 360x740, the page has no horizontal overflow and dialog controls are inside the viewport (Test plan: `test_dashboard.cjs` :: at 360x740 the page has no horizontal overflow and dialog controls are inside the viewport). Statement: The system SHALL fit a 360 px wide viewport with no sideways page scroll and no clipped dialog control, and keep every action usable by keyboard. |
| NFR-02 | Every control has a visible name; errors and counts are announced, not shown by color alone. (`test_dashboard.cjs` :: controls found by role and accessible name; error text found through aria-describedby; count read from the status role) |
| C-01 | Vanilla HTML, CSS and JavaScript only; no dependencies, backend, remote requests or external assets. (human-verified: grep for `http` in source files; slice 04 also adds a test) |
| C-02 | The twelve seeded records stay in `tickets.js` with their IDs and values. (`tickets.js` is not an Allowed file.) |
| C-03 | Stable names: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`. (`test_dashboard.cjs` :: every stable name from the task is found by role and name) |

Constraint registry (`.factory/system/constraints.md`): only SYS-NFR-01 (required fields trimmed and validated before store); slice 04 does not touch it.

## Frozen contract
No signatures change. `03-interface.md` app.js contract (the DOM, checked by role and accessible name) is frozen and must keep holding:
- `button` named `<ID> <title> ...` for each ticket (accessible name contains the ID and title); `searchbox`/textbox `Search tickets`; comboboxes `Status filter`, `Priority filter`; buttons `Reset filters`, `New ticket`; `status` region with the count text `N tickets` / `1 ticket`.
- `dialog` named `Ticket details` with textboxes/comboboxes labelled `Status`, `Priority` and buttons `Save changes`, `Cancel`; `dialog` named `New ticket` with `Title`, `Customer`, `Description`, `Status`, `Priority`, `Create ticket`, `Cancel`.
- An invalid field has `aria-invalid="true"` and an `aria-describedby` target whose text is the error.

`store.js` (TicketStore.open/list/get/update/create) is untouched. Stub form: not needed (no new signatures).

Preserve every behaviour of the current approved code (slices 01-03). Rows may be restructured, but `app.js` must identify the clicked ticket and restore focus by a `data-id` attribute on the ticket button, not by `button.textContent` parsing.

## Context
- Seed data is `window.SEED_TICKETS`, twelve records `id, title, customer, status, priority, description` (tickets.js:1-14).
- Scripts are classic `defer` scripts tickets.js, store.js, app.js (index.html).
- `test_existing.cjs` finds ticket buttons by role and `/T\d{3}/` (test_existing.cjs:6-29); never edit it.
- Today `app.js` finds the clicked ticket through `button.textContent.split(" ")[0]` and restores focus through `textContent.startsWith`; switch both to `data-id`.
- `DESIGN.md` is a gate input and is NOT edited. If new tokens need recording, put a short note in `slices/04/checks.md`.

DESIGN.md (copied, relevant):
- P1 Scanning over decoration: at 1280 px, at least ten tickets visible without scrolling and each row's five fields readable left to right. Rules out card grids with large padding, per-row icons or avatars, summary tiles.
- P2 Status carried by words, not color alone: with the page in grayscale every status and priority is told apart by its text. Rules out color-only badges.
- P3 One main action per surface: each dialog shows one visually dominant button, the commit (`Save changes` / `Create ticket`); `Cancel` is plain. The list's single filled button is `New ticket` in the page header row; `Reset filters` is plain.
- P4 Honest, named states: results "N tickets"; no match "No tickets match your filters."; invalid field shows red text beneath the field naming what is missing, dialog still open.
- Colors: Neutral text on white. The blue focus color (#245ac5) marks keyboard focus and the one primary button. Red (#a01818) only for validation errors, always with text. No other accent.
- Typography: system UI sans-serif. Ticket title is the heaviest weight in a row; customer and status/priority are regular weight (badges are text labels).
- Don't: summary tiles, charts, illustrations; color-only status/priority; page scrolling sideways at 360 px (long words wrap); no per-row icons.

## Allowed files
- `styles.css`
- `index.html`
- `app.js`
- `test_dashboard.cjs`
- `test_review.cjs` (review regression tests)

## Layout
Pattern: existing, root: . (flat tree)
- `index.html`: the page, its controls and both dialogs; no inline script.
- `styles.css`: all styling; no rules for markup that does not exist.
- `app.js`: DOM rendering and event wiring. No storage calls and no business rules.
- `test*.cjs`: Node tests; browser ones are run by the browser-check wrapper.
- `tickets.js`, `store.js`: existing, not Allowed here.

## Tests first
Append slice-04 tests to `test_dashboard.cjs` only (keep earlier tests exactly as they are). Each fails in the red commit (against the current unstyled/old-row markup).
- 360x740 no overflow: `document.documentElement.scrollWidth <= innerWidth` on the list; with each of the two dialogs open (the new-ticket one after an empty submit so errors show) every dialog control's bounding box is within the viewport horizontally and the dialog fits (FR-21).
- 360x740 compact rows: ticket rows do not overflow horizontally; customer, status and priority text of the first row are visible and inside the viewport.
- 1280 row hierarchy: for the first ticket row, the ID element is left of the title element; the title's computed font-weight is >= 600 and strictly heavier than customer, status and priority text, and its font-size >= the customer's; ID is muted/monospace in a fixed-width column; customer, status and priority text are visible inside the row's box (DESIGN P1, P2).
- 1280x800: at least ten ticket rows lie entirely within the first viewport without scrolling (DESIGN P1).
- Status and priority are text: the first row contains the words of its status and priority (DESIGN P2).
- Stable names: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters` found by role+name; the `Ticket details` and `New ticket` dialogs found by role+name; labels Title, Customer, Description, Status, Priority; buttons Save changes, Create ticket, Cancel; each ticket button's accessible name contains its ID and title (C-03, NFR-02).
- One filled primary button: the page has `New ticket` as the only filled button on the list screen (distinct background from `Reset filters`); in each dialog the commit button's background differs from `Cancel`'s (DESIGN P3).
- No remote URL: none of `index.html`, `styles.css`, `app.js`, `store.js`, `tickets.js` contains `http` followed by `://`... (simply: no `http://` or `https://`) (C-01).

## Additional implementation requirements (operator, visual hierarchy; the previous screenshots were called "horrible")
Within the four Allowed files:
- Compact, readable ticket rows: ID (monospace, muted, fixed-width column) + title bold as the dominant element, customer secondary, status and priority as visible TEXT badges (words, not color alone; may add a subtle tinted background/border plus the text label; no emoji, icons or external assets). At 1280 px rows are a single-line grid (ID | title | customer | status | priority) with a column header row or labelled text; at 360 px they wrap into a compact two-line layout with no horizontal overflow. At least ten rows visible without scrolling at 1280x~800.
- Typography scale (h1, row title, meta, labels), consistent spacing; page header row with the h1 and the single filled primary button `New ticket`; filter bar in a tidy responsive grid with visible labels; `Reset filters` a plain secondary button; result count as muted text; styled empty state; styled dialog headings, field labels, error messages (text below fields, red border on `aria-invalid="true"`), dialog actions with Save/Create filled primary and Cancel plain; row hover and a clear visible focus outline; the details dialog shows its fields as a labelled definition-style block (title, customer, description) with status/priority badges.
- Keep every accessible name stable (see Frozen contract). If a column header row is added, it must not be exposed as extra buttons and must not change the list's role/name semantics that earlier tests rely on (hide purely decorative duplicates with `aria-hidden` only if the visible text remains available by another accessible route).
- No fake metrics, no remote URLs, no dependencies, no new files except (optional, after green) `test_screens.cjs`, see below.

## Optional screenshots
After green, a `test_screens.cjs` may be added (same inline static-server pattern, `PLAYWRIGHT_MODULE`) writing PNGs to `/private/tmp/fb-neamoi0s/work/.tmp/shots/` (desktop 1280x800 list, desktop details dialog, desktop new-ticket dialog with validation errors, mobile 360x740 list, mobile details, mobile create with errors). It asserts nothing flaky. `.tmp` stays untracked. This file is committed only in the polish stage if the orchestrator says so; it is admitted by the operator's instruction.

## Verify
- `/private/tmp/fb-neamoi0s/browser-check/browser-check`
- `node --test test_store.cjs`

Run the browser check as EXACTLY that, the whole Bash command: no arguments, prefixes, suffixes, pipes, redirects, semicolons or echo; use a generous Bash timeout (failing Playwright tests wait 30 s each). It runs `node --test` over `test*.cjs` in the workspace. Never edit `test_existing.cjs`; it must stay green. Existing: 35 browser tests, 17 store tests.

## Red commit notes
- Expected red result: every new slice-04 test above fails (report any that pass against the current markup); all earlier tests and `test_existing.cjs` pass.
- Commit messages: `test(support-ticket-dashboard): slice 04 red`, then `feat(support-ticket-dashboard): slice 04`. Stage by path, only Allowed files. Use the repo's git user; no signing is configured; unsigned synthetic commits are permitted by operator policy.
- Historical slice 01/02 git objects are gone (see `recovery.md`); this does not affect slice 04.

## Rules in scope
- Playbook: none.
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md`
- Language pack: none.
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.

## Operator constraints (this benchmark)
No external network, remote git operations, dependency installs, production changes, or git worktrees. Serve only on 127.0.0.1. Keep every scratch file under `/private/tmp/fb-neamoi0s/work/.tmp` (never `/tmp`). Never edit `test_existing.cjs`, `tickets.js`, `store.js`, `DESIGN.md`, `.factory/` or any skill or kit snapshot. Do not commit `.factory/` or `.tmp/`. Do not request a sandbox bypass.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
- a pre-commit hook rejects the red commit
