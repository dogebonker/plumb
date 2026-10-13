## Summary

**Candidate A: BLOCK. Candidate B: BLOCK.** Both treat failed persistence as a successful save. A additionally discards earlier unsaved changes during later mutations; B overwrites other tabs’ saved records even when the operations happen sequentially.

A has a useful repository boundary and preserves sequential changes to different tickets across tabs. B’s single-file structure is reasonable for this application; its problem is ownership of stale data, not file count. These statuses concern operational data integrity, beyond the narrow smoke check.

## Evidence and verification

Reviewed application sources and relevant tests in both candidates, plus the shared brief and evidence. The brief requires saves and created tickets to survive reload ([brief.md:3](brief.md), [brief.md:9](brief.md)).

Fresh verification:

- Both public smoke checks passed: **2 tests, zero failures/errors/skips each**.
- A’s repository tests passed: **17/17**.
- Independent Chromium probes exercised each candidate through its accessible UI, using isolated contexts and a localhost static server.

| Probe | Candidate A | Candidate B |
|---|---|---|
| After an initial persisted edit, make `Storage.setItem` throw `QuotaExceededError`; create Alpha | Dialog closes; list shows 13 | Dialog closes; list shows 13 |
| Keep writes failing; create Beta | Still 13; **Alpha disappears** | 14; Alpha and Beta remain in memory |
| Reload afterward | Both new tickets absent | Both new tickets absent |
| Open two tabs before any changes; create Alpha in one, then Beta in the other | Alpha/T013 and Beta/T014 survive | **Only Beta/T013 survives** |
| Those two tabs edit different tickets: T001 status, then T002 priority | Both changes survive | **T001 status reverts** |
| Those two tabs edit different fields of T001: status, then priority | **Earlier status reverts** | **Earlier status reverts** |

Write failures were deliberately injected. The cross-tab losses required no storage failure or simultaneous execution.

## Candidate A

### Architectural status: `BLOCK`

**A1 — P1 blocker: the persistence interface reports success after failure and can discard unsaved work before reload.**

`create()` updates memory, suppresses `setItem` failure, and returns a normal ticket. `update()` has the same success-shaped failure path. The next mutation prefers the old persisted array over current memory, so a failed create can disappear immediately upon another create ([store.js:50](candidate-a/store.js), [store.js:69](candidate-a/store.js)).

The UI receives no persistence outcome and closes the dialog after the mutation ([app.js:100](candidate-a/app.js), [app.js:139](candidate-a/app.js)). When storage access itself fails, the fallback adapter also silently accepts writes ([app.js:2](candidate-a/app.js)).

**Smallest sound fix:** construct the prospective next array without modifying committed memory, attempt persistence, and return an explicit failure if it fails. Commit repository memory and close the dialog only after successful storage. Keep the draft available with an accessible error and retry action. The unavailable-storage adapter must also communicate failure.

**A2 — P2 observed concurrency risk: refreshing storage at mutation time does not protect unchanged fields from stale dialogs.**

`get()` reads the repository’s cached array. Opening details copies both values into the form; saving always submits both. Although `update()` rereads storage, it replaces both supplied fields, including an unchanged value originating from the stale tab ([store.js:42](candidate-a/store.js), [store.js:50](candidate-a/store.js), [app.js:83](candidate-a/app.js), [app.js:102](candidate-a/app.js)).

**Fix:** retain the dialog-opening snapshot and submit only changed fields. Detect a conflict when a changed field no longer matches its opening value. Refreshing the list when other tabs change storage improves visibility, but does not alone protect a dialog already open.

The tests named around two repositories exercise sequential calls against a synchronous fake store. They establish preservation for those sequences, not concurrent commit safety or stale forms ([test_store.cjs:132](candidate-a/test_store.cjs), [test_store.cjs:181](candidate-a/test_store.cjs)).

### Boundaries worth retaining

The repository receives storage explicitly, validates allowed mutations, returns copies, and owns creation validation. Those are useful, testable boundaries ([store.js:31](candidate-a/store.js), [store.js:46](candidate-a/store.js), [store.js:59](candidate-a/store.js)). Rendering uses `textContent`, keeping ticket text outside HTML parsing ([app.js:15](candidate-a/app.js)).

**Strongest argument against approval:** this boundary conceals the application’s most consequential fact—whether the ticket was saved—and its attempt to preserve other writers actively discards unpersisted local work.

**Strongest counterargument to blocking:** the brief describes a small local application, and the demonstrated same-tab loss requires a storage failure. That limits frequency, but does not justify closing an unsuccessful save or silently losing its draft.

## Candidate B

### Architectural status: `BLOCK`

**B1 — P1 blocker: every save replaces the entire persisted collection from a tab’s startup snapshot.**

