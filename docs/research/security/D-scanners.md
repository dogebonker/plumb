# D: Scanner toolchain for `factory-security` (S11)

Research date: 2026-10-10. Pin rule: a release published on or before 2026-09-26 (at least two weeks old).
Release dates come from the GitHub releases API (`gh api repos/<owner>/<repo>/releases`). Homebrew data from `brew info --json=v2`. Nothing was installed.

## 0. Local machine state (checked, not assumed)

| Tool | Installed | Notes |
|---|---|---|
| semgrep | 1.173.0 via pip in pyenv 3.10 | **Broken.** `semgrep --version` crashes: `pysemgrep` imports `mcp`, which raises `TypeError: Too few parameters for RequestContext` on Python 3.10. Homebrew stable is 1.180.0. |
| gitleaks | 8.18.1 (Homebrew) | **Old.** Has only `detect`/`protect`; the `git`/`dir` subcommands came later. Homebrew stable is 8.30.1. Measured: `gitleaks detect` over this repo (48 commits) took 0.13 s, 0 findings. |
| govulncheck | v1.8.0 (`~/go/bin`), Go 1.27.1 | Works. DB vuln.go.dev, updated 2026-10-08. |
| pip-audit | 2.10.1 (pyenv shim) | Works. |
| actionlint | 1.7.12 (Homebrew) | Works. |
| trivy, osv-scanner, opengrep, zizmor, hadolint, checkov, syft, grype, trufflehog, cargo-audit, cargo-deny, codeql | not installed | |

## 1. Trivy

Sources: https://trivy.dev/docs/latest/references/configuration/cli/trivy_filesystem/ , https://trivy.dev/docs/latest/guide/advanced/air-gap/ , https://trivy.dev/docs/latest/guide/advanced/telemetry/ , https://trivy.dev/docs/latest/guide/coverage/language/ , https://trivy.dev/docs/latest/guide/scanner/misconfiguration/ , https://trivy.dev/docs/latest/guide/scanner/license/ , https://trivy.dev/docs/latest/guide/scanner/vulnerability/

- **Subcommands:** `fs`, `repo`, `image`, `config`, `rootfs`, `sbom`. `--scanners` takes `vuln,misconfig,secret,license`. The default for `fs` is `vuln,secret`. Misconfig is off by default for `fs`, `repo` and `image`.
- **Output:** `--format json|sarif|cyclonedx|spdx-json|table|template|github|cosign-vuln`, plus `--output FILE`. `--exit-code N` sets the code returned on findings. `--list-all-pkgs` defaults to `true`, which puts every package in the JSON, so set it to `false` unless you want an inventory. JSON shape: `.Results[].{Vulnerabilities,Misconfigurations,Secrets,Licenses}`.
- **Lockfiles, fs/repo mode:** npm `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`; `Cargo.lock`; `go.mod`; `poetry.lock`, `uv.lock` (workspaces from v0.75), `Pipfile.lock`, `requirements.txt`. Not in fs mode: bare `package.json`, Go binaries, cargo-auditable binaries, wheels. These are image/rootfs only. Dev dependencies are excluded unless `--include-dev-deps` (npm, yarn, gradle).
- **Vulnerability data:** npm comes from GHSA and nodejs/security-wg. PyPI comes from GHSA only (PyPA advisory-db is not listed). crates.io comes from OSV (RustSec). Go comes from GHSA and the Go vulndb. There is **no reachability**.
- **Misconfig:** Terraform, CloudFormation, ARM, Helm charts, Dockerfile, Kubernetes manifests. **GitHub Actions is not covered.** The checks bundle is fetched from an OCI registry. A copy is embedded in the binary and is used when the fetch fails.
- **Secrets:** regex rules on the working tree only. It does not scan git history and does not verify secrets.
- **License:** `--scanners license` classifies findings as forbidden (CRITICAL), restricted (HIGH), reciprocal (MEDIUM), and notice, permissive and unencumbered (LOW). `--license-full` also scans file headers and LICENSE files, and the docs call it "expensive". Some lockfiles need extra files on disk before a license can be detected (for example `node_modules` or the module cache). In practice, `Cargo.lock`, `go.mod` and Python lockfiles alone carry no license data.
- **SBOM:** `--format cyclonedx` or `spdx-json`. v0.75 adds a CBOM (`crypto` scanner, images only, experimental).
- **Network and phoning home:**
  - DB downloads from `mirror.gcr.io` and `ghcr.io` (trivy-db, java-db, checks bundle).
  - VEX hub from `api.github.com`.
  - Maven Central for Java, unless `--offline-scan`.
  - **Anonymous usage telemetry is on by default.** It sends a hashed machine ID, version, OS and some flag values. Disable with `--disable-telemetry`.
  - A **separate version check** goes to `check.trivy.dev`. Disable with `--skip-version-check`. The docs state the two are independent, so both flags are needed.
  - Offline re-runs: `--skip-db-update --skip-java-db-update --skip-check-update --offline-scan`.
