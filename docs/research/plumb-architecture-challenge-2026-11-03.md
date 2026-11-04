# Architecture challenge: keep the CLI, fix the evidence contract

Reviewed 2026-11-03. Verdict: **keep the local architecture; revise four contracts before implementation.** These are recommendations. The original architecture/ADRs remain unchanged, and no product code is implemented.

[Current proposal diagram](../visualizations/plumb-checker-current.html) · [Recommended first experiment](../visualizations/plumb-checker-recommended.html)

## Intent

> Build Plumb afresh as a minimal local intent-vs-code checker. Review repo docs/ADRs and an explicitly supplied PR body against a pinned change; cite both sides and ask a person to resolve code wrong, spec stale or sources conflict. No MCP, hosted service, automatic fixing or inherited factory machinery.

The challenge concerns whether the proposed design serves that goal, not whether it should become a different product. The review is of design documents, not nonexistent implementation code.

## Reviewers

- **A — `gpt-6-astra`, high:** three substantial findings: scope, analysis/resolution semantics, observable origin ground truth.
- **B — `gpt-6-sol`, high:** three substantial findings plus one narrower risk: scope, policy trust, repeat incomplete outcomes, unsupported-file scope.
- **C — `gpt-6-luna`, high:** two warnings and one nit: authority complexity, context selection, latency measurement.

All three received the same intent, document pointers and Interrogate rubric independently. This is model diversity within OpenAI's model set, not independent-vendor validation. The lead checked their reasoning and merged root causes rather than counting votes.

## Act on

### R1 — Define a scope the command can actually review

**Raised by:** A, B, C. **Severity:** warning. **Confidence:** high for the contract gap; usefulness remains unmeasured.

`docs/intent-spec.md:20` discovers README and Markdown throughout `docs/`; `:14` defers explicit scoping. Yet `docs/ARCHITECTURE.md:53` suggests a narrower invocation on overflow. Narrowing the Git range does not narrow the unchanged documentation corpus. `docs/adr/0005-model-workflow.md:21` also says relevant code is selected without defining how caller guards and exceptions outside the diff enter the packet.

**Pressure test:** committed `HEAD` contains **111** matching Markdown files, **1,457,921 bytes** and **202,811 whitespace-delimited words**. It includes old factory policies, pilot documents and fixture specs. These are exact Git-blob corpus counts, **not provider token counts**. They demonstrate that broad discovery needs selection; they do not prove the eventual model will silently truncate.

**Counterexample:** a five-line helper change is constrained by a guard in an unchanged caller. A diff-only packet can invent a violation. Including all docs can overflow before the relevant caller is read. Both failure modes are plausible; neither is cured by a third model reading the same insufficient packet.

**Smallest recommendation:** expose explicit intent selection in v0.1, for example repeatable `--intent <tracked-path>`; define reviewed code paths and supported text types. Keep the packet manifest and original passages/windows. Default auto-discovery may list suggestions, but cannot imply every discovered document was reviewed. Start with changed files plus deliberately bounded exact path/identifier matches and surrounding code; if the needed caller/guard is still absent, report the gap. This is a concrete baseline to evaluate, not a claim that text search resolves all call relationships.

**Proof needed:** one mature-repo fixture, one historical-policy fixture and paired caller-present/caller-missing cases. Show selected/excluded sources, code windows and outcomes. Record missing-context failures before choosing a parser, index or model-controlled read loop.

### R2 — A Git base is an identity anchor, not a trust anchor

**Raised by:** B; C identified related policy complexity. **Severity:** warning. **Confidence:** high.

`docs/intent-spec.md:22` lets base-snapshot `.plumb/sources.json` set precedence; `:26` lets trusted base policy permit head replacements. `docs/adr/0003-snapshots-and-state.md:31` repeats the assumption. But the user can select an arbitrary `base..head`. No separate rule establishes that the selected base's policy is operator-approved.

**Counterexample:** a contributor puts a rule excluding the refund ADR in commit X, changes refund code in Y, and the command reviews X..Y. The rule's presence in X proves it precedes Y; it does not authorize suppressing the ADR. Immutability makes the policy reproducible, not trusted.

**Smallest recommendation:** only an explicitly operator-selected policy input, or a separately trusted policy revision configured outside the reviewed change, grants authority. Expose the promised policy input in the command. Repo-local policy is evidence/suggested configuration until that trust is established. No signatures, approval server or durable permission database are needed.

**Proof needed:** two-commit fixture above, a trusted-operator-policy control, and a head-authored policy case. Pin identical bytes in all cases; changing only the source of trust must change whether precedence can be applied.

### R3 — Finish the analysis without pretending the human has decided

**Raised by:** A, B. **Severity:** warning. **Confidence:** high for the semantic inconsistency.

`docs/intent-spec.md:31` makes a coherent code/spec revision incomplete when replacement approval is unknown. But a fully characterized source conflict or mismatch can be complete while a human decision remains (`:63`, `:81`). CI cannot distinguish “the review finished and found a decision” from “the API failed or a caller was unread.” Re-running the same PR does not resolve the first condition.

