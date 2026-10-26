---
name: ui-hard-gate
description: Pre-review hard gate for UI changes - start from a visual reference, capture every state in a real browser, grade the change against 22 rules for restraint, honest state, words, visual order and flow, and present it ready for a first-pass approval. Use when building, reviewing or presenting a UI change, or writing user-facing copy.
---

# UI hard gate

Usage: [per-skill accounting](../plumb-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Goal: the UI approver accepts the change on the first pass. Every rule below was raised repeatedly in real, recorded UI reviews. Product-specific rules (the product's vocabulary, its named good screens, what its colors mean, its theme) belong in the repository's design file (`DESIGN.md`: Words, Positions, Colors), not here; where the design file is more specific, it wins.

## Workflow

1. **Use references when supplied.** Reuse the optional 2–3 feature examples from [plumb-ui-ux/references.md](../plumb-ui-ux/references.md), approved branded mockups or this product's good screens. External examples guide useful composition and interactions; DESIGN.md owns brand, density, tokens and component conventions. List what you borrowed, adapted and left out. Without examples, proceed from the approved product job and design system; do not stop for another reference request. Keep all required behavior, rendered-state and accessibility checks.
2. **Read the issue.** The acceptance criteria and the out-of-scope list. Nothing out of scope gets touched.
3. **Build** against the rules below with the project's existing components and tokens. When a visual choice changes data or backend behavior (a count chosen to fill a grid, a code length chosen for looks), name the consequence in the same reply.
4. **Capture every state** in a real browser: default, loading or running, empty, failed, success, read-only, and the page after a refresh mid-work. Check every tab and breakpoint the change touches.
5. **Self-roast.** Look at the rendered screens yourself before handing anything over, mocks included. Grade each rule H1 to H22 pass or fail against the screenshots. Write failures as `(P0|P1|P2) <title>`, what is wrong, screenshot, fix. A P0 is wrong placement, wrong state or a broken flow. Fix every P0 and P1 before review.
6. **Present** as the Present section says.

## Rules

**Show less**
- H1 Headline first, detail on demand. Sources and evidence stay collapsed behind a chip such as "4 sources". "Too much" is the most frequent complaint.
- H2 Cut anything without an action or an explanation: headers with no call to action, duplicate status boxes, decorative bars, statuses nobody defined, unused features. The test: does it look like it was generated rather than designed?
- H3 One way to do one thing. No duplicated actions, no second display of the same diff, no second spinner style. A link that repeats what Back already does is clutter, and a dialog gets at most one secondary text link.
- H4 Flat navigation, no nesting. The most-used view opens by default. The main content gets the width; side panels start collapsed.

**Honest state**
- H5 Running work shows a spinner and a plain-words status of what is happening, and the state survives a refresh. One loader style everywhere.
- H6 Loading, empty, failed, "no change needed" and done each look different. Hide what is empty. "Completed" appears only when the work is complete. Counts match what is on screen, are in the user's units, and use correct plurals.
- H7 A failure says what failed and offers an in-place retry, or it disappears. "Something went wrong" or a raw status code never ships. The user's input survives the failure.
- H8 Fail closed. A control is disabled or hidden exactly when the server would refuse, and says why ("Read-only: guest access").
- H9 Toasts only for live events, never for something a spinner or the page already shows.

**Words**
- H10 The users' vocabulary, from the design file's Words: never internal codenames or the machinery (job, pipeline, queue, lock, source-control metaphors). Name a thing after what it does for the user, so the name alone says why it matters ("recovery codes" over "backup codes"). When the ticket, the backend and the reviewers use different names, choose by that test and say why.
- H11 Every label explains itself and matches behavior. Copy matches what the backend actually does ("use one of the codes" only when several are issued). A button named "Try again" that refreshes something is renamed for what it does. Unexplained badges go. Icons get at least a one-word label. Helper text updates with the selection.
- H12 Short copy. No wall of text, a summary shorter than its description, no key information in a footer, sentence case, no ALL CAPS, "Tip:" over "(Optional)". Tone follows the design file's Voice; without one, neutral and factual with no casual phrasing. In any voice, don't assume what the user did. Each fact is stated once in a flow, where it is needed.
- H13 Every claim links to its source, and the citation opens the exact passage. One citation component everywhere.

**Visual**
- H14 Match the product's named good screens exactly (the design file lists them). Consistency over novelty: no shape, card style or font the product does not already use.
- H15 Density both ways: generous padding, a one-line title and a few labelled sections per card, evidence collapsed, controls at normal sizes and never oversized. One unit of content fits a common laptop viewport (1440 by 900) without scrolling. Titles never truncate. Content lines up with the structure around it, with no stray offsets or dead space. Lists and grids fill their box evenly, with no ragged last row.
- H16 One filled primary button per surface, then outline, then ghost. Never two equal-weight filled buttons side by side.
- H17 Color carries meaning, with a legend for any color coding. Semantic tokens only, never raw hex values. Light and dark themes both correct.
- H18 No layout jumps. The page does not scroll while content streams. Default sizes fit their content.

**Flow**
- H19 Fewer steps. Drop intermediate screens, put defaults on the common path, keep navigation state in the URL.
- H20 Edits target the exact step or field, shown as a per-item diff with current and proposed side by side. Never regenerate everything for a small change.
- H21 Every screen answers "what do I do now?", including right after the user completes an action.
- H22 Each element lives on exactly one surface. The wrong tab or page is a P0.

## Present

- P1 Share screenshots early, while building, not only at review.
- P2 The pull request carries before and after screenshots of every state from step 4, a manual test table (step and result), and an honest "Not verified" line. Comment any temporary workaround in the code.
- P3 Keep it under 1,000 changed lines, with an assignee on the issue and on the pull request.
- P4 Label it for UI review and request the UI approver.
- P5 Map the change to the acceptance criteria point by point.
- P6 Answer numbered or P0/P1/P2 feedback point by point. Follow-ups are fine once the flow is understandable.
- P7 Be ready to explain every choice. When copy differs from the ticket, say so and default to the ticket's wording.

## Tensions (resolved)

- Too compact and too large are both rejected: less content per card, more padding around it, normal-size controls.
- Craft against speed: an understandable flow is mandatory; pure polish can be a follow-up.
- Cutting can overshoot: every cut says exactly what stays.