- **Repo-controlled config:** `trivy.yaml`, `.trivyignore` and `trivy-secret.yaml` are read from the **current working directory** (defaults of `--config`, `--ignorefile`, `--secret-config`). v0.75.0 adds explicit empty values that disable loading them. On v0.74, run Trivy with cwd set to an empty directory so a scanned repo cannot suppress its own findings. Inline `trivy:ignore` comments in IaC are still honored, so report them.
- **Supply-chain incident (GHSA-69fq-xp46-6x23, https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23):**
  - On 2026-03-19, stolen credentials were used to publish a malicious **v0.69.4** (binaries, deb/rpm, GHCR/ECR/Docker Hub images, `get.trivy.dev`).
  - The attackers force-pushed **76 of 77 `trivy-action` tags** and **all 7 `setup-trivy` tags** to an infostealer. It dumped runner memory and exfiltrated credentials, or created a public `tpcp-docs` repo as a fallback.
  - On 2026-03-22, malicious Docker Hub images **0.69.5 and 0.69.6** were published.
  - Root cause: a non-atomic credential rotation after a February compromise.
  - Not affected: the Homebrew core formula (it builds from source), images referenced by digest, and releases protected by GitHub immutable releases (enabled 2026-03-03).
  - The old trivy-action tags were deleted. They were re-published with a `v` prefix.
  - **What this means for pinning:**
    - (a) Never reference `trivy-action` or `setup-trivy` by tag. Use a full commit SHA, or skip the action and run the binary.
    - (b) Pin the binary by version **and** sha256. Verify the sigstore bundle with `cosign verify-blob --certificate-identity-regexp 'https://github\.com/aquasecurity/' --certificate-oidc-issuer https://token.actions.githubusercontent.com`.
    - (c) Pin container images by digest, never `latest`.
    - (d) The min-age rule would not have blocked a 3-hour malicious release on its own, but combined with a hash pin it would have.
- **Later Trivy advisories:**
  - GHSA-q3fv-x8vg-qqm4: Helm tar-bomb OOM, fixed in 0.71.0.
  - GHSA-mcj4-mphf-j9ff: path traversal from a crafted DB or OCI artifact via a custom `--db-repository`, fixed in 0.71.1.
  - GHSA-8rc5-4fr6-64pw: plugin manager path traversal, fixed in 0.72.0.
  - **Minimum acceptable version: 0.72.0.** Never point `--db-repository` or `--checks-bundle-repository` at a mirror you do not control.
- **Releases:** v0.75.0 (2026-10-01, too new), **v0.74.0 (2026-08-14) is the pin**, v0.73.0 (2026-08-03).
- **Install:** the Homebrew formula is 0.75.0. Homebrew cannot hold 0.74.0 without a custom tap, so use the GitHub release tarball `trivy_0.74.0_macOS-ARM64.tar.gz` and verify its checksum and sigstore bundle. Releases are immutable since March 2026. Alternatively, accept Homebrew stable and enforce the min-age rule at run time by checking `trivy --version` against the lock.

## 2. Semgrep CE vs Opengrep

Sources: https://semgrep.dev/blog/2024/important-updates-to-semgrep-oss/ , https://semgrep.dev/legal/rules-license , https://github.com/semgrep/semgrep-rules (LICENSE) , https://docs.semgrep.dev/semgrep-ce-languages , https://docs.semgrep.dev/metrics , https://github.com/opengrep/opengrep , https://github.com/opengrep/opengrep/pull/789 , https://github.com/opengrep/opengrep/issues/763 , https://github.com/opengrep/opengrep-rules

