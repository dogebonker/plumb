# factory-security: what it loads, and why

The decision record for S11. Evidence is in [security/](security/): A (the 817-skill mukul975 catalog, all of it classified, 199 read in full), B (the Masriyan catalog), C (methodology cores), D (scanners). Researched 2026-10-10.

## The question

A security audit of a repository needs three things: tools that find candidates mechanically, a method that turns candidates into proven findings, and knowledge of the specific technology in front of it. The available skill catalogs are large: mukul975 ships 817 skills, Masriyan 22. The user's repositories need a small, correct subset, picked per repository, never the whole library.

## Decisions

### SEC-1. Cloudflare `security-audit` is the method, always loaded

- **What:** [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) (MIT, last commit 2026-09-14, installed copy identical to upstream). Its candidate gate, its verifier and its findings schema decide what counts as a finding. Its attack-class files are the first lens of every security agent.
- **Why:** its evidence bar is the factory's: a finding is `confirmed` only with a full file-and-line trace and a bounded, observed result; otherwise it is `needs_validation` with the exact blocker, or `rejected`. It ships zero-dependency validators for the findings file and the coverage ledger (65 of 65 of their own tests pass, C section 1). Its references split cleanly by component (web and auth, client side, supply chain and CI, cloud and IaC, data isolation, AI and LLM, RPC, resource exhaustion, memory safety, desktop and IPC), which is exactly the unit the router needs.
- **Rejected as the method:** Trail of Bits plugins run as Claude-only workflow pipelines and are CC-BY-SA (C section 2); Anthropic's `claude-code-security-review` is diff-only and excludes classes we care about (C section 3); Semgrep's skills carry a restrictive rules license (C section 3).
- **What it costs:** a full audit is heavy. factory-security defaults to scoped runs and to the quick profile, and uses the full workflow only when asked.

### SEC-2. Five pinned scanners run first, from an empty directory

| Tool | Pin | Job |
| --- | --- | --- |
| Trivy | v0.74.0 (floor 0.72.0) | dependency vulnerabilities for every lockfile and image, IaC misconfiguration, licenses, SBOM |
| Opengrep | v1.30.1 (Semgrep CE 1.178.0 as fallback) | source patterns for TypeScript, Python, Go, Rust |
| Gitleaks | v8.30.1 | secrets in the tree and in git history |
| zizmor | v1.30.1 | GitHub Actions security |
| govulncheck | v1.8.0 | reachability for Go, to separate real from theoretical Go advisories |

