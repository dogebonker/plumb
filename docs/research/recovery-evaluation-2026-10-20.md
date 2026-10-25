# Recovery and engineering-quality evaluation — 20 October 2026

Status: **in progress; no new twenty-task acceptance result yet**. The historical 14/20, 14/20 and 9/20 result is unchanged. [Protocol](recovery-evaluation-plan-2026-10-20.md).

## Verified implementation

The v2 host API preserves original approval/runtime bindings, accepted commits, native session, elapsed time, usage, retries and review passes through durable checkpoint recovery. An independent review confirmed the stale-state, event-deduplication and unpaid-clone recovery fixes. Live provider restart recovery remains unvalidated. Default-skill delivery and experimental v2 recovery are separate measurements.

All nine executable guarantee cases passed against the current sources. These are real regression fixtures, not production or model-behavior assurance.

| Guarantee | Result |
|---|---|
| scope | pass |
| frozen | pass |
| frozen-scenarios | pass |
| write-guard | pass |
| compliant-writes | pass |
| stale-proof | pass |
| adr-conflict | pass |
| approval-reuse | pass |
| imports | pass |

Guarantee report SHA-256: `f552ef89eec4bcf65bc1bd41f220d09f954f66d68104fdad0ed67f63c5b471f2`.

## Corpus calibration

All twenty published tasks were retained. Each historical base fails its feature acceptance; each actual PR reference passes, with zero skipped reference tests. Frozen acceptance/support bytes match the actual PR Git objects. All forty baseline/reference isolation probes pass.

| Task | Reference tests passed | Base feature RED |
|---|---:|---|
| limitless-4720 | 82 | yes |
| goldengate-1038 | 43 | yes |
| bot-1 | 21 | yes |
| limitless-4793 | 210 | yes |
| goldengate-1002 | 1 | yes |
| bot-8 | 1 | yes |
| limitless-4798 | 261 | yes |
| goldengate-995 | 7 | yes |
| bot-10 | 109 | yes |
| limitless-4795 | 54 | yes |
| goldengate-1010 | 7 | yes |
| bot-11 | 128 | yes |
| limitless-4811 | 21 | yes |
| goldengate-957 | 22 | yes |
| bot-12 | 127 | yes |
| limitless-4769 | 128 | yes |
| goldengate-1007 | 13 | yes |
| bot-2 | 21 | yes |
| limitless-4766 | 316 | yes |
| limitless-4762 | 230 | yes |

Calibration manifest SHA-256: `68e06bf770f69ee4125a19f3272b9c1153655053af5ba657a1430fe5cd718599`.

The six Goldengate descriptions use published titles and local squash-commit bodies because fresh API metadata is unavailable. Goldengate 1002 retains its disclosed email-domain unit scope. One transient pre-grading setup error was preserved; unchanged inputs passed recovery. No task or acceptance scope was replaced after a model outcome.

The new study supplies the same standing architecture policy and history contract to every arm. This adds explicit requirements and uses fresh calibration; it is **not an exact replay** of the deleted historical run.

## Four-task diagnostic observations

All four preselected Factory diagnostics completed and passed their immutable supplied acceptance. This is a Factory-only diagnostic subset, without independent anonymous acceptance judgments or a control comparison. It establishes no winner and does not revise the old benchmark.

| Task | Supplied tests | Task minutes | Native USD | New forbidden / cycles / unplanned | Original graph result |
|---|---:|---:|---:|---|---|
| goldengate-1038 | 43 passed | 38.8 | 11.63 | 0 / 0 / 19 | failed |
| limitless-4798 | 261 passed | 31.5 | 8.84 | 0 / 0 / 0 | no_new_violations |
| bot-10 | 109 passed | 20.9 | 6.66 | 0 / 0 / 3 | failed |
| limitless-4795 | 54 passed | 26.2 | 7.98 | 0 / 0 / 9 | failed |

Task time sums native turns; the 1,800-second guard applies to each invocation, not the whole feature. Cost is CLI-reported task-session usage, excluding separate probes and grading; it is not an invoice. Tokens include cached context and are not interchangeable with uncached input.

The initial forbid-only policies left unspecified imports classified as unplanned. Three diagnostic graph checks therefore failed, including ordinary package imports. Those outcomes remain frozen. Before the full comparison, fresh policies explicitly permit unspecified internal and package imports while retaining the named forbids and cycle checks. All three repositories passed unchanged, permitted-import and actual-reference probes, and rejected planted forbidden imports under those policies. This validates limited boundaries, not a complete module layout.

The traces show repeated gate/status repairs and substantial planning, verification and review work. They cannot prove why the deleted historical runs failed. Current assistant-message streams omit final output-token counts; full per-skill costs remain unknown rather than estimated.

