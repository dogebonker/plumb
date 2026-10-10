# D: Tools and posture checks for `factory-ci` (S10)

Research date: 2026-10-10. Pin rule: a release published on or before 2026-09-26 (at least two weeks old).
Release dates, licenses, asset digests, attestations and the immutable-release flag come from the GitHub API
(`gh api repos/<o>/<r>/releases`, `.../releases/tags/<t>`, `.../attestations/<digest>`). Nothing was installed,
no package was downloaded, no `npx` was run. Workflow files were copied to a scratch directory before any tool
read them; no file in the audited repositories was written.

## 0. Local machine state (checked, not assumed)

| Tool | Installed | Notes |
|---|---|---|
| actionlint | 1.7.12 (Homebrew), go1.26.3 | Works. shellcheck and pyflakes are on PATH, so actionlint runs them on `run:` scripts. |
| gh | 2.92.0 (2026-04-28) | Works. Extensions: only `github/gh-stack`. Two accounts logged in; the active one is the user's work account. |
| zizmor, pinact, ratchet, frizbee, act | not installed | `which` returns nothing for each. |
| starslingdev `ci-speedup`, `ci-secure`, `ci-score` | installed as skills in `~/.agents/skills`, 2026-10-02 | See F9. |

Repositories read (copies in scratch): `edgeflow` (2 workflows), `moneylust-app` (19), `pond` (2, plus local actions),
`glarity` (1). Across `~/Work`, 13 of 31 directories have `.github/workflows`; none has `.gitlab-ci.yml`, `.circleci`,
`.buildkite`, `Jenkinsfile`, `azure-pipelines.yml`, `.drone.yml`, `bitbucket-pipelines.yml` or `.woodpecker*`.

## 1. Tool table

| Tool | License | Pin (date) | Install and verification | Phones home | Reads | Executes repo content |
|---|---|---|---|---|---|---|
| actionlint | MIT | v1.7.12 (2026-03-30) | release tarball + `checksums.txt`; 1 SLSA v1 provenance attestation (built by `.github/workflows/release.yaml` at the tag); release not immutable. Homebrew copy is the same version | No (`net/http` appears only in its code generators under `scripts/`) | workflow files, `.github/actionlint.yaml` | No. Runs shellcheck and pyflakes as static checkers on `run:` text |
| zizmor | MIT | v1.30.1 (2026-09-09), same as factory-security | GitHub release: immutable, 2 attestations. PyPI wheel (the current `uv tool install` line): no PEP 740 provenance (HTTP 404) | Only online audits, to the GitHub API, when a token is set | workflows, `action.yml`, `dependabot.yml`, `zizmor.yml` unless `--no-config` | No |
| pinact | MIT | v5.0.0 (2026-09-12); v4.1.1 (2026-07-30) is the conservative choice | immutable release; `checksums.txt` + sigstore bundle, in-toto, SBOM; 2 attestations | GitHub API to resolve tags to SHAs; `--no-api` for an offline check | workflows and action files; **rewrites them unless `--check` / `--fix=false`** | No |
| ratchet | Apache-2.0 | v0.12.0 (2026-07-18) | `SHA512SUMS`; 1 attestation; not immutable | GitHub API, and container registries for image pins | workflows; rewrites them (`pin`, `update`), `lint` is read-only | No |
| frizbee | Apache-2.0 | v0.1.11 (2026-08-14) | per-asset sigstore bundles, checksums, SBOM; no GitHub attestation; not immutable; pre-1.0, 186 stars | GitHub API, registries | workflows; rewrites them (has dry-run) | No |
| act | MIT | v0.2.89 (2026-06-01) | `checksums.txt` only; no attestation; not immutable | **Yes**: `https://api.nektosact.com/notices` with OS, arch and version (`cmd/notices.go`), off with `ACT_DISABLE_VERSION_CHECK=1`. Pulls runner images (large image: ~17 GB download) | everything | **Yes**: runs every `run:` step and every action in Docker, Docker socket mounted by default |
| gh | MIT | v2.101.0 (2026-09-15); local 2.92.0 | immutable release, 2 attestations, `gh attestation verify` | **Yes**: telemetry on by default (see F7); daily update check | GitHub API | No. Logs (`gh run view --log`) are repository-controlled text |
| gh-workflow-stats (`fchimpan`) | MIT | v0.4.1 (2025-12-30), 112 stars | bare binaries, no checksums, no attestation; `gh extension install` verifies nothing | GitHub API | runs, jobs, steps | No, but runs as the user with the user's gh token |
| catchpoint/workflow-telemetry-action | Apache-2.0 | v2.0.0 (2024-02-15), last push 2024-07-24, 50 open issues | an action added to the workflow; `node20` | **Yes**: posts CPU, memory, I/O series to `https://api.globadge.com/v1/chartgen/...` (`src/statCollector.ts` lines 379, 413) | the runner it is installed in | Runs inside CI, with `github.token` |
| Kesin11/actions-timeline | MIT | v3.2.0 (2026-08-01) | an action added to the workflow; `node24` | GitHub API only | the run it is installed in | Runs inside CI, with `github.token` |