- **2024-12-13 change:**
  - Semgrep OSS was renamed Community Edition. The engine stays LGPL-2.1.
  - Semgrep-maintained rules moved to **Semgrep Rules License v1.0**: use "only for your own internal business purposes". The license "does not allow you to distribute the rules, or to make them available to others as a service".
  - Some JSON/SARIF fields and the remaining experimental features moved to the logged-in commercial engine. The current docs list `fingerprint` and `lines` (the matched text) as unavailable in CE. Line numbers stay in `start`/`end`.
- **Who can use the registry:** anyone may scan their own code with registry rules. No login is needed for public `p/` packs. The factory must **not** vendor or redistribute the rule YAML in its public repo, because that is distribution. A user may cache a copy locally for internal use.
- **Opengrep:**
  - An LGPL-2.1 fork of Semgrep CE v1.100.0, backed by Aikido, Endor Labs, Orca, Amplify, Kodem and others.
  - It restores or adds **`--taint-intrafile`** (cross-function taint inside one file, 12 languages), a SARIF fingerprint (`matchBasedId/v1`), Windows support, and Apex, Elixir and VB.
  - **PR #789 (merged 2026-08-14) removed all metrics, telemetry, login, version check and Semgrep-backend calls.**
  - `--config auto` and `p/<pack>` still pull rules from **semgrep.dev**, as a maintainer stated in issue #763. The rule license is therefore the same whichever engine you use.
  - `opengrep/opengrep-rules` is a snapshot of semgrep-rules from 2024-12-13 under LGPL-2.1 plus Commons Clause. It was last pushed 2025-11-28, so it is stale.
  - There is no Homebrew formula. Binaries are signed (`.cert`/`.sig`, cosign).
  - Releases: v1.30.2 (2026-10-07), **v1.30.1 (2026-09-21) is the pin**. v2.0.0 alphas (no-Python, interfile) are pre-release.
- **Semgrep CE:**
  - All languages are "community supported" in CE and analysis is **single-function only**. Cross-file and cross-function dataflow is Pro (login).
  - Metrics: the default `--metrics auto` **sends metrics whenever rules come from the Registry**. Disable with `--metrics off` or `SEMGREP_SEND_METRICS=off`.
  - Releases: 1.180.0 (2026-10-07), 1.179.0 (2026-10-02), **1.178.0 (2026-09-23) is the pin**.
- **Output (identical in both engines):** `--json` / `--json-output FILE`, `--sarif` / `--sarif-output FILE`. Exit code is 0 with findings unless `--error` is passed. `--disable-nosem` ignores `nosemgrep` comments, which are repo-controlled suppressions.
- **Offline rules:** `https://semgrep.dev/c/p/<pack>` returns the pack as YAML or JSON. Fetch it once into the user cache, record its sha256, and pass the file with `--config FILE`. This gives reproducible, offline, metrics-free runs with either engine.
- **Measured registry pack sizes (2026-10-10):**

| Pack | Rules | Rules not in p/default |
|---|---|---|
| p/default | 1074 (python 243, js 152, ts 150, java 118, hcl 99, go 84) | n/a |
| p/javascript, p/typescript | 74 | 1 |
| p/react | 4 | 1 |
| p/nextjs | empty | n/a |
| p/golang | 42 | 3 |
| **p/rust** | **11** | 7 |
| p/python | 151 | 30 |
| p/terraform | 63 | 13 |
| p/dockerfile | 7 | n/a |
| p/kubernetes | 11 | n/a |
| p/github-actions | 12 | n/a |
| p/secrets | 52 | 3 |
| p/security-audit | 225 | 13 |
| p/owasp-top-ten | 560 | 70 |

  Quality by stack:
  - JS/TS and Python: reasonable.
  - Go: moderate.
  - **Rust: thin** (5 rules in default).
  - **Next.js and React: almost nothing.**
  - IaC and GHA rules: duplicate what Trivy and zizmor already cover.

## 3. Gitleaks vs TruffleHog (and Betterleaks)

