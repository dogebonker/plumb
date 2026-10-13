# Packet: slice 01, tracer-list-and-filters

Written from: 04-slices.md c76bed07883e0b17c6c4023b7c1c1832c6a1fc0a9e88e5a4955679e1c770847e, 03-interface.md 1beada6addd868a7b96847b6dccfd3c5508387fce307c7baf8b688afc9f04c54

## Goal
01 Tracer: list and filters from the store

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-01 | first visit -> 12 rows; T001 reads "Password reset link expired", Acme Labs, open, high. |
| FR-03 | stored value is `not json` -> 12 seeded rows, no crash. |
| FR-04 | "acme" -> T001, T005, T011 (customer Acme Labs). "RESET" -> T001 (title). "expired link" -> none (not a substring). |
| FR-05 | status `pending` -> T003, T005, T006, T010; back to "All statuses" -> 12. |
| FR-06 | "acme" + `open` + `high` -> T001 only. "acme" + `resolved` + `low` -> none. |
| FR-07 | "zzz" -> "0 tickets" announced and the empty message shown; clearing the search -> "12 tickets", message gone. |
| FR-08 | "acme" + `open`, then Reset -> empty search, "All statuses", "All priorities", 12 tickets. |

Full FR text (from `01-product.md`):
- FR-01: WHEN the page opens for the first time on an origin, the system SHALL list the twelve seeded tickets T001 to T012 with their ID, title, customer, status and priority.
- FR-03: IF the saved tickets are missing or unreadable THEN the system SHALL show the twelve seeded tickets.
- FR-04: WHEN the operator types in `Search tickets`, the system SHALL list only tickets whose title or customer contains the text, ignoring letter case.
- FR-05: WHEN the operator picks a value in `Status filter` or `Priority filter`, the system SHALL list only tickets with that value; the all-values option removes that filter.
- FR-06: The system SHALL combine search, status and priority with AND.
- FR-07: WHEN the visible list changes, the system SHALL show "N tickets" (or "1 ticket") in a live status region; WHEN no ticket matches, it SHALL also show "No tickets match your filters." in place of the list.
- FR-08: WHEN the operator activates `Reset filters`, the system SHALL clear the search text, set both filters to all, and show every ticket, leaving stored tickets unchanged.

Constraints in force (from `01-product.md`; slice 04 owns their tests, but this slice must not break them):
- C-01: Vanilla HTML, CSS and JavaScript only; no dependencies, backend, remote requests or external assets.
- C-02: The twelve seeded records stay in `tickets.js` with their IDs and values. `tickets.js` is never edited.
- C-03: Stable names: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`.
- NFR-02: Every control has a visible name; counts are announced (the count lives in the `role=status` element), not shown by color alone.

## Frozen contract
Copied from `03-interface.md`. They do not change.

### store.js
Depth: hides storage format and key, seed fallback, shape validation, trimming and required-field rules, ID allocation, filter matching and persistence behind one repository object.
Cost: 5 public methods (`open`, `list`, `get`, `update`, `create`) + 2 constants, 7 parameters, 3 error variants exposed (one per required field) + 1 thrown `RangeError` + 1 `undefined` result (unknown ID), 0 configuration options exposed, 0 pass-through methods

```js
/** @typedef {"open"|"pending"|"resolved"} Status */
/** @typedef {"low"|"medium"|"high"} Priority */
/** @typedef {{id: string, title: string, customer: string, status: Status, priority: Priority, description: string}} Ticket */
/** @typedef {{query?: string, status?: string, priority?: string}} TicketFilter */
/** @typedef {{title: string, customer: string, description: string, status: Status, priority: Priority}} NewTicket */
/** @typedef {{title?: string, customer?: string, description?: string}} FieldErrors */

window.TicketStore = {
  STATUSES: ["open", "pending", "resolved"],
  PRIORITIES: ["low", "medium", "high"],

  /** @param {Storage} storage @param {Ticket[]} seed @returns {TicketRepo} */
  open(storage, seed) {},
};

