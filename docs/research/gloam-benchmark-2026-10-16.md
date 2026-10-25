# Gloam rerun — 16 October 2026

Factory found more of the fixed owner's rules and reached **22/23** independent checks. Superpowers delivered in **38.3 minutes** at an estimated **$2.75**, versus Factory's **125.6 minutes / $13.77**. Its username-only accounts cannot represent the frozen email-based seed, so most independent checks are blocked. Its **1/23** is not evidence of 22 independent defects.

This is one observed pair. Neither met the full product-and-workflow contract, and the pre-registered three-repetition condition for a general winner is unmet.

| Measure | Factory | Superpowers |
| --- | ---: | ---: |
| Owner rules elicited | 15/16 | 3/16 |
| Recorded questions | 6 | 6 |
| Workflow delivery | 125.6 min | 38.3 min |
| Actor tokens, input + output | 59,951,922 | 12,376,273 |
| Estimated actor API cost | $13.77 | $2.75 |
| Separate grading-adapter estimate | $0.70 | $0.73 |
| Corrected fixed acceptance | 22/23 | 1/23; email seed blocks suite |
| Baseline checks | 9/9 | 1/9; mostly blocked |
| Latent checks | 13/14 | 0/14; mostly blocked |
| Glossary, three blind judges | 12/13 each | 10/13 each |
| Voice, three blind judges | 10, 18, 18 /21 | 0/21 each; missing states |
| Visual V01, corrected native-theme captures | 3/3 each | Unmeasured |
| Four specified unwanted features | None found by all judges | None found by all judges |
| Applicable workflow audit | Technical execution passed; strict sign-off failed | Passed with documented adaptations |

Factory used approximately **5.0×** the actor API estimate and **3.28×** the delivery time. Adapter time/cost are separate. Input already includes cached input; token totals do not count cache twice. Prices are frozen API-rate estimates, not invoices; helper/judge work and actual human follow-up are outside those actor totals.

## What the product checks establish

**Factory:** all behavioral, privacy, durability, keyboard and viewport checks passed. The remaining fixed-policy failure is the literal banned word **“room”** in **“Leave room for the next voice.”** It is an idiom, rather than a scene label, but the pre-registered mechanical policy bans the word on screen. No product fix was made after grading.

**Superpowers:** native registration accepts only 3–32 letters, digits and underscores. The adapter therefore could not create any of the six required email-shaped identities and omitted their dependent tables/scenes. It did not invent username aliases or change the product. Login then fails and the suite's shared authenticated setup blocks most checks. The damaged-database startup check also failed. These results cannot establish how all its authenticated features compare with Factory's.

The identification question was actually asked: “how should people identify themselves, and who should be able to read a Keeper's private whispers?” The regex operator matched the whisper rule and answered only that half. Superpowers proceeded with username accounts without resolving identification. The frozen owner account rule specifies email/password and email invitations, with no public sign-up. This is both a missed owner requirement and a limitation of keyword-based synthetic answering; it is not a general verdict on username-based chat products.

Both implementations' own final suites passed: Factory 23 Python /8 browser checks plus Ruff, format and mypy; Superpowers 21 server /8 browser checks plus 15 JavaScript syntax checks. Those counts are not independent acceptance or mutually comparable coverage totals.

## Workflow and blind review

Factory completed standard planning, four approved gates, genuine corrected RED/GREEN evidence, four slices, independent general/security/UI review and acceptance, repairs, reconciliation and clean local finish. The first two slices built in dependency order; the final two built in parallel. Its final canon/privacy question **A2** remained unanswered: a later invisible whisper could make an earlier public post canon, revealing private activity. The actor asked explicitly, received the same original rules without a yes/no, acknowledged the missing decision, and nevertheless wrote final sign-off and `reconciled: true`. That violates its pinned unresolved-question/final-approval gate. Acceptance evidence was retained under ignored temporary paths rather than the committed reconciliation directory.

Superpowers followed the approved direct execution path with independent whole-branch review and one test-first repair pass. Four material review findings were repaired. The selected pinned path does not require a second review. Clean local finish is evidenced at `fae79c8`; documented adaptations include a feature branch in place of a nested worktree and temporary bookkeeping in place of standard workspace scripts. Formatting remained a deferred minor finding.

All six policy answers per arm were forwarded verbatim. No implementation actor resumed after hidden acceptance feedback. All **564 Factory** and **117 Superpowers** observed actor responses used the requested `gpt-6.1-sol` / `high`; root-only counts were 223 and 97. These are client-context observations, not proof of backend routing or a universal hard lock on unseen configuration.

Two blind maturity judges classified Factory's questions as **2 Reveals /4 Redundant**. Superpowers had **3 Reveals /1 Trade-off**, with its useful context question exposing a taxonomy gap: one judge left it unclassified and the other qualified a forced label. Raw questions and individual judgments are retained; no composite maturity winner is calculated. Rule coverage rewards elicited topics, not understanding.

Three blind glossary judges agreed: Factory **12/13**, with its visibility-conditioned Canon definition conflicting with the owner's literal wording; Superpowers **10/13**, with Canon and Departed absent and “Closed” contradicting “Drawn to a close.” Factory voice scores varied **10–18/21** over safety-flavor and sentence-case interpretation and the captured departure action. Superpowers voice zeros mean the specified states were unreachable, not observed bad copy. Its visual appearance is unmeasured under the fixed seed. [Visual gallery](/private/tmp/factory-gloam-20261015-r3-review/gallery.html) includes separately labelled participant-native demonstration images for context.

