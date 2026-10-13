# Product: support-ticket-dashboard

## Problem
A support operator needs to find a ticket, read it, change its status or priority, and log a new one. Today the page lists twelve tickets and does nothing else: no search or filters, no details, no editing, no new tickets, and nothing survives a reload.

## Success metric
In a browser check, an operator finds a ticket by customer, opens it, moves it from `open` to `resolved`, creates a new ticket, reloads, and sees both changes. All of it works with the keyboard alone, at desktop width and at 360 px, with no sideways page scroll.

## Announcement
The support dashboard now lets you search and filter tickets, open one to change its status or priority, and create new tickets. Your changes stay in this browser after a reload.

## Mockups
Screenshots declined (benchmark runs no browser downloads). Sketch, following DESIGN.md (one filled primary action per surface; the list is the product):

```
Support tickets                                   [New ticket]
Search tickets [__________] Status filter [All v] Priority filter [All v] [Reset filters]
12 tickets
T001 Password reset link expired   Acme Labs        open      high
T002 Export stalls at ninety...    Northwind        open      high
...
Dialog "Ticket details": title, customer, description (read-only text);
  Status [v]  Priority [v]                        [Save changes] [Cancel]
Dialog "New ticket": Title, Customer, Description (each with its error text),
  Status [v]  Priority [v]                        [Create ticket] [Cancel]
```

## Rules and examples
### The list shows every ticket
- FR-01: WHEN the page opens for the first time on an origin, the system SHALL list the twelve seeded tickets T001 to T012 with their ID, title, customer, status and priority.
  Example: first visit -> 12 rows; T001 reads "Password reset link expired", Acme Labs, open, high.
- FR-02: WHEN the page reopens or reloads, the system SHALL show the tickets last saved in the browser, not the seed.
  Example: T001 saved as `resolved`, reload -> T001 shows `resolved`.
- FR-03: IF the saved tickets are missing or unreadable THEN the system SHALL show the twelve seeded tickets.
  Example: stored value is `not json` -> 12 seeded rows, no crash.

### Search and filters narrow the list
- FR-04: WHEN the operator types in `Search tickets`, the system SHALL list only tickets whose title or customer contains the text, ignoring letter case.
  Example: "acme" -> T001, T005, T011 (customer Acme Labs). "RESET" -> T001 (title). "expired link" -> none (not a substring).
- FR-05: WHEN the operator picks a value in `Status filter` or `Priority filter`, the system SHALL list only tickets with that value; the all-values option removes that filter.
  Example: status `pending` -> T003, T005, T006, T010; back to "All statuses" -> 12.
- FR-06: The system SHALL combine search, status and priority with AND.
  Example: "acme" + `open` + `high` -> T001 only. "acme" + `resolved` + `low` -> none.
- FR-07: WHEN the visible list changes, the system SHALL show "N tickets" (or "1 ticket") in a live status region; WHEN no ticket matches, it SHALL also show "No tickets match your filters." in place of the list.
  Example: "zzz" -> "0 tickets" announced and the empty message shown; clearing the search -> "12 tickets", message gone.
- FR-08: WHEN the operator activates `Reset filters`, the system SHALL clear the search text, set both filters to all, and show every ticket, leaving stored tickets unchanged.
  Example: "acme" + `open`, then Reset -> empty search, "All statuses", "All priorities", 12 tickets.

### Details open, edit and save
- FR-09: WHEN the operator activates a ticket's button (accessible name includes its ID and title), the system SHALL open the `Ticket details` dialog showing that ticket's title, customer, description, status and priority.
  Example: "T002 Export stalls at ninety percent" -> Northwind, "The monthly CSV export never finishes.", open, high.
- FR-10: WHEN the operator changes status or priority and activates `Save changes`, the system SHALL store the change, close the dialog and update the list.
  Example: T002 high -> low, Save -> row shows `low`; reload -> still `low`.
- FR-11: WHEN a saved change makes a ticket stop matching the active filters, the system SHALL drop it from the list and update the count.
  Example: status filter `open`, T002 saved as `resolved` -> list is one shorter; count updates.
- FR-12: WHEN the operator activates `Cancel` or presses Escape in details, the system SHALL close the dialog and keep the ticket as it was.
  Example: change T002 to `pending`, Cancel -> T002 still `open`.

### New tickets are validated, then created
- FR-13: WHEN the operator activates `New ticket`, the system SHALL open the `New ticket` dialog with empty Title, Customer and Description, and Status and Priority defaulting to `open` and `medium`.
- FR-14: The system SHALL trim surrounding whitespace from Title, Customer and Description before validating or storing them.
  Example: "  Printer jam  " is stored as "Printer jam".
- FR-15: IF a trimmed Title, Customer or Description is empty THEN the system SHALL keep the dialog open, create no ticket, and show an error beside each invalid field that names the field and is tied to it for assistive technology.
  Example: Title "   ", Customer "Acme", Description "x" -> "Title is required" under Title; Title marked invalid; no ticket; list unchanged.
- FR-16: WHEN all three fields are valid and the operator activates `Create ticket`, the system SHALL store a new ticket with the next unused ID, the selected status and priority, close the dialog and show it in the list.
  Example: first creation -> T013; second -> T014; none reuses an ID, also after reload.
- FR-17: WHEN the operator activates `Cancel` or presses Escape in the new-ticket dialog, the system SHALL close it and create nothing, keeping what was typed out of the list.
- FR-18: The system SHALL treat a created ticket like a seeded one: it survives reload and can be searched, filtered, opened and edited.
  Example: create "Printer jam" for "Zed Corp", reload, search "zed" -> it appears; open it, set `pending`, Save -> persists.

### Keyboard, focus and size
- FR-19: WHILE a dialog is open, the system SHALL keep Tab and Shift+Tab inside its controls, and every control shows a visible focus.
- FR-20: WHEN a dialog closes (Save, Create, Cancel or Escape), the system SHALL return focus to the control that opened it.
  Example: open T003, press Escape -> focus is on T003's button.
- FR-21: The system SHALL fit a 360 px wide viewport with no sideways page scroll and no clipped dialog control, and keep every action usable by keyboard.

## Promises
- NFR-01: Nothing the operator saved is lost on reload in the same browser.
- NFR-02: Every control has a visible name; errors and counts are announced, not shown by color alone.

## Constraints
- C-01: Vanilla HTML, CSS and JavaScript only; no dependencies, backend, remote requests or external assets.
- C-02: The twelve seeded records stay in `tickets.js` with their IDs and values.
- C-03: Stable names: `Search tickets`, `Status filter`, `Priority filter`, `New ticket`, `Reset filters`; dialogs `Ticket details`, `New ticket`; labels `Title`, `Customer`, `Description`, `Status`, `Priority`; actions `Save changes`, `Create ticket`, `Cancel`.

## Standing constraints
- SYS-NFR-01: FR-14 and FR-15 are its enforcement: trim and validate before storing; invalid input creates nothing.

## Non-goals
- Deleting tickets, sorting, pagination, comments, assignment, multiple users, sync between browsers.
- Searching descriptions. Editing title, customer or description of an existing ticket.

## Open questions
