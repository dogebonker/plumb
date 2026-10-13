# Architecture: support-ticket-dashboard

## Research
Facts from `research.md` (R1 to R8; Pond not available):
- Classic `defer` scripts, `tickets.js` then `app.js`, no modules, no build, no manifest (R1, R8; `index.html:8-9`).
- `app.js` (14 lines) only renders 12 `li > button.ticket > 3 span` into `#tickets`; the description is not rendered; nothing else is wired (R2, R3; `app.js:1-13`).
- `index.html` already has `#search`, `#status-filter`, `#priority-filter`, `#reset`, `#new-ticket`, `#result-count[role=status]` (hard-coded "12 tickets"), `#tickets`, hidden `#empty-state`; no `<dialog>`, `<form>` or storage anywhere (R3, R4; `index.html:15-23`).
- Seeds are a global `window.SEED_TICKETS`: 12 records, fields id/title/customer/status/priority/description, IDs `T001`..`T012` (R5; `tickets.js:1-14`).
- `styles.css` already styles `dialog`, `dialog form`, `.actions`, `.error`, `:focus-visible` and one `max-width: 600px` query (R6; `styles.css:9,14-20`).
- `test_existing.cjs` needs exactly 12 buttons/links whose name matches `T\d{3}`, a T001 opener, and label `Search tickets` (R7; `test_existing.cjs:25-29`). Nothing else may be a button or link named with `T\d{3}` while the seeds are shown.

## Fit
Small static page; the change fills in behavior behind markup and CSS that already exist and reuses the `#ids`, CSS classes and `window.SEED_TICKETS`. Two new script files split pure logic from DOM wiring so the logic is unit-testable under Node. No new module system, no remote calls (C-01).

## Layout
### . (repository root, static front end)
Pattern: existing, root: ., check: none
- `index.html`: markup, including both `<dialog>` elements and the script tags. No inline script.
- `styles.css`: all styles. No inline styles.
- `tickets.js`: seed data only (`window.SEED_TICKETS`), unchanged. May not read storage or the DOM.
- `store.js`: new. Pure ticket logic and the storage adapter, exposed as `globalThis.TicketStore`. May not touch the DOM.
- `app.js`: DOM wiring, rendering, dialogs, focus. Reads and writes tickets only through `TicketStore`; never calls `localStorage` itself.
- `test*.cjs`: Node tests (logic) and Playwright tests (browser), run by `browser-check`. `test_existing.cjs` stays unchanged.
- Dependency order (the module has no `layers` in `lenses.yaml`, and none is added: five files): `tickets.js` <- `store.js` <- `app.js`; nothing points back.

## Contracts and data
- Ticket: `{id, title, customer, status, priority, description}`, all strings. `status` in `open|pending|resolved`, `priority` in `low|medium|high`. ID format `T` + number padded to 3 digits.
- Storage: one `localStorage` key, `support-tickets.v1`, holding the JSON array of all tickets. Nothing is written until the first save or create, so an untouched browser always shows `tickets.js`. A stored array is accepted only if every item has the six string fields and valid status/priority; otherwise, or when storage throws or is blocked, the seeds are used and edits stay in memory (FR-18).
- `TicketStore`: `load()`, `saveTicket(id, {status, priority})`, `createTicket({title, customer, description, status, priority})` returning `{ok, ticket}` or `{ok:false, errors}`, `filter(tickets, {query, status, priority})`, `countLabel(n)`, `nextId(tickets)`. Exact signatures are decided at the interface gate.
- Filters and open dialog state are not stored (non-goal).

