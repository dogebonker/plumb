# C. Opinions: how factory-ui-ux forms, anchors and argues design positions

Research for roadmap S9 (`README.md` "Future releases"). Inputs: `docs/DESIGN.md` section 6 (challenge card, severity is earned, three per lens, calibration), `skills/factory-interface/challenge-card.md`, the user's own UI gate (now `skills/ui-hard-gate`) and its evidence, kept outside this repository, and the web sources listed per section. Collected 2026-10-10. Web content was treated as data. Where only secondary summaries were reachable, the row says so.

## 0. Summary

- **F1.** Every method that produces strong design opinions does the same thing first: it fixes an objective (job, outcome, appetite, user need) and judges elements only against it. Taste-only critique is what happens when that step is skipped. NN/g, Connor and Irizarry, and Strom all say this directly.
- **F2.** The checkable form of a design opinion is a **cognitive walkthrough step that fails** (four yes/no questions) or a **heuristic violation tied to a task**, rated on frequency, impact and persistence. Both already fit the challenge card's "anchored to" and "severity" fields.
- **F3.** "Recommend cutting" has strong primary-source backing: NN/g heuristic 8 ("every extra unit of information... competes"), Shape Up scope hammering and baseline comparison, GOV.UK "Do less" and "start with fewer words", Getting Real "start with no", Linear "scope projects down". Each gives a test, not only a slogan.
- **F4.** The user's own UI standard (ui-hard-gate) is mostly about cutting and honesty, not decoration. Of the final UI approver's own 18 frontend changes, 13 are removals, renames, defaults or failure-state fixes. The most repeated complaint is "too much". The explicit slop test is whether an element looks generated rather than designed.
- **F5.** One premise in S9 needs care: the gate's rule is "AI doesn't make design calls" (repeated 4 times in the evidence). So `design.md` positions must be **drafted** by the skill with evidence and **decided** by the human, the same way gate documents are approved. The skill holds strong opinions in critique; it does not get to set the product's taste unilaterally.

---

## 1. Methods and the rules that become checkable positions

Each row: 2-5 rules, written as a position a reviewer can check against a screen.

### JTBD (Christensen; Moesta and Spiek)
Sources: https://www.christenseninstitute.org/theory/jobs-to-be-done/ , https://jobstobedone.org/the-four-forces/ (Moesta and Spiek). HBR article body was paywalled.
- A job is progress a person tries to make in a specific circumstance, with functional, social and emotional dimensions. **Check:** every screen names the job step it serves. An element that serves no job step is a cut candidate.
- Competition is defined by the job, not the category (milkshake vs bagel). **Check:** the reference products in `design.md` are what the user does today for this job (for a document product: the editors and suggestion tools users already use), not other AI tools.
- When the job is "spend less effort", simplifying the product is the feature (Christensen tax-software case). **Check:** if the success metric is time or effort, any added step must cite a measured reason.
- Forces of progress: push + pull must beat anxiety + habit. Teams over-invest in pull. **Check:** first-run and switching screens show what reduces anxiety (data safety, reversibility, what happens next), not more feature pull.

### Shape Up (Singer, Basecamp)
Sources: https://basecamp.com/shapeup/1.2-chapter-03 , https://basecamp.com/shapeup/1.3-chapter-04 , https://basecamp.com/shapeup/1.5-chapter-06 , https://basecamp.com/shapeup/3.5-chapter-14
- Appetite before design: "Appetites start with a number and end with a design." **Check:** a proposed alternative must fit the slice's appetite. If it does not, the finding says so and offers the smaller version.
- Narrow the problem: a request for complex permissions became a one-day warning. **Check:** before restyling, ask whether a smaller behavior solves the story.
- Breadboard (places, affordances, connections) before pixels. **Check:** a flow review starts from a breadboard of the screens. Extra places with no new affordance are intermediate screens to cut.
- Pitch ingredients include rabbit holes and **no-gos**. **Check:** `design.md` and each UI slice list no-gos.
- Decide when to stop: compare to the **baseline** (what users do today), not the ideal. Scope hammering asks "must-have? what happens if we don't? new problem or one they already live with? how common? how much does it matter?" **Check:** these five questions are the cut test (section 4).