Tickets load once into `state`; `saveTickets()` serializes that complete array. Details and creation mutate the same cached state, with no refresh or conflict check before writing ([app.js:23](candidate-b/app.js), [app.js:25](candidate-b/app.js), [app.js:169](candidate-b/app.js), [app.js:260](candidate-b/app.js)).

This causes the confirmed unrelated-ticket rollback and lost creation. ID allocation uses that stale array too, so both tabs issue T013; the later save replaces the earlier ticket ([app.js:191](candidate-b/app.js)).

**Smallest immediate repair:** centralize creation and update commits in one function that obtains the latest valid persisted collection, applies only the intended mutation, writes successfully, then replaces in-memory state. Allocate IDs from that refreshed collection. Preserve the opening snapshot for field-conflict detection.

That repair addresses the demonstrated sequential losses. It must not be represented as full simultaneous-writer safety: the read/modify/write sequence still needs serialization if multiple tabs may commit concurrently.

**B2 — P1 blocker: storage failure is indistinguishable from success.**

`saveTickets()` catches and discards storage errors. Callers proceed to render, close, and, for creation, reset the form ([app.js:25](candidate-b/app.js), [app.js:173](candidate-b/app.js), [app.js:262](candidate-b/app.js), [app.js:270](candidate-b/app.js)).

Unlike A, successive failed creations remain in memory during this probe. Both still disappear after reload.

**Fix:** make commit return a persistence outcome; keep the dialog and draft on failure. Avoid publishing a mutation into committed application state before its durable write succeeds.

### Boundaries worth retaining

The filtering, ID allocation, and creation validation already have identifiable function boundaries. There is no need to split the file merely to increase modularity ([app.js:30](candidate-b/app.js), [app.js:191](candidate-b/app.js), [app.js:200](candidate-b/app.js)).

Modal lifecycle handling is shared, tracks each opener, and accounts for hidden or disabled controls. Creation also guards submission after closure ([app.js:93](candidate-b/app.js), [app.js:128](candidate-b/app.js), [app.js:251](candidate-b/app.js)). Rendering uses `textContent` ([app.js:42](candidate-b/app.js)).

**Strongest argument against approval:** a routine second browser tab can destroy successfully stored, unrelated operator work with no warning.

**Strongest counterargument to blocking:** multi-tab behavior is not an explicit acceptance requirement. However, single-writer ownership is neither enforced nor communicated, and the failure occurs during sequential ordinary actions.

## Root cause

Both implementations equate an in-memory mutation with a durable commit. Neither gives the UI a usable failure result.

Their data-authority choices then diverge: A intermittently trusts persisted storage over newer memory; B always trusts its tab snapshot over newer persisted storage. A’s reread narrows some stale-write failures but does not establish conflict handling or atomic commits.

## Suggestions, separate from blockers

1. **P2, small scope: distinguish missing storage from invalid or unreadable storage.** Both silently fall back to seeds. A later successful save can replace the unrecognized payload. Preserve that payload and expose a recovery state before allowing replacement ([A store.js:15](candidate-a/store.js), [B app.js:15](candidate-b/app.js)). This is code-backed risk; corrupted-data recovery was not runtime-tested here.

2. **P2, small scope: validate identity at the storage boundary.** Both validators accept any string ID and duplicate IDs, while lookup selects the first matching record. Validate nonempty, unique identities before accepting the collection ([A store.js:7](candidate-a/store.js), [A store.js:43](candidate-a/store.js), [B app.js:9](candidate-b/app.js), [B app.js:163](candidate-b/app.js)). Imported/corrupted duplicate identities were not runtime-tested.

3. **P1 with the fixes: add behavioral regressions for the demonstrated failures.** Cover write rejection after existing persisted data, two sequential failed writes, two tabs creating tickets, and two tabs editing different fields. The browser harnesses normally create a single page per fresh context, leaving shared-storage behavior outside that setup ([A test_dashboard.cjs:29](candidate-a/test_dashboard.cjs), [B test_dashboard.cjs:37](candidate-b/test_dashboard.cjs)).

## Trade-offs

| Option | Benefit | Cost / limitation |
|---|---|---|
| Explicit commit success/failure | Removes silent persistence loss; modest changes in either candidate | UI needs an accessible save-error state |
| Refresh latest data and apply changed fields | Prevents demonstrated sequential unrelated-record loss | Does not alone serialize simultaneous writes |
| Enforce one writer or serialize cross-tab commits | Establishes a defensible ownership rule | More lifecycle and conflict handling |
| Larger repository/framework rewrite | Could introduce broader architecture | Unnecessary for these defects; adds migration work |

Recommendation: retain each candidate’s current structure, repair commit semantics first, and make the writer-ownership policy explicit. Approval should require regression evidence for those fixes.

Skipped full UI-suite reruns, screen-reader/browser-matrix checks, and simultaneous race stress tests; candidate files were unchanged.
Remaining risk: both candidates currently conceal persistence failure, and B demonstrably loses other tabs’ saved work.
