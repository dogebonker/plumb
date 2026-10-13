# Constraints: support-ticket dashboard

Standing requirements, promises and constraints of this project. Every change reads this file. Each row ends mapped to an enforcement.

| ID | Kind | Statement | Fit criterion | Source | Enforced by |
| --- | --- | --- | --- | --- | --- |
| SYS-NFR-01 | validation | Bad input is rejected at the door: title, customer and description are trimmed and required | whitespace-only or empty values create no ticket and keep the dialog open with an accessible message tied to the field | triage (custom) | unmapped (browser test) |
| SYS-NFR-02 | accessibility | Every action is reachable and operable by keyboard with visible focus; dialogs trap Tab, Escape dismisses and returns focus to the opener | no keyboard-only dead end; focus cycles inside an open modal | triage (custom) | unmapped (browser test) |
| SYS-NFR-03 | responsive layout | Controls and dialogs are usable from desktop width down to 360 px | no horizontal page overflow and no clipped dialog controls at 360 px | triage (custom) | unmapped (browser test) |
| SYS-NFR-04 | persistence | Ticket changes survive a reload on the same origin | edits and new tickets are present after reload; the twelve seeded records stay in `tickets.js` | triage (custom) | unmapped (browser test) |
