# Codex full-stack comparison — 14 October 2026

Superpowers delivered the neutral full-stack support desk much faster and cheaper in this observed run. Factory delivered no HIGH code-review finding; Superpowers delivered one. Neither product passed the subsequent independent code review unchanged. This is useful first-delivery evidence, but **not a valid uniform-effort experiment**: three Factory executor children used installed `medium` defaults despite the requested `high` policy.

| Measure | Factory | Superpowers |
|---|---:|---:|
| Total actor/controller wall time | 4h 02m 06s | 32m 46s |
| Recorded-usage API-rate estimate | $36.07499 | $1.89704 |
| Trusted acceptance at first workflow delivery | 19/19 | 19/19 |
| Predefined journeys accepted | 5/5 | 5/5 |
| Trusted-feedback repair rounds | 0 | 0 |
| Operator questions | 18 | 3 |
| Model responses, including descendants | 1,748 | 86 |
| Native child threads | 40 | 2 |
| Independent CRITICAL findings | 0 | 0 |
| Independent HIGH / MEDIUM findings | 0 / 2 | 1 / 1 |
| Architecture review | WATCH | WATCH |

Factory took **7.39× the time** and **19.02× the estimated API cost**. Its own workflow included several repairs, an initially incorrect frozen test, three six-lens milestone reviews, two independent 30-criterion acceptance passes, a corrective fourth slice, and reconciliation. “Zero trusted-feedback repairs” means the final external suite passed on first delivery; it does not mean zero internal fixes.

## Products and agreements

Both chose SQLite and vanilla HTML/CSS/JavaScript. Factory chose Flask 3.0.3 with project-pinned dependencies and a TLS-capable installed Python 3.9 environment. Superpowers chose the Python standard-library HTTP server, separated HTTP routing from a `Desk` domain module, and added no third-party runtime dependencies. Its decisions explicitly rejected Flask and Express/React as unnecessary for the required local workload.

Both recorded the shared four FR and six NFR agreements before implementation. The trusted suite independently passed authentication/logout, combined search/filtering, creation, operator editing/assignment, comments/history, tenant/customer authorization, mass-assignment rejection, stale versions, sequential clients, validation/failure retention, keyboard/responsive checks, local performance, durable restart, read-only recovery and malformed database preservation. Those ten requirements map to five predefined journeys; workflow-created slices do not increase the denominator.

Both began with the same two-file **Python launch scaffold**. The common brief also fixed HTTP routes/DTOs, accessible labels, seeded data, professional neutral visual direction and owner preferences. This deliberately makes functional grading comparable, but biases the starting stack toward Python and limits evidence about open-ended framework or product discovery. Matching FR/NFR agreements are expected shared inputs, not independently discovered decisions.

### Cross-workspace contamination audit

A separate read-only audit checked Superpowers' fresh root and both child rollouts: 52 root executions, one design-check execution and 12 review executions. It found no observed attempted or successful read of `snapshots/factory`, the original Factory repository, or the completed Factory workspace. Initial inventory contained only `benchmark.sh` and `server.py`; the root was a fresh `exec` session, the design child forked that Superpowers root, and the final reviewer was an isolated Superpowers-root child. Workflow reads targeted pinned Superpowers skills; design/document/image reads targeted its own generated files. The common output directory's `factory-codex-fullstack` name is not evidence of Factory content access.

The harness pasted the same neutral benchmark specification into both prompts; that specification was authored in this repository. It did not paste the completed Factory design or decisions. Some generic transport instructions mentioned Factory reconciliation even in the Superpowers prompt, which explains those text mentions and is another limitation for a pure workflow-discovery claim. This audit establishes observed reads, not absolute protection against every theoretical covert channel. A future discovery comparison should start from blank repositories and an outcome brief, collect independent proposals first, then freeze compatible acceptance requirements before implementation.

Manual trajectory review found the applicable workflows completed. Factory followed triage, design/product, architecture/security, interface, slices, build/review milestones, independent acceptance, retrospective/reconcile and local finish. Superpowers read the pinned Codex bootstrap/reference, then brainstorming, writing/executing plans, test-first implementation, independent review and repairs, verification and local finish. Both merged into their disposable local `main`; neither pushed or deployed. Original result records remain unchanged; reviewed accounting and trajectory evidence are separate.

The external code review revealed that the 19 groups are not exhaustive proof of FR/NFR compliance. They establish the specific tested behavior, not a completely finished product with no follow-up.

## Independent findings

Two fresh reviewers received anonymous final sources and the same public brief; they did not receive identity, timing or cost data. Both saw the actual desktop/mobile/details screenshots. Code findings below were reproduced through native-sandbox API/browser probes.

| Product | Severity | Remaining issue |
|---|---|---|
| Superpowers | HIGH | Malformed successful JSON is converted to success: an intercepted 201 response containing invalid JSON closes creation without a commit or alert. |
| Superpowers | MEDIUM | Native HTML `maxlength=120` permits only 60 emoji through keyboard input, although the server accepts 120 Unicode code points. |
| Factory | MEDIUM | Lone-surrogate login values and deeply nested JSON return 500 HTML instead of the required 400 JSON. |
| Factory | MEDIUM | After a successful detail write refreshes ticket rows, Cancel/Escape focuses New ticket rather than the still-present ticket opener. |

Both code-review recommendations are **REQUEST CHANGES**. These first-delivery defects remain unfixed so the comparison preserves the delivered versions.

