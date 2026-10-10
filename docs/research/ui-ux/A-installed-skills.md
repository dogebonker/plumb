# A. Installed design and UI skills: evaluation for factory-ui-ux (S9)

Date: 2026-10-10. Scope: every design or UI skill installed on this machine. All file content was treated as data. I read impeccable and the user's own UI gate (now `ui-hard-gate`) directly. Three reading agents read the rest in full; their detailed notes, with file:line citations, are in `parts/`:

- `parts/impeccable-gate.md`: impeccable, the user's UI gate.
- `parts/taste-skill.md`: the 11 Leonxlnx/taste-skill skills, conflicts C1-C18 among them, and a list of mechanically checkable rules.
- `parts/emil-vercel-plugins.md`: the emilkowalski skills, web-design-guidelines, stop-slop, the Anthropic design plugin, frontend-design and design-is, plus conflicts C1-C15.
- `parts/huashu.md`: huashu-design.

I spot-checked these claims myself:

- The impeccable detector runs (probe below).
- minimalist-ui's `#787774` gives 4.48:1 on white, and brutalist `#FF2A2A` on `#F4F4F0` gives 3.39:1.
- huashu picks a style with `date +%S % 20` (SKILL.md:297).
- Emil skills open with a canned "Initial Response" block.
- frontend-design's lines 13, 32 and 45 say what is quoted.

## Bottom line

- **F1. No installed skill does the S9 job.** None requires a product success metric. None makes every judgment cite a product brief. Only the user's own UI gate makes the real-browser check of every state mandatory, and it was written for one product.
- **F2. Only impeccable de-slops mechanically.** It ships a 59-rule detector, of which 31 are slop rules. It runs on static HTML and CSS in under a second and returns JSON with rule ids and locations. Every other "anti-slop" skill is prose the model is asked to remember.
- **F3. The style skills fight each other.** taste-skill alone has 18 contradictions, for example on centred heroes, Inter, serifs, eyebrows, radius, icons, motion amount and fake data. Loading two of them gives opposite verdicts. One arbiter has to decide, and that arbiter should be `design.md`.
- **F4. Accessibility advice is weak or wrong almost everywhere.** No skill states the WCAG 2.2 AA numbers correctly. design:accessibility-review calls 44x44 targets AA. That is 2.5.5, which is AAA, while the 2.2 AA rule is 2.5.8 at 24x24. design-taste-frontend sets the large-text threshold at "18px". Two style presets fail contrast with their own palettes. This part has to be written in-house and checked by axe-core in a browser.
- **F5. The user's UI gate is the model for S9's output.** It is a per-product brief whose rules each cite repeated, dated evidence. It judges by removal more than by restyling. It requires screenshots of every state, and it reports findings as P0/P1/P2 with a fix. S9's `design.md` should look like a generic, product-derived version of it.

## Per-skill summary

Notes on the table:

- Tokens are bytes/4. Huashu is CJK-heavy, so its real token count is about 2x what the table shows.
- "Mech" means the skill ships executable checks.
- "Grounded" means it derives positions from users, job or metric.
- "Browser" means it renders and inspects the result.

