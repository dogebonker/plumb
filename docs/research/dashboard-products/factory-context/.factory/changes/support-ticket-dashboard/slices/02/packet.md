# Packet: slice 02, ticket-details

Written from: 04-slices.md c76bed07883e0b17c6c4023b7c1c1832c6a1fc0a9e88e5a4955679e1c770847e, 03-interface.md 1beada6addd868a7b96847b6dccfd3c5508387fce307c7baf8b688afc9f04c54

## Goal
02 Ticket details: open, edit, save, cancel

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-02 | T001 saved as `resolved`, reload -> T001 shows `resolved`. |
| FR-09 | "T002 Export stalls at ninety percent" -> Northwind, "The monthly CSV export never finishes.", open, high. |
| FR-10 | T002 high -> low, Save -> row shows `low`; reload -> still `low`. |
| FR-11 | status filter `open`, T002 saved as `resolved` -> list is one shorter; count updates. |
| FR-12 | change T002 to `pending`, Cancel -> T002 still `open`. |
| FR-19 | (details dialog) Tab and Shift+Tab stay inside its controls; every control shows a visible focus. |
| FR-20 | open T003, press Escape -> focus is on T003's button. |
| NFR-01 | Nothing the operator saved is lost on reload in the same browser (every update calls `setItem` before the next render). |

Full FR text (from `01-product.md`):
- FR-02: WHEN the page reopens or reloads, the system SHALL show the tickets last saved in the browser, not the seed.
- FR-09: WHEN the operator activates a ticket's button (accessible name includes its ID and title), the system SHALL open the `Ticket details` dialog showing that ticket's title, customer, description, status and priority.
- FR-10: WHEN the operator changes status or priority and activates `Save changes`, the system SHALL store the change, close the dialog and update the list.
- FR-11: WHEN a saved change makes a ticket stop matching the active filters, the system SHALL drop it from the list and update the count.
- FR-12: WHEN the operator activates `Cancel` or presses Escape in details, the system SHALL close the dialog and keep the ticket as it was.
- FR-19: WHILE a dialog is open, the system SHALL keep Tab and Shift+Tab inside its controls, and every control shows a visible focus.
- FR-20: WHEN a dialog closes (Save, Create, Cancel or Escape), the system SHALL return focus to the control that opened it.

Constraints in force (slice 04 owns their tests; do not break them):
- C-01: Vanilla HTML, CSS and JavaScript only; no dependencies, backend, remote requests or external assets.
- C-02: Seeds stay in `tickets.js`, never edited.
- C-03: Stable names: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`.
- NFR-02: every control has a visible name; errors/counts are text, announced via `role=status`.

## Frozen contract
Copied from `03-interface.md`. They do not change.

### store.js
Depth: hides storage format and key, seed fallback, shape validation, trimming and required-field rules, ID allocation, filter matching and persistence behind one repository object.

```js
/** @typedef {"open"|"pending"|"resolved"} Status */
/** @typedef {"low"|"medium"|"high"} Priority */
/** @typedef {{id: string, title: string, customer: string, status: Status, priority: Priority, description: string}} Ticket */
/** @typedef {{query?: string, status?: string, priority?: string}} TicketFilter */

window.TicketStore = {
  STATUSES: ["open", "pending", "resolved"],
  PRIORITIES: ["low", "medium", "high"],
  /** @param {Storage} storage @param {Ticket[]} seed @returns {TicketRepo} */
  open(storage, seed) {},
};

