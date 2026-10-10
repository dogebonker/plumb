# factory-ui-ux: what it loads, and why

The decision record for S9. Evidence is in [ui-ux/](ui-ux/): A (every design skill installed here, read in full), B (formats for a design file written for agents), C (methods for product-grounded design opinions, and the standards in `ui-hard-gate`), D (mechanical slop detection and browser tooling, tested on planted-slop fixtures). Researched 2026-10-10.

## The problem

Existing design skills polish surfaces. None ties a judgment to the product's users, job or success metric, none makes every finding cite a product brief, and only one de-slops mechanically (A). The style skills also contradict each other: taste-skill alone holds 18 contradictions (hero layout, Inter, serifs, radius, motion amount), so loading any two gives opposite verdicts (A F3). And the user's own standard, recorded from their PM's real feedback in `ui-hard-gate`, is restraint and correctness, not expression: 13 of 18 of the PM's own UI changes were removals, renames, defaults or failure-state fixes, and his test for slop is "looks generated rather than designed." (A, C F4).

## Decisions

### UI-1. Every repository with a UI has a `DESIGN.md`, and the factory enforces it

- **Format:** [Google Labs DESIGN.md](https://github.com/google-labs-code/design.md) (Apache-2.0, 0.4.0, linted by `@google/design.md`), extended with the factory's product sections: Overview (user, moment, job, success metric, one specific reference), Principles (3 to 5, each "X over Y" with Because, Rules out, Test), Positions (what it refuses to look like, one primary action per screen, the states contract), Words (say, not, source), and Known Gaps. Tokens come only from the code, each citing its source file; nothing is invented.
- **Why this format:** it is the only open, linted, widely adopted file format for design aimed at coding agents, and the one other tools read (B F1). Its linter keeps unknown `##` sections and ignores them in its order check, so the product sections stay lint-clean (B F2). Its own weakness, visual identity only with no product positions, is exactly what the extension fills.
- **Where:** the repository root, because Stitch, impeccable and the linter look there; a file under `.factory/` would make those tools write a second, competing root file (B section 3). When a root `DESIGN.md` already holds something else (an architecture document, for example), the file is `.factory/system/design.md` and the user is told why. A design file carries the stamp `factory:design-schema`; that stamp, not the file name, is what the hook and the runner accept.
- **Enforced three ways:** triage marks a change that touches UI with `ui: true`; every gate skill, build and review stop on such a change until the design file exists; the hard-gate hook blocks source edits on it; and the headless runner sends it to `/factory-ui-ux` first, where the draft waits for an approver's confirmation on the pull request.

### UI-2. The skill drafts, the human decides

The PM's most repeated rule in `ui-hard-gate` is "AI doesn't make design calls" (4 times, C F5). So `factory-ui-ux design-md` follows a creation guide (from B section 4.2 and impeccable's PRODUCT.md flow): detect the UI, read the product evidence, extract tokens from code, render the screens, then draft every principle and position labeled `confirmed` or `inferred`, and interview only on what code cannot answer (at most 3 questions per round, 2 rounds). It never overwrites a design file silently. Principles that read like adjectives ("clean", "modern", "intuitive") are rejected by the guide's tests: each must come from evidence, rule out something visible, be the wrong choice for some other product, and carry a test a reviewer can apply (B F6).

### UI-3. Mechanical checks come before any opinion

- **Impeccable's detector** (Apache-2.0, pinned at 4.1.0): 59 rules, offline, JSON with rule IDs; it found 18 planted problems in under a second (A F1, D F1). Run from an empty directory with `--no-config --no-inline-ignores`, so a repository cannot waive its own findings.
- **The factory's slop catalog** (`kit/ui/slop-patterns.yaml`, 22 patterns): each with why it hurts, a tested code pattern, a rendered check and a false-positive note. It covers what impeccable misses: Tailwind v4 gradient text, emoji as icons, glassmorphism, fake social proof, filler copy, three equal cards, hover-scale on everything (D F2).
- **A computed-style script in a real browser** (`kit/ui/slop-metrics.js`): reading computed styles caught every planted tell, where pixel analysis adds value only for contrast over gradients and images (D F3).
- **Playwright 1.63.0 with axe-core 4.13.0** for WCAG 2.2 AA, at 390, 768 and 1280 wide, light and dark, with empty, error and slow states forced by intercepting requests.
- **What the design file declares, the catalog accepts:** a brand that really is purple, or a font chosen with a reason, becomes a documented waiver, not a finding. Font and palette disagreements between sources are settled per product, never banned globally (D F3).
- **Thresholds are advisory until calibrated** on a labeled set of the user's own screens.

### UI-4. Opinions are anchored, checkable and few

From C section 4:

- **Order:** read the anchors (DESIGN.md, the product gate, constraints), run the mechanical pass, walk the primary job on rendered screens at each breakpoint, apply the cut test to each element, then sweep heuristics only for what the walkthrough and audit did not explain.
- **Every finding is a challenge card** with one added field, **Prediction / check**: what you would observe if the objection is right, and how to check it. A finding without a check is taste and caps at `note`. Walkthrough findings are labeled `predicted`, because they are model predictions, not user tests.
- **Cut first:** the cheapest fix wins, in order delete, merge, make it a default, collapse, restyle. A cut must name what stays.
- **Severity:** `block` when the primary job fails a walkthrough step, the screen lies about state, or a DESIGN.md refusal is broken; `fix` when anchored, costly on the main path and checkable; `note` otherwise. At most 3 `block` or `fix` findings per screen and 7 per review, plus one line on what works.
- **No quality scores.** Models pick the better of two designs at about chance (51.6% in UIClip; about 60% in "MLLM as a UI Judge", near 50% on close calls), and absolute scores cluster in the middle (D F4). The model answers closed questions with quoted evidence against DESIGN.md, and runs any comparison in both orders.

### UI-5. Knowledge: the factory's own, plus one pinned rule set

- **Written in-house:** the WCAG 2.2 AA table. Accessibility advice is outdated or wrong in nearly every installed skill: one calls 44 by 44 targets AA (that is AAA; AA is 24 by 24, criterion 2.5.8), and two style skills fail contrast in their own palettes, 4.48:1 and 3.39:1 (A F4).
- **Not loaded yet:** Vercel's `web-design-guidelines`. Its skill fetches its rules from the `main` branch on every run, so pinning the skill pins nothing (A). Vendoring the rules at a fixed commit is follow-up work.
- **Rejected as lenses:** every style skill (gpt-taste, high-end-visual-design, minimalist-ui, industrial-brutalist-ui, design-taste-frontend, the imagegen and brandkit skills): fixed or randomly picked styles that ignore the product, motion everywhere with no reduced-motion handling, contrast failures, or image outputs instead of code. huashu-design is a deck and video studio that phones home and installs unpinned skills. impeccable's own skill is not loaded: its default posture pushes expression ("Dream big and bold") and it runs two sub-agents, a hook and its own state; only its detector is used (A F2).
- **Held back:** the Emil Kowalski motion skills (MIT) are installed, but five errors in `review-animations` need correcting first (A, W1 to W5), and they are not pinned. Anthropic's `frontend-design` installs as a plugin outside the skills lock, so the pin check cannot cover it; its slop and copy lines (A) are candidates to turn into factory checks. Either becomes a lens once pinned through `/factory-packs`.

### UI-6. Restraint by default

Product UI defaults to restraint: one filled primary action per surface, headline first and detail on demand, honest states, the work named rather than the machinery. Expression (bold display type, motion, illustration) is something a product's DESIGN.md opts into with a principle and a test, never a default.

### UI-7. Mockup screenshots are optional, asked at the product gate

When a change touches UI, the product gate asks once whether it needs mockup screenshots. Yes: `factory-ui-ux mockups` writes static HTML per screen and state from the design file's tokens, Words and states contract, runs the slop catalog over it, and captures it with the Playwright CLI (1.63.0, the version already pinned) at 390 and 1280 wide. The screenshots sit in the change folder and are linked from `01-product.md`, so the user approves the pictures with the rules they show, and review later compares the built screens with them. No: a sketch or ASCII, as before. Why ask rather than always render: a new screen or flow is easier to agree on as a picture, while a tweak to an existing screen is clearer as a sentence, and each render downloads a browser the first time and adds images to the change.

## What this does not cover

- **Calibration.** The metric thresholds (centered text, rounded-plus-shadow ratio, type-scale steps) are first guesses; they stay advisory until a labeled set of the user's screens confirms them.
- **The format is alpha.** DESIGN.md has had four releases since April 2026, so its linter is pinned and re-checked at each kit update.
- **Agents outside the factory** do not read DESIGN.md unless an AGENTS.md or CLAUDE.md line points to it; the guide adds that line only with the user's approval.
- **react-doctor's license** is a modified MIT that restricts use as input for training AI systems; the factory uses it only to review code, and records that reading here.
- **Nothing here is installed yet** on this machine (Playwright, axe, impeccable's CLI, the DESIGN.md linter). Each is skipped with its install line until it is.
