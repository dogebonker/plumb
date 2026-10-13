# Challenges: support-ticket-dashboard

## Round 1

### a-philosophy-of-software-design

#### Card A1

| Field | Value |
| --- | --- |
| Lens / rule | a-philosophy-of-software-design/Naming, Consistency, and Obviousness: Use consistent names, argument order, |
| Where | `TicketRepo.update(id, changes) // (id: string, changes: {status?: string, priority?: string}) => Ticket | undefined` next to `TicketRepo.create(input) // (input: NewTicket) => {ticket: Ticket} | {errors: FieldErrors}` |
| Steelman | The two operations fail differently on purpose. `create` takes user typed text, so an expected failure (an empty field) comes back as data the dialog can show beside the field (FR-15). A status or priority outside the sets can only come from a bug, because the form offers a fixed list, so `create` throws. `update` has no user typed text, and "unknown ID or bad value, nothing stored" is one cheap check for the caller. Nothing is stored in either case, so SYS-NFR-01 holds. |
| Objection | The same bad input (a status of `"closed"`) is a thrown `RangeError` in `create` and a silent `undefined` in `update`. `undefined` from `update` also means two things: an unknown ID, or a bad value. A caller cannot tell which, and a bug in the Save handler shows up as a dialog that does nothing instead of a stack trace. The Cost line says "3 error variants exposed", but the contract has five outcomes a caller must handle: three field errors, a `RangeError`, and an `undefined` that means "not saved" (also returned by `get`). The Cost card understates what callers must learn. |
| Anchored to | Cost line of `store.js`: "3 error variants exposed (one per required field)". The contract text lists 5 failure outcomes. |
| Alternative | `update(id, changes) // (id: string, changes: {status?: Status, priority?: Priority}) => Ticket | undefined` where an out-of-set value throws `RangeError` exactly as `create` does, and `undefined` means only "unknown ID". Update the Cost line to count the `RangeError` and the `undefined`. |
| Cost of alternative | The `update` line of the contract changes, and the `test_store.cjs` case for FR-10 gains an assertion that a bad value throws. `app.js` Save must never pass an unchecked value. It reads from the fixed selects, so this is already true. A thrown error in the Save handler is louder in the browser than a no-op. That is the point, but it is a behavior change. |
| Severity | fix |
| Response | accept: `update` throws RangeError for an out-of-set status or priority; `undefined` means unknown ID only; Cost line counts both. |

#### Card A2

