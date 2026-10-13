# Support-dashboard benchmark — matched r4 run

The later [15-minute continuation and independent code review](dashboard-final-comparison.md)
found 0 critical issues in finished Factory + Context versus 1 in Superpowers; both
require changes. That continuation is separate from this historical matched run.

All six screenshots are copied into this workspace: [open the comparison gallery](dashboard-images/index.html), with mobile and desktop views for each arm.

Follow-up inspection found a two-tab data-loss case in Superpowers that both Factory
arms preserve. See [generated folder structures and the additional check](dashboard-structure.md).
The original 15/15 score does not cover that scenario or polished visual design.

**Superpowers was the only arm to complete the original 30-minute workflow and deliver an independently verified 15/15 dashboard.** Factory and Factory with Context Mode timed out with captured snapshots scoring 6/15 and 11/15. Later recovery established that the Context snapshot was a temporary **RED checkout**, while its already committed GREEN code passes 15/15. The original snapshot scores therefore cannot rank the best available implementations. No global workflow winner or reduced human minutes is established.

This review covers only `/private/tmp/factory-comparison-dashboard-20261012-r4`. The completed run compares Factory, Superpowers, and Factory with Context Mode on the same complete support-ticket dashboard task. Earlier dashboard attempts, including r2 and r3, are diagnostics and are excluded from the comparison.

The target decision is whether improved delivered product quality and substantially less follow-up justify approximately 15% more tokens. Scripted recommendations are a follow-up proxy; this run does not measure human minutes, review difficulty, or the suitability of automatically accepted decisions.

## Matched setup

- Claude Code `2.1.296`, model `claude-sonnet-5-5`, high effort, one repeat per arm.
- Arm order: Factory, Superpowers, Factory with Context Mode.
- Each arm receives a fresh copy of the same retained case, SHA-256 `50a92340472251cad6da7ef820df4e8016c879fe01e6555310a8917641157e7f`.
- Runner SHA-256: `58506c34b796327aea332a04678847d421e5888480750b89258c7e224e8c5816`.
- Superpowers `v7.0.0`, commit `bb92a77741419a4ab5f06e711a283343f1ada0c3`; Context Mode `1.0.169`, commit `98cd9ab0ed417b769dab873f427c5684f6d46d35`.
- Equal per-arm limits: 1,800 seconds, USD 5 model budget, 12 simulated question answers, and one product-repair round. A blocked browser invocation can receive one separately recorded environmental reminder containing the exact permitted check command; it does not weaken permissions.
- Product code uses vanilla HTML/CSS/JavaScript and browser storage. Trusted browser checks run after model execution against a separate product snapshot; generated agent tests do not determine the acceptance score.

The retained [provenance](/private/tmp/factory-comparison-dashboard-20261012-r4/provenance.json) records source and snapshot hashes and adaptations. Factory uses a copied skill/kit snapshot with explicit synthetic-operator handling. Context Mode uses the recorded isolated adaptation, rather than stock startup against personal Claude configuration. Native child-agent write and Bash execution were restored and smoke-tested before this run. The operator prompt directs all scratch work into the trial's `.tmp` directory. Root terminal protocol results and forwarded child results are distinguished by the controller.

Offline regrading used SHA-256 `9db284a2c9ae1da78b2bd6a19a3b2056e94d7a7eace64f15cf758f945dba022a`. That is a reporting/inspection version, distinct from the active run's frozen `58506c...` runner. It did not launch more model calls or replace the retained case inputs. Independent browser reruns used that same frozen r4 case and left the recorded trials unchanged.

## Reading the evidence

The fifteen trusted checks cover seeded records, combined filters and search, count/reset/empty state, readable details, cancel and persisted edits, trimmed creation with accessible errors, creation persistence and identity, Escape/focus restoration, keyboard modal behavior, visible focus, mobile control bounds, screenshots, and external-request restrictions. Passing these checks does not establish a complete accessibility audit or superior visual design.

