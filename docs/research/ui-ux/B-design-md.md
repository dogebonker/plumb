# B. The design file for `factory-ui-ux` (S9)

Research date 2026-10-10. Fetched content was treated as data. Counts come from the GitHub API on that date.

## Conclusion

- **Base format: Google Labs' DESIGN.md** (Apache-2.0, alpha 0.4.0). It is the only open, linted, widely adopted file format for "design for coding agents". It is also the only one that other tools on this machine read (Stitch, impeccable, VoltAgent's collection, `@google/design.md lint`).
- **The gap is the "positions" part.** The spec describes "a visual identity" only. It has no place for users, product principles, refusals, a primary action per screen, or vocabulary. The spec says unknown `##` sections are preserved, and the linter's order check ignores them (verified in `section-order.ts`). So the factory can add `## Principles`, `## Positions` and `## Words` without breaking compatibility.
- **The best model for the positions half is impeccable's split.** Its `PRODUCT.md` holds users, positioning and principles, and its `DESIGN.md` holds the visual system. Each principle should be written to pass Spool's and Keith's tests: it comes from evidence, it rules things out, it would be reversible elsewhere, and a reviewer can check it.
- **Location: root `DESIGN.md`, not `.factory/system/design.md`** (this changes README S9). Every tool that reads the file looks at the root, and impeccable does not look in `.factory/`. If the file lives in `.factory/system/`, the next design tool will create a second, competing root `DESIGN.md`.

---

## 1. Existing conventions

### F1 Google Labs DESIGN.md (the de facto standard)

- **Maintainer and license:** `google-labs-code/design.md`, Apache-2.0. Created 2026-04-10. Releases 0.1.0 (2026-04-21) through 0.4.0 (2026-07-27). npm `@google/design.md@0.4.0`. 28.3k stars, 2.3k forks. https://github.com/google-labs-code/design.md
- **Spec:** https://github.com/google-labs-code/design.md/blob/main/docs/spec.md
- **Philosophy:** https://github.com/google-labs-code/design.md/blob/main/PHILOSOPHY.md
- **Adoption:** GitHub code search finds about 22.9k files named `DESIGN.md` containing `version: alpha`, and about 67k containing "Do's and Don'ts". Stitch imports and exports the file. Impeccable writes it.
- **Structure:**
  - Optional YAML frontmatter holds the tokens: `version`, `name`, `description`, `omitted`, `colors`, `typography`, `rounded`, `spacing` and `components`.
    - Components accept only 8 properties: `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height` and `width`.
    - References use `{colors.primary}`, borrowed from DTCG.
    - Colors can be any CSS color.
    - Dimensions take px, em or rem.
  - Markdown body with `##` sections in a fixed order: Overview (Brand & Style), Colors, Typography, Layout, Elevation & Depth, Shapes, Components, Do's and Don'ts. Any section may be omitted. Unknown headings are preserved. A duplicate heading is an error.
- **How agents use it:** Agents read the file as context. A CLI provides:
  - `lint`: 11 rules, including broken references, WCAG AA contrast on component pairs, missing `primary`, section order and typo'd keys. Output is JSON. Exit code 1 on errors.
  - `diff`: token-level and regression comparison between two files.
  - `export`: to Tailwind v3/v4 or DTCG.
  - `spec`: prints the spec for prompts.
- **Strength:** PHILOSOPHY.md makes the right argument:
  - The prose matters more than the tokens.
  - "A specific reference carries more than a list of adjectives." Adjectives describe a region; a reference describes a point.
  - A few deliberate Don'ts beat a long list.
- **Weaknesses:**
  - It is visual only ("describing a visual identity"). It has no fields for users, product principles, refusals, primary action, vocabulary, empty or error states, or accessibility beyond contrast.
  - Alpha status: the schema changed four times in three months.
  - Frontmatter tokens duplicate the code's tokens, so they drift. Nothing ties a token to its source file.
  - The 8-property component limit cannot express shadows, focus rings or motion.
  - "Overview" invites mood prose that cannot be falsified.

### F2 VoltAgent awesome-design-md (a collection, not a format)