Sources: https://github.com/gitleaks/gitleaks (README v8.30.1) , https://github.com/betterleaks/betterleaks , https://github.com/trufflesecurity/trufflehog (README)

- **Gitleaks:**
  - MIT. Regex plus entropy. No verification and no network.
  - `gitleaks git` scans history via `git log -p`. Use `--log-opts` to choose refs or ranges. `gitleaks dir` scans files and `stdin` reads piped input.
  - JSON output: `--report-format json --report-path FILE`. `--redact` masks secrets. `--exit-code`.
  - **README v8.30.1: "Gitleaks is feature complete... Future releases will be security patches only."** The maintainer moved to Betterleaks. The last release is v8.30.1 (2026-03-21), and that is the pin.
  - Config precedence: `--config`, then `GITLEAKS_CONFIG`, then `GITLEAKS_CONFIG_TOML`, then `<target>/.gitleaks.toml`, then the embedded default. `.gitleaksignore` is read from `-i` (default "."). `gitleaks:allow` comments are honored unless `--ignore-gitleaks-allow`. A scanned repo can therefore suppress its own findings unless you pass an explicit config and ignore path.
- **Betterleaks:**
  - MIT. Built by the Gitleaks authors with Aikido backing, created 2026-02.
  - Adds optional **validation** (`-v`, HTTP calls defined in the rule), Expr filters, BPE "rarity" filtering for generic secrets, and container-image scanning.
  - Validation is off by default.
  - Releases: v1.9.0 (2026-09-29, too new), **v1.8.1 (2026-08-18) is eligible**. v2.0.0-rc.2 is in progress and breaks CLI, config and report formats.
  - Homebrew core has 1.9.0.
  - Re-evaluate when v2 is stable.
- **TruffleHog:**
  - **AGPL-3.0.** More than 700 detectors with **live verification**: it calls each provider's API (for example AWS `GetCallerIdentity`).
  - Result classes are `verified`, `unverified` and `unknown`. Use `--results=verified,unknown` to filter.
  - Flags: `--json`, `--sarif`, `--no-verification`, `--fail` (exit 183), and `--no-update`. It self-checks for updates by default.
  - History: `trufflehog git file://.`. Also scans filesystem, docker, S3 and GCS.
  - Releases: 3.97.9 (2026-09-24) is the newest eligible.
- **Verdict:** use Gitleaks v8.30.1 (or Betterleaks 1.8.1) without validation.
  - Verification sends the found secret to a third party and leaves an access log at the provider. That is a side effect an audit should not take on its own. Offer it only as an explicit, per-finding user action.
  - AGPL is a hurdle if the kit ever wraps the tool.
  - TruffleHog's detection breadth is better on vendor-specific tokens. Gitleaks' default rules are good, and the generic-api-key rule is its main false-positive source.

## 4. OSV-Scanner vs per-ecosystem audit tools

Sources: https://google.github.io/osv-scanner/supported-languages-and-lockfiles/ , https://github.com/google/osv-scanner/blob/v2.6.0/docs/scan-source.md , .../docs/output.md , .../docs/offline-mode.md , .../docs/license-scanning.md , .../docs/configuration.md