### Refactoring UI (Wathan, Schoger)
Source: https://www.refactoringui.com/ (table of contents and preview only; book text not read).
- "Start with a feature, not a layout"; "Limit your choices". **Check:** no shell, hero or grid is proposed before the feature it holds.
- Hierarchy: "De-emphasize to emphasize"; "Labels are a last resort". **Check:** exactly one element per view reads first. Emphasis comes from muting siblings, not from adding weight.
- "Start with too much white space"; "Establish a spacing and sizing system". **Check:** spacing values come from the token scale. Matches ui-hard-gate H15 (density).
- "Don't rely on color alone"; "Use fewer borders"; "Don't overlook empty states". **Check:** color has a legend or a second cue. Every list has a designed empty state.

### Don't Make Me Think (Krug)
Sources (secondary; book not reachable): https://www.oreilly.com/library/view/dont-make-me/0789723107/ch06.html , https://uxplanet.org/dont-make-me-think-20-wise-thoughts-about-usability-from-steve-krug-876b563f1d63
- First law: a page is self-evident, or at least self-explanatory. **Check:** a first-time user can say what the screen is for and what to do next without reading body text (5-second test on the screenshot).
- Third law: "Get rid of half the words on each page, then get rid of half of what's left." Targets: happy talk and instructions. **Check:** count words on the primary path before and after. Instructions that explain the UI are a design defect (GOV.UK says the same).

### Laws of UX (Yablonski)
Source: https://lawsofux.com/
Most useful as named anchors for objections, not as positions on their own:
- Hick's law, choice overload: decision time grows with options. **Check:** count competing actions per view.
- Jakob's law: users expect your product to work like the ones they know. **Check:** deviations from the reference products' conventions need a stated reason.
- Tesler's law: complexity can only be moved. **Check:** every "cut" finding states where the complexity goes (to the system, to a default, to a later step) and who now carries it.
- Doherty threshold (about 400 ms): **Check:** any action slower than this shows progress (matches ui-hard-gate H5).
- Peak-end rule: **Check:** the end of the primary job (after accept, after publish) answers "what now?".

### NN/g heuristics and severity
Sources: https://www.nngroup.com/articles/ten-usability-heuristics/ , https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/ , https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/ , https://www.nngroup.com/articles/aesthetic-minimalist-design/ , https://www.nngroup.com/articles/progressive-disclosure/ , https://www.nngroup.com/articles/match-system-real-world/
- H1 visibility of system status, H2 "speak the users' language", H4 consistency, H5 error prevention, H8 aesthetic and minimalist design, H9 errors in plain language with a precise cause. These six cover almost all of the recorded complaints behind ui-hard-gate.
- H8 is signal-to-noise, not flat styling: "Every extra unit of information in an interface competes with the relevant units." Removing too much is also a failure. **Check:** each visible element supports a task, and nothing the task needs is hidden.
- Progressive disclosure: primary level holds what users frequently need; **no more than two levels**; if you need three, simplify first. **Check:** count disclosure depth.
- Heuristic evaluation: 3-5 independent evaluators; each issue logged against a named heuristic with how it fails the user's task; "a violation is not automatically a problem", context decides.
- Severity = frequency + impact + persistence, with market impact rated separately. Scale 0-4 (4 = must fix before release). Rate after finding, not during. Single-rater severity is "too unreliable"; average three.

### Kathy Sierra, Badass
Source: http://businessofsoftware.org/2013/03/kathy-sierra-on-designing-for-badass/ (talk write-up; book text not read).
- Users want to be better at the **context**, not the tool. Ideal review test: the user talks about what they can now do, not about the product. **Check:** the success metric in `design.md` is a user capability, and the UI's most prominent content is the user's work, not product chrome.
- Cognitive leaks: confusion, choices and anxiety drain a limited pool. Remedy: simplicity, smart defaults, "put it in the world, not in the head". **Check:** every required choice on the primary path has a stated reason it cannot be a default (matches ui-hard-gate H19, defaults on the common path).
- Show excellent examples and visible progress. **Check:** first-run shows a good example of the output, not an empty canvas.