/** @typedef {object} TicketRepo */
TicketRepo.list(filter)    // (filter?: TicketFilter) => Ticket[]
TicketRepo.get(id)         // (id: string) => Ticket | undefined
TicketRepo.update(id, changes) // (id: string, changes: {status?: string, priority?: string}) => Ticket | undefined
TicketRepo.create(input)   // (input: NewTicket) => {ticket: Ticket} | {errors: FieldErrors}
```
- `open` reads `support-tickets.v1`; when it is missing or unreadable (not JSON, not an array, a record with a missing field or a status or priority outside the sets) the repo holds a copy of `seed`. It writes nothing until the first change. Every write (`update`, `create`) first re-reads `support-tickets.v1` (when readable and valid) so a change made by another tab on the same origin is kept; when storage is unreadable the repo's in-memory list is used. A storage that throws on read or write never makes `open` or any method throw: the repo keeps working in memory.
- `list` returns tickets in stored order. `query` matches title or customer as a case-insensitive substring (the query is used as typed, not trimmed); empty or missing `query`, `status` or `priority` means no restriction. Criteria combine with AND. It returns copies; callers cannot change stored data through them.
- `get` returns a copy of the ticket, or `undefined` for an unknown ID.
- `update` re-reads storage, then changes only the status and/or priority named in `changes`, stores the result and returns the updated copy. It returns `undefined` (unknown ID) and stores nothing. A given status or priority outside the sets is a programming error: it throws a `RangeError` and stores nothing.
- `create` trims `title`, `customer` and `description`. If any trimmed value is empty it returns `{errors}` with one entry per empty field (`"Title is required"`, `"Customer is required"`, `"Description is required"`) and stores nothing. Otherwise it re-reads storage and stores a ticket with the next unused ID taken from that fresh data (`T` + number, at least three digits; highest existing number + 1), the trimmed text and the given status and priority, and returns `{ticket}`. A status or priority outside the sets is a programming error: `create` throws a `RangeError`.

Scope of this slice: it implements `STATUSES`, `PRIORITIES`, `open` and `list` for real. `get`, `update` and `create` are on the returned repo as stubs that throw `Error("stub")` until slices 02 and 03 implement them. Export for Node as the architecture decision says: `window.TicketStore` in the browser and, when `module` exists, `module.exports = TicketStore` so `test_store.cjs` can `require("./store.js")`. `store.js` must work when loaded in Node, where `window` is undefined (use `globalThis` or guard on `typeof window`).

### app.js
Depth: wires DOM events to `TicketStore`; no exports.
Cost: 0 public methods, 0 parameters, 0 error variants exposed, 0 configuration options exposed, 0 pass-through methods

Entry script run after `store.js`; it exposes nothing. Its contract is the DOM, which browser tests check by role and accessible name (stable names from `01-product.md` C-03):
- `button` named `<ID> <title> ...` for each ticket (accessible name contains the ID and title); `searchbox`/textbox `Search tickets`; comboboxes `Status filter`, `Priority filter`; buttons `Reset filters`, `New ticket`; `status` region with the count text `N tickets` / `1 ticket`.
- (Slices 02 and 03 add the dialogs; not in this slice.)

Stub form: javascript has no adapter file; use the TypeScript adapter's Stubs rule (`kit/adapters/typescript.md`): types and interfaces exactly as written; functions and methods keep the frozen signature with the body `throw new Error("stub");`; imports: whatever the signatures need, from the paths the module already uses.

## Context
Research facts this slice needs (from `02-architecture.md`, `research.md` in brackets):
- Seed data is the global `window.SEED_TICKETS`, twelve records with `id`, `title`, `customer`, `status`, `priority`, `description` (tickets.js:1-14) [1].
- app.js is 14 lines: it renders one `button.ticket` per record, with three spans (`"<id> <title>"`, customer, `"<status> · <priority>"`); no handlers, filtering or storage (app.js:1-13) [2].
- index.html already holds the controls with the required names: `#search` (label `Search tickets`), `#status-filter`, `#priority-filter`, `#reset`, `#new-ticket`, `p#result-count[role=status]`, `ul#tickets`, hidden `p#empty-state` (index.html:15-23). No `<dialog>`, `<form>` or `<textarea>` exist [3][6].
- Scripts load as classic `defer` scripts in order tickets.js, app.js (index.html:8-9) [3]. This slice inserts `<script src="store.js" defer></script>` between them.
- styles.css has one breakpoint (600 px), one focus rule (`:focus-visible`, 3 px), and unused dialog, `.actions` and `.error` rules (styles.css:9, 14-20) [4].
- No `localStorage`, `sessionStorage`, `indexedDB` or `<dialog>` is used anywhere [6].
- `test_existing.cjs` finds ticket buttons by role and `/T\d{3}/`, serves files with a Node static server, and needs `PLAYWRIGHT_MODULE` (test_existing.cjs:6-29) [5]. It is never edited and must stay green.
- Ticket IDs are `T` plus three digits, `T001` to `T012`; value sets match the filter options (tickets.js:2-13, index.html:16-17) [7].
- Storage: `localStorage` key `support-tickets.v1` holds a JSON array of ticket records, each `{id, title, customer, status, priority, description}`, all strings. Nothing is written on load. `app.js` never touches `localStorage` itself: it calls `TicketStore.open(window.localStorage, window.SEED_TICKETS)`; reading the `window.localStorage` property itself can throw when storage is disabled, so guard that access and fall back to an in-memory object with `getItem`/`setItem`.
- Flow: `app.js` opens the repo, holds the filter state (search text, status, priority) and renders. Render: `repo.list(filter)` gives the visible list; `app.js` rebuilds `ul#tickets`, sets `#result-count` text ("N tickets" or "1 ticket"), and shows or hides `#empty-state` and the list. Filter input (`input` and `change` events) updates the filter state and re-renders. `Reset filters` clears the state and the control values; stored tickets are untouched.
- DESIGN.md at the repository root governs UI work: read it. One filled primary action per surface (`New ticket`), status and priority as text, visible focus. Keep each ticket button's accessible name containing its ID and title.