- **OSV-Scanner v2.6.0 (2026-09-14) is the pin.** Apache-2.0, available in Homebrew.
  - Lockfiles: `bun.lock`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`, `requirements.txt`, `pdm.lock`, `pylock.toml`, `uv.lock`, `Cargo.lock`, `go.mod`. It also reads SBOMs and container images.
  - **Call analysis:** Go is on by default through the govulncheck library and needs `go` on PATH. Rust is experimental (`--call-analysis=rust`). **It compiles the crate and runs dependency `build.rs`, which is arbitrary code.** Never enable it on untrusted repos.
  - Output: `--format json|sarif|table|markdown|html|vertical`.
  - Offline: `--offline-vulnerabilities --download-offline-databases`, then `--offline`. The DB lives in `OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY`.
  - **By default it queries api.osv.dev with package names and versions.** Maven transitive resolution and `--licenses` call **deps.dev**.
  - A per-directory `osv-scanner.toml` can ignore vulns unless `--config` is passed.
- **npm audit / pnpm audit:**
  - Both POST every package name and version to the registry's `/-/npm/v1/security/advisories/bulk`. npm falls back to Quick Audit, which sends the whole tree plus node, OS and arch.
  - The data is GHSA, the same data as Trivy and OSV.
  - JSON with `--json`. pnpm v11+ filters by GHSA only.
  - They add nothing beyond Trivy and OSV except npm's `audit signatures` (registry signature and provenance check), which is a different question.
- **cargo-audit 0.22.2 (2026-06-05):**
  - Uses RustSec, which is the same as Trivy's crates data via OSV. Clones advisory-db from GitHub. Output with `--json`.
  - Can audit `cargo auditable` binaries.
- **cargo-deny 0.20.2 (2026-07-09):** adds what the others lack: **license policy, banned crates, and allowed `sources`** (git and unknown registries). It needs `deny.toml` and `cargo metadata`. Useful only when the repo already has a `deny.toml`.
- **govulncheck v1.8.0 (2026-09-08):**
  - **Symbol-level reachability for Go**, with low false positives.
  - Output: `-format json|sarif|openvex`. With these formats it **always exits 0**.
  - Sends "only module paths with vulnerabilities already known to the database" to vuln.go.dev.
  - Misses calls via reflect and unsafe. Interface and function-pointer calls are treated conservatively.
- **pip-audit 2.10.1 (2026-06-10):**
  - Sources are the PyPI JSON API (default) or OSV.
  - `--locked` supports only `pyproject.toml` and `pylock.*.toml`, **not** `uv.lock` or `poetry.lock`.
  - On `-r requirements.txt` without `--no-deps`, it **resolves through pip in a venv, which can execute `setup.py` of sdists**. That is unsafe on untrusted repos.
- **Verdict:** one SCA database tool plus govulncheck. Trivy already covers every lockfile here, and it is needed anyway for images, IaC and license. The per-ecosystem tools add duplicate data and, for pip-audit, a code-execution risk. govulncheck stays for reachability triage of Go findings.

## 5. GitHub Actions, IaC, Dockerfile, SBOM

Sources: https://docs.zizmor.sh/usage/ , https://github.com/zizmorcore/zizmor/blob/v1.30.1/docs/audits.md , https://github.com/rhysd/actionlint/blob/v1.7.12/docs/{usage,checks}.md , https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html , https://github.com/hadolint/hadolint

- **zizmor v1.30.1 (2026-09-09).** MIT, Rust, available in Homebrew and PyPI.
  - 41 audits, including template-injection, dangerous-triggers (`pull_request_target`, `workflow_run`), excessive-permissions, artipacked, cache-poisoning, unpinned-uses, unpinned-images, impostor-commit, ref-confusion, known-vulnerable-actions, secrets-inherit, overprovisioned-secrets, bot-conditions, typosquat-uses, dependabot-cooldown and use-trusted-publishing.
  - It covers workflows, composite and Docker `action.yml`, `dependabot.yml` and pre-commit config.
  - Output: `--format json` (json-v1, 0-based rows), `sarif` or `github`.
  - Exit codes are 11 to 14 by severity. `--no-exit-codes` disables them.
  - Personas: `regular` (low noise), `pedantic`, `auditor`.
  - `--offline` or no token means offline. **Online-only audits are `impostor-commit`, `known-vulnerable-actions`, `ref-confusion` and `stale-action-refs`.** These are the ones that would have flagged the compromised trivy-action tags. They need `GH_TOKEN` and call the GitHub API with action refs. `--no-config` ignores the repo's `zizmor.yml`. Inline `# zizmor: ignore[...]` comments still apply.
- **actionlint v1.7.12 (2026-03-30, installed).** MIT.
  - Correctness checks: syntax, expression types, runner labels, cron, and shellcheck/pyflakes on `run:`.
  - Security checks: untrusted-input script injection and hardcoded container credentials.
  - JSON with `-format '{{json .}}'`.
  - Overlaps zizmor on injection. It is a lint, not an audit, so it is optional.
- **checkov 3.3.19 (2026-09-17).** Apache-2.0, Python.
  - Larger policy set than Trivy for Terraform and K8s, plus graph checks. It also covers GHA, secrets and SCA.
  - **By default it downloads data from Prisma Cloud** (`--skip-download` stops it). An API key unlocks the platform.
  - It is a heavy Python install, and its checks overlap Trivy's.
