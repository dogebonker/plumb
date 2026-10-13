# Packet: slice 03, inspect-and-edit

Written from: 04-slices.md f66478ef306a0eb9b78e18a69fda9708a8b0acae143023f51d68afd03de450fb, 03-interface.md 0ed380ffd64107cc0d2dd2b93c1cb1fe6fc13555ce623b12aadbd009d8716995

## Goal
### 03 Inspect and edit a ticket

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-08 | Example: "T002 Export stalls at ninety percent" -> dialog shows Northwind, "The monthly CSV export never finishes.", open, high. |
| FR-09 | Example: T001 open -> resolved, save, reload -> T001 shows resolved. |
| FR-10 | Example: change T003 to high, Cancel -> T003 still low. (Cancel and Escape both close without change and return focus to the row button that opened it.) |
| FR-16 (details dialog) | Example: Tab from `Cancel` (last control) -> first field of the dialog. (Shift+Tab wraps the other way.) |
| FR-17 (edit half) | Example: edit T001, create T013, reload -> both present. (This slice: the edit is stored and rebuilt on load.) |
| SYS-NFR-02 (details dialog) | Every action is reachable and operable by keyboard with visible focus; dialogs trap Tab, Escape dismisses and returns focus to the opener. Fit: no keyboard-only dead end; focus cycles inside an open modal. |

## Frozen contract
From `03-interface.md`. They do not change.

### store.js (this slice adds `update` to the Store; `open`, `all`, `filter`, `STATUSES`, `PRIORITIES` exist and stay as they are)
```js
globalThis.TicketStore = {
  STATUSES: ["open", "pending", "resolved"],
  PRIORITIES: ["low", "medium", "high"],
  open(storage = globalThis.localStorage, seeds = globalThis.SEED_TICKETS),   // returns Store
  filter(tickets, {query = "", status = "", priority = ""} = {}),
};
// Store:
//   all(): Ticket[]
//   update(id: string, {status: string, priority: string}): Ticket | null
```
- `open` reads key `support-tickets.v1`. Missing, unparsable or malformed data, or a throwing `storage`, gives the seeds; it never throws for storage problems. Nothing is written until `update` or `create` succeeds. A failed write keeps the change in memory (the `persisted` flag and `#save-warning` are slice 05: do NOT add them here).
- `update` and `create` re-read storage immediately before applying, so two stores over one storage never reuse an ID or drop each other's edits.
- `all` returns a copy in stored order; callers cannot mutate the store.
- `update` persists and returns the updated ticket; `null` for an unknown id; `RangeError` for a status or priority outside `STATUSES`/`PRIORITIES`. Only status and priority change.
- `create` and `persisted` are NOT added in this slice (slices 04, 05).