The architect gave both **WATCH**. Superpowers has clearer HTTP/domain boundaries and better dirty-field conflict recovery, but weaker startup schema verification and nondeterministic SQLite connection closure. The schema concern is static rather than a demonstrated runtime acceptance failure. Factory has stronger stored-data/schema auditing and explicit connection closure, but a larger intertwined server and less convenient conflict recovery. The architect narrowly preferred Superpowers for follow-up overall.

Visual judgment is subjective: both meet the professional neutral direction. Superpowers has stronger details hierarchy and desktop column labels; Factory has more compact queue rows and shorter IDs. Neither screenshot set shows page overflow or clipped controls.

## Where Factory spent the estimate

This groups deduplicated response usage by native thread ancestry/path. The main bucket includes work performed directly by the conductor, not just idle coordination.

| Actor work | API-rate estimate | Share |
|---|---:|---:|
| Main orchestration/direct work | $14.36 | 39.8% |
| Milestone review subtrees | $13.00 | 36.0% |
| Build/executor subtrees | $5.59 | 15.5% |
| Planning/design/research/retro children | $1.59 | 4.4% |
| Independent acceptance children | $1.53 | 4.3% |

Main work and review account for about **76%**. Moving only code changes to a cheaper model cannot close this gap: even free build/executor work would leave roughly $30.48. To reach a 30–50% premium over this Superpowers result, Factory would need about **92–93% less cost**, not a small token trim.

| Recorded tokens | Factory | Superpowers |
|---|---:|---:|
| Ordinary input | 4,905,011 | 254,137 |
| Cached input | 170,552,320 | 7,232,896 |
| Cache writes | 0 | 0 |
| Output, including reported reasoning | 729,207 | 66,548 |
| Input + output | 176,186,538 | 7,553,581 |

Cache reads are included in input and are not charged twice. Per-response estimates use the frozen GPT-6.1-Sol rate schedule and its long-context tier; twenty Factory responses exceeded 272K input, versus none for Superpowers. Resumed cumulative counters are never summed. Complete observed usage is not a verified invoice. [Model pricing reference](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [cache accounting](https://developers.openai.com/api/docs/guides/prompt-caching).

The next optimization experiment should bound conductor handoffs, consolidate repeated review, automate hash/state bookkeeping, and measure cheaper implementation/review routing under explicit contracts. Context compression can help with repeated context, but this pair used no Context Mode or llm-trim and proves no savings from either.

## Controls, defects and limits

Both runs used Codex CLI 0.162.1, `gpt-6.1-sol`, requested root effort `high`, the same frozen brief/operator policy, fresh Git fixtures, browser capability and local native isolation. Superpowers was pinned to v7.0.0 commit `bb92a77741419a4ab5f06e711a283343f1ada0c3`; Factory source baseline was `3dbdbff`, with copied kit/skills and recorded benchmark adaptations. This is a cold skills comparison, with optional unavailable tools recorded as skips and Factory's edit-gate hook absent. Factory's frozen snapshot contained 0 of 35 pinned packs: its global book skills existed, but the separate pinned cache had not been prepared before snapshot creation. It therefore does not evaluate fully book-enabled Factory behavior. All 35 current pinned cache directories were present when audited afterward; historical results are unchanged.

Final accounting found 1,680 high and 68 medium Factory responses, versus 86 high Superpowers responses. Three named executor roles silently applied their installed defaults; no spawn request explicitly selected medium. Native role configuration applies after inherited defaults. The historical `effort_policy_valid=false` and strict pair-invalid status remain. [Resolution order](https://github.com/openai/codex/blob/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d/codex-rs/core/src/agent/child_config.rs#L50-L84).

Future preparation now snapshots the inspected installed role preset, preserves instructions and other fields, pins model/effort in immutable copies and checks tampering. It explicitly does **not** claim complete effective-inventory coverage or universal enforcement: higher-priority managed declarations, undiscovered roots and full forks remain limits. Final observed model/effort auditing is mandatory. This does not retroactively validate the completed pair.

The earlier r1 attempt is excluded operator-policy calibration: an unbounded `sign` match confused design approvals with Git signing. r2 retained one clarification when a defect-classification question mentioning “stack” received a stack answer; it then requested explicit approval and preserved both defects for correction. Its frozen policy was shared and never changed mid-run.

Controller/browser setup and calibration, harness engineering and this common independent audit are outside per-actor time/cost. Human follow-up minutes remain unmeasured. Actual monetary billing is unknown under the current authentication. One paired task, framework choice and the effort discrepancy prevent a causal or general winner claim.

## Practical verdict and artifacts

For this observed task, **Superpowers is the stronger efficiency starting point with mandatory independent review**. Factory bought one fewer HIGH finding and stronger stored-data checks, but not a demonstrated reduction in follow-up commensurate with 19× cost. Better constraints and lower-cost role routing remain sensible; the data says to reduce orchestration/repeated review as well as implementation cost.

The local gallery and exported applications are outside private temporary directories:

- [Desktop, mobile and details gallery](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/gallery.html)
- [Recorded comparison data](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/comparison.json)
- [Independent code review](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/independent-code-review.md)
- [Architecture/visual review](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/independent-architecture-review.md)
- [Factory decisions](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/factory-DECISIONS.md) and [Superpowers decisions](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/superpowers-DECISIONS.md)
- [Factory application](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/apps/factory/benchmark.sh) and [Superpowers application](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/apps/superpowers/benchmark.sh)

Raw r2 trajectories, immutable snapshots, original results, reviewed usage ledgers and helper revisions remain at `/private/tmp/factory-codex-fullstack-20261013-r2`. Final harness verification passed **79 tests**, Ruff and diff checks, plus independent code-review APPROVE and architectural CLEAR across the completed deltas. New harness changes and this report are uncommitted; no new push was performed.