- **hadolint v2.15.1 (2026-07-31).** GPL-3.0.
  - Dockerfile best-practice lint plus shellcheck of `RUN`. JSON with `-f json`.
  - Its security value overlaps Trivy's Dockerfile checks (root user, `latest` tag, ADD, secrets in ENV). Exclude.
- **Syft 1.52.0 / Grype 0.119.0 (2026-09-17).** Syft has broader catalogers and binary classifiers. Grype duplicates Trivy's vuln matching. Add Syft only if image SBOM fidelity becomes a requirement. Exclude for now.

## 6. CodeQL: exclude

Source: https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md , https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/preparing-your-code-for-codeql-analysis

- The CLI license allows analysis **only of OSI-licensed codebases** (plus academic research and demos). It forbids use "in connection with any codebase that is not an Open Source Codebase (e.g., code in a private repo in GitHub)" and automated or CI database creation, unless the user has a paid GitHub Advanced Security license.
- It forbids redistributing the CLI.
- Go needs a build. Rust supports `--build-mode none`. JS/TS and Python need no build. Each language needs its own database, which is a full source copy.
- CodeQL v2.27.0 (2026-09-09) would be the pin if it were added.
- **Exclude from the default toolchain.** Possible opt-in later when the repo is OSI-licensed or the user states they have a GHAS license. Its interfile taint is the main thing missing from the CE/Opengrep engines.

## 7. Recommended minimal toolchain

Five tools. They do not overlap on primary job:

| Tool | Pin (date) | Covers | Install |
|---|---|---|---|
| Trivy | v0.74.0 (2026-08-14) | Dependency vulns (all lockfiles and images), IaC misconfig (Terraform, K8s, Helm, Dockerfile), license, SBOM, image secrets | GitHub release tarball with sha256 and cosign bundle check. Releases are immutable. Never use trivy-action or setup-trivy by tag. |
| Opengrep (alt: Semgrep CE) | v1.30.1 (2026-09-21) / semgrep 1.178.0 (2026-09-23) | SAST for TS/JS, Python, Go, Rust | Opengrep: release binary `opengrep_osx_arm64` plus `cosign verify-blob` of `.sig`/`.cert`. Semgrep: `uv tool install semgrep==1.178.0`. The local pip install is broken. |
| Gitleaks | v8.30.1 (2026-03-21) | Secrets in working tree and git history | `go install github.com/zricethezav/gitleaks/v8@v8.30.1` or a release binary. Upgrade from the installed 8.18.1. |
| zizmor | v1.30.1 (2026-09-09) | GitHub Actions security | `uv tool install zizmor==1.30.1` or a release binary |
| govulncheck | v1.8.0 (2026-09-08) | Go reachability triage of Trivy's Go findings | `go install golang.org/x/vuln/cmd/govulncheck@v1.8.0` (already installed) |

Shared run conventions:
- `$REPO` is the target. `$OUT` is the run's output directory. `$CACHE` is a user cache outside the repo. `$NEUTRAL` is an empty directory used as cwd, so repo-local tool configs cannot suppress findings.
- After each run, list the repo's own suppression files and inline ignores (`.trivyignore`, `trivy:ignore`, `.gitleaks.toml`, `.gitleaksignore`, `gitleaks:allow`, `nosemgrep`, `.semgrepignore`, `zizmor.yml`, `# zizmor: ignore`, `osv-scanner.toml`) as data for model judgment.

