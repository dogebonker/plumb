# WCAG 2.2 AA, for review

The criteria a code and screen review can check, written in-house because most design skills get them wrong (decision record UI-5). Source: the WCAG 2.2 Recommendation, https://www.w3.org/TR/WCAG22/. axe-core checks the ones marked axe; the rest need the walkthrough.

| Criterion | Level | What to check |
| --- | --- | --- |
| 1.1.1 Non-text content | A | images and icon-only controls have a text alternative; decorative ones are hidden (axe) |
| 1.3.1 Info and relationships | A | headings, lists, tables and form labels are in the markup, not only in styling (axe) |
| 1.3.5 Identify input purpose | AA | inputs for personal data carry the right `autocomplete` value |
| 1.4.1 Use of color | A | color is never the only way to tell state, errors or links apart |
| 1.4.3 Contrast (minimum) | AA | text 4.5:1; large text 3:1, where large is 24px regular or 18.66px bold (18pt and 14pt), not 18px (axe; over gradients, glass and images axe reports incomplete: check those by eye) |
| 1.4.4 Resize text | AA | content works at 200% zoom |
| 1.4.10 Reflow | AA | no horizontal scrolling at 320 CSS pixels wide, except content that needs a two-dimensional layout (tables, maps, diagrams) |
| 1.4.11 Non-text contrast | AA | control boundaries, focus indicators and meaningful icons 3:1 against neighbors |
| 1.4.12 Text spacing | AA | nothing clips when line height is 1.5, paragraph spacing 2x, letter spacing 0.12em, word spacing 0.16em |
| 1.4.13 Content on hover or focus | AA | tooltips and popovers can be dismissed, can be hovered, and stay until dismissed or until hover or focus leaves |
| 2.1.1 Keyboard | A | everything works with the keyboard alone |
| 2.1.2 No keyboard trap | A | focus can always leave a component |
| 2.2.2 Pause, stop, hide | A | moving, blinking or auto-updating content that starts on its own and lasts over 5 seconds can be paused or stopped (marquees, carousels, pulsing) |
| 2.4.3 Focus order | A | focus moves in a meaningful order, including into and out of dialogs |
| 2.4.4 Link purpose (in context) | A | a link's text, with its context, says where it goes |
| 2.4.6 Headings and labels | AA | headings and labels describe their content |
| 2.4.7 Focus visible | AA | the focus indicator is always visible |
| 2.4.11 Focus not obscured (minimum) | AA | a focused element is not entirely hidden by sticky headers, footers or banners (new in 2.2) |
| 2.5.3 Label in name | A | a control's accessible name contains its visible label |
| 2.5.7 Dragging movements | AA | anything done by dragging also works with single pointer actions (new in 2.2) |
| 2.5.8 Target size (minimum) | AA | targets at least 24 by 24 CSS pixels, or spaced so a 24px circle around each does not overlap another; 44 by 44 is AAA, not AA (new in 2.2; axe `target-size`) |
| 3.2.6 Consistent help | A | help mechanisms appear in the same order relative to other content across pages (new in 2.2) |
| 3.3.1 Error identification | A | errors say which field and what is wrong, in text |
| 3.3.2 Labels or instructions | A | inputs have visible labels or instructions |
| 3.3.3 Error suggestion | AA | when an error is detected and a fix is known, the message suggests it |
| 3.3.7 Redundant entry | A | information already given in a flow is not asked for again (new in 2.2) |
| 3.3.8 Accessible authentication (minimum) | AA | no cognitive test to log in: allow paste and password managers (new in 2.2) |
| 4.1.2 Name, role, value | A | custom controls expose name, role and state (axe) |
| 4.1.3 Status messages | AA | status changes (saved, failed, loading) are announced without moving focus |

Beyond AA, as a factory position: decorative motion honors `prefers-reduced-motion` (2.3.3 is AAA, but the factory treats it as required).