## Allowed files
- `store.js`
- `app.js`
- `index.html`
- `styles.css`
- `test_store.cjs`
- `test_dashboard.cjs`

## Layout
Pattern: existing, root: . (a flat tree; the files below are admitted by the architecture Layout)
- `index.html`: the page, its controls and both dialogs; no inline script.
- `styles.css`: all styling; no rules for markup that does not exist.
- `tickets.js`: seed data only; never edited. (Not an Allowed file.)
- `store.js` (new): pure ticket logic and storage (load, save, filter, validate, create, update). No `document` access.
- `app.js`: DOM rendering and event wiring. No storage calls (`app.js` does not touch `localStorage` directly) and no business rules; it calls `TicketStore`.
- `test*.cjs`: Node tests; the browser ones are run by the browser-check wrapper.

## Tests first
Each fails in the red commit, before any implementation exists, except the one red-exempt test below.
- `test_store.cjs` :: open lists T001 to T012 in order: `open(fakeStorage, seed)` on empty storage, `list()` returns T001..T012 in order, T001 with its fields (FR-01).
- `test_store.cjs` :: open falls back to the seed for non-JSON, a non-array, and a bad status: storage holds `not json`, a non-array such as `{}`, and an array with a record whose status is `closed`; each `list()` returns the twelve seed records (FR-03).
- `test_store.cjs` :: list matches title or customer case-insensitively: "acme" -> T001, T005, T011; "RESET" -> T001; "expired link" -> none (FR-04).
- `test_store.cjs` :: list by status and priority: status `pending` -> T003 T005 T006 T010; empty string status returns all 12; a priority filter returns only that priority (FR-05).
- `test_store.cjs` :: combined AND: "acme" + open + high -> T001 only; "acme" + resolved + low -> empty (FR-06).
- `test_store.cjs` :: seed array untouched (C-02): after `open` and `list`, and after mutating a returned copy, the seed array still equals the twelve original records (ids T001 to T012).
- `test_dashboard.cjs` :: first visit lists the twelve seeded tickets (FR-01): 12 ticket rows, T001 reads Password reset link expired, Acme Labs, open, high. **Red-exempt** (`red_exempt` in `status.yaml`): FR-01 already holds in today's page, so this test passes against the stub on purpose. Do not change it to make it fail, and report that it passes.
- `test_dashboard.cjs` :: first visit shows 12 ticket buttons named with ID and title, rendered from the store (FR-01): 12 buttons whose accessible names contain each ID and title, and `window.TicketStore` is defined in the page (`page.evaluate(() => typeof window.TicketStore)` is `"object"`). The store assertion keeps this test red until `index.html` loads `store.js`; this test is NOT exempt and must fail in the red commit.
- `test_dashboard.cjs` :: search, status and priority filters combine (FR-04, FR-05, FR-06): "acme" -> 3 buttons; plus `open` plus `high` -> T001 only.
- `test_dashboard.cjs` :: count text and empty message (FR-07): "zzz" -> status region reads "0 tickets", "No tickets match your filters." visible; clearing -> "12 tickets", message hidden; a single match reads "1 ticket".
- `test_dashboard.cjs` :: Reset filters restores everything (FR-08): after "acme" + `open`, Reset -> empty search, "All statuses", "All priorities", 12 tickets.