Initial quality is the first completed product's trusted grade. Final quality includes at most one product-repair round. Snapshot quality for an interrupted arm is a separate observation and cannot establish delivery, workflow completion, or time to acceptance. Environmental command reminders are reported separately from product repairs and simulated approval questions.

Token totals include input, output, cache reads, cache creation, and subagents from the last cumulative `result.modelUsage`. Cumulative resume totals are not added together. USD values are CLI-reported list-price estimates, rather than an invoice or measured subscription charge. If a call is interrupted, exact final usage is unknown; the last observed cumulative amount is a lower bound. Technical measurement validity, substantive workflow adherence, and actual human follow-up are assessed separately.

## Results

All three arms reached terminal state. [Official report](/private/tmp/factory-comparison-dashboard-20261012-r4/report.md), [summary](/private/tmp/factory-comparison-dashboard-20261012-r4/summary.json).

| Arm | Delivered initial / final | Independently checked snapshot | Total seconds | Tokens, including cache/subagents | Estimated USD | Post-delivery repairs | Environment reminders | Simulated questions |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Factory | Not delivered / not delivered | 6/15 | 1,800.2, timeout | ≥8,737,317 | ≥3.1201 | 0 | 1 | 8 |
| Superpowers | 15/15 / 15/15 | 15/15 | 1,550.4, accepted | 8,272,040 | 3.4746 | 0 | 1 | 2 |
| Factory + Context Mode | Not delivered / not delivered | 11/15 | 1,800.8, timeout | ≥9,238,053 | ≥3.3178 | 0 | 1 | 8 |

Snapshot grades cannot be substituted for a first delivered grade. Both timeout arms have unknown exact final usage and no measured time to acceptance. Their zero post-delivery repairs reflect the absence of a completed first delivery, not successful first-pass validation. All three manual human-follow-up fields remain `null`.

**Capture correction:** the Context row remains the historical score of the workspace captured at timeout. The step agent had checked out RED commit `2acf68a` to prove failing tests after its native executor had already committed GREEN `03c6d91`. The captured workspace and exported source were consequently RED, not the best committed implementation. Replaying three recorded source actions into a fresh Git checkpoint recovered that original GREEN before any new model implementation; it passes 17/17 store tests and the frozen 15/15 browser suite. This changes the interpretation, not the recorded r4 score, timeout, or usage. See [restoration provenance](/private/tmp/factory-dashboard-extension-20261013/restoration.json), [recorded recovery actions](/private/tmp/factory-dashboard-extension-20261013/recovery-actions.json), and [recovered GREEN quality](/private/tmp/factory-dashboard-extension-20261013/recovered-green-quality.json).

### Factory: interrupted workflow and partial product

Factory timed out after **1,800.2 seconds**, without a first or final delivered-product grade. The recorded totals are **8 simulated questions**, **1 environmental browser-command reminder**, and **0 post-delivery product-repair rounds**. Zero repairs does not establish first-pass correctness: there was no completed delivery to grade.

An independent browser run against the unchanged, retained r4 case graded its saved workspace **6/15**, with 9 failures, no runtime errors, and no skips. This is **snapshot quality only**. [Independent check results](/private/tmp/dashboard-r4-independent-3a2mej0f/factory-snapshot.json), [desktop screenshot](/private/tmp/dashboard-r4-independent-3a2mej0f/factory-snapshot/desktop.png), [mobile screenshot](/private/tmp/dashboard-r4-independent-3a2mej0f/factory-snapshot/mobile.png), [recorded trial](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-factory-1/result.json).

The six passing groups establish seeded list metadata, case-insensitive search, combined filtering, count/reset, empty-state behavior, and local-only assets with screenshots. The nine failing groups have two main causes, rather than nine independent defects:

