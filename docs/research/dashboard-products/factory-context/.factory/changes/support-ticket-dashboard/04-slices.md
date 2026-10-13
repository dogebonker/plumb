# Slices: support-ticket-dashboard

Test files: `test_store.cjs` (Node `node:test`, fake `Storage`, loads `store.js` with `require`) and `test_dashboard.cjs` (Playwright, same inline static-server pattern as `test_existing.cjs`). The browser-check wrapper runs every `test*.cjs`, so both run in `Verify`. `test_existing.cjs` must stay green and is never edited. Test names below are the stems the test plan in `03-interface.md` names.

## Slices
### 01 Tracer: list and filters from the store
Milestone: 1
Covers: FR-01, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08
Modules: .
Tests first: `test_store.cjs` (the seed is loaded in the main realm, not through a `vm` context, so `deepStrictEqual` compares same-realm values) :: open lists T001 to T012 in order; open falls back to the seed for non-JSON, a non-array and a bad status; list matches title or customer case-insensitively; list by status and priority; combined AND; seed array untouched (C-02). `test_dashboard.cjs` :: first visit lists the twelve seeded tickets (red-exempt: FR-01 already holds in today's page, so this test passes against the stub); first visit shows 12 ticket buttons named with ID and title; search, status and priority filters combine; count text and empty message; Reset filters restores everything.
Allowed files: `store.js`, `app.js`, `index.html`, `styles.css`, `test_store.cjs`, `test_dashboard.cjs`
Verify: `node --test test_store.cjs`; `/private/tmp/fb-neamoi0s/browser-check/browser-check`

### 02 Ticket details: open, edit, save, cancel
Milestone: 2
Covers: FR-02, FR-09, FR-10, FR-11, FR-12, FR-19, FR-20, NFR-01
Modules: .
Tests first: `test_store.cjs` :: get returns a copy and undefined for T999; update persists priority, throws RangeError for status "closed" with nothing stored, returns undefined for an unknown ID; a new open on the same storage returns the update (FR-02); two repos on one fake storage keep both repos' edits. `test_dashboard.cjs` :: opening T002 shows its title, customer, description, status, priority in the `Ticket details` dialog; Save changes updates the row and survives reload; a ticket that stops matching the status filter leaves the list; Cancel and Escape change nothing; focus returns to the ticket's button (or `Search tickets` when it left the list); Tab and Shift+Tab stay inside the dialog.
Allowed files: `store.js`, `app.js`, `index.html`, `styles.css`, `test_store.cjs`, `test_dashboard.cjs`
Verify: `node --test test_store.cjs`; `/private/tmp/fb-neamoi0s/browser-check/browser-check`

### 03 New ticket: validate, create, persist
Milestone: 2
Covers: FR-13, FR-14, FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, NFR-01, SYS-NFR-01
Modules: .
Tests first: `test_store.cjs` :: create trims "  Printer jam  "; whitespace-only fields return one error per field and store nothing; first create is T013, second T014, next after reopening T015; two repos on one fake storage never issue the same ID and the first repo's edit is not lost; an out-of-set status throws RangeError. `test_dashboard.cjs` :: New ticket opens an empty form with status open and priority medium; an invalid submit keeps the dialog open with `aria-invalid` and `aria-describedby` error text and no new row; Create ticket closes the dialog and shows the row with the chosen status and priority; Cancel and Escape create nothing; the created ticket survives reload and can be searched, opened and edited; Tab and Shift+Tab stay inside the dialog; focus returns to `New ticket`.
Allowed files: `store.js`, `app.js`, `index.html`, `styles.css`, `test_store.cjs`, `test_dashboard.cjs`
Verify: `node --test test_store.cjs`; `/private/tmp/fb-neamoi0s/browser-check/browser-check`

### 04 Hierarchy, 360 px fit and stable names
Milestone: 2
Covers: FR-21, NFR-02, C-01, C-02, C-03
Modules: .
Tests first: `test_dashboard.cjs` :: at 360x740 the page has no horizontal overflow and every dialog control is inside the viewport; at 1280 px a ticket row shows ID and title most prominently with customer, status and priority readable beside them; every stable name from the task is found by role and name; no source file contains a remote URL (C-01). Visual hierarchy follows `DESIGN.md` (status and priority as text, one filled primary button per surface, visible focus).
Allowed files: `styles.css`, `index.html`, `app.js`, `test_dashboard.cjs`
Verify: `/private/tmp/fb-neamoi0s/browser-check/browser-check`

## Open questions