Test mechanics:
- `test_store.cjs` uses `node:test`, `node:assert` and a fake `Storage` object (`getItem`, `setItem`, `removeItem`, backed by a Map) and `require("./store.js")`. Load the seed in the main realm, never through a `vm` context: read `tickets.js` with `fs`, evaluate it with `new Function("window", src)` given a plain `{}` object (`const win = {}; new Function("window", src)(win); const seed = win.SEED_TICKETS;`). Then `assert.deepStrictEqual` compares same-realm values (a `vm` context makes arrays cross-realm and deepStrictEqual fails on prototypes). Take the expected IDs and records from that seed; do not edit `tickets.js`.
- `test_dashboard.cjs` is a Playwright test following `test_existing.cjs` for setup: `PLAYWRIGHT_MODULE` from the environment, `chromium` from it, the inline Node static server on `127.0.0.1` port 0 rooted at `process.cwd()`, then `browser.close()` and `server.close()` in `finally`. Use `node:test` (`test(...)`) so a failing assertion fails the file; each test uses a fresh browser context so `localStorage` starts empty. Find controls by role and accessible name (`getByLabel("Search tickets", {exact: true})`, `getByRole("combobox", {name: "Status filter"})`, `getByRole("button", {name: /T001/})`, `getByRole("status")`).
- Scratch files go under `/private/tmp/fb-neamoi0s/work/.tmp/`, never `/tmp`.
- The browser tests only run through the wrapper: run exactly `/private/tmp/fb-neamoi0s/browser-check/browser-check` as the whole Bash command (no arguments, prefixes, suffixes, pipes, redirects, semicolons or echo). It runs `node --test` over `test*.cjs` in the workspace. Pure tests: `node --test test_store.cjs`.

## Verify
- `node --test test_store.cjs`
- `/private/tmp/fb-neamoi0s/browser-check/browser-check`

## Red commit notes
- Red stubs: create `store.js` with the frozen shape: `STATUSES`, `PRIORITIES` and `open` whose body throws `Error("stub")`, exported for Node. `index.html` and `app.js` stay as they are in the red commit. `test_existing.cjs` and every other test must still pass at red.
- Expected red result: every `test_store.cjs` test fails on the stub; every `test_dashboard.cjs` test fails except the red-exempt "first visit lists the twelve seeded tickets", which passes. Report exactly which new tests passed.
- Commit messages: `test(support-ticket-dashboard): slice 01 red`, then `feat(support-ticket-dashboard): slice 01`. Stage by path, only Allowed files. Commits are unsigned locally (commit.gpgsign is false); that is allowed here.

## Rules in scope
Read these before writing code, and apply them inside the frozen contract.
- Playbook: none (no `.factory/system/playbook.md`).
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md` (profile crud-service `packet` lens; pin check passed)
- Language pack: none (`pack: none` for this module).
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.

## Operator constraints (this benchmark)
No external network, remote git operations, dependency installs, production changes, or git worktrees. Keep every scratch file under `/private/tmp/fb-neamoi0s/work/.tmp` (never `/tmp`). Never edit `test_existing.cjs`, `tickets.js`, `DESIGN.md`, `.factory/` or any skill or kit snapshot. Do not request a sandbox bypass.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
- a pre-commit hook rejects the red commit
- a commit fails to sign (commits here are unsigned by design; this does not apply)
