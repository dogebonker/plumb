# Packet: slice 01, tracer-list-from-store

Written from: 04-slices.md f66478ef306a0eb9b78e18a69fda9708a8b0acae143023f51d68afd03de450fb, 03-interface.md 0ed380ffd64107cc0d2dd2b93c1cb1fe6fc13555ce623b12aadbd009d8716995

## Goal
### 01 Tracer: list from the store

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-01 | Example: first load -> 12 rows, T001 "Password reset link expired", Acme Labs, open, high; count reads "12 tickets". |
| FR-02 | (no Example line) The system SHALL keep the twelve seeded records, IDs and values, in `tickets.js`. `tickets.js` is not an Allowed file and stays unchanged. |
| FR-17 (load half) | Example: edit T001, create T013, reload -> both present. (This slice: the list is rebuilt from local storage on load.) |
| FR-18 | (no Example line) IF stored data is missing or unreadable THEN the system SHALL show the seeded tickets instead of failing. |
| C-01 | Vanilla HTML, CSS and JavaScript only; no dependencies, backend, remote requests or external assets. |

Standing constraints touched: SYS-NFR-04 (persistence) fit criterion: "edits and new tickets are present after reload; the twelve seeded records stay in `tickets.js`". Slice 01 covers the load side only (listed in 04-slices.md Coverage check).

## Frozen contract
From `03-interface.md`. Language: plain JavaScript (classic scripts). They do not change.

### store.js
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

Scope of this slice (04-slices.md Notes): `store.js` gets `STATUSES`, `PRIORITIES`, `open`, `all`. `update`, `create`, `filter` and `persisted` are not exported yet (later slices add them). Stored-data validity (architecture, Contracts and data): a stored array is accepted only if every item has the six string fields (`id`, `title`, `customer`, `status`, `priority`, `description`) and valid status/priority; otherwise the seeds are used. `all()` returns copies, so mutating a returned ticket or array does not change the store.

### app.js (page contract, the part this slice touches)
Depth: no exports; the interface is the page. It hides rendering, dialog focus handling, the Tab trap and validation display.
Cost: 0 public methods, 0 parameters, 0 error variants exposed, 0 configuration options exposed, 0 pass-through methods (plus the DOM contract below)

```html
<p id="result-count" role="status">12 tickets</p>   <!-- "N tickets", "1 ticket" -->
<ul id="tickets"><li><button class="ticket" data-id="T001"> ID title / customer / status · priority </button></li></ul>
<p id="empty-state">No tickets match your filters.</p>   <!-- hidden unless 0 matches -->
```
- Dialog headings are not buttons or links, so only the 12 (plus created) row buttons match `T\d{3}`.

Stub form: plain JavaScript has no kit adapter. A function or method stub keeps the frozen signature (parameters and defaults as written) with the body `throw new Error("not implemented")`. Constants (`STATUSES`, `PRIORITIES`) are real values, not stubs. Compile check: `node --check <file>`.

## Context
- Classic `defer` scripts, no modules, no build: `index.html:8-9` loads `tickets.js` then `app.js`. Slice 01 adds `<script src="store.js" defer></script>` between them (R1, R8).
- `app.js:1-13` only renders 12 `li > button.ticket > 3 span` into `#tickets` from `window.SEED_TICKETS`; span texts are `` `${id} ${title}` ``, customer, `` `${status} · ${priority}` ``; the description is not rendered (R2, R3).
- `index.html:15-23` already has `#result-count[role=status]` (hard-coded "12 tickets"), `#tickets`, hidden `#empty-state`; no storage anywhere (R3, R4).
- `tickets.js:1-14`: `window.SEED_TICKETS`, 12 records with fields id/title/customer/status/priority/description, IDs `T001`..`T012` (R5). Do not edit it. In Node, `window` is undefined: a Node test sets `globalThis.window = globalThis` before `require("./tickets.js")`, then `require("./store.js")` (store.js sets `globalThis.TicketStore` and must not touch the DOM or require `window`).
- `test_existing.cjs:25-29` needs exactly 12 buttons/links whose name matches `T\d{3}`, a T001 opener (name containing `T001` and `Password reset link expired`), and label `Search tickets`. It must keep passing; do not edit it. Nothing else may be a button or link named with `T\d{3}` while the seeds are shown (R7).
- `test_existing.cjs:1-24` is the pattern for browser tests: `process.env.PLAYWRIGHT_MODULE` for `chromium` and `expect` (`require(path.join(PLAYWRIGHT_MODULE, "test"))`), a `http.createServer` on `127.0.0.1` port 0 serving the repo root, `chromium.launch({headless: true})`.
- Budgets: SYS-NFR-04 (seeds in `tickets.js` unmodified; `git diff` on `tickets.js` empty). All user text goes in with `textContent` or `value`, never `innerHTML`. `app.js` never calls `localStorage` itself; it reads tickets only through `TicketStore`. Dependency order `tickets.js` <- `store.js` <- `app.js`.
- Storage key: `support-tickets.v1`, holding the JSON array of all tickets. Nothing is written in this slice.

## Allowed files
- store.js
- app.js
- index.html
- test_store.cjs
- test_dashboard.cjs

