# D. Detecting AI UI slop: catalog, tooling, model judgment

Research for `factory-ui-ux` (README roadmap S9: "De-slop as a mechanical pass ... checked from code and from real screenshots before any taste opinion"; "Seen, not imagined"). Date: 2026-10-10. All web content and installed skills were read as data.

## Summary

- **F1. A mechanical slop detector already exists and works.** Impeccable's `detect` (Apache-2.0, Paul Bakaus) has 59 deterministic rules across four engines: regex over source, static HTML+CSS cascade, live browser DOM, and screenshot-based contrast. It runs offline, needs no account, and gives JSON plus exit codes (0 clean, 2 findings, 1 scan error). I ran the copy installed under `~/.claude/skills/impeccable` against two fixtures. On a TSX file it caught 5 tells. On the same page as HTML it caught 12.
- **F2. Its source mode is weak on React and Tailwind.** Copy analyzers (buzzwords, em dashes, aphorisms), type-scale and spacing checks run only on "full pages", so a `.tsx` component gets class-level checks only. The gradient-text regex requires `bg-gradient-to-*` (Tailwind v3) and misses v4's `bg-linear-to-*`, which I confirmed on the fixture. It has no rule for emoji-as-icon, glassmorphism, lorem or fake social proof, three equal cards, centered everything, hover-scale on cards, or animated gradients. The factory should run it against the **rendered URL** and add about 12 `rg` patterns of its own for the gaps.
- **F3. Rendered-DOM metrics beat pixel analysis.** `getComputedStyle` and bounding boxes answer "is this gradient text, glass, a glow, a three-equal-card row, mostly centered, a flat type scale" exactly. Pixels only add value where the DOM cannot say what a person sees: contrast over images, gradients or glass. `axe-core` returns those cases as `incomplete`, which means the slop surfaces are exactly where the standard contrast check gives up. I wrote a 60-line metrics script and verified it in a real Chromium (Section 4).
- **F4. A model is a poor absolute judge of design quality but useful for targeted questions.** Evidence:
  - [UIClip](https://arxiv.org/abs/2404.12500): GPT-4V scored 51.6% on pairwise design-quality choices, near chance, against 75.1% for a fine-tuned CLIP.
  - [MLLM as a UI Judge](https://arxiv.org/abs/2510.08783), 2025: Claude 3.5 Sonnet and GPT-4o reached about 60% pairwise accuracy overall. That rose to 90% or more when humans saw a large gap and fell to about 50% on near-ties. Absolute 7-point scores matched humans exactly only 35-38% of the time and were compressed toward the middle.
  - [VLMs are blind](https://arxiv.org/abs/2407.06581): fine spatial perception fails.
  - [WiserUI-Bench](https://arxiv.org/abs/2505.05026): pairwise judgments show position bias.

  So the model should answer presence and evidence questions against `design.md`, with the mechanical findings attached. It should not give a 0-100 taste score, which is what the local `visual-verdict` skill does.
- **F5. Pins**, each the newest stable release at least 14 days old on 2026-10-10:

  | Tool | Pin | Note |
  |---|---|---|
  | `@playwright/test` | 1.63.0 | |
  | `@axe-core/playwright` | 4.13.0 | bundles axe-core ~4.13 |
  | impeccable detector | 4.1.0 on npm, or pin the skill by git commit | |
  | `eslint-plugin-jsx-a11y` | 6.10.2 | |
  | `eslint-plugin-better-tailwindcss` | 4.7.0 | |
  | `stylelint` | 17.15.0 | optional |
  | `react-doctor` | 0.9.14 | already pinned |
  | `lighthouse` | 13.5.0 | optional, needs Node 22.19 or newer |

  Skip Lighthouse CI, pa11y, APCA and hosted visual-regression services (Section 5).

---

## 1. Sources

Practitioner and vendor:
- Anthropic, "Improving frontend design through Skills", 2025-11-12. Names "distributional convergence". Defaults it lists: "Inter fonts, purple gradients on white backgrounds, and minimal animations". The prompt warns that banning one default produces the next, for example Space Grotesk. <https://claude.com/blog/improving-frontend-design-through-skills>
- Impeccable slop catalog: 65 entries, 59 detector rules and 6 design-review patterns, grouped into visual, type, color, layout, motion, copy and imagery. <https://impeccable.style/slop>. Source: <https://github.com/pbakaus/impeccable>. Local copies: `~/.claude/skills/impeccable` (v4.1.1) and `~/.agents/skills/impeccable` (v4.5.0). Registry: `scripts/detector/registry/antipatterns.mjs`.
- Leonxlnx taste-skill: `~/.agents/skills/design-taste-frontend/SKILL.md` section 9 "AI TELLS", plus `redesign-existing-projects`, from <https://github.com/Leonxlnx/taste-skill>. Covers 3-column equal cards, the "LILA rule" (purple/blue glow), Inter, fake-perfect numbers, "Jane Doe" names, startup brand names (Acme, Nexus), div-built fake screenshots, version-label eyebrows, section-number eyebrows, centered hero, and a beige-and-brass premium palette.
- stop-slop (copy only): `~/.agents/skills/stop-slop/references/phrases.md`, from <https://github.com/hardikpandya/stop-slop>.
- Jeff Humble (The Fountain Institute), "7 Tells that a UI is AI-Generated": neon palettes, dark-mode glow, emoji everywhere, purple gradients, cards on cards, multicolored side tabs, status dots. <https://pages.thefountaininstitute.com/posts/7-tells-that-a-ui-is-ai-generated>
- Jason Zhou (Superdesign), "Why AI design looks generic", 2026-06-15. Inter, indigo/violet (#6366F1, #8B5CF6, #A855F7), centered hero with one CTA, three boxed icon cards, rounded corners plus soft shadows on everything, glass, badge above the headline, colored left-border cards. Cites a Developers Digest audit of Show HN launches (secondhand, not verified). <https://www.superdesign.dev/blog/why-ai-design-looks-generic>
- Laith0003 ux-skill wiki, "How to detect AI slop": thresholds (hero copy 30-45ch, a 1.2/1.25 type ratio, 44px targets), `from-purple-600 to-blue-600`, three equal feature cards, shadow+border+tint cards, "Get started →", round invented stats, a placeholder-name list. <https://github.com/Laith0003/ux-skill/wiki/How-to-detect-AI-slop-in-your-design>
- DeSlop (MIT, one commit, 0 stars). Catalogs cover visual, copy and structure; detection is done by the model, not a script. <https://github.com/nate-zz/DeSlop>
- Tailwind's indigo default: Adam Wathan's August 2025 apology for `bg-indigo-500` in Tailwind UI, reported secondhand at <https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website> and <https://news.aibase.com/zh/news/20365>. The causal story (Tailwind examples → training data → indigo) is plausible commentary, not measured.

Research:
- UIClip (Wu et al., CMU/Apple, UIST'24): <https://arxiv.org/abs/2404.12500>
- MLLM as a UI Judge (Adobe/Berkeley et al., 2025): <https://arxiv.org/abs/2510.08783>
- UICrit (Duan et al., UIST'24): 3,059 critiques of 983 screens. Few-shot and visual prompting improved LLM feedback by 55%, still below experts. <https://arxiv.org/abs/2407.08850>
- WiserUI-Bench / G-FOCUS: 300 A/B-tested UI pairs. Models show position bias and weak behavior prediction. <https://arxiv.org/abs/2505.05026>
- Vision language models are blind (ACCV'24): about 58% average on trivial spatial tasks; failures concentrate where shapes overlap or sit close together. <https://arxiv.org/abs/2407.06581>
- MLLM-as-a-Judge (ICML'24): pairwise comparison is reliable, scoring and batch ranking are poor. <https://arxiv.org/abs/2402.04788>

Tool docs: Playwright accessibility <https://playwright.dev/docs/accessibility-testing> and snapshots <https://playwright.dev/docs/test-snapshots>; the `screenshot` CLI flags come from `packages/playwright-core/src/cli/program.ts`. axe-core tags and `incomplete`: <https://github.com/dequelabs/axe-core/blob/develop/doc/API.md>; rules: `doc/rule-descriptions.md`. Lighthouse CLI flags: <https://github.com/GoogleChrome/lighthouse/blob/main/readme.md>. LHCI upload targets: <https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md>. better-tailwindcss `no-restricted-classes`: <https://github.com/schoero/eslint-plugin-better-tailwindcss/blob/main/docs/rules/no-restricted-classes.md>. Tailwind v4 gradient classes: <https://tailwindcss.com/docs/background-image>. APCA license: <https://github.com/Myndex/apca-w3/blob/master/LICENSE.md>. WCAG 3 contrast status: <https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html>, and the W3C draft placeholder at <https://www.w3.org/WAI/WCAG3/informative/text-and-wording/text-appearance/text-contrast-sufficient-minimum/>. react-doctor: <https://github.com/millionco/react-doctor> (LICENSE read raw).

**Disagreements between sources** (they matter for the skill):
- Impeccable lists **Geist** and **Instrument Serif** as overused. taste-skill recommends Geist as the replacement for Inter and bans Instrument Serif.
- Impeccable bans kicker/eyebrow labels outright. taste-skill bans only version and number eyebrows.
- Anthropic's own prompt warns that each ban breeds the next default.

Conclusion: a font or color blacklist cannot be the rule. A default-font finding means "this was not decided". It clears when `design.md` names the choice and says why.

---

## 2. Pattern catalog

Code patterns are tested `rg -P` expressions (ripgrep 15.1; all matched the fixture in `research-ui/fixture/`). Scope them to `-g '*.{tsx,jsx,html,mdx,css,scss,vue,svelte,astro}'`. "DOM" refers to the metrics script in Section 4, which I ran in Chromium. "Imp" names an impeccable rule id. FP = false-positive risk.

| ID | Pattern | Why it hurts | Detect in code | Detect rendered (DOM or screenshot) | FP | Usual fix |
|---|---|---|---|---|---|---|
| P1 | Purple/indigo/violet accent or gradient (the "AI palette") | The highest-probability default; signals that nobody chose a brand color | `\b(?:from\|via\|to)-(?:indigo\|violet\|purple\|fuchsia)-\d{2,3}\b`, the hexes `#(?:6366f1\|4f46e5\|8b5cf6\|7c3aed\|a855f7\|9333ea)`, and `bg-indigo-(500\|600)` on buttons. Imp `ai-color-palette` (v3 classes and CSS) | DOM `purpleSurfaces` counts background and gradient stops with hue 245-290° and saturation above 0.35 | High when the brand really is purple. Suppress when `design.md` declares the hue. | Take the accent from `design.md`; one accent over neutral tints |
| P2 | Gradient text on headings or metrics | Decoration instead of hierarchy; hurts contrast; axe cannot measure it | `^(?=.*\bbg-clip-text\b)(?=.*\bbg-(?:gradient\|linear\|radial\|conic)-)` plus `background-clip:\s*text`. Imp `gradient-text` (**misses Tailwind v4 `bg-linear-to-*`**, verified) | DOM `gradientText`: computed `background-clip: text` with a gradient `background-image` | Low | Solid color; get emphasis from weight and size |
| P3 | Emoji as icons, bullets or headings | Inconsistent glyph rendering across operating systems; stands in for an icon system; screen readers read the names aloud | `[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B50}]` in JSX and markup. Ignore i18n and user-content fixtures. No Imp rule. | DOM `emojiIcons`: leaf elements whose text is only emoji | Medium. Chat or social products may want them; `design.md` can opt in. | One icon library at one stroke weight; `aria-hidden` on decorative icons |
| P4 | Icon in a rounded tinted square above a heading (feature-card template) | Every generator emits this exact shape | `class(?:Name)?="(?=[^"]*\b(?:w\|size)-(?:8\|10\|12\|14\|16)\b)(?=[^"]*\brounded-(?:md\|lg\|xl\|2xl\|full)\b)(?=[^"]*\bbg-[a-z]+-(?:50\|100\|\d{3}/10)\b)(?=[^"]*\b(?:items\|place)-center\b)[^"]*"`. Imp `icon-tile-stack` (HTML and URL modes only) | Imp `icon-tile-stack` in browser mode | Low-Medium | Icon inline with the heading, or no icon; put the point in the heading text |
| P5 | Three (or four) equal cards as the feature row | Gives every point equal weight; interchangeable; says "template" | `\b(?:(?:sm\|md\|lg):)?grid-cols-3\b\|repeat\(3,\s*1fr\)` combined with a `.map(` over an array whose items have `{icon, title, description}` keys: `rg -U -P '\{\s*(?:icon\|Icon)\s*:[^}]*title\s*:[^}]*desc'` | DOM `cardRows`: a parent with 3-4 visible children of equal width (±2px) on the same top line, each holding a heading and a `<p>` | Medium. Pricing tiers and real comparisons are legitimate. | Rank the points; give one a large slot; merge or cut the rest |
| P6 | Glassmorphism as decoration | Blur costs performance; translucency kills contrast and makes axe report `incomplete` | `^(?=.*\bbackdrop-blur(?:-\w+)?\b)(?=.*\bbg-(?:white\|black\|\w+-\d+)/\d+)` plus `backdrop-filter:\s*blur` | DOM `glass`: `backdrop-filter` set and background alpha below 0.9 | Medium. Legitimate over real content (sticky header over a scrolling list). | Solid surface; use blur only where layers overlap |
| P7 | Rounded-2xl plus shadow-xl on every box | Removes elevation as a signal; everything floats | Counts per file: `\brounded-(?:2xl\|3xl)\b`, `\bshadow-(?:xl\|2xl)\b`. Flag when they co-occur on most card elements. Imp `gpt-thin-border-wide-shadow` covers the hairline-plus-wide-shadow variant. | DOM `roundShadowRatio`: share of boxes over 120×80 with radius ≥16px and a shadow. Advisory above 0.5. | Medium | A radius scale from `design.md`; shadow only on raised layers (menus, dialogs) |
| P8 | Centered everything | Long centered text is hard to read; no reading edge; hero, sections and cards all look alike | Counts: `\btext-center\b\|\bitems-center\b\|\bmx-auto\b\|text-align:\s*center` per section | DOM `centeredRatio`: share of text blocks over 20 characters that are center-aligned. Advisory above about 0.6 outside the hero. | Medium. Short heroes, empty states and dialogs are fine centered. | Left-align body copy; keep one centered moment |
| P9 | Default font with no type scale (Inter, Geist, system) | The face was never chosen; a flat scale gives no hierarchy | `next/font/google` imports of `Inter\|Geist\|Plus_Jakarta_Sans\|Space_Grotesk\|Roboto`; `font-family:\s*(?:Inter\|Roboto\|system-ui)`; no `--text-*` or `fontSize` tokens. Imp `overused-font`, `flat-type-hierarchy` (full pages only) | DOM `families`, `fontSizes`, `sizeSteps`. Flag when adjacent steps are mostly below 1.2, or when there are more than 7 distinct sizes. | High for the face (see the disagreement above); Low for the scale | Name the face and scale in `design.md` with a reason; use fewer sizes with bigger steps |
| P10 | Generic marketing copy ("Unlock the power of", "Seamless", "Supercharge", "Elevate", "Empower", "Next-gen", "Revolutionize", "Effortless", "Harness") | Says nothing the user can verify; replaceable across products | `rg -i -P '\b(?:unlock the power\|seamless(?:ly)?\|supercharge\|empower\|elevate\|unleash\|revolutioniz\w*\|next-gen(?:eration)?\|cutting-edge\|game-chang\w*\|world-class\|enterprise-grade\|effortless(?:ly)?\|harness the power\|streamline)\b'`. Imp `marketing-buzzword`, `aphoristic-cadence`, `em-dash-overuse` (rendered pages only) | Run the same regex over `innerText` of the rendered page | Low-Medium. "Seamless" can be literal, as in seamless tiling. | Use the words users say, listed in `design.md`; a specific verb and noun |
| P11 | Fake social proof: invented testimonials, logo walls, round stats ("10,000+ teams", "99.9%", "10x"), placeholder names (John Doe, Sarah Johnson, Acme) | Unverifiable claims; legal risk; trust drops when spotted | `lorem ipsum\|trusted by [\d,.]+\s*[km+]?\|\b\d{1,3}(?:,\d{3})+\+\|\b99\.9+%\|\b10x\b\|\b(?:john\|jane) (?:doe\|smith)\b\|\bsarah (?:johnson\|chen)\b\|\bacme\b`, plus `★★★★★`, `5\.0`, and logo SVGs named `logo-?\d`. No Imp rule. | Same regex on rendered text; the model checks whether quotes and logos have a source in the repo | Medium. Real metrics exist; require a source (data file, CMS, analytics link) | Cut it, or wire it to real data and attribute it |
| P12 | Lorem ipsum or filler content | The page ships unfinished; design gets judged on fake text lengths | `\blorem ipsum\b\|\bdolor sit amet\b\|placeholder text\|TODO:? copy` | Same, on rendered text | Very low | Real copy, or the longest realistic string (i18n) |
| P13 | Decorative blobs and radial halos | Noise behind content; often a GPU blur layer | `class(?:Name)?="(?=[^"]*\babsolute\b)(?=[^"]*\brounded-full\b)(?=[^"]*\bblur-(?:2xl\|3xl\|\[\d+px\])\b)[^"]*"`; CSS `radial-gradient\([^)]*transparent`, `filter:\s*blur\(\d{2,}px\)`. Imp `radial-halo`, `radial-spotlight-glow`, `codex-grid-background`, `shape-assembled-illustration` | Imp browser mode | Low-Medium | Remove; if the page needs a surface, use a flat tint from the palette |
| P14 | Dark mode with neon glow | The "cool" default; glow lowers legibility and has no meaning | `\bshadow-\w+-(?:400\|500\|600)/\d+\b`, `shadow-\[0_0_`, `drop-shadow-\[0_0_`, `box-shadow:\s*0\s+0\s+\d+px\s+(?:#\|rgb)`. Imp `dark-glow` | DOM `glow`: zero-offset shadow with a saturated color | Low | Neutral elevation; color only on state (focus, error) |
| P15 | Badges, pills and eyebrows everywhere (badge above the H1, "NEW", "v2.0", "01 / Features") | A label before the message; repeated chrome | `rounded-full` with `text-xs` with `uppercase\|tracking-wider` on one element, counted per page; `\b0\d\s*[/·]` section numbers. Imp `hero-eyebrow-chip`, `kicker-above-heading`, `numbered-section-labels` | Imp browser mode | Medium. Real status badges in app UI are fine. | Delete the label or fold it into the heading |
| P16 | Animated gradients, pulsing dots, bounce, marquee | Motion without a reason; vestibular harm; battery cost | `\banimate-(?:bounce\|pulse\|ping\|spin)\b` on non-loading elements; `@keyframes` that animates `background-position`; `bg-\[length:\d+%`. Imp `bounce-easing`, `pulsing-dot`, `marquee`, `blinking-cursor`, `layout-transition` | Imp browser mode; also load with `--color-scheme` and `reducedMotion: 'reduce'` and check whether anything still moves | Low | One authored moment; honor `prefers-reduced-motion` |
| P17 | Hover-scale or lift on everything | Every element claims to be clickable; layout jiggle | Count of `\bhover:(?:scale-1(?:0[1-9]\|[1-9]\d)\|-?translate-y-)` plus `:hover\s*\{[^}]*scale\(`. Flag when it is on cards that are not links. Imp `image-hover-transform` covers images only. | Code-side only (hover state needs interaction); Playwright `hover()` plus a screenshot diff if needed | Medium | Hover states only on interactive elements; color or underline, not scale |
| P18 | Missing reduced-motion handling while motion exists | WCAG 2.3.3 (AAA); user harm | Any `animate-\|@keyframes\|motion\.` with no `motion-reduce:\|motion-safe:\|prefers-reduced-motion\|useReducedMotion` in the repo | Emulate `reducedMotion: 'reduce'` and diff two screenshots taken 500ms apart | Low | Gate decorative motion |
| P19 | Side-tab accent borders and nested cards | Every card looks like an alert; depth noise | `border-l-(?:[2-8])\b` with a colored `border-\w+-\d+` on cards. Imp `side-tab`, `border-accent-on-rounded`, `nested-cards` | Imp browser mode | Low | Remove; separate with spacing and type |
| P20 | Template page skeleton (Hero → Features → Testimonials → Pricing → FAQ → CTA) with section families repeated | Interchangeable product page | Component and file names: all of `Hero`, `Features`, `Testimonials`, `Pricing`, `FAQ`, `CTA` exist under one route | Model question (Section 3) | Medium | Sections ordered by the user's questions from `design.md`; cut what has no evidence |
| P21 | Div-built fake product screenshots, terminals or dashboards | Fakes the product; breaks at every breakpoint | Hard to grep: many `rounded` `div`s with `bg-gray-\d+ h-2 w-\d+/\d` skeleton bars outside a loading component | Model question with a crop | Medium | A real screenshot or nothing |
| P22 | Missing states (empty, loading, error, disabled) | AI output ships only the happy path | For each data-fetching component, look for `isLoading\|isError\|error\|empty\|length === 0` branches | Playwright with routes mocked to 0 items, 500, and slow responses, then screenshot | Low | Design every state; this is the interface gate's job |

Accessibility and quality checks that pair with slop (axe and Imp cover them): contrast (P2, P6 and P14 make it unmeasurable), heading order (Imp `skipped-heading`, verified on the fixture), line length, tiny text, touch target size (axe `target-size`, tag `wcag22aa`), cramped padding, text overflow at 390px.

---

## 3. Can a model judge screenshots for slop?

**Evidence**
- [UIClip](https://arxiv.org/abs/2404.12500): on pairs where one screenshot had injected design defects, GPT-4V picked the better design 51.6% of the time (LLaVA 54.6%), near random. GPT-4V sometimes preferred the defective screen with "realistic-sounding but inaccurate reasoning". A 2.3M-pair fine-tuned CLIP reached 75.1%.
- [MLLM as a UI Judge](https://arxiv.org/abs/2510.08783): 30 UIs, 9 factors, about 9.3k human ratings.
  - Pairwise accuracy was about 60% for Claude 3.5 Sonnet and GPT-4o and 53% for Llama.
  - Accuracy rose to about 90% or more when humans saw a large gap and stayed near 50% on near-ties.
  - Absolute Likert scores were exactly right 35-38% of the time and within ±1 72-77% of the time, with smaller variance than human scores.
  - "Ease of use" was overrated and "interesting" was underrated.
  - The authors recommend models "supplement" early evaluation, not replace people.
- [UICrit](https://arxiv.org/abs/2407.08850): few-shot examples and visual prompting (marking regions) raised critique quality 55%, still below human experts.
- [WiserUI-Bench](https://arxiv.org/abs/2505.05026): position bias in pairwise judgments; poor at predicting which A/B variant performs better.
- [VLMs are blind](https://arxiv.org/abs/2407.06581): spatial details that are close or overlapping get misread. This rules out "is this 8px off" judgments.
- Anthropic's frontend post evaluates only by side-by-side examples, with no metric.

**Limits that follow**
- **L1.** No absolute scores. A 0-100 score with a 90 pass bar (the local `visual-verdict` skill) measures the model's prior, not the page.
- **L2.** No pixel-precision claims (alignment, spacing, contrast). Those come from the DOM and axe.
- **L3.** "Is this good?" is near chance. "Is there an X here?" is the kind of large gap where models do well.
- **L4.** Pairwise comparisons need both orders; when the two orders disagree, the result is "no signal".

**How to structure the check**
1. Mechanical pass first (Section 6). Its JSON goes into the model's context as facts, so the model never re-derives "is this gradient text".
2. Inputs: the `design.md` excerpt (refusals, primary action, users' words); full-page screenshots at 390, 768 and 1280 in light and dark; and section crops at deviceScaleFactor 2, because crops help small-detail perception.
3. A rubric of closed questions, each answered `yes/no/unsure` with an evidence field that must quote visible text or name a region:
   - Q1. What is the one primary action on this screen? Does it match `design.md`?
   - Q2. Does the hero say what the product does in the users' words listed in `design.md`? Quote it.
   - Q3. Are any testimonials, logos or statistics shown? For each, is there a source in the repository?
   - Q4. Is any product preview built from shapes rather than a real screenshot (P21)?
   - Q5. Does the page follow the template skeleton (P20)? Name the sections in order.
   - Q6. Which items in `design.md`'s "refuses to look like" list are present? Cite the region.
   - Q7. Do any two sections share the same layout family?
   - Q8. At 390px, is anything clipped, overlapping or unreachable?
4. Pairwise only against a baseline (previous screenshot or mockup), run in both orders. Report a difference only when both orders agree.
5. Every model finding goes through the challenge card from the README (argue the current design first) and cites `design.md`, not taste.
6. Calibrate by keeping a small gold set: the fixture page plus 3-5 real screens labelled by the user. Re-run the gold set when the model or prompt changes, and report agreement.

---

## 4. Rendered-DOM metrics script (tested)

File: `research-ui/fixture/slop-metrics.js` (60 lines, no dependencies). Run it with `page.evaluate(fs.readFileSync(...))` in Playwright after `waitForLoadState('networkidle')`. Output on `fixture/page.html` in Chromium (via the Claude Browser pane):

```json
{"textBlocks":5,"centeredRatio":0.4,"fontSizes":[12,13,16,19,64],"sizeSteps":[1.08,1.23,1.19,3.37],
 "families":["inter","arial"],"gradientText":1,"glass":3,"glow":1,"purpleSurfaces":2,"emojiIcons":3,
 "boxes":6,"roundShadowRatio":0.5,"cardRows":1}
```

Every planted tell was detected. Caveats:
- `families` includes UA defaults such as Arial on `<button>`. That is itself a finding: the button font was not set.
- Thresholds are not calibrated. Treat them as advisory until the gold set exists.

Impeccable's browser engine can also be injected without puppeteer. Set `window.__IMPECCABLE_CONFIG__ = {autoScan:false}` via `page.addInitScript` (autoScan otherwise draws overlays into the page), then `page.addScriptTag({path: <skill>/scripts/detector/detect-antipatterns-browser.js})` and `page.evaluate(() => impeccableDetect())`. The exported globals are confirmed in the source; the call path is **untested**. The supported path is `impeccable detect <url>`, which needs `puppeteer` and an installed Chrome.

---

## 5. Tooling

Pin = newest stable release published at least 14 days before 2026-10-10 (from `npm view <pkg> time`).

| Tool | Latest / pin | License | Output | Headless run | Network / telemetry | Account | Verdict |
|---|---|---|---|---|---|---|---|
| `@playwright/test` / `playwright` | 1.64.0 (2026-10-07) / **1.63.0** | Apache-2.0 | PNG/WebP screenshots, `trace.zip`, JSON reporter, ARIA snapshots | Headless by default. CLI: `npx --no-install playwright screenshot --viewport-size "390, 844" --full-page --color-scheme dark --wait-for-timeout 500 $URL $OUT/s-390-dark.png`. Tests: `--trace on`. | Downloads browsers from the Playwright CDN on `install`; no runtime telemetry. `@playwright/cli` 0.1.x writes an update check (`~/Library/Caches/ms-playwright/cli-update-check.json` is present locally). | No | **Pin.** Core of "seen, not imagined". |
| `toHaveScreenshot` (visual regression) | part of `@playwright/test` | Apache-2.0 | PNG and diff PNG | `expect(page).toHaveScreenshot({maxDiffPixelRatio, animations:'disabled', mask})`; `--update-snapshots` | none | No | Use **only** for intentional before/after on a slice. Baselines depend on OS, fonts and GPU, so generate and compare on the same host. Not a slop detector. |
| `@axe-core/playwright` | **4.13.0** (bundles `axe-core ~4.13.0`; axe-core 4.14.0 is 5 days old) | MPL-2.0 | JSON `{violations, incomplete, passes}` | `new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']).analyze()` | none (runs in page) | No | **Pin.** `wcag22aa` adds `target-size`. Treat `incomplete` color-contrast as review items: that is where gradients, glass and images hide failures. |
| impeccable detector | 4.5.2 (2026-10-09) / **4.1.0** on npm; or the vendored skill at a git commit | Apache-2.0 | stderr text, `--json` stdout; exit 0/2/1 | `node <skill>/scripts/detect.mjs --json --no-config <files>` (pure JS; deps css-select, css-tree, domutils, htmlparser2). URLs: `impeccable detect --json --viewport 390x844 $URL` (needs puppeteer and Chrome) | npm build: optional native `@impeccable/cli-*` binary, or a one-time fetch into `~/.impeccable/bin`. No telemetry documented for `detect`. Live mode and image generation are separate features; do not enable them. | No | **Pin, run from a neutral cwd with `--no-config --no-inline-ignores`** (the repository can otherwise waive rules through `.impeccable/config.json` and inline comments, the same pattern as in factory-security). Wrap it with the factory's own gap rules (P3, P5, P6, P11, P12, P17, P18, Tailwind v4 P2). |
| `eslint-plugin-jsx-a11y` | **6.10.2** (2024-10-26) | MIT | ESLint | `eslint .` | none | No | **Propose** in the React pack (`flat/recommended`). Peer range stops at ESLint 9 while ESLint is 10.12; check before proposing for ESLint 10 repositories. `eslint-config-next` already enables a subset. Oxlint ships the same rules natively. |
| `eslint-plugin-better-tailwindcss` | 4.9.0 / **4.7.0** | MIT | ESLint | `no-restricted-classes` with regex patterns (one class at a time; cannot express "A and B together") | none | No | **Optional.** Good for hard bans the brief declares (e.g. `^(?:.*:)?(?:from\|to\|via)-(?:indigo\|violet\|purple)-\d+$`). Co-occurrence rules stay in `rg`. Supports Tailwind 3 and 4. `eslint-plugin-tailwindcss` 4.4.0 requires Tailwind 4 and has no restriction rule worth adding. |
| `stylelint` | 17.16.0 / **17.15.0** | MIT | JSON formatter | `declaration-property-value-disallowed-list` (e.g. `background-clip: [text]`, `backdrop-filter: [/blur/]`), `function-disallowed-list`, `font-family-name-quotes` | none | No | **Optional**; only for repositories with real CSS. Tailwind-only repositories get nothing from it. |
| `react-doctor` | 0.9.17 / **0.9.14** (already in `kit/languages/react.yaml`) | **"Modified MIT"**: needs written permission to use it as training, fine-tuning or **evaluation data or input to any automated pipeline for training or improving** an AI system, or to sell it as a hosted service | text; `--format json\|jsonl` (documented for runtime scan) | `react-doctor --no-telemetry {files}`; `react-doctor scan $URL --format json --no-telemetry` (opens system Chrome, records until Enter or 5 minutes; check for a non-interactive stop before relying on it in CI) | Sentry crash reports, traces and usage counters unless `--no-telemetry` | No | Keep. Ask whether the license clause bites; the factory reviews code, it does not train. Record that reading. |
| `lighthouse` | **13.5.0** | Apache-2.0 | JSON, HTML, CSV | `npx --no-install lighthouse $URL --output json --output-path $OUT/lh.json --only-categories=accessibility,best-practices,performance --chrome-flags="--headless=new" --no-enable-error-reporting --quiet` | Prompts for error reporting on first interactive run; pass `--no-enable-error-reporting` | No | **Optional.** Its a11y category is an axe subset, so it duplicates axe. Worth it only for performance. Needs Node ≥22.19 (local Node is 22.15.0). |
| `@lhci/cli` | 0.15.1 (2025-06-25, bundles lighthouse 12.6.1) | Apache-2.0 | `.lighthouseci/` | `lhci autorun --upload.target=filesystem` | Default target `lhci` needs a server; `temporary-public-storage` uploads reports to a **public** Google bucket | Server or none | **Skip.** Stale, older Lighthouse, upload footgun. |
| `pa11y` / `pa11y-ci` | 10.0.0 / 5.0.0 (4.1.1 ≥14d) | **LGPL-3.0** | JSON, CSV, CLI | `pa11y --runner axe --runner htmlcs --reporter json $URL` | Downloads puppeteer's Chrome | No | **Skip.** Duplicates axe; HTML_CodeSniffer targets WCAG 2.1; second browser stack (puppeteer). |
| APCA (`apca-w3`) | 0.1.9 (2022) | Custom "W3 License for compliant code only", patent pending; non-compliant implementations "deemed in breach" | number (Lc) | library | none | No | **Skip as a gate.** APCA was dropped from the WCAG 3 draft in July 2023, and the draft's contrast measure is "to be determined". WCAG 2.2 AA (4.5:1, 3:1) remains the referenced standard. Use APCA at most as advisory text in `design.md`. For color math, `colorjs.io` 0.7.1 (MIT) has both WCAG 2.1 and APCA without the license tangle. |
| react-scan | 0.5.7 | MIT | overlay | none | none | No | Already ruled out in `react.yaml`: no headless mode or exit code. |
| Hosted visual review (Argos, Chromatic, Percy) | `@argos-ci/playwright` 7.7.1 | MIT client | hosted | needs a token | uploads screenshots | **Yes** | **Skip.** Account needed, and screenshots leave the machine. |
| `@playwright/mcp` 0.0.83, `chrome-devtools-mcp` 1.10.1 | | Apache-2.0 | MCP | agent-driven | none known | No | For interactive agent inspection; the mechanical pass should be a script so it is repeatable. |

---

## 6. Recommendation: mechanical checks, in order

Conventions match `kit/security/tools.yaml`: `$REPO`, `$OUT` (run folder), `$NEUTRAL` (empty cwd), `$URL` (dev server), `$KIT`. Every result is a candidate. `design.md` declarations (brand hue, chosen font, allowed motion) become documented waivers, never inline ignores inside the repository.

**Code pass** (no browser; seconds):
1. `cd $NEUTRAL && node $KIT/vendor/impeccable/scripts/detect.mjs --json --no-config --no-inline-ignores $REPO/src > $OUT/imp-src.json`. Exit code 2 means findings; the JSON goes to the reviewer.
2. Factory gap rules. Use one `rg -n -P --json` invocation per row of Section 2: P1 (incl. hexes), P2 (v3 and v4 gradient text), P3, P4, P5, P6, P10, P11, P12, P13, P14, P16, P17. Use `-g '*.{tsx,jsx,html,mdx,css,scss,vue,svelte,astro}' -g '!**/*.{test,spec,stories}.*' -g '!**/__fixtures__/**'`. Write the results to `$OUT/slop-rg.json`. Keep the patterns in a `kit/ui/slop-patterns.yaml` so the code and screenshot passes share IDs.
3. Repository-level checks: P18 (motion without a reduced-motion guard) and P20 (template skeleton by component names).
4. The existing React pack lint (`eslint`, with jsx-a11y proposed) and `react-doctor --no-telemetry`.

**Rendered pass** (Playwright 1.63.0; per route and per breakpoint 390×844, 768×1024, 1280×800; light and dark):

5. Screenshots: `npx --no-install playwright screenshot --viewport-size "<w>, <h>" --full-page --color-scheme <light|dark> --wait-for-timeout 500 $URL/<route> $OUT/shots/<route>-<w>-<scheme>.png`. Or the same in one Playwright script with `reducedMotion: 'reduce'` for a stable capture.
6. In that script, per page:
   - `slop-metrics.js` → `$OUT/dom-metrics.json`
   - `AxeBuilder(...).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa'])` → `$OUT/axe-<route>-<w>.json`, with violations as candidates and `incomplete` color-contrast as review items
   - console errors and failed requests.
7. `impeccable detect --json --no-config --viewport <w>x<h> $URL/<route> > $OUT/imp-url-<w>.json`. This adds the layout, contrast-over-image, eyebrow, icon-tile and copy rules that need rendering.
8. State capture (P22): use `page.route` to return empty, 500 and slow responses for the route's data calls, then screenshot each state.
9. `react-doctor scan $URL --format json --no-telemetry` where the React pack applies, once a non-interactive stop is confirmed.

**Model pass** (only after 1-9): the Section 3 rubric, with `design.md` plus all JSON from `$OUT` plus the screenshots and crops. The model reports closed-question answers with evidence. It does not score.

**Pins to record** (proposed `kit/ui/tools.yaml`):
```yaml
playwright:        { version: 1.63.0, install: "npm i -D @playwright/test@1.63.0 && npx playwright install chromium" }
axe-playwright:    { version: 4.13.0, install: "npm i -D @axe-core/playwright@4.13.0" }   # axe-core ~4.13.0
impeccable:        { version: 4.1.0, source: pbakaus/impeccable, run: "scripts/detect.mjs --json --no-config --no-inline-ignores" }  # or pin by commit in packs.lock.yaml
jsx-a11y:          { version: 6.10.2, propose: "eslint flat config jsx-a11y/recommended (ESLint <=9)" }
better-tailwindcss: { version: 4.7.0, optional: "no-restricted-classes for bans declared in design.md" }
react-doctor:      { version: 0.9.14, note: "Modified MIT; --no-telemetry" }   # existing
lighthouse:        { version: 13.5.0, optional: "performance only; node >=22.19; --no-enable-error-reporting" }
```

## 7. Open questions and risks

- **Q1.** Vendor impeccable's detector (Apache-2.0, about 10k lines of JS) under `~/.software-factory/` at a commit, as packs are today, or depend on the npm package with its native binary? Vendoring the pure-JS `scripts/detector` avoids the binary fetch. That is what I ran.
- **Q2.** Should a default font or the purple hue be a finding at all when `design.md` is silent? The sources disagree (Section 1). Proposal: report "undecided", not "slop".
- **Q3.** react-doctor's license clause on "automated pipeline for ... improving any machine learning model or AI system": needs a recorded reading, or permission from Million.
- **R1.** Thresholds (centered ratio, round-shadow ratio, size steps) are uncalibrated. Build the gold set before they block anything.
- **R2.** Impeccable's rule set changes fast: 4.1 to 4.5 in a month, and a `single-font` rule was removed 2026-07-29 per a source comment. Pin it and re-run the fixture on every bump.
- **R3.** Untested here: Playwright and axe on this machine (packages not installed; I did not download them), impeccable URL mode (needs puppeteer), and the `impeccableDetect()` injection path.

## Artifacts in this folder

- `fixture/Hero.tsx`, `fixture/page.html`: planted-slop fixtures. `impeccable` found 5 tells in the TSX and 12 in the HTML. The `rg` patterns of Section 2 matched every planted P1-P8, P10-P12 tell; P13 (blob) was checked on a one-line sample. Note that table cells escape `|` as `\|` for Markdown: unescape before running.
- `fixture/slop-metrics.js`: the rendered-DOM metrics script, verified in Chromium.
