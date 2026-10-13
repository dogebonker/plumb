# Challenges: support-ticket-dashboard

## Round 1

### a-philosophy-of-software-design

#### Card 1

| Field | Value |
| --- | --- |
| Lens / rule | /private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/a-philosophy-of-software-design/Interface Design Rules: Design interfaces around what clients |
| Where | `update(id: string, {status: string, priority: string}): Ticket | null` with the promise "A failed write keeps the change in memory." |
| Steelman | Hiding the write failure keeps the interface at five calls and gives the UI one path with no "save failed" state. DESIGN.md says failed states do not exist in this local product. `open` already treats storage problems as a non-event, so `update` and `create` follow the same rule. Callers never need defensive code. |
| Objection | The operator is told "Everything is kept in your browser and survives reloads" (Announcement). When localStorage is full, blocked or in a restricted private window, `update` and `create` return success and the list looks saved. The change is gone after reload and nothing ever told the operator. What the client needs to know is whether the change stuck, and the interface hides exactly that. SYS-NFR-04 ("edits and new tickets are present after reload") is broken with no signal. The Test plan has a throwing-storage test only for reading (FR-18), none for a failed write. |
| Anchored to | SYS-NFR-04 (persistence), FR-17 |
| Alternative | `update(id, {status, priority}): {ticket: Ticket, saved: boolean} | null` and `create(...)`: `{ok: true, ticket, saved: boolean}`. Or one read-only `store.saved: boolean` that turns false after any failed write. |
| Cost of alternative | Every caller reads one more field. The UI needs a small "not saved, changes last until you close this tab" note, which DESIGN.md says does not exist today, so it adds a state and a test. The Cost line gains one return field. |
| Severity | fix |
| Response | modify: keep the return types; add read-only `persisted: boolean` on the Store, false after a failed write; app.js shows a text note. |

#### Card 2

| Field | Value |
| --- | --- |
| Lens / rule | /private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/a-philosophy-of-software-design/Error Handling and Exception Elimination: Eliminate exception cases by changing |
| Where | `update(...)`: `Ticket | null`, `RangeError` for a status or priority outside `STATUSES`/`PRIORITIES`; `create(...)`: `{ok: false, errors: {...}}` plus `RangeError` |
| Steelman | The split is principled. Empty text is operator error, so it is a returned value the UI shows. A status outside the list is a programmer error, because the UI only offers `<select>` options built from `STATUSES`, so it throws. An unknown id is routine, because the ticket may have gone, so it returns `null`. Throwing keeps the common return types small. |
| Objection | One module has three failure styles: a result union (`create`), `null` (`update`) and a throw (`update` and `create`). A caller must know which applies to which call, and `create` mixes two styles in one method. The Cost line counts 4 error variants exposed. `create` already returns a `{ok, errors}` shape, so a bad status could be reported the same way instead of becoming a fourth thing to catch. |
| Anchored to | store.js Cost line: "4 error variants exposed" |
| Alternative | `create(...)`: `{ok: true, ticket} | {ok: false, errors: {title?, customer?, description?, status?, priority?}}` and `update(id, changes)`: `{ok: true, ticket} | {ok: false, errors: {id?, status?, priority?}}`. No exceptions leave the store. |
| Cost of alternative | `update` loses its simple `Ticket | null` return and every caller unwraps `ok`. The programmer-error signal (a loud throw in tests) turns into a value that can be ignored. The UI never triggers these errors, so the benefit is mainly consistency. |
| Severity | note |
| Response | overrule: returned errors are for operator mistakes, RangeError is for programmer errors, null means unknown id. |

#### Card 3

| Field | Value |
| --- | --- |
| Lens / rule | /private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/a-philosophy-of-software-design/Interface Design Rules: Eliminate arguments that only exist |
| Where | `filter(tickets, {query = "", status = "", priority = ""} = {})` on `TicketStore`, beside `all(): Ticket[]` on `Store` |
| Steelman | A pure `filter(tickets, criteria)` can be tested with no storage and no fake, and the ticket list is plain data. FR-03 and FR-04 are tested directly in `test_store.cjs`. Putting it on the namespace keeps `Store` to three methods. |
| Objection | The caller must run `filter(store.all(), criteria)`, so search semantics are split across two objects and the caller has to remember to pass the store's current list. `tickets` is the one parameter on the page-facing path that exists only because filtering is placed outside the store. It accounts for 1 of the 7 parameters on the Cost line. The filter also lives apart from the store that owns the data and its invariants. |
| Anchored to | none: taste (the saving is one parameter out of 7 on the Cost line, not a constraint) |
| Alternative | `Store.find({query = "", status = "", priority = ""} = {}): Ticket[]` and no top-level `filter`. |
| Cost of alternative | Filter tests need a store opened over a fake storage plus seeds, which `open(storage, seeds)` already allows. Filtering an arbitrary array of tickets is no longer possible, which nothing in the product needs. |
| Severity | note |
| Response | overrule: a pure filter is testable without storage. |