A corrected derived report distinguishes explicit Skill invocations from artifact accesses and literal skill-file mentions. It covers all four trials and six native turns, using profiler SHA-256 `6fd0d16b494730e4c992ead18ea92b938a4e420ce9cbc19a39a2093976dc379d`; the original runtime profiler and reports remain preserved. Message-level output counters do not reconcile with terminal totals, and internal skill boundaries lack complete receipts. Task totals remain usable; allocation of those totals to individual skills would be an estimate.


Finalized records for the exact recorded native sessions subsequently recovered complete per-response token counters for three diagnostics. All four token classes reconcile with the original terminal totals, counting linked children once. The table below assigns whole responses to the interval following an explicit native Skill marker; it is **not the semantic cost of that skill**. Child usage is assigned only when dispatch and continuation links agree. Tokens include cached context; no USD allocation is inferred.

| Task | Observed interval | Tokens |
|---|---|---:|
| bot-10 | unattributed before first explicit native Skill | 41,519 |
| bot-10 | after native Skill factory:factory-triage | 11,753,801 |
| bot-10 | unattributed child dispatch/continuation | 0 |
| goldengate-1038 | unattributed before first explicit native Skill | 41,176 |
| goldengate-1038 | after native Skill factory:factory-triage | 2,323,310 |
| goldengate-1038 | after native Skill factory:factory-plan | 1,181,872 |
| goldengate-1038 | after native Skill factory:factory-build | 8,340,145 |
| goldengate-1038 | after native Skill factory:factory-review | 8,547,154 |
| goldengate-1038 | after native Skill factory:factory-reconcile | 2,840,125 |
| goldengate-1038 | unattributed child dispatch/continuation | 0 |
| limitless-4798 | unattributed before first explicit native Skill | 41,429 |
| limitless-4798 | after native Skill factory:factory-triage | 2,735,008 |
| limitless-4798 | after native Skill factory:factory-build | 5,082,861 |
| limitless-4798 | after native Skill factory:factory-review | 5,858,420 |
| limitless-4798 | after native Skill factory:factory-reconcile | 2,860,191 |
| limitless-4798 | unattributed child dispatch/continuation | 0 |
| limitless-4795 | all intervals | unmeasured |

Bot 10 has only a triage entry marker, so its large after-triage interval includes later implementation and review. Limitless 4795 lacks a finalized receipt for one linked child API message; its task-level native totals remain known, but interval allocation is held. These limitations prevent a complete per-skill-cost claim. The numeric interval receipt has SHA-256 `36a4f121417db83b07ea894fe7ac8dab977cb7c80363d0d3b711d039be29cb59`.

All four traces hit the “no building slice” guard before editing: six refusals in total. Limitless 4798 also needed unparseable slice headings repaired. Goldengate queued three writes against the same unchanged readiness failure; that repetition is directly evidenced. Other repeated checks followed code fixes or newly available evidence, so repetition alone is not classified as waste.

The resulting improvement candidates are:

- Validate build readiness and slice headings mechanically before implementation; keep the required history update inside the authorized build lifecycle.
- Resolve paths and verify the execution substrate before spending a model turn on setup repair.
- Reuse verification only when its relevant input fingerprints match; a document-only diff by itself is insufficient proof.

These are diagnostic recommendations, not changes to the framework frozen for the running comparison. The private overhead note retains 66 validated raw-log references and SHA-256 `b026b46dfc36ba9231172f39ed8f8b3c2c146ed355db08e5a15239dc08e2a7fb`.

## Maintenance chain

The three-step bot 10 → 11 → 12 chain has finished with incomplete semantic review coverage. Each executed follow-up used its own arm’s retained implementation and a fresh session. No historical implementation was substituted. A failed or unverified step halted later work in that arm.

| Arm | Step | Actor outcome | Supplied tests | Pinned architecture | Immutable inputs | Static correctness | Static history | Static rules |
|---|---|---|---|---|---|---|---|---|
| bare | bot-10 | complete | 109 passed | pass: no new violations | pass | pass | pass | pass |
| bare | bot-11 | complete | 128 passed | pass: no new violations | pass | pass | pass | pass |
| bare | bot-12 | complete | 155 passed | pass: no new violations | pass | unmeasured | unmeasured | unmeasured |
| claude-md | bot-10 | complete | candidate_error | pass: no new violations | pass | pass | pass | pass |
| claude-md | bot-11 | not run: inherited failure | not run | not run | not run | not run | not run | not run |
| claude-md | bot-12 | not run: inherited failure | not run | not run | not run | not run | not run | not run |
| factory | bot-10 | timeout | 109 passed | pass: no new violations | pass | unmeasured | unmeasured | unmeasured |
| factory | bot-11 | not run: inherited failure | not run | not run | not run | not run | not run | not run |
| factory | bot-12 | not run: inherited failure | not run | not run | not run | not run | not run | not run |

