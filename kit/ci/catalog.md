# plumb-ci catalog

What plumb-ci looks for in workflows and run data, and the fix it proposes. IDs match the evidence in `docs/research/ci/C-techniques.md` of the Plumb repository (T techniques, A anti-patterns); A10 and W1 are plumb-ci's own, and A5 to A7 are covered by T18, T11 and T10. Detect: **S** a read of the workflow files is enough, **R** it needs `summary.json`, **S+R** the files find it and the data sizes it.

## Rules for every proposal

- **Never buy speed by checking less.** No test, check, platform or required check is removed or skipped unless it still runs where it guards something: main, the merge queue, or a schedule. A path filter always comes with the gate in T9.
- Pin every action to a commit SHA with its tag as a comment. The pins below were published on or before 2026-09-26; newer releases are left until they are two weeks old.
- A cache proposal never adds a cache to a release or publish job, never makes a `pull_request_target`, `issue_comment` or `workflow_run` job write a cache, and never adds a remote cache that untrusted builds can write and trusted builds read (A9, T7). A missing cache on those triggers is not a finding: GitHub has denied the write on purpose since June 2026.

## Doing less

- **T10 concurrency cancel-in-progress.** S+R. `pull_request` workflows with no `concurrency:`; size with cancelled and superseded runs per head ref. Fix: `concurrency: { group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}, cancel-in-progress: true }`. Guard: never cancel on `push` to the default branch (it loses cache saves and deploys); keep `github.workflow` in the group.
- **T9 path filters with an always-run gate.** S+R. Expensive `pull_request` workflows with no path filter while many PRs touch only docs or one sub-project. Fix: always trigger; a `changes` job with `dorny/paths-filter@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d # v4.0.3`; job-level `if:` on its outputs; one required `check` job with `if: always()` running `re-actors/alls-green@b5b5b37504aa4183270bd3d855c52a67f212be35 # v1.3.0` with `allowed-skips:`. The user then makes `check` the required check (a repository setting: plumb-ci says so and never changes it). Guard: a workflow-level `paths:` on a required check leaves it pending forever; a plain `needs:` gate is skipped, and so passes, when a job it needs fails. Flag both wherever they exist already.
- **T11 duplicate triggers.** S. `on: [push, pull_request]` with `push` not limited to the default branch; data shows two runs per `head_sha`. Fix: `push: { branches: [main] }`, keep `pull_request` (forks fire only that).
- **T12 affected-only builds.** S+R. Monorepo markers (`turbo.json`, `nx.json`, `pnpm-workspace.yaml`, Cargo `[workspace]`, `go.work`) with CI running every package. Fix: `turbo run <task> --affected`, `nx affected -t <task>` with `nrwl/nx-set-shas@afb73a62d26e41464e9254689e1fd6122ee683c1 # v5.0.1`, or per-package path filters (T9). Guard: a shallow clone silently marks everything changed; root config, lockfile and CI files must map to "everything".
- **T13 merge queue.** R. Branches must be up to date (`up_to_date_required_by_ruleset`, or the user says so) and PRs re-run several times before merge. Fix: a merge queue with the `merge_group` trigger on every required workflow. Guard: without `merge_group` the required check never reports.
- **T14 drafts.** S. Fix: `if: github.event.pull_request.draft == false` with `ready_for_review` in `types`. Docs-only changes: T9.

## Doing it in parallel

- **T16 test sharding.** S+R. A test step of several minutes in one job, on the critical path. Fix per runner: Playwright `--shard=i/n` (with `fullyParallel`) and `merge-reports`; Vitest `--shard=i/n --reporter=blob` then `--merge-reports`; Jest `--shard=i/n`; pytest-split `--splits n --group i` from a committed `.test_durations`; cargo-nextest `--partition hash:i/n` from one archived build. Guard: each shard pays setup again (T15); reports and coverage need a merge job.
- **T17 in-process parallelism first.** S+R. Fix: `cargo nextest`, `pytest -n auto` (pytest-xdist), Vitest threads, `t.Parallel()` in Go. Guard: shared databases, ports and temp directories race. Private repositories get 2 vCPU runners, so the ceiling is near 2x.
- **T15, T19 fan-out and splitting.** R. Split lint, typecheck and test only when two of them take minutes; merge short jobs whose setup costs more than their work. Each job adds about 5 to 16 s of setup at p50, plus installs, plus a round-up to the minute.
- **T18 matrix trimming.** S+R. An OS or version matrix on every PR. Fix: Linux plus the oldest supported version on PRs, the full matrix on main, the merge queue or a schedule. Guard: platform bugs surface later; say where the full matrix still runs.

## Caches

