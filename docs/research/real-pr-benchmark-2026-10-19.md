# Real feature PR benchmark — 19 October 2026

Factory has **9 accepted tasks out of 20**, versus **14/20 with a good CLAUDE.md**: an observed **−25 percentage points**, below the predeclared +10pp target. Both of those arms have complete quality evidence for all 20 tasks.

After two isolated mechanical grading recoveries on unchanged source, bare and CLAUDE.md each have **14/20** accepted tasks; Factory has **9/20**. Quality evidence now covers all 60 trials. The original first-pass errors and tables remain below, alongside the separate recovery evidence. This is one descriptive trial; it establishes no statistical superiority.

This measures the existing sequential Factory skills. The constrained Sonnet-worker / mechanical-gate / Opus-review v2 pilot is a separate experiment.

## Quality

| Arm | Confirmed accepted | Quality coverage | Tests pass | No new detected cycles | Blind accept | Completed delivery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bare | 14/20 | 20/20 | 20/20 | 20/20 | 14/20 | 20/20 |
| claude-md | 14/20 | 20/20 | 20/20 | 20/20 | 14/20 | 20/20 |
| factory | 9/20 | 20/20 | 14/20 | 20/20 | 12/20 | 11/20 |

Acceptance requires completed delivery, passing immutable PR tests, a clean cycle-diff check and blind acceptance. A passed test suite or positive review alone does not establish delivery. All nine execution-guard timeouts occurred in Factory and remain delivery failures.

The first pass had two bare-agent grading gaps. Each received one unchanged-source mechanical followup using the exact pinned tools and test commands; no model, candidate or blind-review retry occurred. Original records and verdicts remain frozen. The quality table above uses the separately bound recoveries; the raw table below preserves first-pass evidence.

## Mechanical grading recovery

| Bare trial | First-pass gap | One supplemental check | Effect on acceptance |
| --- | --- | --- | --- |
| `bot-12` | Candidate and PR-control setup/timeouts | Both pass 127 tests, zero skips; sandbox verified; 83.2 seconds total | Frozen review still rejects; remains unaccepted |
| `limitless-4769` | Architecture diff timed out after 300 seconds | Pinned scans/diff find no new cycles; 237.1 seconds total | Passing tests plus frozen acceptance now establish acceptance |

Before/after source, provided tests, original result, prepared reference and tool bindings matched exactly. These grading seconds are evaluation overhead, excluded from agent execution time. Both original failures and recovery receipts are retained; no favorable agent implementation was selected.

Recovered grading-view SHA-256: `eb36321971ff46b5e03e60c6f03b702fbb422423b55eec15dede1c1e1c03a56e`.

## Cost and time — separate from quality

The generated tables below contain every measured value and its coverage. Bare used 107,805,668 task tokens and $51.597362 in native CLI list cost; CLAUDE.md used 116,221,158 tokens and $54.186370. Factory’s full totals are unknown. Its observed lower bounds are **237,146,131 tokens and $127.003999**, from 17 tasks with some usage evidence; only 11/20 have final accounting. Missing usage is never zero.

Median task execution time was 419.2 seconds for bare, 377.2 for CLAUDE.md and 1,800.1 for Factory. Total execution time was 11,058.6 / 10,062.1 / 35,704.9 seconds respectively. Times sum invocation elapsed time on a shared host, including contention; they exclude calibration, grading and independent review. These are native reported list costs, not invoices.

## Method and limits

