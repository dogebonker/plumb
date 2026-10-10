# factory-ci: how to measure "why is my CI so slow?"

Lane B for S10. Date: 2026-10-11. Sources: docs.github.com REST and billing pages, the GitHub changelog and pricing pages, read live; then a read-only pull of 30 days of runs and jobs from two public repositories.

## Verdict

Everything the skill needs is in the REST API with a read-only token: runs, jobs and steps with timestamps, attempts, required checks, merge queue events. About one API call per workflow run, so a 30-day sample costs a few hundred calls out of 5,000 per hour. The billing endpoints are not needed and mostly gone; minutes and dollars are computed from job durations and the published per-SKU prices.

The live test changed three assumptions:

- **Queue time is invisible at run level.** `run_started_at` equals `created_at` on every first attempt (502 of 502). Queue time only shows per job, as `started_at - created_at`.
- **Whole-run wall clock is too noisy for short before/after tests.** Two random halves of the same unchanged history differ by up to 21% (10 runs per side) and 14 to 31% (20 runs per side), at the 95th percentile. Measured claims must be made on the changed job, from a stratified sample, against this noise floor.
- **The critical path can be recovered from timestamps alone.** A job's `created_at` is when its `needs:` were met, so walking back from the last job to finish reproduces the `needs:` graph. The `axum` workflow file confirms it.

## Key numbers from the live test

| Measure | tokio-rs/axum | python-poetry/poetry |
| --- | --- | --- |
| Runs, 2026-09-10..2026-10-10 | 176 | 333 |
| API calls to pull runs + all job attempts | 178 | 342 |
| Main workflow, successful runs | CI, n=114 | Tests, n=168 (117 full matrix, 51 path-filtered) |
| Wall clock, median / p90 | 3.4m / 4.7m | 5.6m / 7.6m (full matrix only) |
| Runner time per run, median | 13.0m | 62.0m (all), 47 to 58 jobs per full run |
| Job queue, median / p90 | 3s / 4s | ubuntu 3s / 4s; macOS-15 97s / 220s |
| Critical path, as inferred | `check (examples)` then `test-msrv` | matrix, then `Status` aggregator; macOS queue dominates |
| Time to all required checks green per PR commit, median / p90 | 3.4m / 4.7m (17 required contexts) | 5.3m / 7.8m (`Status`) |
| Minutes in failed runs + earlier attempts + cancelled | 16.9% | 26.1% |
| Per-job round-up to whole minutes, as if billed | +62% | +37% |
| A/A noise, whole-run median, 20 runs per side (95th pct) | 30.9% | 14.5% (full matrix only) |
| A/A noise, one job, 20 runs per side | 11.4% (`cargo-hack`) | 9.5% (one Ubuntu pytest job) |

## Findings

### Data sources

