# Research: support-ticket-dashboard

1. How does the page get its ticket data, what are the fields of one record, and where is the data defined?
   Answer:
      - The data is a global array, `window.SEED_TICKETS`, defined in tickets.js:1-14. It is hard-coded with 12 records, one per line (tickets.js:2-13). There is no fetch or network call anywhere.
      - app.js:2 reads it with `for (const ticket of window.SEED_TICKETS)`.
      - Each record has six string fields: `id`, `title`, `customer`, `status`, `priority`, `description` (tickets.js:2).
      - Example: `{id: "T001", title: "Password reset link expired", customer: "Acme Labs", status: "open", priority: "high", description: "..."}` (tickets.js:2).

2. What does app.js do today with that data (rendering, event handlers, filtering, storage)?
   Answer:
      - Rendering:
        - It selects `#tickets` (app.js:1).
        - For each ticket it builds an `li` (app.js:3) holding a `button` with `type="button"` and class `ticket` (app.js:4-6).
        - The button holds three `span` lines (app.js:7-11):
          - `"<id> <title>"`
          - `customer`
          - `"<status> · <priority>"`
        - It appends the button to the `li` and the `li` to the `ul` (app.js:12-13).
        - It sets text with `textContent` (app.js:9).
        - `description` is never rendered.
      - Event handlers: none. There is no `addEventListener` or `onclick`.
      - Filtering: none. `#search`, `#status-filter`, `#priority-filter`, `#reset` and `#new-ticket` are never referenced in app.js.
      - Counts and empty state:
        - `#result-count` is never updated. It stays the static "12 tickets" from index.html:21.
        - `#empty-state` is never shown or hidden. It stays `hidden` (index.html:23).
      - Storage: none.

3. What elements, ids, roles and accessible names exist in index.html? Which scripts load, in what order and how (defer, module)?
   Answer:
      - Document:
        - `<html lang="en">` (index.html:2).
        - `<title>Support tickets</title>` (index.html:6).
        - Viewport meta (index.html:5).
        - `<link rel="stylesheet" href="styles.css">` (index.html:7).
      - Landmarks and headings:
        - `<main>` (index.html:12).
        - `<h1>Support tickets</h1>` (index.html:13).
      - Filter container: `<div class="filters">` (index.html:14).
      - Controls and their accessible names:
        - `input#search`, `type="search"`, wrapped in `<label>Search tickets ...</label>`. The accessible name is "Search tickets" (index.html:15).
        - `select#status-filter` with `aria-label="Status filter"` and a wrapping label "Status filter" (index.html:16).
          - Options: "All statuses" (value ""), `open`, `pending`, `resolved`.
        - `select#priority-filter` with `aria-label="Priority filter"` and a wrapping label "Priority filter" (index.html:17).
          - Options: "All priorities" (value ""), `low`, `medium`, `high`.
        - `button#reset`, `type="button"`, text "Reset filters" (index.html:18).
        - `button#new-ticket`, `type="button"`, text "New ticket" (index.html:19).
      - Result area:
        - `p#result-count` with `role="status"`, text "12 tickets" (index.html:21).
        - `ul#tickets`, empty in the markup and filled by app.js (index.html:22).
        - `p#empty-state` with `hidden`, text "No tickets match your filters." (index.html:23).
      - Rendered ticket buttons (from app.js:4-11):
        - Role is button, class `ticket`.
        - The accessible name is the concatenated span text, for example "T001 Password reset link expired Acme Labs open · high".
      - Not present in the markup: `<dialog>`, `<form>`, `<textarea>`.
      - Scripts, both in `<head>` with `defer` and neither `type="module"`:
        1. `<script src="tickets.js" defer>` (index.html:8)
        2. `<script src="app.js" defer>` (index.html:9)
      - Because both are `defer`, they run in document order after parsing. tickets.js therefore sets `window.SEED_TICKETS` before app.js reads it.

4. What does styles.css define: layout, breakpoints, focus styles, dialog styles, classes used by no current markup?
   Answer:
      - Layout:
        - `* {box-sizing: border-box}` (styles.css:1).
        - `body` margin 0, system-ui font (styles.css:2).
        - `main` max-width 1100px, centered, padding 24px (styles.css:3).
        - `.filters` is a wrapping flex row with gap 12px and `align-items: end` (styles.css:4).
        - `label` is a grid with gap 5px (styles.css:5).
        - Form controls: `font: inherit; max-width: 100%` (styles.css:6); input/select/textarea padding 8px and `min-width: 0` (styles.css:7); button `cursor: pointer; padding: 9px` (styles.css:8).
        - `#tickets` has no list style or padding (styles.css:10), and `#tickets li` has margin 12px 0 (styles.css:11).
        - `.ticket` is a grid, gap 5px, full width, left-aligned, white background, 1px #aaa border (styles.css:12).
      - Breakpoints: one only, `@media (max-width: 600px)` (styles.css:20). It sets `main` padding to 16px and `.filters` to `display: grid`.
      - Focus styles: `:focus-visible { outline: 3px solid #245ac5; outline-offset: 2px; }` (styles.css:9). It is the only focus rule.
      - Dialog styles:
        - `dialog` width `min(560px, calc(100% - 32px))`, max-height `calc(100% - 32px)`, overflow auto, padding 20px (styles.css:14).
        - `dialog form` is a grid with gap 12px (styles.css:15).
        - `dialog textarea` is width 100%, min-height 90px, `resize: vertical` (styles.css:16).
        - `dialog::backdrop` is `#0006` (styles.css:17).
      - Classes and selectors with no matching current markup:
        - `.actions` (styles.css:18)
        - `.error` (styles.css:19)
        - `.ticket strong` (styles.css:13). app.js creates only `span`s, so the `.ticket span` half of that rule is used.
        - All `dialog`, `dialog form` and `dialog textarea` rules (styles.css:14-17). No dialog, form or textarea exists in index.html or app.js.

