# mukul975/Anthropic-Cybersecurity-Skills: fit for factory-security (S11)

Date: 2026-10-10. Catalog snapshot: 817 skills installed 2026-08-16 under `~/.agents/skills/`, source `mukul975/Anthropic-Cybersecurity-Skills` in `~/.agents/.skill-lock.json`.

## Verdict

Pin at most 11 skills whole (1.3% of the catalog), plus up to about 20 narrow ones selected by the routing index. A smaller and safer option is to pin none and lift about 30 vetted excerpts into factory-security's own checklists. Only 11 skills passed full-text review as core. Even those need edits, and none covers Go, Rust or Next.js server code. The catalog is mostly pentest, SOC and forensics content, and its bundled scripts are live attack clients.

## Key numbers

| Measure | Value |
|---|---|
| Skills in catalog | 817 (all have `SKILL.md`, `references/`, `scripts/agent.py`) |
| Bucket (a): topically in scope | 167 (20.4%) |
| Bucket (b): narrow case only | 32 (3.9%) |
| Bucket (c): out of scope | 618 (75.6%) |
| Full-text reviewed (a + b) | 199 |
| Verdict KEEP-CORE | 11 (1.3% of catalog) |
| Verdict KEEP-NARROW | 46 (5.6%) |
| Verdict REJECT | 142 of the 199 reviewed |
| Skills with source-review value 3/3 (concrete vulnerable-vs-fixed code or config) | 8 |
| Name + description text, all 817 | 358,596 chars, about 57k to 90k tokens |
| Full frontmatter, all 817 | 716,853 chars |
| Agent scripts that disable TLS verification (`verify=False`) | 35 |

The user expected 15% or less to matter. Topically 24% touch the scope, but only 7% survive a quality read, and only 1.3% are worth pinning whole.

## Method

1. Listed the 817 names from the lock file. Extracted `name`, `description` and `subdomain` from every SKILL.md frontmatter (`fm.json`).
2. Built a candidate pool by name and description keywords (373 hits). Read every pool description, then picked 199 candidates in seven themes (`cand.py`). Scanned the other 618 descriptions for missed app-sec terms (source code, repository, lockfile, Dockerfile, Terraform, OWASP). Only product-specific or detection skills turned up.
3. Nine parallel reviewers read the full SKILL.md, all `references/*.md` and skimmed `scripts/agent.py` for each of the 199. They ran nothing. Each skill got a mode, a source-review score 0 to 3, currency and issue notes, duplicates, a verdict, and quoted evidence. Per-group reports are in `parts/` (API1, API2, WEB1, WEB2, AUTH_CRYPTO_SECRETS, PIPELINE_SUPPLY, CONTAINER_K8S, IAC_CLOUD, LLM_WEB3_MOBILE). They hold the full per-skill evidence.
4. I spot-checked load-bearing claims against the files (see "Verification of reviewer claims").

Rubric for the source-review score: 0 none; 1 prose or tool tutorial; 2 some concrete patterns usable while reading a repo; 3 concrete vulnerable-vs-fixed code or config in our stacks, sink lists or file checks an agent can apply directly.

## 1. Classification

### Bucket (a): topically in scope, 167

| Theme | (a) | (b) | CORE | NARROW | REJECT |
|---|---|---|---|---|---|
| API authz and API controls | 29 | 1 | 1 | 11 | 18 |
| Web vulnerability classes | 32 | 2 | 5 | 14 | 15 |
| Auth, crypto, secrets | 21 | 9 | 1 | 8 | 21 |
| SAST/DAST pipeline, supply chain, vuln triage, threat modeling | 23 | 5 | 0 | 4 | 24 |
| Containers and Kubernetes | 25 | 6 | 2 | 4 | 25 |
| IaC and cloud | 23 | 2 | 0 | 2 | 23 |
| LLM/agent, web3, mobile | 14 | 7 | 2 | 3 | 16 |
| **Total** | **167** | **32** | **11** | **46** | **142** |

### Bucket (b): narrow case only, 32

| Narrow case | Skills |
|---|---|
| Repo ships a mobile app (5) | performing-android-app-static-analysis-with-mobsf, exploiting-insecure-data-storage-in-mobile, testing-android-intents-for-vulnerabilities, exploiting-deeplink-vulnerabilities, testing-mobile-api-authentication |
| Off-stack: PHP, SOAP, GitLab, C/C++ fuzzing (5) | exploiting-type-juggling-vulnerabilities, performing-soap-web-service-security-testing, building-devsecops-pipeline-with-gitlab-ci, implementing-fuzz-testing-in-cicd-with-aflplusplus, performing-fuzzing-with-aflplusplus |
| Niche crypto or identity (9) | configuring-hsm-for-key-storage, implementing-end-to-end-encryption-for-messaging, implementing-zero-knowledge-proof-for-authentication, implementing-saml-sso-with-okta, performing-oauth-scope-minimization-review, migrating-to-post-quantum-cryptography, performing-post-quantum-cryptography-migration, implementing-mtls-for-zero-trust-services, implementing-envelope-encryption-with-aws-kms |
| ML training pipelines (2) | detecting-data-and-model-poisoning, detecting-model-extraction-attacks |
| Specific product or paid platform (6) | implementing-aws-nitro-enclave-security, implementing-gcp-binary-authorization, securing-container-registry-with-harbor, implementing-api-security-testing-with-42crunch, performing-sca-dependency-scanning-with-snyk, implementing-github-advanced-security-for-code-scanning |
| Needs a live host or cluster (5) | hardening-docker-daemon-configuration, performing-docker-bench-security-assessment, performing-kubernetes-etcd-security-assessment, benchmarking-kubernetes-with-kube-bench, performing-kubernetes-cis-benchmark-with-kube-bench |

### Bucket (c): out of scope, 618

| Sub-theme | Count |
|---|---|
| C4 SOC, detection, threat hunting, threat intel | 204 |
| C1 offensive, red team, pentest of infrastructure, C2 | 94 |
| C3 forensics, incident response, ransomware | 85 |
| C6 network, endpoint, zero-trust products, firmware | 59 |
| C2 malware analysis, reverse engineering | 50 |
| C9 compliance, GRC, privacy, vulnerability-management programs | 30 |
| C5 enterprise identity (AD, Entra, Okta, PAM, IGA) | 28 |
| C7 OT and ICS | 28 |
| C10 cloud account operations (CSPM, GuardDuty, Security Hub) | 17 |
| C8 phishing, email, social engineering | 14 |
| C12 mobile dynamic testing (Frida, pinning bypass) | 5 |
| C13 WAF ops, RASP, Apigee | 3 |
| C11 runtime enforcement (Tetragon) | 1 |

Sub-themes come from the frontmatter `subdomain` field, with name rules overriding it (for example `exploiting-*` goes to C1). The frontmatter subdomains are themselves skewed: threat-hunting 58, threat-intelligence 52, digital-forensics 41, malware-analysis 39, soc-operations 35, red-teaming 33, against application-security 4 and supply-chain-security 8. Full name lists per bucket are in Appendices A and B.

## 2. Quality findings across the catalog

- **F1. Wrong mode for a static audit.** Most in-scope skills are black-box pentest recipes or live-account tutorials, not source review. Examples: 13 of 15 in API1 and 14 of 17 in WEB2 are Burp, curl or ZAP workflows against a running target. 21 of 25 IaC/cloud skills run `aws`, `gcloud` or `az` against live accounts. About 20 of 31 container/K8s skills need a live cluster, daemon or registry. What transfers to source review is the remediation and sink tables, usually in `references/` or the "Output Format" section.
- **F2. The bundled scripts are attack or ops tools.** Every skill has `scripts/agent.py`. 35 disable TLS verification (`verify=False`). Others do things like generate a pickle RCE payload (exploiting-insecure-deserialization), post manifests to the public `v2.kubesec.io` API (scanning-kubernetes-manifests-with-kubesec), run `kubectl apply` or `kubectl label` (the Calico and admission-controller skills), run SSM shell commands (implementing-aws-nitro-enclave-security), or read Azure storage keys (detecting-misconfigured-azure-storage). Never vendor or run the scripts.
- **F3. Example code is often wrong, even in good skills.** Examples:
  - The model Dockerfile in hardening-docker-containers-for-production has a non-root user that cannot read `/root/.local`.
  - One NetworkPolicy example reopens all egress.
  - A Calico GlobalNetworkPolicy example blocks pod-to-pod traffic cluster-wide.
  - An MFA SCP (`BoolIfExists`) denies every role session.
  - Permission-boundary and Lambda SCPs use `StringEquals` on wildcard ARNs, so they can never match.
  - WAF update steps wipe existing rules.
  - A Gatekeeper rule never fires on Deployments.
  - An SSVC decision tree treats a high EPSS score as "PoC exists".
  - A CVSS 4.0 calculator uses an invented linear formula.