### The Mom Test (Fitzpatrick)
Sources (secondary; book not read): https://www.shortform.com/blog/what-is-the-mom-test/ , https://www.ybrikman.com/blog/2023/03/29/the-mom-test/
- Talk about their life, not your idea; ask about specific past events, not opinions about the future; listen more. For copy: **user words come from transcripts of real past events, never from the team's paraphrase**. The gate's evidence rule is the same: never present a paraphrase as something a user said.
- **Check:** each glossary term in `design.md` cites where users said it (interview, ticket, support email) or is marked "team term, unverified".

### GOV.UK Service Standard, design principles, interface copy
Sources: https://www.gov.uk/service-manual/service-standard , https://www.gov.uk/service-manual/service-standard/point-2-solve-a-whole-problem , https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use , https://www.gov.uk/guidance/government-design-principles , https://www.gov.uk/service-manual/design/writing-for-user-interfaces , https://design-system.service.gov.uk/patterns/question-pages/
- "Start with user needs", "Do less" ("the irreducible core"), "Do the hard work to make it simple", "Be consistent, not uniform".
- One thing per page as the starting point; group only when research supports it. **Check:** a form or step that asks for several unrelated things needs a reason.
- Interface copy: use the users' words in headings, labels, links and errors; front-load; "Start with fewer words. Add help text only when user research shows it's needed"; "If you need to explain how the interface works, fix the interface instead"; "Aim to be boring."
- Solve a whole problem: scope by how users think, not by team boundaries. **Check:** a screen's grouping follows the user's job, not the API or data model (ui-hard-gate H10: the user's words, not the system's concepts).

### Linear Method
Sources: https://linear.app/method/introduction , https://linear.app/method/scope-projects
- Purpose-built over unlimited flexibility; "Simple first, then powerful"; "Aim for clarity", don't invent terms ("Projects should be called projects"); "Say no to busy work".
- Scope down: "Shorter projects force you to prioritize the most important feature set." **Check:** configurability, settings and options need a named user who asked.

### Teresa Torres, opportunity solution trees
Sources: https://www.producttalk.org/opportunity-solution-trees/ , https://www.producttalk.org/2021/08/product-outcomes/
- Root is a **product outcome** (a customer behavior the team can move), not a business metric or a feature traction metric.
- Opportunities are customer needs from story-based interviews. A solution is something with only one way to satisfy it. **Check:** a feature with no opportunity above it in the tree is unanchored.
- Compare more than one solution per opportunity; test the riskiest assumption. **Check:** a block or fix finding offers at least one alternative, and the steelman counts as the other.

### Getting Real (Basecamp)
Source: chapter list at https://basecamp.com/books/getting-real/ ; chapter text only via secondary quotes.
- "Start with no": the default answer to a feature is "not now"; repeated demand earns a look. Every feature carries ongoing cost and is hard to remove. **Check:** a feature with one requester and no repeated evidence is a cut-or-defer candidate.

---

## 2. Critique structures that avoid taste-only feedback

| Structure | What it forces | Source |
| --- | --- | --- |
| Connor and Irizarry's four questions | What is the objective? Which elements relate to it? Are they effective? Why or why not? | *Discussing Design* (O'Reilly); summarized at https://www.zeitspace.com/blog/how-to-do-design-critique-a-tool-for-designers-to-improve-their-work and https://mattstromawn.com/writing/critique-vs-review |
| NN/g critique rules | Agree the user needs and problem first; rephrase taste ("I would have done it differently") into a question about the task; no directives | https://www.nngroup.com/articles/design-critiques/ |
| Critique vs review (Strom) | Critique drives iteration. Review commits, by consent not consensus. An objection asks "is this safe to try?". Say what works as plainly as what doesn't. Aim for good enough | https://mattstromawn.com/writing/critique-vs-review |
| Heuristic evaluation | Each issue is tied to a named heuristic and a task; independent evaluators; consolidate after | https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/ |
| Cognitive walkthrough | Per step: will users try to reach this result? notice the action? link the action to the result? see progress? Any "no" fails the step | https://www.nngroup.com/articles/cognitive-walkthroughs/ |
| Severity rating | Frequency, impact, persistence (market impact separate), 0-4, rated after finding, averaged over raters | https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/ |
| Lean UX hypothesis (Gothelf) | "We believe [X]. We will know we're [right/wrong] when we see [feedback]" | https://www.goodreads.com/quotes/7498863 (book excerpt) |