- **Repository:** https://github.com/VoltAgent/awesome-design-md. MIT. Created 2026-03-31. 120k stars, 13.4k forks. 74 `DESIGN.md` files.
- **Contents:** Each file is extracted from a company's public marketing site (Linear, Stripe, Vercel, Claude, Apple and others). Each has a `preview.html` and `preview-dark.html`.
- **Format:** The Stitch format plus extra sections: Responsive Behavior, Iteration Guide (an agent workflow), Known Gaps and Agent Prompt Guide. Example: https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/linear.app/DESIGN.md
- **Useful ideas:**
  - The "Known Gaps" section states what the extraction could not see. For example, Linear's file says form errors were "not visible on the inspected pages".
  - The "Iteration Guide" ends with "run lint after edits".
  - The Don'ts are concrete: "Don't pill-round CTAs", "Don't introduce a second chromatic accent".
- **Weaknesses:**
  - Each file describes someone else's brand, taken from marketing pages rather than product UI. Copying one produces a lookalike, which is the slop S9 is meant to remove.
  - There are no product positions.
  - The README promotes paid services (getdesign.md).
  - Brand and trademark use is unaddressed beyond "we do not claim ownership".
- **Use for the factory:** as format examples, and as a catalog of named anti-references ("does not look like Linear's marketing site").

### F3 Impeccable: PRODUCT.md + DESIGN.md (the closest to what S9 wants)

- **Repository:** https://github.com/pbakaus/impeccable. Apache-2.0. 79k stars. Already installed at `~/.claude/skills/impeccable`.
- **Product truth goes in `PRODUCT.md`.** It has these sections: Platform, Stack, Users, Product Purpose, Positioning ("the mechanism a neighboring product could not truthfully copy"), Operating Context, Capabilities and Constraints, Brand Commitments, Evidence on Hand, Product Principles (3 to 5, "no visual recipes"), and Accessibility. The file carries a schema stamp, `<!-- impeccable:product-schema 1 -->`. About 10.8k public files carry that stamp.
- **The visual system goes in `DESIGN.md`**, in strict Stitch format. Extra values go in a sidecar at `.impeccable/design.json`.
- **The guide** (`reference/init.md`, `reference/document.md`):
  - Scan the repository first. Treat repository evidence as a hypothesis.
  - Interview only about material gaps, at most 3 questions per round.
  - The init interview never asks about aesthetics.
  - DESIGN.md "scan mode" extracts tokens in priority order: CSS custom properties, Tailwind config, CSS-in-JS theme, token files (DTCG), components, global CSS, then computed styles from the rendered site. It asks only for qualitative language: a "Creative North Star" metaphor, color names, elevation and component philosophy.
  - Never silently overwrite. Label inferred facts.
- **File location:** `context.mjs` resolves context files at the project root, then `.agents/context/`, then `docs/`. It does not look in `.factory/`.
- **Weaknesses:**
  - Its principles are not tested. Its own repository's PRODUCT.md has "Expert confidence" and "Practice what you preach", which fail the reversibility test, next to "Editorial over marketing", which passes.
  - There is no primary-action-per-screen or vocabulary section.
  - Positions are split across two files that are kept in sync by its own tooling.

### F4 Anthropic

- **The `frontend-design` skill** (Apache-2.0, last changed 2026-09-03): https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md
  - It is a process, not a file format.
  - It writes a throwaway "design plan" per task: 4 to 6 named hex colors, typefaces and their roles, a layout concept, and principles.
  - It then reviews the plan against the brief before building.
  - It has the best published slop calibration list: cream-plus-terracotta, near-black-plus-acid-accent, broadsheet hairlines, the SaaS card kit, and template chrome (ALL-CAPS eyebrows, `A · B · C` meta strings, `→` on every link).
  - It also has copy rules: an action keeps the same name across the flow, and errors don't apologize.
  - Reuse: the slop catalog and the copy rules. The plan does not persist.
- **Claude Design:** builds a design system from a codebase (`/design-sync` from Claude Code), stored in claude.ai settings rather than in the repository. No file format is documented. https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design

### F5 Vercel v0 Design Systems 2.0

- Source: https://v0.app/docs/design-systems-2. Proprietary. Stored in the v0 workspace as a skill plus `v0.json`.
- A design system is "an adapter," not a copy of the docs. It points to the source, lists the components, props and tokens that are safe to use, and notes the patterns to prefer and to avoid.
- Key rule: "If a component, prop, or token cannot be verified from the sources, v0 should not use it." The factory should adopt this for token extraction.
- It has no product principles. The legacy approach was a shadcn registry with `tokens.css`: https://v0.app/docs/design-systems