| Field | Value |
| --- | --- |
| Lens / rule | a-philosophy-of-software-design/Interface Design Rules: Eliminate arguments that only exist |
| Where | `open(storage, seed) {}` with `@param {Storage} storage` |
| Steelman | Passing `storage` in lets `test_store.cjs` use a fake `Storage` object and lets tests make it throw, which the contract promises to survive (the "storage that throws" clause). `seed` must be passed because C-02 keeps the twelve records in `tickets.js`, so `store.js` cannot own them. Callers pass `window.localStorage` and `window.SEED_TICKETS` once, in one place (`app.js`). |
| Objection | The Depth line says the module hides "storage format and key", but the `Storage` type in the signature tells every caller that a Web Storage object backs the repo. The argument exists mostly so tests can substitute it. The lens says test convenience should not shape the interface. The cost is small: one caller, one call. |
| Anchored to | none (taste). C-02 justifies `seed`, but nothing in the constraints requires an injected `storage`. |
| Alternative | `open(seed, storage = window.localStorage) {}` (storage optional, defaulting to the browser's). |
| Cost of alternative | The reader must learn a default. Tests still pass a fake as the second argument, so the leak stays visible to tests and is hidden from the one production caller. The argument order differs from the current signature, so the test plan and the `app.js` call site must be updated together. The gain is small. |
| Severity | note |
| Response | overrule: keep `open(storage, seed)` explicit, no hidden global default. |

#### Card A3

| Field | Value |
| --- | --- |
| Lens / rule | a-philosophy-of-software-design/Prefer Deep Modules: Prefer a small interface with |
| Where | `TicketRepo.get(id)         // (id: string) => Ticket | undefined` |
| Steelman | `get` is a one-line, obvious operation for the details dialog (FR-09), and it returns a copy, so the dialog cannot change stored data. It keeps `app.js` from scanning the list and removes any doubt about which ticket a row refers to. Its Cost entry is 1 of 5 methods, and the Cost line claims 0 pass-through methods. |
| Objection | No line in the Test plan exercises `get` (FR-09 is checked in the browser through the dialog). It adds a fifth method to the Cost line's "5 public methods" for something `list()` already returns. This is a small surplus surface that readers must learn, not a defect. |
| Anchored to | none (taste). The Cost line's "5 public methods" is a count, not a limit. |
| Alternative | `TicketRepo.list(filter) // (filter?: TicketFilter & {id?: string}) => Ticket[]` with no `get`. |
| Cost of alternative | `TicketFilter` grows a field that no user can type, which is a worse special case than a separate `get`. The dialog caller reads `list({id})[0]`, which is less obvious than `get(id)`. Keeping `get` is probably right. Raise it only if the slice that implements it has no test of its own. |
| Severity | note |
| Response | modify: keep `get`, and add a `test_store.cjs` case for it. |

### patterns-of-enterprise-application-architecture

#### Card P1

| Field | Value |
| --- | --- |
| Lens / rule | patterns-of-enterprise-application-architecture/Decision rules: Design concurrency and transactions in |
| Where | `open(storage, seed) {}` with `TicketRepo.create(input)   // (input: NewTicket) => {ticket: Ticket} \| {errors: FieldErrors}` |
| Steelman | `open` reads storage once and the repo then works on its own copy. That keeps `list` cheap and makes the "storage throws, keep working in memory" promise simple to state and test. Multiple users and cross-browser sync are non-goals, so one repo per page looks like enough. |
| Objection | The same browser can have two tabs open on one origin, and each `open` takes its own snapshot of `support-tickets.v1`. The interface does not say what a write does to the other tab's changes. If each write stores the whole in-memory array, the tab that writes last overwrites the other tab's saved edit or new ticket. Both tabs also compute "highest existing number + 1" from their own snapshot, so both can issue T013, which breaks FR-16's "none reuses an ID". Nothing says which behaviour is intended: last write wins, or detect and merge. |
| Anchored to | NFR-01 ("Nothing the operator saved is lost on reload in the same browser"); FR-16 (no ID reused) |
| Alternative | `TicketRepo.update(id, changes)` and `TicketRepo.create(input)` keep their signatures. The promise changes: each write re-reads `support-tickets.v1`, applies the one change to that fresh data, then stores. The ID is allocated from the fresh data. `list` and `get` also read fresh data, or the repo adds `refresh()`. |
| Cost of alternative | Every call parses storage, so there are more reads and the "copy held by the repo" model gets more complicated. The in-memory fallback for a throwing storage needs its own rule for when memory and storage disagree. It is still not atomic across tabs, because `localStorage` has no compare-and-swap, but the lost-update window shrinks to a few instructions. The test plan needs a two-repo-on-one-storage case. |
| Severity | fix |
| Response | accept: `update` and `create` re-read storage before applying the change; `create` allocates the ID from the fresh data; add a two-repos-on-one-fake-storage test. |

#### Card P2

| Field | Value |
| --- | --- |
| Lens / rule | patterns-of-enterprise-application-architecture/Trigger rules: If one class or layer |
| Where | `window.TicketStore = { STATUSES, PRIORITIES, open(storage, seed) {} }` with `TicketRepo.create(input) // trims, validates, allocates ID, stores` |
| Steelman | The interface says it is one deep module, with 5 public methods and 0 pass-through methods. Trimming, required-field rules and ID allocation run in the same call that stores the ticket, so SYS-NFR-01 ("invalid input creates nothing") cannot be skipped by a caller. The module is tested in Node with a fake `Storage` and no DOM. A separate rules module would be close to a pass-through layer. |
| Objection | `store.js` holds three responsibilities: record persistence (storage key, JSON, fallback), ticket rules (trim, required fields, status and priority sets, ID format) and query matching. If the workflow grows, for example by adding a rule that edits must keep the title non-empty, every change to the rules touches the persistence module and its storage-failure tests. For now this is a taste concern. |
| Anchored to | none |
| Alternative | `TicketRules.prepare(input) => {values: NewTicket} \| {errors: FieldErrors}` as a pure function, and `TicketRepo.create(values)` that only allocates the ID and stores. |
| Cost of alternative | There is a second public module and the caller must call two things in order. A caller that forgets `prepare` can store untrimmed input, which weakens SYS-NFR-01 unless `create` re-checks. The cost line grows from 5 public methods to about 6. |
| Severity | note |
| Response | overrule: a rules module would be a near pass-through. |
