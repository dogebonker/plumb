# Packet: slice 02, find-tickets

Written from: 04-slices.md f66478ef306a0eb9b78e18a69fda9708a8b0acae143023f51d68afd03de450fb, 03-interface.md 0ed380ffd64107cc0d2dd2b93c1cb1fe6fc13555ce623b12aadbd009d8716995

## Goal
### 02 Find tickets: search, filters, count, empty state, reset

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-03 | Example: "acme" -> T001, T005, T011 (customer Acme Labs); "EXPORT" -> T002. |
| FR-04 | Example: "acme" + status pending + priority medium -> T005 only. |
| FR-05 | Example: filter status resolved -> "3 tickets"; one match -> "1 ticket". |
| FR-06 | Example: search "zzz" -> empty message, no rows. (Text "No tickets match your filters." and count "0 tickets".) |
| FR-07 | Example: after "zzz", reset -> all tickets again, search empty. (Stored tickets unchanged.) |

## Frozen contract
From `03-interface.md`. They do not change.

### store.js (this slice adds `filter`; `open`, `all`, `STATUSES`, `PRIORITIES` already exist from slice 01 and stay as they are)
```js
globalThis.TicketStore = {
  STATUSES: ["open", "pending", "resolved"],
  PRIORITIES: ["low", "medium", "high"],
  open(storage = globalThis.localStorage, seeds = globalThis.SEED_TICKETS),
  /** @returns {Ticket[]} */
  filter(tickets, {query = "", status = "", priority = ""} = {}),
};
```
- `filter` matches title or customer by case-insensitive substring of `query` trimmed of surrounding whitespace, AND exact `status` and `priority`; `""` means any. Pure; preserves order. Does not mutate `tickets`.
- `update`, `create` and `persisted` are NOT added in this slice (slices 03, 04, 05).

### app.js (page contract, the part this slice touches)
```html
<input id="search" type="search">  <!-- label "Search tickets" -->
<select id="status-filter" aria-label="Status filter">  <select id="priority-filter" aria-label="Priority filter">
<button id="reset">Reset filters</button>
<p id="result-count" role="status">12 tickets</p>   <!-- "N tickets", "1 ticket" -->
<ul id="tickets"><li><button class="ticket" data-id="T001"> ID title / customer / status · priority </button></li></ul>
<p id="empty-state">No tickets match your filters.</p>   <!-- hidden unless 0 matches -->
```
Depth (app.js): no exports; the interface is the page. It hides rendering, dialog focus handling, the Tab trap and validation display.

Stub form: plain JavaScript has no kit adapter. A function or method stub keeps the frozen signature (parameters and defaults as written) with the body `throw new Error("not implemented")`. Compile check: `node --check <file>`.

