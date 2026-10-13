## Code Review Summary

Candidate B has more CRITICAL application issues: **B: 1; A: 0**. A fresh two-tab browser reproduction shows B deleting an already persisted ticket when another tab saves an unrelated edit. A preserves the ticket in that reproduction. Both require changes because their storage fallbacks suppress failures and can overwrite recoverable data.

| Candidate | Files reviewed | CRITICAL | HIGH | MEDIUM | LOW | Total | Recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A | 10 | 0 | 3 | 1 | 0 | 4 | REQUEST CHANGES |
| B | 6 | 1 | 2 | 0 | 0 | 3 | REQUEST CHANGES |

Counts are candidate-specific, deduplicated by root cause within each application. Two findings apply to both independent implementations; repeated creation/edit symptoms are counted once. CRITICAL here identifies deletion of previously persisted tickets through ordinary supported controls. Conditional failure-state recovery defects are HIGH, with their injected preconditions disclosed below. This is an application/code review; architecture is outside this lane.

### Scope and verification

Read the complete shared `brief.md` and `evidence.md`, and all application/test files in each candidate. A: `app.js`, `store.js`, `tickets.js`, `index.html`, `styles.css`, `test_existing.cjs`, `test_dashboard.cjs`, `test_store.cjs`, `test_review.cjs`, `test_screens.cjs`. B: `app.js`, `tickets.js`, `index.html`, `styles.css`, `test_existing.cjs`, `test_dashboard.cjs`.

Fresh checks using the supplied installed Playwright/Chromium runtime:

- A: public smoke **2/2 passed**; `node --test test_store.cjs test_dashboard.cjs test_review.cjs` **44/44 passed**, zero skipped.
- B: public smoke **2/2 passed**; `node --test test_dashboard.cjs` **47/47 passed**, zero skipped.
- `node --check` passed for every JavaScript application and test file in both candidates.
- File diagnostics were requested for all nine application HTML/CSS/JS files. The available diagnostic backend reported `tsc skipped: no tsconfig found`; those responses are **not** evidence of a passing typecheck or HTML/CSS lint.
- Independent browser probes used fresh isolated contexts and localhost servers: two-tab creates/edits, same-ticket stale dialogs, throwing storage writes, malformed saved records, double-click creation, mobile validation/Tab traversal, and widths 360, 601, 620, 640, 768, and 1280. Probes produced no uncaught page errors; silent error handling is itself part of the findings.

Reproduction script and raw results are copied into this workspace: [probe script](evidence/code-review-probes.cjs) and [results](evidence/code-review-results.json). These are evidence, not candidate changes.

### Spec compliance and root-cause guard

Both preserve the twelve identical seed records and implement the requested ordinary list, case-insensitive title/customer substring search, AND filters, count/status region, empty/reset behavior, named dialogs, editing, trimmed required creation fields, associated validation errors, reload persistence under healthy storage, and keyboard dismissal/focus containment. The provided suites pass those happy-path behaviors. Text is rendered through `textContent`; no hardcoded credentials, remote product requests, or markup injection path was found in application code.

Persistence is incomplete under failure. Both continue as though a rejected write saved successfully, and both silently substitute seeds when existing data fails validation. These are root-cause-guard blockers: fix the persistence/error contract and protect the existing stored payload rather than approving the silent fallbacks. Neither suite checks visible failure behavior, preservation after a malformed load followed by save, or same-ticket dialog conflicts. B additionally lacks two-tab persistence tests. A's fake-storage tests cover sequential edits to different tickets and sequential ID allocation, which do not prove conflict safety.

## Candidate A

**Files Reviewed:** 10  
**Total Issues:** 4

### By Severity

- CRITICAL: 0
- HIGH: 3 (should fix; approval blocked)
- MEDIUM: 1 (consider fixing)
- LOW: 0

### Issues

**[HIGH] A1 — Failed persistence is reported as successful creation/editing.**  
File: `candidate-a/store.js:56`; also `store.js:73`, `app.js:4`, `app.js:139`.

The store mutates its working dataset, swallows `setItem` failures, and returns success; the UI renders the result and closes the dialog. The no-op storage substitute likewise provides no visible failure. The required persistence contract is therefore broken without warning. Trigger: quota exhaustion or blocked storage. With `Storage.prototype.setItem` made to throw `QuotaExceededError`, Create closes, T013 appears, no payload is stored, and reload returns to twelve tickets. Save similarly displays T002 as resolved/low, then reload restores open/high. The quota error is injected; no disk exhaustion was required for this reproduction.

Fix: expose write/access errors, keep the draft/dialog available with an accessible error, and commit successful UI/repository state only after storage succeeds. Add regression evidence for rejected creation and editing writes. Count both manifestations and the no-storage substitute as one failed-persistence root cause.

**[HIGH] A2 — An invalid saved record silently resets the dataset and a later save destroys recoverable tickets.**  
File: `candidate-a/store.js:18`; also `store.js:32`, `store.js:50`, `store.js:56`.

`read` collapses missing storage, malformed data, and read failure into `null`; opening substitutes seeds, and later editing persists that substitute over the original payload. Reproduction: create a legitimate T013; externally change only T001's saved priority to an unsupported value; reload; save an unrelated T002 priority edit. The UI shows twelve seeds after reload, and the next save changes the actual stored count from 13 to 12, deleting otherwise valid T013. The malformed priority was injected into localStorage and is not produced by the normal controls, hence this conditional recovery defect is HIGH rather than an ordinary-use CRITICAL finding.

Fix: distinguish an absent key from existing unreadable/invalid data; surface the load error and preserve the original payload, blocking destructive writes until explicit recovery. Do not silently drop bad records or overwrite with seeds. Replace the current fallback-only test expectation (`test_store.cjs:39`) with preservation/error regression evidence.