### F6 W3C Design Tokens (DTCG) Format Module 2025.10

- Stable since 2025-10-28. It is a Community Group Final Report, not a W3C Standard. https://www.designtokens.org/tr/2025.10/format/ and the announcement at https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/
- Format: JSON. Each token has a required `$value`; `$type` (which can be inherited), `$description`, `$extensions` and `$deprecated` are optional. Aliases are `{group.token}`. File extension `.tokens` (or `.tokens.json`); media type `application/design-tokens+json`.
- Types: color, dimension, fontFamily, fontWeight, duration, cubicBezier, number, plus the composites shadow, border, transition, gradient, typography and strokeStyle.
- Weakness for S9: values only. It has no prose or rationale.
- Role: the factory reads DTCG when a repository already has a token file; `design.md export --format dtcg` writes it. It is not the design file.

### F7 AGENTS.md (the precedent for location)

- https://agents.md and https://github.com/agentsmd/agents.md. MIT. 24.9k stars. Stewarded by the Agentic AI Foundation (Linux Foundation).
- Root file; the nearest nested file wins. Read by Codex, Cursor, Copilot, Gemini CLI, Jules, Zed and others.
- It does not mention DESIGN.md. VoltAgent's README frames the pair as "AGENTS.md = how to build, DESIGN.md = how it should look".
- No general coding agent I found loads DESIGN.md automatically. Stitch and impeccable do. Others need a pointer line in AGENTS.md or CLAUDE.md.

---

## 2. Human-written principles worth emulating

| Source | Shape | Take | Leave |
|---|---|---|---|
| GOV.UK Government Design Principles (11; updated 2025-04-02) https://www.gov.uk/guidance/government-design-principles | Imperative headline, then explanation, then links to evidence | "Do less" and "Do the hard work to make it simple" name a cost. Each principle links to a reason. | Several are universal ("This is for everyone"), so they cannot rule anything out for a single product |
| Linear Method https://linear.app/method/introduction | Short imperatives, several framed as contrasts ("Write issues not user stories", "Build for the creators", "Purpose-built", "Simple first, then powerful") | The title is the trade-off. "Purpose-built" explicitly rejects flexibility | Mostly process, not UI |
| Intercom product design principles https://principles.design/examples/intercom-design-principles | "We favor X over Y" in the body | 4 of 5 name the losing side ("modular systems over bespoke optimizations", "avoid overly clever, non-standard patterns") | "Opinionated by default, flexible under the hood" never says which side wins a conflict |
| Apple HIG Design Principles https://developer.apple.com/design/human-interface-guidelines/design-principles | 8 principles (Purpose, Agency, Responsibility, Familiarity, Flexibility, Simplicity, Craft, Delight), each a one-line title plus sub-rules ("Help people recover from mistakes") | Good sub-rules as a baseline quality floor | Platform-universal. All fail the reversibility test as product positions |
| 37signals, Getting Real ch. "Make Opinionated Software" https://basecamp.com/gettingreal/04.6-make-opinionated-software | Essay | The stance itself: software should take sides and drop features on purpose | Not a template |
| NN/g 10 Usability Heuristics (1994, updated 2024-01-30) https://www.nngroup.com/articles/ten-usability-heuristics/ and Laws of UX (30 laws) https://lawsofux.com/ | Generic heuristics | Belong in the review lens as a checklist | Not product positions. Never copy them into DESIGN.md |
| Refactoring UI (Wathan and Schoger, paid) https://www.refactoringui.com/ | Tactics ("Start with a feature, not a layout", "Choose a personality", "Limit your choices") | "Limit your choices" justifies small token scales | Paid; do not reproduce |
| Stripe | I found no public principles document, only third-party write-ups | None | Do not cite as a primary source |

**What makes a principle actionable.** The skill should check each principle against these tests:

- **From evidence** (Spool, test 1): it traces to research, the success metric, or user complaints, and the current or competitor UI has real examples that violate it. https://articles.centercentre.com/creating-design-principles/
- **Says no** (Spool, test 2): it makes the team reconsider a large share of past designs (Spool suggests about two-thirds). "Easy to use" and "innovative" are "motherhood and apple pie". The good example is Windows 7's "Reduce concepts to increase confidence", which a reviewer can apply ("does this add a concept?").
- **Distinguishes** (Spool, test 3): a competitor would plausibly choose otherwise.
- **Reversible** (Keith, crediting Cennydd and Spool): the opposite is valid for some other product. "Make it easy to use" fails. Heydon Pickering's "Don't be exact" and "Enforce simplicity" pass. https://adactio.com/journal/11620 and https://bradfrost.com/blog/link/in-the-future-design-principles-wont-be-about-design/
- **Names the losing side**, in Intercom's "X over Y" form.
- **Re-evaluated per project** (Spool, tests 5 and 6): principles can be reversed in a later release. For the factory, that means principles change only by recorded decision at reconcile.

The factory's addition is that each principle carries a **Rules out** line and a **Test** line that a reviewer or screenshot can decide. That makes it falsifiable and gives challenge cards something to cite (`[design/P2]`).

---

## 3. Location