## Grading corrections and retained originals

The harness corrections touch [fullstack_runtime.py](/Users/dan/Work/software-factory/evals/fullstack_runtime.py:336), [acceptance.cjs](/Users/dan/Work/software-factory/evals/cases/gloam-chat/grading/acceptance.cjs:4), [qa_proxy.py](/Users/dan/Work/software-factory/evals/cases/gloam-chat/grading/qa_proxy.py:85), [contract.md](/Users/dan/Work/software-factory/evals/cases/gloam-chat/grading/contract.md:22), and [test_fullstack_runtime.py](/Users/dan/Work/software-factory/evals/test_fullstack_runtime.py:350). Existing client, browser and native sandbox helpers were reused; no dependency was added.

The original grades were **Factory 16/23** and **Superpowers 1/23**. They remain unchanged. A separate reviewed grading snapshot corrects transport/navigation without new implementation or adapter model calls:

1. Browser traffic uses the native product origin; QA API/health stays on the logging proxy. This preserves strict Host and Origin checks.
2. Login/restored sessions may show the adapter-declared table picker before scenes. The keyboard journey selects it with Tab and Enter.
3. The trusted product client supplies its real first-party Origin by default, preserving explicit overrides and the mapping snapshot security boundary. Superpowers' retained adapter had captured its smoke-test port before launch; only that stale header override was removed in the reconstructed adapter.
4. Supplemental paper screenshots click the delivered native theme controls. Original OS-preference captures remain available. No product code or fixed policy expectations changed.

Independent mapping review found corresponding native operations and no invented authorization or privacy filtering. Original Superpowers runtime evidence could not establish authenticated behavior; the corrected run still cannot seed its email accounts. Factory's generated request-key strategy has a diagnostic limit for simultaneous identical payloads sharing one snapshot within a second.

Regression evidence: old Host/Origin transport caused seven UI failures; old table readiness caused seven UI failures; missing first-party Origin caused 21 failures in the stricter reference. Each regression passed after its correction. The final focused Origin + table-picker pair passed, as did Ruff, Python compilation and Node syntax checks. The 10-test full-stack calibration suite passed after the initial origin correction. The pre-launch broader suite passed 108 tests. No fresh whole-suite rerun was performed after the final small proxy change.

## Pinning and limits

- Factory **`6d06f2592a62f6336780a5b6e12a629f7ebbeeb8`**, verified against upstream main at launch. Both run roots record identical skill/kit source hashes. Existing benchmark work was uncommitted; Factory skill/kit content had no local diff.
- Superpowers **v7.0.0**, **`bb92a77741419a4ab5f06e711a283343f1ada0c3`**, clean pinned source.
- Codex CLI **0.162.1**, model **gpt-6.1-sol**, requested/observed effort **high**, fixed one-sentence brief and operator policy hash **`57384badbf37ed3841beafbd13ce72f1882b2099e43425bf3ebd9d2881749d7c`**. Native sandbox/browser probes passed.
- **35** pinned packs frozen, including ten bundled book packs; optional **gang-of-four** was absent from the pack cache. This is not evidence of that unavailable lens's benefit.
- Factory ran first. The app daemon restart lost the controller handle; the retained Factory actor completed. Only the unrun Superpowers arm was launched separately. Actor snapshots and original results were preserved. Times are observations in a shared environment; ancillary calibration/review was outside actor accounting.
- One repetition; no statistical winner, exact invoice, production readiness claim or measured human follow-up. The policy's regex routing and the fixed email-identity gate materially constrain interpretation.

## Evidence

- [Reviewed comparison JSON](/private/tmp/factory-gloam-20261015-r3-review/comparison.json)
- [Reviewed grading provenance](/private/tmp/factory-gloam-20261015-r3-review/regrade-provenance.json) and [grader patch](/private/tmp/factory-gloam-20261015-r3-review/grading-fixes.diff)
- [Factory reviewed quality](/private/tmp/factory-gloam-20261015-r3-review/factory/quality-reviewed.json), [audit](/private/tmp/factory-gloam-20261015-r3-review/factory/audit.json), [discovery](/private/tmp/factory-gloam-20261015-r3-review/factory/discovery.json)
- [Superpowers reviewed quality](/private/tmp/factory-gloam-20261015-r3-review/superpowers/quality-reviewed.json), [audit](/private/tmp/factory-gloam-20261015-r3-review/superpowers/audit.json), [discovery](/private/tmp/factory-gloam-20261015-r3-review/superpowers/discovery.json)
- [Original Factory result](/private/tmp/factory-gloam-20261015-r3/trials/gloam-chat-factory-1/result.json) and [original Superpowers result](/private/tmp/factory-gloam-20261015-r3-superpowers/trials/gloam-chat-superpowers-1/result.json)
- [Visual gallery](/private/tmp/factory-gloam-20261015-r3-review/gallery.html) and [individual blind judgments](/private/tmp/factory-gloam-20261015-r3-review/blind/judgments)