**How to make an opinion falsifiable and anchored.** Combine three of these:
1. **Anchor**: the objective comes from the product, not from the reviewer. It is a `design.md` position ID, a product-gate field (user, job, success metric) or a constraint ID. This is the challenge card's "anchored to" field.
2. **Mechanism**: name the heuristic or law and the walkthrough step that fails ("step 3: user will not notice the action, because the primary button is one of two equal-weight buttons").
3. **Prediction plus disconfirming check**: what observable thing happens if the objection is right, and what would show it is wrong. Examples: "a first-time user clicks Reject before reading the diff (check: 5-second test, or the session recording)"; "the primary path takes 4 screens where the baseline takes 2 (check: breadboard count)". If no check can be named, the finding is taste and caps at note.

This is the same rule the factory already uses for interface design, applied to screens.

---

## 3. The user's own standard (ui-hard-gate)

Source: the user's own UI gate, now the generic `skills/ui-hard-gate`, built from recorded review feedback by the product's final UI approver (collected 2026-10-08). The evidence stays outside this repository; counts come from it, and no quote is reproduced here.

| ID | Recurring rule | Count in evidence |
| --- | --- | --- |
| M1 | **Show less. Headline first, detail on demand.** | 17 |
| M2 | **Cut what has no action or explanation.** Headers with no call to action, duplicate status boxes, statuses nobody defined, unused features | 12 |
| M3 | **Slop test: does it look generated?** | 5 |
| M4 | **AI doesn't make design calls.** Build from a reference: a design frame, wireframe, screenshot or conversation | 4 |
| M5 | **One way to do one thing; one primary action.** | about 5 |
| M6 | **Honest state.** Running work is visible and survives refresh; loading, empty, failed, no-change and done look different; "Completed" only when complete; counts match the screen | 25 |
| M7 | **Failures name the cause and offer a retry in place, or disappear.** | 13 |
| M8 | **Fail closed.** Hide or disable what the server would refuse, and say why | 5 |
| M9 | **The user's words, never the machinery or the team's codename.** | 15 |
| M10 | **Labels say what they do and match behavior.** | about 6 |
| M11 | **Short copy, one fact once, no footer info.** | 6 |
| M12 | **Every screen answers "what do I do now?"** | 6 |
| M13 | **Fewer steps; defaults on the common path.** | 9 |
| M14 | **Flat navigation; the most-used view opens first; content gets the width.** | 8 |
| M15 | **Match named in-app good examples; consistency over novelty.** | 10 |
| M16 | **Density: generous padding, normal-size controls, less per card.** | 7 |
| M17 | **Taste with a point of view, not defaults.** | 2 |
| M18 | **Information nobody acts on is a failure mode.** | 1, echoes M2 and M12 |
| M19 | **Customer reality beats the roadmap; propose the smaller thing; say what you are not building.** | 3 |
| M20 | **Review format: ranked, numbered, with screenshots; pragmatic follow-ups.** | 10 |
| M21 | **Be able to explain every choice.** | 2 |

Generalizable vs product-specific: M1-M14 and M17-M21 are product-agnostic and line up almost one to one with NN/g H1, H2, H4, H5, H8, H9 and with Shape Up's scope hammering. M15, M16 and the product's color meanings are product-specific and belong in that product's `design.md`, not in the skill.

Two calibration points from the evidence:
- The approver accepts imperfect but clear UI. The protocol must separate "flow not understandable" (block) from polish (note or follow-up): an understandable flow is mandatory, pure polish can be a follow-up.
- Cutting has overshot once: a whole section was removed and then restored the same day. Cut findings must say exactly what goes and what stays.

---

## 4. Recommendation: the factory-ui-ux critique protocol

### 4.1 Where opinions come from (order matters)