### patterns-of-enterprise-application-architecture

#### Card 1

| Field | Value |
| --- | --- |
| Lens / rule | `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/patterns-of-enterprise-application-architecture/Trigger rules: If concurrency conflicts, stale locks,` |
| Where | `open(storage = globalThis.localStorage, seeds = globalThis.SEED_TICKETS)` with `create({title, customer, description, status = "open", priority = "medium"})` and "Valid: new ticket with `T` + (highest numeric suffix + 1, padded to 3), persisted." |
| Steelman | One read at `open` and writes from an in-memory list keep the store simple and fast. The tool is single-user and local, and the product lists multi-user sync as a non-goal. `all()` returns a copy of a single source of truth, so callers cannot see torn state. A `localStorage` read per call would also complicate the rule "a failed write keeps the change in memory". |
| Objection | The interface does not say who wins when two tabs of the same origin are open. Each tab holds its own in-memory list from `open`. Tab A and tab B both compute the next ID from their own copy, so both create `T013`. Whichever tab writes last overwrites the whole stored array. The other tab's ticket is lost after reload, or two tickets share an ID. The same overwrite hits `update` on a different ticket: tab B saves its stale list over tab A's saved edit. This is an unstated last-writer-wins policy where the lens asks for explicit conflict semantics. Multi-tab use is not "multi-user sync"; it is one operator with two tabs. |
| Anchored to | SYS-NFR-04 (edits and new tickets are present after reload) and FR-14 (unique ID). The interface has no test for two stores over the same storage. |
| Alternative | `create` and `update` read-modify-write: each one re-reads `support-tickets.v1`, applies the change to the fresh list, computes the ID from that list, and writes it. The signatures stay the same. Add `all(): Ticket[]  // reflects the stored list at call time`, and add a test named "two stores over one storage: both creates persist, IDs T013 and T014". |
| Cost of alternative | A JSON parse and validation on every call (12 tickets, negligible). The "failed write keeps the change in memory" rule needs a merge rule between the stale memory copy and a fresh read. `all()` now depends on storage state, so the test double for `storage` needs a shared instance. It still does not tell the operator that another tab changed something; it only stops silent loss. |
| Severity | fix |
| Response | accept: update and create re-read storage immediately before applying; signatures unchanged; add a two-store test. |

#### Card 2

| Field | Value |
| --- | --- |
| Lens / rule | `/private/tmp/factory-comparison-dashboard-20261012-r4/snapshots/factory/installed/skills/patterns-of-enterprise-application-architecture/Decision rules: Make responsibility ownership explicit before` |
| Where | `filter(tickets, {query = "", status = "", priority = ""} = {}),` on `globalThis.TicketStore`, which also owns storage keying, validation and ID generation |
| Steelman | The Cost line shows five public methods, zero pass-throughs and zero configuration, so the module is deep. FR-03 and FR-04 are tested in `test_store.cjs` without a browser, and only one script has to be loaded. `filter` is already pure and takes `tickets` as a parameter, so it does not depend on storage state. At 12 tickets a separate module is more ceremony than value. |
| Objection | `filter` is query logic over a plain array. It does not read or write the store, yet it sits in the same namespace as persistence and validation. If search later gains fields, ranking or a new criterion, it changes for a reason that has nothing to do with storage. `TicketStore` would then change for three unrelated reasons. Today this is only a placement choice. |
| Anchored to | none (taste) |
| Alternative | `globalThis.TicketFilter = { apply(tickets, {query = "", status = "", priority = ""} = {}) }` in its own script; `TicketStore` keeps `open`, `all`, `update`, `create`. |
| Cost of alternative | One more global and script tag, and one more module for the page to wire. The store's depth statement no longer lists filter semantics. A second tiny module with one method is shallower than the current design, and C-01 (no dependencies) leaves no module loader to hide it. |
| Severity | note |
| Response | overrule: a separate module is not worth it for one pure function. |
