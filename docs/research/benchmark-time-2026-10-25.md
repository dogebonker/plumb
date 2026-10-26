# Where Factory's benchmark time went — 25 October 2026

P0 of the [reusable workflow plan](reusable-workflow-plan-2026-10-25.md). Factory is Plumb's name at the time of the [2026-10-19 benchmark](real-pr-benchmark-2026-10-19.md).

**Result.** Planning took **46.7%** of Factory's 35,705 task seconds, so the plan's gate (stop when planning is under a quarter) does not stop it. The loss is concentrated on the **critical track**: its 9 tasks hold 8 of Factory's 9 timeouts and 2 of 9 accepted, against 5 of 9 for each control. On the other 11 tasks Factory accepted **10 of 11**, one more than each control, at a median of 1,464 s against 247 s (bare) and 199 s (CLAUDE.md).

| Tasks | Bare | CLAUDE.md | Factory |
| --- | --- | --- | --- |
| 11 small and standard | 9/11 accepted, median 247 s | 9/11, median 199 s | **10/11**, median 1,464 s, 1 timeout |
| 9 critical | 5/9, median 1,023 s | 5/9, median 677 s | **2/9**, median 1,897 s, 8 timeouts |

"Critical" here is Factory triage's track. The controls had no tracks; their rows are the same tasks.

## Evidence

The raw run directory was deleted. The native Claude Code transcripts of the Factory arm remain under `~/.claude/projects/*pr-benchmark-actors-azzaa964-*-factory-work/`, one folder per task. Every folder's isolation probe names `.tmp/pr-benchmark-private/run-corrected`, the scored run. limitless-4766 holds two task attempts on 2026-10-19; the later one (13:44 UTC) is the scored one, and the earlier (13:01, 1,549 s) is not counted.

**Validation.** Each task's transcript span (first to last event of the scored session; for a timeout, up to the last event of its own subagents, which kept running inside the killed turn) is within 1% of the report's task seconds for all 20 tasks (99% to 100%). These are the scored transcripts, not the excluded pilot.

## Per task

Planning is the time before the first build step: triage and the product, architecture, security, interface, slices and plan stages. Delivery is everything after: build, review, acceptance and reconcile. Turns are user prompts in the scored session, the first request plus each question or resume turn; the benchmark's operator answers instantly, so question time is inside these seconds and adds no waiting. No task used `AskUserQuestion`; questions go through the benchmark's JSON reply.

| Task | D1 route | Triage track | Outcome | Blind review | Report s | Transcript s (match) | Planning s (share) | Turns | Stage at timeout | Seconds by stage |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| bot-1 | feature | small | complete | accept | 1294 | 1293 (100%) | 327 (25%) | 1 |  | build 539, review 418, triage 264, slices 62, reconcile 9 |
| bot-10 | critical | critical | timeout | reject | 1907 | 1879 (99%) | 1907 (100%) | 2 | interface | architecture 627, interface 505, triage 285, security 275, product 215 |
| bot-11 | critical | critical | timeout | reject | 1800 | 1793 (100%) | 1016 (56%) | 1 | build | build 784, triage 409, interface 256, architecture 222, product 53, security 43, slices 32 |
| bot-12 | critical | critical | timeout | reject | 2719 | 2717 (100%) | 927 (34%) | 7 | build | build 1248, review 544, interface 282, triage 247, architecture 202, product 86, slices 62, security 48 |
| bot-2 | feature | small | complete | accept | 455 | 454 (100%) | 182 (40%) | 1 |  | triage 182, review 162, build 111 |
| bot-8 | feature | standard | complete | accept | 532 | 531 (100%) | 192 (36%) | 1 |  | build 196, triage 192, review 143 |
| goldengate-1002 | critical | critical | timeout | reject | 1897 | 1889 (100%) | 1897 (100%) | 2 | architecture | architecture 938, triage 836, product 122 |
| goldengate-1007 | feature | standard | complete | accept | 2021 | 2019 (100%) | 346 (17%) | 10 |  | build 806, review 792, triage 222, plan 124, reconcile 77 |
| goldengate-1010 | feature | standard | complete | accept | 1867 | 1866 (100%) | 454 (24%) | 8 |  | review 798, build 534, triage 401, reconcile 81, plan 52 |
| goldengate-1038 | feature | standard | timeout | accept | 1800 | 1794 (100%) | 220 (12%) | 4 | review | review 845, build 735, plan 137, triage 83 |
| goldengate-957 | feature | standard | complete | accept | 1650 | 1648 (100%) | 290 (18%) | 4 |  | build 738, review 580, triage 261, reconcile 41, plan 29 |
| goldengate-995 | feature | standard | complete | accept | 1251 | 1250 (100%) | 331 (26%) | 7 |  | review 498, build 378, triage 224, plan 107, reconcile 44 |
| limitless-4720 | feature | standard | complete | accept | 1464 | 1463 (100%) | 302 (21%) | 7 |  | review 625, build 473, triage 169, plan 133, reconcile 64 |
| limitless-4762 | critical | critical | timeout | reject | 4488 | 4458 (99%) | 2738 (61%) | 7 | build | build 1712, architecture 850, interface 828, product 287, security 275, slices 256, triage 242, review 39 |
| limitless-4766 | critical | critical | timeout | reject | 1904 | 1903 (100%) | 1904 (100%) | 2 | interface | architecture 1288, triage 252, security 223, product 137, interface 4 |
| limitless-4769 | critical | critical | timeout | accept | 1800 | 1782 (99%) | 622 (35%) | 1 | review | build 667, triage 622, review 511 |
| limitless-4793 | feature | standard | complete | reject | 2186 | 2185 (100%) | 612 (28%) | 12 |  | review 882, build 614, plan 430, triage 181, reconcile 78 |
| limitless-4795 | critical | critical | complete | reject | 1340 | 1339 (100%) | 373 (28%) | 5 |  | build 908, triage 373, review 60 |
| limitless-4798 | critical | critical | timeout | accept | 1871 | 1857 (99%) | 1648 (88%) | 2 | build | interface 492, architecture 459, slices 243, build 223, security 200, triage 148, product 105 |
| limitless-4811 | feature | small | complete | accept | 1458 | 1457 (100%) | 405 (28%) | 10 |  | review 576, build 390, triage 362, reconcile 87, slices 43 |

