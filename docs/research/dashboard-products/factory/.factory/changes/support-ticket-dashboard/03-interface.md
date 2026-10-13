# Interface: support-ticket-dashboard

Language: plain JavaScript (classic scripts). No kit adapter covers plain JavaScript (`kit/adapters/` has go, python, rust, typescript), so the compile step used `node --check` plus a `require` of stubbed `store.js` (exports loaded, stubs threw "not implemented"); that is a syntax and shape check only, not a type check. Stubs were undone.

## store.js
Depth: hides storage keying and validation of stored data, the fallback to seeds, ID generation, trimming and required-field rules, and the filter semantics behind five calls.
Cost: 5 public methods (`open`, `all`, `update`, `create`, `filter`) + 2 constants + 1 read-only property (`persisted`), 7 parameters (`storage`, `seeds`, `id`, `changes`, `input`, `tickets`, `criteria`), 4 error variants exposed (`errors.title`, `errors.customer`, `errors.description`, `RangeError`), 0 configuration options exposed (`storage` and `seeds` default to browser values), 0 pass-through methods

```js
/** @typedef {{id:string,title:string,customer:string,status:string,priority:string,description:string}} Ticket */
globalThis.TicketStore = {
  STATUSES: ["open", "pending", "resolved"],
  PRIORITIES: ["low", "medium", "high"],
  /** @returns {Store} */
  open(storage = globalThis.localStorage, seeds = globalThis.SEED_TICKETS),
  /** @returns {Ticket[]} */
  filter(tickets, {query = "", status = "", priority = ""} = {}),
};
// Store:
//   all(): Ticket[]
//   readonly persisted: boolean   // true until a write to storage fails
//   update(id: string, {status: string, priority: string}): Ticket | null
//   create({title, customer, description, status = "open", priority = "medium"}):
//     {ok: true, ticket: Ticket} | {ok: false, errors: {title?: string, customer?: string, description?: string}}
```
- `open` reads key `support-tickets.v1`. Missing, unparsable or malformed data, or a throwing `storage` (including `undefined`), gives the seeds; it never throws for storage problems. Nothing is written until `update` or `create` succeeds. A failed write keeps the change in memory and sets `persisted` to false for the rest of the session; `app.js` then shows the text note "Changes could not be saved in this browser and will be lost on reload." in an element with id `save-warning` (hidden while `persisted` is true).
- `update` and `create` re-read storage immediately before applying, so two stores over one storage never reuse an ID or drop each other's edits.
- `all` returns a copy in stored order (seeds first, then created); callers cannot mutate the store.
- `update` persists and returns the updated ticket; `null` for an unknown id; `RangeError` for a status or priority outside `STATUSES`/`PRIORITIES`. Only status and priority change.
- `create` trims title, customer and description, then validates. Valid: new ticket with `T` + (highest numeric suffix + 1, padded to 3), persisted. Invalid: `errors` holds a message per empty field ("Title is required", "Customer is required", "Description is required"), nothing is created or stored. `RangeError` for an invalid status or priority.
- `filter` matches title or customer by case-insensitive substring of `query` trimmed of surrounding whitespace, AND exact `status` and `priority`; `""` means any. Pure; preserves order.

## app.js (page contract)
Depth: no exports; the interface is the page. It hides rendering, dialog focus handling, the Tab trap and validation display.
Cost: 0 public methods, 0 parameters, 0 error variants exposed, 0 configuration options exposed, 0 pass-through methods (plus the DOM contract below)

