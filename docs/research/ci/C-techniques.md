# C: Technique catalog for `factory-ci` (S10)

Research date: 2026-10-10. Lane C answers one question per technique: what it saves, what it breaks, and how factory-ci can tell it applies.
Pin rule: a release published on or before 2026-09-26, checked with `gh api repos/<o>/<r>/releases`. Nothing was installed. Web pages are quoted as data.
Stacks in scope: TypeScript, React and Next.js (pnpm, npm), Rust (cargo), Go, Python (uv, pip, poetry), on GitHub Actions.

Each technique row gives: **Detect** (static = the workflow files alone, run = needs `gh run list` or job and step timings, or the cache API), **Saves** (with a cited number, or "no published number"), **Needs** (preconditions), **Breaks** (failure modes and security), **How** (current action and pin).

## 0. Measurements taken for this lane

**F1. Per-job fixed overhead is small on GitHub-hosted runners, but not zero.** Script `overhead.py` (scratchpad) over the last 8 successful push runs of three public repositories, using `gh api repos/<r>/actions/runs/<id>/jobs`:

```
astral-sh/ruff runs 8
 set-up-job n=161 p50=2s p90=5s
 checkout   n=158 p50=6s p90=9s
 queue      n=161 p50=3s p90=69s
 job-total  n=161 p50=182s p90=404s
pnpm/pnpm runs 8
 set-up-job n=59 p50=5s p90=40s
 checkout   n=57 p50=4s p90=13s
 queue      n=59 p50=7s p90=46s
 job-total  n=59 p50=91s p90=605s
BurntSushi/ripgrep runs 8
 set-up-job n=176 p50=1s p90=2s
 checkout   n=176 p50=1s p90=5s
 queue      n=176 p50=2s p90=8s
```

Reading: set-up plus checkout plus queue is about 5 to 16 s at p50, and 15 to 100 s at p90. The toolchain and dependency install that each extra job repeats costs more (F2). Billing rounds each job up to a whole minute (F31), so the cost of a fan-out is in runner minutes more than in wall clock.

**F2. Setup and cache-restore steps from the same run data.** `steps.py` (scratchpad), step names matching install, setup or cache:

```
pnpm/pnpm
  Install pnpm            n=30 p50=2s  max=4s
  Install Rust Toolchain  n=25 p50=7s  max=17s
  Cache pnpm              n=16 p50=8s  max=10s
  Install pnpm and Node   n=15 p50=13s max=34s
  Install hyperfine       n=14 p50=2s  max=4s     (cargo-binstall, prebuilt)
astral-sh/ruff
  Run astral-sh/setup-uv@c18668ad...  n=96 p50=1s  max=5s
  Run Swatinem/rust-cache@6323deb...  n=72 p50=19s max=347s
  Run actions/setup-node@82076278...  n=10 p50=5s  max=9s
```

A Rust cache restore has a 19 s median and a 347 s worst case in a repository with large caches (F3). A cache is a cost as well as a saving, and only run data shows which side wins.

**F3. Cache usage is readable for public repositories, and shows entries that are never reused.**

```
$ gh api repos/astral-sh/ruff/actions/cache/usage
{"full_name":"astral-sh/ruff","active_caches_size_in_bytes":53606655308,"active_caches_count":226}
$ gh api ".../actions/caches?sort=size_in_bytes" (top rows)
v0-rust-hawk-Linux-x64-1a092f59-d9dec187  refs/heads/main  821 MB  created 2026-10-09T16:33  last 2026-10-10T22:44
$ (entries whose created_at equals last_accessed_at to the minute)
never-restored-ish: 68 entries, 4.6 GB
```

ruff holds 53.6 GB of cache, above the 10 GB default, which confirms the limit is now raisable (F7). 68 of 226 entries (4.6 GB) look like they were written and never restored. The heuristic is rough (a restore within the same minute counts as never), but `actions/caches` gives factory-ci a direct, cheap signal for "uploading caches that never hit".

**F4. Clone cost, full history against shallow and partial, one sample from this machine (not a runner):**

```
$ git clone --bare --depth 1 https://github.com/astral-sh/ruff.git   real 6.06  17M
$ git clone --bare --filter=tree:0 ...                               real 4.36  18M
$ git clone --bare --filter=blob:none ...                            real 7.04  47M
$ git clone --bare ...                (full)                         real 24.05 236M
```

`actions/checkout` already defaults to depth 1 (F30), so the saving exists only where a workflow sets `fetch-depth: 0`. For ruff that is about 18 s and 219 MB per job, one sample.

## 1. Pins (published on or before 2026-09-26)

**F5. Command:** `gh api "repos/<r>/releases?per_page=100" --paginate` filtered to `published_at <= 2026-09-27`, sorted by version, then `gh api repos/<r>/git/ref/tags/<tag>` resolved to a commit.

