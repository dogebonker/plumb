# Architecture: support-ticket-dashboard

## Research
Facts from `research.md` (answer number in brackets):
- Seed data is the global `window.SEED_TICKETS`, twelve records with `id`, `title`, `customer`, `status`, `priority`, `description` (tickets.js:1-14) [1].
- app.js is 14 lines: it renders one `button.ticket` per record, with three spans (`"<id> <title>"`, customer, `"<status> · <priority>"`); no handlers, filtering or storage (app.js:1-13) [2].
- index.html already holds the controls with the required names: `#search` (label `Search tickets`), `#status-filter`, `#priority-filter`, `#reset`, `#new-ticket`, `p#result-count[role=status]`, `ul#tickets`, hidden `p#empty-state` (index.html:15-23). No `<dialog>`, `<form>` or `<textarea>` exist [3][6].
- Scripts load as classic `defer` scripts in order tickets.js, app.js (index.html:8-9) [3].
- styles.css has one breakpoint (600 px), one focus rule (`:focus-visible`, 3 px), and unused dialog, `.actions` and `.error` rules (styles.css:9, 14-20) [4].
- No `localStorage`, `sessionStorage`, `indexedDB` or `<dialog>` is used anywhere [6].
- `test_existing.cjs` finds ticket buttons by role and `/T\d{3}/`, serves files with a Node static server, and needs `PLAYWRIGHT_MODULE` (test_existing.cjs:6-29) [5].
- Ticket IDs are `T` plus three digits, `T001` to `T012`; value sets match the filter options (tickets.js:2-13, index.html:16-17) [7].
- Pond: not found; no Pond tools in this session [8].

## Fit
A static page with no build, so the change lives in the existing files and adds one:
- `index.html` gains two `<dialog>` elements and a `<script src="store.js">` before `app.js`.
- `store.js` (new) holds all ticket rules and storage with no DOM access.
- `app.js` becomes the UI layer: render, events, dialogs, focus.
- `styles.css` reuses the existing dialog, `.actions` and `.error` rules and gains hierarchy styles.
- `tickets.js` stays untouched (C-02). It is the seed and the fallback.

## Layout
### .
Pattern: existing, root: ., check: none
- `index.html`: the page, its controls and both dialogs; no inline script.
- `styles.css`: all styling; no rules for markup that does not exist.
- `tickets.js`: seed data only (`window.SEED_TICKETS`); never edited at runtime.
- `store.js`: pure ticket logic and storage (load, save, filter, validate, create, update). No `document` access.
- `app.js`: DOM rendering and event wiring. No storage calls and no business rules; it calls `TicketStore`.
- `test*.cjs`: Node tests; the browser ones are run by the browser-check wrapper.

No `layers` in `lenses.yaml` apply (profile crud-service, flat tree), so there is no checker. Rule kept by review: `app.js` does not touch `localStorage`; `store.js` does not touch `document`.

## Contracts and data
- Storage: `localStorage` key `support-tickets.v1` holds a JSON array of ticket records, each `{id, title, customer, status, priority, description}`, all strings. Same origin only.
- Load: if the key is missing, not JSON, not an array, or any record has a missing field or a status or priority outside the supported sets, return a copy of `SEED_TICKETS` (FR-03). Nothing is written on load, so the first visit leaves storage empty until the first change.
- Save: every mutation writes the whole array synchronously (`setItem`), then re-renders. A storage exception (quota, disabled) is caught: the in-memory list still works for the session, and the page shows no error (non-goal: reporting storage failure).
- IDs: `T` + zero-padded number, three digits minimum. New ID = highest numeric part of all current IDs + 1. Nothing is ever deleted, so IDs are never reused.
- No external contract, no migration. The `.v1` suffix lets a later change migrate.
- `TicketStore` surface (signatures belong to the interface gate): load, filter by (query, status, priority), update status and priority, validate and create a ticket.

## Flow
1. Page load: `tickets.js`, `store.js`, `app.js` run in order. `app.js` calls `TicketStore.load()`, holds the array in memory with the filter state (search text, status, priority), and renders.
2. Render: `TicketStore.filter` gives the visible list; `app.js` rebuilds `ul#tickets`, sets `#result-count` text, and shows or hides `#empty-state` and the list.
3. Filter input (`input` and `change` events) updates the filter state and re-renders. `Reset filters` clears the state and the control values; stored tickets are untouched.
4. Open details: a ticket button records itself as the opener (by ticket ID), fills the `Ticket details` dialog and calls `showModal()`.
5. `Save changes`: `TicketStore.update` returns the new array, `app.js` persists through the store, closes the dialog, re-renders and restores focus.
6. `New ticket`: opens the `New ticket` dialog with the form reset. Submit trims, `TicketStore.validate` returns per-field errors; errors render in `.error` elements wired by `aria-describedby`, `aria-invalid` is set, the dialog stays open, and focus moves to the first invalid field. Valid input is created and stored, then the dialog closes and focus is restored.
7. Cancel and Escape close either dialog without writing. Escape is handled on the dialog's `cancel` event so one path closes and restores focus.
8. Tab and Shift+Tab: a `keydown` handler on each open dialog wraps focus between its first and last focusable control (FR-19).

