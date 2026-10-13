# Research: support-ticket-dashboard

Method: questions were written without the product document and answered by a fresh sub-agent from a `git archive` export of `change_base_commit` (no worktree: operator policy). Pond: not available.

1. How does the page load and wire its scripts and styles (index.html), and in what order do tickets.js and app.js run?
   Answer:
   - Stylesheet: `<link rel="stylesheet" href="styles.css">` in head (index.html:7).
   - Scripts: `<script src="tickets.js" defer></script>` (index.html:8) then `<script src="app.js" defer></script>` (index.html:9). Both are classic scripts (no `type="module"`), both in `<head>` with `defer`.
   - Order: deferred classic scripts execute in document order after parsing, so tickets.js runs first (sets `window.SEED_TICKETS`, tickets.js:1), then app.js (reads it, app.js:2). No other scripts, no inline scripts.
   - Doc: `<!doctype html>`, `lang="en"` (index.html:1-2), charset utf-8 (index.html:4), viewport meta `width=device-width, initial-scale=1` (index.html:5), title "Support tickets" (index.html:6).

2. What does app.js do today with window.SEED_TICKETS, and what DOM does it build for each ticket (element types, classes, text, accessible names)?
   Answer:
   - app.js:1 `const list = document.querySelector("#tickets");` (top-level `const`, no IIFE/module wrapper).
   - app.js:2 loops `for (const ticket of window.SEED_TICKETS)`; the array is read directly, not copied, not filtered, not sorted, no guard if undefined.
   - Per ticket (app.js:3-13):
     - `li` (app.js:3), no class, no attributes.
     - `button` (app.js:4) with `type="button"` (app.js:5), `className = "ticket"` (app.js:6). No id, no data-*, no aria-* attributes, no click/other listeners.
     - Three `span` children (app.js:7-11), no class, text set via `textContent` (app.js:9):
       1. `${ticket.id} ${ticket.title}` e.g. "T001 Password reset link expired"
       2. `ticket.customer`
       3. `${ticket.status} · ${ticket.priority}` (middle dot U+00B7), e.g. "open · high"
     - `ticket.description` is not rendered.
     - Button appended to li (app.js:12), li appended to `#tickets` (app.js:13).
   - Accessible name: no aria-label; the name comes from button content, i.e. the three span texts concatenated (computed by browser, not set in code). The test relies on it matching `/T\d{3}/` and containing "T001" and "Password reset link expired" (test_existing.cjs:25,27).
   - Nothing else in app.js (14 lines total): no updating of `#result-count`, no toggling of `#empty-state`.

3. What controls and regions exist in index.html (ids, labels, aria attributes, roles, hidden elements), and which have any behavior attached in app.js?
   Answer:
   Elements (index.html):
   - `<main>` (12) wrapping everything; `<h1>Support tickets</h1>` (13).
   - `div.filters` (14).
   - `#search`: `<input id="search" type="search">` inside `<label>Search tickets ...</label>` (15). Name via wrapping label; no aria attributes.
   - `#status-filter`: `<select id="status-filter" aria-label="Status filter">` inside `<label>Status filter ...` (16). Options: "" -> "All statuses", `open`, `pending`, `resolved` (option values are the text; no value attr on the last three).
   - `#priority-filter`: `<select id="priority-filter" aria-label="Priority filter">` inside `<label>Priority filter ...` (17). Options: "" -> "All priorities", `low`, `medium`, `high`.
   - `#reset`: `<button id="reset" type="button">Reset filters</button>` (18).
   - `#new-ticket`: `<button id="new-ticket" type="button">New ticket</button>` (19).
   - `#result-count`: `<p id="result-count" role="status">12 tickets</p>` (21). Static, hard-coded text "12 tickets"; role=status (implicit live region).
   - `#tickets`: `<ul id="tickets"></ul>` (22), empty in markup, populated by app.js.
   - `#empty-state`: `<p id="empty-state" hidden>No tickets match your filters.</p>` (23). Only `hidden` element.
   - No `<dialog>`, `<form>`, `<textarea>`, or other aria-live/aria-describedby/roles beyond `role="status"` in index.html.

   Behavior attached in app.js: only `#tickets` is touched (app.js:1,13). `#search`, `#status-filter`, `#priority-filter`, `#reset`, `#new-ticket`, `#result-count`, `#empty-state` have NO behavior (no references, no listeners anywhere in app.js).

4. Does any code today read or write browser storage (localStorage, sessionStorage, cookies, IndexedDB)? Does any code define dialogs or forms?
   Answer:
   - localStorage / sessionStorage / document.cookie / indexedDB: not found in any file (grep-level: app.js, tickets.js, test_existing.cjs, index.html contain none).
   - Dialogs/forms: not found in JS or HTML (no `<dialog>`, `<form>`, `showModal`, `createElement("dialog"|"form")`). Only CSS selectors for them exist: `dialog` rules (styles.css:14-17), `dialog form`, `dialog textarea`, `dialog::backdrop`, plus `textarea` in shared rules (styles.css:6-7), but no matching markup exists.

