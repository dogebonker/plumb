# Interface: support-ticket-dashboard

## store.js
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

## app.js
Depth: wires DOM events to `TicketStore`; no exports.
Cost: 0 public methods, 0 parameters, 0 error variants exposed, 0 configuration options exposed, 0 pass-through methods

Entry script run after `store.js`; it exposes nothing. Its contract is the DOM, which browser tests check by role and accessible name (stable names from `01-product.md` C-03):
- `button` named `<ID> <title> ...` for each ticket (accessible name contains the ID and title); `searchbox`/textbox `Search tickets`; comboboxes `Status filter`, `Priority filter`; buttons `Reset filters`, `New ticket`; `status` region with the count text `N tickets` / `1 ticket`.
- `dialog` named `Ticket details` with textboxes/comboboxes labelled `Status`, `Priority` and buttons `Save changes`, `Cancel`; `dialog` named `New ticket` with `Title`, `Customer`, `Description`, `Status`, `Priority`, `Create ticket`, `Cancel`.
- An invalid field has `aria-invalid="true"` and an `aria-describedby` target whose text is the error.

## Test plan
### . (bdd: off)
Node tests (`test_store.cjs`, `node:test`, a fake `Storage` object) and browser tests (`test_dashboard.cjs`, Playwright, run by the browser-check wrapper).
- FR-01: `test_store.cjs` :: open with empty storage lists T001 to T012 in order with T001's fields; `test_dashboard.cjs` :: first visit shows 12 ticket rows with ID, title, customer, status, priority
- FR-02: `test_store.cjs` :: an update is returned by a new open on the same storage; `test_dashboard.cjs` :: a saved status survives reload
- FR-03: `test_store.cjs` :: open falls back to the seed for text that is not JSON, a non-array, and a record with a bad status
- FR-04: `test_store.cjs` :: list query is a case-insensitive substring of title or customer ("acme", "RESET", "expired link")
- FR-05: `test_store.cjs` :: list by status pending returns T003 T005 T006 T010, empty string returns all
- FR-06: `test_store.cjs` :: acme + open + high is T001 only, acme + resolved + low is empty
- FR-07: `test_dashboard.cjs` :: result count text and live region update, empty message shows for "zzz" and hides on clear
- FR-08: `test_dashboard.cjs` :: Reset filters clears search and both filters and shows 12 tickets
- FR-09: `test_store.cjs` :: get returns a copy of T002 with its fields, and undefined for T999; `test_dashboard.cjs` :: opening T002 shows title, customer, description, status, priority
- FR-10: `test_store.cjs` :: update changes priority and persists, throws RangeError for status "closed" and stores nothing, returns undefined for an unknown ID; `test_dashboard.cjs` :: Save changes updates the row and survives reload
- FR-11: `test_dashboard.cjs` :: a saved ticket that stops matching the status filter leaves the list and the count drops
- FR-12: `test_dashboard.cjs` :: Cancel and Escape in details leave the ticket unchanged
- FR-13: `test_dashboard.cjs` :: New ticket opens an empty form with status open and priority medium
- FR-14: `test_store.cjs` :: create stores "Printer jam" from "  Printer jam  "
- FR-15: `test_store.cjs` :: create with a whitespace title returns the title error and stores nothing; `test_dashboard.cjs` :: invalid submit keeps the dialog open with aria-invalid and aria-describedby error text and no new row
- FR-16: `test_store.cjs` :: first create is T013, second T014, the next after reopening is T015, and two repos on one fake storage never issue the same ID; `test_dashboard.cjs` :: Create ticket closes the dialog and shows the new row with the chosen status and priority
- FR-17: `test_dashboard.cjs` :: Cancel and Escape in New ticket create nothing
- FR-18: `test_dashboard.cjs` :: a created ticket survives reload and can be found by search, opened and edited
- FR-19: `test_dashboard.cjs` :: Tab and Shift+Tab stay inside each open dialog; focus is visible
- FR-20: `test_dashboard.cjs` :: Escape, Cancel, Save and Create return focus to the opening control
- FR-21: `test_dashboard.cjs` :: at 360x740 the page has no horizontal overflow and dialog controls are inside the viewport

## Decisions

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 to FR-21 | the tests named under Test plan, one line per FR |
| NFR-01 | test: `test_dashboard.cjs` :: a saved edit and a created ticket survive reload; `test_store.cjs` :: with two repos on one fake storage, the second creator gets a new ID and the first repo's edit is not lost |
| NFR-02 | test: `test_dashboard.cjs` :: controls found by role and accessible name; error text found through aria-describedby; count read from the status role |
| C-01 | human-verified: review checks no dependency, no remote request, no external asset (grep for `http` in source files) |
| C-02 | test: `test_store.cjs` :: seed array is untouched and equals the twelve original records (ids T001 to T012) |
| C-03 | test: `test_dashboard.cjs` :: every stable name from the task is found by role and name |
| SYS-NFR-01 | test: `test_store.cjs` :: create trims and rejects whitespace-only fields, storing nothing (registry row stays `unmapped` until reconcile maps it to this test) |

## Open questions