An actor’s `complete` response is distinct from passing quality checks. The CLAUDE.md candidate received the frozen `candidate_error` classification despite a valid static acceptance judgment: twelve DB-dependent tests exceeded their five-second limits. A later reference control passed 109/109, but that sequence does not establish a candidate-code defect; the cause of the timeouts remains unresolved. The separate causal note preserves all twelve locations and both runs’ timings without changing their scores. Bare completed all three changes and passed all cumulative tests, but its final review had prose before the required JSON and remains unmeasured. Factory’s first attempt timed out with green supplied tests; its original review lacked standing-intent citations and remains unmeasured. Original invalid receipts and opinions are preserved; neither was re-reviewed or normalized into a scored verdict.

| Arm | Attempted steps | Native task tokens | Native task USD | Native task minutes |
|---|---:|---:|---:|---:|
| bare | 3 | 15,060,752 | 10.65 | 38.0 |
| claude-md | 1 | 9,416,773 | 5.61 | 20.4 |
| factory | 1 | unknown | unknown | 42.0 |

Evaluation overhead is separate from task usage: five isolation probes and five native review calls, including invalid reviews. Administrative revalidation and report completion added zero provider calls; aliases do not double-count the original sessions.
- probes tokens: 392,112.
- probes native USD: 0.38.
- reviews tokens: 3,740,276.
- reviews native USD: 4.02.

This is one historical chain, not evidence of a general history-quality advantage. Pinned architecture checks cover the declared boundaries; static review does not establish runtime correctness. Administrative final-report SHA-256: `2d937fc07d4e4eba2ec38e2ee7989ed5d4110f05eb7cef88b4d2d626fe653103`.

## Pending evidence

The maintenance chain above has finished with two unmeasured reviews. The fresh twenty-task three-arm trial is still running against frozen inputs. Initial isolation probes passed for all three comparison arms. Independent anonymous review and separate delivery, correctness, architecture, rule-compliance, history, token and time tables will follow the full trial. Missing evidence is not a pass.

The first maintenance judgments exposed an evaluator compatibility error: pinned Claude Code 2.1.304 reports two built-in plugins even when third-party plugins are disabled. The original inventory validator rejected those receipts. A separately reviewed adapter accepts only that exact built-in inventory, while retaining the model, session, read-only tools, empty MCP and evidence checks. Original receipts and invalid statuses are preserved; revalidation reuses the original opinion without another model call. Actual code or test failures remain failures. The same correction was recorded before full-study anonymous review began; its rubric and execution limits are unchanged.

Before any full-study review, the prospective reporting protocol also gained native JSON-schema output. Its only added tool is the pinned CLI’s read-only `StructuredOutput`; the hook applies the original verdict, quote and standing-intent checks before allowing it. Other requests retain the original read scope. Every full-study packet gets this same protocol, original rubric and one native session bounded at 600 seconds; internal format corrections count as evaluator overhead. No maintenance opinion is retried. One synthetic calibration passed in 22.55 seconds, with 25,706 tokens and CLI-reported USD 0.1046378, recorded separately from feature and review costs. This checks reporting and scope, not review accuracy.

Disk pressure required temporary pauses of new full-study dispatch and its waiting postprocessor. Active actors and their guard timers continued. Generated Go caches were removed only from finished attempts and proven orphan grading scratch directories, with unchanged source hashes recorded before and after; raw evidence and source remain retained. Offline uv pruning removed unreachable cached objects. With new dispatch paused and no Jest process running, 217 generated Jest transform-cache directories predating the study were also removed. New dispatch resumed after free space recovered to about 18 GiB, with continued finished-cache cleanup and space monitoring. Native task timings retain the original limits; supervisor wall time can include these operational pauses. Cache cleanup is recorded separately from quality scoring. A study-scoped monitor held new dispatch below 8 GiB, but free space subsequently fell below 1 GiB while active work continued. On the second low-space incident, automatic resumption was disabled and both dispatchers were held for diagnosis; active actors and their guard-owning controllers were not signaled. This shows the original disk watermark was insufficient under the observed operating load.

Active attempts shared laptop CPU and I/O with that cleanup. Timing and deadline outcomes are observations under this operating load, not controlled estimates of the workflow’s causal speed effect.

The host also entered low-power sleep at 03:32 and woke on AC at 13:56 local time. Overlapping controller records show about 37,414 seconds of epoch elapsed time absent from their monotonic timers. Native timing columns therefore exclude that suspension; actual end-to-end elapsed time does not. A process-scoped idle-sleep assertion was added for the remaining run. Original guard limits, outcomes and raw receipts remain unchanged; affected rows will be flagged rather than silently rerun or reclassified.

Private source, immutable inputs and raw receipts are retained outside `.tmp` under `~/.local/state/software-factory/recovery-evaluation-20261020/`. Only summaries and fingerprints belong in this repository.
