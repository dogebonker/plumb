# B. Masriyan/Claude-Code-CyberSecurity-Skill evaluation for factory-security (S11)

Evaluated 2026-10-10 at commit `42e150160396a2e0e9e9ef7caf07bcefa2731212` (HEAD of `main`).
Base URL for evidence: `https://github.com/Masriyan/Claude-Code-CyberSecurity-Skill/blob/42e1501/<path>`.
Method: `gh api` metadata, tree and commits; raw text files downloaded to `scratchpad/research/masriyan-src/` (nothing installed or executed from the repo). One local check used my own Python snippet, not repo code.

## Verdict (short)

Do not pin or vendor this repository. Take a handful of ideas (V1 to V5 below) into factory-security's own rules. It is a 22-skill generalist security-practitioner pack (pentest, SOC, DFIR, malware, OT, GRC). Only 5 skills touch our scope, and those 5 are black-box or checklist oriented, with no per-language source review for TypeScript/React/Next.js, Rust, Go or Python, and nothing on money-moving or web3 code. Where it overlaps mukul975, mukul975 is deeper on most topics. Masriyan wins on crypto code review and on compact one-page overviews (LLM Top 10 lens, cloud attack-path framing).

## 1. Repository facts

| Item | Value | Evidence |
|---|---|---|
| License | MIT (Copyright 2026 Riyan Pratama). License churn: MIT, then AGPLv3 on 2026-06-15, back to MIT on 2026-06-23 | `LICENSE`, commits `Change license from MIT to AGPLv3` (06-15) and `Change license from AGPLv3 to MIT` (06-23) |
| Stars / forks / watchers | 471 / 88 / 7 | `gh api repos/Masriyan/Claude-Code-CyberSecurity-Skill` |
| Created / last push | 2026-02-27 / 2026-09-07 | same |
| Commits | 39 total. Bursty: Feb 27 (initial), May 28-30 (rewrite), Jun 23 (v3.0), Jul 17-18 (3 outside bug-fix PRs), Aug 30 (skill 20 from a contributor), Sep 7 (v3.1). Most maintainer commits are "Add files via upload" (web-UI uploads, no granular history) | `gh api .../commits` |
| Contributors | Masriyan 32, DrNOFX97 4, farhan6667 3 | `gh api .../contributors` |
| Issues / PRs | 1 open PR (#13, 2026-09-30, "Register skills 21 and 22 in plugin manifest", unmerged). 10 closed PRs, 7 of them bug fixes to scripts. No issues filed | `gh api .../issues?state=all` |
| Releases / tags | None. Versions exist only in `CHANGELOG.md` and frontmatter (3.1.0) | `gh api .../releases`, `.../tags` |
| Size | 6.1 MB (mostly PNG banners); 198 tree entries; 22 `SKILL.md` (162-756 lines each), ~33 Python scripts, 17 committed `.pyc` files | tree |
| CI / tests | None. CLAUDE.md states "no test suite, and no CI pipeline"; verification is `py_compile` + `--help` | `CLAUDE.md` |
| Install | Many skills, not one. (a) `cp -r skills/* ~/.claude/skills/` or symlink (INSTALL.md lines 81-107); (b) Claude Code plugin marketplace `.claude-plugin/marketplace.json`, one plugin `cybersecurity` listing skills 01-20 only (21 and 22 missing, PR #13 open) | `INSTALL.md`, `.claude-plugin/marketplace.json` |

Hygiene red flags:
- **Stale committed bytecode.** 17 `__pycache__/*.cpython-314.pyc` files committed in February and never updated. Example: `skills/02-vulnerability-scanner/scripts/__pycache__/dependency_auditor.cpython-314.pyc` lacks the `MODERATE` severity fix present in the `.py` (0 vs 2 occurrences of `MODERATE`). Binary code that does not match its source should not be vendored.
- **Manifest drift.** README and CLAUDE.md claim 22 skills and say "the marketplace manifest lists all 22"; the manifest lists 20.
- **Skill frontmatter is not Agent Skills spec-conformant.** `name` values are title-case prose ("AI & LLM Security", "Cloud Security & Container Hardening") that do not match the directory names (`16-ai-llm-security`). `description` lacks "use when" trigger phrasing; triggers sit in the body ("Activation Triggers"), which the router cannot see before loading.

## 2. Content

### Skill inventory

| # | Skill | Covers | In S11 scope? |
|---|---|---|---|
| 01 | recon-osint | subdomain enum, DNS, fingerprinting, dorking | No (offensive recon) |
| 02 | vulnerability-scanner | dependency CVE audit, nginx/sshd/Dockerfile/K8s checklists, CVSS, Nmap NSE | Partly (dependency triage, Docker/K8s checklists) |
| 03 | exploit-development | PoC templates, payload generator, shellcode | No |
| 04 | reverse-engineering | binary triage, disassembly, firmware | No |
| 05 | malware-analysis | static/dynamic analysis, YARA | No |
| 06 | threat-hunting | IOCs, ATT&CK, Sigma/SIEM queries | No |
| 07 | incident-response | PICERL, evidence collection, timelines | No |
| 08 | network-security | PCAP, Suricata/Snort, firewall audit | No |
| 09 | web-security | OWASP Top 10 (2021), SQLi/XSS/SSRF/SSTI payloads, API checklist, JWT, OAuth, headers, CORS | Partly (black-box) |
| 10 | cloud-security | AWS/Azure CLI audits, Dockerfile, K8s, Terraform examples, compliance mapping | Partly (IaC, containers) |
| 11 | csoc-automation | alert triage, playbooks, shift reports | No |
| 12 | log-analysis | Splunk/KQL/EQL, Sigma, anomaly detection | No |
| 13 | crypto-analysis | TLS audit, cipher ratings, hash ID, crypto code review (Python), key sizes, PQC | Partly (crypto code review) |
| 14 | red-team-ops | engagement planning, C2, AD attacks | No |
| 15 | blue-team-defense | Linux/Windows hardening, detection engineering | No (host hardening) |
| 16 | ai-llm-security | OWASP LLM Top 10 (2025), prompt injection, RAG, agent/MCP tools, model supply chain | Yes |
| 17 | mobile-security | MASVS/MASTG, APK triage, Frida | No (mobile excluded unless S11 adds it) |
| 18 | ot-ics-security | Purdue, Modbus/DNP3, IEC 62443 | No |
| 19 | grc-compliance | risk register, NIST CSF 2.0/ISO/SOC 2 crosswalk | No |
| 20 | supply-chain-security | SBOM, typosquatting, dependency confusion, malicious package indicators, GitHub Actions checklist, SLSA/Sigstore | Yes |
| 21 | threat-intelligence | CTI cycle, STIX/MISP | No |
| 22 | purple-team | adversary emulation, detection coverage | No |

Coverage gaps for our scope (grep across all SKILL.md, evidence in section "Method"): zero mentions of Next.js, React, `dangerouslySetInnerHTML`, server actions, Rust `unsafe`, Go-specific review, Solidity/web3, idempotency, race conditions/TOCTOU, Stripe/webhook signature verification, Semgrep, Gitleaks/TruffleHog, zizmor/actionlint, `govulncheck`/`cargo audit`/`pip-audit`/`npm audit`, STRIDE or a code-level threat model. "Threat model" appears only in skills 16, 18, 21.

### Quality of in-scope skills (read in full)

**09 web-security** (`skills/09-web-security/SKILL.md`, 458 lines). Pentest playbook: payload libraries for SQLi, XSS filter bypass, command injection, SSRF filter bypass, SSTI to RCE, JWT attacks with `jwt_tool` (flags `-X a`, `-X k -pk`, `-C -d` are correct). Checklists for API (BOLA, mass assignment, function-level authz), session, OAuth (state, redirect_uri, PKCE, code reuse) and CORS are accurate and usable as review questions. Weaknesses: targets OWASP Top 10 **2021** (the 2025 edition, with A03 Software Supply Chain Failures and A10 Mishandling of Exceptional Conditions, is not referenced); no source-to-sink guidance, no framework specifics; "Step 3: Extraction" teaches `UNION SELECT username,password FROM users`, which is more than a proof needs. The "v3.0 Enhancements" appendix lists API Top 10 2023, request smuggling, prototype pollution as one-liners only.

**02 vulnerability-scanner** (320 lines). Useful: the v3.0 rule "every finding row carries `CVSS | EPSS | KEV(Y/N) | Reachable(Y/N/Unknown) | Fix`" and "a KEV or high-EPSS medium outranks a high-CVSS CVE with no exploitation signal". Checklists for Dockerfile and K8s are standard. Outdated items: sshd `Protocol 2` (option removed from OpenSSH since 7.4), "consider non-default port". Report template says CVSS v3.1 while the appendix says use 4.0, so the file contradicts itself.

**10 cloud-security** (473 lines). Broad AWS/Azure CLI checklists, Dockerfile before/after, secure Pod spec, Terraform insecure/secure examples, compliance mapping table. Useful framing in the appendix: "report each finding as misconfig, reachable identity/data, blast radius" and identity-first escalation paths (`iam:PassRole`, OIDC trust from CI). Inaccuracies: recommends `tfsec` (deprecated, folded into Trivy by Aqua); password policy "rotation ≤90 days" (contradicts NIST SP 800-63B, which advises against forced periodic rotation); runs `aquasec/kube-bench:latest` while its own checklist says never use `latest`; secure Dockerfile example adds a `curl` HEALTHCHECK to a runtime stage that never installs curl; "all images from private registry (not Docker Hub public)" is overreach. Mostly live-account auditing, little IaC source review.

**13 crypto-analysis** (371 lines). The best in-scope file. Concrete Python anti-patterns (ECB, static IV, MD5 passwords, `verify=False`, `_create_unverified_context`) with secure AES-GCM and Argon2id replacements, a code-review checklist, key-size table, PQC (FIPS 203/204/205, `X25519MLKEM768`). Inaccuracies: PBKDF2 iteration minimums (600k SHA-256 etc.) are attributed to "NIST 2023" but come from the OWASP Password Storage Cheat Sheet; the hash table elsewhere says PBKDF2 is "good if iterations ≥ 260,000", contradicting 600k; recommends OCSP stapling with no note that major CAs are ending OCSP. Python only; no Go `crypto/*`, Rust `ring`/RustCrypto, or Node `crypto` patterns.

**16 ai-llm-security** (192 lines). Compact and current: OWASP LLM Top 10 **2025** table with "what to look for", RAG access control at retrieval (filter by caller permissions), agent as confused deputy, tool args as untrusted, HITL on irreversible actions (payments named), MCP hardening, memory poisoning, "never pass LLM output to eval/SQL/shell/innerHTML". Good as a review lens. Script `model_supply_chain.py` is flawed: it reads `GLOBAL`/`STACK_GLOBAL` args, but `STACK_GLOBAL` carries no inline argument, so dangerous imports in protocol 4+ pickles are never named (verified locally: protocol 5 pickle of `os.system` yields `('STACK_GLOBAL', None)`). It also marks any pickle with `REDUCE` as DANGEROUS, which flags nearly every benign PyTorch checkpoint. `picklescan`/`modelscan`/`fickling` are better.

**20 supply-chain-security** (200 lines, contributed by DrNOFX97). Good malicious-package indicators list (lifecycle scripts reading `NPM_TOKEN`, obfuscation, raw-IP egress, patch bump that adds install scripts), dependency confusion via scoping, SLSA L1-L3 and keyless cosign. GitHub Actions checklist covers SHA pinning, top-level `permissions:`, `pull_request_target` plus PR-head checkout, self-hosted runners on public repos. Missing: expression/script injection (`${{ github.event.* }}` inside `run:`), `persist-credentials`, cache poisoning, `workflow_run` chains, OIDC subject-claim scoping, secrets inheritance in reusable workflows. Script `supply_chain_auditor.py` flags "no top-level permissions" even when every job sets `permissions:`, and skips job-level reusable workflow `uses:`. zizmor covers all of this better.

### Dangerous advice and odd instructions

- **SECURITY.md tells users to add a Windows Defender exclusion for the whole repository directory** (`Add-MpPreference -ExclusionPath ...`, elevated PowerShell) and to "whitelist the directory" in any AV. Broad AV exclusions for a third-party repo that ships stale binaries is the wrong default. Not relevant to macOS, but it disqualifies vendoring as-is.
- Offensive payload content (03 `payload_generator.py`, 09 bypass libraries, 14 C2) sits in the same plugin. Installing the marketplace plugin loads all of it into every session's skill list.
- Broad activation triggers: installing all 22 globally (the recommended path) means skills like web-security trigger on any "CORS" or "JWT" question. This is the opposite of the S11 router design.
- No prompt injection found. Checks: no hidden Unicode (zero-width, bidi, tag characters) in any `.md` or `.json`; zero-width characters appear only in `prompt_injection_tester.py` as deliberate test payloads; no HTML comments in Markdown; no "ignore previous", "without asking", `curl | sh` style text. Repository `CLAUDE.md` is contributor guidance only (do not remove authorization gates, do not "fix" payload templates) and would load only if the repo itself were opened in Claude Code.
- Scripts that make network calls: `dependency_auditor.py` (OSV API, sends package names), `supply_chain_auditor.py --check-registry` (registries), `cti_processor.py --enrich` (rdap.org), `prompt_injection_tester.py` (target URL), `owasp_scanner.py`/`api_security_tester.py` (active scanning of a target). None run by default from SKILL.md, but each needs to be known before any reuse.

## 3. Comparison with mukul975/Anthropic-Cybersecurity-Skills (local `~/.agents/skills`)

| Topic | Masriyan | mukul975 | Better | Evidence |
|---|---|---|---|---|
| GitHub Actions | 7-item checklist in skill 20; no script injection | `securing-github-actions-workflows` (263 lines): SHA pinning + Dependabot, `permissions: {}` then per-job grants, script injection via `env:` indirection, safe `pull_request_target` pattern, environments, CODEOWNERS on `.github/workflows/`, org settings | mukul975 | Masriyan misses expression injection entirely. Neither names zizmor, cache poisoning or `persist-credentials` |
| Dependency confusion / typosquatting | One subsection each, heuristic script | `detecting-dependency-confusion` (224 lines): `confused`, OWASP dep-scan, claimability triage, scope-to-registry pinning for npm/PyPI/Maven, placeholder registration, CI wiring; plus `detecting-typosquatting-packages-in-npm-pypi` | mukul975 | Depth per sub-topic |
| Malicious package indicators, SLSA/provenance | Concise, accurate list | Spread across `analyzing-supply-chain-malware-artifacts`, `implementing-supply-chain-security-with-in-toto` | Masriyan for a one-page lens | Masriyan skill 20 sections 3 and 5 |
| LLM/agent threat model (code review lens) | OWASP LLM 2025 table + agent/RAG/MCP checklist on one page | Per-topic deep skills: `securing-agentic-ai-tool-invocation` (allowlist + JSON schema + scoped STS creds + HITL code), `auditing-mcp-servers-for-tool-poisoning` (tool hash pinning, rug-pull), `testing-prompt-injection-in-rag-pipelines` (garak, promptfoo, PyRIT) | Split: Masriyan for the lens, mukul975 for controls and testing | |
| Web/API (OWASP) | One file, Top 10 2021, payload heavy | `testing-api-security-with-owasp-top-10` (API Top 10 2023 step per category), plus per-vuln skills (IDOR, mass assignment, SSRF, race conditions) | mukul975 for API; both black-box | Neither gives source-sink review for TS/Next.js/Go/Rust/Python |
| JWT | ~10 lines | `testing-jwt-token-security` (354 lines): alg none, RS/HS confusion, secret brute force, claim and `kid` injection, lifetime and revocation | mukul975 | |
| IaC / containers / K8s | Broad checklists, attack-path framing, Terraform examples | `auditing-terraform-infrastructure-for-security` and `implementing-infrastructure-as-code-security-scanning`: Checkov/tfsec/Terrascan/OPA workflows | Roughly even; Masriyan has more "what is wrong" content, mukul975 more "how to run the tool" | Both still recommend deprecated tfsec |
| Crypto code review | Concrete anti-patterns and fixes, PQC, key sizes | `performing-cryptographic-audit-of-application` (111 lines): generic objectives and a category table, no code patterns in SKILL.md | Masriyan | Despite the PBKDF2 attribution error |
| Dependency CVE prioritization | CVSS x EPSS x KEV x reachability row rule | `performing-sca-dependency-scanning-with-snyk` (Snyk-centric) | Masriyan for the rule | |
| Money-moving, web3, React/Next.js, Rust, Go | Nothing | `auditing-foundry-smart-contract-security`, `analyzing-ethereum-smart-contract-vulnerabilities`, `exploiting-race-condition-vulnerabilities`; no framework-specific Next.js/Rust/Go review either | mukul975 (only one with any content) | The kit's own `fin-*`, `rust-skills`, `vercel-react-best-practices` cover more than either |

Structural difference: mukul975 skills are narrow (one technique each, spec-shaped frontmatter with `name` matching the folder, Apache-2.0, `nist_csf`/`mitre_attack` tags usable by a routing index). Masriyan skills are wide (one domain each, 160-760 lines), which makes them hard to route selectively and expensive to load whole.

## 4. Verdict per part

| Code | Part | Decision | Reason |
|---|---|---|---|
| V1 | Skill 16 OWASP LLM Top 10 (2025) table and agent/RAG/MCP checklist | Adapt as ideas into factory-security's LLM-feature lens | Best compact review lens of either source; rewrite in our words with source-code questions (where is the prompt built, which tools, whose identity) |
| V2 | Skill 02 finding row rule `CVSS / EPSS / KEV / Reachable / Fix` and KEV-first ordering | Adapt as idea for the scanner-results triage step | Simple, correct prioritization rule; fits "scanners first" |
| V3 | Skill 13 crypto anti-pattern list and checklist | Adapt as ideas, extend to Go/Rust/Node, fix PBKDF2 attribution (OWASP, not NIST) | Strongest crypto code-review content in either source |
| V4 | Skill 20 malicious-package indicators and SLSA L1-L3 summary | Adapt as ideas | Accurate and short. Use mukul975 `securing-github-actions-workflows` plus zizmor for the GitHub Actions lens instead of skill 20's checklist |
| V5 | Skill 10 "misconfig, reachable identity/data, blast radius" finding framing | Adapt as idea for IaC findings | Matches "findings proven" and the threat-model step |
| V6 | Any SKILL.md vendored or pinned as-is | Reject | Spec-nonconformant frontmatter, wide scope per file, outdated items (Top 10 2021, tfsec, 90-day rotation, sshd Protocol 2), offensive content in the same plugin, no releases or tags, stale `.pyc`, web-UI upload history, AV-exclusion advice |
| V7 | Python scripts (`supply_chain_auditor.py`, `model_supply_chain.py`, `dependency_auditor.py`, `iac_scanner.py`, `config_auditor.py`) | Reject | No tests or CI; confirmed defects (STACK_GLOBAL blindness, REDUCE false positives, job-level permissions false positives); S11 already plans pinned Trivy, Semgrep, Gitleaks, OSV-Scanner and native audit tools, plus zizmor/picklescan cover the rest |
| V8 | Marketplace plugin install | Reject | Loads all 22 skills including exploit and red-team content; manifest out of sync |
| V9 | Skills 01, 03-08, 11, 12, 14, 15, 17-19, 21, 22 | Reject as out of scope | Offensive, SOC, DFIR, OT, GRC, mobile |

If the S11 design still wants something referenced by URL, cite commit `42e1501` and the specific file, and record the license as MIT at that commit, given the June AGPL flip.

## Method notes

- Metadata: `gh api repos/Masriyan/Claude-Code-CyberSecurity-Skill`, `/contributors`, `/commits?per_page=100`, `/commits/<sha>` (file lists), `/issues?state=all`, `/releases`, `/tags`, `/git/trees/HEAD?recursive=1` (tree saved to `masriyan-tree.txt`).
- Content: all `.md`, `.py`, `.json`, `.txt` and `.pyc` blobs fetched from `raw.githubusercontent.com/.../42e1501.../` into `masriyan-src/` (read only, nothing executed). In-scope SKILL.md files (02, 09, 10, 13, 16, 20) read in full; the rest by frontmatter and grep.
- Injection scan: grep for zero-width/bidi/tag Unicode, HTML comments, and instruction-style phrases across `.md`/`.py`/`.json`.
- STACK_GLOBAL check: own snippet `pickle.dumps(obj_reducing_to_os.system, protocol=5)` then `pickletools.genops`, run with `python3 -I` from the scratchpad.
- mukul975 comparison: local `~/.agents/skills` (993 entries including non-mukul skills), files read: `securing-github-actions-workflows`, `performing-cryptographic-audit-of-application`, `securing-agentic-ai-tool-invocation` (partial); section headings and keyword counts for `testing-api-security-with-owasp-top-10`, `testing-jwt-token-security`, `auditing-terraform-infrastructure-for-security`, `implementing-infrastructure-as-code-security-scanning`, `detecting-dependency-confusion`, `testing-prompt-injection-in-rag-pipelines`, `auditing-mcp-servers-for-tool-poisoning`, `detecting-supply-chain-attacks-in-ci-cd`.
- Not verified: OWASP Top 10:2025 category names are from my knowledge (released November 2025), not fetched in this session. The claim that major CAs are ending OCSP is from knowledge, not fetched.
