# Packet: slice 03, new-ticket

Written from: 04-slices.md c76bed07883e0b17c6c4023b7c1c1832c6a1fc0a9e88e5a4955679e1c770847e, 03-interface.md 1beada6addd868a7b96847b6dccfd3c5508387fce307c7baf8b688afc9f04c54

## Goal
03 New ticket: validate, create, persist

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-13 | WHEN the operator activates `New ticket`, the `New ticket` dialog opens with empty Title, Customer and Description, Status `open` and Priority `medium`. |
| FR-14 | "  Printer jam  " is stored as "Printer jam". |
| FR-15 | Title "   ", Customer "Acme", Description "x" -> "Title is required" under Title; Title marked invalid; no ticket; list unchanged. (Dialog stays open; an error beside each invalid field, tied to it with `aria-invalid` and `aria-describedby`.) |
| FR-16 | first creation -> T013; second -> T014; none reuses an ID, also after reload. (Dialog closes, row shows chosen status and priority.) |
| FR-17 | Cancel or Escape in New ticket closes it and creates nothing. |
| FR-18 | create "Printer jam" for "Zed Corp", reload, search "zed" -> it appears; open it, set `pending`, Save -> persists. |
| FR-19 | (dialog) Tab and Shift+Tab stay inside its controls; every control shows a visible focus. |
| FR-20 | closing (Create, Cancel, Escape) returns focus to the `New ticket` button. |
| NFR-01 | Nothing the operator saved is lost on reload (every create calls `setItem` before the next render; a second repo on the same storage never loses the first's edit nor reuses an ID). |
| SYS-NFR-01 | required fields are trimmed and validated before any ticket is stored; invalid input creates nothing. |

Constraints in force: C-01 vanilla HTML/CSS/JS, no remote requests or assets; C-02 never edit `tickets.js`; C-03 stable names `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`. NFR-02: every control has a visible name; errors are text, not color alone.

## Frozen contract
Copied from `03-interface.md`. They do not change.

```js
/** @typedef {{title: string, customer: string, description: string, status: Status, priority: Priority}} NewTicket */
/** @typedef {{title?: string, customer?: string, description?: string}} FieldErrors */
TicketRepo.create(input)   // (input: NewTicket) => {ticket: Ticket} | {errors: FieldErrors}
```
- `create` trims `title`, `customer` and `description`. If any trimmed value is empty it returns `{errors}` with one entry per empty field (`"Title is required"`, `"Customer is required"`, `"Description is required"`; keys `title`, `customer`, `description`) and stores nothing. Otherwise it re-reads storage and stores a ticket with the next unused ID taken from that fresh data (`T` + number, at least three digits; highest existing number + 1), the trimmed text and the given status and priority, and returns `{ticket}`. A status or priority outside the sets is a programming error: `create` throws a `RangeError` (nothing stored).
- Every write first re-reads `support-tickets.v1` (when readable and valid) so another repo's/tab's change is kept; whole array stored synchronously. A storage that throws never makes a method throw: the repo keeps working in memory.
- store.js depth: hides storage format and key, seed fallback, shape validation, trimming and required-field rules, ID allocation, filter matching and persistence behind one repository object.

Stub form: `store.js` `create(input) { throw new Error("stub"); }` already exists (store.js:57). No new frozen signature: the red commit adds no stubs.

app.js DOM contract (by role and accessible name): `dialog` named `New ticket` with labelled controls `Title`, `Customer`, `Description` (textboxes), `Status`, `Priority` (comboboxes; use separate `<label for=...>` elements for the selects, not wrapping labels) and buttons `Create ticket`, `Cancel`. Initial values: empty text, `open`, `medium`. A field error is text in an element referenced by that field's `aria-describedby`, the field has `aria-invalid="true"`, error text is the store's message (e.g. "Title is required"). Errors clear when the dialog is reopened.

## Context
- index.html has `#search`, `#status-filter`, `#priority-filter`, `#reset`, `#new-ticket`, `p#result-count[role=status]`, `ul#tickets`, `p#empty-state`, the `Ticket details` dialog (slice 02), and loads `store.js` before `app.js`. No inline script.
- styles.css has dialog, `.actions` and `.error` rules (reuse them), one breakpoint (600 px), one `:focus-visible` rule. No rules for markup that does not exist.
- app.js (slice 02) already has the Tab/Shift+Tab wrap function and focus-restore logic for the details dialog: reuse the shared wrap function for the second dialog and handle Escape on the dialog's `cancel` event. Opener for this dialog is `#new-ticket`. `Create ticket` calls `repo.create`; on `{errors}` it keeps the dialog open and shows errors; on `{ticket}` it closes, re-renders (the new ticket shows if it matches the active filters; filters are not changed) and restores focus to `New ticket`. `app.js` never touches `localStorage`; it only calls the repo.
- DESIGN.md (repo root, read it, never edit): one filled primary action per surface (`Create ticket` here; `Cancel` secondary), status and priority as text, visible focus.

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
Append to the existing test files (keep earlier tests exactly as they are). Each new test fails in the red commit.
- `test_store.cjs` :: create trims "  Printer jam  ": create with title "  Printer jam  " (customer/description valid) returns `{ticket}` whose title is "Printer jam"; the stored array holds the trimmed title (FR-14, SYS-NFR-01).
- `test_store.cjs` :: whitespace-only fields return one error per field and store nothing: all three blank -> `errors` has `title`, `customer`, `description` with the messages above; storage has no `support-tickets.v1` key; `list()` still 12 (FR-15, SYS-NFR-01).
- `test_store.cjs` :: first create is T013, second T014, next after reopening is T015: IDs are asserted on the returned ticket, and the third comes from a fresh `open` on the same storage (FR-16).
- `test_store.cjs` :: two repos on one fake storage never issue the same ID and the first repo's edit is not lost: repoA and repoB opened first; A updates T001 to `resolved`; B creates (T013); A creates (T014, not T013); a fresh open holds T001 `resolved`, T013 and T014 (FR-16, NFR-01).
- `test_store.cjs` :: create throws RangeError for an out-of-set status and stores nothing (FR-16).
- `test_dashboard.cjs` :: New ticket opens an empty form: `getByRole("dialog", {name: "New ticket"})` visible; Title, Customer, Description empty; Status `open`, Priority `medium` (FR-13).
- `test_dashboard.cjs` :: invalid submit keeps the dialog open with aria-invalid and aria-describedby error text and no new row: Title "   ", Customer "Acme", Description "x" -> dialog visible, Title has `aria-invalid="true"`, its `aria-describedby` target reads "Title is required", ticket button count still 12 (FR-15).
- `test_dashboard.cjs` :: Create ticket closes the dialog and shows the row: fill Title "Printer jam", Customer "Zed Corp", Description "Jams", Status `pending`, Priority `high`, Create ticket -> dialog closed, a ticket button matching /T013 Printer jam/ exists and its row shows `pending` and `high`; count "13 tickets" (FR-16).
- `test_dashboard.cjs` :: Cancel and Escape create nothing: type values, Cancel -> 12 tickets; reopen, type, Escape -> 12 tickets, dialog closed; reopened form is empty (FR-17).
- `test_dashboard.cjs` :: the created ticket survives reload and can be searched, opened and edited: create it, reload, search "zed" -> it appears; open it, set status `pending`, Save changes; reload -> still `pending` (FR-18, NFR-01).
- `test_dashboard.cjs` :: Tab and Shift+Tab stay inside the New ticket dialog (press Tab more times than it has controls, and Shift+Tab from the first control; `document.activeElement` is always inside the dialog) and focus returns to `New ticket` after Create, Cancel and Escape (FR-19, FR-20).

Test mechanics: same as earlier slices (`test_store.cjs`: `node:test`, fake `Storage` backed by a Map, seed loaded in the main realm via `new Function("window", src)`; `test_dashboard.cjs`: Playwright via `PLAYWRIGHT_MODULE`, inline static server, `node:test`, fresh browser context per test, controls found by role and accessible name). Reuse the helpers already in those files. Scratch files go under `/private/tmp/fb-neamoi0s/work/.tmp/`, never `/tmp`.

## Verify
- `node --test test_store.cjs`
- `/private/tmp/fb-neamoi0s/browser-check/browser-check`

Run the browser check as EXACTLY that, the whole Bash command: no arguments, prefixes, suffixes, pipes, redirects, semicolons or echo; use a generous Bash timeout (failing Playwright tests wait 30 s each). It runs `node --test` over `test*.cjs` in the workspace. Never edit `test_existing.cjs`; it must stay green.

## Red commit notes
- Expected red result: every new test above fails; all earlier tests and `test_existing.cjs` pass. Report any new test that passes.
- Commit messages: `test(support-ticket-dashboard): slice 03 red`, then `feat(support-ticket-dashboard): slice 03`. Stage by path, only Allowed files. Commits are unsigned locally (commit.gpgsign is false); that is allowed here.

## Rules in scope
- Playbook: none.
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md`
- Language pack: none.
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.

## Operator constraints (this benchmark)
No external network, remote git operations, dependency installs, production changes, or git worktrees. Keep every scratch file under `/private/tmp/fb-neamoi0s/work/.tmp` (never `/tmp`). Never edit `test_existing.cjs`, `tickets.js`, `DESIGN.md`, `.factory/` or any skill or kit snapshot. Do not request a sandbox bypass.
