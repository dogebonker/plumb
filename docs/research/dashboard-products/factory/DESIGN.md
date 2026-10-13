---
name: Support tickets
description: "a triage desk list for one support operator, not a CRM suite or analytics dashboard"
colors:
  text: "#202124"            # styles.css body color
  focus: "#245ac5"           # styles.css :focus-visible outline
  error: "#a01818"           # styles.css .error
  border: "#aaa"             # styles.css .ticket border
  surface: "white"           # styles.css .ticket background
  scrim: "#0006"             # styles.css dialog::backdrop
typography:
  body:
    fontFamily: system-ui, sans-serif   # styles.css body
    fontSize: 1rem                      # styles.css (inherited; inputs use font: inherit)
    lineHeight: normal
  error:
    fontFamily: system-ui, sans-serif
    fontSize: .9rem                     # styles.css .error
    lineHeight: normal
spacing:
  gap-control: 12px          # styles.css .filters gap, #tickets li margin, dialog form gap
  gap-tight: 5px             # styles.css label gap, .ticket gap
  page: 24px                 # styles.css main padding (16px under 600px)
omitted:
  - section: brand colors, status/priority colors, display type
    reason: "the code has none; status and priority are conveyed by text first and any color is added only as a second cue"
---

<!-- factory:design-schema 1 - reviewed support-ticket-dashboard -->

## Overview
One support operator scans a short list of tickets, finds one, reads it and changes its status or priority, or files a new one. The job is to find and update a ticket in few steps, on desktop or a 360 px phone, with keyboard only if needed (task statement; SYS-NFR-01 to 04). Reference (confirmed by user): a triage desk's clipboard, not a CRM dashboard.

## Principles
### P1 Scan over decorate  (confirmed by user)
Because: the operator's moment is finding a ticket in the list; the task asks for "a sensible visual hierarchy".
Rules out: card grids with avatars, charts, KPI tiles, gradients.
Test: in the list, the ID and title are read first, customer second, status and priority third, with no element that does not help picking a ticket.

### P2 Stated over implied  (confirmed by user)
Because: SYS-NFR-02 and the task require status regions, labelled fields and validation messages tied to fields.
Rules out: color-only status, placeholder-as-label, toast-only errors, silent empty lists.
Test: every status, priority, error and empty/count state has visible text, and the same text is exposed to assistive technology.

### P3 One primary action per surface  (confirmed by user)
Because: the task has distinct commit actions (`Save changes`, `Create ticket`) next to `Cancel`.
Rules out: two filled buttons in one dialog; a filled `New ticket` competing with list rows.
Test: each dialog shows one filled action; `Cancel` and `Reset filters` are plain.

### P4 Works at 360 px as designed  (confirmed by user)
Because: SYS-NFR-03: no horizontal overflow, no clipped dialog controls.
Rules out: fixed-width tables, desktop-only layouts squeezed later.
Test: at 360 px, no page-level horizontal scroll and every dialog control reachable.

## Positions
Refuses to look like: Zendesk-style multi-pane consoles (too dense for one operator), a spreadsheet grid (no hierarchy), a marketing dashboard with stat tiles (no job here).

| Screen | Primary action | Demoted |
| --- | --- | --- |
| Ticket list | Open a ticket (row button) | `New ticket` (plain button), `Reset filters` |
| Ticket details dialog | `Save changes` | `Cancel` |
| New ticket dialog | `Create ticket` | `Cancel` |

Disclosure: list shows ID, title, customer, status, priority; the description appears only in details. At most two levels: list, then one dialog.
States: empty search shows "No tickets match your filters." with `Reset filters` available; the result count is always visible ("12 tickets", "3 tickets"); validation errors appear under their fields in the error color with text; saved changes show in the list immediately.
Earning a place: a new element must serve finding, reading or updating a ticket; "not now" is the default.

## Words
| Say | Not | Source |
| --- | --- | --- |
| ticket | issue, case | task statement |
| customer | client, account | task statement |
| status: open, pending, resolved | active, closed | tickets.js |
| priority: low, medium, high | urgent, P1 | tickets.js |
| Save changes / Create ticket / Cancel / New ticket / Reset filters | Submit, OK, Clear | task statement (stable accessible names) |
Voice: plain, short, no exclamation marks.

## Colors
Neutral page; one accent (the focus blue, #245ac5) for focus outlines and the single filled primary action; error red only for validation text. Status and priority never rely on color alone.

## Typography
System UI stack, so nothing loads remotely. Scale: ticket ID+title at body weight 600, customer and meta at body size in a muted tone, error text .9rem.

## Do's and Don'ts
- Do keep visible focus on every control (P2, P4).
- Do keep every field label visible (P2).
- Don't use color alone for status or priority (P2).
- Don't add a second filled button to a dialog (P3).
- Don't add fixed widths that exceed 360 px (P4).

## Known Gaps
- Principles, positions, anti-references and the reference line were drafted without a user quote or product.md; the user confirmed them on 2026-10-12.
- `design.md lint` is not installed and was skipped (no installs allowed).
- Renders at 390/768/1280 were skipped because the current UI is a bare list.