- **T1 dependency caches through setup actions.** S. An install (`npm ci`, `pnpm install`, `pip install`, `poetry install`, `uv sync`) with no cache input and no cache step in the job. Fix: `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0` with `cache: pnpm` after `pnpm/action-setup@ea17c68df8912ef543352723c149a84f56e3d413 # v6.1.0`; `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0` with `cache: pip|poetry`; `astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0` with `enable-cache: true` and `prune-cache: true`. Guard: needs a committed lockfile; on a small tree the restore can cost what it saves, so size it from the step timings; in privileged workflows set `package-manager-cache: false`.
- **T2 Go caches.** S. `actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0` caches by default; key on `go.sum`, save from main only, one saving job per matrix. Guard: the build cache is never refreshed for an unchanged `go.sum`, so it drifts stale; add the sources to the key only if run data shows the cost is worth the extra entries.
- **T3, T4 Rust.** S+R. `cargo` with no `Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2` after the toolchain step; `CARGO_INCREMENTAL: 0` and `CARGO_PROFILE_DEV_DEBUG: 0` (or `line-tables-only`). Use `shared-key` across jobs with one profile and `save-if: ${{ github.ref == 'refs/heads/main' }}`. Guard: per-job keys fill the quota; nightly throws the cache away daily.
- **T5 sccache.** S+R. Only when run data shows rust-cache missing often; never with rust-cache on the same `target`. It hits the 200 uploads per minute limit.
- **T6 Next.js.** S. `next build` with no cache on `.next/cache`. Fix: `actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0` keyed on the lockfile and sources, saved from main only.
- **T7 Turborepo and Nx remote cache.** S. Only Turborepo with `remoteCache.signature: true` and a read-only token on PRs, or Nx Cloud. Bucket caches are poisonable from PRs (CVE-2025-36852).
- **T8 Docker layers on the GitHub cache.** S+R. Fix: `docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1` and `docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0` with `cache-from` and `cache-to: type=gha,mode=max,scope=<image>`. Guard: one `scope` per image, or each build overwrites the last; fix layer order (T22) first.
- **A4 caches that never hit or thrash.** R. `caches.never_restored`, `caches.on_pull_refs`, a total near the repository limit, keys with `github.sha`, `github.run_id` or dates. Fix: save from the default branch only, restore elsewhere; `uv cache prune --ci`; fewer, shared keys.

## Faster pieces

- **T23 health checks instead of sleep (A1).** S. `sleep N` or retry loops after starting services. Fix: `options: --health-cmd ... --health-interval 10s --health-timeout 5s --health-retries 5` on the service, or `docker compose up --wait`. Exact saving: the sleep step's duration minus real start time.
- **T24 prebuilt tool binaries.** S. `cargo install` or `go install` of a tool in CI. Fix: `taiki-e/install-action@4cef1412cce204788f482e778a0b9187f9626a29 # v2.87.21` with `tool: <name>@<version>` and `fallback: none`.
- **T20 checkout depth (A8).** S. `fetch-depth: 0` in a job that never reads history (`git log`, `git describe`, affected tools, changelog or version tools); `lfs: true` or `submodules:` where nothing reads them. Fix: the default depth, or `filter: tree:0` where history is needed. Pin: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`.
- **T21 larger or ARM runners.** R. CPU-bound steps of several minutes on 2-core private runners. Arithmetic, never a promise: a 4-core x64 job costs the same as a 2-core one when it halves the time; arm64 4-core pays off when at least 25% faster than x64 2-core. Guard: native dependencies and base images for arm64; larger runners have their own queues.
- **T22 Docker layer order.** S. `COPY . .` before the dependency install, or no `.dockerignore`.
- **T25 TypeScript and ESLint caches.** S. Fix: cache `.tsbuildinfo` and `.eslintcache` with `--cache-strategy content` (a fresh checkout has new mtimes), keyed on the lockfile and the config files.
- **T26 artifact handoff.** S+R. The same build repeated in several jobs. Fix: build once, `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1` and `actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1`; compression level 0 for already-compressed files.

## Waste

- **A2 redundant installs.** S. The same checkout, setup and install in many jobs, or an action that installs what the runner image already has (zizmor `superfluous-actions`).
- **A3 artifacts nobody downloads.** S+R. Uploads on every PR with no job or workflow downloading that name.
- **A9 caches in privileged jobs.** S. A release or publish job that restores any cache, or `cache-mode: write` or `write-only` on `pull_request_target`, `issue_comment` or `workflow_run`. A poisoning risk, not a speed one: report it beside any cache proposal.
- **A10 no job timeout.** S. A job without `timeout-minutes` can hang for the 360-minute default. Fix: a timeout a few times the job's p90.

## Run-data findings with no static signal

- **Queue.** `queue_seconds_by_label`: a label whose median queue is minutes (macOS concurrency, a busy self-hosted pool). Fix depends on the label: fewer jobs on it per PR (T18), a larger concurrency plan, or more self-hosted capacity.
- **Rerun and failure cost.** `runner_minutes_by_outcome`: minutes in failed runs and in jobs a re-run did again. Call it rerun cost, not a flake rate.

## Posture beside speed

Besides the zizmor audits in `tools.yaml`:

- **W1 CODEOWNERS.** S. No CODEOWNERS entry covers `.github/workflows/`, so any writer can change what CI runs with its secrets.

Anything that needs a verdict (a privileged trigger, a self-hosted runner on a public repository, cloud keys instead of OIDC) is named and handed to `/plumb-security`; plumb-ci never confirms a security finding.