### app.js (page contract, the part this slice touches)
```html
<dialog id="details-dialog" aria-labelledby="details-title">  <!-- name "Ticket details" -->
  title, customer, description as text; <select id="details-status"> label "Status"; <select id="details-priority"> label "Priority";
  <button type="submit">Save changes</button> <button type="button">Cancel</button>
```
- Dialog headings are not buttons or links, so only the 12 (plus created) row buttons match `T\d{3}`.
- Opening a dialog remembers the opener; on close (Save, Cancel, Escape) focus returns to the opener (the ticket's row button by `data-id`, else `Search tickets`), or to `New ticket`.
- Tab and Shift+Tab wrap between the first and last focusable controls of the open dialog.

Depth (app.js): no exports; the interface is the page. It hides rendering, dialog focus handling, the Tab trap and validation display.

Stub form: plain JavaScript has no kit adapter. A method stub keeps the frozen signature (parameters as written) with the body `throw new Error("not implemented")`. Compile check: `node --check <file>`.

## Context
- Flow 3 (02-architecture.md): a row button opens the shared `Ticket details` `<dialog>` via `showModal()`, filled with `textContent`; `Save changes` calls update, re-renders, closes, and focuses that ticket's row button if still listed (else `Search tickets`). `Cancel` or Escape closes with no write and focuses the opener. Flow 5: a `keydown` handler on each dialog wraps Tab and Shift+Tab between its first and last focusable controls. Decision: native `<dialog>` plus explicit Tab trap; restore focus on `close`.
- Current `store.js` (41 lines): IIFE with `STORAGE_KEY`, `STATUSES`, `PRIORITIES`, `TEXT_FIELDS`, `isValidTicket`, `readStored(storage)` (returns the valid array or null), `copyTicket`; `open()` (`store.js:27-32`) holds `const tickets = readStored(storage) ?? seeds` and returns `{all}`. Add `update` beside `all`: copy the base array (never mutate `seeds`/`SEED_TICKETS`), re-read with `readStored(storage)` right before applying (fall back to the in-memory list), validate status/priority (`RangeError`), return `null` for an unknown id, change only status and priority, write the whole array with `storage.setItem(STORAGE_KEY, JSON.stringify(...))` inside try/catch (a throwing write keeps the change in memory), return a copy via `copyTicket`. Keep the working list in a `let` that `update` replaces so `all()` sees edits.
- Current `app.js` (34 lines): `const tickets = TicketStore.open().all()` at `app.js:5` and `render()` at `app.js:7-25`, which builds `li > button.ticket[data-id]` rows. Change it to keep `const store = TicketStore.open()` and have `render()` read `store.all()`. Add a click handler (delegated on `#tickets` for `button.ticket`) that opens the details dialog. `app.js` never calls `localStorage` itself. User text only via `textContent`/`value`.
- Shared dialog helpers (slice 04 reuses them for `#create-dialog`, so keep them generic: they take the dialog element and an opener or a function that finds the element to focus, and know nothing about tickets): (1) open: remember the opener and `showModal()`; (2) close handler: on the dialog's `close` event (fires for Save, Cancel and Escape) focus the remembered opener, or its fallback when the opener is gone from the DOM; (3) a `keydown` Tab trap bound per dialog that wraps between the first and last focusable controls (query `button, input, select, textarea, [href]` not disabled) for Tab and Shift+Tab. After Save, `render()` replaces the row buttons, so resolve the opener by `data-id` at close time (`#tickets [data-id="T001"]`), else `#search`.
- `index.html:13-25`: no `<dialog>` yet. Add `#details-dialog` inside `<body>` after `</main>`: a `<form novalidate>` (no `method="dialog"`) (styles.css `dialog form` is a grid), `<h2 id="details-title">Ticket details</h2>`, text elements for ID/title, customer and description (e.g. `<p id="details-heading">`, `<p id="details-customer">`, `<p id="details-description">`; plain text, never a button or link), `<label>Status <select id="details-status">` and `<label>Priority <select id="details-priority">` with options from the same values as the filters (no "All" option), and `<div class="actions">` with `<button type="submit">Save changes</button><button type="button" id="details-cancel">Cancel</button>`. The form submit handler calls `store.update`, renders, then `dialog.close()`. Escape closes natively (`cancel` then `close`); the close handler returns focus.
- Words and design (DESIGN.md): dialog title "Ticket details"; actions `Save changes` (the one filled primary action) and `Cancel` (plain) per P3/Positions; do not add a second filled button; description appears only in details; status and priority shown as text in the select values.
- `test_existing.cjs:25-29` needs exactly 12 buttons/links named `T\d{3}` on first load, a T001 opener and label `Search tickets`. Keep it passing; do not edit it. The closed dialog is not in the accessibility tree; its text may contain an ID and title but never a button/link named with `T\d{3}` (C-02).
- `test_dashboard.cjs` (223 lines): `openDashboard({stored})` at `test_dashboard.cjs:42` opens a fresh page (optionally seeding localStorage via init script) and returns `{page, requests}`; `seeds` and `KEY` are defined at the top; tests wrap in try/finally closing the page. Reuse it; add new tests after the existing ones. `test_store.cjs` (173 lines): `fakeStorage(initial)` with `calls.setItem`, `openWith(initial)` returning `{storage, store}`, `seeds()`, `KEY`. Reuse these.
- Seeds (`tickets.js`, unchanged): T001 open, high; T002 "Export stalls at ninety percent", customer Northwind, "The monthly CSV export never finishes.", open, high; T003 pending, low.
- Budgets: SYS-NFR-04 `tickets.js` diff stays empty and the seeds array is not mutated (copy before editing); persistence under the single key `support-tickets.v1`, whole array, written only on a successful update. NFR-01: native controls, no positive `tabindex`, `:focus-visible` outline stays.

## Allowed files
- store.js
- app.js
- index.html
- styles.css
- test_store.cjs
- test_dashboard.cjs

## Layout
Pattern: existing, root: ., check: none. All six files are named by the Layout lines.
- `index.html`: markup, including both `<dialog>` elements and the script tags. No inline script.
- `store.js`: pure ticket logic and the storage adapter, exposed as `globalThis.TicketStore`. May not touch the DOM.
- `app.js`: DOM wiring, rendering, dialogs, focus. Reads and writes tickets only through `TicketStore`; never calls `localStorage` itself.
- `styles.css`: existing styles; extend, do not restructure. No inline styles.
- `test*.cjs`: Node tests (logic) and Playwright tests (browser), run by `browser-check`. `test_existing.cjs` stays unchanged.
- Not allowed: `tickets.js`, `test_existing.cjs`.

## Tests first
Each fails in the red commit, before any implementation exists. Copied from 04-slices.md:
- `test_store.cjs` :: update persists and a reopened store returns it; unknown id returns null; invalid status throws RangeError; two stores over one storage keep both edits - asserts FR-09, FR-17
- `test_dashboard.cjs` :: opening T002 shows title, customer, description, status, priority in "Ticket details"; saving T001 as resolved updates the list and survives reload; Cancel and Escape leave T003 low and return focus to its row button; Tab and Shift+Tab cycle inside the dialog - asserts FR-08, FR-09, FR-10, FR-16

Writing guidance (does not change the lines above): `node:test`, one `test` per clause so each is reported by name. Store tests: after `update("T001", {status:"resolved", priority:"high"})` the returned ticket has those values, `store.all()` shows them, `JSON.parse(storage.getItem(KEY))` holds them, a second `open(storage, seeds)` returns them, other tickets and the order are unchanged, and the seeds array is unmodified; unknown id returns `null` and writes nothing; invalid status and invalid priority throw `RangeError` and write nothing; two stores opened before either edits, one editing T001 and the other T002, end with both edits in a third reopened store. Page tests: `getByRole("dialog", {name: "Ticket details"})` shows T002's title, "Northwind", the description, status select value "open" and priority "high"; save T001 as resolved: the row shows "resolved", reload keeps it, `localStorage[KEY]` holds it; change T003 (low) to high then Cancel, and again then Escape: the row still reads low, the dialog is closed, `document.activeElement` is the T003 row button, and nothing is stored; Tab from the last control (Cancel) lands on the first focusable control and Shift+Tab from the first lands on Cancel. Red commit: `store.js` gets the `update` stub only; leave `app.js`, `index.html`, `styles.css` unchanged. Where a new test would pass against the stub (for example "nothing is stored"), list it in your report; do not change it.

## Verify
- `node --test test_store.cjs`
- `/private/tmp/fb-zt0pwkma/browser-check/browser-check`

Run the second command exactly as written: no arguments, prefix, suffix, pipe, redirect, `cd &&`, semicolon or echo. It runs `node --test` over every `test*.cjs` (so also `test_existing.cjs`, which must stay green) with `PLAYWRIGHT_MODULE` set. Running Chromium tests directly in the ordinary sandbox cannot work. Scratch files only under `/private/tmp/fb-zt0pwkma/work/.tmp`. No network, no installs, no worktrees.

## Rules in scope
No playbook exists. Read before writing code and apply inside the frozen contract.
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md` (pin check passed in slice 01)
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
- Language pack: none (`pack: none` in `lenses.yaml`); skipped.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
- a pre-commit hook rejects the red commit
- a commit fails to sign (never commit unsigned; unsigned local commits are the accepted setup, so this applies only if signing is configured and fails)
- a new test passes against the stub (report it; do not change it)