- Creation is not implemented: `New ticket` has no listener or creation dialog. Four groups depending on that surface fail.
- Details contain wrapped selects whose required exact accessible names `Status` and `Priority` are missing. Five detail/edit/keyboard groups consequently fail to identify those controls. The source contains update and persistence logic; these failures do not independently prove five separate data-loss or editing defects.

I viewed both screenshots. The result is a readable plain list with bordered tickets, adequate space, and vertically stacked mobile filters. `styles.css` is byte-identical to the starter; the design document did not become a delivered visual redesign. The visible `New ticket` control is inactive. This is not a complete dashboard, even though the implemented list and filters work.

All four approved gate-document hashes match their files, and native child agents produced actual red/green commits. Only slice 01 has a completed milestone review; slice 02 is green, slice 03 remains building, and slices 04/05 are pending. `reconciled` is false. The copied workflow therefore did not reach its own completion criteria.

The timeout also has an observed orchestration failure. In [turn 09](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-factory-1/turn-09.jsonl), the slice-03 step agent returned a hand-back saying its executor was still running and it was waiting for its report. The main session then issued two loops polling status up to 60 times at eight-second intervals. The executor had committed red/green code, but the status owner had already handed back without proving or recording green. This is a premature-handback/polling failure in the observed workflow path; the evidence does not establish equivalent completion or a confound-free full-workflow comparison.

No tool results reported denied Read/Write/Bash permission in this arm. Its environmental reminder followed attempts to launch Chromium directly or invoke the checker with appended pipes/commands; those attempts failed under the sandbox. The recorded reminder restated the exact permitted argument-free checker, which subsequently ran. That resolved capability friction must remain in the reported intervention count.

The last completed root result reports **at least 8,737,317 tokens** and **at least USD 3.1201**. The classes are input 264, output 109,017, cache reads 8,226,178, and cache creation 401,858, including subagents. The interrupted final invocation adds unknown usage; these lower bounds are not the final exact cost or total.

### Superpowers: accepted product, qualified workflow evidence

Superpowers delivered **15/15 on its first trusted submission**, retained **15/15 as its final grade**, and required **0 post-delivery repair rounds**. An independent run of the same frozen r4 grader against its saved workspace also passed all fifteen checks with no failures, runtime errors, or skips. [Recorded trial](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-superpowers-1/result.json), [independent verification](/private/tmp/dashboard-r4-independent-3a2mej0f/superpowers.json).

Time to the first complete protocol result was **1,548.1 seconds**; total time to trusted acceptance was **1,550.4 seconds**. It used **8,272,040 cumulative tokens** and **USD 3.4746**, with input 296, output 131,760, cache reads 7,649,574, and cache creation 490,410. The record has **2 simulated approval questions** and **1 environmental browser-command reminder**. All recorded model usage is the pinned Sonnet model, and plugin snapshots remain unchanged.

The source implements the complete tested flows: literal title/customer search, combined filters, persisted edits, trimmed creation with associated validation messages, unique IDs, cancellation, and explicit modal focus handling. User-controlled text is placed through `textContent`. The saved product has four source files: HTML, CSS, the unchanged seed data, and a 278-line application script; it adds no dependency or backend.

I viewed the [desktop](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-superpowers-1/grade-0/desktop.png) and [mobile](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-superpowers-1/grade-0/mobile.png) screenshots. Compared with Factory's partial starter presentation, titles are more prominent, customers have a quieter secondary style, and status/priority badges provide additional scanning cues while retaining text. The mobile layout keeps the content readable and moves badges below each ticket. It is a modest functional design improvement, not evidence of exceptional visual design or a measured aesthetic score. Desktop card widths vary with badge width, and both filter actions share similar visual emphasis.

The trajectory shows four native implementation tasks, independent task reviews, scoped fixes and re-reviews for tasks 3 and 4, and a final whole-branch review. Those internal fix rounds are ordinary pre-delivery development; they must not be mistaken for two failed trusted submissions. It invoked `using-superpowers`, `brainstorming`, `writing-plans`, `subagent-driven-development`, and `finishing-a-development-branch`, then completed the recorded local merge and verification. Provisional waiting messages did not terminate the root turn. No denied Read/Write/Bash tool results were recorded. The final branch cleanup reported a nonblocking `.git/config` lock warning; the trajectory reports the branch deleted and the final checks passing.

