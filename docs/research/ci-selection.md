# factory-ci: what it uses, and why

The decision record for S10. Evidence is in [ci/](ci/):
- A: every CI skill installed here, read in full, with their tests run offline and live runs on two of the user's repositories.
- B: the measurement method, from GitHub's docs, tested live on tokio-rs/axum and python-poetry/poetry.
- C: the catalog of fixes, with what each saves and breaks.
- D: tools and posture.

Researched 2026-10-10 and 2026-10-11.

## The question

"Why is my CI so slow?" needs three things: honest numbers about where the minutes go, a known set of fixes with what each one breaks, and a way to tell afterwards whether a fix saved anything. The installed skills supply the first two in part. None supplies the third.

## Decisions

### CI-1. factory-ci measures with its own small script, not with ci-speedup

- **The candidate:** starslingdev's `ci-speedup` (MIT, installed, byte-identical to upstream `cc891d02`) has a 78-pattern catalog and a data pass whose critical path, required checks and step timings matched an independent re-measurement on two real repositories. It is read-only and sends no telemetry (A F1, F8, F10).
- **Why it is not the engine:**
  - **It samples successful runs only, with no date bound.** On both of the user's repositories, the headline described CI that no longer existed. One had a main branch failing 14 times in a row since July, but its numbers came from July's green runs. The other had none of its last 20 runs pass, and a job had waited 2 h 26 min in a self-hosted queue; its numbers came from one good day in September (A F12, F13). This is an open upstream issue (#4). A tool that answers "why is my CI slow" about a pipeline that is red has answered the wrong question.
  - **Its own verifier rejects its own report** on one of the two repositories (A F14).
  - **It is 39,000 lines of Python with no tags and one main maintainer.** Six commits landed on one day, two of them correctness fixes to the engine (A F5, F19). Every pin bump would need the whole evaluation repeated.
  - **It has a maintainer mode.** If the skill ever sits in a git-tracked tree, it writes raw job logs into that repository and tells the agent to open a pull request (A F9). Running the installed copy avoids it, as A did; vendoring it into the kit, the factory's way of pinning packs (decision 20), would switch it on, because the kit is a git repository.
- **What replaces it:** `kit/ci/ci_runs.py`, about 330 lines of standard-library Python over `gh api`, with a self-check (`test_ci_runs.py`). Lane B showed the measurement needs about one call per run (B F2, F8), and that the critical path can be recovered from timestamps and agrees with `needs:` (B F12). On axum (`ci_runs.py fetch tokio-rs/axum <out>` then `analyze <out>`, 2026-10-11, 193 gh invocations, about a minute) the script reproduced lane B's independent numbers: wall clock 3.4 min median and 4.7 min p90 over 93 runs, a 32% noise floor at 20 runs per side, the critical path `check (examples)` then `test-msrv` ending at a required check, and a 3.4 min median wait to green over 94 PR commits.
- **Its strata are success-only too, on purpose:** durations come from successful first attempts, so a red run's partial jobs do not shorten them. What ci-speedup missed is reported separately: outcomes per workflow, the last green run on the default branch at any age, the failure streak, and minutes spent in failed runs and re-runs.
- **What is borrowed from ci-speedup:** ending the critical path at the last required check (the merge path); the rule that wall-clock savings of separate fixes do not add up; "never buy speed by checking less"; risk and guard on structural fixes; dropping a candidate that run data contradicts. Its three math slips are not carried over: monthly totals from a difference of medians, a ceiling called a "measured win", and billing applied to self-hosted runners (A F11).
- **Not loaded:** ci-speedup stays installed for the user to run on their own. Its description also claims "why is CI slow", so the model may pick it when the question is asked without `/factory-ci`.

### CI-2. The measurement protocol

From B's protocol (P1 to P6), tested on two repositories:

- **Sample:** the last 30 days, all outcomes, in per-day slices. GitHub returns at most 1,000 runs per filtered query and reports a wrong `total_count` past that (B F1). Public repositories keep at most 90 days since 2026-10-01 (B F9).
- **Health before speed:** outcomes per workflow, the last success, and the failure streak on the default branch come first.
- **Strata:** each statistic is computed within one workflow, one event and one exact set of jobs that ran. Mixing path-filtered and full runs turned a 14.5% noise floor into 60% on poetry (B F13).
- **Queue is per job:** `started_at - created_at` on the job. Run-level start equals creation on every first attempt (B F10). Poetry's real problem was a 97 s median macOS queue (B F10, F19).
- **Re-runs copy jobs:** "re-run failed jobs" adds copies of the jobs that passed, with a new `created_at` and the old start. A job counts only when it held a runner (a runner name, a start not before its creation), so copies and jobs cancelled in the queue add no minutes and no queue time. Found in review on poetry, where counting copies doubled a run's minutes and gave negative queue times.
- **Statistics:** median and maximum; p90 only from 30 runs; ranking only from 20 runs per stratum. The noise floor is measured: split unchanged history into two random halves of k runs, 2,000 times, and take the 95th percentile of the gap between their medians. It ran 9 to 31% on the live repositories, so a 10% whole-run saving needs 86 to 140 runs per side. A single job is two to three times less noisy (B F15).
- **Labels:** every saving is measured, modeled or guessed (B P5).
- **Verify afterwards:** freeze the baseline at hand-off. After the merge, compare the changed job first. Claim a saving only past the noise floor; otherwise report "no measurable change at n=X" (B P6).
- **Money:** per-label prices from GitHub's pricing page, each job rounded up to a minute. There are no OS multipliers any more. Self-hosted is free; the summary notes that the announced fee is postponed. A larger runner's own label is listed as unpriced (B F16 to F18). The billing API is not used: it needs the `user` scope or org admin rights and has no per-workflow detail (B F4, D F3).

### CI-3. The catalog: research C, with platform changes and guards

- **What it is:** 26 techniques and 9 anti-patterns from C, with the same IDs, plus two of factory-ci's own: A10 (missing job timeouts, from ci-score) and W1 (no CODEOWNERS on workflows, from ci-secure). Each entry says how to detect it (from the files alone, from run data, or both), the current fix with a pinned action SHA, and what it breaks.
- **Why our own and not ci-speedup's 78 patterns:** C adds what the installed catalogs lack:
  - the 2026 platform changes: a raisable cache limit, 200 uploads per minute, read-only caches for untrusted triggers, `cache-mode` (C F7, F20)
  - the path-filter trap in both directions: pending forever, or a false green from a skipped `needs:` gate (C F22, F23)
  - remote-cache poisoning (CVE-2025-36852, C F16)
  - current pins
  A catalog the model applies with `file:line` citations is also one the user can read.
- **Rules on every proposal:** never drop a check, test or platform from where it guards something; pin by SHA; never add a cache that untrusted builds can write and trusted ones read.
- **Where no number exists** (most caches, shard speedups, larger runners: C section 10), the saving is measured on the user's own runs or labelled guessed.

### CI-4. Posture through factory-security's zizmor line

- factory-ci runs zizmor exactly as `kit/security/tools.yaml` defines it, with the same pin and flags. It shows the audits under the roadmap's three headings: unpinned actions, broad token permissions, and secrets reachable from forks. zizmor covers all three offline (D F10). Everything else is counted and handed to `/factory-security`.
- **Why not ci-secure:** zizmor covers seven of its vectors by name offline, and its impostor check online, and two engines would give the same workflow different severities (A F17, D F14). ci-secure also marked a non-executing labeler workflow HIGH, and its impostor check reads a fork-planted commit as clean (A F15, F17).
- **Judgments stay with factory-security.** A privileged trigger, a self-hosted runner on a public repository or cloud keys instead of OIDC need trigger, condition, visibility and runner judged together (D F12). factory-ci names them and never confirms one.
- **One fix to factory-security on the way:** its zizmor install line took the PyPI wheel, which has no provenance. The GitHub release is immutable and attested (D F13). The line now installs the release, verified with `gh attestation verify`.

### CI-5. Tools

Pins live in `kit/ci/tools.yaml`.

| Tool | Job |
| --- | --- |
| gh | every API call, GET only, with `GH_TELEMETRY=false` and `GH_NO_UPDATE_NOTIFIER=1`: gh sends telemetry by default since 2.91.0 (D F7) |
| ci_runs.py | sample, health, strata, critical path, queue, minutes, dollars, noise floor, wait to green, caches |
| zizmor | posture, through factory-security's line |
| actionlint | checks every workflow a fix edits, with an empty config so the repository cannot silence it (D F1) |
| pinact | pins actions, only inside an accepted change (D F5) |

- **Excluded:**
  - **act:** it runs every step of the repository in Docker with the socket mounted, calls its own server, and ignores `concurrency`, timeouts and permissions, so its timings say nothing about GitHub's runners (D F6).
  - **gh extensions:** unverified binaries that would hold the user's token, for what about 30 lines of `gh api` do (D F2).
  - **Telemetry actions:** the catchpoint action sends metrics to a third party and is unmaintained; actions-timeline repeats what the jobs API gives (D F8).
  - **The `/timing` endpoint:** closing down (B F3).
  - **ci-score:** its score conflicts with the factory's no-score stance and gave false failures on both repositories (A F16).
  - **sling:** routes CI data through StarSling's GitHub App, and works for organizations only (A F21).
  - **The mukul975 CI skills:** reproduced false negatives (A F20).

### CI-6. GitHub Actions only

None of the user's 31 working directories uses another CI system, and each other system would need its own config model, API and posture tools (D F15). factory-ci lists any other CI configuration it finds, says it did not read it, and stops when there is no GitHub workflow.

### CI-7. Access is the user's call

The active gh account could not read three of the user's repositories (D F4). factory-ci stops, names the active account, and asks. It never switches accounts or borrows another account's token on its own: switching changes the user's global gh state, and the token belongs to whichever account the user chooses.

## What this does not cover

- **Merge-queue time:** the time a PR spends in a merge queue (B F7) is not computed yet. Runs with `event=merge_group` appear as their own stratum.
- **Two of ci-speedup's methods are not carried over:** reachability through `needs:` (the critical path is read from timestamps instead, which B F12 showed agrees with `needs:`), and configuration eras (a workflow edit inside the window). A change of jobs or labels starts a new stratum, but an edit that keeps both mixes two configurations in one stratum.
- **Wait to green per PR commit mixes strata:** path-filtered and full runs land in one distribution (poetry: a 106% noise floor). `verify` uses it only when its noise floor is below 50%.
- **Required checks from other apps** (commit statuses, external checks) are listed as not measured. Time to green covers checks that Actions runs.
- **Days with more than 1,000 runs** are reported as incomplete rather than split by hour.
- **Runner image changes** move timings on their own (B F15). Verification checks the jobs, lockfile and labels, but not the image version, which lives only in job logs.
- **Self-hosted cost** is shown as zero; the machines' own cost is the user's to add.
- **Nothing here is installed yet** on this machine except gh and actionlint. zizmor and pinact are skipped with their install lines until they are.