5. What shape do records in tickets.js have (fields, ID format, value sets for status and priority, counts)?
   Answer:
   - Single global `window.SEED_TICKETS = [ ... ];` (tickets.js:1-14), plain array of object literals, one per line (tickets.js:2-13). Count: 12.
   - Fields (all strings, all present in all 12): `id`, `title`, `customer`, `status`, `priority`, `description`.
   - ID format: `"T"` + 3-digit zero-padded, sequential T001..T012 (tickets.js:2-13).
   - status values used: `open`, `pending`, `resolved` (counts: open 5 [T001,T002,T007,T009,T012]; pending 4 [T003,T005,T006,T010]; resolved 3 [T004,T008,T011]). No declared enum in code; matches the select options in index.html:16.
   - priority values used: `low`, `medium`, `high` (low 4 [T003,T007,T008,T012]; medium 4 [T004,T005,T009,T010]; high 4 [T001,T002,T006,T011]). Matches index.html:17.
   - Customers (string): Acme Labs (T001,T005,T011), Northwind (T002,T006), Bluebird Studio (T003,T010), Cedar Works (T004,T009), Maple Partners (T007,T012), Harbor Design (T008).
   - No timestamps, no assignee, no other fields. No exports/modules; plain global.

6. What does styles.css define for layout, focus, dialogs, the ticket buttons, errors and narrow viewports (max-width media queries)?
   Answer:
   (20 lines total.)
   - Layout:
     - `* { box-sizing: border-box; }` (1); body margin 0, `system-ui, sans-serif`, color #202124 (2).
     - `main { max-width: 1100px; margin: auto; padding: 24px; }` (3).
     - `.filters { display: flex; flex-wrap: wrap; gap: 12px; align-items: end; }` (4).
     - `label { display: grid; gap: 5px; }` (5).
     - `input, select, textarea, button { font: inherit; max-width: 100%; }` (6); `input, select, textarea { padding: 8px; min-width: 0; }` (7); `button { cursor: pointer; padding: 9px; }` (8).
     - `#tickets { list-style: none; padding: 0; }` (10); `#tickets li { margin: 12px 0; }` (11).
   - Focus: `:focus-visible { outline: 3px solid #245ac5; outline-offset: 2px; }` (9). Only focus rule; no `:focus` or `outline: none` rules.
   - Ticket buttons: `.ticket { display: grid; gap: 5px; width: 100%; text-align: left; background: white; border: 1px solid #aaa; }` (12); `.ticket strong, .ticket span { overflow-wrap: anywhere; }` (13). (No `strong` is created by app.js; no `.ticket` hover/state/status/priority styles; no color/font-weight differentiation of the spans.)
   - Dialogs: `dialog { width: min(560px, calc(100% - 32px)); max-height: calc(100% - 32px); overflow: auto; padding: 20px; }` (14); `dialog form { display: grid; gap: 12px; }` (15); `dialog textarea { width: 100%; min-height: 90px; resize: vertical; }` (16); `dialog::backdrop { background: #0006; }` (17). `.actions { display: flex; gap: 10px; flex-wrap: wrap; }` (18). All unused by current HTML/JS.
   - Errors: `.error { color: #a01818; font-size: .9rem; }` (19). Unused by current HTML/JS.
   - Narrow viewports: one media query, `@media (max-width: 600px) { main { padding: 16px; } .filters { display: grid; } }` (20). No other media queries.
   - Not found: styles for `[hidden]` / `#empty-state` / `#result-count`, no CSS variables, no `prefers-*` queries.

7. How does test_existing.cjs serve the app and what does it assert about the DOM?
   Answer:
   (36 lines; CommonJS, Node built-ins fs/http/path, test_existing.cjs:1-3.)
   - Requires env `PLAYWRIGHT_MODULE`, throws if unset (6); loads `chromium` from it (7) and `expect` from `path.join(PLAYWRIGHT_MODULE, "test")` (8).
   - Serving: `root = process.cwd()` (9); `http.createServer` static server (10-18): `/` maps to `/index.html`, otherwise the decoded pathname (11); resolved path must start with `root + path.sep` else 403 (12); read error -> 404 (14); Content-Type by extension for .html/.js/.css, else application/octet-stream (15). Listens on `127.0.0.1` port 0 (random) (19). Runs headless chromium (22), `page.goto("http://127.0.0.1:<port>")` (24). Closes browser and server in `finally` (32-33).
   - DOM assertions:
     1. `page.getByRole("button", {name: /T\d{3}/})` `.or(` link with same name) has count 12 (25-26).
     2. A button (or link) whose name matches `/(?=.*\bT001\b)(?=.*Password reset link expired)/` exists (`waitFor`) (27-28).
     3. `page.getByLabel("Search tickets", {exact: true})` exists (`waitFor`) (29).
   - Output: prints a `BENCHMARK_GRADE=<json>` line; on success `{tests: 2, failures: 0, errors: 0, skipped: 0}` (30); on exception `{tests: 0, failures: 0, errors: 1, skipped: 0}` and exit code 1 (36). (Note: 3 awaited checks but reported as tests: 2, hard-coded.)
   - Implication visible in code: ticket openers may be buttons or links; count is exact 12, so any new element with a name matching `T\d{3}` that has button/link role would break the count (test_existing.cjs:25-26). Search label must match exactly "Search tickets" (29); the `#search` label text in index.html:15 is "Search tickets" (accessible name from wrapping label).

8. Is there any build step, module system, manifest, or other tooling in the repository?
   Answer:
   - Not found: package.json, lockfile, bundler/transpiler config, tsconfig, linter/formatter config, CI config, README, manifest (web app manifest/service worker), `.gitignore` (directory listing: app.js, index.html, styles.css, test_existing.cjs, tickets.js only).
   - Module system: none. Classic global scripts with `defer` (index.html:8-9); data shared via `window.SEED_TICKETS` (tickets.js:1; app.js:2). No `import`/`export`/`require` in browser code. Only test_existing.cjs uses `require` (CommonJS, test_existing.cjs:1-3,7-8).
   - Only tooling: test_existing.cjs, which needs an externally supplied Playwright via `PLAYWRIGHT_MODULE` (test_existing.cjs:6-8); no install/run script is defined in the repo.