**F1. Runs: `GET /repos/{o}/{r}/actions/runs`, at most 1,000 results per filtered query.** The docs say the endpoint "will return up to 1,000 results for each search" when filtering by `actor, branch, check_suite_id, created, event, head_sha, status` ([workflow runs](https://docs.github.com/en/rest/actions/workflow-runs)). Checked live on cli/cli with `created=2026-09-10..2026-10-10`: page 10 returns 100 runs, page 11 returns 0, and `total_count` says 2500, which is also wrong. The same query without a filter paginates past 1,000 (page 11 returned 100). Rule: split the window by day, or smaller, until every slice is under 1,000. `per_page` max is 100.

```
$ gh api "repos/cli/cli/actions/runs?per_page=100&page=11&created=2026-09-10..2026-10-10" --jq '"total_count=\(.total_count) returned=\(.workflow_runs|length)"'
total_count=0 returned=0
$ ... page=10 ...
total_count=2500 returned=100
```

**F2. Jobs and steps: `GET .../actions/runs/{id}/jobs?filter=all`.** `filter=all` returns jobs of every attempt, `latest` (the default) only the last ([workflow jobs](https://docs.github.com/en/rest/actions/workflow-jobs)). Each job has `created_at`, `started_at`, `completed_at`, `run_attempt`, `labels`, `runner_name`, `runner_group_name`, `conclusion`, and `steps[]` with `started_at` and `completed_at`. Per-attempt jobs are also at `.../runs/{id}/attempts/{n}/jobs`, and a run attempt at `.../runs/{id}/attempts/{n}`. One call per run covers up to 100 job records; poetry needed a second page on a few runs (342 calls for 333 runs plus 4 list pages).

**F3. `/timing` is "closing down" but still answers.** The docs mark "Get workflow run usage" (`.../runs/{id}/timing`) as "in the process of closing down" ([workflow runs](https://docs.github.com/en/rest/actions/workflow-runs)); the changelog tied it to the move of Team and Enterprise customers to the new billing platform by 2025-04-01 ([changelog 2025-02-02](https://github.blog/changelog/2025-02-02-actions-get-workflow-usage-and-get-workflow-run-usage-endpoints-closing-down)). Live, it returns 200 under both API versions, with `run_duration_ms` and `billable.*.total_ms = 0` for a public repository:

```
$ gh api -H 'X-GitHub-Api-Version: 2026-03-10' repos/tokio-rs/axum/actions/runs/37993631549/timing
{"billable":{"UBUNTU":{"total_ms":0,"jobs":2,...}},"run_duration_ms":116000}
```

Do not depend on it. Everything it gives is derivable from job timestamps (F11).

**F4. Billing API: per SKU and repository, not per workflow.** The product-specific `/settings/billing/actions` endpoints are retired ([changelog 2025-09-26](https://github.blog/changelog/2025-09-25-product-specific-billing-apis-are-closing-down)). The replacement `GET /organizations/{org}/settings/billing/usage` (and `/users/{u}/...`) returns `date, product, sku, quantity, unitType, pricePerUnit, grossAmount, discountAmount, netAmount, repositoryName`, filtered by `year, month, day`; a `usage/summary` variant adds `repository, product, sku` filters and is in public preview ([billing usage](https://docs.github.com/en/rest/billing/usage)). Organization endpoints need an org administrator. Per-workflow detail is only in the usage report downloaded from the UI. Use: reconciliation of the computed dollars when the user is an admin; never the primary source.

**F5. `gh run list/view --json` lacks job queue time and runner labels.** `gh run list` fields: `attempt, conclusion, createdAt, databaseId, displayTitle, event, headBranch, headSha, name, number, startedAt, status, updatedAt, url, workflowDatabaseId, workflowName`. `gh run view --json jobs` gives per job `completedAt, conclusion, databaseId, name, startedAt, status, url` and steps, but no job `createdAt` and no `labels` (checked on axum run 37993631549). `gh run list --created` hits the same 1,000 cap. Use `gh api` for jobs.

**F6. Required checks: readable without admin, from two places, and not always from Actions.**
- `GET /repos/{o}/{r}/branches/{b}/protection` returns 404 to a non-admin (cli/cli). `GET /repos/{o}/{r}/branches/{b}` returns `protection.required_status_checks.checks[]` (`context`, `app_id`) to any reader.
- Rulesets: `GET /repos/{o}/{r}/rules/branches/{b}` returns active rules, including `required_status_checks` with `context` and `integration_id` ([rules](https://docs.github.com/en/rest/repos/rules)). Poetry has both: classic protection requires `pre-commit.ci - pr` (app 68672) and a ruleset requires `Status` (integration 15368, GitHub Actions). The skill must read and union both.
- A required context can be a commit status rather than a check run. Poetry's `pre-commit.ci - pr` appears only in `GET .../commits/{sha}/status`, not in check runs. Time-to-green must read `commits/{sha}/check-runs` (paged; only the 1,000 most recent suites per ref; 1,000 runs per name kept, [check runs](https://docs.github.com/en/rest/checks/runs)) plus `commits/{sha}/status`.
- Actions job names are the check-run names (`build (ubuntu-latest)`, `test-versions (beta, .)`), so required contexts map to jobs by name, with app id 15368.

**F7. Merge queue is measurable.** Runs triggered by the queue have `event=merge_group` and `head_branch = gh-readonly-queue/{base}/pr-{N}-{sha}` (bevyengine/bevy: 729 such runs in 30 days; github/docs: 322). Queue entry and exit are in the issue timeline REST endpoint (`added_to_merge_queue`, `removed_from_merge_queue`) and GraphQL (`AddedToMergeQueueEvent`, `RemovedFromMergeQueueEvent{reason}`). Bevy PR 26000: added 00:50:35, first queue run +0.3m, merged 01:34:37, 44.0m in queue. Over 12 sampled bevy PRs, queue CI took 33.5 to 98.9 minutes, so on that repo the queue, not the PR checks, is the merge latency. Queue settings (`max_entries_to_build`, `min_entries_to_merge_wait_minutes`, `grouping_strategy`, `check_response_timeout_minutes`) are in the ruleset `merge_queue` rule ([rules](https://docs.github.com/en/rest/repos/rules), [merge queue docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)).

**F8. Rate limits: a 30-day sample is cheap but slow if serial.** 5,000 requests per hour for a user token, 15,000 for Enterprise Cloud apps, 1,000 per hour per repository for `GITHUB_TOKEN`; secondary limits of 100 concurrent requests and 900 points per minute (GET = 1) ([rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)). Observed: about 1.02 calls per run. Serial `gh api` calls took about 2.6 s each (poetry: 342 calls in about 15 minutes). A repository with 3,000 runs a month costs about 3,000 calls: inside one hour's budget, but it needs 4 to 8 parallel workers and a cap below 900 per minute. Note: `gh api rate_limit` reported `used: 0` throughout while response headers showed `X-Ratelimit-Used: 610`; read the headers.

**F9. Retention: plan for 90 days on public repositories now.** Since 2026-10-01, checks, workflow runs and commit statuses follow the same retention setting as logs and artifacts, with a 90-day maximum on public repositories ([changelog 2026-10-01](https://github.blog/changelog/2026-10-01-actions-retention-now-covers-checks-runs-and-statuses)). Logs and artifacts default to 90 days, configurable 1 to 90 days (public) or 1 to 400 days (private); before that date runs were kept "400+ days" ([repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)). Observed on 2026-10-11: cli/cli still lists runs back to between 2025-08-20 and 2025-09-01 (zero runs with `created<2025-08-20`, 484 with `created<2025-09-01`), so cleanup had not caught up. A 30-day window is safe everywhere. A baseline older than 90 days may already be gone. Org Insights "Actions Performance Metrics" shows queue time and failure rate for up to one year on all Cloud plans, in the UI only, with no API ([changelog 2025-03-14](https://github.blog/changelog/2025-03-14-actions-performance-metrics-are-generally-available-and-enterprise-level-metrics-are-in-public-preview)).

### What to measure

**F10. Queue: per job only.** On all 502 first-attempt runs, `run_started_at - created_at = 0`. Job `created_at` is when the job became runnable. In axum run 37960174589, the eight jobs with `needs: check` were created at +185s, one second after `check (examples)` finished at +184s. So `started_at - created_at` is pure runner wait. It found the main problem in poetry: macOS-15 jobs wait a median 97s (p90 220s, max 684s) while Ubuntu and Windows wait 3s. Each full run starts at least 12 macOS jobs (1,404 macos-15 jobs over 117 runs), and standard macOS runners are capped at 5 concurrent jobs on Free, Pro and Team (50 on Enterprise; 20/40/60/500 total) ([limits](https://docs.github.com/en/actions/reference/limits)). On the critical path, queue is a median 41.7% of poetry's Tests time and 3.0% of axum's CI time.

**F11. Wall clock, runner time and their ratio.** Wall = last job `completed_at` minus first job `created_at` within the final attempt. This agrees with `updated_at - run_started_at` to within 1 to 2s at median. Runner time = sum of `completed_at - started_at` over jobs that ran (conclusion not `skipped`). The ratio shows fan-out: 0.26 for axum (17 jobs), 0.09 for poetry (47 jobs). Fan-out buys wall clock with minutes. On private repositories each job is rounded up to a whole minute ([runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)), which added 62% to axum's minutes and 37% to poetry's, so short matrix legs cost more than their seconds.

**F12. Critical path: from timestamps, then checked against `needs:`.** Algorithm: start at the job that finished last; step to the job with the latest `completed_at` that is not after the current job's `created_at` (2s tolerance, and strictly earlier completion to avoid cycles between sub-2s jobs); repeat. On axum it gives `check (examples)` then `test-msrv` in 96 of 114 runs, which matches `test-msrv: needs: check` in `.github/workflows/CI.yml`. The YAML gives the exact graph; timestamps give the observed one, including queue waits that the YAML cannot show. Use both and report disagreements. For merge gating, the path ends at the last required context (F6), not the last job: an aggregator job such as poetry's `Status` makes them the same.

**F13. Stratify before any statistic.** Poetry's Tests mixes 51 path-filtered runs (under 30s, `Detect changed files` only) with 117 full-matrix runs (about 5.6m). Unstratified, CV is 0.80 and the A/A noise at 20 runs per side is 60%. Full-matrix only, CV is 0.43 and the noise is 14.5%. Axum CI is bimodal for another reason: in slow runs (n=50), `check (examples)` takes 1.88m against 0.52m and `test-versions (beta, examples)` 2.35m against 0.70m, the signature of a cache miss. Strata: workflow, trigger event, set of jobs that actually ran, and runner label. A bimodal stratum is itself a finding (cache hit rate) and should be reported as two modes, not one median. Time of day showed no material effect in poetry (5.47m to 5.90m medians across 6-hour UTC buckets).

**F14. Reruns, failures, cancellations.** Minutes by outcome:
- axum: 83.1% successful final attempts, 11.0% failed runs, 5.0% earlier attempts, 0.9% cancelled.
- poetry: 73.9% successful, 20.1% failed, 3.0% earlier attempts, 3.0% cancelled.

Rerun rate (`run_attempt > 1`) is 1.1% and 1.5%, close to the 3.2% of builds rerun in 1,960 Java projects on GitHub Actions, where 67.7% of reruns were flaky ([Ge and Zhang 2026, arXiv 2602.02307](https://arxiv.org/abs/2602.02307v1), preprint). A rerun undercounts flakiness: an industrial study found 32% of intermittent job failures mislabeled when reruns are the label ([arXiv 2507.04173](https://arxiv.org/html/2507.04173v1)). Report flaky cost as minutes in earlier attempts plus the wall-clock delay to green for the affected commits, and call it "rerun cost", not "flake rate". Cancelled runs come from `concurrency` groups: a new run cancels pending ones, and running ones only with `cancel-in-progress: true` ([concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)). `action_required` (21 axum runs, fork PRs awaiting approval) and `skipped` runs have no runner time and must be excluded from duration statistics. The approval wait still counts in time-to-green: axum's max time-to-green was 1,480 minutes.

**F15. Statistics that hold up.**
- **Median and p90 per stratum, with n.** Durations are right-skewed (poetry full-matrix max 24.3m against a 5.6m median), so means mislead. p90 is unstable below about 30 runs (at n=20 it sits between the 18th and 19th values).
- **The A/A noise floor is the yardstick for any claim.** Randomly split an unchanged history into two groups of k runs, 2,000 times, and take the 95th percentile of the relative difference of medians:

  | Sample | k=10 | k=20 | k=30 |
  | --- | --- | --- | --- |
  | axum CI, whole run | 38.0% | 30.9% | 27.7% |
  | poetry Tests, full matrix | 20.9% | 14.5% | 11.8% |
  | axum `cargo-hack`, one job | 14.3% | 11.4% | 9.3% |
  | poetry one Ubuntu pytest job | 13.5% | 9.5% | 8.1% |

- **What a 10% saving needs.** With a normal approximation on log duration (sd 0.25 to 0.31), a 10% saving on a whole run needs 86 to 140 runs per side at alpha 0.05 and power 0.8. A single job's duration is two to three times less noisy than the whole run.
- **Published guidance agrees.** Repetition counts must come from measured variance, not a fixed rule ([Kalibera and Jones, ISMM 2013](https://kar.kent.ac.uk/33611/); [Georges et al., OOPSLA 2007](https://dri.es/files/oopsla07-georges.pdf)). Benchmark studies on GitHub-hosted runners report detectable changes down to about 4.4% for sequential workloads after many repetitions ([arXiv 2411.05491](https://arxiv.org/html/2411.05491v1)), and runner image updates have shifted timings without code changes ([arXiv 2510.11310](https://arxiv.org/html/2510.11310v1)). No peer-reviewed study reports end-to-end CI duration variance on GitHub-hosted runners; the noise-floor numbers above are this repository's own and should be recomputed per target.
- **Related empirical work.** On long builds: rerunning failed commands is the factor most associated with long durations, and about 40% of projects do not use or misuse caching (Ghaleb, da Costa, Zou, EMSE 2019, 104,442 builds; [ICSE 2020 journal-first](https://2020.icse-conferences.org/details/icse-2020-Journal-First/71/An-Empirical-Study-of-the-Long-Duration-of-Continuous-Integration-Builds)). On GitHub Actions resource use: 91.2% of resources go to build and test, and caching is used by only 32.9% of paid-tier repositories (Bouzenia and Pradel, [ICSE 2024](https://conf.researchr.org/details/icse-2024/icse-2024-research-track/15/Resource-Usage-and-Optimization-Opportunities-in-Workflows-of-GitHub-Actions)).

### Money

**F16. Prices are per SKU per minute; there are no OS multipliers.** From [runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing), read 2026-10-11; the page carries no date. The old `actions-minute-multipliers` URL now serves this page and lists no multipliers.

Standard runners:

| Runner | USD per minute |
| --- | --- |
| Linux 1-core | 0.002 |
| Linux 2-core x64 | 0.006 |
| Linux 2-core arm64 | 0.005 |
| Windows 2-core | 0.010 |
| macOS 3 or 4-core | 0.062 |

Larger runners, USD per minute:
- Linux x64: 4-core 0.012, 8-core 0.022, 16-core 0.042, 32-core 0.082, 64-core 0.162, 96-core 0.252.
- Windows x64: 4-core 0.022, 8-core 0.042, 16-core 0.082, 32-core 0.162, 64-core 0.322, 96-core 0.552.
- macOS: 12-core `macos_l` 0.077, M2 Pro `macos_xl` 0.102.
- GPU: Linux 0.052, Windows 0.102.

Each job is rounded up to the whole minute.

**F17. Included minutes and what is free.** Per month, for private repositories: Free 2,000, Pro 3,000, Team 3,000, Enterprise Cloud 50,000 ([Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)). Standard hosted runners are free on public repositories. Larger runners are always billed and never use included minutes. Self-hosted usage is free. The live pages do not say how included minutes are drawn down per OS; the skill should state dollar cost and let the plan's included minutes offset it, marked as an assumption.

**F18. 2026 pricing changes.** Hosted-runner prices dropped "up to 39%" on 2026-01-01. The $0.002 per minute self-hosted "cloud platform charge", announced for 2026-03-01, was postponed on 2025-12-15 to "re-evaluate our approach", with no new date ([GitHub resources page, 2025-12-15](https://github.com/resources/insights/2026-pricing-changes-for-github-actions); [changelog 2025-12-16](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)). The current billing docs list self-hosted usage as free. No later changelog entry was found (changelog checked 2026-10-11). The skill should show self-hosted cost as $0 with a note that GitHub's charge is postponed, not cancelled.

**F19. Dollars from job data.** Poetry's full-matrix Tests, priced as if private: median $2.00 per run, $252 over 117 runs. Billed minutes by OS were Ubuntu 2,836, Windows 5,279, macOS 2,933, so macOS is 26% of the minutes and about 72% of the dollars. Windows pytest legs run a median 3.20m against 1.32m on Ubuntu. The first lever on poetry's cost is macOS legs, on wall clock macOS queue (F10), and on minutes Windows. This is the kind of ranking the skill should produce.

## Proposed measurement protocol

**P1. Sample.**
- The last 30 days, up to the newest completed run, split into per-day `created` slices (F1).
- Runs plus `jobs?filter=all`, required contexts from both branch protection and rulesets (F6), and merge queue timeline events if `merge_group` runs exist (F7).
- Extend to 90 days only if a stratum has fewer than 20 runs, and never further than 90 on public repositories (F9).
- Record the API calls used and the pull time.

**P2. Strata and exclusions.**
- Group by workflow, event, the set of executed jobs, and runner label (F13).
- Exclude `action_required`, `skipped` and runs with no executed job from durations.
- Keep failed, cancelled and earlier-attempt minutes in cost (F14).

**P3. Minimum sample.**
- 20 successful runs per stratum for a median, 30 for p90.
- Below that, report the numbers labelled "insufficient sample" and do not rank on them.

**P4. Report per stratum.** Show n, then the median and p90 of each of:
- wall clock;
- time to merge-gating green (last required context, check run or commit status, per PR head commit);
- runner minutes;
- per-job queue, split by runner label;
- dollars at F16 prices, including per-job round-up.

Also report the critical path: from timestamps, checked against `needs:` (F12). Bimodal strata are reported as two modes with their likely cause.

**P5. Rank proposals by saving, and label each number by how it was obtained.**
- **measured:** observed in this repository's data, for example macOS queue of 97s median on the critical path, or minutes in earlier attempts. Quote n and the A/A noise floor at that n.
- **modeled:** computed by replaying the recorded timelines with one change, for example removing a job from the critical path, raising macOS concurrency, or a cache-hit-rate change that moves the slow mode to the fast mode. Give the replay inputs. Whole-run savings are modeled by default.
- **guessed:** from published or vendor figures with no local data. Give a range and the source, and never rank a guessed saving above a measured one of similar size.

**P6. Verify a change afterwards.**
- Before the change, freeze the baseline: the stratum, its n, the median, and the A/A 95th-percentile noise floor at the planned after-sample size.
- After merge, collect at least as many runs of the same stratum (same event and executed-job set), at least 20.
- Compare first the changed job's duration, which is less noisy (F15), then the whole-run wall clock and time-to-green.
- Claim the saving only if the median moved by more than the noise floor at that n. Otherwise report "no measurable change at n=X; the noise floor is Y%" and keep collecting.
- Check that nothing else changed in the window: runner image version in the `Set up job` step log, the dependency lockfile, and the `needs:` graph. Runner image updates move timings on their own (F15).
- Report the realized saving next to the predicted one, with the label from P5.

## Live test: exact commands

Scratch scripts, outside the repository: `/private/tmp/claude-501/-Users-dan-Work-software-factory/9cabba1d-c833-4690-a8e5-97f0e8babfb7/scratchpad/ci/{fetch.py,analyze.py,dist.py}`.
- `fetch.py` pages `actions/runs?per_page=100&created=A..B`, then `runs/{id}/jobs?filter=all&per_page=100` for each run, through `gh api`.
- `analyze.py` computes F10 to F15.
- `dist.py` prints the histograms and step medians.

All calls were GET.

The repositories named for this lane (dogebonker/edgeflow, LeaveMyYard/moneylust-app, fntch1/bitxchange-backend) returned 404 to the active `gh` account. Trying the second logged-in account's token was blocked by the permission classifier, so the test ran on public repositories instead.

```
python3 -I fetch.py tokio-rs/axum 2026-09-10 2026-10-10
  -> tokio-rs/axum: runs=176 api_calls=178
python3 -I fetch.py python-poetry/poetry 2026-09-10 2026-10-10
  -> python-poetry/poetry: runs=333 api_calls=342
gh api repos/tokio-rs/axum/branches/main --jq '.protection.required_status_checks.contexts[]' > axum.required
python3 -I analyze.py tokio-rs__axum.json <17 contexts from axum.required>
python3 -I analyze.py python-poetry__poetry.json Status
python3 -I dist.py tokio-rs__axum.json CI test-msrv
```

Excerpts (axum):

```
run_started_at - created_at (attempt 1): max=0s, nonzero=0 of 174
### CI
  wall-clock (first job queued -> last job done): n=114 median=3.4m p90=4.7m max=7.5m mean=3.7m CV=0.25 IQR/med=0.48
  runner time per run: n=114 median=13.0m p90=17.8m max=20.9m
  job queue: median=3s p90=4s max=106s over 1938 jobs
  last job on critical path (most common): [('test-msrv', 96), ('test-versions (beta, examples)', 11), ...]
  |jobs wall - (updated_at - run_started_at)|: median=1s p90=2s
runner minutes total=1968 (billed-rounded 3186, +62% from per-job round-up)
## time to all 17 required checks green, per PR head commit: n=94 median=3.4m p90=4.7m max=1480.4m
```

Excerpts (poetry, full-matrix stratum):

```
full-matrix runs 117 path-filtered runs 51
full: median=5.63 p90=7.60 max=24.27 CV=0.43 IQR/med=0.27
queue macos-15: n=1404 median=97s p90=220s max=684s
queue ubuntu-24.04: n=1404 median=3s p90=4s max=40s
pytest exec windows-2025: n=898 median=3.20m p90=4.22m
pytest exec ubuntu-24.04: n=898 median=1.32m p90=1.77m
A/A full k=10: 95th pct 20.9%   k=20: 14.5%   k=30: 11.8%
if private: median $2.00 per full run, total $252 over 117 runs
```

## Limits of this lane

- The live test used public repositories, so private-repository billing (`/timing` billable, rounding as billed) was modeled from prices rather than observed.
- No repository in the sample used larger or self-hosted runners.
- Merge queue timing was sampled on 12 PRs only.
- The A/A noise floors come from two repositories and are illustrative; the protocol recomputes them per target.