### Trivy (source)
```sh
cd "$NEUTRAL" && trivy fs \
  --scanners vuln,misconfig,license \
  --format json --output "$OUT/trivy-fs.json" \
  --list-all-pkgs=false --exit-code 0 \
  --disable-telemetry --skip-version-check \
  --cache-dir "$CACHE/trivy" \
  "$REPO"
# offline re-run (DB already cached): add
#   --skip-db-update --skip-java-db-update --skip-check-update --offline-scan
# SBOM:
cd "$NEUTRAL" && trivy fs --format cyclonedx --output "$OUT/sbom.cdx.json" \
  --disable-telemetry --skip-version-check --cache-dir "$CACHE/trivy" "$REPO"
# image (OS + language packages, secrets baked into layers, image misconfig):
cd "$NEUTRAL" && trivy image --scanners vuln,secret,misconfig \
  --format json --output "$OUT/trivy-image.json" --exit-code 0 \
  --disable-telemetry --skip-version-check --cache-dir "$CACHE/trivy" "$IMAGE@sha256:..."
```
- **Runtime (estimate, not measured here):** the first run downloads trivy-db and the checks bundle. java-db downloads only if Java artifacts are present. Later scans take seconds to about a minute. `--license-full` is much slower.
- **False positives:** no reachability, so every vulnerable version is reported. Misconfig is noisy at LOW and MEDIUM (K8s resource limits, `readOnlyRootFilesystem`, Terraform logging and CMK encryption). Treat HIGH and CRITICAL as findings and the rest as advisory.
- **Misses:** reachability, git-history secrets, GitHub Actions, bare `package.json` or unpinned `requirements.txt` (no transitive deps), and licenses for Cargo, Go and Python from lockfiles alone.

### Opengrep (or Semgrep CE)
```sh
# once per pin, into the user cache (never the repo): fetch packs and record sha256
curl -fsSL https://semgrep.dev/c/p/default -o "$CACHE/rules/p-default.yml"
curl -fsSL https://semgrep.dev/c/p/rust    -o "$CACHE/rules/p-rust.yml"   # only if Cargo.toml present
shasum -a 256 "$CACHE"/rules/*.yml

opengrep scan --config "$CACHE/rules/p-default.yml" [--config "$CACHE/rules/p-rust.yml"] \
  --taint-intrafile --disable-nosem \
  --json-output "$OUT/sast.json" --sarif-output "$OUT/sast.sarif" "$REPO"

# Semgrep CE equivalent
semgrep scan --metrics off --disable-version-check \
  --config "$CACHE/rules/p-default.yml" --disable-nosem \
  --json-output "$OUT/sast.json" "$REPO"
```
- **Runtime (estimate):** tens of seconds to a few minutes per 100k LOC with about 1,000 rules. Memory can reach 1-4 GB. `--taint-intrafile` adds time.
- **False positives:** moderate. Audit-style pattern rules fire on already-sanitized input.
- **Misses:**
  - Cross-file taint, authn/authz logic, IDOR and business logic.
  - Next.js server actions, middleware and route handlers (no rules).
  - Most Rust issues.
- **Phones home:** Semgrep sends metrics with registry configs unless `--metrics off`. Using local files avoids this. Opengrep has no telemetry from PR #789 onward, but fetching `p/` packs at scan time contacts semgrep.dev.

### Gitleaks
```sh
# kit-owned config forces the embedded default ruleset, ignoring <repo>/.gitleaks.toml:
#   $KIT/gitleaks.toml:  [extend]\nuseDefault = true   (+ optional [allowlist] paths for node_modules, vendor)
cd "$NEUTRAL" && gitleaks git --no-banner --redact \
  --config "$KIT/gitleaks.toml" --gitleaks-ignore-path "$NEUTRAL" --ignore-gitleaks-allow \
  --log-opts="--all --full-history" \
  --report-format json --report-path "$OUT/gitleaks-history.json" --exit-code 0 "$REPO"
cd "$NEUTRAL" && gitleaks dir --no-banner --redact \
  --config "$KIT/gitleaks.toml" --gitleaks-ignore-path "$NEUTRAL" --ignore-gitleaks-allow \
  --report-format json --report-path "$OUT/gitleaks-tree.json" --exit-code 0 "$REPO"
```
- **Runtime:** measured 0.13 s for 48 commits. Expect minutes on histories with tens of thousands of commits.
- **False positives:** the generic-api-key rule, test fixtures, and example keys.
- **Misses:** verification (is it live?), custom internal token formats, encoded secrets (unless `--max-decode-depth`), and objects not reachable from any ref.
- **Phones home:** no.