5. What does test_existing.cjs check, how does it serve the page and find ticket buttons, and which environment does it need?
   Answer:
      - Environment:
        - It needs the env var `PLAYWRIGHT_MODULE` and throws if it is unset: "no runtime will be installed or skipped" (test_existing.cjs:6).
        - It `require`s `chromium` from that path (test_existing.cjs:7) and `expect` from `<PLAYWRIGHT_MODULE>/test` (test_existing.cjs:8).
        - It uses headless Chromium (test_existing.cjs:22).
        - The root is `process.cwd()` (test_existing.cjs:9), so it must run from the repo directory.
        - It is CommonJS (`.cjs`) and uses only Node built-ins: fs, http, path (test_existing.cjs:1-3).
      - Serving:
        - A `http.createServer` static server (test_existing.cjs:10-18) listens on 127.0.0.1 with port 0, an ephemeral port (test_existing.cjs:19).
        - "/" maps to /index.html (test_existing.cjs:11).
        - Paths outside the root get 403 (test_existing.cjs:12). Read errors get 404 (test_existing.cjs:14).
        - Content-Type is set for .html, .js and .css only (test_existing.cjs:15).
        - The page is loaded with `page.goto("http://127.0.0.1:<port>")` (test_existing.cjs:24).
      - Finding ticket buttons: `page.getByRole("button", {name: /T\d{3}/})` `.or(` the same for role `link`) (test_existing.cjs:25).
      - Checks:
        1. `expect(openings).toHaveCount(12)` (test_existing.cjs:26).
        2. A button or link whose name matches both `\bT001\b` and "Password reset link expired" (regex at test_existing.cjs:27) appears via `.waitFor()` (test_existing.cjs:28).
        3. `page.getByLabel("Search tickets", {exact: true}).waitFor()` (test_existing.cjs:29).
      - Output:
        - On success it prints `BENCHMARK_GRADE={"tests":2,"failures":0,"errors":0,"skipped":0}` (test_existing.cjs:30). The count of 2 is hard-coded, although the code has three assertions.
        - On error it prints `BENCHMARK_GRADE=` with `errors: 1` and sets exit code 1 (test_existing.cjs:36).
        - The browser and server are always closed in `finally` (test_existing.cjs:31-34).

6. Is any browser storage (localStorage, sessionStorage, IndexedDB) or dialog element used anywhere in the code?
   Answer:
      - `localStorage`, `sessionStorage` and `indexedDB`: not used anywhere in the code (searched all five files; no matches).
      - A `<dialog>` element in markup or JS (`showModal` etc.): not used. The only dialog references are the CSS rules at styles.css:14-17.
      - `#new-ticket` (index.html:19) has no handler.

7. What do the existing records look like regarding id format and value sets for status and priority?
   Answer:
      - There are 12 records, ids T001 to T012 (tickets.js:2-13). The format is the letter "T" plus a 3-digit zero-padded number, sequential and unique. This matches the test regex `T\d{3}` (test_existing.cjs:25).
      - `status` values in use are `open`, `pending` and `resolved` (tickets.js:2-13). They match the `#status-filter` options (index.html:16).
      - `priority` values in use are `low`, `medium` and `high` (tickets.js:2-13). They match the `#priority-filter` options (index.html:17).
      - Counts by status: open 5 (T001, T002, T007, T009, T012), pending 4 (T003, T005, T006, T010), resolved 3 (T004, T008, T011).
      - Counts by priority: high 4 (T001, T002, T006, T011), medium 4 (T004, T005, T009, T010), low 4 (T003, T007, T008, T012).
      - All values are lowercase strings. Customers repeat: Acme Labs ×3, Northwind ×2, Bluebird Studio ×2, Cedar Works ×2, Maple Partners ×2, Harbor Design ×1.

8. Does Pond record earlier sessions about this repository? (Say "not found" if Pond tools are unavailable.)
   Answer:
      - not found. No Pond tools are available in this session. A tool search for "pond" returned no matches. No earlier session ids can be cited.
