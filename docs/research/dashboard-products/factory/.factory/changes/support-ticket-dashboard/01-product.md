# Product: support-ticket-dashboard

## Problem
A support operator needs to find a ticket quickly, read it, change its status or priority, and file new tickets, in a small local tool. Today the page only lists the twelve seeded tickets: no search, no filters, no details, no way to edit or create, and nothing survives a reload.

## Success metric
An operator can, using only the keyboard or a 360 px phone: find a seeded ticket by typing part of its title or customer, change its status or priority and still see the change after reload, and create a ticket that then behaves like a seeded one.

## Announcement
Support tickets now has search and status/priority filters with a live result count, a details dialog where you update status and priority, and a New ticket dialog. Everything is kept in your browser and survives reloads.

## Mockups
Screenshots declined (they need a Playwright download; none is allowed here). Sketch, following DESIGN.md:
```
Support tickets
[Search tickets    ] [Status filter v] [Priority filter v] [Reset filters] [New ticket]
3 tickets                                              (role=status)
+-------------------------------------------+
| T001  Password reset link expired         |   <- opens "Ticket details"
| Acme Labs                                 |
| open · high                               |
+-------------------------------------------+
Dialog "Ticket details": title, customer, description (read-only text);
  Status [v]  Priority [v]      [Save changes (filled)] [Cancel]
Dialog "New ticket": Title, Customer, Description (each with error text under it),
  Status [v] Priority [v]       [Create ticket (filled)] [Cancel]
```
Primary actions per DESIGN.md: row button (list), `Save changes`, `Create ticket`.

## Rules and examples
### Seeded list
- FR-01: WHEN the dashboard opens with no saved changes, the system SHALL list all twelve seeded tickets (T001 to T012) with ID, title, customer, status and priority.
  Example: first load -> 12 rows, T001 "Password reset link expired", Acme Labs, open, high; count reads "12 tickets".
- FR-02: The system SHALL keep the twelve seeded records, IDs and values, in `tickets.js`.

### Search and filters
- FR-03: WHEN the operator types in `Search tickets`, the system SHALL show tickets whose title or customer contains the text, ignoring case.
  Example: "acme" -> T001, T005, T011 (customer Acme Labs); "EXPORT" -> T002.
- FR-04: The system SHALL combine search, `Status filter` and `Priority filter` with AND; each filter has an all-values choice.
  Example: "acme" + status pending + priority medium -> T005 only.
- FR-05: The system SHALL show the matching count in a `role="status"` region, updated on every change, singular for one.
  Example: filter status resolved -> "3 tickets"; one match -> "1 ticket".
- FR-06: IF no ticket matches THEN the system SHALL show "No tickets match your filters." and a count of "0 tickets".
  Example: search "zzz" -> empty message, no rows.
- FR-07: WHEN the operator activates `Reset filters`, the system SHALL clear search and both filters, without changing stored tickets.
  Example: after "zzz", reset -> all tickets again, search empty.

### Ticket details
- FR-08: WHEN the operator activates a ticket's button (accessible name contains its ID and title), the system SHALL open the `Ticket details` dialog showing title, customer, description, and editable status and priority.
  Example: "T002 Export stalls at ninety percent" -> dialog shows Northwind, "The monthly CSV export never finishes.", open, high.
- FR-09: WHEN the operator changes status or priority and activates `Save changes`, the system SHALL update the list and persist the change across reload.
  Example: T001 open -> resolved, save, reload -> T001 shows resolved.
- FR-10: WHEN the operator activates `Cancel` or presses Escape in details, the system SHALL close the dialog without changing the ticket and return focus to the ticket button that opened it.
  Example: change T003 to high, Cancel -> T003 still low.

### New ticket
- FR-11: WHEN the operator activates `New ticket`, the system SHALL open the `New ticket` dialog with Title, Customer, Description, Status (default open) and Priority (default medium).
- FR-12: The system SHALL trim surrounding whitespace of Title, Customer and Description before validating and storing.
  Example: "  Printer jam  " is stored as "Printer jam".
- FR-13: IF any of Title, Customer or Description is empty after trimming THEN the system SHALL keep the dialog open, create no ticket, and show a message under each invalid field, associated with it (`aria-describedby`, field marked `aria-invalid`), and move focus to the first invalid field.
  Example: Title "   " -> "Title is required" under Title; list unchanged.
- FR-14: WHEN the form is valid and the operator activates `Create ticket`, the system SHALL store a ticket with a unique ID, the trimmed text and chosen status and priority, close the dialog, and persist it.
  Example: first created ticket gets T013; after reload it is listed and searchable, and opens in `Ticket details`.
- FR-15: WHEN the operator activates `Cancel` or presses Escape in New ticket, the system SHALL create nothing, discard the entered text, and return focus to `New ticket`.

### Modal keyboard behavior
- FR-16: WHILE a dialog is open, the system SHALL keep Tab and Shift+Tab cycling within that dialog's controls.
  Example: Tab from `Cancel` (last control) -> first field of the dialog.

### Persistence
- FR-17: The system SHALL store ticket changes in browser local storage and rebuild the list from it on load.
  Example: edit T001, create T013, reload -> both present.
- FR-18: IF stored data is missing or unreadable THEN the system SHALL show the seeded tickets instead of failing.

## Promises
- NFR-01: Every action works with the keyboard alone, with a visible focus indicator.
- NFR-02: At desktop widths and 360 px, the page has no horizontal overflow and no dialog control is clipped.
- NFR-03: Everything has a text label; status and priority are never color-only.

## Constraints
- C-01: Vanilla HTML, CSS and JavaScript only; no dependencies, backend, remote requests or external assets.
- C-02: Accessible names fixed: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`.

## Standing constraints
- SYS-NFR-01 (validation): FR-12, FR-13.
- SYS-NFR-02 (accessibility): FR-10, FR-15, FR-16, NFR-01.
- SYS-NFR-03 (responsive layout): NFR-02.
- SYS-NFR-04 (persistence): FR-02, FR-09, FR-14, FR-17.

## Non-goals
- Deleting tickets, assigning owners, comments, sorting, pagination, multi-user sync, saving filter state.
- Editing title, customer or description of an existing ticket.

## Open questions
