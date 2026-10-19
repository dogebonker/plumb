# Retro metrics

What `/factory-retro` measures for a change, and where each number comes from. Normalize per slice where a count grows with size. Queries that work on Pond, with their outputs: `docs/research/retro/C-signals.md` (appendix) in the factory repository.

| ID | Metric | Source |
| --- | --- | --- |
| M1 | Questions to the user, per step: AskUserQuestion items plus free-text user turns. Headless: approver comments after each `waiting_since` | Pond, split at the `step_start` times in `history` (the autopilot orchestrator's session holds every step's questions, and reconcile), or at the `/factory-*` command rows when `history` has none. A user turn counts only when its text does not start with `<` and is not a skill body or an agent hand-back |
| M2 | Wall clock and minutes waiting for the user, per step | Pond: `step_start` times, or command timestamps; AskUserQuestion call to its result |
| M3 | Observed tokens per task and named skill: invocation count, disjoint input/cache-read/cache-write/output, total and coverage; parent/resume overlap excluded | `usage.jsonl` and `python3 <kit>/usage.py report --ledger <task>/usage.jsonl`; provider logs retained by caller/runner. Missing attribution stays unknown |
| M4 | Interface panel rounds, cards per round, share overruled, cards left unanswered | `panel_round` events, `challenges.md` |
| M5 | Rework: gate send-backs and reopens by gate and cause; rewinds, red retries, green retries, check retries and executor stops by reason, per slice (a rewind caused by a red retry counts once, as the retry) | `history` |
| M6 | Review findings per slice by tag and outcome; tags already seen in this repository's earlier changes, including `[adr/NNNN]` | `slices/*/review.md`, including Phase 1 ADR enforcement failures; deduplicate findings repeated in the agent/card sections |
| M7 | Whether the factory hook was installed | `~/.claude/settings.json`, and the repository's `.claude/settings.json` and `.claude/settings.local.json` |
| M8 | Track proposed against track chosen | `track_proposed`, `track` |
| M9 | Model calls and input/cache/output classes per stage; rework calls separately from initial work | Deduplicated provider message ids, step reports and benchmark progress; incomplete output is a lower bound |
| M10 | Actual human review/correction minutes and follow-up rounds, alongside independent issues by severity | Human-recorded measurements and independent review; questions and scripted approvals are proxies, never minutes |
| M11 | Context tools actually called, raw/returned/retrieved output sizes and additional retrieval turns | Tool-call ids and retained raw logs; enabled hooks alone do not establish compression savings |
| M12 | Defect origin per stage and slice: wrong or silent gate document, changed frozen interface, or build nonconformance; evidence coverage and unknown origins separately | Unique fixed/auto-fixed/held findings in `slices/*/review.md`, every failed line in `acceptance.md`, their anchors and approved gate revisions, and reconcile drafts/decisions; `drift.md` supports repeated ADR-drift proposals |
| M13 | Confirmed post-merge defects per fully observed merged feature, by arm and declared window; incomplete coverage separately | Explicit incident IDs, feature/merge SHA, detection time, attribution and continuous observation evidence in `outcomes.json`; `<kit>/outcomes.py report` |
| M14 | Detection-to-recovery seconds, with unresolved incidents right-censored at as-of | M13 incident records, recovery evidence and report cutoff |
| M15 | Product adoption against a named eligible population and successful event; unknown without evidence | User-defined event/population, deduplicated adopted/eligible counts, cutoff and analytics evidence in `outcomes.json` |

## M12: defect origin

Count each underlying defect once across mechanical findings, review cards, repair rounds and acceptance failures; retain its source references and outcome. Include fixed, auto-fixed and held findings and every acceptance failure, including unresolved ones. A failure is not automatically the build's fault. Attribute only from the anchor and the approved-versus-reconcile evidence:

- **Wrong gate document**: cite its stage/path, approved line/revision and the user's later correction of that line at reconcile. The finding contradicted the approved intent, and that intent was wrong.
- **Silent gate document**: cite its stage/path, the missing promise and the new constraint or ADR the user adopted at reconcile. A missing anchor alone cannot establish silence or authorize a requirement.
- **Interface**: cite the frozen contract and its approved change. Do not also count the same defect as a wrong architecture line.
- **Build**: cite the unchanged, correct document/contract and the contradicting implementation or failed example.
- **Unknown**: missing evidence or unresolved authority leaves the origin unknown, with the evidence needed; never infer an origin from a tag or a reviewer guess.

Keep one primary origin for totals; cross-stage contributing causes may be links without another count. Report a compact evidence table: defect/source IDs, affected slices, origin stage, wrong/silent/interface/build/unknown, approved anchor, reconcile correction or unchanged-contract proof, outcome. Normalize stage counts by completed slices, count a cross-slice defect once for the change total, and use the existing trend rule against this repository's earlier changes. Also show attribution coverage so a small known sample cannot imply a reliable ranking.