| Skill | Source, license | Size (main + refs) | De-slop | Mech | Grounded | Browser | Verdict |
|---|---|---|---|---|---|---|---|
| impeccable v4.1.1 | Paul Bakaus, Apache-2.0, not in skill-lock (no pin) | 11 KB + 390 KB refs + 3.4 MB scripts | Yes, 31 slop + 28 quality rules | **Yes** | Partial: PRODUCT.md has users and job, no metric. Expressive by default | Yes, injects the detector into the live page | Use its **detector** as the de-slop engine. Mine craft-floor and operate. Do not load the skill. |
| ui-hard-gate (the user's UI gate) | user's own | 11 KB + evidence kept outside this repository | Yes, by removal | No | **Total** (one product) | **Yes, mandatory** | Template for `design.md` and the finding format. Evidence of user standards. |
| design-taste-frontend | Leonxlnx/taste-skill, MIT (repo root only) | 87 KB (~22k tok) | Richest prose catalog | No | Audience and vibe, not job or metric | Instruction only | Mine the catalog (sections 0.D, 4.7, 4.9, 9, 14) and the redesign-preservation rules (11.C, 11.F). Reject as a lens: landing pages only, says it excludes product UI. |
| redesign-existing-projects | taste-skill, MIT | 15 KB | Broad checklist | No | No | No | Mine the audit order, omissions list and a11y items. It advises fabricating data ("randomize dates") and scroll-jacking. |
| gpt-taste | taste-skill, MIT | 8 KB | Small | No | Anti: RNG from prompt length | No | Reject. |
| high-end-visual-design | taste-skill, MIT | 11 KB | Small | No | No, fixed premium style | No | Reject: animates every element over 800ms+ with no reduced motion. |
| minimalist-ui | taste-skill, MIT | 8 KB | Small | No | No, fixed style | No | Reject: its secondary text colour fails AA. |
| industrial-brutalist-ui | taste-skill, MIT | 8 KB | No | No | No, fixed style | No | Reject: accent colour fails AA, fake "REV 2.6" data strings. |
| image-to-code, imagegen-frontend-web/-mobile | taste-skill, MIT | 36-40 KB each | Prose | No | Funnel and flow level, inferred | No (images) | Reject. Mine the nested-box, micro-label, KPI, marquee and gradient slop items and the mobile safe-area rules. |
| brandkit | taste-skill, MIT | 16 KB | Logo slop only | No | Brand strategy | No | Reject (out of scope). |
| full-output-enforcement | taste-skill, MIT | 2.6 KB | n/a | No | n/a | No | Reject (not UI). |
| frontend-design | claude-plugins-official, Apache-2.0 | 9.4 KB (~2.3k) | **Best compact catalog, with values** | No, but convertible | **Best**: subject, audience, primary job (:13) | Optional screenshots | **Adopt as a lens** for visual direction and de-slop. Convert :17-43 into checks. |
| review-animations (STANDARDS.md) | emilkowalski/skills, licence unverified | 9.8 KB | Motion only | Convertible | Frequency of use | Manual DevTools | **Adopt STANDARDS.md as the motion lens after patching.** Licence check first. |
| emil-design-eng, animate, improve-animations, find-animation-opportunities | emilkowalski/skills | 10-27 KB each | Motion only | Grep sweeps | Frequency, "personality" | Manual | Mine: the frequency gate, the "delete the animation" first step, the rejected-candidates section, CDP feel-check steps. The same core is copied 5 times. |
| apple-design | emilkowalski/skills | 23 KB | No | No | Partial | Manual | Conditional lens for gesture-heavy UI. Mine the reduced-motion, reduced-transparency and prefers-contrast trio and the size-specific tracking. Its default glass toolbars work against de-slop. |
| animation-vocabulary, pick-ui-library, ask-sonner | emilkowalski/skills | 5-13 KB | No | No | No | No | Reject. |
| web-design-guidelines | vercel-labs, rules unlicensed | 1.2 KB wrapper + remote rules | Engineering hygiene | Mostly lintable | No | No | Reject the wrapper: it fetches `command.md` from `main`, so it is unpinned and the remote page sets the output format. **Vendor the rules at a fixed commit** as code checks for focus, forms, labels and glyphs. Override its Title Case rule. |
| stop-slop | hardikpandya, MIT | 12.5 KB | Prose tells | Phrase lists are greppable | No | n/a | Mine for long-form copy only. On microcopy it misfires (adverbs, "What's new", passive "Payment declined"). |
| design:design-critique | Anthropic knowledge-work-plugins | 3.9 KB | No | No | Asks, derives nothing | No | Reject. |
| design:accessibility-review | same | 4.3 KB | No | No | No | No | Mine the report tables only. Criteria are WCAG 2.1 and the target-size level is wrong. |
| design:ux-copy | same | 3.4 KB | Greppable patterns ("Submit", "OK", "Click here") | Partly | User state | No | Mine the CTA, error, empty-state and confirm patterns. Reject "empathetic errors" and the mandatory three alternatives. |
| design:design-system | same | 5.6 KB | Token drift | Convertible | No | No | Mine the hard-coded-value count as a slop check. |
| design:design-handoff | same | 4.0 KB | No | No | No | No | Mine the required-states list for screenshots. |
| design:user-research, research-synthesis | same | 4.8 KB | n/a | n/a | Evidence discipline | n/a | Mine for `design.md` evidence fields ("separate observations from interpretations"). |
| design-is | thedotmack/claude-mem, Apache-2.0 | 18.8 KB | Evidence fields, dark patterns | Partly | Primary user and task | Via agent-browser, marks "INFERRED" | Mine: the evidence contract, the observed vs inferred label, "pick the lower score" and "score the worst instance". Reject as a lens (its own orchestrator). |
| huashu-design | alchaincyf, MIT (relicensed 2026-05-14) | 65 KB + 530 KB refs. Install 33 MB, of which 26 MB is MP3 | 24 prose items | No | Brand assets, not users. Default style picked by clock seconds | Screenshots plus console errors only | Reject as a lens. It stops for three drafts even "unattended" and calls `git ls-remote` every 30 days. Mine typography.md sections 0-3, 5, 6, the critique-guide "works with a different product name = template" veto, and the colour-derivation protocol (design-styles.md:22-57). |
| visual-verdict (OMC) | oh-my-claudecode | 2.4 KB | No | No | No | Compares screenshots to a reference | Out of scope. It could later serve reference-fidelity checks. |

## impeccable vs design-taste-frontend (the two the roadmap names)

- **impeccable is better than its reputation on mechanics and worse on stance.**
  - Strengths: a real detector, PRODUCT.md, browser injection, and modes (Operate mode permits density and system fonts).
  - Weaknesses:
    - Its default posture is "Go all out ... Dream big and bold" and "when torn between refined and committed, commit".
    - concept-seed.mjs rolls dice to choose which three layout concepts reach the user.
    - A critique needs two sub-agents, a live server, a persisted snapshot and a closing question.
    - It installs an always-on hook and a `.impeccable/` state directory.
    - It contradicts itself on custom scrollbars (craft-floor says theme them, operate.md says do not reinvent them) and on where personas come from (CLAUDE.md in v3, PRODUCT.md in v4).
    - It misapplies Cowan's working-memory limit to visible options ("<=4 visible options", "<=5 nav items").
    - It flags Inter and Geist as slop outright, and the user's product ships Inter and plans Geist.
- **design-taste-frontend is a long ban list for landing pages.**
  - It excludes product UI by its own statement.
  - It costs about 22k tokens.
  - It pushes motion by default (dials at 8/6/4, and "the page must actually move" above 4).
  - It has accessibility errors: 18px counted as large text, `transition: all` as the default, and a horizontal pan that clips content under reduced motion.
  - Its catalog is still the most specific list of AI tells available. About 30 items convert to grep or DOM checks (`parts/taste-skill.md`, "Mechanically checkable extract").
- **How S9 beats both.**
  1. Write the product brief first, and make every finding cite it.
  2. Run the de-slop pass as code before any opinion.
  3. Make removal a first-class verdict.
  4. Require a real-browser render of every state at each breakpoint.
  5. Keep the token cost small by loading one lens per component.

## Probe: impeccable detector on a 15-line slop page

`probe/slop.html` contained:

- An Inter body.
- A 96px purple-cyan gradient-text h1.
- An "Introducing" eyebrow.
- Cards with a 4px left border and a purple glow, one nested inside another.
- Emoji headings ("🚀 Fast").
- Buzzword copy.

`node ~/.claude/skills/impeccable/scripts/detect.mjs --json slop.html` exited with code 2 and reported 18 findings: side-tab x4, gradient-text x2, dark-glow x5, hero-eyebrow-chip, extreme-negative-tracking, overused-font, nested-cards, skipped-heading, ai-color-palette, marketing-buzzword.

It missed:

- Emoji used as icons, which craft-floor bans but no rule checks.
- The row of three identical icon+title+text cards, craft-floor's first "refuse" item, also with no rule.
- The filler line "Unlock the power of AI".
- The 96px h1, because the rule's threshold is above 6rem.

So the detector is a solid base, and S9 must add the missing rules (`parts/taste-skill.md` and frontend-design :17-43 supply them). URL scanning needs puppeteer, which is not installed. Running it inside the factory's own Playwright session avoids that.

## What the user's UI gate tells us about the user's standards

The user is a second UI approver and built this gate from the recorded review feedback of the product's final UI approver. The generic rules are now `skills/ui-hard-gate` (H1 to H22); the evidence itself stays outside this repository, and no quote from it is reproduced here.

- **M1. AI does not make design calls. Start from a reference.** The gate's first step stops when there is no visual reference to build from. For S9: the brief and a named reference come before any build; opinions without one are proposals, not decisions.
- **M2. Slop is judged by whether it looks generated, and the fix is removal** (H2). Of the approver's own 18 UI changes, 13 were removals, renames, defaults or failure-state fixes, not new features.
- **M3. Less on screen, detail on demand** (H1). "Too much" is the most repeated complaint.
- **M4. Density is a balance** (H15): cards rejected as too compact and, elsewhere, as too large. The resolution is less content per card, more padding around it, normal-size controls, and one unit of content fitting a laptop viewport.
- **M5. Honest state, every state** (H5 to H9): a visible running state that survives a refresh, one loader style, distinct loading, empty, failed and done states, "Completed" only when complete, specific errors, and failing closed.
- **M6. Customer words, not machinery** (H10), and names that say what a thing does for the user.
- **M7. Copy matches the backend and states each fact once** (H11, H12), in a neutral, factual tone.
- **M8. One way to do one thing, one filled primary** (H3, H16).
- **M9. Precision and alignment matter** (H15): even grids, no ragged last row, no stray offsets.
- **M10. Keep what the current screen has** when copying a reference (workflow step 1).
- **M11. Process discipline** (Present): nothing out of scope, acceptance criteria checked point by point, before and after screenshots of every state, a manual test table, a "Not verified" line, and findings as `(P0|P1|P2) <title>`, what is wrong, screenshot, fix.
- **M12. Self-roast before handover** (workflow step 5): visual misses in mocks went unnoticed until someone looked at the renders.

What S9 should take from this:

- The user's taste is restraint plus correctness: fewer elements, honest states, precise words, and alignment. It is not expression.
- That matches impeccable's Operate mode and frontend-design's copy rules. It conflicts with the "bold, award-winning" default of impeccable, taste-skill and huashu.
- S9 should default to the Operate posture for product UI and treat expression as something the brief opts into.

## Lens and source map for factory-ui-ux

S9 should load at most two of these per step, chosen by `design.md` and the surface:

| Component | Use | Why |
|---|---|---|
| De-slop (mechanical) | The **impeccable detector** (pinned by a content hash, since the skill lock has none, run from the kit, JSON) plus **S9's own rule additions**: the design-taste-frontend checkable extract, frontend-design :17-43 values, design:design-system token drift, and the probe misses (emoji icons, identical card rows, filler phrases). Rules such as `overused-font` become advisory and give way to `design.md`. | It is the only existing executable catalog, it is fast, and it outputs structured findings. |
| De-slop (catalog text, judgment) | **frontend-design** (9.4 KB, Apache-2.0) as the one prose lens. Mine impeccable craft-floor "Refuse". | It is compact, and its "the brief's own words always win" matches the `design.md` arbiter model. |
| Brief (`design.md`) | Own template. Sources: the user's UI gate structure (rules H1..Hn, each backed by repeated evidence), impeccable init's PRODUCT.md questions, frontend-design :13 (subject, audience, primary job), design-is :63, research-synthesis "observations vs interpretations", huashu's "works with a different product name = template" veto. **Add what none have**: the success metric, refusals ("what this product refuses to look like"), the one primary action per screen, users' own words, and usage frequency per surface. | No installed skill writes this. The user's UI gate shows the target shape. |
| Typography | frontend-design :19-23. Mine impeccable typeset.md (16px floor, 45-75ch, role scale), apple-design size-specific tracking, and huashu typography.md sections 0-3, 5, 6. | No standalone typography skill qualifies. |
| Layout | frontend-design :30, :45-53. impeccable operate.md (product permissions: density, standard nav, consistency). ui-hard-gate H14-H18 as an example of layout rules. | Layout must come from the job and density. Generic layout rules conflict. |
| Motion | **review-animations STANDARDS.md**, patched for W1-W5: per-element duration budgets instead of a flat 300ms, the clip-path acceleration claim removed, the missing `@keyframes fade` defined, the stagger default made visible, fades exempted in reduced-motion branches. Strip the "Initial Response" block. Licence check first. Turn its escalation triggers into regex and DOM checks. apple-design only for gesture UI. | It is the cleanest values-only file. The other Emil skills duplicate it. |
| Copy | Assembled: frontend-design :61-71 (user vocabulary, CTA names the outcome, same verb through the flow, errors don't apologize, sentence case) + design:ux-copy patterns + ui-hard-gate H10-H12 as the example. stop-slop phrase regex on long-form copy only. | No single copy skill is right. stop-slop misfires on microcopy. |
| Accessibility | **In-house WCAG 2.2 AA table** (2.5.8 24x24, 2.4.11, 2.5.7, 3.3.8, 1.4.10/12/13, 2.2.2) + axe-core in the real browser + web-design-guidelines rules vendored at a commit + apple-design's media-query trio + design:accessibility-review report tables. | Every candidate is outdated or wrong somewhere. |
| Browser verification | Own step: Playwright at each breakpoint; screenshots of default, loading, empty, error, success, read-only and refresh-mid-flow (ui-hard-gate step 4 + design-handoff states); CDP reduced-motion emulation and playback rate (improve-animations PLAN-TEMPLATE :63-64); the detector injected into the page; design-is "observed vs INFERRED" labels. | Only the user's UI gate makes this mandatory. |

## Rejected, with the reason

- **R1. gpt-taste, high-end-visual-design, minimalist-ui and industrial-brutalist-ui.** These are fixed styles or RNG-picked styles that ignore the product. Three of them animate everything with no reduced-motion handling, and two fail contrast with their own palettes.
- **R2. image-to-code, imagegen-frontend-web/-mobile and brandkit.** These produce images, not code. Their pipelines are outside S9 scope.
- **R3. huashu-design as a lens.**
  - It is a prototype, deck and video studio, not a product UI reviewer.
  - It stops for three drafts even in unattended runs and picks its default style from the clock.
  - It calls `git ls-remote` every 30 days, installs unpinned skills through `npx -y hyperframes`, and watermarks exports.
  - Its real token cost is about 36k for SKILL.md alone, and the install is 33 MB.
- **R4. design:design-critique, animation-vocabulary, pick-ui-library, ask-sonner and full-output-enforcement.** They are generic, narrow, or not about UI.
- **R5. impeccable and design-taste-frontend loaded whole.** Both are too large and expressive by default. Each conflicts with restraint-first product UI. Use their parts as described above.

## Conflicts S9 must settle (pick once, record in design.md)

- **K1. Fonts.** Inter, Geist and system fonts are banned by impeccable, taste-skill and huashu, but allowed by impeccable Operate mode and apple-design, and shipped by the user's product. Rule: a font is slop only when `design.md` did not choose it.
- **K2. Hero layout.** Centred and split heroes are each called slop by some skill. S9 should not take a position. It should flag the layout only when it is interchangeable with an unrelated product, per impeccable's specificity test and huashu's "works with a different product name" test.
- **K3. Motion amount.**
  - "the page must move" (taste-skill) against "one authored moment" (impeccable, frontend-design) and "delete the animation" first (review-animations).
  - Default for product UI: motion conveys state only. Use per-element duration budgets and keep feedback under reduced motion.
- **K4. Case.** web-design-guidelines' Title Case against sentence case (frontend-design, ux-copy, ui-hard-gate H12's no ALL CAPS). Default to sentence case.
- **K5. Error tone.** ux-copy's "empathetic" against "errors don't apologize". Take the latter, plus ui-hard-gate H7's "what failed + in-place retry".
- **K6. Fake data.** taste-skill and redesign tell the model to invent "messy" numbers and "randomize dates". That conflicts with honesty, impeccable's "never fabricate" and ui-hard-gate H6. S9 bans fabricated proof outright.
- **K7. Glass and translucency.** apple-design defaults to it, every de-slop list flags it. Allow it only when `design.md` chooses it and contrast is verified in the browser.
- **K8. Target size.** 24x24 is the AA floor (2.5.8). 44x44 is the target for touch-first briefs. Never label 44 as AA.

## Gaps no installed skill covers

- **G1.** A success metric tied to design judgments.
- **G2.** Findings that must cite a brief line.
- **G3.** Correct WCAG 2.2 AA numbers.
- **G4.** Mandatory real-browser verification across breakpoints and states (except the user's UI gate, which was written for one product).
- **G5.** A "cut it" verdict with its cost argued. impeccable's distill and ui-hard-gate H2 come closest.
- **G6.** Pinning. impeccable is not in the skill lock, and web-design-guidelines fetches from `main` at run time.