1. **Read the anchors.** `design.md` positions (section 4.6), the product gate's user, problem, job and success metric, and the constraints registry. No anchors means the skill stops and drafts `design.md` first.
2. **Mechanical pass first.** The slop catalog and the honest-state checklist (M6-M8) run from code and screenshots. These are facts, not opinions, and they never cost a critique slot.
3. **Walk the primary job on rendered screens.** A breadboard of the screens it touches, then the cognitive walkthrough's four questions per step at each breakpoint. Failed steps are the strongest evidence the skill can have without users.
4. **Element audit.** For each visible element, apply the cut test (4.3). This is where "recommend cutting" comes from.
5. **Heuristic sweep.** Only for issues steps 3-4 did not explain, each tagged with its heuristic number and the task it hurts.
6. **Form the opinion as a challenge card** (4.2). Anything without an anchor and a check caps at note.

### 4.2 Finding format (challenge card for UI)

Extends the existing card. Field changes are marked **new**.

| Field | UI meaning |
| --- | --- |
| Lens / rule | e.g. `NN/g H8`, `walkthrough q2`, `Shape Up baseline`, `design.md D3` |
| Where | screen + element + screenshot path (breakpoint) |
| Steelman | Why the current design is reasonable: what job it serves, who asked for it, what it costs to remove |
| Objection | What goes wrong, as the failed walkthrough step or the task it hurts |
| Anchored to | `design.md` position ID, product-gate metric, or constraint ID. "none" means taste |
| **Prediction / check** (new) | The observable outcome if the objection is right, and how to check it (walkthrough, step count, word count, 5-second test, analytics, a user quote). No check means note |
| Alternative | Concrete: a sketch, a breadboard diff, exact copy, or "delete X, keep Y" |
| Cost of alternative | What gets worse, and where the complexity moves (Tesler). Who loses what (habit, anxiety) |
| Severity | block / fix / note (4.4) |
| Response | accept / modify / overrule, written by the human |

Presentation follows ui-hard-gate's format on top of the card: `(P0|P1|P2) <title>`, what is wrong, screenshot, fix. P0 = block, P1 = fix, P2 = note.

### 4.3 When to recommend cutting

An element or feature is a cut candidate when it fails any of these. The first three come from the ui-hard-gate evidence, the rest from the sources in section 1.

- **C1 Action or explanation.** It neither lets the user act nor explains something they need for the job (M2, NN/g H8).
- **C2 Duplicate.** A second path, status or display of the same thing (M5, ui-hard-gate H3).
- **C3 Undefined.** A status, badge or label whose meaning the product never defined for users (M2, M10).
- **C4 No job.** It maps to no job step or opportunity in `design.md` (JTBD, OST).
- **C5 No demand.** Speculative configurability or a single unrepeated request ("start with no", Linear "purpose-built").
- **C6 Depth.** It sits at a third disclosure level, or behind nesting (NN/g progressive disclosure).
- **C7 Intermediate place.** A screen or modal with no new affordance in the breadboard (Shape Up, M13).

Scope-hammer questions decide whether to cut now: must-have for the job? what happens if we don't? is it a new problem or one users already live with? how common? how much does it matter?

Prefer the cheapest move that solves the objection, in this order: **delete > merge into an existing element > default it > collapse it (second level) > restyle**. A cut finding must state exactly what stays (the overshoot in section 3) and where the complexity goes.

### 4.4 Severity and ranking

Severity is earned, as in DESIGN.md section 6.

| Severity | Rule |
| --- | --- |
| **block** (P0) | Anchored, and the primary job fails a walkthrough step, or the screen lies about state (M6-M8), or it violates a `design.md` refusal. Maps to NN/g 3-4 |
| **fix** (P1) | Anchored, and it costs time, errors or trust on the primary path, with a named check. Maps to NN/g 2-3 |
| **note** (P2) | Unanchored, cosmetic, off the primary path, or no check can be named. Maps to NN/g 1 |

Rank within a severity by frequency x impact x persistence (NN/g), then by how close the element is to the primary action, then by the lowest cost of alternative. Because a single rater's severity is unreliable (NN/g), the skill should run the walkthrough and the element audit as two independent fresh-context reviewers and keep the higher-confidence rating when they agree. This matches the factory's existing fresh-context challenge panel.