TicketRepo.list(filter)        // (filter?: TicketFilter) => Ticket[]
TicketRepo.get(id)             // (id: string) => Ticket | undefined
TicketRepo.update(id, changes) // (id: string, changes: {status?: string, priority?: string}) => Ticket | undefined
TicketRepo.create(input)       // slice 03; stays a stub that throws Error("stub")
```
- `open` reads `support-tickets.v1`; when missing or unreadable (not JSON, not an array, a record with a missing field or status/priority outside the sets) the repo holds a copy of `seed`. It writes nothing until the first change. Every write (`update`, `create`) first re-reads `support-tickets.v1` (when readable and valid) so a change made by another tab on the same origin is kept; when storage is unreadable the repo's in-memory list is used. A storage that throws on read or write never makes `open` or any method throw: the repo keeps working in memory.
- `list` returns copies in stored order (already implemented in slice 01).
- `get` returns a copy of the ticket, or `undefined` for an unknown ID.
- `update` re-reads storage, then changes only the status and/or priority named in `changes`, stores the result (whole array under `support-tickets.v1`, synchronously) and returns the updated copy. It returns `undefined` (unknown ID) and stores nothing. A given status or priority outside the sets is a programming error: it throws a `RangeError` and stores nothing.

Scope of this slice: implement `get` and `update` for real in `store.js` (they are `throw new Error("stub")` today). `create` stays a stub. No new frozen signature is added, so the red commit adds no stubs.

### app.js
Depth: wires DOM events to `TicketStore`; no exports. Contract is the DOM, checked by role and accessible name:
- `button` named `<ID> <title> ...` per ticket (existing).
- `dialog` named `Ticket details` with controls labelled `Status`, `Priority` and buttons `Save changes`, `Cancel`. The title, customer and description are shown as text in the dialog (read-only).
- (The `New ticket` dialog and its form belong to slice 03; do not build it.)

## Context
Facts this slice needs (from `02-architecture.md`):
- index.html already holds the controls: `#search`, `#status-filter`, `#priority-filter`, `#reset`, `#new-ticket`, `p#result-count[role=status]`, `ul#tickets`, `p#empty-state`. After slice 01 it also loads `store.js` before `app.js`. No `<dialog>` exists yet; add the `Ticket details` dialog to `index.html` (no inline script).
- styles.css has unused dialog, `.actions` and `.error` rules (styles.css:9, 14-20) to reuse, one breakpoint (600 px), one focus rule (`:focus-visible`, 3 px). No rules for markup that does not exist.
- Flow 4-5, 7-8: a ticket button records itself as the opener (by ticket ID), fills the dialog from `repo.get(id)` and calls `showModal()`. `Save changes` calls `repo.update`, closes the dialog, re-renders and restores focus. Cancel and Escape (handled on the dialog's `cancel` event so one path closes and restores focus) close without writing. A `keydown` handler on the open dialog wraps Tab/Shift+Tab between its first and last focusable control (write it as one shared function so slice 03 reuses it for the second dialog).
- Decision: native `<dialog aria-labelledby=...>` with `showModal()`; Tab wrap and focus return are done by us. The dialog's heading text is exactly `Ticket details`. If the opener ticket no longer matches the filters after a save, focus falls back to `Search tickets` (FR-20 applies to a control that still exists). The list re-render replaces the ticket buttons, so restore focus to the new button with the same ID.
- Storage: `app.js` never touches `localStorage` directly; it only calls `TicketStore.open(...)` (already in place from slice 01, with a guarded fallback) and repo methods. `store.js` has no `document` access.
- DESIGN.md (repo root, read it, never edit) governs UI: one filled primary action per surface (`Save changes` in this dialog; `Cancel` is secondary), status and priority as text, visible focus.

## Allowed files
- `store.js`
- `app.js`
- `index.html`
- `styles.css`
- `test_store.cjs`
- `test_dashboard.cjs`

## Layout
Pattern: existing, root: . (flat tree)
- `index.html`: the page, its controls and both dialogs; no inline script.
- `styles.css`: all styling; no rules for markup that does not exist.
- `tickets.js`: seed data only; never edited. (Not an Allowed file.)
- `store.js`: pure ticket logic and storage. No `document` access.
- `app.js`: DOM rendering and event wiring. No storage calls and no business rules.
- `test*.cjs`: Node tests; browser ones are run by the browser-check wrapper.

## Tests first
Append to the existing test files (keep slice 01's tests exactly as they are). Each new test fails in the red commit.
- `test_store.cjs` :: get returns a copy and undefined for T999: `get("T002")` has its seed fields; mutating the returned object does not change a second `get("T002")`; `get("T999")` is `undefined` (FR-09).
- `test_store.cjs` :: update persists priority: `update("T002", {priority: "low"})` returns T002 with priority `low` and other fields unchanged; `list()` shows it; the storage key holds it (FR-10).
- `test_store.cjs` :: update throws RangeError for status "closed" with nothing stored: `assert.throws(..., RangeError)`, the fake storage has no `support-tickets.v1` entry and `get` is unchanged (FR-10).
- `test_store.cjs` :: update returns undefined for an unknown ID and stores nothing (FR-10).
- `test_store.cjs` :: a new open on the same storage returns the update: update T001 status `resolved`, `open(sameStorage, seed)` then `get("T001").status === "resolved"` (FR-02, NFR-01).
- `test_store.cjs` :: two repos on one fake storage keep both repos' edits: repoA updates T001, repoB (opened before A's write) updates T002; a fresh open shows both edits (NFR-01).
- `test_dashboard.cjs` :: opening T002 shows its details: click button `/T002/`; `getByRole("dialog", {name: "Ticket details"})` is visible and shows "Export stalls at ninety percent", "Northwind", "The monthly CSV export never finishes.", Status select = `open`, Priority select = `high` (FR-09).
- `test_dashboard.cjs` :: Save changes updates the row and survives reload: T002 priority -> `low`, Save; dialog closed; T002 row text contains `low`; after `page.reload()` still `low` (FR-10, FR-02, NFR-01).
- `test_dashboard.cjs` :: a ticket that stops matching the status filter leaves the list: Status filter `open`, count "N tickets"; T002 saved as `resolved`; list has one fewer ticket button and the count text matches (FR-11).
- `test_dashboard.cjs` :: Cancel and Escape change nothing: change T002 status to `pending`, Cancel -> row still shows `open`; reopen, change, press Escape -> still `open`; the dialog is closed each time (FR-12).
- `test_dashboard.cjs` :: focus returns to the ticket's button after Escape, Cancel and Save, and to `Search tickets` when the saved ticket left the list (FR-20).
- `test_dashboard.cjs` :: Tab and Shift+Tab stay inside the dialog: with the dialog open, press Tab more times than it has controls, and Shift+Tab from the first control; `document.activeElement` is always inside the dialog (FR-19).

Test mechanics: same as slice 01 (`test_store.cjs`: `node:test`, fake `Storage` backed by a Map, seed loaded in the main realm via `new Function("window", src)`; `test_dashboard.cjs`: Playwright via `PLAYWRIGHT_MODULE`, inline static server, `node:test`, fresh browser context per test so `localStorage` starts empty, controls found by role and accessible name). Reuse the helpers already in those files. Scratch files go under `/private/tmp/fb-neamoi0s/work/.tmp/`, never `/tmp`.

## Verify
- `node --test test_store.cjs`
- `/private/tmp/fb-neamoi0s/browser-check/browser-check`

Run the browser check as EXACTLY that, the whole Bash command: no arguments, prefixes, suffixes, pipes, redirects, semicolons or echo. It runs `node --test` over `test*.cjs` in the workspace. Never edit `test_existing.cjs`; it must stay green.

## Red commit notes
- No new stubs are needed (`get` and `update` already throw `Error("stub")`). Expected red result: every new test above fails; all slice 01 tests and `test_existing.cjs` pass. Report any new test that passes.
- Commit messages: `test(support-ticket-dashboard): slice 02 red`, then `feat(support-ticket-dashboard): slice 02`. Stage by path, only Allowed files. Commits are unsigned locally (commit.gpgsign is false); that is allowed here.

## Rules in scope
- Playbook: none.
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md` (profile crud-service `packet` lens; pin check passed in slice 01)
- Language pack: none (`pack: none` for this module).
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.

## Operator constraints (this benchmark)
No external network, remote git operations, dependency installs, production changes, or git worktrees. Keep every scratch file under `/private/tmp/fb-neamoi0s/work/.tmp` (never `/tmp`). Never edit `test_existing.cjs`, `tickets.js`, `DESIGN.md`, `.factory/` or any skill or kit snapshot. Do not request a sandbox bypass. The executor uses the same model as the step agent (no model override).