**Per stage, all 20 tasks:** build 11,058 s (31%), review 7,474 (21%), triage 5,957 (17%), architecture 4,587 (13%), interface 2,367 (7%), security 1,065 (3%), plan 1,013 (3%), product 1,004 (3%), slices 699 (2%), reconcile 481 (1%).

**Per track:**

| Track | Tasks | Timeouts | Accepted | Median s | Planning share | Median triage s | Median turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| small | 3 | 0 | 3 | 1,294 | 29% | 264 | 1 |
| standard | 8 | 1 | 7 | 1,725 | 22% | 207 | 7 |
| critical | 9 | 8 | 2 | 1,897 | 66% | 285 | 2 |

**Stage running at a timeout:** build 4, interface 2, review 2, architecture 1.

## Findings

- F1. **The critical track decides the result.** Every timeout but one is critical. Four critical tasks spent at least 88% of their time planning, three of them never reaching build; their architecture and interface gate agents alone ran 459 to 1,288 s. All nine are money or payment changes in an exchange or a payments bot, which decision 6 sends to critical.
- F2. **Outside critical, quality is already ahead and time is the cost.** 10 of 11 accepted against 9 for each control, at six to seven times their median time. There planning is 22% to 29%; build and review are the larger share.
- F3. **Triage is a fixed cost of three to five minutes.** Its median is 207 to 285 s on every track and 17% of all Factory time. It reads the repository, records a profile and runs the baseline twice before choosing a track.
- F4. **Questions cost turns, not waiting.** The instant operator hides human wait, so D4 (answer facts before asking) can save only the model time spent writing and resuming those turns: a median of 7 turns on standard, 1 to 2 elsewhere.
- F5. **D1's work-type routing has nothing to route here.** All 20 PRs are features; the protocol selects them. D1's critical check would give the same tracks as triage did.

## What this means for P1 to P4

The gate passes, but F1 says the plan aims at the smaller part of the loss. D1 keeps the critical track "unchanged", and D3 tunes thresholds that F1 shows are not the cause: on these tasks the critical decision was right by decision 6, and the track itself timed out. P3's Goldfish is planned for standard only. A change to how the critical track plans (for example one discovery pass and one approval with the threat model folded in, as `/plumb-plan` does for standard) would reach 8 of the 9 timeouts; the planned P1 to P3 reach one.

## Limits

- Stage boundaries come from the conductor's own markers: Skill invocations, `step_start` lines it writes into `status.yaml`, gate, executor and reviewer agents it dispatches, and its first source edit. Markers written at a stage's commit put some seconds in the neighbouring stage; triage's marker is written at its end and is ignored. The planning/delivery split depends only on the first build marker and is the robust figure; per-stage seconds are approximate.
- Background agents overlap the conductor; seconds are the conductor's wall time, not model time.
- Two critical tasks (limitless-4769, limitless-4795) show no separate gate agents; their planning sits inside triage's seconds.
- Seconds and outcomes come from the report; the transcripts only attribute them.

## Method

[benchmark-time-2026-10-25/measure.py](benchmark-time-2026-10-25/measure.py) applies the rules above: `python3 docs/research/benchmark-time-2026-10-25/measure.py docs/research/real-pr-benchmark-2026-10-19.md`. It reads only the transcripts on the machine that ran the benchmark. Inputs: the report's per-task table (`real-pr-benchmark-2026-10-19.md:108-169`) and the transcript folders named above.