### zizmor
```sh
cd "$NEUTRAL" && zizmor --offline --no-config --persona regular \
  --format json --no-exit-codes "$REPO" > "$OUT/zizmor.json"
# with a read-only token, drop --offline to add impostor-commit, known-vulnerable-actions, ref-confusion, stale-action-refs:
GH_TOKEN=... zizmor --no-config --persona regular --format json --no-exit-codes "$REPO" > "$OUT/zizmor.json"
```
- **Runtime:** under a second offline. Online, it makes one GitHub API call per action ref.
- **False positives:** low at `regular`.
- **Misses:** non-GitHub CI, and everything outside workflow, action and dependabot files.
- **Phones home:** only online, to the GitHub API.

### govulncheck (per Go module, only when Trivy reports Go vulns or for full audits)
```sh
govulncheck -C "$MODULE_DIR" -format json ./... > "$OUT/govulncheck-<module>.json"   # exit code is 0 in json mode; read .finding entries
```
- **Runtime (estimate):** tens of seconds. The first run is longer because it downloads modules.
- **False positives:** low.
- **Misses:** reflect and unsafe paths. It covers Go only.
- **Phones home:** module paths go to vuln.go.dev, and modules come from the Go proxy.

## 8. Decisions to confirm (codes)

- **D1:** Drop `npm audit`, `pnpm audit`, `cargo audit` and `pip-audit` from S11's "scanners first" list. They duplicate Trivy's GHSA/RustSec data, and pip-audit can execute `setup.py`. The README line 263 currently lists them.
- **D2:** Drop OSV-Scanner from the default set. Trivy plus govulncheck covers the same lockfiles and Go reachability. Keep OSV-Scanner v2.6.0 as an optional second database if Trivy's PyPI coverage (GHSA only) proves thin.
- **D3:** Use Opengrep v1.30.1 instead of Semgrep CE. Reasons: no telemetry, intrafile taint, same rules and same JSON. Semgrep CE 1.178.0 is the fallback. Swapping is one binary name.
- **D4:** Semgrep registry rules are fetched by the user into `$CACHE` and hash-pinned. They are never committed to this repo, because the rules license forbids distribution.
- **D5:** Gitleaks v8.30.1 now. Re-evaluate Betterleaks at v2 stable. TruffleHog-style live verification only as an explicit per-finding user action.
- **D6:** Use zizmor for GitHub Actions. actionlint is optional and already installed.
- **D7:** Exclude CodeQL, checkov, hadolint, Syft/Grype and TruffleHog (reasons in sections 3, 5 and 6).
- **D8:** Every tool runs from an empty cwd with explicit configs. Repo-local suppressions are reported, not obeyed.
- **D9:** Trivy pin is v0.74.0, with a floor of 0.72.0. Pin by sha256 and verify the sigstore bundle. Never use `aquasecurity/trivy-action` or `setup-trivy` by tag.

## 9. Phones home or needs an account

| Tool | Default network | Disable | Account |
|---|---|---|---|
| Trivy | DB pulls (mirror.gcr.io, ghcr.io), **telemetry on**, version check (check.trivy.dev), VEX hub, Maven Central | `--disable-telemetry --skip-version-check`; `--skip-*-update --offline-scan` after first pull | No |
| Semgrep CE | **Metrics with registry configs**, registry fetch, version check | `--metrics off`, `--disable-version-check`, local `--config` files | No (Pro features need login) |
| Opengrep | Registry fetch only when `p/` or `auto` is used | local `--config` files | No |
| Gitleaks | None | n/a | No |
| TruffleHog | **Sends found secrets to provider APIs**, update check | `--no-verification --no-update` | No |
| OSV-Scanner | api.osv.dev (package names and versions), deps.dev | `--offline` with a downloaded DB | No |
| npm/pnpm audit | Full dependency list to the registry | n/a | No |
| pip-audit | PyPI or OSV API, pip resolution | `--no-deps` with fully pinned requirements | No |
| govulncheck | vuln.go.dev (known-vulnerable module paths), Go proxy | `-db file://...` mirror | No |
| cargo-audit | Clones advisory-db from GitHub | `--no-fetch` | No |
| zizmor | GitHub API only when a token is set | `--offline` | Token for online audits |
| checkov | **Downloads from Prisma Cloud** | `--skip-download` | API key optional |
| CodeQL | n/a | n/a | **GHAS license required for private repos** |