Among evidenced wrong/silent defects, name the stage with the greatest count as a **proposal** for the next review-budget allocation (ties stay ties); the user decides, and no budget or workflow changes automatically. With no evidenced wrong/silent defects, make no stage recommendation. Read current and previous `drift.md` files: two distinct changes with evidenced drift of the same accepted ADR/Decision revision justify proposing a mechanical `Enforced by` rule or test, with both citations; repeated reports in one change count once. A superseded Decision starts a new comparison. Missing history is unknown, not evidence of no drift.

## Token cost

Run the usage report for every task, even when the full retrospective is skipped.
List the largest observed skills first and separate initial work from repair invocations.
Unknown coverage is a measurement gap, not a cheap skill. Never sum child totals into
an inclusive parent or add cumulative resume snapshots. Use the receipt helper.

The old multi-million-token budgets were guesses, not measured acceptable costs;
they are retired. Compare against the last three comparable completed tasks of the
same size/track/model and quality bar when available; otherwise report raw values
without a savings verdict. Size, selected design_lenses and retries explain the result.
Actual invoice cost and model-call counts remain unknown unless separately observed;
cache tokens and uncached input do not have the same price. No extra model call or
mandatory full retro is justified merely to format these numbers.

## Finding the change's sessions

The `step_start` events name each step's session. Without them, scan Pond for the `/factory-*` command rows whose arguments carry the slug: Pond's project filter is unreliable, because a step can run from a session started in another directory. Say how far Pond has synced; a session it has not synced yet is reported as missing, not as zero.

## The trend

Each change's numbers go in its `retro.md`, with the factory commits from its `step_start` events and the model when known. Compare each metric with the median of this repository's previous 5 changes of the same track, read from their `retro.md` files in git (in ignored mode, from the working tree). With fewer than 3, show the values without a verdict. Call a move better or worse only when it leaves the range of those previous changes, and say when the factory commit or the model changed between them.

## M13–M15: outcomes after merge

These are outcome metrics, separate from violations caught before merge. Use explicit
observations with `python3 <kit>/outcomes.py report --input <change>/outcomes.json`.
The helper reads local JSON and prints a report; it does not collect telemetry or
create incidents. Keep its input and evidence with `retro.md`. No new model call is
needed to calculate it.

- **M13 — escaped defects per merged feature.** Pin feature ID, full merge SHA,
  merge timestamp, arm and a predeclared observation window (for example 7 days).
  Count unique confirmed incident IDs detected in `[merge, merge + window)`;
  repeated reports of one incident count once. Suspected incidents remain separate.
  A feature enters the rate denominator only when the entire window has elapsed
  and confirmed evidence covers observation continuously from merge through its
  end. Report all/merged/fully observed feature counts per arm and exclusions.
  Unmerged, immature or unobserved features have unknown rates, never zero.
  Partial confirmed incidents are lower bounds. Discovery after the window belongs
  to a later-window report, not a silently changed original window.
- **M14 — time to recovery.** For each confirmed M13 incident, report elapsed
  detection-to-recovery seconds with the recovery evidence, even if recovery falls
  after the defect observation window. Unresolved incidents are right-censored at
  the report's `as_of`: show elapsed ongoing time and unknown recovery time. Do
  not turn an ongoing incident into zero or omit it from a favorable median. If a
  closed-incident median is shown, label it and show unresolved counts alongside.
  Detection time is not necessarily incident onset; do not call this availability.
- **M15 — adoption.** Name the user-defined successful event, eligible population,
  observation cutoff and evidence; report adopted unique eligible units divided by
  eligible units for that same population/window. The input counts must already
  deduplicate the chosen unit (user, account or team). Missing data, an undefined
  event/population, or a zero denominator means unknown adoption. Do not substitute
  agent invocations, pageviews or a merged commit for product adoption. Keep
  differently defined populations/events separate; do not pool their rates.

The JSON input has `as_of` (timezone-aware timestamp), `window_days`, `features`
and `incidents` lists. Each feature has `id`, `arm`, `merge_sha` and `merged_at`
(the last two are both null before merge). Optional `observation` is
`{through, confidence, evidence}`: confidence is `confirmed` or `reported` and
attests continuous incident observation from merge through that timestamp.
Optional `adoption` is `{event, population, eligible, adopted, through, confidence,
evidence}` with the same confidence vocabulary. Each incident has `id`, `feature`,
`merge_sha`, `detected_at`, `recovered_at` (null while unresolved), `confidence`
(`confirmed` or `suspected`) and `evidence` supporting detection, attribution and,
when present, recovery. Timestamps after `as_of`, invalid ordering, conflicting
incident IDs and wrong feature/SHA bindings are rejected. Evidence is a reference
to retained facts, not a model's estimate; the helper validates the records, not
the truth or completeness of an external incident system.

Keep the honest **agent + a good CLAUDE.md** control, alongside bare agent and
Factory where available. Compare quality only over comparable cohorts with the
same window, surveillance, feature size/stack and incident definition. The
historical PR benchmark is a delivery-quality baseline, not production escaped-
defect or adoption telemetry. Show tokens, provider cost and wall time separately;
no combined cost-quality score or new benchmark run is needed for these metrics.
Use the existing trend rule only after comparable observed features exist. A
missing control cohort or immature pilot supports no claim of outcome improvement.
