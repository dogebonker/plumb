# Support-Ticket Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the seeded vanilla HTML/CSS/JS support-ticket dashboard (list, search/filters, details editing, ticket creation, localStorage persistence, keyboard/a11y/responsive behavior).

**Architecture:** `tickets.js` keeps the 12 seeds in `window.SEED_TICKETS` untouched. `app.js` holds state (`tickets`, `filters`), loads/saves `localStorage["support-tickets.v1"]` (falls back to a copy of the seeds if missing or corrupt), and renders the list from state. Details and creation use native `<dialog>` opened with `showModal()`, plus an explicit Tab focus trap and Escape handling that restores focus to the opener.

**Tech Stack:** Vanilla HTML, CSS, JS. Playwright via `PLAYWRIGHT_MODULE`, run only through `/private/tmp/fb-yvs5n0g1/browser-check/browser-check` (`test*.cjs` files in the workspace root). No dependencies.

**Spec:** the task statement ("Support-ticket dashboard"), recorded in the Global Constraints below.

## Global Constraints

- Keep the twelve records in `tickets.js` unchanged (IDs T001–T012 and values).
- No dependencies, backend, remote requests, or external assets.
- Statuses: `open`, `pending`, `resolved`. Priorities: `low`, `medium`, `high`.
- Accessible names: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; field labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`.
- Each opening control is a button whose accessible name includes the ticket ID and title.
- Result count lives in `role="status"`.
- No horizontal overflow at 360px; visible focus; Tab/Shift+Tab trapped in the open modal; Escape dismisses without saving and returns focus to the opener.
- Text fields are trimmed before validation and storage.
- Local commits only. Scratch files under `.tmp`.

## Review Focus

- Corrupt or non-array localStorage JSON: fall back to the seeds without crashing.
- Ticket text containing HTML (`<b>x</b>`): rendered as text, never as markup (use `textContent`).
- Very long unbroken titles or customers at 360px: no horizontal overflow.
- Rapid double-submit of Create ticket: exactly one ticket, and IDs stay unique after reload (next ID is max numeric ID + 1, not the array length).
- Cancel or Escape after changing the status or priority selects: the ticket is unchanged, and the selects reset when the dialog is reopened.
- Search with regex characters (`(`, `.*`) is treated as a literal substring.
- Reset filters leaves stored tickets untouched and keeps any new ticket.

---

### Task 1: List, filters, persistence

**Files:**
- Modify: `index.html`, `app.js`, `styles.css`
- Test: `test_dashboard.cjs`

**Interfaces:**
- Produces in `app.js`: `loadTickets(): Ticket[]`, `saveTickets(): void`, `matches(ticket, filters): boolean`, `render(): void`, and `state = {tickets, filters: {query, status, priority}}`. A `Ticket` is `{id, title, customer, status, priority, description}`.

- [ ] **Step 1: Write failing tests in `test_dashboard.cjs`**, using the same server and Playwright harness as `test_existing.cjs`, with the real node:test runner format. Tests cover:
  - 12 openers initially, each row showing ID, title, customer, status, and priority.
  - Search "acme" gives 3 results, with the status text "3 tickets"; "NORTHWIND" matches case-insensitively, and an ID-only query like "T001" does not match.
  - Search "acme" plus status "pending" gives exactly 1 (T005).
  - Status "all" and priority "all" restore the full set.
  - A no-match search shows the empty state and "0 tickets".
  - Reset filters clears all three controls and shows 12 again.
  - A regex-literal query like `(` yields the empty state without throwing.
  - A corrupt localStorage value falls back to 12 tickets.
- [ ] **Step 2: Run `/private/tmp/fb-yvs5n0g1/browser-check/browser-check`.** Expected: new tests FAIL.
- [ ] **Step 3: Implement.** Add a proper table-like list: each `li` holds the opener button (the ID and title as the primary line, the customer as secondary) plus status and priority badges. Keep the opener's accessible name as `"T001 Password reset link expired"` (badges outside the button or `aria-hidden` is not needed; the name only has to include the ID and title). Wire the `#search` label, the filters, and Reset. Use `textContent` for all ticket text. Add the empty state and the count (singular/plural handled: "1 ticket").
- [ ] **Step 4: Run browser-check.** Expected: PASS, and `node test_existing.cjs` passes.
- [ ] **Step 5: Commit** `feat: list, filters and persistence`.

### Task 2: Ticket details dialog

**Files:**
- Modify: `index.html`, `app.js`, `styles.css`
- Test: `test_dashboard.cjs`

**Interfaces:**
- Consumes: `state`, `saveTickets()`, `render()`.
- Produces: `openDialog(dialog, opener)` and `closeDialog(dialog)` helpers, which handle `showModal`, the Tab trap, Escape, and focus return. Task 3 reuses them.

- [ ] **Step 1: Write failing tests:**
  - Opening T001 shows the dialog named `Ticket details` with title, customer, description, and status/priority selects.
  - Changing the status to resolved and the priority to low, then `Save changes`, updates the row, and the values survive `page.reload()`.
  - `Cancel` after changing the selects leaves the ticket unchanged, and reopening shows the stored values.
  - Escape dismisses without saving, and focus returns to the opener button.
  - Tab and Shift+Tab stay within the dialog across 6+ presses.
  - An edited ticket still honors the active filters after saving (the list re-filters).
- [ ] **Step 2: Run browser-check.** Expected: FAIL.
- [ ] **Step 3: Implement** a `<dialog aria-labelledby>` with a heading, read-only title/customer/description text, and Status and Priority selects labeled `Status` and `Priority`, plus `Save changes` and `Cancel`. Implement `openDialog`/`closeDialog` with a keydown handler that wraps focus between the first and last focusable elements. Handle the native `cancel` event for Escape so focus returns to the opener.
- [ ] **Step 4: Run browser-check.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: ticket details dialog`.

### Task 3: New ticket dialog and validation

**Files:**
- Modify: `index.html`, `app.js`, `styles.css`
- Test: `test_dashboard.cjs`

**Interfaces:**
- Consumes: `openDialog`, `closeDialog`, `state`, `saveTickets`, `render`.
- Produces: `nextId(tickets): string`, which returns `"T" + zero-padded(max numeric suffix + 1, 3 digits)`, and `validateNew(values): {errors, clean}`.

- [ ] **Step 1: Write failing tests:**
  - `New ticket` opens a dialog named `New ticket`.
  - An empty submit keeps the dialog open, creates nothing, and shows one error message per field. Each field has `aria-invalid="true"` and `aria-describedby` pointing at its message, and focus moves to the first invalid field.
  - Whitespace-only values are invalid.
  - A valid submission `"  Printer jam  "` / `"  Zed Co "` / `" Jammed "` with status pending and priority high stores trimmed values, gets ID T013, appears in the list, and survives reload.
  - The new ticket can be found by search, opened, and edited.
  - Cancel and Escape create nothing, and focus returns to `New ticket`.
  - A double click on `Create ticket` creates exactly one ticket.
  - After a reload, a second created ticket gets T014.
  - Reopening the dialog shows a clean form with no stale errors.
  - HTML in a title renders as text.
- [ ] **Step 2: Run browser-check.** Expected: FAIL.
- [ ] **Step 3: Implement** the form with `novalidate`, labeled Title, Customer, Description (textarea), Status, and Priority (defaults: open, medium). Add per-field `<p class="error" id=… >` elements, filled on invalid submit and cleared on reopen or on a valid submit. Close the dialog right after a successful create (this prevents duplicates).
- [ ] **Step 4: Run browser-check.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: new ticket dialog with validation`.

### Task 4: Responsive and visual polish, review focus

**Files:**
- Modify: `styles.css` (and small markup tweaks)
- Test: `test_dashboard.cjs`

- [ ] **Step 1: Write failing tests** at a 360×740 viewport:
  - `document.documentElement.scrollWidth <= innerWidth` initially, with a 200-character unbroken title created, and with each dialog open.
  - Every dialog button is fully inside the viewport (bounding box checks).
  - The focused element has a non-empty outline (visible focus), at desktop width too.
  - A keyboard-only flow works (Tab to a ticket, Enter opens it, Escape closes it).
- [ ] **Step 2: Run browser-check.** Expected: failures only where the layout needs work.
- [ ] **Step 3: Adjust CSS.** Use a clear hierarchy (ID and title bold, customer muted, color-coded status/priority badges that are also text), wrapping controls, and dialog `max-height` with scrolling. Keep contrast at AA level.
- [ ] **Step 4: Run browser-check and `node test_existing.cjs`.** Expected: all PASS.
- [ ] **Step 5: Commit** `style: responsive layout and focus polish`.

### Final: whole-branch review

- [ ] Dispatch a fresh reviewer (superpowers:requesting-code-review) over the full diff against this plan and the task statement. Fix findings, rerun all checks, and commit.

## Self-review

- Spec coverage: list and hierarchy (T1, T4), search/filter/AND/reset/count/status region/empty state (T1), details/edit/save/cancel/persist (T2), creation/validation/trim/unique ID/persist (T3), responsive/keyboard/focus trap/Escape/focus return (T2–T4), seeds kept (Global Constraints, T1 test).
- Names are consistent across tasks (`openDialog`, `closeDialog`, `nextId`, `validateNew`, `state`).
- Plan size is proportionate: signatures and test assertions only.