- Twenty curated merged features, selected before outcomes, from Limitless API, Goldengate API and Bitxchange Telegram. Each actual PR passed its acceptance contract; its first-parent base failed for a feature reason.
- Every arm received the same immutable actual-PR tests/support and task. Reference production implementations stayed hidden. CLAUDE.md and Factory received the same frozen repository guide; Factory additionally received the pinned skills snapshot.
- Root and child models were pinned to `claude-opus-5-5`, high effort, CLI `2.1.302`. No global skills, memory or additional MCP tools were treatment inputs. The adapter used a synthetic operator; this does not measure a live discovery/HITL session or the complete hook installation.
- Each invocation had a 30-minute guard, at most 20 question/resume turns per task, and up to three concurrent case drivers. Timeouts were retained. Token values use final cumulative task-session usage; observed lower bounds use the maximum known cumulative value per task, never a sum of resumes.
- Offline unit scope. Goldengate #1002 measures its email-domain unit contract; Docker-backed auth/workspace integration is excluded. Architecture is **cycle-only**: no policies were supplied, so forbidden/unplanned-edge checks were inert. This does not establish policy compliance.
- Fresh independent Codex code-reviewer agents saw anonymous task/base/source/diff packets, without arm labels, metrics or the historical implementations. They used the fixed rubric, froze one verdict per implementation, and all 60 packets matched final packet and result hashes exactly. Review was primarily static with limited offline reproduction; dependencies were absent from source-only packets.
- The initial diagnostic pilot is excluded: hidden novel API names, initialization and dependency-overlay defects made it unsuitable for the quality comparison. The corrected experiment reran the same twenty tasks with the disclosed contract.
- A temporary frozen-framework deletion affected one later Factory attempt. Only missing tracked bytes were restored to the exact pinned tree; 56 prior actor-source hashes matched. That one infrastructure-invalid attempt was archived before review and rerun once; its valid rerun timed out. No successful outcome was selected by retry.
- After all 60 inference runs exited, a tested reporting-only amendment separated quality coverage from accounting gaps and recognized strictly evidenced guard timeouts as non-delivery. Original controller/results/protocol remain archived. No inference inputs, tests, source, reviewer verdicts or quality margin changed.

See the [protocol](../../evals/REAL_PR_BENCHMARK.md), [repository guides](../../evals/REAL_PR_BASELINES.md), and [blind-review rubric](../../evals/REAL_PR_REVIEW.md).

## Actual PR provenance