## Layout
Pattern: existing, root: ., check: none. All five files are named by the Layout lines.
- `index.html`: markup, including both `<dialog>` elements and the script tags. No inline script.
- `store.js`: new. Pure ticket logic and the storage adapter, exposed as `globalThis.TicketStore`. May not touch the DOM.
- `app.js`: DOM wiring, rendering, dialogs, focus. Reads and writes tickets only through `TicketStore`; never calls `localStorage` itself.
- `test*.cjs`: Node tests (logic) and Playwright tests (browser), run by `browser-check`. `test_existing.cjs` stays unchanged.
- Not allowed in this slice: `tickets.js` (seed data only, unchanged), `styles.css`, `test_existing.cjs`.

## Tests first
Each fails in the red commit, before any implementation exists. Copied from 04-slices.md:
- `test_store.cjs` :: open() on empty storage returns the 12 seeds unchanged; corrupt JSON, wrong shape, invalid status and a throwing storage all give the seeds - asserts FR-02, FR-18
- `test_dashboard.cjs` :: lists all 12 seeded tickets with ID, title, customer, status, priority and "12 tickets"; makes no request outside 127.0.0.1 - asserts FR-01, C-01

Writing guidance (does not change the lines above):
- Use `node:test` (`test(name, fn)`) in both files, one `test` per sentence of the line, so each fails or passes on its own and `node --test` reports it by name. `test_store.cjs` runs under plain `node --test test_store.cjs`. `test_dashboard.cjs` follows `test_existing.cjs` (PLAYWRIGHT_MODULE, local server on `127.0.0.1`), launches the browser once for the file and closes it and the server in an `after` hook.
- `test_store.cjs`: assert the seeds by value (12 tickets, IDs T001..T012 in order, T001 equals `{id: "T001", title: "Password reset link expired", customer: "Acme Labs", status: "open", priority: "high", description: "The reset link expires before the customer can use it."}`). Use an in-memory fake storage `{getItem, setItem}`; the cases: empty storage; value `"{not json"`; wrong shape (an object, an array item missing `description`, a non-string field); an item with status `"closed"` and one with priority `"urgent"`; a storage whose `getItem` throws; `undefined` storage. Each returns the seeds from `all()` and `open` does not throw. Also assert nothing is written (`setItem` never called), `STATUSES` and `PRIORITIES` equal the frozen arrays, a valid stored array (for example the seeds with T001 changed to resolved) is returned by `all()` in stored order, and mutating the returned array or a ticket does not change a second `all()`.
- `test_dashboard.cjs`: assert the 12 rows by name and text (ID, title, customer, status, priority per row compared with the seeds, count text "12 tickets" in the `role=status` region, `li > button.ticket[data-id]`); record every request URL with `page.on("request")` and assert each starts with `http://127.0.0.1:<port>` (data: and blob: URLs aside). Because the list must come from `TicketStore.open().all()`, also assert the load half of FR-17 and FR-18 in the page: with `localStorage["support-tickets.v1"]` pre-set (via `page.addInitScript` or a first visit then `page.evaluate` and `reload`) to the seeds with T001 `resolved`, the T001 row shows `resolved · high`; with the key set to `"{not json"` the 12 seeds show. These page tests fail against the stub because `app.js` does not read the store yet.
- Where a new test would pass against the stub, list it in your report; do not change it to make it fail.

## Verify
- `node --test test_store.cjs`
- `/private/tmp/fb-zt0pwkma/browser-check/browser-check`

Run the second command exactly as written: no arguments, prefix, suffix, pipe, redirect, `cd &&`, semicolon or echo. It runs `node --test` over every `test*.cjs` in the workspace (so also `test_existing.cjs`, which must stay green) with `PLAYWRIGHT_MODULE` set. Running `node test_dashboard.cjs` or `node test_existing.cjs` directly in the ordinary sandbox cannot launch Chromium. Write `.tmp` scratch files only under `/private/tmp/fb-zt0pwkma/work/.tmp`.

Notes (04-slices.md): `store.js` gets `STATUSES`, `PRIORITIES`, `open`, `all` (stubs for the rest are not exported yet); `app.js` renders rows from `TicketStore.open().all()`, keeping `button.ticket` rows and `data-id`; `index.html` adds the `store.js` script tag between `tickets.js` and `app.js`.

Red commit stubs: `store.js` defines `globalThis.TicketStore` with `STATUSES`, `PRIORITIES` and `open` whose body is `throw new Error("not implemented")`. Leave `app.js` and `index.html` as they are at red (existing tests must keep passing); the page tests fail on the pre-set storage assertions because `app.js` does not read the store yet. The green commit adds the `store.js` script tag and switches `app.js` to `TicketStore.open().all()`.

## Rules in scope
No playbook exists (`.factory/system/playbook.md` is missing). Read these before writing code, and apply them inside the frozen contract.
- `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/clean-code/clean-code.nano.md` (pin check passed: hash 7a746649e5eb77326cf54d381adf030994f4e311)
- Simplification ladder: Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
- Language pack: none (`pack: none` in `lenses.yaml`); skipped.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
- a pre-commit hook rejects the red commit
- a commit fails to sign (never commit unsigned; the operator accepts unsigned local commits as the repository's configured setup, so this applies only if signing is configured and fails)