**[HIGH] A3 — A stale details dialog overwrites another tab's edit to an untouched field.**  
File: `candidate-a/app.js:102`; also `store.js:53` and `store.js:54`.

Although the store rereads current storage before a write, the details submit passes both field values from the old dialog. Trigger: tab one opens T002 (open/high); tab two saves its priority as low; tab one changes only status to resolved and saves. Fresh browser results show persisted open/low becoming resolved/high. The operator's status edit silently undoes the other tab's priority edit, even though priority was untouched in the submitting dialog. This is separate from A2 and A1: storage reads/writes succeed and the dataset is valid.

Fix: compare the dialog's original values with current persisted values before committing; apply only fields the operator changed and surface conflicts when the changed field is stale. Add a two-page regression for this exact sequence. A's existing different-ticket fake-storage test cannot detect it.

**[MEDIUM] A4 — The desktop row layout collapses ticket titles just above the mobile breakpoint.**  
File: `candidate-a/styles.css:22`; also `styles.css:52`.

The fixed ID/customer/status/priority tracks leave the title track only 15 px at a 601-pixel viewport while the compact layout stops at 600 px. A bounding-box probe measured the first seeded title at **15 × 492.6 px**, turning a short title into an almost one-character column; at 620 px it is **34 × 179.1 px**. This makes scanning normal tickets impractical despite no horizontal overflow. The 360/1280 tests miss this intermediate-width failure.

Fix: switch to the existing compact layout before the fixed tracks squeeze the title, or reduce those tracks sufficiently; verify readable title widths across the transition. No new layout framework is needed.

### Recommendation

**REQUEST CHANGES.** No CRITICAL defect established for A. Three HIGH correctness/error-contract defects block approval despite passing supplied tests.

## Candidate B

**Files Reviewed:** 6  
**Total Issues:** 3

### By Severity

- CRITICAL: 1 (must fix)
- HIGH: 2 (should fix; approval blocked)
- MEDIUM: 0
- LOW: 0

### Issues

**[CRITICAL] B1 — Saving from a second tab overwrites the whole dataset and deletes previously saved tickets.**  
File: `candidate-b/app.js:26`; also `app.js:23`, `app.js:169`, `app.js:260`.

Each page loads an independent in-memory ticket array once, and every save replaces the complete localStorage payload with that stale array. There is no reread/conflict check. This is reproducible using ordinary UI actions with healthy storage: open two tabs on the same origin; create a ticket in tab one; in tab two edit unrelated T002's priority and Save. Persisted count drops from **13 to 12**, permanently removing tab one's saved ticket. In a separate two-tab sequential Create probe, both tabs issue **T013**, and storage retains only the second tab's new ticket. Same-ticket dialog edits also revert another tab's priority, but that symptom is included in this single stale-snapshot finding, not counted again.

Fix: commit edits/creates against the current persisted dataset rather than blindly replacing it with the page's snapshot; allocate IDs from current records and detect conflicting stale edits. Include the exact two-page create-then-unrelated-edit and sequential-create reproductions as regression evidence. A passes these two sequential probes, but that does not establish atomic simultaneous-write safety for A.

**[HIGH] B2 — Failed persistence is reported as successful creation/editing.**  
File: `candidate-b/app.js:26`; also `app.js:173`, `app.js:262`, `app.js:272`.

`saveTickets` swallows storage errors after callers mutate state. Both callers continue rendering and closing their dialogs. The same injected `QuotaExceededError` probe used for A creates visible T013, closes the dialog, stores nothing, and loses T013 on reload; editing T002 likewise shows resolved/low then reloads open/high. There is no accessible error or retained draft. This violates reload persistence and hides a failure the operator needs to handle.

Fix: make a rejected write observable, retain the draft/dialog with an associated accessible error, and accept the operation only after persistence succeeds. Cover creation and editing error paths. This is one error-contract finding, independent of the stale-snapshot overwrite in B1.

**[HIGH] B3 — An invalid saved record silently resets the dataset and a later save destroys recoverable tickets.**  
File: `candidate-b/app.js:18`; also `app.js:20`, `app.js:26`.

The whole array must validate; any bad record triggers an undocumented seed replacement in memory without informing the operator. The next ordinary save writes the replacement over the existing payload. The same controlled reproduction used for A (valid saved T013, injected unsupported T001 priority, reload, unrelated T002 save) reduces persisted count **13 → 12** and deletes T013. Existing tests (`test_dashboard.cjs:158`) assert fallback-to-seeds only and never check preservation of the original dataset after a later write. The malformed input is injected, so this is conditional failure-state recovery, not an additional ordinary-use CRITICAL finding.

Fix: distinguish a missing key from existing malformed/unreadable storage, report the latter, and preserve its bytes while preventing accidental overwrite. Add recovery/preservation regression evidence rather than treating silent seed replacement as success.

### Recommendation

**REQUEST CHANGES.** B has the stronger release blocker: normal sequential activity in two tabs permanently deletes saved tickets. Its supplied tests are broader in several UI areas, but do not exercise that persistence scenario.

### Limits and remaining risks

No candidate edits, installs, external operations, identity key, other research reports, private trial logs, or prior benchmark findings were used. No architectural design review was performed. `test_screens.cjs` was read but not run because it writes into the candidate directory and only asserts screenshot-file existence. Browser verification used installed headless Chromium; Safari/Firefox, assistive-technology speech, physical mobile keyboards, genuinely simultaneous writes, actual quota saturation, and formal HTML/CSS lint were not checked. All storage failure/corruption preconditions are explicitly identified as injected; the two-tab destructive overwrite uses unmodified healthy storage and ordinary application controls.