```html
<input id="search" type="search">  <!-- label "Search tickets" -->
<select id="status-filter" aria-label="Status filter">  <select id="priority-filter" aria-label="Priority filter">
<button id="reset">Reset filters</button>  <button id="new-ticket">New ticket</button>
<p id="result-count" role="status">12 tickets</p>   <!-- "N tickets", "1 ticket" -->
<ul id="tickets"><li><button class="ticket" data-id="T001"> ID title / customer / status · priority </button></li></ul>
<p id="empty-state">No tickets match your filters.</p>   <!-- hidden unless 0 matches -->
<p id="save-warning" hidden>Changes could not be saved in this browser and will be lost on reload.</p>
<dialog id="details-dialog" aria-labelledby="details-title">  <!-- name "Ticket details" -->
  title, customer, description as text; <select id="details-status"> label "Status"; <select id="details-priority"> label "Priority";
  <button type="submit">Save changes</button> <button type="button">Cancel</button>
<dialog id="create-dialog" aria-labelledby="create-title"> <!-- name "New ticket" -->
  <form novalidate> inputs "Title", "Customer", textarea "Description", selects "Status", "Priority";
  each invalid field: aria-invalid="true", aria-describedby -> <p class="error" id="create-<field>-error">;
  <button type="submit">Create ticket</button> <button type="button">Cancel</button>
```
- Dialog headings are not buttons or links, so only the 12 (plus created) row buttons match `T\d{3}`.
- Opening a dialog remembers the opener; on close (Save, Cancel, Escape) focus returns to the opener (the ticket's row button by `data-id`, else `Search tickets`), or to `New ticket`.
- Tab and Shift+Tab wrap between the first and last focusable controls of the open dialog.

## Test plan
### . (bdd: off)
Logic, Node `node:test`, `test_store.cjs`; page, Playwright, `test_dashboard.cjs`, both run by `browser-check`.
- FR-01: `test_dashboard.cjs` :: lists all 12 seeded tickets with ID, title, customer, status, priority and "12 tickets"
- FR-02: `test_store.cjs` :: seeds in tickets.js keep their 12 IDs and values (`open()` on empty storage returns them unchanged)
- FR-03: `test_store.cjs` :: filter "acme" returns T001, T005, T011 and "EXPORT" returns T002; `test_dashboard.cjs` :: typing in Search tickets narrows the list
- FR-04: `test_store.cjs` :: filter combines query, status and priority with AND (acme+pending+medium returns T005)
- FR-05: `test_dashboard.cjs` :: result count updates in the status region ("3 tickets" for resolved, "1 ticket" for one match)
- FR-06: `test_dashboard.cjs` :: no match shows "No tickets match your filters." and "0 tickets"
- FR-07: `test_dashboard.cjs` :: Reset filters clears search and both filters and stored tickets are unchanged
- FR-08: `test_dashboard.cjs` :: opening T002 shows title, customer, description, status and priority in Ticket details
- FR-09: `test_dashboard.cjs` :: saving T001 as resolved updates the list and survives reload; `test_store.cjs` :: update persists and a reopened store returns it
- FR-10: `test_dashboard.cjs` :: Cancel and Escape in details leave T003 low and return focus to its row button
- FR-11: `test_dashboard.cjs` :: New ticket dialog opens with Title, Customer, Description, Status open, Priority medium
- FR-12: `test_store.cjs` :: create trims title, customer and description ("  Printer jam  " stored as "Printer jam")
- FR-13: `test_store.cjs` :: whitespace-only fields return an error per field and create nothing; `test_dashboard.cjs` :: invalid submit keeps dialog open, messages tied by aria-describedby, aria-invalid set, first invalid field focused, list unchanged
- FR-14: `test_store.cjs` :: first created ticket is T013 and persists; `test_dashboard.cjs` :: created ticket survives reload, can be searched, opened and edited
- FR-15: `test_dashboard.cjs` :: Cancel and Escape in New ticket create nothing, discard text and return focus to New ticket
- FR-16: `test_dashboard.cjs` :: Tab and Shift+Tab cycle within each open dialog
- FR-17: `test_dashboard.cjs` :: edit T001 and create T013, reload, both present; `test_store.cjs` :: two stores over one storage create T013 then T014 and keep both edits
- SYS-NFR-04 (failed write): `test_store.cjs` :: a storage whose setItem throws keeps the change in memory and sets persisted to false; `test_dashboard.cjs` :: the save-warning note appears when localStorage writes throw
- FR-18: `test_store.cjs` :: corrupt JSON, wrong shape, invalid status and a throwing storage all give the seeds
- States (DESIGN.md): empty = FR-06, count = FR-05, validation error = FR-13; loading and failed states do not exist in this local product.

## Decisions
None: no lens conflicts. Round 1 cards APoSD-1 (modified) and PEAA-1 (accepted) are folded into the signatures above; the other three were overruled (`challenges.md`). The user ended the panel rounds by approving.

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 to FR-18 | test: the test named on each FR line of the Test plan |
| NFR-01 | test: `test_dashboard.cjs` :: every action is reachable and operable by keyboard with a visible focus indicator |
| NFR-02 | test: `test_dashboard.cjs` :: no horizontal overflow and no clipped dialog controls at 360 px and 1280 px |
| NFR-03 | test: `test_dashboard.cjs` :: status and priority are visible text in the list and dialogs |
| C-01 | test: `test_dashboard.cjs` :: page makes no request outside 127.0.0.1 and loads no external asset |
| C-02 | test: `test_dashboard.cjs` :: accessible names and labels of the stable interface exist; `test_existing.cjs` still passes |
| SYS-NFR-01 | test: `test_store.cjs` :: whitespace-only fields create no ticket (FR-12, FR-13) |
| SYS-NFR-02 | test: `test_dashboard.cjs` :: focus trap, Escape and focus return (FR-10, FR-15, FR-16, NFR-01) |
| SYS-NFR-03 | test: `test_dashboard.cjs` :: 360 px layout (NFR-02) |
| SYS-NFR-04 | test: `test_dashboard.cjs` :: reload persistence (FR-09, FR-14, FR-17) and the save-warning note; `test_store.cjs` :: failed write sets persisted false, two stores keep both edits; `tickets.js` diff is empty (human-verified in review) |

## Open questions