## Context
- Flow (02-architecture.md Flow 2): `input` and `change` events call `filter()` on the current tickets, re-render, update `#result-count` (live region) and toggle `#empty-state`; `Reset filters` clears the three controls and re-renders without touching storage. Filters are not stored.
- Current `store.js` (slice 01, IIFE with `STATUSES`, `PRIORITIES`, `isValidTicket`, `readStored`, `copyTicket`, `TicketStore.open`): add `filter` as a sibling of `open`. Reuse nothing new; no parallel helpers.
- Current `app.js` (14 lines, `app.js:1-18`): builds `li > button.ticket > 3 span` for each ticket in a top-level loop and sets the count text once. Turn that loop into a `render()` over `TicketStore.filter(tickets, criteria)` that clears `#tickets` (`replaceChildren`), keeps the same row markup (`data-id`, span texts `` `${id} ${title}` ``, customer, `` `${status} · ${priority}` ``), sets `#result-count` ("1 ticket" / "N tickets", `app.js:3`) and sets `#empty-state.hidden = matches.length > 0`. Call it once on load and on `input` of `#search` and `change` of both selects; `#reset` sets the three controls to `""` and calls `render()`. User text only via `textContent`/`value`. `app.js` never calls `localStorage` itself.
- `index.html:15-23`: `#result-count` holds a hard-coded "12 tickets" (the review of slice 01 left it: the slice-02 re-render owns the count; it may stay as the initial markup or be emptied) and `#empty-state` is `hidden`. The select options are `<option>open</option>` etc. with `""` for all values.
- `test_existing.cjs:25-29` needs exactly 12 buttons/links named `T\d{3}` on first load, a T001 opener and label `Search tickets`. Keep it passing; do not edit it. Label `Search tickets` must stay on `#search`; `New ticket` and `Reset filters` buttons are not renamed or duplicated (C-02).
- `test_dashboard.cjs` (122 lines from slice 01): `test.before` launches Chromium and the 127.0.0.1 server once; a helper at `test_dashboard.cjs:42` opens the dashboard in a fresh page (optionally with `stored` in localStorage). Reuse that helper; add new tests after the existing ones. `test_store.cjs` (124 lines) has an in-memory fake storage and loads `tickets.js` then `store.js` with `globalThis.window = globalThis`; reuse that setup.
- `styles.css` is allowed (`.filters`, `#tickets`, `.ticket`, `.error` and one `max-width: 600px` query exist; `:focus-visible` outline stays). DESIGN.md: empty state shows "No tickets match your filters." with `Reset filters` available; the count is always visible text. Add a style only if the empty state or count needs one; use the tokens already in `styles.css`.
- Seeds (`tickets.js`, unchanged): T001, T005, T011 customer Acme Labs; T002 title contains "export"; resolved count is 3; T005 is Acme + pending + medium.
- Budgets: SYS-NFR-04 `tickets.js` diff stays empty; nothing is written to storage in this slice. Dependency order `tickets.js` <- `store.js` <- `app.js`.

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
- `styles.css`: existing styles; extend, do not restructure.
- `test*.cjs`: Node tests (logic) and Playwright tests (browser), run by `browser-check`. `test_existing.cjs` stays unchanged.
- Not allowed: `tickets.js`, `test_existing.cjs`.

## Tests first
Each fails in the red commit, before any implementation exists. Copied from 04-slices.md:
- `test_store.cjs` :: filter "acme" returns T001, T005, T011 and "EXPORT" returns T002; filter combines query, status and priority with AND (acme+pending+medium returns T005); surrounding whitespace of the query is ignored - asserts FR-03, FR-04
- `test_dashboard.cjs` :: typing narrows the list; result count in the status region reads "3 tickets" for resolved and "1 ticket" for one match; no match shows "No tickets match your filters." and "0 tickets"; Reset filters clears all three controls and leaves stored tickets unchanged - asserts FR-03 to FR-07

Writing guidance (does not change the lines above): use `node:test`, one `test` per clause so each is reported by name. Assert outcomes: the exact ID lists in order (from `.ticket` `data-id`s), the exact count text in `#result-count`, `#empty-state` visible with the exact text and zero rows, after Reset the 12 rows, empty search, both selects at `""`, and `localStorage["support-tickets.v1"]` still unset (nothing written). In `test_store.cjs` also assert `filter` does not mutate its input and `status`/`priority` alone filter. Red commit: `store.js` gets the `filter` stub only; leave `app.js`, `index.html`, `styles.css` unchanged. Where a new test would pass against the stub, list it in your report; do not change it.

## Verify
- `node --test test_store.cjs`
- `/private/tmp/fb-zt0pwkma/browser-check/browser-check`

Run the second command exactly as written: no arguments, prefix, suffix, pipe, redirect, `cd &&`, semicolon or echo. It runs `node --test` over every `test*.cjs` (so also `test_existing.cjs`, which must stay green) with `PLAYWRIGHT_MODULE` set. Running Chromium tests directly in the ordinary sandbox cannot work. Scratch files only under `/private/tmp/fb-zt0pwkma/work/.tmp`.

## Rules in scope
No playbook exists. Read before writing code and apply inside the frozen contract.
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md` (pin check passed in slice 01: hash 7a746649e5eb77326cf54d381adf030994f4e311)
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
- Language pack: none (`pack: none` in `lenses.yaml`); skipped.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
- a pre-commit hook rejects the red commit
- a commit fails to sign (never commit unsigned; the operator accepts unsigned local commits as the configured setup, so this applies only if signing is configured and fails)