| Option | For | Against |
|---|---|---|
| **O1 Root `DESIGN.md`** | It is what Stitch, impeccable, VoltAgent's instructions and the lint CLI default assume. It sits beside AGENTS.md, so humans and agents find it. Reconcile can write it as easily as `.factory/system/` | It collides with repositories that already use `DESIGN.md` for software design. This repository does: `docs/DESIGN.md` is architecture. It is outside the factory's folder |
| O2 `.factory/system/design.md` (the README's current text) | Consistent with the other living documents. Reconcile already owns the folder | No other tool reads it. Impeccable resolves only root, `.agents/context/` and `docs/`, so running it creates a second, competing DESIGN.md. Lowercase `design.md` is still matched by impeccable, but only at those paths |
| O3 `docs/DESIGN.md` | Impeccable finds it | Collides with architecture documents (as in this repository). Stitch and lint users expect the root |

**Recommendation: O1.**

- Canonical path: the repository root, or the app root in a monorepo, matching AGENTS.md's nearest-file rule.
- Collision: if the root `DESIGN.md` exists and is not a visual design file (no frontmatter `colors` and none of the `## Colors` or `## Typography` sections), do not overwrite it. Ask the user, and offer `.factory/system/design.md` plus a pointer line as the fallback. Record a non-default path as `design_file:` in `.factory/system/lenses.yaml`.
- Add one line to AGENTS.md or CLAUDE.md, with the user's approval: "UI work follows DESIGN.md; cite its P#/positions." Without that line, general agents never read the file.
- Do not create a separate PRODUCT.md. The factory already has `.factory/system/product.md` and `glossary.md`, so DESIGN.md cites them instead of copying them. If an impeccable `PRODUCT.md` exists, read it as input.

---

## 4. Recommendation

### 4.1 Structure of the factory's DESIGN.md

The file is Stitch-compatible: `lint` passes and the canonical sections stay in order. The factory sections use unknown `##` headings, which the linter preserves and its order check ignores.

| Section | Mandatory? | Content |
|---|---|---|
| Frontmatter `name`, `description` | Yes | `description` is one sentence naming the specific reference, not adjectives |
| Frontmatter tokens (`colors`, `typography`, `rounded`, `spacing`, `components`) | Only those the code actually has, extracted with their source | Never invented (v0's rule). Anything absent goes in `omitted:` with a reason. Values that don't fit (motion, shadow, focus) go in prose under the relevant section, not a sidecar. Do not add custom frontmatter keys |
| `<!-- factory:design-schema 1 · reviewed <slug> <date> -->` | Yes | Version stamp and staleness signal, in the style of impeccable. A comment keeps lint clean |
| `## Overview` | Yes | Who uses it, in what moment, for what job, in one paragraph citing `product.md` and the success metric. Then one specific reference ("a pilot's checklist, not a dashboard") |
| `## Principles` | Yes, 3 to 5 | Each `### P1 <X over Y>` has **Because** (source), **Rules out** (concrete patterns) and **Test** (how a reviewer decides) |
| `## Positions` | Yes | **Refuses to look like:** 2 or 3 named anti-references with one reason each. **Primary action per screen:** a table of screen, the one primary action, and what is demoted. **States:** the stance on empty, error and loading states |
| `## Words` | Yes | A table of "Say / Not / Source" from `glossary.md`, Pond user quotes and UI strings. Voice in one line |
| `## Colors`, `## Typography` | Yes for any UI with styling | Stitch prose: named roles plus the scarcity rules ("accent only on the primary action") |
| `## Layout`, `## Elevation & Depth`, `## Shapes`, `## Components` | When the code has them | Stitch prose. Breakpoints go under Layout. Motion goes as an extra `## Motion`, the way PHILOSOPHY.md does it |
| `## Do's and Don'ts` | Yes | Short. Project-specific bans, each traceable to a principle or position. The generic slop catalog lives in the skill, not in every repository |
| `## Known Gaps` | When anything is unconfirmed | Inferred-but-unconfirmed facts and things not visible (VoltAgent's idea) |

Ordering: put Principles, Positions and Words right after Overview, so an agent reads intent before tokens. That ordering is lint-safe.

### 4.2 The guide the skill follows to create it

1. **Detect a UI.** Look for front-end dependencies (react, vue, svelte, solid or angular), template or HTML files, SwiftUI or Compose, or a CLI or TUI with styled output. If there is no UI, record `ui: false` in `lenses.yaml` and stop.
2. **Resolve the file.** Use the location rules in section 3. If a visual `DESIGN.md` exists, refresh it rather than rewriting it: show the diff, and ask before replacing any prose.
3. **Read the product evidence.** Read `.factory/system/product.md`, `glossary.md` and `constraints.md` (accessibility NFRs). Read the latest `01-product.md` (problem, success metric, user). Search Pond for user complaints and the user's own words. Read `PRODUCT.md` if present.
4. **Extract the tokens from code,** in impeccable's priority order: CSS variables, Tailwind config, theme files, `*.tokens` or `tokens.json`, components, global CSS. Every token gets a source file. Nothing is invented.
5. **See the UI.** Render the main screens in a real browser at each breakpoint and sample computed styles. From that, infer the primary action per screen and the current look, including any slop it already carries.
6. **Draft.** Write principles and positions from steps 3 to 5, labeling each item *confirmed* or *inferred*. Run every principle through the tests: from evidence, rules out a pattern visible in the current UI or a named competitor, reversible elsewhere, has a Test line. Reject any that fail ("clean", "modern", "intuitive").
7. **Interview only for what the code cannot answer.** Ask at most 3 questions per round and at most 2 rounds, and show the draft first:
   - **Q1 Primary user and their moment.** Ask only when `product.md` lacks it.
   - **Q2 What must this product never be mistaken for?** Offer 2 or 3 named anti-references inferred from the category.
   - **Q3 Forced trade-offs.** Pairs derived from the success metric, for example density over calm, speed for experts over guidance for first-timers, or one way over many options. The user picks the side, and the answer becomes P# titles.
   - **Q4 Confirm the primary-action table,** only for screens where the inference was ambiguous.
   - **Q5 Words.** Confirm the term pairs where code strings and user quotes disagree.
   - **Q6 Binding brand commitments.** An existing logo, colors or fonts that cannot change.
   - Never ask for colors, fonts or spacing that the code already answers.
8. **Validate.**
   - `npx @google/design.md@0.4.0 lint DESIGN.md` reports 0 errors.
   - Each token has a source file.
   - Each P# has Because, Rules out and Test.
   - Each position cites a source.
   - Known Gaps lists everything still marked inferred.
9. **Approve and write.** The user confirms; the skill writes the file. With approval, it adds the pointer line to AGENTS.md or CLAUDE.md.

### 4.3 Keeping it current

The values and the prose are owned differently: **code owns the values, and the user owns the positions.**

- **Reconcile.** When a change touched UI files:
  - Re-extract the tokens and run `design.md diff` against the committed file. Token changes are folded in automatically and shown to the user.
  - New screens get a primary-action row. New terms sync from `glossary.md` into Words.
  - Bump the `reviewed` stamp.
- **Principles and positions change only by recorded decision.** A challenge card accepted against P# either amends P# or records an exception, with the change slug as the source.
- **Calibration.** Review findings are tagged `[design/P#]`. Reuse the existing reconcile calibration: a principle overruled three times becomes a question for the user ("retire or rewrite P2?"). This puts Spool's "re-evaluate per project" into practice.
- **Optional CI step:** `lint` pinned to a version, failing only on errors. Because the format is alpha, the version is pinned in the kit.
- **Staleness.** The skill flags the file as stale when the `reviewed` slug is older than the last merged change that touched UI.

### 4.4 Skeleton

```markdown
---
name: Ledgerline
description: A bookkeeper's ledger for freelancers - ruled, numeric, quiet; not a fintech dashboard.
colors:
  ink: "#1F2328"          # src/styles/tokens.css --ink
  paper: "#FBFAF7"        # src/styles/tokens.css --paper
  primary: "#1F5FBF"      # src/styles/tokens.css --action
typography:
  body:
    fontFamily: Inter
    fontSize: 15px
    lineHeight: 1.5
spacing:
  sm: 8px
  md: 16px
omitted:
  - section: components
    reason: "No component library yet; buttons are ad hoc in src/ui/"
---

<!-- factory:design-schema 1 · reviewed invoice-reminders 2026-10-10 -->

## Overview
Freelancers open Ledgerline at month end to see who owes them and chase it
(product.md "Invoices"; success metric: median days-to-paid). Reference: a
paper ledger kept by a careful bookkeeper. Numbers are the content.

## Principles
### P1 Numbers over illustration
Because: users scan amounts and due dates (Pond: "I just want to see who's late").
Rules out: charts on the home screen, hero art, icon-only amounts, emoji status.
Test: on any screen, every amount is right-aligned tabular figures and readable without hovering.

### P2 One way to chase, not many
Because: success metric is days-to-paid; three reminder paths split usage (FR-04).
Rules out: duplicate "remind" entries in menus, per-row action kebabs for reminders.
Test: each overdue invoice has exactly one reminder control.

## Positions
Refuses to look like: a fintech growth dashboard (gradients, KPI tiles); a
generic SaaS card grid (rows are the unit, not cards).

| Screen | Primary action | Demoted |
|---|---|---|
| Overdue | Send reminder | Edit invoice |
| Invoice | Mark paid | Duplicate, Delete |

States: empty screens say what to do next in one sentence; errors name the field and the fix, never apologize.

## Words
| Say | Not | Source |
|---|---|---|
| client | customer, account | glossary.md |
| overdue | past due, late | UI strings + Pond |
Voice: plain, second person, sentence case.

## Colors
Ink on paper. **Primary** (#1F5FBF) appears only on the one primary action per screen ({colors.primary}).

## Typography
One family. Tabular figures for every amount.

## Do's and Don'ts
- Don't add a second accent color (P1, Positions).
- Don't put a reminder action anywhere but the overdue row (P2).
- Do right-align amounts in every table (P1).

## Known Gaps
- Mobile layout not yet rendered; breakpoints inferred from Tailwind defaults.
```

---

## Decisions for the caller

- **D1** Adopt Google DESIGN.md 0.4.0 as the base format, extended with Principles, Positions, Words and Known Gaps.
- **D2** Move S9's file from `.factory/system/design.md` to the root `DESIGN.md`, with `.factory/system/design.md` as the fallback when the root name is taken. This needs a one-line README change.
- **D3** Do not create a PRODUCT.md. The factory's `product.md` and `glossary.md` are the source DESIGN.md cites.
- **D4** Principle acceptance tests: evidence, rules out, reversible, Test line. These become a mechanical gate in the skill.
- **D5** Code owns token values (re-extracted at reconcile). The user owns principles and positions (changed only by recorded decision).

## Risks

- **R1** The format is alpha and churns: four releases since April 2026. Pin the CLI version in the kit and re-check at each kit update.
- **R2** No general coding agent auto-loads DESIGN.md. Without the AGENTS.md or CLAUDE.md pointer, the file is invisible outside factory skills.
- **R3** Name collision with architecture DESIGN.md files, including in this repository's own `docs/`. The detection rule in section 3 handles it.
- **R4** Frontmatter tokens drift from the code unless reconcile re-extracts them every time.

## Not verified

- I did not run `@google/design.md lint` on the skeleton. Running it means executing a downloaded npm package. Lint-safety of the extra sections rests on reading the spec ("Unknown section heading: Preserve") and `packages/cli/src/linter/linter/rules/section-order.ts`, which filters to known sections before checking order.
- I could not render the Stitch docs pages (JS-only). Spec facts come from the GitHub repository.