- **F4. Dangerous advice.** implementing-zero-knowledge-proof-for-authentication ships a homemade Schnorr/ZKPP protocol. It is replayable, yet its checklist claims "Protocol resists replay attacks" (SKILL.md:86), and it publishes g^x behind PBKDF2, which allows an offline dictionary attack. implementing-nitro-enclave's attestation validator skips the signature and chain checks.
- **F5. The skills break the hygiene they teach.** Their workflows use `trivy-action@master` (for example scanning-iac-and-images-with-trivy/SKILL.md:216), `snyk/actions/node@master`, `curl | sh`, `:latest`, and secrets interpolated into `run:`. The tag-pinning point is not hypothetical: trivy-action had 76 of 77 tags rewritten to credential-stealing code on 2026-03-19 (CVE-2026-33634, on CISA KEV). Safe versions are trivy-action 0.35.0, setup-trivy 0.2.6 (recreated tag), and Trivy 0.69.2/0.69.3; 0.69.4 is malicious. S11 pins Trivy, so this is a direct input to the adapter pins: pin actions by commit SHA. Sources: [Debian tracker](https://security-tracker.debian.org/tracker/CVE-2026-33634), [CIRCL](https://cve.circl.lu/cve/CVE-2026-33634), [Docker Scout](https://scout.docker.com/vulnerabilities/id/CVE-2026-33634).
- **F6. Stale tooling.**
  - tfsec and Terrascan are recommended (auditing-terraform-infrastructure-for-security frontmatter lists `tfsec`).
  - `returntocorp/semgrep-action@v1` is deprecated (integrating-sast-into-github-actions-pipeline).
  - kube-hunter is archived (benchmarking-kubernetes-with-kube-bench:216).
  - etcd encryption uses `aescbc`, which upstream discourages in favor of KMS v2.
  - Docker Content Trust / Notary v1 still appears.
  - Notary is enabled on Harbor 2.10, but it was removed in 2.9.
  - `gitleaks protect` is deprecated.
  - `COSIGN_EXPERIMENTAL` is obsolete.
  - SLSA L4 is described, but SLSA v1.0 removed it.
  - CIS AWS 1.4/1.5 and Prowler v3 flags are used.
  - gcr.io has been shut down.
  - `pip install trufflehog` installs the abandoned v2 package, not v3 (detecting-aws-credential-exposure-with-trufflehog/SKILL.md:75, 89).
- **F7. Currency is good in places.** Where it matters, these are cited correctly: OWASP API Top 10 2023, OAuth 2.1 and RFC 9700, FIPS 203/204/205, OpenSSL 3.5 hybrid X25519MLKEM768, Pod Security Admission (PSP removal handled correctly), IMDSv2, and SameSite=Lax defaults. The web skills cite OWASP Top 10 2021, never 2025. The LLM skills cite LLM Top 10 2025 with some wrong numbering, and none uses the OWASP Top 10 for Agentic Applications (Dec 2025).
- **F8. Fabricated authority.** For example, implementing-api-abuse-detection-with-rate-limiting/SKILL.md:39 states a "94% reduction in successful DDoS attempts" with no source. Other unsourced metrics include a "99% accuracy" injection detector and a "2.3% false positive rate".
- **F9. Heavy duplication.** Clusters include JWT x5, SQLi x3, SSRF x3, XSS x2, Trivy x5, typosquatting x3, signing/provenance x5, vuln prioritization x4, IAM x4, serverless x4, CSPM x3, network policy x3, RBAC x3 and PQC x2. Each cluster has at most one keeper.
- **F10. Stack gaps.** No skill has Go or Rust vulnerable-vs-fixed code. None covers Next.js server actions, route handlers or SSR data leaks. None reviews LLM features from source: untrusted content in system prompts, tool output fed back, model output reaching SQL or shell, markdown-link exfiltration, tenant filters in retrieval. Threat modeling from code is also absent: the Threat Dragon skill is a GUI tutorial. Money-moving logic is covered only by remediation bullets in two pentest skills. The user's existing fin-* skills already cover that domain better.
- **F11. Frontmatter noise.** Each skill carries `nist_csf` and offensive `mitre_attack` tags (for example T1190 and T1059 on defensive skills). Some bodies contain copy-pasted SOC boilerplate unrelated to the skill, for example detecting-broken-object-property-level-authorization.

### Verification of reviewer claims

I confirmed these in the files: the trufflehog `pip install` lines, the ZKP replay claim (SKILL.md:86), the "94%" metric, `trivy-action@master`, `returntocorp/semgrep-action@v1`, kube-hunter, `aescbc`, the tfsec recommendation, and 35 `verify=False` scripts. I confirmed the trivy-action compromise by web search.

One correction to the WEB1 reviewer. The X-XSS-Protection problem is not in testing-for-xss-vulnerabilities, whose SKILL.md and references never recommend it. It is in two other places:
- testing-for-xss-vulnerabilities-with-burpsuite/SKILL.md:315 reports "X-XSS-Protection header not set" as a finding.
- performing-security-headers-audit/SKILL.md:169 says "Expected: 1; mode=block (or 0 if CSP is comprehensive)". Its own table at :302 correctly recommends `0`.

## 3. Ranked shortlist

### Tier 1: core, 11 skills (pin whole only after the noted edits, never the scripts)

| # | Skill | Covers | Why it beats alternatives | Quality notes |
|---|---|---|---|---|
| 1 | auditing-foundry-smart-contract-security | Solidity audit in Foundry: reentrancy, access control, oracle/price manipulation, arithmetic; Slither, Aderyn, forge fuzz and invariant tests behind a PASS/FAIL gate | Only checklist where each item says how to find, confirm and fix. The Ethereum sibling is boilerplate. Mythril is largely unmaintained. | Score 3. Fix: a deprecated Chainlink field, an OpenZeppelin function removed in v5, no general signature-replay check (domain, chainId, nonce), and a private-key regex that matches any 64-hex constant. Complements fin-onchain, which covers chain-boundary logic. |
| 2 | implementing-kubernetes-pod-security-standards | Field-level Baseline and Restricted rules with a fully hardened Deployment | Beats the PSA-controller skill (cluster admin) and securing-kubernetes-on-cloud (shallow survey) | Score 3, current (PSP removed, PSA GA). |
| 3 | performing-container-image-hardening | Dockerfile checklist: multi-stage, non-root, minimal packages, CIS Docker | hardening-docker-containers-for-production has a broken model Dockerfile. The distroless skill is a subset with a Python version mismatch. | Score 3. Drop its dpkg purge step. |
| 4 | exploiting-prototype-pollution-in-javascript | Node/TS sinks (merge, clone, set-by-path) and safe alternatives | Only skill in the web groups with an explicit "Source Code Detection Patterns" section (references/api-reference.md:56-82) | Score 3. Value sits in about 40 lines of references; the body is an exploit walkthrough. |
| 5 | testing-cors-misconfiguration | ACAO reflection, credentials with wildcard, unanchored origin regex, `null` origin | Sole CORS skill, and directly applies to API and SPA config | Score 3. |
| 6 | implementing-api-schema-validation-security | OpenAPI and JSON Schema hardening: `additionalProperties: false`, Pydantic `extra='forbid'`, readOnly, bounds | Only API skill with vulnerable-vs-fixed config. Covers mass assignment at the contract. 42Crunch duplicates it behind a vendor. | Score 3. Strip its regex-denylist "injection fix". |
| 7 | performing-cryptographic-audit-of-application | Weak algorithms, modes, hardcoded keys, IV reuse, KDF parameters, as a static review taxonomy | Only purpose-built static crypto review. The other crypto skills are build guides. | Score 3. Its scanner duplicates Semgrep/Bandit, so pin the taxonomy, not the script. |
| 8 | securing-agentic-ai-tool-invocation | Tool allowlist, argument validation, human approval, scoped credentials, audit log | Only skill on agent tool calls. All other LLM skills are runtime filters or red-team tool tutorials. | Score 2. Its approval prompt shows the approver only a hash of the arguments; treat that as a flaw to detect. Needs our own source checklist added (F10). |
| 9 | testing-for-xss-vulnerabilities | DOM sources and sinks including React `dangerouslySetInnerHTML` and Vue `v-html`, plus a CSP table | Beats the Burp duplicate, which also carries the X-XSS-Protection finding | Score 2. |
| 10 | performing-security-headers-audit | CSP, HSTS, frame-ancestors, Permissions-Policy, cookie attributes | Subsumes the clickjacking skill. Uses no HPKP, Expect-CT or Feature-Policy. | Score 2. Fix line 169 (X-XSS-Protection `1; mode=block`). |
| 11 | performing-graphql-depth-limit-attack | Apollo/Node depth limit, query complexity, limits config | Has in-stack config. The broad GraphQL assessment skill is a black-box umbrella. | Score 2. Pair with the introspection skill's field-authz checklist (Tier 2). |

### Tier 2: narrow, selected by the routing index (best of each cluster; rejected duplicates in parentheses)

| Router tag | Skill | Use | Notes |
|---|---|---|---|
| ci:github-actions | securing-github-actions-workflows | Starting checklist: SHA pins, `permissions`, script injection | Thin. Misses `pull_request_target` with PR-head checkout, `workflow_run`, `persist-credentials`, `GITHUB_ENV` injection, cache poisoning, `secrets: inherit`. Its audit scripts have false negatives (PyYAML parses `on:` as `True`). Prefer pinned zizmor + actionlint and compare with the local `ci-secure` skill first. (Rejected: detecting-supply-chain-attacks-in-ci-cd, whose SHA-pin check is broken.) |
| supply:private-registry | detecting-dependency-confusion | `.npmrc`, `pip.conf`, Maven `settings.xml` scope checks | One invalid pip example. |
| supply:npm | detecting-malicious-npm-packages | Lockfile vs known-bad versions (Shai-Hulud), install-script triage | Only skill naming the 2025 npm worm. (Rejected: three typosquatting skills.) |
| k8s | implementing-network-policies-for-kubernetes | Default-deny and DNS-only egress checks | Exclude the metadata-block example (reopens egress) and the 100.100.100.200 = Azure claim (it is Alibaba Cloud). |
| k8s:rbac | auditing-kubernetes-rbac-privilege-escalation | Dangerous-verb list as rules for Role and ClusterRole YAML | Drop the offensive privileged-pod step. (Rejected: implementing-rbac-hardening, whose secrets check misses list/watch/*.) |
| k8s:helm | securing-helm-chart-deployments | Render each chart with its shipped values before scanning; flag secrets in values.yaml | |
| iac:aws-iam | detecting-aws-iam-privilege-escalation | 14 privesc combos applied to IAM JSON, runs offline | Incomplete. Merge with the vector list from performing-aws-privilege-escalation-assessment (rejected as offensive and live), including `iam:PassRole` on `*` without `PassedToService`. |
| iac:serverless | detecting-serverless-function-injection | S3 key, SQS body, Dynamo stream and APIGW headers as untrusted sources into exec/eval/shell (Steps 2-3) | |
| iac:scan | scanning-iac-and-images-with-trivy | `trivy config` / `trivy fs` reference | Update renamed flags and SHA-pin the action (F5). Low value if the adapter already wraps Trivy. |
| web:ssrf | exploiting-server-side-request-forgery | SSRF-prone features and remediation, IMDSv2-aware | (Rejected: two SSRF duplicates, one pure boilerplate.) |
| web:nosql | exploiting-nosql-injection-vulnerabilities | Mongo/Node operator injection | Only NoSQL coverage. |
| web:sqli | exploiting-sql-injection-vulnerabilities, performing-second-order-sql-injection | SQLi taxonomy; "re-check data read back from DB" | PHP-heavy code. Semgrep covers most sinks. |
| web:python | exploiting-insecure-deserialization, exploiting-template-injection-vulnerabilities | pickle/YAML and Jinja2/EJS slices | Off-stack Java/PHP/.NET bulk. The deserialization script generates RCE payloads. |
| web:session | performing-csrf-attack-simulation, testing-for-open-redirect-vulnerabilities, testing-for-host-header-injection | Token and SameSite checklist; redirect and OAuth `redirect_uri`; reset links built from the Host header | |
| api:authz | detecting-broken-object-property-level-authorization, testing-for-broken-access-control | Property-level field tables; vertical, horizontal and tenant checklist | Black-box framing, so harvest tables only. |
| api:money | testing-for-business-logic-vulnerabilities (+ remediation bullets from exploiting-race-condition-vulnerabilities) | About 8 lines: server-side price, atomic balance update, idempotency key, single-use coupon guard | Prefer the existing fin-money-core and fin-ledger skills; fold these lines in only if missing there. |
| auth | implementing-jwt-signing-and-verification, configuring-oauth2-authorization-flow, implementing-hardware-security-key-authentication | RFC 8725 alg allowlist and claims; OAuth 2.1/PKCE/refresh rotation; WebAuthn RP | Only defensive members of the JWT x5, OAuth x3 and FIDO2 x2 clusters. |
| graphql | performing-graphql-introspection-attack | Introspection off and field-authz checklist | |
| websocket | testing-websocket-api-security | Origin check, handshake auth, CSWSH | |
| xml | testing-for-xxe-injection-vulnerabilities | defusedxml and DTD-off parser hardening | |
| llm:mcp | auditing-mcp-servers-for-tool-poisoning | Repos that ship or configure MCP servers | Its scanner may send tool descriptions to the vendor (verify before use). Misses the current MCP auth spec and uses the deprecated SSE transport. |
| mobile | performing-android-app-static-analysis-with-mobsf | Only if a repo ships an Android app | |

Lower value, keep only if a repo needs it: implementing-api-rate-limiting-and-throttling, implementing-api-key-security-controls, implementing-api-gateway-security-controls, testing-api-authentication-weaknesses, testing-api-for-mass-assignment-vulnerability, testing-for-sensitive-data-exposure, performing-web-application-vulnerability-triage, testing-for-email-header-injection, performing-content-security-policy-bypass, implementing-aes-encryption-for-data-at-rest, implementing-rsa-key-pair-management, configuring-tls-1-3-for-secure-communications, migrating-to-post-quantum-cryptography, implementing-secret-scanning-with-gitleaks (redundant with the pinned Gitleaks adapter), verifying-build-provenance-with-slsa-sigstore (only for repos that publish artifacts; the only signing skill current on SLSA v1.0), continuous-llm-red-teaming-with-promptfoo (CI suggestion, score 0).

## 4. Notable rejects that look relevant by name

| Skill | Why rejected |
|---|---|
| implementing-zero-knowledge-proof-for-authentication | Unsound homemade crypto: replayable, but claims replay resistance (SKILL.md:86). Never reuse. |
| auditing-terraform-infrastructure-for-security | tfsec/Terrascan; Rego that cannot match the plan JSON it is fed; wrong Checkov IDs. Trivy misconfig supersedes it. |
| implementing-infrastructure-as-code-security-scanning | Stale tfsec/KICS tutorial with contradictory Checkov IDs |
| implementing-semgrep-for-custom-sast-rules | One example rule cannot work; `--config auto` combined with `--metrics off` |
| integrating-sast-into-github-actions-pipeline | Deprecated `returntocorp/semgrep-action`; CSRF rule flags every POST |
| detecting-supply-chain-attacks-in-ci-cd | SHA-pin check broken; flags the safe env-var secret pattern |
| performing-threat-modeling-with-owasp-threat-dragon | GUI tutorial, no method for deriving a threat model from code. Only its STRIDE-per-element table and threat-register template are worth copying. |
| hardening-docker-containers-for-production | Broken model Dockerfile; promotes Docker Content Trust |
| securing-aws-iam-permissions, implementing-aws-iam-permission-boundaries, securing-aws-lambda-execution-roles | SCPs and conditions that never match or deny everything (F3) |
| detecting-indirect-prompt-injection, detecting-ai-model-prompt-injection-attacks, defending-llms-with-guardrails, implementing-llm-guardrails-for-security | Present classifiers or regex as the defense. One reads only the first 512 characters, one claims 99% accuracy, Llama Guard 3 is used although 4 exists, and NeMo config versions are mislabeled. |
| testing-prompt-injection-in-rag-pipelines | Its "indirect" script sends direct injection and counts refusals as successes |
| analyzing-ethereum-smart-contract-vulnerabilities | Boilerplate, superseded by the Foundry skill |
| detecting-aws-credential-exposure-with-trufflehog | `pip install trufflehog` installs abandoned v2 |
| triaging-vulnerabilities-with-ssvc-framework, prioritizing-vulnerabilities-with-cvss-scoring, implementing-epss-score-for-vulnerability-prioritization | Wrong SSVC tree; invented CVSS 4.0 formula; contradictory thresholds. A 5-line KEV + EPSS rule is enough. |
| testing-jwt-token-security, testing-for-json-web-token-vulnerabilities, exploiting-jwt-algorithm-confusion-attack, performing-jwt-none-algorithm-attack | Four offensive clones of one playbook. None cites RFC 8725. |
| performing-kubernetes-etcd-security-assessment, benchmarking-kubernetes-with-kube-bench | Live-cluster only; `aescbc`; archived kube-hunter |
| securing-container-registry-with-harbor | Notary on Harbor 2.10 (removed in 2.9); `curl -k` with the default admin password |
| implementing-api-abuse-detection-with-rate-limiting | Fabricated metrics (SKILL.md:39) and placeholder prose |
| performing-supply-chain-attack-simulation, performing-fuzzing-with-aflplusplus, performing-container-escape-detection, implementing-container-network-policies-with-calico, performing-container-security-scanning-with-trivy | Stubs |

## 5. Cost of having all 817 installed

- **Claude Code does not load them.** None of the 817 is in `~/.claude/skills` (0 of 817 symlinked), and none appears in this Claude Code session's skill list. The premise that they load in every Claude Code session is wrong for this machine.
- **OpenClaw does load them.** All 817 are symlinked into `~/.openclaw/skills` (927 entries in total there). Any harness that reads `~/.agents/skills` directly also sees them. The lock's `lastSelectedAgents` lists 18 targets, including codex, opencode, gemini-cli, cursor and openclaw. Whether each of those reads `~/.agents/skills` was not verified per harness. `~/.codex/skills` holds none of them.
- **Listing cost wherever they load.** Names plus descriptions total 358,596 chars, about 57k tokens at 1.33 tokens per word or about 90k at 4 chars per token. Call it roughly 60k to 90k tokens per session before any work. Mean description length is 402 chars, max 1,043. In Claude Code the skill listing is budget-capped, so most entries would be truncated or dropped, crowding out the user's own skills. The full frontmatter, including MITRE and NIST tags, is 716,853 chars if a harness loads it.
- **Behavioral risk on top of token cost.** Every skill is model-invocable and ships an offensive `agent.py`: 35 disable TLS verification, one generates RCE payloads, others mutate clusters or send data to third-party APIs. A broad prompt such as "test my API" can route into them.
- **Recommendation.** Uninstall the catalog from shared agent dirs. Vendor only the shortlisted SKILL.md excerpts (Apache-2.0 per frontmatter `license`), pinned by commit under `~/.software-factory/`. The S11 routing index then loads them per repo.

## 6. Implications for S11 design

- D1. Treat this catalog as a source of excerpts, not of skills to install. Pin at most Tier 1. Load Tier 2 entries only through the routing index (stack, component, threat-class tags), and never ship `scripts/`.
- D2. factory-security needs its own checklists for the gaps no catalog skill fills (F10):
  - Go and Rust source patterns
  - Next.js server actions and route handlers
  - LLM features reviewed from source
  - Modern GitHub Actions (zizmor-class checks)
  - A code-derived threat-model procedure (assets, trust boundaries, entry points, attackers; borrow STRIDE-per-element from Threat Dragon)
- D3. Money-moving review should route to the existing fin-* skills, not to this catalog.
- D4. Pin scanner GitHub Actions by commit SHA and avoid Trivy 0.69.4 / trivy-action ≤0.34.2 tags rewritten on 2026-03-19 (CVE-2026-33634).
- D5. Compare against Masriyan/Claude-Code-CyberSecurity-Skill (the README's second candidate) and the local `security-audit`, `security-review` and `ci-secure` skills before final selection. This report did not assess them.

## Files

- `fm.json`: frontmatter extract for all 817 (name, description, subdomain, sizes, file counts)
- `cand.py`, `verdicts.py`, `class_c.json`, `classify.py`: classification inputs and outputs
- `parts/*.md`: per-skill full-text reviews with evidence (9 files, about 260 KB)

## Appendix A. Bucket (a) and (b): all 199 in-scope candidates with verdicts

Verdict CORE/NARROW/REJECT comes from the full-text review (parts/<GROUP>.md). Bucket b = narrow topic case.

| Group | Skill | Bucket | Verdict |
|---|---|---|---|
| API | implementing-api-schema-validation-security | a | CORE |
| API | detecting-broken-object-property-level-authorization | a | NARROW |
| API | exploiting-race-condition-vulnerabilities | a | NARROW |
| API | implementing-api-gateway-security-controls | a | NARROW |
| API | implementing-api-key-security-controls | a | NARROW |
| API | implementing-api-rate-limiting-and-throttling | a | NARROW |
| API | performing-web-application-vulnerability-triage | a | NARROW |
| API | testing-api-authentication-weaknesses | a | NARROW |
| API | testing-api-for-mass-assignment-vulnerability | a | NARROW |
| API | testing-for-broken-access-control | a | NARROW |
| API | testing-for-business-logic-vulnerabilities | a | NARROW |
| API | testing-for-sensitive-data-exposure | a | NARROW |
| API | bypassing-authentication-with-forced-browsing | a | REJECT |
| API | conducting-api-security-testing | a | REJECT |
| API | detecting-shadow-api-endpoints | a | REJECT |
| API | exploiting-api-injection-vulnerabilities | a | REJECT |
| API | exploiting-broken-function-level-authorization | a | REJECT |
| API | exploiting-excessive-data-exposure-in-api | a | REJECT |
| API | exploiting-idor-vulnerabilities | a | REJECT |
| API | exploiting-mass-assignment-in-rest-apis | a | REJECT |
| API | implementing-api-abuse-detection-with-rate-limiting | a | REJECT |
| API | implementing-api-security-posture-management | a | REJECT |
| API | implementing-api-security-testing-with-42crunch | b | REJECT |
| API | performing-api-fuzzing-with-restler | a | REJECT |
| API | performing-api-inventory-and-discovery | a | REJECT |
| API | performing-api-rate-limiting-bypass | a | REJECT |
| API | performing-api-security-testing-with-postman | a | REJECT |
| API | performing-web-application-penetration-test | a | REJECT |
| API | testing-api-for-broken-object-level-authorization | a | REJECT |
| API | testing-api-security-with-owasp-top-10 | a | REJECT |
| WEB | exploiting-prototype-pollution-in-javascript | a | CORE |
| WEB | performing-graphql-depth-limit-attack | a | CORE |
| WEB | performing-security-headers-audit | a | CORE |
| WEB | testing-cors-misconfiguration | a | CORE |
| WEB | testing-for-xss-vulnerabilities | a | CORE |
| WEB | exploiting-insecure-deserialization | a | NARROW |
| WEB | exploiting-nosql-injection-vulnerabilities | a | NARROW |
| WEB | exploiting-server-side-request-forgery | a | NARROW |
| WEB | exploiting-sql-injection-vulnerabilities | a | NARROW |
| WEB | exploiting-template-injection-vulnerabilities | a | NARROW |
| WEB | performing-content-security-policy-bypass | a | NARROW |
| WEB | performing-csrf-attack-simulation | a | NARROW |
| WEB | performing-graphql-introspection-attack | a | NARROW |
| WEB | performing-second-order-sql-injection | a | NARROW |
| WEB | testing-for-email-header-injection | a | NARROW |
| WEB | testing-for-host-header-injection | a | NARROW |
| WEB | testing-for-open-redirect-vulnerabilities | a | NARROW |
| WEB | testing-for-xxe-injection-vulnerabilities | a | NARROW |
| WEB | testing-websocket-api-security | a | NARROW |
| WEB | exploiting-http-request-smuggling | a | REJECT |
| WEB | exploiting-sql-injection-with-sqlmap | a | REJECT |
| WEB | exploiting-type-juggling-vulnerabilities | b | REJECT |
| WEB | exploiting-websocket-vulnerabilities | a | REJECT |
| WEB | performing-blind-ssrf-exploitation | a | REJECT |
| WEB | performing-clickjacking-attack-test | a | REJECT |
| WEB | performing-directory-traversal-testing | a | REJECT |
| WEB | performing-graphql-security-assessment | a | REJECT |
| WEB | performing-http-parameter-pollution-attack | a | REJECT |
| WEB | performing-soap-web-service-security-testing | b | REJECT |
| WEB | performing-ssrf-vulnerability-exploitation | a | REJECT |
| WEB | performing-web-cache-deception-attack | a | REJECT |
| WEB | performing-web-cache-poisoning-attack | a | REJECT |
| WEB | testing-for-xml-injection-vulnerabilities | a | REJECT |
| WEB | testing-for-xss-vulnerabilities-with-burpsuite | a | REJECT |
| AUTH_CRYPTO_SECRETS | performing-cryptographic-audit-of-application | a | CORE |
| AUTH_CRYPTO_SECRETS | configuring-oauth2-authorization-flow | a | NARROW |
| AUTH_CRYPTO_SECRETS | configuring-tls-1-3-for-secure-communications | a | NARROW |
| AUTH_CRYPTO_SECRETS | implementing-aes-encryption-for-data-at-rest | a | NARROW |
| AUTH_CRYPTO_SECRETS | implementing-hardware-security-key-authentication | a | NARROW |
| AUTH_CRYPTO_SECRETS | implementing-jwt-signing-and-verification | a | NARROW |
| AUTH_CRYPTO_SECRETS | implementing-rsa-key-pair-management | a | NARROW |
| AUTH_CRYPTO_SECRETS | implementing-secret-scanning-with-gitleaks | a | NARROW |
| AUTH_CRYPTO_SECRETS | migrating-to-post-quantum-cryptography | b | NARROW |
| AUTH_CRYPTO_SECRETS | configuring-hsm-for-key-storage | b | REJECT |
| AUTH_CRYPTO_SECRETS | detecting-aws-credential-exposure-with-trufflehog | a | REJECT |
| AUTH_CRYPTO_SECRETS | exploiting-jwt-algorithm-confusion-attack | a | REJECT |
| AUTH_CRYPTO_SECRETS | exploiting-oauth-misconfiguration | a | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-digital-signatures-with-ed25519 | a | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-end-to-end-encryption-for-messaging | b | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-envelope-encryption-with-aws-kms | b | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-hashicorp-vault-dynamic-secrets | a | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-mtls-for-zero-trust-services | b | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-passwordless-authentication-with-fido2 | a | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-saml-sso-with-okta | b | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-secrets-management-with-vault | a | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-secrets-scanning-in-ci-cd | a | REJECT |
| AUTH_CRYPTO_SECRETS | implementing-zero-knowledge-proof-for-authentication | b | REJECT |
| AUTH_CRYPTO_SECRETS | performing-jwt-none-algorithm-attack | a | REJECT |
| AUTH_CRYPTO_SECRETS | performing-oauth-scope-minimization-review | b | REJECT |
| AUTH_CRYPTO_SECRETS | performing-post-quantum-cryptography-migration | b | REJECT |
| AUTH_CRYPTO_SECRETS | performing-ssl-tls-security-assessment | a | REJECT |
| AUTH_CRYPTO_SECRETS | testing-for-json-web-token-vulnerabilities | a | REJECT |
| AUTH_CRYPTO_SECRETS | testing-jwt-token-security | a | REJECT |
| AUTH_CRYPTO_SECRETS | testing-oauth2-implementation-flaws | a | REJECT |
| PIPELINE_SUPPLY | detecting-dependency-confusion | a | NARROW |
| PIPELINE_SUPPLY | detecting-malicious-npm-packages | a | NARROW |
| PIPELINE_SUPPLY | securing-github-actions-workflows | a | NARROW |
| PIPELINE_SUPPLY | verifying-build-provenance-with-slsa-sigstore | a | NARROW |
| PIPELINE_SUPPLY | analyzing-sbom-for-supply-chain-vulnerabilities | a | REJECT |
| PIPELINE_SUPPLY | building-devsecops-pipeline-with-gitlab-ci | b | REJECT |
| PIPELINE_SUPPLY | detecting-supply-chain-attacks-in-ci-cd | a | REJECT |
| PIPELINE_SUPPLY | detecting-typosquatting-packages | a | REJECT |
| PIPELINE_SUPPLY | detecting-typosquatting-packages-in-npm-pypi | a | REJECT |
| PIPELINE_SUPPLY | generating-and-analyzing-sboms | a | REJECT |
| PIPELINE_SUPPLY | implementing-code-signing-for-artifacts | a | REJECT |
| PIPELINE_SUPPLY | implementing-devsecops-security-scanning | a | REJECT |
| PIPELINE_SUPPLY | implementing-epss-score-for-vulnerability-prioritization | a | REJECT |
| PIPELINE_SUPPLY | implementing-fuzz-testing-in-cicd-with-aflplusplus | b | REJECT |
| PIPELINE_SUPPLY | implementing-github-advanced-security-for-code-scanning | b | REJECT |
| PIPELINE_SUPPLY | implementing-image-provenance-verification-with-cosign | a | REJECT |
| PIPELINE_SUPPLY | implementing-semgrep-for-custom-sast-rules | a | REJECT |
| PIPELINE_SUPPLY | implementing-sigstore-for-software-signing | a | REJECT |
| PIPELINE_SUPPLY | implementing-supply-chain-security-with-in-toto | a | REJECT |
| PIPELINE_SUPPLY | integrating-dast-with-owasp-zap-in-pipeline | a | REJECT |
| PIPELINE_SUPPLY | integrating-sast-into-github-actions-pipeline | a | REJECT |
| PIPELINE_SUPPLY | performing-cve-prioritization-with-kev-catalog | a | REJECT |
| PIPELINE_SUPPLY | performing-fuzzing-with-aflplusplus | b | REJECT |
| PIPELINE_SUPPLY | performing-sca-dependency-scanning-with-snyk | b | REJECT |
| PIPELINE_SUPPLY | performing-supply-chain-attack-simulation | a | REJECT |
| PIPELINE_SUPPLY | performing-threat-modeling-with-owasp-threat-dragon | a | REJECT |
| PIPELINE_SUPPLY | prioritizing-vulnerabilities-with-cvss-scoring | a | REJECT |
| PIPELINE_SUPPLY | triaging-vulnerabilities-with-ssvc-framework | a | REJECT |
| CONTAINER_K8S | implementing-kubernetes-pod-security-standards | a | CORE |
| CONTAINER_K8S | performing-container-image-hardening | a | CORE |
| CONTAINER_K8S | auditing-kubernetes-rbac-privilege-escalation | a | NARROW |
| CONTAINER_K8S | implementing-network-policies-for-kubernetes | a | NARROW |
| CONTAINER_K8S | scanning-iac-and-images-with-trivy | a | NARROW |
| CONTAINER_K8S | securing-helm-chart-deployments | a | NARROW |
| CONTAINER_K8S | auditing-kubernetes-cluster-rbac | a | REJECT |
| CONTAINER_K8S | benchmarking-kubernetes-with-kube-bench | b | REJECT |
| CONTAINER_K8S | detecting-privilege-escalation-in-kubernetes-pods | a | REJECT |
| CONTAINER_K8S | hardening-docker-containers-for-production | a | REJECT |
| CONTAINER_K8S | hardening-docker-daemon-configuration | b | REJECT |
| CONTAINER_K8S | implementing-aqua-security-for-container-scanning | a | REJECT |
| CONTAINER_K8S | implementing-container-image-minimal-base-with-distroless | a | REJECT |
| CONTAINER_K8S | implementing-container-network-policies-with-calico | a | REJECT |
| CONTAINER_K8S | implementing-kubernetes-network-policy-with-calico | a | REJECT |
| CONTAINER_K8S | implementing-opa-gatekeeper-for-policy-enforcement | a | REJECT |
| CONTAINER_K8S | implementing-pod-security-admission-controller | a | REJECT |
| CONTAINER_K8S | implementing-policy-as-code-with-open-policy-agent | a | REJECT |
| CONTAINER_K8S | implementing-rbac-hardening-for-kubernetes | a | REJECT |
| CONTAINER_K8S | performing-container-escape-detection | a | REJECT |
| CONTAINER_K8S | performing-container-security-scanning-with-trivy | a | REJECT |
| CONTAINER_K8S | performing-docker-bench-security-assessment | b | REJECT |
| CONTAINER_K8S | performing-kubernetes-cis-benchmark-with-kube-bench | b | REJECT |
| CONTAINER_K8S | performing-kubernetes-etcd-security-assessment | b | REJECT |
| CONTAINER_K8S | scanning-container-images-with-grype | a | REJECT |
| CONTAINER_K8S | scanning-containers-with-trivy-in-cicd | a | REJECT |
| CONTAINER_K8S | scanning-docker-images-with-trivy | a | REJECT |
| CONTAINER_K8S | scanning-kubernetes-manifests-with-kubesec | a | REJECT |
| CONTAINER_K8S | securing-container-registry-images | a | REJECT |
| CONTAINER_K8S | securing-container-registry-with-harbor | b | REJECT |
| CONTAINER_K8S | securing-kubernetes-on-cloud | a | REJECT |
| IAC_CLOUD | detecting-aws-iam-privilege-escalation | a | NARROW |
| IAC_CLOUD | detecting-serverless-function-injection | a | NARROW |
| IAC_CLOUD | auditing-aws-s3-bucket-permissions | a | REJECT |
| IAC_CLOUD | auditing-cloud-with-cis-benchmarks | a | REJECT |
| IAC_CLOUD | auditing-gcp-iam-permissions | a | REJECT |
| IAC_CLOUD | auditing-terraform-infrastructure-for-security | a | REJECT |
| IAC_CLOUD | detecting-azure-storage-account-misconfigurations | a | REJECT |
| IAC_CLOUD | detecting-misconfigured-azure-storage | a | REJECT |
| IAC_CLOUD | implementing-aws-iam-permission-boundaries | a | REJECT |
| IAC_CLOUD | implementing-aws-nitro-enclave-security | b | REJECT |
| IAC_CLOUD | implementing-cloud-security-posture-management | a | REJECT |
| IAC_CLOUD | implementing-cloud-vulnerability-posture-management | a | REJECT |
| IAC_CLOUD | implementing-cloud-waf-rules | a | REJECT |
| IAC_CLOUD | implementing-gcp-binary-authorization | b | REJECT |
| IAC_CLOUD | implementing-gcp-organization-policy-constraints | a | REJECT |
| IAC_CLOUD | implementing-gcp-vpc-firewall-rules | a | REJECT |
| IAC_CLOUD | implementing-infrastructure-as-code-security-scanning | a | REJECT |
| IAC_CLOUD | performing-aws-account-enumeration-with-scout-suite | a | REJECT |
| IAC_CLOUD | performing-aws-privilege-escalation-assessment | a | REJECT |
| IAC_CLOUD | performing-serverless-function-security-review | a | REJECT |
| IAC_CLOUD | remediating-s3-bucket-misconfiguration | a | REJECT |
| IAC_CLOUD | securing-api-gateway-with-aws-waf | a | REJECT |
| IAC_CLOUD | securing-aws-iam-permissions | a | REJECT |
| IAC_CLOUD | securing-aws-lambda-execution-roles | a | REJECT |
| IAC_CLOUD | securing-serverless-functions | a | REJECT |
| LLM_WEB3_MOBILE | auditing-foundry-smart-contract-security | a | CORE |
| LLM_WEB3_MOBILE | securing-agentic-ai-tool-invocation | a | CORE |
| LLM_WEB3_MOBILE | auditing-mcp-servers-for-tool-poisoning | a | NARROW |
| LLM_WEB3_MOBILE | continuous-llm-red-teaming-with-promptfoo | a | NARROW |
| LLM_WEB3_MOBILE | performing-android-app-static-analysis-with-mobsf | b | NARROW |
| LLM_WEB3_MOBILE | analyzing-ethereum-smart-contract-vulnerabilities | a | REJECT |
| LLM_WEB3_MOBILE | assessing-vector-and-embedding-weaknesses | a | REJECT |
| LLM_WEB3_MOBILE | defending-llms-with-guardrails | a | REJECT |
| LLM_WEB3_MOBILE | detecting-ai-model-prompt-injection-attacks | a | REJECT |
| LLM_WEB3_MOBILE | detecting-data-and-model-poisoning | b | REJECT |
| LLM_WEB3_MOBILE | detecting-indirect-prompt-injection | a | REJECT |
| LLM_WEB3_MOBILE | detecting-model-extraction-attacks | b | REJECT |
| LLM_WEB3_MOBILE | exploiting-deeplink-vulnerabilities | b | REJECT |
| LLM_WEB3_MOBILE | exploiting-insecure-data-storage-in-mobile | b | REJECT |
| LLM_WEB3_MOBILE | implementing-llm-guardrails-for-security | a | REJECT |
| LLM_WEB3_MOBILE | orchestrating-llm-attacks-with-pyrit | a | REJECT |
| LLM_WEB3_MOBILE | red-teaming-llms-with-garak | a | REJECT |
| LLM_WEB3_MOBILE | testing-android-intents-for-vulnerabilities | b | REJECT |
| LLM_WEB3_MOBILE | testing-for-system-prompt-leakage | a | REJECT |
| LLM_WEB3_MOBILE | testing-mobile-api-authentication | b | REJECT |
| LLM_WEB3_MOBILE | testing-prompt-injection-in-rag-pipelines | a | REJECT |

## Appendix B. Bucket (c): 618 out-of-scope skills by sub-theme

### C1 offensive / red team / pentest (94)

abusing-dpapi-for-credential-access, abusing-shadow-credentials-for-privesc, attacking-entra-id-with-roadtools, attacking-oauth-with-device-code-phishing, building-c2-infrastructure-with-sliver-framework, building-c2-redirector-infrastructure, building-red-team-c2-infrastructure-with-havoc, building-threat-actor-profile-from-osint, coercing-authentication-with-coercer-petitpotam, conducting-cloud-penetration-testing, conducting-domain-persistence-with-dcsync, conducting-external-reconnaissance-with-osint, conducting-full-scope-red-team-engagement, conducting-internal-network-penetration-test, conducting-internal-reconnaissance-with-bloodhound-ce, conducting-man-in-the-middle-attack-simulation, conducting-mobile-app-penetration-test, conducting-network-penetration-test, conducting-pass-the-ticket-attack, conducting-social-engineering-penetration-test, conducting-social-engineering-pretext-call, conducting-spearphishing-simulation-campaign, conducting-wireless-network-penetration-test, detecting-dcsync-attack-in-active-directory, detecting-kerberoasting-attacks, detecting-pass-the-ticket-attacks, emulating-cloud-attacks-with-stratus-red-team, enumerating-cloud-with-cloudfox, escaping-containers-to-host, executing-active-directory-attack-simulation, executing-phishing-simulation-campaign, executing-red-team-engagement-planning, executing-red-team-exercise, exploiting-active-directory-certificate-services-esc1, exploiting-active-directory-with-bloodhound, exploiting-adcs-with-certipy, exploiting-aws-with-pacu, exploiting-bgp-hijacking-vulnerabilities, exploiting-broken-link-hijacking, exploiting-constrained-delegation-abuse, exploiting-ipv6-vulnerabilities, exploiting-kerberoasting-with-impacket, exploiting-ms17-010-eternalblue-vulnerability, exploiting-nopac-cve-2021-42278-42287, exploiting-smb-vulnerabilities-with-metasploit, exploiting-vulnerabilities-with-metasploit-framework, exploiting-zerologon-vulnerability-cve-2020-1472, hunting-for-dcsync-attacks, hunting-for-domain-fronting-c2-traffic, implementing-attack-surface-management, mapping-attack-paths-with-bloodhound-ce, moving-laterally-with-netexec, operating-havoc-c2, operating-sliver-c2, performing-active-directory-bloodhound-analysis, performing-active-directory-forest-trust-attack, performing-active-directory-penetration-test, performing-ai-driven-osint-correlation, performing-arp-spoofing-attack-simulation, performing-bandwidth-throttling-attack-simulation, performing-binary-exploitation-analysis, performing-cloud-penetration-testing-with-pacu, performing-credential-access-with-lazagne, performing-external-network-penetration-test, performing-gcp-penetration-testing-with-gcpbucketbrute, performing-hash-cracking-with-hashcat, performing-initial-access-with-evilginx3, performing-iot-security-assessment, performing-kerberoasting-attack, performing-kubernetes-penetration-testing, performing-lateral-movement-with-wmiexec, performing-open-source-intelligence-gathering, performing-osint-with-spiderfoot, performing-phishing-simulation-with-gophish, performing-physical-intrusion-assessment, performing-privilege-escalation-assessment, performing-privilege-escalation-on-linux, performing-purple-team-atomic-testing, performing-purple-team-exercise, performing-red-team-phishing-with-gophish, performing-red-team-with-covenant, performing-soc2-type2-audit-preparation, performing-ssl-stripping-attack, performing-subdomain-enumeration-with-subfinder, performing-thick-client-application-penetration-test, performing-threat-emulation-with-atomic-red-team, performing-vlan-hopping-attack, performing-vulnerability-scanning-with-nessus, performing-web-application-firewall-bypass, performing-wifi-password-cracking-with-aircrack, performing-wireless-network-penetration-test, post-exploiting-microsoft-graph-with-graphrunner, relaying-ntlm-for-adcs-esc8, scanning-network-with-nmap-advanced

### C2 malware analysis / reverse engineering (50)

analyzing-android-malware-with-apktool, analyzing-bootkit-and-rootkit-samples, analyzing-cobalt-strike-beacon-configuration, analyzing-cobaltstrike-malleable-c2-profiles, analyzing-golang-malware-with-ghidra, analyzing-linux-elf-malware, analyzing-linux-kernel-rootkits, analyzing-macro-malware-in-office-documents, analyzing-malware-behavior-with-cuckoo-sandbox, analyzing-malware-family-relationships-with-malpedia, analyzing-malware-persistence-with-autoruns, analyzing-malware-sandbox-evasion-techniques, analyzing-network-covert-channels-in-malware, analyzing-network-traffic-of-malware, analyzing-packed-malware-with-upx-unpacker, analyzing-pdf-malware-with-pdfid, analyzing-ransomware-encryption-mechanisms, analyzing-supply-chain-malware-artifacts, analyzing-uefi-bootkit-persistence, building-automated-malware-submission-pipeline, building-malware-incident-communication-template, conducting-malware-incident-response, deobfuscating-javascript-malware, deobfuscating-powershell-obfuscated-malware, detecting-fileless-malware-techniques, detecting-mobile-malware-behavior, detecting-ransomware-encryption-behavior, detecting-rootkit-activity, eradicating-malware-from-infected-systems, extracting-config-from-agent-tesla-rat, extracting-iocs-from-malware-samples, hunting-bootkits-in-efi-system-partition, hunting-for-cobalt-strike-beacons, implementing-email-sandboxing-with-proofpoint, performing-automated-malware-analysis-with-cape, performing-dynamic-analysis-with-any-run, performing-firmware-malware-analysis, performing-malware-hash-enrichment-with-virustotal, performing-malware-ioc-extraction, performing-malware-persistence-investigation, performing-malware-triage-with-yara, performing-static-malware-analysis-with-pe-studio, performing-threat-hunting-with-yara-rules, performing-yara-rule-development-for-detection, reverse-engineering-android-malware-with-jadx, reverse-engineering-dotnet-malware-with-dnspy, reverse-engineering-ios-app-with-frida, reverse-engineering-malware-with-ghidra, reverse-engineering-ransomware-encryption-routine, reverse-engineering-rust-malware

### C3 forensics / incident response / ransomware (85)

acquiring-disk-image-with-dd-and-dcfldd, analyzing-browser-forensics-with-hindsight, analyzing-campaign-attribution-evidence, analyzing-disk-image-with-autopsy, analyzing-docker-container-forensics, analyzing-linux-system-artifacts, analyzing-lnk-file-and-jump-list-artifacts, analyzing-memory-dumps-with-volatility, analyzing-memory-forensics-with-lime-and-volatility, analyzing-mft-for-deleted-file-recovery, analyzing-network-traffic-for-incidents, analyzing-outlook-pst-for-email-forensics, analyzing-powershell-empire-artifacts, analyzing-ransomware-leak-site-intelligence, analyzing-ransomware-network-indicators, analyzing-ransomware-payment-wallets, analyzing-slack-space-and-file-system-artifacts, analyzing-windows-amcache-artifacts, analyzing-windows-lnk-files-for-artifacts, analyzing-windows-registry-for-artifacts, analyzing-windows-shellbag-artifacts, building-incident-response-dashboard, building-incident-response-playbook, building-incident-timeline-with-timesketch, building-ransomware-playbook-with-cisa-framework, building-soc-playbook-for-ransomware, building-super-timelines-with-plaso, collecting-indicators-of-compromise, collecting-volatile-evidence-from-compromised-host, conducting-cloud-incident-response, conducting-memory-forensics-with-volatility, conducting-phishing-incident-response, conducting-post-incident-lessons-learned, containing-active-breach, deploying-decoy-files-for-ransomware-detection, deploying-ransomware-canary-files, detecting-ransomware-precursors-in-network, extracting-browser-history-artifacts, extracting-credentials-from-memory-dump, extracting-memory-artifacts-with-rekall, extracting-windows-event-logs-artifacts, fleet-hunting-with-velociraptor, generating-forensic-timelines-with-hayabusa, implementing-anti-ransomware-group-policy, implementing-honeypot-for-ransomware-detection, implementing-immutable-backup-with-restic, implementing-ot-incident-response-playbook, implementing-ransomware-backup-strategy, implementing-ransomware-kill-switch-detection, implementing-ticketing-system-for-incidents, implementing-velociraptor-for-ir-collection, investigating-phishing-email-incident, investigating-ransomware-attack-artifacts, parsing-artifacts-with-eric-zimmerman-tools, performing-active-directory-compromise-investigation, performing-cloud-forensics-investigation, performing-cloud-forensics-with-aws-cloudtrail, performing-cloud-incident-containment-procedures, performing-cloud-log-forensics-with-athena, performing-cloud-native-forensics-with-falco, performing-cloud-storage-forensic-acquisition, performing-disk-forensics-investigation, performing-endpoint-forensics-investigation, performing-file-carving-with-foremost, performing-insider-threat-investigation, performing-linux-log-forensics-investigation, performing-log-analysis-for-forensic-investigation, performing-memory-forensics-with-volatility3, performing-memory-forensics-with-volatility3-plugins, performing-mobile-device-forensics-with-cellebrite, performing-network-forensics-with-wireshark, performing-network-packet-capture-analysis, performing-ransomware-response, performing-ransomware-tabletop-exercise, performing-sqlite-database-forensics, performing-steganography-detection, performing-timeline-reconstruction-with-plaso, performing-windows-artifact-analysis-with-eric-zimmerman-tools, recovering-deleted-files-with-photorec, recovering-from-ransomware-attack, testing-ransomware-recovery-procedures, triaging-security-incident, triaging-security-incident-with-ir-playbook, triaging-windows-with-kape, validating-backup-integrity-for-recovery

### C4 SOC / detection / hunting / threat intel (204)

analyzing-active-directory-acl-abuse, analyzing-api-gateway-access-logs, analyzing-apt-group-with-mitre-navigator, analyzing-azure-activity-logs-for-threats, analyzing-certificate-transparency-for-phishing, analyzing-cloud-storage-access-patterns, analyzing-command-and-control-communication, analyzing-cyber-kill-chain, analyzing-dns-logs-for-exfiltration, analyzing-email-headers-for-phishing-investigation, analyzing-heap-spray-exploitation, analyzing-indicators-of-compromise, analyzing-ios-app-security-with-objection, analyzing-kubernetes-audit-logs, analyzing-linux-audit-logs-for-intrusion, analyzing-malicious-pdf-with-peepdf, analyzing-network-flow-data-with-netflow, analyzing-network-packets-with-scapy, analyzing-network-traffic-with-wireshark, analyzing-office365-audit-logs-for-compromise, analyzing-persistence-mechanisms-in-linux, analyzing-powershell-script-block-logging, analyzing-prefetch-files-for-execution-history, analyzing-security-logs-with-splunk, analyzing-threat-actor-ttps-with-mitre-attack, analyzing-threat-actor-ttps-with-mitre-navigator, analyzing-threat-intelligence-feeds, analyzing-threat-landscape-with-misp, analyzing-tls-certificate-transparency-logs, analyzing-typosquatting-domains-with-dnstwist, analyzing-usb-device-connection-history, analyzing-web-server-logs-for-intrusion, analyzing-windows-event-logs-in-splunk, analyzing-windows-prefetch-with-python, auditing-tls-certificate-transparency-logs, automating-ioc-enrichment, building-adversary-infrastructure-tracking-system, building-attack-pattern-library-from-cti-reports, building-detection-rule-with-splunk-spl, building-detection-rules-with-sigma, building-ioc-defanging-and-sharing-pipeline, building-ioc-enrichment-pipeline-with-opencti, building-soc-escalation-matrix, building-soc-metrics-and-kpi-tracking, building-threat-feed-aggregation-with-misp, building-threat-hunt-hypothesis-framework, building-threat-intelligence-enrichment-in-splunk, building-threat-intelligence-feed-integration, building-threat-intelligence-platform, building-vulnerability-scanning-workflow, collecting-open-source-intelligence, collecting-threat-intelligence-with-misp, correlating-security-events-in-qradar, correlating-threat-campaigns, deploying-active-directory-honeytokens, deploying-cloud-deception-with-decoy-resources, deploying-honeytokens-and-canarytokens, designing-adversary-engagement-with-mitre-engage, detecting-anomalous-authentication-patterns, detecting-api-enumeration-attacks, detecting-arp-poisoning-in-network-traffic, detecting-aws-cloudtrail-anomalies, detecting-aws-guardduty-findings-automation, detecting-azure-lateral-movement, detecting-azure-service-principal-abuse, detecting-beaconing-patterns-with-zeek, detecting-bluetooth-low-energy-attacks, detecting-cloud-threats-with-guardduty, detecting-command-and-control-over-dns, detecting-compromised-cloud-credentials, detecting-container-drift-at-runtime, detecting-container-escape-attempts, detecting-container-escape-with-falco-rules, detecting-container-runtime-threats-with-falco, detecting-credential-dumping-techniques, detecting-cryptomining-in-cloud, detecting-dll-sideloading-attacks, detecting-dns-exfiltration-with-dns-query-analysis, detecting-email-account-compromise, detecting-email-forwarding-rules-attack, detecting-entra-offensive-tools-in-graph-logs, detecting-evasion-techniques-in-endpoint-logs, detecting-exfiltration-over-dns-with-zeek, detecting-fileless-attacks-on-endpoints, detecting-golden-ticket-attacks-in-kerberos-logs, detecting-golden-ticket-forgery, detecting-insider-data-exfiltration-via-dlp, detecting-insider-threat-behaviors, detecting-insider-threat-with-ueba, detecting-lateral-movement-in-network, detecting-lateral-movement-with-splunk, detecting-lateral-movement-with-zeek, detecting-living-off-the-land-attacks, detecting-living-off-the-land-with-lolbas, detecting-malicious-scheduled-tasks-with-sysmon, detecting-mimikatz-execution-patterns, detecting-network-anomalies-with-zeek, detecting-network-scanning-with-ids-signatures, detecting-ntlm-relay-with-event-correlation, detecting-oauth-token-theft, detecting-pass-the-hash-attacks, detecting-port-scanning-with-fail2ban, detecting-privilege-escalation-attempts, detecting-process-hollowing-technique, detecting-process-injection-techniques, detecting-rdp-brute-force-attacks, detecting-s3-data-exfiltration-attempts, detecting-secure-boot-bypass, detecting-service-account-abuse, detecting-shadow-it-cloud-usage, detecting-sql-injection-via-waf-logs, detecting-suspicious-oauth-application-consent, detecting-suspicious-powershell-execution, detecting-t1003-credential-dumping-with-edr, detecting-t1055-process-injection-with-sysmon, detecting-t1548-abuse-elevation-control-mechanism, detecting-wmi-persistence, evaluating-threat-intelligence-platforms, generating-threat-intelligence-reports, hunting-advanced-persistent-threats, hunting-credential-stuffing-attacks, hunting-evtx-with-chainsaw, hunting-for-anomalous-powershell-execution, hunting-for-beaconing-with-frequency-analysis, hunting-for-command-and-control-beaconing, hunting-for-data-exfiltration-indicators, hunting-for-data-staging-before-exfiltration, hunting-for-dcom-lateral-movement, hunting-for-defense-evasion-via-timestomping, hunting-for-dns-based-persistence, hunting-for-dns-tunneling-with-zeek, hunting-for-lateral-movement-via-wmi, hunting-for-living-off-the-cloud-techniques, hunting-for-living-off-the-land-binaries, hunting-for-lolbins-execution-in-endpoint-logs, hunting-for-ntlm-relay-attacks, hunting-for-persistence-mechanisms-in-windows, hunting-for-persistence-via-wmi-subscriptions, hunting-for-process-injection-techniques, hunting-for-registry-persistence-mechanisms, hunting-for-registry-run-key-persistence, hunting-for-scheduled-task-persistence, hunting-for-shadow-copy-deletion, hunting-for-spearphishing-indicators, hunting-for-startup-folder-persistence, hunting-for-supply-chain-compromise, hunting-for-suspicious-scheduled-tasks, hunting-for-t1098-account-manipulation, hunting-for-unusual-network-connections, hunting-for-unusual-service-installations, hunting-for-webshell-activity, hunting-saas-sso-token-abuse, implementing-alert-fatigue-reduction, implementing-canary-tokens-for-network-intrusion, implementing-deception-based-detection-with-canarytoken, implementing-diamond-model-analysis, implementing-ebpf-security-monitoring, implementing-endpoint-detection-with-wazuh, implementing-honeytokens-for-breach-detection, implementing-log-forwarding-with-fluentd, implementing-log-integrity-with-blockchain, implementing-mitre-attack-coverage-mapping, implementing-network-deception-with-honeypots, implementing-security-chaos-engineering, implementing-security-information-sharing-with-stix2, implementing-security-monitoring-with-datadog, implementing-siem-correlation-rules-for-apt, implementing-siem-use-case-tuning, implementing-siem-use-cases-for-detection, implementing-soar-automation-with-phantom, implementing-soar-playbook-for-phishing, implementing-soar-playbook-with-palo-alto-xsoar, implementing-stix-taxii-feed-integration, implementing-syslog-centralization-with-rsyslog, implementing-taxii-server-with-opentaxii, implementing-threat-intelligence-lifecycle-management, implementing-threat-modeling-with-mitre-attack, investigating-insider-threat-indicators, managing-intelligence-lifecycle, mapping-mitre-attack-techniques, modeling-threats-with-opencti, monitoring-darkweb-sources, operationalizing-misp-threat-feeds, performing-alert-triage-with-elastic-siem, performing-brand-monitoring-for-impersonation, performing-dark-web-monitoring-for-threats, performing-deception-technology-deployment, performing-dns-tunneling-detection, performing-false-positive-reduction-in-siem, performing-indicator-lifecycle-management, performing-ioc-enrichment-automation, performing-ip-reputation-analysis-with-shodan, performing-lateral-movement-detection, performing-log-source-onboarding-in-siem, performing-paste-site-monitoring-for-credentials, performing-soc-tabletop-exercise, performing-threat-hunting-with-elastic-siem, performing-threat-intelligence-sharing-with-misp, performing-threat-landscape-assessment-for-sector, performing-user-behavior-analytics, processing-stix-taxii-feeds, profiling-threat-actor-groups, tracking-threat-actor-infrastructure, triaging-security-alerts-in-splunk

### C5 enterprise identity (AD/Entra/Okta/PAM/IGA) (28)

auditing-entra-id-with-aadinternals, building-identity-federation-with-saml-azure-ad, building-identity-governance-lifecycle-process, building-role-mining-for-rbac-optimization, configuring-active-directory-tiered-model, configuring-ldap-security-hardening, configuring-multi-factor-authentication-with-duo, implementing-azure-ad-privileged-identity-management, implementing-conditional-access-policies-azure-ad, implementing-delinea-secret-server-for-pam, implementing-google-workspace-admin-security, implementing-google-workspace-sso-configuration, implementing-identity-governance-with-sailpoint, implementing-just-in-time-access-provisioning, implementing-pam-for-database-access, implementing-passwordless-auth-with-microsoft-entra, implementing-privileged-access-management-with-cyberark, implementing-privileged-access-workstation, implementing-privileged-session-monitoring, implementing-scim-provisioning-with-okta, implementing-zero-standing-privilege-with-cyberark, performing-access-recertification-with-saviynt, performing-access-review-and-certification, performing-entitlement-review-with-sailpoint-iiq, performing-privileged-account-access-review, performing-privileged-account-discovery, performing-service-account-audit, performing-service-account-credential-rotation

### C6 network / endpoint / zero-trust products / firmware (59)

auditing-uefi-firmware-with-chipsec, configuring-aws-verified-access-for-ztna, configuring-certificate-authority-with-openssl, configuring-host-based-intrusion-detection, configuring-identity-aware-proxy-with-google-iap, configuring-microsegmentation-for-zero-trust, configuring-network-segmentation-with-vlans, configuring-pfsense-firewall-rules, configuring-snort-ids-for-intrusion-detection, configuring-suricata-for-network-monitoring, configuring-windows-defender-advanced-settings, configuring-windows-event-logging-for-detection, configuring-zscaler-private-access-for-ztna, deploying-cloudflare-access-for-zero-trust, deploying-edr-agent-with-crowdstrike, deploying-osquery-for-endpoint-monitoring, deploying-palo-alto-prisma-access-zero-trust, deploying-software-defined-perimeter, deploying-tailscale-for-zero-trust-vpn, hardening-linux-endpoint-with-cis-benchmark, hardening-windows-endpoint-with-cis-benchmark, implementing-application-whitelisting-with-applocker, implementing-beyondcorp-zero-trust-access-model, implementing-bgp-security-with-rpki, implementing-browser-isolation-for-zero-trust, implementing-cisa-zero-trust-maturity-model, implementing-ddos-mitigation-with-cloudflare, implementing-device-posture-assessment-in-zero-trust, implementing-disk-encryption-with-bitlocker, implementing-endpoint-dlp-controls, implementing-file-integrity-monitoring-with-aide, implementing-identity-verification-for-zero-trust, implementing-memory-protection-with-dep-aslr, implementing-microsegmentation-with-guardicore, implementing-network-access-control, implementing-network-access-control-with-cisco-ise, implementing-network-intrusion-prevention-with-suricata, implementing-network-segmentation-with-firewall-zones, implementing-network-traffic-analysis-with-arkime, implementing-network-traffic-baselining, implementing-next-generation-firewall-with-palo-alto, implementing-usb-device-control-policy, implementing-zero-trust-dns-with-nextdns, implementing-zero-trust-for-saas-applications, implementing-zero-trust-network-access-with-zscaler, implementing-zero-trust-with-beyondcorp, implementing-zero-trust-with-hashicorp-boundary, performing-bluetooth-security-assessment, performing-dns-enumeration-and-zone-transfer, performing-endpoint-vulnerability-remediation, performing-firmware-extraction-with-binwalk, performing-hardware-security-module-integration, performing-network-traffic-analysis-with-tshark, performing-network-traffic-analysis-with-zeek, performing-packet-injection-attack, performing-ssl-certificate-lifecycle-management, performing-ssl-tls-inspection-configuration, performing-wireless-security-assessment-with-kismet, validating-tpm-measured-boot-attestation

### C7 OT / ICS (28)

detecting-anomalies-in-industrial-control-systems, detecting-attacks-on-historian-servers, detecting-attacks-on-scada-systems, detecting-dnp3-protocol-anomalies, detecting-modbus-command-injection-attacks, detecting-modbus-protocol-anomalies, detecting-stuxnet-style-attacks, implementing-conduit-security-for-ot-remote-access, implementing-dragos-platform-for-ot-monitoring, implementing-ics-firewall-with-tofino, implementing-iec-62443-security-zones, implementing-nerc-cip-compliance-controls, implementing-network-segmentation-for-ot, implementing-ot-network-traffic-analysis-with-nozomi, implementing-patch-management-for-ot-systems, implementing-purdue-model-network-segmentation, monitoring-scada-modbus-traffic-anomalies, performing-ics-asset-discovery-with-claroty, performing-oil-gas-cybersecurity-assessment, performing-ot-network-security-assessment, performing-ot-vulnerability-assessment-with-claroty, performing-ot-vulnerability-scanning-safely, performing-plc-firmware-security-analysis, performing-power-grid-cybersecurity-assessment, performing-s7comm-protocol-security-analysis, performing-scada-hmi-security-assessment, securing-historian-server-in-ot-environment, securing-remote-access-to-ot-environment

### C8 phishing / email / social engineering (14)

analyzing-malicious-url-with-urlscan, building-phishing-reporting-button-workflow, detecting-business-email-compromise, detecting-business-email-compromise-with-ai, detecting-deepfake-audio-in-vishing-attacks, detecting-qr-code-phishing-with-email-security, detecting-spearphishing-with-email-gateway, implementing-anti-phishing-training-program, implementing-dmarc-dkim-spf-email-security, implementing-google-workspace-phishing-protection, implementing-mimecast-targeted-attack-protection, implementing-proofpoint-email-security-gateway, performing-adversary-in-the-middle-phishing-detection, performing-dmarc-policy-enforcement-rollout

### C9 compliance / GRC / privacy / vuln-management programs (30)

achieving-cmmc-level-2-compliance, building-patch-tuesday-response-process, building-vulnerability-aging-and-sla-tracking, building-vulnerability-dashboard-with-defectdojo, building-vulnerability-exception-tracking-system, conducting-cyber-risk-assessment-with-nist-800-30, executing-nist-rmf-authorization-to-operate, implementing-attack-path-analysis-with-xm-cyber, implementing-continuous-security-validation-with-bas, implementing-data-loss-prevention-with-microsoft-purview, implementing-gdpr-data-protection-controls, implementing-gdpr-data-subject-access-request, implementing-hipaa-security-rule-safeguards, implementing-iso-27001-information-security-management, implementing-patch-management-workflow, implementing-pci-dss-compliance-controls, implementing-rapid7-insightvm-for-scanning, implementing-vulnerability-management-with-greenbone, implementing-vulnerability-remediation-sla, implementing-vulnerability-sla-breach-alerting, managing-third-party-vendor-risk, performing-active-directory-vulnerability-assessment, performing-agentless-vulnerability-scanning, performing-asset-criticality-scoring-for-vulns, performing-authenticated-scan-with-openvas, performing-authenticated-vulnerability-scan, performing-nist-csf-maturity-assessment, performing-privacy-impact-assessment, performing-web-application-scanning-with-nikto, scanning-infrastructure-with-nessus

### C10 cloud account ops (CSPM, detection, IR, product setup) (17)

auditing-azure-active-directory-configuration, building-cloud-siem-with-sentinel, implementing-aws-config-rules-for-compliance, implementing-aws-macie-for-data-classification, implementing-aws-security-hub, implementing-aws-security-hub-compliance, implementing-azure-defender-for-cloud, implementing-cloud-dlp-for-data-protection, implementing-cloud-trail-log-analysis, implementing-cloud-workload-protection, implementing-zero-trust-in-cloud, implementing-zero-trust-network-access, managing-cloud-identity-with-okta, performing-cloud-asset-inventory-with-cartography, performing-cloud-native-threat-hunting-with-aws-detective, performing-gcp-security-assessment-with-forseti, securing-azure-with-microsoft-defender

### C11 container runtime detection / forensics (1)

implementing-runtime-security-with-tetragon

### C12 mobile (no mobile in scope) (5)

implementing-mobile-application-management, intercepting-mobile-traffic-with-burpsuite, performing-dynamic-analysis-of-android-app, performing-ios-app-security-assessment, performing-mobile-app-certificate-pinning-bypass

### C13 web/API detection, WAF ops, product-specific (3)

implementing-api-threat-protection-with-apigee, implementing-runtime-application-self-protection, implementing-web-application-logging-with-modsecurity