**Smallest recommendation:** separate `analysis` from `resolution`. A fully established intent revision may yield a question with complete analysis, without asserting that the revision was approved or that code is wrong. Reserve incomplete for missing required evidence, an unfinished phase, or applicability the checker could not characterize. Human resolution stays outside Plumb initially; do not add an approval workflow just to make an exit code green.

| Observed result | Recommended analysis | Recommended shell outcome |
| --- | --- | ---: |
| Declared scope read, no retained issue/question | Complete | 0 |
| Mismatch, concurrent source conflict, or fully characterized intent-change question | Complete; human decision needed | 1 |
| Invalid config/range, credentials or Git acquisition | Not started / error | 2 |
| Missing caller, unread required passage, refused/truncated/timed-out analysis | Incomplete; preserve valid partial evidence | 3 |

This proposes a change to the original intent-change mapping; the diagram is not evidence that the contract was already updated. “Complete” still means the declared analysis finished, never that all code is correct.

**Proof needed:** golden reports for coherent code/spec revision, unchanged-source mismatch, source conflict and missing-context/API failure. A caller must distinguish a pending human choice from an unfinished review without interpreting prose.

### R4 — Do not grade hidden history as observable intent

**Raised by:** A. **Severity:** warning. **Confidence:** high for the identifiability problem; scorer behavior is not implemented.

The contract correctly allows an unresolved origin (`docs/intent-spec.md:63`). The evaluation proposes equal code-wrong/spec-stale buckets and origin recall/confusion targets (`docs/research/plumb-intent-forces-2026-11-03.md:31`, `:121`, `:123`, `:127`), without fully defining what input evidence makes that cause knowable.

**Counterexample:** the packet says “refund to card” in docs and issues credit in code. One fixture author knows the docs were forgotten; another knows the code is buggy. With identical visible packets, the checker cannot infer those different histories. An accurate mismatch plus an unresolved origin should earn detection credit in both cases.

**Smallest recommendation:** score mismatch detection separately from origin classification. “Recall within seeded origin buckets” may mean detection recall stratified by known fixture history; say that explicitly. Score origin only when visible evidence distinguishes it, and require abstention otherwise. Report false confident origin claims as a separate error.

**Proof needed:** paired identical packets with different hidden histories must have the same acceptable unresolved result. Add a second pair where visible authoritative evidence actually distinguishes the origin. Keep latency/cost/completion separate from these quality scores.

## Consider

- **Context acquisition beyond the baseline.** All reviewers see it as the hardest remaining uncertainty. A bounded host-controlled read request, parser or lexical index may pay, but none has an evaluated benefit yet. First distinguish retrieval misses from semantic misses. Do not introduce an open-ended agent framework to make a diagram feel complete.
- **Unsupported changed files.** B notes that code plus an image/lockfile can force exit 3. R1 should define supported review scope and disclose deliberate exclusions separately from unread required evidence. Do not claim to review an image or generated artifact just because Git enumerated it.
- **Authority lifecycle complexity.** C's objection is useful for automatic retirement permissions: precedence metadata was in the recalled brief, but a policy engine for retiring individual commitments has no demonstrated user need. Keep provenance/precedence explicit; defer stored resolutions and lifecycle machinery.

## Noted

- C flags the p99 target. The original appendix already calls it unmeasured and warns that 120 held-out cases do not establish a production tail percentile. Keep it a target until a separate timing protocol exists; no new architecture is required.
- The extraction/assessment/disproof workflow is not established as superior. The plan already includes a naive baseline and optional disproof. Make that baseline the first candidate, retaining original passages so an extraction omission is not automatically inherited by every later stage. Adopt extra stages only after ablation.

## Dismissed

- **“Source precedence was not requested.”** The recovered user conversation explicitly requires source authority/precedence. Removing it wholesale would discard a real requirement. The valid part is R2's trust boundary and the narrower recommendation to defer automatic retirement machinery.
- **“An index or autonomous agent is necessarily required.”** No reviewer demonstrated that. The scope/relevance gap is real; the right tool is still an experiment. No fixed new backend follows from the gap.

## Agreement map and surviving decisions

All three converged on scope/context selection. A and B independently found the analysis/resolution tension. B's trust-anchor counterexample and A's hidden-history counterexample stand on their concrete logic, not vote count. C's broad authority objection conflicts with the recalled brief, so only its narrower complexity concern survives.

Keep: **one local synchronous CLI; Python provisionally; one official SDK boundary; pinned committed inputs; exact source/code citations; a deterministic validation boundary; JSON/Markdown from one report; explicit errors/gaps; human resolution; baseline-first evaluation.** No finding requires a database, server, queue, MCP adapter, generic plugin API or compatibility layer for the factory.

## Visuals and validation limits

The two standalone diagrams distinguish the existing proposal from the recommended first experiment. Their schema, layout, artifact and real-browser automated gates passed. They model a proposed system, not running repository behavior. Interactive in-conversation diagrams additionally show the trust boundary and revised outcome semantics; markup, script syntax and scenario updates were checked.

An attempted manual browser preview of the inline fragment was blocked by browser URL policy; no workaround was attempted. Manual font/overlap inspection is therefore unverified. The standalone diagrams' automatic browser checks were separate authorized Archify runs. No model quality, live API, price or performance benchmark was run. Original design documents, source, tests and dependencies remain unchanged in this challenge turn.