- **Why these:** no two share a primary job (D section 7). Trivy alone covers every ecosystem's advisories, so `npm audit`, `pip-audit` and `cargo-audit` add nothing but cost: npm audit sends the full dependency list to the registry, and pip-audit can execute `setup.py` (D section 5). govulncheck stays because it is the only low-noise reachability analysis in the set.
- **Trivy, carefully:** on 2026-03-19 attackers published a malicious Trivy 0.69.4 and repointed 76 of 77 `trivy-action` tags to a credential stealer (GHSA-69fq-xp46-6x23, CVE-2026-33634, on CISA KEV). So Trivy is installed from a release verified by sha256 and cosign, never through those actions by tag, and run with `--disable-telemetry --skip-version-check` (D section 1).
- **Opengrep over Semgrep CE:** Opengrep removed telemetry and adds intra-file taint across functions. Semgrep's registry rules have been internal-use only since 2024-12-13 whichever engine runs them, so rule packs are fetched into the user's cache with their sha256 recorded in each report, never committed (D section 2).
- **Limiting self-suppression:** each tool runs from an empty working directory with explicit config, which stops `trivy.yaml`, `.trivyignore`, `.gitleaks.toml` and `zizmor.yml`; `nosemgrep` is disabled. What tools still honor is reported as data: Gitleaks always reads `.gitleaksignore` from its source (the history scan runs on a bare mirror, and each entry is a candidate), Opengrep reads the target's `.semgrepignore` and skips tests and vendor by default (the report lists the patterns), and inline `trivy:ignore`, `tfsec:ignore` and `zizmor: ignore` comments still apply.
- **No credentials leave with a scan:** Trivy runs with `--offline-scan` (otherwise a `pom.xml` can make it send the user's Maven credentials to a host the repository names), remote Terraform module sources are a question for the user first, and govulncheck runs with `GOTOOLCHAIN=local GOPROXY=off`.
- **Excluded:** CodeQL (its CLI license covers only OSI-licensed code without GitHub Advanced Security), TruffleHog (AGPL, and it sends each found secret to the provider to test it by default), checkov, hadolint, Syft and Grype (Trivy covers them), OSV-Scanner (optional later, if Trivy's PyPI data proves thin).
- **Scanner output is never a finding.** It enters the Cloudflare gate as candidates.

### SEC-3. A routing index picks at most one second lens per agent

`kit/security/index.yaml` tags every approved knowledge source by component and stack. The repository's threat model selects the entries that apply; each agent gets the Cloudflare file for its component plus at most one routed entry. Every run records what it loaded and why everything else was skipped.

Approved second-lens sources, loaded by the part the index names (mukul975 entries: their SKILL.md, never `scripts/`):

| Source | License | Used for |
| --- | --- | --- |
| [OpenAI `security-best-practices`](https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices) | Apache-2.0 | framework rules with stable IDs for Next.js, React, Express, Go, FastAPI, Django, Flask (e.g. `NEXT-ACTION-001`, Server Actions are public endpoints) |
| [Trail of Bits skills](https://github.com/trailofbits/skills) | CC-BY-SA-4.0 | `insecure-defaults` category files, `sharp-edges` language files, `variant-analysis`, `agentic-actions-auditor`, `fp-check` bug-class file, `building-secure-contracts` for non-EVM chains |
| [Sentry `security-review`, `gha-security-review`](https://github.com/getsentry/skills/tree/main/skills) | Apache-2.0 | GitHub Actions attack patterns and "do not flag" tables for false positives |
| mukul975 (15 skills) | Apache-2.0 | gaps no other source fills; see SEC-4 |
| `fin-*` (already pinned) | per pack | anything that moves money or touches a chain |

- **Conflict rule:** verdicts, severity and the evidence bar come only from the Cloudflare lens. A second lens contributes facts, never its own report format, severity scale or "fix and commit" instructions.
- **Trail of Bits stays unmodified:** CC-BY-SA allows installing and pinning the packs as they are; their text is never copied into the factory's MIT files.

### SEC-4. 15 of 817 mukul975 skills, 1.8%

The catalog is 75.6% out of scope by its own descriptions: SOC and detection (204), offensive (94), forensics (85), network and endpoint (59), malware (50), compliance (30) and more (A section 2). Of the 199 that touch the scope, 142 failed a full read: black-box testing that needs a live target, wrong example code, stale tools (tfsec, Terrascan, kube-hunter, `pip install trufflehog` for the abandoned v2), or dangerous advice, such as homemade zero-knowledge-proof code that claims replay resistance and has none (A section 3-4). Every skill ships `scripts/agent.py`; 35 of them disable TLS verification, and one generates a pickle remote-code-execution payload. **The scripts are never run.**

Kept, because each fills a gap the method and the other sources leave, with its known errors recorded in the index so a loading agent skips them:

| Skill | Gap it fills |
| --- | --- |
| `auditing-foundry-smart-contract-security` | EVM contracts with Foundry (errata: deprecated Chainlink field, an OpenZeppelin function removed in v5, no signature-replay check, a 64-hex regex that flags any constant) |
| `implementing-kubernetes-pod-security-standards` | Pod Security Standards levels against manifests |
| `auditing-kubernetes-rbac-privilege-escalation` | dangerous RBAC verbs as rules (skip its offensive privileged-pod step) |
| `performing-container-image-hardening` | Dockerfile and image hardening (skip its dpkg purge step) |
| `detecting-aws-iam-privilege-escalation` | IAM policy escalation combinations, offline (add `iam:PassRole` on `*` without `PassedToService`) |
| `securing-agentic-ai-tool-invocation` | the only source on agent tool-call authorization |
| `auditing-mcp-servers-for-tool-poisoning` | repositories that ship or configure MCP servers (never run its scanner; it may send tool descriptions to a vendor) |
| `exploiting-prototype-pollution-in-javascript` | its source-code detection patterns section only |
| `testing-cors-misconfiguration` | CORS origin reflection and credential rules |
| `implementing-api-schema-validation-security` | schema validation at the API boundary (ignore its regex-denylist fix) |
| `performing-graphql-depth-limit-attack` | Apollo depth and complexity limits |
| `implementing-jwt-signing-and-verification` | RFC 8725 algorithm allow-lists and claims |
| `configuring-oauth2-authorization-flow` | OAuth 2.1, PKCE, refresh rotation |
| `detecting-malicious-npm-packages` | lockfiles against known-bad versions (the 2025 npm worm), install scripts |
| `detecting-dependency-confusion` | registry scoping in `.npmrc`, `pip.conf` |

Rejected although they look relevant by name, among others: the XSS skills and the security-headers skill (the Burp XSS skill and the headers skill still recommend `X-XSS-Protection`; React and Next.js sinks are covered by OpenAI's rule files and the Cloudflare client-side file), the GitHub Actions skills (thin and with broken checks; zizmor and Sentry replace them), the cryptographic-audit skill (Trail of Bits `sharp-edges` covers crypto APIs per language), and every black-box API testing skill.

### SEC-5. Masriyan: ideas only

Rejected as a pack (B): its plugin manifest is broken, its committed bytecode is stale, its names break the Agent Skills format, its web content is on OWASP 2021, and it recommends 90-day password rotation (against NIST SP 800-63B) and the deprecated tfsec. Five ideas are rewritten into factory-security's own rules (`skills/factory-security/checklists.md` and step 6): rank dependency findings known-exploited (KEV) first, then by EPSS, reachability and CVSS; report IaC findings as misconfiguration, then what it reaches, then blast radius; crypto anti-patterns per language; signs of a malicious package; the OWASP LLM Top 10 (2025) as the checklist for LLM features.

### SEC-6. What factory-security adds itself

- **A threat model built from the repository**, not from an interview: `.factory/system/` (product, ADRs, constraints) plus the code, in the structure of OpenAI's `security-threat-model` (system model, trust boundaries, assets, entry points, attacker capabilities and non-capabilities, abuse paths). It names the components the router reads.
- **Findings become factory changes:** each confirmed finding is proposed as its own small change, with a regression test that fails before the fix. A lasting rule becomes a `SYS-C` row and, through `variant-analysis`, a scanner rule.
- **Runs live in `.factory/security/`, excluded from git.** Cloudflare's workflow keeps output outside the target unless the user picks a folder inside it; invoking the audit is that choice, and the folder is checked to be ignored.

## What this does not cover

- **No sandbox, no dynamic proof.** Cloudflare's method validates exploitability inside an isolated sandbox. Without one, factory-security leaves such candidates at `needs_validation` with a plan instead of guessing. A container runner is the recommended setup.
- **Rule coverage is thin for some stacks** (D section 2): Semgrep's default packs have 5 Rust rules, 4 React rules and none for Next.js. Next.js depth comes from OpenAI's rule files, Rust from Trail of Bits `sharp-edges` and Cloudflare's memory-safety file.
- **Packs that are not installed are skipped**, with a notice, until the user installs them and `/factory-packs` pins them after a read: today that is OpenAI's, Trail of Bits' and Sentry's.
- **The scanners are not installed or are out of date on this machine** (Trivy, Opengrep, zizmor missing; Gitleaks 8.18.1 lacks the subcommands; the local Semgrep install crashes on start). factory-security reports a missing tool as skipped, with its install line.