## 2. Findings

### Tools

**F1. actionlint finds no speed problems and no posture problems in the user's workflows; its value to factory-ci is validating an edited workflow.**
Command (per repository, from the scratch copy, explicit file arguments because a copy is not a git repository):
`actionlint -no-color -oneline .github/workflows/*.yml`

| Repo | Exit | Output lines | Seconds | What |
|---|---|---|---|---|
| edgeflow | 1 | 1 | 0.30 | `ci.yml:51:9` shellcheck SC2034 (unused variable) |
| moneylust-app | 1 | 5 | 0.48 | `api-tests.yml:629` SC2010 x2, SC2086; `backend-coverage.yml:557` SC2086, SC2129 |
| pond | 1 | 1 | 0.24 | `ci.yml:562:14` `label "pond-ci" is unknown` [runner-label] |
| glarity | 0 | 0 | 0.25 | none |

Without arguments it fails on a copy: `no project was found in any parent directories`. It reads
`.github/actionlint.yaml` from the project, so a repository can silence it; `-config-file <empty file>` works
(tested on pond: same single finding, JSON via `-format '{{json .}}'` gives `kind=runner-label line=562`).
Use: after an accepted proposal edits a workflow, run actionlint on the edited file as the cheap syntax and
expression check before the change is offered. Not a detector.

**F2. Step-level timing needs nothing beyond `gh api`.** On public `tenequm/pond`, 1 list call plus 1 jobs call per
run gave job and step `started_at` / `completed_at` for 8 successful CI runs (9 calls, core limit 5000/hour):
- `build-and-test-linux` median 2.7 min, max 44.8 min; `build-and-test-windows` median 10.0 min (step `Test` 8.6 min);
  `dist-build-unix` 50.7 min (`Build + package binaries` 50.4 min), `dist-build-windows` 35.1 min.
- One run's `sudo rm -rf /usr/local/lib/android ...` disk-cleanup step took 4 min 49 s (12:13:10 to 12:17:59).
- Data quirks factory-ci must handle: 28 skipped jobs had `completed_at` earlier than `started_at`; a run created
  10:47:52 started 12:13:01 (fork-approval wait, `action_required`), so `created_at` to `run_started_at` is not
  queue time. Queue time per job is `started_at - created_at` on the job object.
A gh extension (gh-workflow-stats) adds an unverified binary holding the user's token for what ~30 lines over
`gh api` do. Not needed.