Strict full-workflow adherence remains unconfirmed. The root explicitly treated the supplied task as an approved specification before receiving a controller design approval; no separate specification file is retained. It also disclosed that the original full Task-1 RED result was not captured after browser capability friction: a corrected search test was subsequently demonstrated RED/GREEN, while the remaining original tests were verified GREEN. The approved plan and implemented product are real evidence, but they do not fill those procedural gaps. Consequently technical `measurement_valid` is true, while strict `comparative_valid` remains false and human follow-up stays unmeasured.

### Factory with Context Mode: captured RED, recovered committed GREEN

This arm timed out after **1,800.8 seconds**, with no initial/final delivered-product grade, **8 simulated questions**, **1 environmental reminder**, and **0 post-delivery repair rounds**. Its last completed root result establishes lower bounds of **9,238,053 tokens** and **USD 3.3178**: input 252, output 113,846, cache reads 8,692,830, and cache creation 431,125. The interrupted final invocation adds unknown usage. [Recorded trial](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-factory-context-1/result.json).

Independent grading reproduced the official **11/15 captured-snapshot score**, with four failures, no runtime errors, and no skips. All four failed groups stop waiting for a `New ticket` dialog: required-field validation, valid creation/persistence, Escape on creation, and mobile dialog/control bounds. That captured RED source contains neither creation markup nor a creation handler. These are correlated consequences of the temporary RED state, not evidence that ticket creation had never been built. The mobile check did not reach its creation-dialog sizing assertions, so that failure is not evidence of actual horizontal overflow. [Independent checks of the captured RED workspace](/private/tmp/dashboard-r4-independent-3a2mej0f/factory-context-snapshot.json).

I viewed the independent [desktop](/private/tmp/dashboard-r4-independent-3a2mej0f/factory-context-snapshot/desktop.png) and [mobile](/private/tmp/dashboard-r4-independent-3a2mej0f/factory-context-snapshot/mobile.png) screenshots. They show the same readable, starter-like bordered list and stacked filters as Factory, rather than a redesigned completed product. The details save button has a blue primary style in the source; the main list still lacks Superpowers' title/customer hierarchy and badges. A viewer briefly displayed the official mobile image as a white strip. The official and independent PNGs are byte-identical: 360×1630, 92,571 bytes, SHA-256 `1f7e7b4fe963ba54bb139ea6bc821d19083399f98dc6835d3c44721f81b0aca4`. The independently viewed image is a full list, so the strip is a display issue, not a demonstrated product defect.

The captured RED source also duplicates the details-dialog setup inside Reset and at top level, registering extra listeners on reset. The recorded GREEN actions remove this nested duplicate and implement creation. That static observation must not be attributed to the latest committed implementation.

The original Git directory was not retained, so recovery reconstructed checkpoints rather than pretending the original objects were still available: original RED/GREEN `2acf68a`/`03c6d91` correspond to reconstructed `7f0211614c6f45727e5f41e87cbd05bf89bf83ca`/`4b66b4a52158905395ccf0f73888a22a90332448`. The actions SHA is `ee3c631b3497fb431303f6092a445a2ba1759ef8cf66ffa110156b5356d7367c`. Main verified the recovered GREEN with **17/17 store tests and 15/15 frozen browser checks before any new model implementation**; [RED unit evidence](/private/tmp/factory-dashboard-extension-20261013/recovered-red-unit.txt), [GREEN unit evidence](/private/tmp/factory-dashboard-extension-20261013/recovered-green-unit.txt), and [browser evidence](/private/tmp/factory-dashboard-extension-20261013/recovered-green-quality.json) are retained. The earlier screenshot/source observations describe the captured RED version only; they do not score the recovered GREEN's visual quality.