| Action | Pin | Published | Commit | Newer, too fresh |
|---|---|---|---|---|
| actions/cache | v6.1.0 | 2026-06-26 | 55cc8345863c7cc4c66a329aec7e433d2d1c52a9 | |
| actions/checkout | v7.0.1 | 2026-07-20 | 3d3c42e5aac5ba805825da76410c181273ba90b1 | |
| actions/setup-node | v7.0.0 | 2026-07-14 | 820762786026740c76f36085b0efc47a31fe5020 | v7.1.0 (2026-10-08) |
| actions/setup-python | v7.0.0 | 2026-07-20 | 5fda3b95a4ea91299a34e894583c3862153e4b97 | |
| actions/setup-go | v7.0.0 | 2026-07-16 | b7ad1dad31e06c5925ef5d2fc7ad053ef454303e | |
| actions/upload-artifact | v7.0.1 | 2026-04-10 | 043fb46d1a93c77aae656e7c1c64a875d1fc6a0a | v7.0.2 (2026-10-07) |
| actions/download-artifact | v8.0.1 | 2026-03-11 | 3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c | v8.0.2 (2026-10-07) |
| pnpm/action-setup | v6.1.0 | 2026-09-05 | ea17c68df8912ef543352723c149a84f56e3d413 | |
| astral-sh/setup-uv | v10.2.0 | 2026-09-21 | c18668ad3cf93ea998bef934396af7bb5c839dc7 | v10.3.0 (2026-10-09) |
| Swatinem/rust-cache | v2.9.2 | 2026-08-06 | 6323deb102c322ba6fcbdcafc7e3dddab59af2b6 | |
| mozilla-actions/sccache-action | v0.0.11 | 2026-07-29 | fc920bf0ec8de6ee65d409111f7ec508035751ba | |
| taiki-e/install-action | v2.87.21 | 2026-09-26 | 4cef1412cce204788f482e778a0b9187f9626a29 | v2.87.27 (2026-10-09) |
| cargo-bins/cargo-binstall | v1.24.0 | 2026-09-26 | (binary, not an action) | v1.25.3 (2026-10-10) |
| actions-rust-lang/setup-rust-toolchain | v2.0.0 | 2026-09-07 | ecabd13d1c56bd1345c230e542e9144811ad706f | |
| docker/setup-buildx-action | v4.4.1 | 2026-09-16 | f87e5991a6d7451dcb8d9637bfbc97413f497069 | |
| docker/build-push-action | v7.4.0 | 2026-09-15 | c3c9e263c25d99ce0380d002d59b67737d91b0dc | |
| dorny/paths-filter | v4.0.3 | 2026-08-05 | ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d | |
| re-actors/alls-green | v1.3.0 | 2026-08-22 | b5b5b37504aa4183270bd3d855c52a67f212be35 | |
| nrwl/nx-set-shas | v5.0.1 | 2026-03-20 | afb73a62d26e41464e9254689e1fd6122ee683c1 | |
| vercel/turborepo (CLI) | v2.11.4 | 2026-09-24 | | v2.11.8-canary |
| nextest-rs/nextest (CLI) | cargo-nextest-0.9.146 | 2026-09-21 | | |

Cross-check: ruff's live workflows run `setup-uv@c18668ad`, `setup-node@82076278` and `rust-cache@6323deb1` (F2), the same commits as this table. Proposals should pin by commit SHA with the tag in a comment, because tags can be repointed (the trivy-action incident, docs/research/security/D-scanners.md section 1).

**F6. Release notes that change advice** (`gh api repos/<r>/releases/tags/<tag> --jq .body`):
- actions/cache v6.0.0: "Update packages, migrate to ESM". v6.1.0: "handle read-only cache access". No change to keys or paths, so v5 and v6 behave the same in a workflow.
- actions/checkout v7.0.0: "block checking out fork pr for pull_request_target and workflow_run". A speed proposal must never suggest checking out PR head code in those events.
- actions/setup-node v7.0.0: adds `cache-primary-key` and `cache-matched-key` outputs, and "docs: Update caching recommendations to mitigate cache poisoning risks".
- actions/setup-python v7.0.0: "Remove the pip-install input".

## 2. Caching

