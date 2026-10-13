# Creating the design file

The guide `factory-ui-ux design-md` follows. Adapted from the DESIGN.md format's own guidance and impeccable's product-context flow; evidence in `docs/research/ui-ux/B-design-md.md` of the factory repository. The skill drafts; the user decides every principle and position.

## 1. Detect a UI

Front-end dependencies (react, next, vue, svelte, solid, angular), templates or HTML, SwiftUI or Compose, or a terminal UI with styling. No UI: say so and stop.

## 2. Resolve the file

- No root `DESIGN.md`: the file is the root `DESIGN.md`.
- A root `DESIGN.md` that is a design file (DESIGN.md frontmatter, or the factory's stamp comment): refresh it. Show the diff and ask before replacing any prose.
- A root `DESIGN.md` that holds something else (architecture, for example): the file is `.software-factory/system/design.md`; tell the user why.

## 3. Read the product evidence

`.software-factory/system/product.md`, `glossary.md`, `constraints.md` (accessibility promises), the latest `01-product.md` (problem, user, success metric), a `PRODUCT.md` if present, and Pond for the users' own words and complaints.

## 4. Extract tokens from code

In this order: CSS variables, Tailwind config or `@theme`, theme files, `*.tokens` or `tokens.json`, components, global CSS. Every observed token cites its source file. Record these as **observed implementation**, not the approved target. Identify whether they belong to an intentional brand/theme or a disposable starter; absent evidence, mark that status `inferred`. What the code lacks goes under `omitted:` with a reason. Target tokens may be proposed from the product evidence and desired reference, with their decision source and confirmation status; do not preserve starter styling merely because it exists.

## 5. See the UI

Render the main screens at the baseline widths, brief minimum width and media-query boundaries just below, at and above each breakpoint (the shared `viewportWidths` helper in `ui/tools.yaml`) (Playwright, as `ui/tools.yaml` says) and sample computed styles. From that, infer each screen's primary action and the current look, including any slop it already carries.

## 6. Draft

Fill [DESIGN.template.md](DESIGN.template.md), with 3 to 5 principles. Label each principle, position, word and target-token decision `confirmed` (from explicit approval or an existing approved brand decision) or `inferred`. Current code alone confirms only the observed implementation, never the intended target. Separate the observed appearance from the approved target in the draft. Every principle must pass all four tests, or it is dropped:

1. It comes from evidence: a user quote, the success metric, a constraint, a recorded decision.
2. It rules out something concrete: a pattern visible in the current UI or a named competitor.
3. Its opposite is the right choice for some other product. ("Clean", "modern" and "intuitive" fail here.)
4. It has a Test line a reviewer can apply to a screen without asking the author.

## 7. Confirm intent where evidence cannot answer

Show the draft first. Then ask at most 3 questions per round, at most 2 rounds, picking from:

- the primary user and their moment, only when `product.md` lacks it
- what the product must never be mistaken for, offering 2 or 3 named anti-references from its category
- forced trade-offs derived from the success metric (density over calm, experts over first-timers, one way over many); the chosen side becomes a principle's title
- the primary action of screens where the inference was ambiguous
- term pairs where code strings and user quotes disagree
- whether the existing appearance is intentional approved branding or replaceable starter styling
- one desired product/reference and the quality bar for this release (for example, a finished daily work tool versus a functional prototype), with a concrete acceptance check
- one example of the intended voice for a real action or error, offering a draft when none exists
- brand commitments that cannot change (logo, colors, faces)

Reuse answers already recorded in the brief; ask only for missing intent. Never ask the user to invent spacing, colors or font scales: propose those from the reference and job. A confirmed brand constrains the proposal; disposable starter values do not. Before implementation expands across screens, render one representative primary-job screen with realistic content at a narrow width and a wide width. Record approval or specific requested changes alongside the design draft. A required visual quality bar is a delivery criterion, not an optional cosmetic follow-up.

## 8. Validate

- `design.md lint <file>` reports 0 errors.
- Every observed token cites a source file; target tokens cite their decision/reference and status; every principle has Because, Rules out and Test; every position cites a source.
- Known Gaps lists everything still `inferred`.

## 9. Write

Write the file once the user confirms it, stamped `<!-- factory:design-schema 1 - reviewed <slug or date> -->`; the stamp is what the factory hook and runner look for. Give the user the one line for `AGENTS.md` or `CLAUDE.md` that points agents to it, for them to add. Committed mode: commit it on the change's branch, or on its own branch when no change is open. Ignored mode: the root file stays untracked unless the user commits it.

Headless mode: write the draft to `<change>/design-draft.md`, commit and push it, and wait for the user as gates.md's Headless mode describes, asking the interview questions in that comment. The next run reads the approvers' replies as the interview answers: once they answer every open question, or reply `confirm design`, it writes the design file from the draft with their corrections; otherwise it updates the draft and asks what is still open, within the 2-round cap; after that, what is still open stays `inferred` under Known Gaps.

## Keeping it current

Code records implemented token values; approved design decisions own the target, principles and positions. Reconciliation reports drift rather than silently replacing the approved target with current code. At reconcile, a change that touched UI re-extracts tokens (`design.md diff`), adds new screens to the primary-action table, syncs new terms from `glossary.md` into Words, and bumps the stamp. Principles and positions change only by a decision the user records; a principle overruled three times in review is raised for rewrite through calibration.