Native step/executor agents did implement code, and all four approved gate-document hashes match. The first slice required a rewind/rebuild after a cross-realm bug in the agent's own RED test. At timeout, the recorded state still marks slices 01 and 02 green, slice 03 building and slice 04 pending; no milestone review file exists, and `reconciled` is false. Those workflow records remain unfinished even though the slice-03 executor had committed functional GREEN code. The timeout occurred during the step agent's detached RED proof checkout.

The realized workflow also differs from the initially prescribed schedule. In question 8, the root estimated roughly USD 3.3 spent and recommended building the remaining slices before combined reviews, skipping optional lenses, and using a shortened reconcile. The controller echoed that recommendation under the shared scripted-answer policy. In [turn 09](/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-factory-context-1/turn-09.jsonl), the root then dispatched **one step agent for two consecutive slices, 03 and 04**, rather than a fresh step agent per slice; only the slice-03 executor appears before timeout. That broader implementation grouping must not be hidden behind the approved review-schedule change. The shortened reviews/reconcile were proposed, not completed.

No denied Read/Write/Bash tool results were recorded, but there was **one denied `Monitor` call** while waiting for a browser-check output file. There were also file/commit polling waits. Those operational issues and the budget-driven scheduling changes preclude describing the arm as a strict, confound-free full Factory execution.

Context Mode was enabled and its hooks were active: the `context_window_protection` marker occurs repeatedly in retained trajectories (132 textual occurrences, not an execution-count metric). However, there are **zero explicit `ctx_` tool calls** in the recorded model trajectory. It is inaccurate to call the entire plugin unused, and equally unsupported to claim demonstrated execute/index/search use or isolated compression savings. The arm changes hooks, registered tools, agent decisions, and review scheduling together; one observation cannot separate their effects.

## Switching decision and limits

For the original **30-minute completed-delivery criterion**, Superpowers has the strongest evidence: it was the only accepted arm and passed the same fifteen trusted checks without a post-delivery repair. The base Factory snapshot is still incomplete. The Context arm did not finish its workflow, but its recovered, previously committed GREEN implementation also passes 15/15; claims that it had not built creation or that its latest implementation retained the Reset duplication are withdrawn. Its captured RED cannot support a best-code quality ranking against Superpowers. The modest Superpowers visual improvement was observed against the captured versions; recovered GREEN requires its own source/visual review.

There is **no measured evidence here that establishes a 15% token premium buys far less human follow-up**. Factory's known lower-bound token count is at least **5.6% above** the completed Superpowers run; the Context arm is at least **11.7% above**, with unknown additional usage. Those original-run values remain historical and do not include recovery or an extension. Superpowers has two scripted approval questions versus eight in each Factory arm, but those counts do not establish human minutes or actual corrective work. The Context capture failure required recovery work and must be distinguished from implementing a missing feature. Zero post-delivery repairs for an undelivered workflow cannot prove reduced follow-up.

Do **not** claim Superpowers was cheaper in dollars: its complete USD estimate is 3.4746, while the two interrupted estimates are only lower bounds of 3.1201 and 3.3178. Nor can this single, sequential, adapted run establish a global winner, statistically stable performance, strict full-workflow equivalence, or Context Mode savings. Order/cache effects were not balanced across repeats; the original model-specific role choices were overridden by the common inherited-model policy; workflow gaps and operational waits remain explicit. Passing fifteen checks is a bounded product-quality result, not a production-readiness or full accessibility certification.

The original captured r4 products were independently graded against frozen inputs and all six original screenshots inspected. The later recovery correction is supported by retained action/provenance and test artifacts; it does not overwrite those historical captures. A separate fresh same-model metered extension has an additional 15-minute/USD 5 cap. It is still running: no extension final result, review count, or comparison is claimed here. Artifact links point to local `/private/tmp` directories, which must be retained to preserve this evidence.