### 4.5 How many findings, and disagreement

- **At most three block-or-fix findings per screen and seven per review**, plus at most one cut proposal per screen even if it is a note. DESIGN.md already caps lenses at three each. The approver's reviews run three to seven numbered items. More findings than that becomes a findings dump (M12, M18).
- **Always say what works**, one line per screen (Strom). It shows the steelman was real, and it tells the builder what not to touch.
- **Zero findings is allowed** if the reviewer names the strongest objection it dropped (existing rule).
- **Disagreement.** The human answers accept, modify or overrule in one line. An overrule is recorded and never re-raised for the same element (DESIGN.md section 11, Pond). Three overrules of the same rule demote it to note (existing calibration). If the human overrules a `design.md` position itself, the skill proposes amending `design.md` instead of repeating the objection. Lens conflicts (for example Jakob's law against a product refusal) go to the human, and the call becomes an ADR.
- **Critique vs review.** In the product and interface gates the skill critiques (iteration). On slice review it reviews (consent): it only raises objections that make the change unsafe to ship, and everything else becomes a follow-up, matching the approver's habit of accepting an understandable flow and leaving polish to follow-ups.

### 4.6 What every design.md must force a product to decide

Eight positions. Each must say what it rules out, cite its source (user quote, metric, PM rule, or "book prior"), and be approved by the human (M4: the skill drafts, the human decides).

| ID | Position the product must decide | What it rules out | Primary basis |
| --- | --- | --- | --- |
| D1 | **Who the user is, the job, and the one success metric** (a product outcome, not a business metric) | Features and screens that serve no job step; designing for "users" in general | JTBD, Torres, GOV.UK point 1 |
| D2 | **Vocabulary: the words users say, and the words the UI never says** (each term cites where users said it) | Internal codenames, machinery words, invented terms, team paraphrase presented as user language | Mom Test, NN/g H2, GOV.UK copy, M9 |
| D3 | **The primary action of each core screen** (one per screen) and the button hierarchy | Two equal-weight primary actions, duplicate paths to one result | M5, Refactoring UI hierarchy, Hick's law |
| D4 | **Density and disclosure**: what is visible by default, what is one click away, maximum two levels | "Show everything" defaults, and hiding what the job needs | NN/g progressive disclosure, H8, M1 |
| D5 | **Refusals**: what this product refuses to look like (named anti-references plus which slop-catalog entries apply) and its reference products for conventions | Generic AI-template looks, novelty that breaks the conventions users bring | Jakob's law, M3, M17 |
| D6 | **State honesty contract**: the states each surface must show distinctly (running, empty, failed, no change, done) and the error rule (cause plus in-place recovery) | Generic errors, false "completed", silent work, controls enabled when the server refuses | NN/g H1, H9, M6-M8 |
| D7 | **Admission rule**: what an element or feature must show to earn a place, and the default answer to new ones ("not now" unless repeated demand) | Speculative settings, unused sections, statuses nobody defined | Getting Real, Linear, Shape Up, M2 |
| D8 | **Voice and tone**: one line, with an example of in and out (for an enterprise product: neutral and factual) | Casual phrasing, happy talk, instructions that explain the UI | GOV.UK "aim to be boring", Krug, M11, ui-hard-gate H12 |

Left out on purpose: brand palette, type scale and component library. They are decided by the design system or the existing tokens, not by product positions. M15 says "match the existing pattern" and that is a mechanical check against tokens.

---

## 5. Risks

- **R1.** Positions drafted from a thin product gate are hypotheses. Each must carry its source tag, and book rules stay priors that project history overrides (DESIGN.md section 11).
- **R2.** Walkthroughs by a model are not user tests. Findings should say "predicted", and the check field should name a real check the human can run.
- **R3.** Several method summaries here are secondary (Krug, Mom Test, Moesta's book, Getting Real, Connor and Irizarry). The rules used are consistent across sources, but exact quotes from those books are not verified.
- **R4.** The ui-hard-gate evidence has gaps: design-tool comments, most screenshots and spoken feedback are not captured, and some written text was drafted by agents and approved by the approver rather than written by them.
