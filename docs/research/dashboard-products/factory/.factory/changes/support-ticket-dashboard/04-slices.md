# Slices: support-ticket-dashboard

Conventions for every slice. Logic tests: `node --test test_store.cjs` (plain Bash). Browser tests: run exactly `/private/tmp/fb-zt0pwkma/browser-check/browser-check` with no arguments, prefixes, pipes or redirects; it runs `node --test` over every `test*.cjs`, so it also keeps `test_existing.cjs` green. Browser tests in `test_dashboard.cjs` use `PLAYWRIGHT_MODULE` like `test_existing.cjs` and serve the repo on a temporary 127.0.0.1 port. No lint step (`check_command: none`). All files sit at the repository root and fit the Layout (`existing`).

## Slices
### 01 Tracer: list from the store
Milestone: 1
Covers: FR-01, FR-02, FR-17 (load half), FR-18, C-01
Modules: .
Tests first: `test_store.cjs` :: open() on empty storage returns the 12 seeds unchanged; corrupt JSON, wrong shape, invalid status and a throwing storage all give the seeds - asserts FR-02, FR-18 | `test_dashboard.cjs` :: lists all 12 seeded tickets with ID, title, customer, status, priority and "12 tickets"; makes no request outside 127.0.0.1 - asserts FR-01, C-01
Allowed files: store.js, app.js, index.html, test_store.cjs, test_dashboard.cjs
Verify: `node --test test_store.cjs`; `/private/tmp/fb-zt0pwkma/browser-check/browser-check`
Notes: `store.js` gets `STATUSES`, `PRIORITIES`, `open`, `all` (stubs for the rest are not exported yet); `app.js` renders rows from `TicketStore.open().all()`, keeping `button.ticket` rows and `data-id`; `index.html` adds the `store.js` script tag between `tickets.js` and `app.js`.

### 02 Find tickets: search, filters, count, empty state, reset
Milestone: 2
Covers: FR-03, FR-04, FR-05, FR-06, FR-07
Modules: .
Tests first: `test_store.cjs` :: filter "acme" returns T001, T005, T011 and "EXPORT" returns T002; filter combines query, status and priority with AND (acme+pending+medium returns T005); surrounding whitespace of the query is ignored - asserts FR-03, FR-04 | `test_dashboard.cjs` :: typing narrows the list; result count in the status region reads "3 tickets" for resolved and "1 ticket" for one match; no match shows "No tickets match your filters." and "0 tickets"; Reset filters clears all three controls and leaves stored tickets unchanged - asserts FR-03 to FR-07
Allowed files: store.js, app.js, index.html, styles.css, test_store.cjs, test_dashboard.cjs
Verify: `node --test test_store.cjs`; `/private/tmp/fb-zt0pwkma/browser-check/browser-check`

### 03 Inspect and edit a ticket
Milestone: 2
Covers: FR-08, FR-09, FR-10, FR-16 (details dialog), FR-17 (edit half), SYS-NFR-02 (details dialog)
Modules: .
Tests first: `test_store.cjs` :: update persists and a reopened store returns it; unknown id returns null; invalid status throws RangeError; two stores over one storage keep both edits - asserts FR-09, FR-17 | `test_dashboard.cjs` :: opening T002 shows title, customer, description, status, priority in "Ticket details"; saving T001 as resolved updates the list and survives reload; Cancel and Escape leave T003 low and return focus to its row button; Tab and Shift+Tab cycle inside the dialog - asserts FR-08, FR-09, FR-10, FR-16
Allowed files: store.js, app.js, index.html, styles.css, test_store.cjs, test_dashboard.cjs
Verify: `node --test test_store.cjs`; `/private/tmp/fb-zt0pwkma/browser-check/browser-check`
Notes: introduces the shared dialog helpers in `app.js` (opener memory, focus return on close, Tab trap) that slice 04 reuses.

### 04 Create a ticket
Milestone: 3
Covers: FR-11, FR-12, FR-13, FR-14, FR-15, FR-16 (New ticket dialog), FR-17, SYS-NFR-01, SYS-NFR-02 (New ticket dialog)
Modules: .
Tests first: `test_store.cjs` :: create trims title, customer and description; whitespace-only fields return an error per field and create nothing; first created ticket is T013 and persists; two stores over one storage create T013 then T014 - asserts FR-12, FR-13, FR-14, SYS-NFR-01 | `test_dashboard.cjs` :: New ticket opens with defaults open and medium; invalid submit keeps the dialog open with messages tied by aria-describedby, aria-invalid set, first invalid field focused and the list unchanged; a valid ticket survives reload, can be searched, opened and edited; Cancel and Escape create nothing, discard text and return focus to New ticket; Tab cycles inside - asserts FR-11 to FR-17
Allowed files: store.js, app.js, index.html, styles.css, test_store.cjs, test_dashboard.cjs
Verify: `node --test test_store.cjs`; `/private/tmp/fb-zt0pwkma/browser-check/browser-check`

### 05 Honest storage and layout hardening
Milestone: 3
Covers: NFR-01, NFR-02, NFR-03, C-02, SYS-NFR-02, SYS-NFR-03, SYS-NFR-04 (failed write)
Modules: .
Tests first: `test_store.cjs` :: a storage whose setItem throws keeps the change in memory and sets persisted to false - asserts SYS-NFR-04 | `test_dashboard.cjs` :: with localStorage writes throwing, a save shows the save-warning note; at 360 px and 1280 px there is no horizontal page overflow and every dialog control lies inside the viewport horizontally and is reachable; every action works by keyboard alone with a visible focus outline; status and priority appear as visible text in the list and dialogs; the stable accessible names and labels exist - asserts NFR-01 to NFR-03, C-02
Allowed files: store.js, app.js, index.html, styles.css, test_store.cjs, test_dashboard.cjs
Verify: `node --test test_store.cjs`; `/private/tmp/fb-zt0pwkma/browser-check/browser-check`
Notes: adds `persisted` and the `#save-warning` element; any overflow or focus fixes found by the tests land in `styles.css`/`app.js`.

## Coverage check
FR-01 to FR-18: 01 (01, 02, 18), 02 (03 to 07), 03 (08 to 10), 04 (11 to 15), FR-16 in 03 and 04, FR-17 in 01, 03, 04. NFR-01 to 03, C-02: 05. C-01: 01. SYS-NFR-01: 04. SYS-NFR-02: 03, 04, 05. SYS-NFR-03: 05. SYS-NFR-04: 01, 03, 04, 05. `tickets.js` stays unchanged in every slice (not in any Allowed files).

## Open questions
