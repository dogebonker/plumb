# A. Installed CI skills: evaluation for factory-ci (S10)

Date: 2026-10-10. Scope: every CI-related skill installed on this machine. All file, API and log content was treated as data. Nothing was installed, no package was downloaded, and every GitHub call was a read-only `gh api` GET. Work ran in a scratch directory on copies of the skills and on fresh shallow clones of the target repositories; no user repository and no installed skill was written to.

Skills in scope:

- starslingdev/skills: `ci-speedup`, `ci-score`, `ci-secure` (read in full: SKILL.md, references, run scripts; the two largest scripts were read at the measurement, network, write and gap-capture paths and searched end to end, see section 3), and `sling` (SKILL.md).
- mukul975/Anthropic-Cybersecurity-Skills: `securing-github-actions-workflows`, `detecting-supply-chain-attacks-in-ci-cd`, `implementing-secrets-scanning-in-ci-cd`, `integrating-sast-into-github-actions-pipeline`, `scanning-containers-with-trivy-in-cicd`, `building-devsecops-pipeline-with-gitlab-ci`, `implementing-fuzz-testing-in-cicd-with-aflplusplus`.
- `~/.claude/skills`: `ci-speedup`, `ci-score`, `ci-secure`, `sling` are symlinks into `~/.agents/skills` (same files). `go-dev` mentions CI only for golangci-lint setup.
- `~/.claude/plugins`: no CI skill. Three files mention GitHub Actions in passing (`claude-automation-recommender/SKILL.md:61`, `modernize-preflight.md:88`, thedotmack `version-bump/SKILL.md:71`).

## Bottom line

- **F1. ci-speedup's measurement core is sound and worth reusing; the skill around it is not.** On two real repositories its critical path, required-check resolution, `needs:` chain and dominant-step numbers matched my own re-measurement (section 5). It is read-only, has no telemetry, and calls only `api.github.com` through `gh` (section 3). But its sample is success-only and unbounded in time, so on both repositories the headline described CI that no longer exists (F12, F13); its own verifier fails its own report on one of the two (F14); and its interaction contract conflicts with factory-triage (F18).
- **F2. ci-score and ci-secure add little next to factory-security.** ci-score is an 11-fact adherence grade that marked an intentional `fetch-depth: 0` and a 1-second install as failures and could not see a 12-minute test step (F16). ci-secure's ten vectors overlap zizmor's core audits, which factory-security already pins at 1.30.1; its three repository-settings hygiene checks are the only part zizmor lacks (F17).
- **F3. The mukul975 CI skills and `sling` are rejected.** The mukul975 scripts carry false negatives I reproduced (F20). `sling` needs StarSling's GitHub App on an organization and sends CI data through StarSling's control plane (F21).

## Per-skill summary

| Skill | Source, license, pin | Size | Network | Verdict |
| --- | --- | --- | --- | --- |
| ci-speedup | starslingdev/skills, MIT, commit cc891d0249 (tree afc429b0) | SKILL.md 37 KB; scripts 2.2 MB, 39k lines | `gh api` GET to api.github.com only | **Wrap the data pass** (`scripts/run.py`), never load SKILL.md; borrow the methodology |
| ci-score | starslingdev/skills, MIT, same commit (tree 66a4a29c) | SKILL.md 14 KB; scripts 127 KB | none (0 calls measured) | **Reject**; borrow two posture facts |
| ci-secure | starslingdev/skills, MIT, same commit (tree 63362a15) | SKILL.md 31 KB; scripts 0.6 MB | `gh api` (repo settings, impostor probe) | **Reject as engine** (zizmor covers it); borrow three hygiene checks |
| sling | starslingdev/skills, MIT (tree 80391991) | SKILL.md 30 KB | StarSling control plane; binary not installed | **Reject** |
| 7 mukul975 CI skills | Apache-2.0, pinned 2026-08-16 | 23-58 KB each | scripts not run | **Reject** (as in security SEC-4) |

## 1. Upstream: age, activity, pin