| Case | Actual merged PR | Base | Reference |
| --- | --- | --- | --- |
| limitless-4720 | [feat(parlay-rfq): expiresAfter filter on the maker quote history](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4720) | `56860867af38` | `63772429cf7e` |
| goldengate-1038 | [[EPD-2083] Add a typed document editor to sopdocument](https://github.com/drawbridgeai/goldengate/pull/1038) | `f816e318c70d` | `86aae3a694b0` |
| bot-1 | [feat(bot): Back button on swap steps](https://github.com/fntch1/bitxchange-tg/pull/1) | `383bb00452e2` | `aa15340a5a34` |
| goldengate-1002 | [[EPD-2211] Limit a workspace to its allowed email domains](https://github.com/drawbridgeai/goldengate/pull/1002) | `5f26ed29710c` | `832cdbe0d688` |
| limitless-4793 | [feat(parlay): let a custom pack hold up to four coins and two stocks](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4793) | `503f68e3867d` | `1dab20e9ac02` |
| goldengate-995 | [[EPD-93] Expose suggested-answer options over the question API](https://github.com/drawbridgeai/goldengate/pull/995) | `815c83fe55b8` | `9a1660fbc8bb` |
| bot-8 | [feat(app): reopen the last order after a reload, and list my orders](https://github.com/fntch1/bitxchange-tg/pull/8) | `2fbce72f3539` | `779c22d68f98` |
| limitless-4798 | [feat(parlay): $100 admin pack stake, payout cut at the ceiling instead of refused](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4798) | `64be9c733f4e` | `e251db9d98d2` |
| goldengate-1010 | [[EPD-2106] Publish evidence and reason on proposed updates and the generate result](https://github.com/drawbridgeai/goldengate/pull/1010) | `e1fdc216e15c` | `f454ad39399e` |
| bot-10 | [feat(bot): /send in a group lets a friend choose how to receive](https://github.com/fntch1/bitxchange-tg/pull/10) | `9f579d42699e` | `4d07495f5ee7` |
| limitless-4795 | [feat(market): adminka external slug check endpoint](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4795) | `188245b04987` | `f9e01de5c9bf` |
| goldengate-957 | [[EPD-2159] Accept a canonical SOP document as cached_draft](https://github.com/drawbridgeai/goldengate/pull/957) | `eec826c1338e` | `77d4baf25470` |
| bot-11 | [feat(bot): the sender finishes a group transfer in their DM](https://github.com/fntch1/bitxchange-tg/pull/11) | `4d07495f5ee7` | `fbf154adcc5d` |
| limitless-4811 | [feat(replication): mint UFC prelim bouts alongside the main card](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4811) | `8a48cb9217a1` | `188245b04987` |
| goldengate-1007 | [[EPD-2106] Give proposal prompts the SOP document and retrieve per step group](https://github.com/drawbridgeai/goldengate/pull/1007) | `d0f8f0ab3f29` | `94c88b5562ec` |
| bot-12 | [feat(bot): a group transfer's line follows its order to the end](https://github.com/fntch1/bitxchange-tg/pull/12) | `fbf154adcc5d` | `f5d7e315bbf3` |
| limitless-4769 | [feat(replication): store job options in JSONB metadata and preview team cards](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4769) | `62f67d450f6f` | `c4b30012e79c` |
| bot-2 | [feat(bot): Back replaces Change amount on the address step](https://github.com/fntch1/bitxchange-tg/pull/2) | `aa15340a5a34` | `9199486a8fb9` |
| limitless-4766 | [feat(replication): add NBA detection and background controls](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4766) | `ed67292fa85d` | `b3ac2a89424b` |
| limitless-4762 | [feat(fees): account direct collateral fees in rewards, rebates and PnL](https://github.com/limitless-labs-group/limitless-exchange-api/pull/4762) | `3a25161aa64b` | `04a296864bec` |

## Excluded diagnostic overhead

| Retained diagnostic set | Records | Observed task token lower bound | Observed CLI list USD lower bound | Usage-observed records |
| --- | ---: | ---: | ---: | ---: |
| Initial invalid pilot | 9 | 20,487,767 | 14.393035 | 8/9 |
| Framework-invalid attempt | 1 | 648,451 | 0.866805 | 1/1 |

These are lower bounds from retained task-session receipts, not complete evaluation totals. The per-trial tables show corrected-run isolation probes separately. Calibration, controller development, coordination, independent Codex review, other probes and repairs have no complete cost ledger and are excluded; the reported task costs do not represent the total cost of building this benchmark.

## Integrity

**Artifact availability:** after publication and verification, the user deleted
the private `.tmp` directory. The measured table, conclusions and hashes survive
in this report; the raw trial logs, source packets and verdict JSON are currently
unavailable for independent re-audit. The benchmark has not been rerun. The
hashes below describe the records verified before that deletion.

- Frozen execution controller SHA-256: `a1b1c45129373684eb2eee3346afec8d5950e78e58223e7141d61660e7f49ae7`.
- Frozen Factory input tree SHA-256: `dea61815d81775996892b65449053a470fb81877f1c64ab5d45746ff66d77101`.
- Frozen manifest SHA-256: `81c270e4caeb293e5d18eca7078879e0391a4b966397b5188ae2d451b2382995`.
- Frozen blind verdicts SHA-256: `f83e9ab22d3cedad6f5054fc92aa6362f8ea50e56c46b4f7d1b87503b0e7161e`.
- Generated measured table SHA-256: `ceb9ab7788bf11478b02b8f309a7c6009a8806836b4f2bc1832914b72ebd4158`.

## Frozen first-pass records

The two original bare grading gaps remain visible here. Use the mechanical recovery table and the quality summary above for the recovered result. The first-pass controller completeness flag below describes this preserved view.

Model: `claude-opus-5-5`; effort: `high`.
Quality determines the comparison. Tokens and time are separate. Archgraph is **cycle-only**: no policies are supplied, so forbidden/unplanned gates are inert. It checks new cycles, not zero baseline debt.
Acceptance contract: provided immutable tests and support, identical in every arm.

| Task | Arm | Outcome | Tests | Archgraph | Blind review | Task tokens | Task USD | Task seconds | Probe tokens | Probe USD | Probe seconds |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| limitless-4720 | bare | complete | pass | no_new_violations | accept | 1105171 | 0.684056 | 219.2 | 80196 | 0.078879 | 7.8 |
| limitless-4720 | claude-md | complete | pass | no_new_violations | accept | 1324376 | 0.688236 | 154.5 | 80371 | 0.080573 | 7.6 |
| limitless-4720 | factory | complete | pass | no_new_violations | accept | 12685432 | 7.895444 | 1464.4 | 83380 | 0.095855 | 9.9 |
| goldengate-1038 | bare | complete | pass | no_new_violations | reject | 2646491 | 2.043196 | 452.2 | 80310 | 0.079938 | 9.6 |
| goldengate-1038 | claude-md | complete | pass | no_new_violations | reject | 3094414 | 2.177509 | 506.1 | 80495 | 0.082130 | 8.3 |
| goldengate-1038 | factory | timeout | pass | no_new_violations | accept | unknown | unknown | 1800.1 | 83079 | 0.091359 | 7.6 |
| bot-1 | bare | complete | pass | no_new_violations | accept | 1059323 | 0.675800 | 149.8 | 80223 | 0.079702 | 11.5 |
| bot-1 | claude-md | complete | pass | no_new_violations | accept | 1375700 | 0.867112 | 138.3 | 80230 | 0.079071 | 11.2 |
| bot-1 | factory | complete | pass | no_new_violations | accept | 12193774 | 7.046884 | 1293.7 | 83004 | 0.091107 | 8.4 |
| goldengate-1002 | bare | complete | pass | no_new_violations | accept | 8267980 | 4.175900 | 745.8 | 80203 | 0.078594 | 10.5 |
| goldengate-1002 | claude-md | complete | pass | no_new_violations | accept | 7952697 | 3.919515 | 776.3 | 80365 | 0.080255 | 8.2 |
| goldengate-1002 | factory | timeout | candidate_error | no_new_violations | reject | unknown | unknown | 1896.7 | 83360 | 0.095346 | 11.4 |
| limitless-4793 | bare | complete | pass | no_new_violations | accept | 1578948 | 0.997244 | 281.4 | 80347 | 0.080987 | 10.1 |
| limitless-4793 | claude-md | complete | pass | no_new_violations | reject | 2020609 | 1.124923 | 198.7 | 80492 | 0.082297 | 11.8 |
| limitless-4793 | factory | complete | pass | no_new_violations | reject | 28075543 | 14.328951 | 2185.9 | 83403 | 0.096069 | 12.3 |
| goldengate-995 | bare | complete | pass | no_new_violations | accept | 912722 | 0.767853 | 179.8 | 80591 | 0.084136 | 15.4 |
| goldengate-995 | claude-md | complete | pass | no_new_violations | accept | 1344851 | 0.907470 | 182.3 | 80405 | 0.081164 | 8.5 |
| goldengate-995 | factory | complete | pass | no_new_violations | accept | 13665430 | 7.843683 | 1251.4 | 83135 | 0.092320 | 10.0 |
| bot-8 | bare | complete | pass | no_new_violations | reject | 2176704 | 1.360543 | 307.9 | 80422 | 0.082235 | 10.5 |
| bot-8 | claude-md | complete | pass | no_new_violations | accept | 2504959 | 1.393567 | 215.1 | 80475 | 0.082644 | 9.8 |
| bot-8 | factory | complete | pass | no_new_violations | accept | 4698974 | 2.832148 | 531.5 | 83125 | 0.092652 | 8.5 |
| limitless-4798 | bare | complete | pass | no_new_violations | accept | 1885963 | 1.109579 | 260.2 | 80165 | 0.078247 | 16.2 |
| limitless-4798 | claude-md | complete | pass | no_new_violations | accept | 2101650 | 1.101369 | 242.4 | 80538 | 0.082884 | 12.6 |
| limitless-4798 | factory | timeout | pass | no_new_violations | accept | unknown | unknown | 1871.1 | 82921 | 0.089515 | 7.8 |
| goldengate-1010 | bare | complete | pass | no_new_violations | accept | 2583453 | 1.467589 | 246.8 | 80300 | 0.080013 | 15.0 |
| goldengate-1010 | claude-md | complete | pass | no_new_violations | accept | 2517081 | 1.558864 | 311.0 | 80221 | 0.078318 | 8.9 |
| goldengate-1010 | factory | complete | pass | no_new_violations | accept | 23814922 | 11.842567 | 1867.3 | 83252 | 0.094021 | 11.9 |
| bot-10 | bare | complete | pass | no_new_violations | reject | 7853277 | 4.054701 | 1329.7 | 80264 | 0.080016 | 10.0 |
| bot-10 | claude-md | complete | pass | no_new_violations | reject | 7824441 | 4.578291 | 1537.9 | 80315 | 0.080464 | 11.3 |
| bot-10 | factory | timeout | assertion_failure | no_new_violations | reject | unknown | unknown | 1906.8 | 82878 | 0.089259 | 9.3 |
| limitless-4795 | bare | complete | pass | no_new_violations | accept | 3286996 | 1.888774 | 490.2 | 80159 | 0.078159 | 8.1 |
| limitless-4795 | claude-md | complete | pass | no_new_violations | accept | 5002512 | 2.463929 | 491.9 | 80547 | 0.083288 | 9.8 |
| limitless-4795 | factory | complete | pass | no_new_violations | reject | 13951869 | 8.174206 | 1340.5 | 83078 | 0.091827 | 9.6 |
| goldengate-957 | bare | complete | pass | no_new_violations | accept | 3554024 | 1.911549 | 386.2 | 80408 | 0.081592 | 10.4 |
| goldengate-957 | claude-md | complete | pass | no_new_violations | accept | 3338799 | 1.866419 | 361.5 | 80513 | 0.082644 | 11.2 |
| goldengate-957 | factory | complete | pass | no_new_violations | accept | 20654089 | 10.518129 | 1649.5 | 83164 | 0.092943 | 9.8 |
| bot-11 | bare | complete | pass | no_new_violations | reject | 4898011 | 3.122130 | 1217.0 | 80403 | 0.082083 | 9.4 |
| bot-11 | claude-md | complete | pass | no_new_violations | reject | 5995598 | 3.667087 | 677.4 | 80471 | 0.082424 | 11.9 |
| bot-11 | factory | timeout | assertion_failure | no_new_violations | reject | unknown | unknown | 1800.1 | 83383 | 0.096523 | 10.6 |
| limitless-4811 | bare | complete | pass | no_new_violations | accept | 592133 | 0.419486 | 88.0 | 80452 | 0.082407 | 13.8 |
| limitless-4811 | claude-md | complete | pass | no_new_violations | accept | 434576 | 0.314403 | 58.1 | 80503 | 0.082568 | 12.0 |
| limitless-4811 | factory | complete | pass | no_new_violations | accept | 14925665 | 7.264552 | 1457.8 | 82932 | 0.089576 | 9.3 |
| goldengate-1007 | bare | complete | pass | no_new_violations | accept | 6049723 | 2.968766 | 530.7 | 80192 | 0.078374 | 10.7 |
| goldengate-1007 | claude-md | complete | pass | no_new_violations | accept | 4473182 | 2.489769 | 392.9 | 80449 | 0.081719 | 10.4 |
| goldengate-1007 | factory | complete | pass | no_new_violations | accept | 34132310 | 19.009155 | 2021.1 | 83006 | 0.090722 | 11.7 |
| bot-12 | bare | complete | setup_error | no_new_violations | reject | 12179866 | 4.914773 | 1022.6 | 80376 | 0.081826 | 8.1 |
| bot-12 | claude-md | complete | pass | no_new_violations | reject | 6598993 | 3.755136 | 654.8 | 80414 | 0.081695 | 13.8 |
| bot-12 | factory | timeout | assertion_failure | no_new_violations | reject | unknown | unknown | 2719.4 | 82982 | 0.091018 | 10.4 |
| limitless-4769 | bare | complete | pass | missing | accept | 16833102 | 6.714541 | 1281.0 | 80406 | 0.081564 | 11.0 |
| limitless-4769 | claude-md | complete | pass | no_new_violations | accept | 12315377 | 5.513744 | 888.7 | 159940 | 0.149601 | 22.3 |
| limitless-4769 | factory | timeout | pass | no_new_violations | accept | unknown | unknown | 1800.1 | 83238 | 0.094051 | 9.0 |
| bot-2 | bare | complete | pass | no_new_violations | accept | 386742 | 0.280335 | 80.7 | 80342 | 0.081071 | 9.0 |
| bot-2 | claude-md | complete | pass | no_new_violations | accept | 544346 | 0.342413 | 108.7 | 80274 | 0.079795 | 9.9 |
| bot-2 | factory | complete | pass | no_new_violations | accept | 3453665 | 2.038074 | 455.2 | 83395 | 0.096743 | 9.7 |
| limitless-4766 | bare | complete | pass | no_new_violations | accept | 20680684 | 7.779414 | 1196.3 | 80179 | 0.078464 | 8.2 |
| limitless-4766 | claude-md | complete | pass | no_new_violations | accept | 35175345 | 10.848148 | 1507.1 | 80361 | 0.080565 | 17.5 |
| limitless-4766 | factory | timeout | candidate_error | no_new_violations | reject | unknown | unknown | 1904.0 | 83208 | 0.093400 | 9.1 |
| limitless-4762 | bare | complete | pass | no_new_violations | reject | 9274355 | 4.261135 | 593.1 | 80298 | 0.079992 | 8.2 |
| limitless-4762 | claude-md | complete | pass | no_new_violations | reject | 10281652 | 4.608465 | 658.6 | 80198 | 0.335000 | 7.1 |
| limitless-4762 | factory | timeout | assertion_failure | no_new_violations | reject | unknown | unknown | 4488.5 | 83246 | 0.093936 | 9.0 |

| Arm | Task tokens total / median | Task USD total / median | Task seconds total / median |
| --- | ---: | ---: | ---: |
| bare | 107805668 / 2966744 | 51.597362 / 1.900161 | 11058.6 / 419.2 |
| claude-md | 116221158 / 3216606 | 54.186370 / 2.021964 | 10062.1 / 377.2 |
| factory | unknown | unknown | 35704.9 / 1800.1 |

| Arm | Quality coverage | Token coverage | USD coverage | Seconds coverage | Observed task token lower bound | Observed task USD lower bound |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bare | 18/20 | 20/20 | 20/20 | 20/20 | 107805668 (20/20 tasks observed) | 51.597362 (20/20 tasks observed) |
| claude-md | 20/20 | 20/20 | 20/20 | 20/20 | 116221158 (20/20 tasks observed) | 54.186370 (20/20 tasks observed) |
| factory | 20/20 | 11/20 | 11/20 | 20/20 | 237146131 (17/20 tasks observed) | 127.003999 (17/20 tasks observed) |

Observed lower bounds use the largest known cumulative task-session value per task, never summed across resumes. They are not complete totals; wholly unobserved tasks remain unknown.
A verified execution-guard timeout is failure to deliver, even when final native usage is missing. This exception does not establish exhaustive native model-call accounting.
Acceptance requires completed delivery, passing acceptance tests, no new archgraph violations and blind acceptance.
Task tokens and USD use the final cumulative task-session usage; task seconds sum its turns. USD is the native CLI-reported value, not an invoice claim; missing values and incomplete aggregates stay unknown. Separate isolation probes are shown explicitly and excluded from task metrics. Raw records retain total observed tokens and seconds, including failed probes.

**Incomplete evidence: no winner.** All 20–30 tasks × 3 arms need test, architecture, blind-review and valid treatment/isolation coverage. Accounting gaps are reported separately.

This single paired 20–30-task trial is descriptive; it does not establish statistical superiority.
