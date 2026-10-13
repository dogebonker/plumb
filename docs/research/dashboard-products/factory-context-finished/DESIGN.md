---
name: Support tickets
description: "a support operator's triage queue, closer to a plain shared inbox than a metrics dashboard"
colors:
  text: "#202124"            # styles.css body color
  border: "#aaa"             # styles.css .ticket border
  surface: "white"           # styles.css .ticket background
  focus: "#245ac5"           # styles.css :focus-visible outline
  error: "#a01818"           # styles.css .error
  backdrop: "#0006"          # styles.css dialog::backdrop
typography:
  body:
    fontFamily: "system-ui, sans-serif"   # styles.css body
    fontSize: 1rem                        # browser default; no size set in styles.css
    lineHeight: normal
  error:
    fontFamily: "system-ui, sans-serif"
    fontSize: .9rem                       # styles.css .error
    lineHeight: normal
spacing:
  gap-sm: 5px                # styles.css label gap
  gap-md: 12px               # styles.css .filters, dialog form
  page: 24px                 # styles.css main padding; 16px under 600px
omitted:
  - section: dark color set
    reason: "styles.css defines no dark scheme; adding one is outside this change"
  - section: type scale beyond body and error
    reason: "styles.css sets no heading sizes; the hierarchy work of this change defines them"
---

<!-- factory:design-schema 1 - reviewed 2026-10-13 -->

## Overview
A single support operator works through a short queue of tickets: find one, read it, change its status or priority, or log a new one. The job is fast, repeated lookup and small edits, so the list is the product and everything else opens on demand. The task states the interface: a list of ticket ID, title, customer, status and priority, filters, details, and a creation dialog. Think of a plain shared inbox, not an analytics dashboard.

## Principles
### P1 Scanning over decoration (inferred)
Because: the operator "finds tickets" first; the list must show ID, title, customer, status and priority for twelve or more rows at once.
Rules out: card grids with large padding, per-row icons or avatars, summary tiles above the list.
Test: at 1280 px, at least ten tickets are visible without scrolling and each row's five fields can be read left to right without opening anything.

### P2 Status carried by words, not color alone (inferred)
Because: the task requires usable controls and accessible names; status and priority are the sorting facts of the queue.
Rules out: color-only badges, tooltips as the only label.
Test: with the page in grayscale, every status and priority is still told apart by its text.

### P3 One main action per surface (inferred)
Because: the task names few actions; each dialog has exactly one commit (`Save changes`, `Create ticket`) and one escape (`Cancel`).
Rules out: two filled buttons in a dialog, destructive-looking styling on `Cancel`.
Test: each dialog shows one visually dominant button, and it is the commit.

### P4 Honest, named states (inferred)
Because: the task requires a result count, an empty state and validation messages tied to fields.
Rules out: silent empty lists, generic "Something went wrong", errors shown only by color.
Test: each state (results, no match, invalid field) has its own text, and an error names the field and the fix.

## Positions
Refuses to look like: a metrics dashboard (charts and KPI tiles hide the queue), a kanban board (it makes status a place instead of a field), a marketing page (hero, gradient or illustration).

| Screen | Primary action | Demoted |
| --- | --- | --- |
| Ticket list | Open a ticket (each row) | `New ticket` (single filled button in the page header row), `Reset filters` (plain) |
| Ticket details | `Save changes` | `Cancel` |
| New ticket | `Create ticket` | `Cancel` |

Disclosure: the list shows five fields per ticket; description, and the status and priority editors, show in the details dialog only. At most two levels: list, then dialog.
States: results show "N tickets" in the live region; no match shows "No tickets match your filters." and the count reads 0; an invalid dialog field shows red text beneath the field naming what is missing, with the dialog still open.
Earning a place: a new element must support finding, reading or editing a ticket; anything else is "not now".

## Words
| Say | Not | Source |
| --- | --- | --- |
| ticket | case, issue | index.html, task |
| customer | account, client | tickets.js |
| status: open, pending, resolved | active, closed | tickets.js |
| priority: low, medium, high | urgency, severity | tickets.js |
| Save changes / Create ticket / Cancel | Submit, OK, Done | task |
| Reset filters | Clear all | index.html |
Voice: plain and short; says what happened and what to do next.

## Colors
Neutral text on white. The blue focus color marks keyboard focus and the one primary button. Red appears only for validation errors, always with text. No other accent.

## Typography
System UI sans-serif, because the operator reads dense short lines and gains nothing from a loaded face. Ticket title is the heaviest weight in a row; customer and status/priority are regular weight.

## Do's and Don'ts
- Do keep the focus outline visible on every control (P3, task keyboard rules).
- Do tie every error message to its field with `aria-describedby` and `aria-invalid` (P4).
- Don't carry status or priority by color alone (P2).
- Don't add summary tiles, charts or illustrations (Positions).
- Don't make the page scroll sideways at 360 px; long words wrap (P1).

## Known Gaps
- Every principle and position is `inferred`; no user quotes or other products were available.
- The rendered screens at 390, 768 and 1280 px were not captured for the draft; the current UI is an unstyled list.
- `design.md lint` was skipped: the tool is not installed (`npm i -g @google/design.md@0.4.0`) and installs are not permitted here.
- The 3-width screenshots were skipped.