**F3. GitHub's own metrics have no API, and the old timing endpoint is closing down.**
- Actions Performance Metrics (GA 2025-03-14): repository members see job run time, queue time and failure rate,
  up to one year, all GitHub Cloud plans; org and enterprise views exist. UI only; no REST or GraphQL endpoint is
  documented (https://github.blog/changelog/2025-03-14-actions-performance-metrics-are-generally-available-and-enterprise-level-metrics-are-in-public-preview , https://docs.github.com/en/actions/concepts/metrics , https://github.com/orgs/community/discussions/188189).
  factory-ci can point the user to Insights > Actions as a cross-check for queue time; it cannot read it.
- `GET /repos/{o}/{r}/actions/runs/{id}/timing` is "in the process of closing down"
  (https://github.blog/changelog/2025-02-02-actions-get-workflow-usage-and-get-workflow-run-usage-endpoints-closing-down).
  It still answered for pond: `run_duration_ms: 2698000`, every `billable` entry 0 (public repository).
- The billing usage API needs the `user` scope: `gh api users/<me>/settings/billing/usage` returned
  `This API operation needs the "user" scope`. factory-ci should not ask for it. Runner minutes = sum of job
  durations, labelled with runner OS and size; the per-OS multiplier and the free tier are stated, not fetched.

**F4. The active gh account cannot see three of the four repositories.** `gh api repos/dogebonker/edgeflow`,
`LeaveMyYard/moneylust-app` and `dogebonker/glarity` return 404 for the user's work account; `tenequm/pond` is public.
`gh auth status` shows a second account (`skylightxo`). The settings endpoints
(`actions/permissions`, `actions/permissions/workflow`) return 403 even for `dogebonker/software-factory`.
factory-ci must check access from the remote URL first, say which account it used and which data is missing, and
never run `gh auth switch` itself (it changes the user's global state).

**F5. Pinning tools: pinact for the fix, nothing for detection.** zizmor `unpinned-uses` already detects (F10).
When the user accepts "pin these actions", pinact v5 is the strongest choice: immutable release with attestations,
`--check` and `--no-api` modes, version comments, and a minimum-release-age (cooldown) option that matches the
factory's two-week pin rule (https://github.com/suzuki-shunsuke/pinact docs/check.md, docs/update.md). v5.0.0 is
28 days old at the research date; v4.1.1 is the fallback. ratchet works but its releases are mutable and its
comment format (`# ratchet:`) is its own; frizbee is pre-1.0 with no GitHub attestation. Pinning resolves tags
through the GitHub API, so it is a write step with network, done only as an accepted change.

**F6. act cannot answer "why is CI slow" and runs untrusted code: exclude.**
Its own list of unsupported features includes `concurrency`, `job.timeout-minutes`, `job.permissions`,
`job.environment`, step summaries, and OIDC (https://nektosact.com/not_supported.html). Its images are not GitHub's
runner images, there is no macOS or Windows, the cache server is local, so timings do not transfer. It executes
every step and action of the repository in Docker with the Docker socket mounted, and calls
`api.nektosact.com/notices` on every run unless `ACT_DISABLE_VERSION_CHECK=1`.

**F7. gh itself sends telemetry.** `gh help environment` (2.92.0): "`GH_TELEMETRY`: set to `log` to print telemetry
data to standard error instead of sending it. Set to `false` or `0` to disable telemetry." Telemetry entries appear
in release notes from v2.91.0 (2026-04-22) through v2.100.0. gh also checks for updates daily
(`GH_NO_UPDATE_NOTIFIER`). Every factory-ci gh call should run with `GH_TELEMETRY=false GH_NO_UPDATE_NOTIFIER=1`.
This also means starslingdev's "There is no telemetry" claim (F9) holds only for its own code.

**F8. Step-telemetry actions are changes to CI, not diagnosis.** catchpoint/workflow-telemetry-action (formerly
runforesight) is unmaintained since 2024, runs on node20, and sends resource metrics to a third party
(api.globadge.com) to draw charts. actions-timeline is maintained and GitHub-only, but its timeline is what
factory-ci already computes from the jobs API (F2). Neither belongs in the default path. Resource metrics (CPU,
memory, disk) are the one thing the API cannot give; if a finding needs them ("is this job CPU-bound, would a
larger runner help"), the proposal is a temporary step running `vmstat`/`df` in that job, not a third-party action.

**F9. Prior art: one serious skill, the rest are checklists.**
- starslingdev/skills (MIT, created 2026-07-22, 29 stars, commits daily; installed locally): `ci-speedup`
  (78 `OPT` patterns in `references/optimization-patterns.md`, ~38,000 lines of Python, deterministic detection,
  critical path scoped to required checks, measured wall-clock and runner-minute sizing, needs `gh` and PyYAML),
  `ci-secure` (ten attack vectors, cites zizmor), `ci-score` (eleven config checks), `sling` (the vendor's CLI).
  The vendor sells GitHub Actions runners (https://www.ycombinator.com/launches/R7B-starsling-runners-self-driving-ci).
  Listed on skills.sh (https://www.skills.sh/starslingdev/skills/ci-speedup). The README's S10 list ("missing
  caches, redundant setup, ... sleep-based readiness") mirrors ci-speedup's own description almost word for word.
- Others found by `gh search code --filename SKILL.md` ("slow CI", "ci optimization", "github actions"):
  `Wellux/claude-code-deprecated` pipeline-opt (42 lines, no license), `curiositech/windags-skills`
  ci-cache-optimizer (141 lines, grants itself `docker`, `kubectl`, `terraform`, `npx`), `retlehs/gh-actions` (130 lines,
  authoring guide, no license), `greedychipmunk/agent-skills` github-ci (85 lines, authoring guide). None measures runs.
- The skills.sh search page returned an empty table to a fetch; its catalog was not enumerated further.
Whether factory-ci wraps, vendors or ignores ci-speedup is a decision for the selection record, not this lane.

### Posture

**F10. zizmor already covers the three roadmap items, offline, at the `regular` persona** (v1.30.1 docs/audits.md):

| Roadmap item | zizmor audits | Notes |
|---|---|---|
| Unpinned actions | `unpinned-uses`, `unpinned-images`, `unpinned-tools`, `ref-version-mismatch`; online: `impostor-commit`, `ref-confusion`, `stale-action-refs`, `known-vulnerable-actions` | Default policy since v1.20.0: every action, `actions/*` included, must be hash-pinned |
| Broad token permissions | `excessive-permissions`, `artipacked`, `github-app` | Also flags workflows with no `permissions:` at all |
| Secrets reachable from forks | `dangerous-triggers` (`pull_request_target`, `workflow_run`), `template-injection`, `cache-poisoning`, `secrets-inherit`, `overprovisioned-secrets`, `bot-conditions`; `secrets-outside-env` (auditor) | |
| Self-hosted runners | `self-hosted-runner` | **pedantic only**, and offline it cannot know whether the repository is public |
| OIDC instead of long-lived secrets | `use-trusted-publishing` (PyPI, RubyGems, crates.io, npm, pub.dev, nuget.org) | No audit for cloud credentials (AWS, GCP, Azure keys versus OIDC) |

Two zizmor audits are speed findings, not security: `concurrency-limits` (pedantic) and `superfluous-actions`
(actions that duplicate preinstalled runner tools).

**F11. Pinning by tag versus SHA, with the two incidents.**
- tj-actions/changed-files, CVE-2025-30066 / GHSA-mrrh-fwg8-r2c3 (published 2025-03-15): versions through 45.0.7
  let attackers read secrets from Actions logs; tags were repointed to a malicious commit. Related:
  reviewdog, CVE-2025-30154 / GHSA-qmg3-hpqr-gqvc.
- Trivy, GHSA-69fq-xp46-6x23 / CVE-2026-33634 (critical, published 2026-03-24): on 2026-03-19, 76 of 77
  `aquasecurity/trivy-action` tags and all 7 `setup-trivy` tags were force-pushed to credential stealers for
  about 12 and 4 hours; malicious Trivy v0.69.4 binaries and v0.69.5/0.69.6 Docker Hub images were published.
  The advisory lists as safe: images referenced by digest, and v0.69.3, protected by GitHub immutable releases.
- What SHA pinning does not fix: a SHA-pinned action that downloads "latest" of a tool fetched the malicious binary
  during the window. That is zizmor `unpinned-tools`, not `unpinned-uses`.
- GitHub now offers an allowed-actions policy that fails any workflow using an action not pinned to a full SHA
  (https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions).
  It is an account setting; factory-ci can recommend it, never change it.
- In the user's repositories (parsed with PyYAML from the scratch copies): `pond` 24 of 24 remote `uses:` SHA-pinned,
  `glarity` 41 of 41, `edgeflow` 0 of 4, `moneylust-app` 0 of 84 (most frequent: `actions/checkout@v7` x33,
  `actions/setup-node@v7` x8, `actions/upload-artifact@v7` x7, `docker/login-action@v4.6.0` x6).

**F12. Token permissions and fork reachability need repository context zizmor does not have.**
- Default `GITHUB_TOKEN`: read-only for repositories created under personal accounts and for new orgs since
  2023-02-02; existing ones keep their old setting
  (https://github.blog/changelog/2023-02-02-github-actions-updating-the-default-github_token-permissions-to-read-only/).
  When `permissions:` is set, unlisted scopes become none (metadata stays read). Reading the actual repository
  default (`GET .../actions/permissions/workflow`) needed more access than the user's token had (F4), so factory-ci
  reports "workflow sets no `permissions:`, effective scope depends on a setting I cannot read".
- `pull_request_target` now always takes the workflow and `GITHUB_REF` from the default branch (effective 2025-12-08,
  https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/).
  GitHub's guidance: `pull_request_target` and `workflow_run` "share the same cache of the main branch" with other
  privileged triggers; self-hosted runners "should almost never be used for public repositories"; OIDC lets you
  "stop storing these credentials as long-lived secrets" (https://docs.github.com/en/actions/reference/security/secure-use).
- Examples from the user's repositories:
  - `moneylust-app/.github/workflows/pr-meta.yml`: `pull_request_target`, `pull-requests: write`, on
    `[self-hosted, linux]`, using `actions/labeler@v7` and `amannn/action-semantic-pull-request@v6` by tag. Its comment
    says the PR's code is never checked out, which is true of the file, but a repointed tag would run attacker code
    on a self-hosted machine with a write token. Visibility unknown (404, F4); on a private repository the fork path
    is narrower.
  - `moneylust-app/.github/workflows/main-red.yml`: `workflow_run` on failures of main, passes
    `TELEGRAM_BOT_TOKEN`; filtered on `head_branch == 'main'`.
  - `pond/.github/workflows/ci.yml:562`: `runs-on: pond-ci`, an ARC self-hosted runner (comment at line 559), on a
    public repository; the job runs only when `release-prep` says a release is due, and fork PRs already wait for
    approval (`action_required` runs). zizmor `regular` would not report it; `pedantic` would, without that context.
  These are judgments about trigger, condition, visibility and runner together. They belong to factory-security's
  method (candidate, trace, verdict), not to a speed report.

**F13. The zizmor install line in `kit/security/tools.yaml` uses the weaker channel.** `uv tool install zizmor==1.30.1`
pulls a PyPI wheel without provenance (`https://pypi.org/integrity/zizmor/1.30.1/zizmor-1.30.1-py3-none-macosx_11_0_arm64.whl/provenance`
returns 404). The GitHub release for the same version is immutable and has 2 attestations
(`gh attestation verify <tarball> -R zizmorcore/zizmor`). Noted for factory-security; this lane edits no other file.

**F14. ci-speedup's posture overlap.** ci-speedup declines security work and routes it to `ci-secure`; `ci-secure`
re-implements ten vectors in its own scanner and points to zizmor for template injection
(`references/security-patterns.md` line 156). Two security engines with different rules for the same workflows
is what the factory already avoided by picking zizmor in SEC-2.

### Non-GitHub CI

**F15. A first version should detect other CI, say so, and stop.**
- None of the user's 31 working directories has non-GitHub CI config (section 0).
- zizmor and actionlint are GitHub Actions only (D-scanners section 7: "Misses: non-GitHub CI").
- Each system needs its own config model and API: GitLab has `include:`, `extends:`, anchors and child pipelines, and
  its jobs API does give `duration` and `queued_duration` (https://docs.gitlab.com/api/jobs/); CircleCI has orbs and an
  Insights API behind a personal token; Buildkite pipelines are often uploaded at run time
  (`buildkite-agent pipeline upload`), so the repository file is not the pipeline. Each would be a second
  implementation of parsing, critical path and posture, with its own CLI and credentials.
- Behavior: list the files found (`.gitlab-ci.yml`, `.circleci/config.yml`, `.buildkite/`, `Jenkinsfile`,
  `azure-pipelines.yml`, `bitbucket-pipelines.yml`, `.drone.yml`, `.woodpecker*`), state "factory-ci covers
  GitHub Actions only", and stop. A repository with both analyzes the GitHub part and names what it did not read.

## 3. Recommendation

- **A1. Measurement uses `gh api` only**, with `GH_TELEMETRY=false GH_NO_UPDATE_NOTIFIER=1`: runs list, jobs per run
  (steps included), required checks from branch protection or rulesets where the token can read them. No gh
  extension, no `/timing`, no billing scope, no act, no telemetry action.
- **A2. actionlint v1.7.12** (already installed) validates every workflow an accepted proposal edits, run with
  `-config-file` pointing at an empty file. Optional; skipped with its install line when missing.
- **A3. pinact** (v5.0.0, or v4.1.1) is the tool for an accepted "pin actions" proposal, never run unasked.
- **A4. Posture: factory-ci runs zizmor itself, through factory-security's `zizmor` line in `kit/security/tools.yaml`**
  (same pin, `--offline --no-config --persona regular --format json --no-exit-codes`, from an empty directory), and
  reports only the audits in F10's first three rows, grouped under the roadmap's three headings, beside the speed
  findings. Reason: the roadmap promises posture "on the way", which a pointer to another skill does not deliver,
  and reading the existing line keeps one pin and one flag set for both skills. Everything else zizmor reports is
  counted, not shown, with "run `/factory-security` for the rest". If zizmor is missing, the posture section says
  skipped, with the install line; factory-ci does not fall back to its own checks.
- **A5. Hand to `/factory-security`:** anything that needs a verdict (F12): privileged triggers, self-hosted runners
  on public repositories, cache poisoning, OIDC versus cloud keys, online audits that need a token. factory-ci
  never marks a posture item confirmed.
- **A6. Non-GitHub CI:** detect, say so, stop (F15).

Skipped: a factory-ci posture engine of its own, and support for other CI systems. Add the latter when a user
repository actually uses one.