- **F4. The installed copies are byte-identical to upstream commit `cc891d0249e91c3615d894ac82b176a3421b0d74` (2026-09-30).** `~/.agents/.skill-lock.json` records `skillFolderHash` `afc429b0...` (ci-speedup), `66a4a29c...` (ci-score), `63362a15...` (ci-secure). `gh api repos/starslingdev/skills/contents/skills?ref=cc891d02...` returns exactly those tree SHAs. Comparing `git hash-object` of every installed file with `gh api .../git/trees/<tree>?recursive=1`: 128/128, 89/89 and 107/107 blobs match, no extra or missing file.
- **F5. Upstream is young, fast-moving and single-maintainer.** `gh api repos/starslingdev/skills`: created 2026-07-22, MIT, 29 stars, 1 fork, not archived, last push 2026-10-10T16:13Z. No releases and no tags (`/releases` and `/tags` both empty), so a pin can only be a commit. Contributors: yonasb 91 commits, NWelde 4, dbworku 2. Of 23 issues ever filed, 1 is not by yonasb (`search/issues ... -author:yonasb` = 1, issue #119). Six commits landed on 2026-10-10 alone, two of them correctness fixes to the installed engine: #126 "a skipped step no longer counts as two thousand years of CI time" and #128 "flat estimates are capped at measured compute". Upstream main is `a7c2db4a1e281ba8656de2b18b01f72dcc9effa1` (ci-speedup tree `ffbd9629ba8194ee9fc365b191858a20ceb09394`); it was not tested here.
- **F6. The red-main bias I found live (F12) is a known open issue.** Issue #4, open since 2026-07-22: "Red-main repos: 'typical PR waits Xs' should carry a success-only-basis caveat with the observed failure rate". Issue #7 (open): deleted files linger in installs.

## 2. Test suites, offline

Run from copies in the scratch directory, with `gh` replaced by a stub that logs and exits 1, `HTTP(S)_PROXY` pointed at a dead port, and `GH_TOKEN=invalid`. Python 3.10.0, PyYAML 6.0.1, pytest 8.3.3 (all already installed).

- **F7. All three suites pass except tests that assume the upstream source checkout.**
  - ci-score: `python3 -m pytest -q tests` -> `204 passed in 3.82s`.
  - ci-secure: -> `1102 passed, 2 skipped in 25.29s`.
  - ci-speedup: plain `pytest tests` fails at collection (`ModuleNotFoundError: No module named 'blocking_path'`), because upstream's root `pyproject.toml` sets `pythonpath`. With `PYTHONPATH=scripts:tests`: `3 failed, 3225 passed, 16 skipped in 138.54s`. The three failures (`test_emit_gap_signal_maintainer_next_action_is_imperative`, `test_is_maintainer_source_true_in_this_checkout`, `test_provenance_is_derived_from_git_when_omitted`) each assert that the skill sits in a git-tracked source checkout; an installed copy is not one.
  - The suites tried `gh` 4 times in total (`gh api repos/owner/name/actions/workflows/ci.yml/runs?per_page=50`, `gh auth status` x3); all hit the stub. ci-score's tests also monkeypatch `socket.socket` to fail on any egress (`tests/test_b4_controls.py:87-95`).

## 3. What the scripts do

### Network

- **F8. No telemetry, no upload, one host.** No script in the three skills imports `urllib`, `http.client`, `socket`, `requests` or `httpx`, and none shells out to `curl` or `wget` (grep over `scripts/` and `scaffold/`; the only `socket` imports are the ci-score test egress guards). Every network call is a `gh` subprocess:
  - ci-speedup: `collect_runs.py:666-673` builds `gh api -i [--allow-escape-sequences] <endpoint>`, GET only (no `-X`, `-f`, `-F` or `--input` anywhere in ci-speedup or ci-score). Endpoints (`collect_runs.py:2358-16339`): `repos/{r}`, `actions/workflows`, `actions/workflows/{id}/runs` (with `status=success`, `event=`, `created=>=` filters), `actions/runs/{id}/jobs`, `actions/jobs/{id}/logs`, `commits?path=`, `commits/{sha}/check-runs`, `rulesets`, `rulesets/{id}`, `branches/{b}/protection/required_status_checks`, `contents/{path}`. Plus `gh auth status`, `gh --version`, `gh auth token` (return code only, `collect_runs.py:1501-1540`).
  - ci-secure: `gh_utils.py:265-276` can send `-X <method>` and `-f` fields, and `run_graphql` (`gh_utils.py:153`) posts to GraphQL, but no caller passes a non-GET method and `run_graphql` has no caller in `scan.py`, `report.py`, `run.py` or `vendor.py`. Live calls observed: `repos/{r}`, `actions/permissions/fork-pr-contributor-approval`, `actions/workflows/{f}/runs?per_page=50`, `branches/main/protection/required_status_checks`, `rules/branches/main`; the impostor probe adds `repos/{action}/commits/{sha}`, `repos/{action}`, `repos/{action}/git/tags/{sha}` (`scan.py:4835-4960`).
  - ci-score: no network. Live runs made 0 `gh` calls.
  - URLs in the scripts (docs.github.com, vitest.dev, starsling.dev and others) are links printed into reports, never fetched.

### Writes and repository content

- **F9. Writes stay in the output path, with one dangerous exception.**
  - ci-speedup writes `--out` (via a `.partial` file and an atomic rename, `run.py:261-317`), a sibling `<out>.data/` with raw job logs, and on render the report plus a `.claims.json` sidecar. Nothing was written into the audited clones (`git status --short` empty after all runs); `git status` did refresh `.git/index` mtime, which is git's own behaviour.
  - **The exception:** `blocking_path.py:10153-10166` (`_is_maintainer_source`) and `collect_runs.py:12724-12754` decide "maintainer mode" by `git ls-files --error-unmatch scripts/...` on the skill's own directory. If true, the data pass writes `.ci-speedup-gaps/bill-workflows/` and the render writes `.ci-speedup-gaps/<repo>__<job>/` (raw third-party job logs) at the root of the git repository that contains the skill, and SKILL.md:237 tells the agent it "MUST" draft a detector and open a PR. The docstring at `blocking_path.py:10095-10098` concedes the probe "succeeds on a vendored copy the user committed". `~/.software-factory` is a symlink to `/Users/dan/Work/software-factory/kit`, a git repository, so committing ci-speedup under `kit/` would switch this on for every factory run.
- **F10. No repository content is executed.** Workflow YAML is parsed with `yaml.safe_load` or a `SafeLoader` subclass (`ci-speedup/scripts/scan.py:3478-3502`, `collect_runs.py:14839`, ci-score `collect_config.py:149`, ci-secure `scan.py:496,533,2434`). The only processes run against the target are `git -C <root>` (`rev-parse`, `status`, `ls-tree`, `config --get`). Requirements: `gh` authenticated, Python >= 3.9, PyYAML. ci-secure's optional CI gate (`scaffold/`, `vendor.py`) writes into the user's repository, with consent per its SKILL.md.

## 4. How ci-speedup measures, and the math

- **Sampling.** Per workflow, the last N runs with `status=success`, newest first, with no time bound (`collect_runs.py:3449-3547`): a 10-run shallow pass (`_SHALLOW_RUNS = 10`, `collect_runs.py:12650`), deepened to 20 (`--max-runs 20`) for workflows that look like poles; a separate PR-gate sample targets 20 PRs (`run.py --target` help). Workflow file changes split the sample into configuration eras and keep the current era when it has at least 6 runs (`pr_critical_path.config_eras`, `sufficiency_min: 6`).
- **Statistics.** Medians (`statistics.median`) and a linear-interpolated percentile (`collect_runs.py:2334-2341`). Job duration is the jobs API `started_at -> completed_at`; queue is reported separately (OPT43).
- **Critical path.** Per PR, the gate is the max over concurrent checks, with `needs:` chains summed (`wall-clock-methodology.md` section 2 and the "chain facts" note). The spine is restricted to required checks read from active rulesets that target the scored branch plus classic protection, extended by `needs:` reachability (`spine-scoping.md`); without readable required checks it falls back to the "PR-floor". Checks are ranked by how often they are the per-PR pole, not by size.
- **Confidence** is expressed as labels, never as intervals: `measured` vs `modeled` sizing, "single observation", "short sample", era banners, a failure-rate gate of n >= 30 (`savings-methodology.md:111-123`). `wall-clock-methodology.md:235-282` forbids reading the observed spread as uncertainty.
- **F11. Math: mostly right, three problems.**
  - Right: `wall-clock ~ entry gate + max(parallel) + joiner`; the below-floor rule; serial-gate fixes can add wall-clock; per-finding wall-clock deltas are not additive; `1/(1-f)` attempts for a first-pass failure rate f; and section 8's joint model correctly takes the max per observation before the median (`median(max) != max(median)`).
  - Wrong: the "REQUIRED" monthly wall-clock total is `(P50 now - P50 stacked) x runs/mo` (`wall-clock-methodology.md:371-377`, `savings-methodology.md:360-364`). A monthly sum needs the mean per-run saving, as the same file says for runner-minutes (`savings-methodology.md:384`), and a difference of two medians is not the median of differences (its own section 8, line 498). Neither live report rendered this total.
  - Mislabelled: the Bottom line calls the gap between the slowest check and the next one "the biggest single measured win" (`blocking_path.py:9053-9055`). It is a ceiling on what any change to that check can buy, not a measured saving of a proposal. On edgeflow that reads "~12m 48s", i.e. deleting the job.
  - Fragile: P95 from 10 to 20 samples by interpolation is close to the sample maximum (edgeflow `ci`: p95 823.05 s from 10 runs).
  - Out of model: the methodology "targets gh-hosted (ephemeral) runners" (`wall-clock-methodology.md:80-82`), yet the cost spine applies GitHub's per-job minute rounding to self-hosted rows (moneylust `api-changes` on `linux self-hosted`: raw 13.903, "billable" 91.000 min/mo) with no warning.

## 5. Live runs (read-only)

Account: the second `gh` login (`skylightxo`), passed as `GH_TOKEN` per process; the active account cannot see these repositories. `dogebonker/edgeflow` (TS/React/Bun, 2 workflows) and `LeaveMyYard/moneylust-app` (Rust + TS, 19 workflow files, self-hosted runners) were shallow-cloned into scratch. `fntch1/bitxchange-backend` was skipped: 4 runs in total. Command: `python3 -I scripts/run.py --root <clone> --out <scratch>/findings.json --repo <r> --with-logs`, then the printed `blocking_path.py` render and `tests/verify_report.py`. `gh` was wrapped by a pass-through logger.

| | edgeflow | moneylust-app |
| --- | --- | --- |
| data pass | 17 s, 103 `gh` invocations (tool counts 102) | 61 s, 258 invocations (tool counts 257) |
| render | < 1 s | 1 s |
| report | 18 KB | 79 KB |
| verify_report | 1 FAIL: coverage-gap pole needs the LLM gap-fill (expected, phase 4a) | 2 FAIL: savings above measured compute; misrouted build bin (F14) |
| ci-score | < 1 s, 0 calls, 43/100 | < 1 s, 0 calls, 63/100 |
| ci-secure | 7 s, 8 calls, 0 findings | 14 s, 25 calls, 1 finding (P14.18 HIGH) |

What ci-speedup said, and what I found:

- **edgeflow.** Report: "A typical PR waits 13m 12s"; pole `ci` (P50 13m 12s over 10 runs), dominant step `Test` 12m 04s (92%), "biggest single measured win ~12m 48s"; header "Runs window 2026-09-10 -> 2026-10-10 (30-day window)", "PR gate sample 0 / 20 PRs"; cost spine 0.000 min/mo.
  - Correct: the last successful run (29511344462, 2026-07-16) has `Test` from 15:29:47 to 15:42:06, 12m 19s of a 13m 20s job; Install takes 1 s, so no cache finding is right (the admission gate held).
  - **F12. It missed that main has been red for two months.** `gh api .../actions/runs?per_page=30`: every `CI` run since 2026-07-17 failed (14 in a row through 2026-09-02); in the latest (33646531716) `Test` is `cancelled` after 10m 52s and the build steps are skipped, which matches the runner kill described in the `ci.yml` comment. The 10 runs behind the P50 are 2026-07-13 to 2026-07-16 (`runner_minute_spine.rows[0].sample_window_start/end`), yet the header names a 30-day window in which zero runs exist (`created=>=2026-09-10` -> `total_count 0`). There are no PRs, so "a typical PR" describes push runs. The four static findings (OPT32 x2, OPT45, OPT40) were sized at 0 and not rendered.
- **moneylust-app.** Report: "A typical PR waits 9m 45s for the `api-changes` -> `backend-image` -> `api-tests` chain"; 10 required checks; poles `backend-tests` 9m 14s (one observation), `api-tests` 6m 29s; "PR gate sample 1 / 20 PRs"; queue "worst savable wait 31s" with `api-changes` P90 queue 2228 s; OPT70 HIGH on `backend-image`, OPT75 on `backend-tests`; "Also noticed" OPT33 at 260 min/mo.
  - Correct: the required set matches the active ruleset `main-requires-green` exactly (`gh api .../rulesets/{id}`), and the chain matches `api-tests.yml` (`api-tests` and `e2e-tests` need `api-changes` and `backend-image`).
  - **F13. It described one good day and missed the current failure and queue.** The success sample is 2026-09-10 to 2026-09-11 (`runs?status=success&per_page=20`). In the 30-day window `api-tests.yml` ran 118 times: 27 success, 22 failure, 69 cancelled; none of the last 20 succeeded (my script, section 6). In the latest PR run (37264952784) `api-changes` was created 04:46:14 and started 07:12:12, 2 h 26 min in the self-hosted queue, then `api-tests` and `e2e-tests` failed at "Start stack; Backend egress guard". The report's headline wait is 9m 45s.
  - Minor: the headroom "~31s" compares the chain with `backend-tests` alone (9m 14s), but `backend-tests` also `needs: api-changes`, so the rival path is about 9m 23s and the headroom about 22 s. Inferred from the job graph, not re-derived from per-PR data.
- **F14. The skill's own verifier rejects its own moneylust report.** `verify_report.py`: "finding `OPT33` credits 252.1 min/mo of runner-time but its affected job(s) ['backend-tests'] measure only 227.5 min/mo", and "OPT70 ... dominant step `Build backend test image (cargo-chef, cached deps)` binned `build` but its name runs payload work". Re-rendering cannot change a deterministic result, so per SKILL.md:337-339 the user would get no saveable report. Upstream #128 (2026-10-10) touches capping at measured compute; not tested here.
- **F15. ci-secure on the same repositories.** edgeflow: 0 findings, impostor check "ran: no sha-pinned actions found" shown as a green row, while 0 of 4 action references are pinned (ci-score's count). moneylust: P14.18 HIGH on `pr-meta.yml:18`, `pull_request_target` with `pull-requests: write`. The workflow checks out nothing and runs only `actions/labeler@v7` and `amannn/action-semantic-pull-request@v6`, the documented labeler pattern; the real exposure is those two mutable tags and the `[self-hosted, linux]` runner on an untrusted trigger, which ci-secure's ten vectors do not cover. Its "required checks skippable" hygiene check went "unmeasured" on a classic-protection 404 although the rulesets that ci-speedup read were available.

## 6. ci-score and ci-secure against the factory

- **F16. ci-score's facts misfire on these repositories.** edgeflow: `dependency-cache fail` (Install takes 1 s), `test-sharding not_applicable` ("no test-like job detected": the 12-minute `Test` step sits in a job named `ci`), `concurrency-groups pass` with 1 of 2 workflows (the expensive `ci.yml` has none). moneylust: `shallow-clone fail` on `frontend-ci.yml:52`, where `fetch-depth: 0` is commented as required by `--scope changed` (`frontend-ci.yml:209-210`). Its own spec says the score is adherence, not speed (`SKILL.md:32-37`), and a score contradicts the factory's no-score stance (UI-4). Two facts are useful as posture lines: SHA-pinned share (0 of 4, 0 of 84) and job timeouts.
- **F17. ci-secure overlaps zizmor, which factory-security already pins.** By audit name (zizmor was not run; it is not installed here): P14.10 template-injection, P14.9 and P14.18 dangerous-triggers and excessive-permissions, P14.7 cache-poisoning, P14.11 impostor-commit, P14.14 overprovisioned-secrets, P14.15 github-env, P14.19 artipacked; zizmor also covers unpinned-uses and self-hosted-runner, which ci-secure lacks. ci-secure's own catalog says zizmor's template-injection model "is more comprehensive" (`references/security-patterns.md:156`). Its impostor check has a measured blind spot it documents: `repos/{r}/commits/{sha}` answers for the whole fork network, so a fork-planted commit reads clean (`scan.py:4977-4986`), while its finding text still says "fork-only or dangling" (`scan.py:5058-5060`). Not in zizmor, worth borrowing: a CODEOWNERS entry covering `.github/workflows/`, required checks reported only by conditional jobs (skipped counts as pass), fork-PR approval policy; and the P14.24 (curl into shell, mutable fetch-and-run) and P14.25 (install scripts in a privileged job) checks.

## 7. Instruction-shaped text found

No prompt injection was found (grep for override phrases across all SKILL.md and references). These are the skills' own instructions, recorded because they conflict with factory rules if the skills are loaded:

- ci-speedup `SKILL.md:278-286`: verification is an "INTERNAL gate - run them, never narrate them ... If a check fails, fix it and re-render once, silently". The factory reports evidence.
- ci-speedup `SKILL.md:349-354`: on a pick, the skill "makes the change and verifies it". factory-ci must hand proposals to `/factory-triage` instead.
- ci-speedup `SKILL.md:235-241` and `references/gap-fill.md` 4c: in maintainer mode the agent "MUST drive the gap -> catalog loop", ending in a PR to the skill (F9).
- ci-score `SKILL.md:180-186`: the post-apply menu "leads with 'Commit this branch and open a PR'".
- sling `SKILL.md:4-9`: "Invoke this BEFORE using `gh` or fetching any logs" whenever CI slowness is asked about.
- Front-matter routing: ci-speedup's description claims "why is CI slow" and `/ci-speedup`; installed beside factory-ci, both trigger on the same question.

## 8. The other installed CI skills

- **F18. ci-speedup's UX is built for a solo chat, not a factory.** Phase 1 and 6 require one `AskUserQuestion` with fixed slots and a verbatim save option, the Markdown report is opt-in, OPT ids must never appear in chat, and per-pole prompts run as fixes in the same session (SKILL.md:127-359). Its prompts end in a useful "NEVER BUY SPEED BY CHECKING LESS" rail and structural levers carry risk, guardrail and rollout (`references/structural-track.md`), which the factory can reuse as text in each triage change.
- **F19. Size and churn make loading costly.** `collect_runs.py` 20,310 lines and `blocking_path.py` 10,654 lines (452 and 229 functions), ARCHITECTURE.md 241 KB, CHANGELOG.md 213 KB, catalog 276 KB with 78 OPT ids; issue and PR numbers reach #128 in 80 days.
- **F20. mukul975 CI skills: rejected, consistent with security SEC-4.** Reproduced: `securing-github-actions-workflows/scripts/process.py:131` reads `workflow.get("on")`, but PyYAML parses `on:` as `True` (`yaml.safe_load("on:\n  pull_request_target: ...")` -> keys `[True, 'jobs']`), so its `pull_request_target` check never fires. `detecting-supply-chain-attacks-in-ci-cd/scripts/agent.py:52-74` flags only `main|master|latest` or `v\d+` refs, so `aquasecurity/trivy-action@0.28.0`, the tag style repointed in the 2026-03 trivy-action compromise and the one `scanning-containers-with-trivy-in-cicd/SKILL.md:91,108,228` recommends, passes unflagged. Prior record (security A, lines 148, 181-182): `integrating-sast-into-github-actions-pipeline` uses the deprecated `returntocorp/semgrep-action`; `building-devsecops-pipeline-with-gitlab-ci` and the AFL++ skill are off-target.
- **F21. sling: rejected.** It reads "CI that the StarSling GitHub App collected" (`SKILL.md:120-121`), so a run's data must flow to StarSling first; installation is a one-line installer from `docs.starsling.dev` (`SKILL.md:40-43`); organizations only, "The app installs on a personal repository but StarSling does not pick up its jobs" (`SKILL.md:162-164`). Both test repositories are user-owned. The `sling` binary is not installed (`command -v sling` empty).

## 9. Verdicts

| Skill | Verdict | Reasons | Risks if used | Pin |
| --- | --- | --- | --- | --- |
| ci-speedup | **Wrap the data pass only.** factory-ci runs `scripts/run.py` (with `--with-logs`) as a pinned measurement tool and reads `findings.json` (`pr_critical_path`, `required_checks`, `per_workflow_timing`, `data_bundle`, `runner_minute_spine`). It does not load SKILL.md, does not use the render or its menus, and owns its own report, savings and hand-off. | F1, F8, F10 and section 5: correct critical path, required checks, chains and step timings; read-only; 17-61 s and 100-260 calls on real repositories. | Success-only, unbounded sample (F12, F13): factory-ci must add per-workflow 30-day success, failure and cancel counts and queue time (1 to 3 `per_page=1` count calls per workflow) and state the sample's age. Maintainer-mode writes (F9): never commit the skill into a git-tracked tree; run it from the installed copy. Unstable `findings.json` schema and daily churn (F5, F19): re-run this evaluation, both test suites and both live repositories at every pin bump. Self-hosted cost rows (F11): drop the billable column for self-hosted runners. Raw logs in `<out>.data/`: keep under `.factory/ci/`, ignored by git. | `starslingdev/skills@cc891d0249e91c3615d894ac82b176a3421b0d74`, path `skills/ci-speedup`, tree `afc429b09744aee39df1d4ce2af8e35685a48a59` (installed, verified). That commit predates fixes #126 and #128; move to `a7c2db4a1e281ba8656de2b18b01f72dcc9effa1` (tree `ffbd9629ba8194ee9fc365b191858a20ceb09394`) only after repeating sections 2 and 5 on it. |
| ci-speedup methodology | **Borrow** into factory-ci's own rules | Required-check scoping by `needs:` reachability and ruleset enforcement and branch; pole frequency ranking; config-era split; admission gate (positive evidence only, absence is not proof); below-floor rule; serial-gate warning; non-additive totals; section 8 joint model; the no-weakening rail; risk, guardrail and rollout on structural levers; intent recovery from git history. | Fix while borrowing: monthly totals from mean per-run saving, not P50 difference (F11); call the pole gap a ceiling, not a win; no P95 claims below about 20 samples. | n/a |
| ci-score | **Reject** | Grade conflicts with the no-score stance; false fails and blind spots on both repositories (F16). | n/a | none |
| ci-secure | **Reject as engine**; borrow 3 hygiene checks and P14.24, P14.25 | zizmor 1.30.1 in factory-security covers its core vectors and more (F17); a second scanner would duplicate findings with different severities (P14.18 HIGH on a non-executing labeler, F15). | n/a | none |
| sling | **Reject** | Third-party data path and app install; orgs only (F21). | n/a | none |
| mukul975 CI skills (7) | **Reject** | Reproduced false negatives (F20); prior SEC-4 record. | n/a | none |

Posture "on the way" should therefore come from factory-security's existing zizmor run (same pin, same empty-directory invocation), plus ci-score's pinned-SHA share and timeout facts and ci-secure's three repository-settings checks, rewritten as factory checks.

## 10. Reproduction

Scratch directory (session-local): skill copies in `skills/`, clones in `repos/`, outputs in `out/` (`speedup-*`, `score-*`, `secure-*`, `tests-*.txt`), helper scripts `run_speedup.sh`, `run_other.sh`, `cmp_upstream.sh`, `check_timings.py` (independent per-job re-measurement from the jobs API). The scratch directory is not kept; the commands above are enough to repeat every number here.