**F7. Repository cache limit, eviction and rate limits (2026).** https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching : the default is 10 GB per repository and it can be raised by repository, organization or enterprise admins, billed pay-as-you-go above the default. Entries "not accessed in over 7 days" are removed, and above the limit eviction is least recently used. Rate limits: 200 uploads and 1,500 downloads per minute per repository, with `Retry-After` on 429. The actions/cache README still says "up to 10GB" (`gh api repos/actions/cache/readme`, line 268), and so does the rust-cache README. Both are out of date. The upload limit started 2026-01-16 (https://github.blog/changelog/2026-01-16-rate-limiting-for-actions-cache-entries/, quoted in https://github.com/Mozilla-Actions/sccache-action/issues/238).

**F8. Branch scope.** Same page: a run restores from its own branch and the default branch, and a PR also from its base branch. Sibling and child branches are invisible, and tags are isolated. PR caches are scoped to `refs/pull/N/merge`, so only re-runs of that PR reuse them. Consequence: a cache that is only ever saved from PR runs never helps the next PR. Warm caches come from the default branch, so `save-if: github.ref == 'refs/heads/main'` (rust-cache) or a restore-only step on PRs (actions/cache `restore`) loses nothing on PR hit rates and cuts storage. Detect: run data (`actions/caches` `ref` field: many entries on `refs/pull/*`).

**F9. Cache thrashing is now a named failure.** sccache-action issue 238, written by GitHub staff (2026-01-19): "a substantial number of repositories adopting this library (or action) are exhibiting consistent cache thrashing behavior", where workflows produce more cache data than the quota holds, so entries are evicted and re-created and the result is "Little to no performance benefit from caching". Detect: run data (cache usage near the limit, `created_at` close to eviction, low `last_accessed_at` reuse, F3).

### 2.1 Technique rows

**T1. Dependency cache through the setup-* actions** (setup-node, setup-python, setup-go, setup-uv, pnpm/action-setup).
- Detect (static): `npm ci`, `pnpm install`, `pip install`, `poetry install`, `uv sync`, `go mod download` or `go build` with no `cache:` input and no actions/cache step in the same job. setup-node caches npm automatically only when `package.json` has `packageManager` or `devEngines.packageManager` set to npm (setup-node README lines 25, 199), pnpm and yarn need `cache:`. setup-python caching "is turned off by default" (README line 85). setup-go caching "is enabled by default" (README line 126). setup-uv `enable-cache: auto` is on for GitHub-hosted runners (F11).
- Saves: **F10.** https://pnpm.io/benchmarks (fetched 2026-10-10, fastest of three runs, 50 ms 200 Mbps emulated link), "alotta-packages" fixture: npm 12.2.0 clean 1m54s, lockfile-only 37.0s, cache plus lockfile 29.8s. pnpm 11.28.2: clean 26.7s, lockfile 13.1s, cache plus lockfile 6.43s. So the store cache saves 7 to 8 s for npm and 6.7 s for pnpm 11 on a large tree, over a lockfile install. The bigger saving in that table is npm to pnpm, which is a migration, not a CI fix. Run data: pnpm's own "Cache pnpm" step p50 8 s (F2), so the cache restore can cost as much as it saves on small trees.
- Needs: a committed lockfile (the key hashes it). setup-python warns that unpinned `requirements.txt` makes pip fetch newer versions anyway (README line 104).
- Breaks: none of these cache `node_modules` or a virtualenv for pip, so a hit still runs the install. setup-node advises `package-manager-cache: false` "for workflows with elevated privileges" (README line 211), the poisoning concern in section 3.
- How: `actions/setup-node@v7.0.0` with `cache: pnpm` after `pnpm/action-setup@v6.1.0`, or `pnpm/action-setup` `cache: true` (README line 99). `actions/setup-python@v7.0.0` `cache: pip|poetry|pipenv`. `actions/setup-go@v7.0.0` (default on).

**F11. uv: cache only what is expensive to rebuild.** https://docs.astral.sh/uv/concepts/cache/ recommends `uv cache prune --ci` at the end of the job: it drops pre-built wheels and keeps wheels built from source, because re-downloading pre-built wheels is often faster than restoring them. setup-uv `docs/caching.md` (`gh api repos/astral-sh/setup-uv/contents/docs/caching.md`): `prune-cache` defaults to `false` now, `enable-cache: auto` "is enabled on GitHub-hosted runners except for `release`, tag push, `pull_request_target`, and `workflow_run` events ... to prevent insecure or release-sensitive jobs from restoring potentially poisoned caches", and `save-cache: auto` skips saving on `merge_group` because those refs "are unlikely to be reused". Python installs are not cached by default for the same speed reason. No published number for prune. Run data from ruff: setup-uv p50 1 s (F2).
- How: `astral-sh/setup-uv@v10.2.0` with `enable-cache: true`, `prune-cache: true`.

**T2. Go build and module cache.**
- Detect (static): `actions/setup-go` with `cache: false`, or a manual actions/cache on `~/go/pkg/mod` only, or matrix jobs that all save the same key.
- Saves: no published number from the Go or setup-go docs.
- Needs and breaks: **F12.** setup-go `docs/advanced-usage.md`: the key hashes `go.mod` by default (`go.sum` via `cache-dependency-path`). It also caches `GOCACHE`, but "this cache is not updated based on source changes", so the build cache freezes at the first save for a given `go.mod` and drifts stale. Adding `**/*.go` to the key fixes freshness at the cost of "new caches on many commits". For matrices: "use distinct cache keys ... or create the cache in only one build and restore it in the other builds". Go's test result cache works only in package list mode, and `-count=1` disables it (https://pkg.go.dev/cmd/go). Whether test results hit after a fresh checkout depends on the files a test reads, not verified here.
- How: `actions/setup-go@v7.0.0`, `cache-dependency-path: go.sum`, save from main only.

**T3. Rust: Swatinem/rust-cache plus CI profile.**
- Detect (static): `cargo build|test|clippy` with no rust-cache, sccache or actions/cache on `target`. Toolchain installed after rust-cache (the key needs the rustc version). Nightly unpinned.
- Saves: **F13.** rust-cache README: "only caches the _dependencies_ of a crate, so it is more effective if the dependency / own code ratio is higher". It sets `CARGO_INCREMENTAL=0` itself, drops incremental artifacts, files older than a week and `~/.cargo/registry/src`. Nightly "will throw away the cache every day". corrode.dev (2025-01-28, updated 2025-08-16, https://corrode.dev/blog/tips-for-faster-ci-builds/) says "several minutes" with no measured figure. matklad (2021-09-04, https://matklad.github.io/2021/09/04/fast-rust-builds.html): rust-analyzer CI takes 8 minutes for about 200k lines plus 1M lines of dependencies, with incremental off, debuginfo off and only dependencies cached. Run data: ruff's restore p50 19 s, worst 347 s, entries of 650 to 820 MB (F2, F3).
- Needs: `Cargo.lock` committed. Stable or pinned nightly.
- Breaks: each job id gets its own key by default (`add-job-id-key: true`), so many jobs times many lockfile versions fills the quota (ruff, F3). Use `shared-key` across jobs with the same profile and `save-if` on main.
- How: `Swatinem/rust-cache@v2.9.2` after the toolchain step (`actions-rust-lang/setup-rust-toolchain@v2.0.0` or `rustup`).

**T4. Rust CI profile settings.**
- Detect (static): no `CARGO_INCREMENTAL=0` and no rust-cache (which sets it), `[profile.dev] debug` left at default in CI, no `CARGO_PROFILE_TEST_DEBUG=0`.
- Saves: matklad and corrode both say "Disable debuginfo, it makes `./target` much bigger, which again harms caching", no measured number in either. The direct effect is smaller caches and faster link, the size of which a run can measure (cache size before and after).
- Breaks: backtraces lose line numbers in CI test failures. Keep `line-tables-only` if that matters.
- How: `env: CARGO_INCREMENTAL: 0, CARGO_PROFILE_DEV_DEBUG: 0` (or `line-tables-only`), `CARGO_TERM_COLOR: always` is cosmetic only.

**T5. sccache with the GitHub Actions cache backend.**
- Detect (static): `RUSTC_WRAPPER=sccache` with `SCCACHE_GHA_ENABLED=true`.
- Saves: no published number from sccache or the action. It caches per compilation unit, so it helps when dependencies change often and rust-cache would miss.
- Breaks: **F14.** One cache entry per compiled crate collides with the 200 uploads per minute limit (F7). https://github.com/mozilla/sccache/issues/2593 (open, 2026-02-04): "Cache check failure with ErrorKind::RateLimited sets cache to read-only mode", with concurrent builds on different VMs. Thrashing warning in F9 names this library. Do not combine sccache and rust-cache on the same `target`.
- How: `mozilla-actions/sccache-action@v0.0.11`. Prefer rust-cache unless run data shows rust-cache missing often.

**T6. Next.js `.next/cache`.**
- Detect (static): `next build` with no cache on `.next/cache`. Run data: build log contains "No Cache Detected".
- Saves: https://nextjs.org/docs/app/guides/ci-build-caching gives no number. Its GitHub Actions example keys on the lockfile hash plus a hash of all `**/*.{js,jsx,ts,tsx}` with a lockfile-only `restore-keys` fallback (the example still says `actions/cache@v4`).
- Breaks: keying on all source files writes a new entry per commit. Combined with F8 (PR caches only reused by that PR), save from main only, or the cache becomes a thrash source.
- How: `actions/cache@v6.1.0` with the documented key.

**T7. Turborepo and Nx remote cache.**
- Detect (static): `turbo run` or `nx` without `TURBO_TOKEN`/`TURBO_TEAM` or an Nx Cloud token, `TURBO_FORCE: true` (disables caching), or a cache configured but never written (read-only token on all events).
- Saves: **F15.** https://turborepo.dev/docs/core-concepts/remote-caching says it "can save enormous amounts of time", no number. Turbo signs artifacts only if `remoteCache.signature: true` with `TURBO_REMOTE_CACHE_SIGNATURE_KEY`, and unsigned or failing artifacts are treated as a miss.
- Needs: deterministic task `outputs` and complete `env` inputs, otherwise a hit restores wrong output.
- Breaks: **F16.** CVE-2025-36852 "CREEP" (https://nx.dev/blog/cve-2025-36852-critical-cache-poisoning-vulnerability-creep, GitLab advisory CVSS 9.9): with bucket caches (S3, GCS, Azure, shared fs), a PR that changes only the CI workflow hashes to the same key as main, so "first-to-cache wins" and main restores the PR's artifact. Nx says the design "cannot be patched" and deprecated `@nx/s3-cache`, `@nx/gcs-cache`, `@nx/azure-cache`, `@nx/shared-fs-cache` on 2026-05-21. The advice generalizes to every self-hosted remote cache: untrusted builds must not write keys that trusted builds read.
- How: Turborepo v2.11.4 with signature on and a read-only token for PRs. Nx Cloud, or no remote cache, for Nx.

**T8. Docker buildx with `type=gha`.**
- Detect (static): `docker build` or `docker/build-push-action` without `cache-from`/`cache-to`. Several images built with `type=gha` and no `scope=` (each overwrites the last). `mode=max` on large multi-stage images.
- Saves: no published number from Docker.
- Breaks: **F17.** https://docs.docker.com/build/cache/backends/gha/ : default scope `buildkit`, "If you build multiple images, each build will overwrite the cache of the previous, leaving only the final cache." The backend "is subject to rate limiting", which can fail export with "maximum timeout reached". Only the v2 cache API works since 2025-04-15, which needs Buildx 0.21.0 or later and BuildKit 0.20.0 or later (https://docs.docker.com/build/ci/github-actions/cache/). It shares the repository quota with every other cache, and `mode=max` exports every intermediate layer, so it is a thrash source (F9).
- How: `docker/setup-buildx-action@v4.4.1`, `docker/build-push-action@v7.4.0` with `cache-from: type=gha,scope=<image>` and `cache-to: type=gha,mode=max,scope=<image>`. Fix layer order first (T22).

## 3. Cache poisoning

**F18. Mechanism.** Adnan Khan, "The Monsters in Your Build Cache" (2024-05-06, updated 2025-01-23, https://adnanthekhan.com/2024/05/06/the-monsters-in-your-build-cache-github-actions-cache-poisoning/): code running in a default-branch context (a `pull_request_target` "Pwn Request", a compromised dependency) can take the cache token and write entries. Keys and versions are client-chosen strings, the server only enforces the branch boundary, and restore extracts archives without checking paths, so an entry can overwrite files in a later privileged job. Filling the 10 GB quota evicts the targets first. Since January 2025, writes after the job ends are blocked, but in-job poisoning still works.

**F19. Real incident.** Ultralytics, December 2024: shell injection in a `pull_request_target` workflow, then a likely poisoned cache reaching the release job, then cryptominer releases on PyPI. PyPI's analysis (https://blog.pypi.org/posts/2024-12-11-ultralytics-attack-analysis/) advises avoiding `pull_request_target` and "shared caches during the build and release process". The cache step is inferred, not confirmed (https://blog.yossarian.net/2024/12/06/zizmor-ultralytics-injection notes the fix PR removed `cache: "pip"`).

**F20. Platform fix, June and September 2026.** https://github.blog/changelog/2026-06-26-read-only-actions-cache-for-untrusted-triggers/ : untrusted triggers that run in the default-branch scope (`pull_request_target`, `issue_comment`, fork `workflow_run` cascades) now get read-only cache tokens. `push`, `schedule`, `workflow_dispatch`, `repository_dispatch`, `delete`, `registry_package`, `page_build` keep write. `pull_request` and `release` keep write in their own scope. A denied save logs a warning and the job continues. https://github.blog/changelog/2026-09-10-control-github-actions-cache-access-with-cache-mode : `cache-mode: read | write | write-only | none` at workflow or job level, `read` is the default for low-trust events, and declaring `write` there "can increase the risk of cache poisoning". The workflow syntax page shows top-level `cache-mode: read`.

**F21. What factory-ci should do with this.**
- Static check, report beside any cache proposal: a release or publish job that restores any cache. PyPI and Adnan Khan both say not to. setup-uv already turns caching off for `release` and tag pushes (F11).
- Static check: `cache-mode: write` or `write-only` on `pull_request_target`, `issue_comment` or `workflow_run`.
- Never propose a cache whose key is reachable from untrusted builds and read by trusted ones outside the GitHub cache (T7, F16).
- A "missing cache" finding on a `pull_request_target` workflow is not a finding. The platform now denies the write on purpose.

## 4. Doing less

**T9. `paths` and `paths-ignore` filters, and the pending-forever trap.**
- Detect (static): expensive workflows triggered on `pull_request` with no path filter, while the repository has docs-only or sub-project-only changes in its history (run data: `gh pr list` with changed files).
- Saves: the whole workflow for skipped changes. No published average. factory-ci can measure it: runs whose changed files fall outside the workflow's inputs, times their minutes.
- Breaks: **F22.** https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks : when a workflow is skipped by path, branch or commit-message filtering, "Associated checks stay in a "Pending" state and block merging", and the advice is "Avoid requiring workflows that can be skipped." The workflow syntax page adds that `paths` evaluates only the first 3,000 changed files, and a push of more than 1,000 commits always runs.
- **F23. The correct workaround.** Always trigger the workflow, decide inside it, and require one gate job. https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions : "A job that is skipped will report its status as "Success"." and "It will not prevent a pull request from merging, even if it is a required check." That second sentence is the trap in the other direction: a plain `needs:` gate is skipped, so it passes, when a job it needs fails. re-actors/alls-green README: "in case when something fails, the `check` job's result is set to `skipped` and not `failed`". So: a `changes` job with `dorny/paths-filter@v4.0.3`, job-level `if:` on its outputs, and a required `check` job with `if: always()` running `re-actors/alls-green@v1.3.0` with `allowed-skips:` for the filtered jobs. Detect (static): required check names (branch protection API) that match a workflow with `paths:` filters, or a gate job with `needs:` and no `if: always()`.

**T10. Concurrency groups with cancel-in-progress.**
- Detect (static): `pull_request` workflows with no `concurrency:`. Run data: count of runs per PR head ref that were superseded and ran to completion.
- Saves: the full runner minutes of every superseded run. Wall clock for the final run is unchanged, except that it no longer queues behind old runs on busy self-hosted or larger-runner pools. No published number, measured per repository from run data.
- Breaks: **F24.** https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency : example `group: ${{ github.head_ref || github.run_id }}` with `cancel-in-progress: true`, which cancels only on PR events. "At most one job or workflow run can be `pending` in the concurrency group", and the older pending one is cancelled. A group keyed on `github.ref` with cancel on `push` to main cancels main builds, which loses cache saves (F8) and deploys. Include `github.workflow` in the group, or two workflows cancel each other.
- How: built in, no action.

**T11. Duplicate `push` plus `pull_request` triggers.**
- Detect (static): `on: [push, pull_request]` with `push` not restricted to the default branch. Run data: two runs with the same `head_sha`, one per event.
- Saves: up to half the PR runner minutes for same-repository branches. No external number. It is a direct count from run data.
- Breaks: fork PRs only fire `pull_request`, so keep that one. Restrict `push` to `branches: [main]`.

**T12. Affected-only builds.**
- Detect (static): monorepo markers (`turbo.json`, `nx.json`, `pnpm-workspace.yaml`, Cargo `[workspace]`, `go.work`, several `go.mod`) with CI that runs every package.
- Saves: **F25.** Nx (https://nx.dev/docs/features/ci-features/affected) says affected "drastically improves the speed" but warns it "might not be sufficient" when a change touches a widely used project. No number. The saving is the share of packages untouched by a typical PR, which run data plus `git diff` can estimate.
- Needs and breaks: Turborepo `--affected` is `--filter=...[main...HEAD]`, and "If the checkout is too shallow, then all packages will be considered changed" (https://turborepo.dev/docs/reference/run). Nx needs `fetch-depth: 0` or `nrwl/nx-set-shas@v5.0.1`, which sets `NX_BASE` to the last successful main run. A shallow clone therefore silently disables the saving (no failure, no speedup). Root-level config changes (lockfile, tsconfig base, CI files) must map to "everything", or affected misses real breakage.
- How, per stack: `turbo run test --affected` (v2.11.4), `nx affected -t test`, Go: `go list -deps -test ./...` reverse lookup or per-module path filters (no official affected tool), Cargo: `cargo test -p <crate>` from changed paths (no official affected tool, `cargo-hack` or path filters).

**T13. Merge queue.**
- Detect (static): branch protection with "require branches to be up to date" and no `merge_group` trigger. Run data: PRs with several "update branch" re-runs before merge.
- Saves: **F26.** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue : the queue "provides the same benefits as the Require branches to be up to date before merging" setting without making authors update and re-wait. No number. It removes repeated rebase re-runs, and lets PR CI run a cheaper subset while the queue runs the full suite.
- Breaks: "You must use the `merge_group` event", otherwise "The merge will fail as the required status check will not be reported." Path-filtered workflows hit F22 again. Merge-queue refs are temporary, so their cache saves are waste (setup-uv skips them, F11).

**T14. Skip on docs-only changes and drafts.**
- Same mechanics as T9, with F23's gate. Draft gating: job-level `if: github.event.pull_request.draft == false` plus `types: [opened, synchronize, reopened, ready_for_review]`. Skipped jobs report Success (F23), and drafts cannot be merged, so the skip is harmless. Low risk.

## 5. Doing it in parallel

**T15. Job fan-out against setup overhead.**
- Detect: run data. A serial job whose test step dominates, and setup (F1 plus F2) is small relative to the test step.
- Saves: wall clock up to the longest split. Cost: each extra job pays F1 (about 5 to 16 s p50) plus install (F2, F10) plus a round-up to the next minute (F31). Rule of thumb from these numbers: fan out when the split step is minutes and setup is seconds. Merging short jobs is the reverse fix.
- Breaks: more jobs means more cache writes (F7 rate limit) and more required-check names (F23).

**T16. Test sharding.**
- Detect (static): test commands with no shard flag in a single job. Run data: that step's p50 over a few minutes.
- Saves: up to 1/N of the test step per job, bounded by shard balance. **F27.** Playwright (https://playwright.dev/docs/test-sharding): `--shard=x/y`, balanced per test only with `fullyParallel`, otherwise per file and "certain shards may end up running significantly more tests". Merge with the blob reporter and `npx playwright merge-reports`. Vitest (https://vitest.dev/guide/improving-performance): "splits your _test files_, not your test cases", `--reporter=blob --shard=N/M`, then `--merge-reports`. Jest: `--shard=i/n` (https://jestjs.io/docs/cli, which does not state the version that added it), a custom `testSequencer` must implement `shard`. pytest-split (https://github.com/jerry-git/pytest-split): `--splits N --group i` from a committed `.test_durations`, `least_duration` balances better, `duration_based_chunks` breaks with random ordering plugins. cargo-nextest (https://nexte.st/docs/ci-features/partitioning/): `--partition hash:m/n` (stable) or `slice:m/n` (even, shifts when tests change), `count:` deprecated, and build once with an archive so shards do not each recompile. None of these pages publish a CI speedup figure.
- Breaks: shards each repeat setup (T15). Coverage and reports need a merge job. Order-dependent tests surface.

**T17. In-process parallelism (before adding jobs).**
- **F28.** pytest-xdist (https://pytest-xdist.readthedocs.io/en/stable/distribution.html): `-n auto` uses physical cores, `--dist loadscope|loadfile|loadgroup|worksteal`. cargo-nextest benchmarks (https://nexte.st/docs/benchmarks/, Ryzen 9 7950X, 16 cores): 1.37x (penumbra) to 3.38x (crucible) over `cargo test`, tokio 24.27 s to 11.60 s. corrode says about 40% in CI "because runners have fewer cores". Go: `go test -p` defaults to GOMAXPROCS (https://pkg.go.dev/cmd/go), so the knob is `t.Parallel()` in tests, not a flag. Jest `--maxWorkers` defaults to cores minus one. Vitest: `pool: threads` with `isolate: false` is "the fastest option" if tests tolerate shared state, jsdom costs about 200 to 500 ms per file under isolation.
- Saves: up to the core count. Private-repo standard runners have 2 vCPU, public ones 4 (F32), so in-process parallelism on private repos is capped near 2x.
- Breaks: shared fixtures (databases, ports, temp dirs) race.

**T18. Matrix trimming.**
- Detect (static): matrix over `os: [ubuntu, macos, windows]` or many language versions on every PR. Code with no platform-specific paths.
- Saves: **F29.** By price (F31): a macOS minute is $0.062 against $0.006 for Linux x64 2-core, 10.3x, Windows 2-core is $0.010, 1.7x. Wall clock is often bounded by macOS queue time (run data: queue time per label).
- Breaks: platform bugs found later. Keep the full matrix on main, nightly or the merge queue, and run Linux plus the oldest supported version on PRs.

**T19. Split lint, typecheck and test into parallel jobs.**
- Detect (static): one job running `lint && typecheck && test` serially.
- Saves: wall clock down to the longest of the three, at the cost of two extra setups (F1, F2). Worth it only when two of them are long. No published number.

## 6. Faster pieces

**T20. Checkout depth and sparse checkout.**
- **F30.** actions/checkout README line 31: "Only a single commit is fetched by default", `fetch-depth: 0` fetches all history. Inputs: `filter` (partial clone, overrides sparse), `sparse-checkout`, `sparse-checkout-cone-mode`, `fetch-tags`, `lfs`.
- Detect (static): `fetch-depth: 0` in jobs that never run `git log`, `git describe`, `turbo --affected`, `nx affected`, changelog or versioning tools. `lfs: true` or `submodules:` in jobs that do not read them.
- Saves: F4, about 18 s and 219 MB for ruff, one sample. Larger for big histories. Where history is needed, `filter: tree:0` or `blob:none` keeps it cheaper (F4). GitHub's guidance (https://github.blog/open-source/git/get-up-to-speed-with-partial-clone-and-shallow-clone/, 2020) supports shallow clones for one-off CI builds and warns against fetching from them later.
- Breaks: affected-only tools fall back to "everything changed" silently (T12).

**T21. Larger runners and ARM runners.**
- **F31.** https://docs.github.com/en/billing/reference/actions-runner-pricing (per minute): Linux x64 2-core $0.006, 4-core $0.012, 8-core $0.022, 16-core $0.042. Linux arm64 2-core $0.005, 4-core $0.008, 8-core $0.014, 16-core $0.026. Windows 2-core $0.010. macOS $0.062. Jobs round up to a whole minute, larger runners are "not free for public repositories", and included minutes do not apply to them.
- **F32.** https://docs.github.com/en/actions/reference/runners/github-hosted-runners : standard Linux, Windows and arm64 runners have 4 vCPU and 16 GB for public repositories and 2 vCPU and 8 GB for private ones. `ubuntu-slim` is 1 vCPU, enough for gate and filter jobs. arm64 labels: `ubuntu-24.04-arm`, `ubuntu-22.04-arm`, `ubuntu-26.04-arm`.
- Saves: no neutral benchmark of GitHub larger runners was found. GitHub's ARM claim is "up to a 40% performance boost compared to Microsoft Azure's previous generation of Arm-based VMs" (https://github.blog/changelog/2025-01-16-linux-arm64-hosted-runners-now-available-for-free-in-public-repositories-public-preview/), which is not a comparison with x64 runners. The arithmetic: a 4-core x64 job costs the same as a 2-core job when it finishes in half the time. An arm64 4-core minute ($0.008) costs a third more than an x64 2-core minute ($0.006), so it pays off when it is at least 25% faster. corrode's author found queue time "dwarfed" the ARM speedup in his tests.
- Detect: run data only. CPU-bound steps (compile, test) longer than a few minutes on 2-core private runners. Static only shows the label.
- Breaks: ARM needs every native dependency and Docker base image for arm64. Larger runners have their own queues and cost on public repos.

**T22. Docker layer order.**
- Detect (static): `COPY . .` before the dependency install in a Dockerfile, no `.dockerignore`.
- Saves: the whole install layer on every source-only change. https://docs.docker.com/build/cache/optimize/ : "Steps that change often should appear near the end", "First, copy over the package management files", then source. No number. `RUN --mount=type=cache` helps only where the builder persists (ephemeral runners need an external cache, T8).

**T23. Service container readiness.**
- Detect (static): `sleep N` or retry loops after starting services or `docker compose up`. **F33.** https://docs.github.com/en/actions/how-tos/use-cases-and-examples/using-containerized-services/creating-postgresql-service-containers uses `--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5` under `services.<id>.options`, with the comment "Set health checks to wait until postgres has started".
- Saves: the fixed sleep minus real start time, every run. Exact from logs (run data: the sleep step's duration). No external number needed.
- Breaks: a health command that passes before the service accepts the app's queries. `docker compose up --wait` is the compose equivalent.

**T24. Prebuilt tool binaries instead of `cargo install` or `go install`.**
- Detect (static): `cargo install <tool>` or `go install` of a tool in CI, uncached.
- Saves: run data from pnpm/pnpm: `Install hyperfine` through cargo-binstall p50 2 s (F2). The compile it replaces is not measured here. **F34.** taiki-e/install-action README: SHA256 checksums on by default, attestation or signature checks where the tool publishes them, a one-day "dependency cooldown" for unpinned versions, and the default `fallback: cargo-binstall` gets `github.token` passed in, so `fallback: none` "helps enhance security".
- How: `taiki-e/install-action@v2.87.21` with `tool: cargo-nextest@0.9.146` and `fallback: none`. cargo-binstall v1.24.0 for tools outside its list.

**T25. TypeScript incremental and ESLint cache.**
- Detect (static): `tsc --noEmit` or `eslint .` in CI with no `.tsbuildinfo` or `.eslintcache` cached.
- Saves: no published number from either project. TypeScript: `incremental` saves the project graph to `.tsbuildinfo` (https://www.typescriptlang.org/tsconfig/incremental.html). ESLint: `--cache` reuses results for unchanged files, and `--cache-strategy content` exists because "git does not track file modification time", for example after `git clone` (https://eslint.org/docs/latest/use/command-line-interface). So in CI, a restored `.eslintcache` with the default `metadata` strategy treats every file as changed, since a fresh checkout has new mtimes. This is an inference from the docs, not measured here.
- Breaks: a stale cache can hide errors when config or plugin versions change, so include the lockfile and the config files in the key.

**T26. Artifact handoff instead of rebuilding.**
- Saves: run data. ruff downloads a benchmark binary with p50 6 s (max 35 s, n=45), uv downloads its binary with p50 3 s (n=47), instead of each job compiling it. nextest archives do the same for test binaries (T16).
- Cost: **F35.** https://github.blog/changelog/2023-12-14-github-actions-artifacts-v4-is-now-generally-available/ : v4 has "up to 10x performance improvements", artifacts are immutable, 500 per job. upload-artifact README: default zlib level 6, and "For large files that are not easily compressed, a value of 0 is recommended for significantly faster uploads". Uploading on every PR what nobody downloads is an anti-pattern (A3).
- How: `actions/upload-artifact@v7.0.1`, `actions/download-artifact@v8.0.1`.

## 7. Anti-patterns that cost time

- **A1. Sleep-based waits.** T23. Static: `sleep` in `run:` steps. Measured exactly from the step duration.
- **A2. Redundant installs across jobs.** Static: identical checkout, setup, install sequences in N jobs that could be one job, or a build repeated in jobs that could download an artifact (T26). Cost per job: F1 plus F2 plus F10.
- **A3. Artifact upload and download overhead.** Run data: upload steps on every PR whose artifacts are never downloaded (`gh api repos/<r>/actions/artifacts` has no download count, so check whether any later job or workflow downloads that name). Compression on already-compressed files (F35).
- **A4. Caches that never hit or thrash.** Run data: F3 (entries created and never accessed), F9 (quota thrash), F2 (restore longer than the work it saves, ruff worst case 347 s). Static hints: keys containing `github.sha`, `github.run_id` or dates, or keys hashing all source files saved from PRs (F8).
- **A5. OS matrix not needed.** T18, F29.
- **A6. push plus pull_request duplicated.** T11.
- **A7. Missing concurrency cancel.** T10.
- **A8. `fetch-depth: 0` without a history consumer.** T20.
- **A9. Release job restoring caches.** Not a speed problem, a poisoning one (F18 to F21). Report it beside any cache proposal.

## 8. Ranking

Saving: H = minutes per run or a large share of runner minutes, M = tens of seconds to a few minutes, L = seconds. Risk: what can go wrong if applied blindly. Detect: S = static read is enough, R = run data needed to size it or to confirm it applies, S+R = static finds the candidate and run data sizes it.

| Rank | Technique | Saving | Risk | Detect | Evidence |
|---|---|---|---|---|---|
| 1 | T10 concurrency cancel-in-progress | H (minutes, not wall clock) | L | S+R | F24 |
| 2 | T9 + F23 path filters with an always-run gate | H on skipped changes | M (pending forever, or false green without alls-green) | S+R | F22, F23 |
| 3 | T16 test sharding | H on long suites | M (balance, report merge, setup per shard) | S+R | F27 |
| 4 | T12 affected-only builds | H in monorepos | M (shallow clone disables it silently, root config) | S+R | F25 |
| 5 | T23 health checks instead of sleep | M, exact | L | S | F33 |
| 6 | T3 + T4 rust-cache and CI profile | H for Rust | L to M (quota, stale on nightly) | S+R | F13, F2, F3 |
| 7 | T1 dependency caches via setup-* | M | L (M on privileged workflows) | S | F10, F11 |
| 8 | T11 duplicate triggers | M to H (minutes) | L | S | run count |
| 9 | T17 in-process parallelism (nextest, xdist) | M to H | M (shared state) | S+R | F28 |
| 10 | T24 prebuilt tool binaries | M | L with checksums | S | F2, F34 |
| 11 | T18 matrix trimming | M wall, H cost on macOS | M (late platform bugs) | S+R | F29, F31 |
| 12 | T13 merge queue | M to H (fewer re-runs) | M (process change, `merge_group`) | R | F26 |
| 13 | T7 remote cache (Turbo, Nx) | H when it hits | H (CREEP, wrong outputs) | S | F15, F16 |
| 14 | T6 Next.js cache | M | L to M (thrash if keyed per commit on PRs) | S+R | Next docs |
| 15 | T8 Docker gha cache | M to H | M (scope overwrite, rate limit, quota) | S+R | F17 |
| 16 | T21 larger or ARM runners | M to H for CPU-bound | M (cost, arm64 deps, queues) | R | F31, F32 |
| 17 | T15 / T19 fan-out and splitting | M wall clock | L (more minutes) | R | F1 |
| 18 | T26 artifact handoff | M | L | S+R | F35 |
| 19 | T5 sccache on GHA | M | M (rate limit to read-only, thrash) | S+R | F14 |
| 20 | T2 Go caches | L to M | L (stale GOCACHE) | S | F12 |
| 21 | T20 shallow and partial checkout | L to M | L (breaks history consumers) | S | F4, F30 |
| 22 | T25 tsbuildinfo and ESLint cache | L | L (stale on config change) | S | T25 docs |
| 23 | T22 Docker layer order | M on Docker builds | L | S | Docker docs |

Static-only detections, ready for a lint pass: T1, T2, T11, T20, T22, T23, T24, T25, A9, F23's gate pattern, F21's cache-mode and release checks. Everything that claims a number needs run data: per-step timings (`gh api .../jobs`), cache listings (`.../actions/caches`, `.../actions/cache/usage`), run counts per head SHA and per PR, and queue time per runner label.

## 9. Prior art on this machine

**F36.** `~/.claude/skills/ci-speedup` (installed, MIT, 2026-10-02) already catalogs 78 patterns (`references/optimization-patterns.md`, 4,211 lines: `grep -n "^### OPT"`), with run collection scripts and tests. Its catalog overlaps this one: OPT5 pnpm store, OPT6 key entropy, OPT17 sleep readiness, OPT24 sharding, OPT28 full history, OPT32 path filters, OPT45 and OPT46 concurrency, OPT47 push plus pull_request, OPT79 a cache that costs more than it saves. It reports a measured critical path and leaves the fix to an agent. What this lane adds over it: 2026 platform changes (cache limit raisable, upload rate limit, read-only tokens, `cache-mode`), the alls-green false-green trap, CREEP, current pins, and the per-technique risk. Lane decisions (reuse, wrap or replace it) belong to the selection record, not here.

## 10. Where no number exists

No published, neutral measurement was found for: setup-go caching, sccache on GHA, rust-cache (beyond "several minutes"), Next.js `.next/cache`, Turborepo or Nx remote cache, Docker `type=gha`, shard speedups for Playwright, Vitest, Jest or pytest-split, ESLint and TypeScript caches, GitHub larger runners against standard ones, merge queue. For these factory-ci should state "no published number" and measure on the user's own runs: step duration before and after, cache hit rate from `cache-hit` outputs and the caches API, and runner minutes from job durations rounded up per job.