## Budgets
- NFR-01 (nothing saved is lost on reload) -> every mutation calls `setItem` before the next render; a browser test saves a change, reloads and finds it, for an edit and for a create.
- NFR-02 (visible names, announced counts and errors) -> the count lives in the existing `role=status` element and is updated on every list change; each error is text linked to its field with `aria-describedby`; axe-style checks are not available, so a browser test reads accessible names and descriptions through role queries.
- Page size and speed: all work is synchronous over tens of tickets; no measured budget needed.

## Constraints
- C-01 (vanilla only, no dependency) -> rules out a framework, a bundler, ES-module imports that need a server MIME configuration, and remote fonts. Classic `defer` scripts stay.
- C-02 (seeds stay in tickets.js) -> rules out moving or editing the records; storage holds a copy.
- C-03 (stable names) -> rules out renaming existing labels; new dialogs take their names from `aria-labelledby` headings with the exact text.
- SYS-NFR-01 (trim and validate before store) -> `TicketStore.create` trims and validates, and returns no ticket on error; `app.js` cannot store a ticket any other way.

## Decisions
### Flat tree with a pure store module
Supersedes: none
Context: five files, no build (research 1-5). Profile crud-service and `domain_model: transaction-scripts` in `lenses.yaml`. The layout rules favor an existing convention.
Decision: keep the flat tree (`Pattern: existing`), add `store.js` for rules and storage, keep `app.js` for DOM. `store.js` exposes `window.TicketStore` and, when `module` exists, `module.exports`, so Node tests run the rules without a browser.
Consequences: the rules get fast Node tests and the UI gets browser tests. Two globals (`SEED_TICKETS`, `TicketStore`) instead of modules. Rejected: one big `app.js` (rules testable only through a browser) and ES modules (the smoke server and `http.server` serve them, but C-01 prefers the current script style).

### Transaction scripts, no rich domain model
Supersedes: none
Context: a ticket has two editable fields and three required text fields; no invariants beyond membership in value sets and non-empty text.
Decision: plain record objects and functions in `store.js`; `domain_model: transaction-scripts` in `lenses.yaml` stays.
Consequences: simple. If rules grow (assignment, SLAs), revisit. Rejected: a Ticket class with behavior.

### Storage: one JSON array under a versioned key
Supersedes: none
Context: data fits a few kilobytes; the operator only needs reload persistence on one origin (NFR-01).
Decision: one `support-tickets.v1` array, read at load and fully rewritten on each change; unreadable data falls back to the seed; nothing written until the first change.
Consequences: simple and atomic per write. Last-write-wins across two tabs (non-goal). Rejected: storing only the diff from the seed (a corrupted diff is harder to recover from; edits to seed fields would need merge rules) and `indexedDB` (async, no benefit at this size).

### Native `<dialog>` with `showModal()` plus a manual Tab wrap and explicit focus return
Supersedes: none
Context: required: modal semantics, Tab cycling inside, Escape dismisses without saving, focus returns to the opener (Product FR-19, FR-20).
Decision: use `<dialog>` with `aria-labelledby`, rely on it for modality, inert background and Escape's `cancel` event, but wrap Tab ourselves and restore focus ourselves, because browsers differ in whether Tab leaves the dialog for browser UI and in where focus lands after close.
Consequences: small handler duplicated across two dialogs, shared as one function. If the opener ticket no longer matches the filters after a save, focus falls back to `Search tickets` (Product FR-20 applies to a control that still exists). Rejected: custom `div role=dialog` (needs inert handling and a trap for everything) and trusting native focus return.

### Validation messages: text beside each field, linked by id
Supersedes: none
Context: invalid input must name the field and be tied to it for assistive technology (FR-15).
Decision: forms use `novalidate`; each field has a `.error` paragraph referenced by `aria-describedby`; `aria-invalid="true"` is set only while the error shows; the first invalid field gets focus. Rejected: native browser bubbles (unstyleable, not reliably exposed, and they skip the trim rule).
Consequences: more markup; full control over wording and tests.

## Open questions