## Flow
1. Load: scripts run in order; `app.js` calls `TicketStore.load()`, renders rows, sets the count and empty state.
2. Filter: `input` and `change` events call `filter()` on the current tickets, re-render, update `#result-count` (live region) and toggle `#empty-state`; `Reset filters` clears the three controls and re-renders without touching storage.
3. Details: a row button opens the shared `Ticket details` `<dialog>` via `showModal()`, filled with `textContent`; `Save changes` calls `saveTicket`, re-renders, closes, and focuses that ticket's row button if still listed (else `Search tickets`). `Cancel` or Escape closes with no write and focuses the opener.
4. New ticket: `New ticket` opens its `<dialog>` with a form. Submit calls `createTicket`: on `errors`, the dialog stays open, each message goes in a `.error` element tied to its field by `aria-describedby` and the field gets `aria-invalid`, and focus moves to the first invalid field. On success: persist, re-render, close, focus `New ticket`. Cancel or Escape discards entered text.
5. Keyboard: a `keydown` handler on each dialog wraps Tab and Shift+Tab between its first and last focusable controls.

## Budgets
- NFR-01 keyboard: every control is a native `button`, `input`, `select`, `textarea`; `:focus-visible` outline stays (3 px, `styles.css:9`); no positive `tabindex`; focus returns to the opener on every dialog dismissal. Checked by browser test.
- NFR-02 layout: at 360 px and 1280 px, `document.documentElement.scrollWidth <= clientWidth`, and each dialog control's bounding box lies inside the viewport horizontally and is reachable by scrolling the dialog vertically.
- NFR-03 text, not color: status and priority exist as visible text in the list and dialogs; error colour is never the only cue.
- SYS-NFR-01 validation: `createTicket` trims before checking; whitespace-only creates nothing (Node test on `store.js`).
- SYS-NFR-04 persistence: after save and create, reload shows the changes; seeds in `tickets.js` are unmodified (`git diff` on `tickets.js` empty).
- All user text is inserted with `textContent` or `value`, never `innerHTML`.

## Constraints
- C-01 vanilla only -> rules out frameworks, bundlers, ES module imports, `fetch`, web fonts and CDNs.
- C-02 fixed accessible names -> rules out renaming or duplicating `New ticket`/`Reset filters` buttons, and any other button or link named with `T\d{3}`.

## Decisions
### Keep the existing flat tree; add `store.js`
Supersedes: none
Context: five files, no framework (R8); `frontend-small` (row L8) is a React/Vite tree and does not fit.
Decision: Pattern `existing`; one new file for pure logic beside `app.js`.
Consequences: logic is testable in Node; two small globals instead of one growing `app.js`. Rejected: everything in `app.js` (needs a browser to test every rule); ES modules (change to the working script setup for no need).

### Domain model: transaction scripts
Supersedes: none
Context: `lenses.yaml` says `crud-service`; the rules are field validation and filtering (FR-03 to FR-14).
Decision: plain functions in `store.js` over plain objects. `lenses.yaml` keeps `domain_model: transaction-scripts`.
Consequences: simplest code. Rejected: ticket classes with invariants, since there are no invariants beyond three required strings.

### Persist the full ticket array under one key, written on first change only
Supersedes: none
Context: R4 (no storage today), FR-02, FR-17, FR-18.
Decision: key `support-tickets.v1` (versioned name), whole array; seeds are the fallback.
Consequences: simple; a seed edit in `tickets.js` does not reach a browser that already saved. Rejected: storing only deltas (merge logic, no gain at 12 records).

### Native `<dialog>` with `showModal()` plus an explicit Tab trap
Supersedes: none
Context: the task asks for modal semantics, Escape and Tab cycling; native `showModal` makes the rest of the page inert and handles Escape and `::backdrop` (CSS exists, R6).
Decision: native dialogs; add a keydown trap so Tab cycles inside regardless of the browser; restore focus on `close`.
Consequences: little code and real semantics. Rejected: `div role=dialog` (focus, inertness and Escape all hand-built).

### New IDs: next number after the highest existing `T###`
Supersedes: none
Context: FR-14 needs unique IDs; no deletion exists.
Decision: `nextId` = `T` + (max numeric suffix + 1) padded to 3, over loaded tickets.
Consequences: first new ticket is `T013`; stable while there is no deletion. Rejected: random or time-based IDs (unlike the seeds).

## Open questions
