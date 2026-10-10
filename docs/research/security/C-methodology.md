# C. Methodology core for `factory-security` (S11)

Researched 2026-10-10. All third-party content was read as data. Token figures are bytes/4, rounded.

## Verdict

- **Core methodology: `cloudflare/security-audit-skill`** (MIT, active, installed copy equals upstream). Take its evidence contract, three verdicts, `report-schema.json`, both validators and the attack-class companions as the routing units. Do not run its full six-phase orchestration by default. It is the heaviest part, and its sandbox/promotion rules need infrastructure the factory must supply.
- **Component depth: a few small, section-addressable files**, at most one per agent next to the Cloudflare core: OpenAI `security-best-practices` per-framework specs (Next.js, React, Express, Go, FastAPI/Django/Flask), Trail of Bits `insecure-defaults` category files, ToB `sharp-edges` language files, ToB `variant-analysis` after a confirmed finding, ToB `fp-check` bug-class file for verifiers, ToB `agentic-actions-auditor` or Sentry `gha-security-review` for GitHub Actions, and the user's existing `fin-*` packs for money.
- **Scanners do the mechanical layer** (Trivy, Semgrep, Gitleaks, OSV-Scanner, zizmor, govulncheck, cargo audit, pip-audit, npm audit). Their hits are *candidates* that enter Cloudflare's verifier. They are never reported raw.
- **The factory adds:** the threat model built from `.factory/system/`, the routing index, scanner adapters with SARIF-to-candidate conversion, a sandbox runner, profile mapping to the three plug-in points, and turning confirmed findings into small-track slices and `SYS-C` rows.

---

## 1. Cloudflare `security-audit` (core candidate)

**Source:** https://github.com/cloudflare/security-audit-skill. MIT. ~27.7k stars. Created 2026-06-18. Last commit 2026-09-14 (`c1c8a8c`, "Clarify guidance and full audit modes"). Not archived. The installed copy at `~/.claude/skills/security-audit` (symlink to `~/.agents/skills/security-audit`, installed via skills CLI 2026-10-04) has tree SHA `ccbc33ed119b…`, identical to upstream `main` (per-file blob hashes match). The README says it seeded Cloudflare's vulnerability harness (https://blog.cloudflare.com/build-your-own-vulnerability-harness).

### 1.1 Modes and workflow

- **Guidance mode (default).** Answers questions, does focused reviews and triage. It uses only the relevant parts and writes no artifacts. This mode fits the factory's "review lens on a slice" plug-in point.
- **Full audit mode.** Runs only on an explicit audit/pen-test request, a request for a full review, or a request for report artifacts. All six phases are mandatory and end in exactly two terminal states: complete with both validators passing, or `run_status: incomplete` with a reason.
- **Profiles:** `quick` (one hunter wave, one critic, one verifier per candidate), `standard`, `deep`. Scoped runs cover paths, a subsystem, a companion domain, or a diff between refs. Profiles change breadth, never the evidence bar. There is an optional strict agent-invocation budget with mandatory reserves for critics and verifiers.

| Phase | What happens | Output |
| --- | --- | --- |
| 1 Recon | 4 parallel read-only agents: product/stack/local ops, principals and controls, entry surfaces→sinks, local execution and deployment visibility. Read prior runs. | `run-metadata.json`, `architecture.md` (≤1,000 words), `coverage-ledger.json` |
| 2 Hunting waves | One hunter per ledger unit (surface × boundary × subsystem × attack class). The prompt carries `architecture.md` verbatim plus the *verbatim* selected blocks. A coverage critic runs after each wave, and a final-clean critic runs in standard/deep. | Structured JSON per unit: covered / candidate / blocked, plus `uncovered` |
| 3 Candidate validation | A fresh verifier per candidate tries to refute it and must re-run any decisive check itself. | confirmed / needs_validation / rejected |
| 4 Structured output | `findings.json` sorted by fingerprint. `validate-findings.cjs` and `validate-coverage-ledger.cjs` must pass. | `findings.json` |
| 5 Record verification | A fresh verifier per final record. Material replacements go to yet another fresh verifier. | verified / replace |
| 6 Report | Prose derived only from the verified records. | `REPORT.md`, `FINDINGS-DETAIL.md`, `NEEDS-VALIDATION.md` |

Runs are additive. Prior `confirmed` records carry forward only if the relevant source is unchanged, and they are re-verified. Prior `rejected` records suppress only the identical claim. `needs_validation`, `deferred` and `blocked` always become current work.

### 1.2 Evidence and validation standard (matches factory "findings proven")

- **Candidate gate.** Every candidate must name the lower-trust principal, the accepted input, the intended control, the crossed boundary, the affected principal or resource, and a concrete result. A missing best practice, a guessed deployment fact, a generic parser crash or self-impact is not a finding.
- **`confirmed`** needs a complete repository-relative trace (entrypoint → propagation → sink with file:line), evidence, conditions, a *bounded local observed result* in the target's native interface, a remediation (the smallest source fix at the last trusted decision point), severity (likelihood, impact, overall ≤ impact) and confidence. Severity anchors are explicit (critical = unauth RCE, full data store or arbitrary account takeover; high = full defeat of an explicit control, etc.).
- **`needs_validation`** carries no severity, the exact blocker, and a local and/or owner-observed plan. It "is never a parking place for a speculative idea."
- **`rejected`** is kept so later runs do not re-raise the claim.
- **Independence.** The hunter never verifies its own candidate. Phase 5 uses fresh agents again.
- **Execution safety.** Target code runs only in an OS-enforced sandbox: no network, empty allowlisted env, read-only target and toolchain, scratch-only writes, and explicit CPU/memory/process/file/disk/time limits. Without that, it does not execute, and the candidate becomes `needs_validation`. Evidence files leave scratch only via an 11-step, descriptor-based, no-follow "promotion procedure" run by trusted parent code.
- **Anti-patterns list:** checklist deviations as vulns, defense-in-depth advice without a reachable violation, live testing, guessing deployment behavior, self-impact, over-stated parser effects, prose-only results, re-reporting carried findings, severity on `needs_validation`, and writing the report before verification.

### 1.3 Validators (mechanical, zero-dependency Node)

- **`validate-findings.cjs`** (28.8 KB) is an interpreter for the JSON-Schema keyword subset used by `report-schema.json` (oneOf by `verdict`, `additionalProperties:false`, patterns, enums, custom `visibleContent`). It adds semantic checks: unique fingerprints sorted lexicographically, positive line numbers, safe relative paths (also in `remediation.code_changes[].file_name`), trace shape (first `entrypoint`, last `sink`, middle `propagation`), verdict-specific forbidden fields, `observed_result` and `remediation.strategy` required on confirmed, `overall_severity` ≤ `impact.score`, and at least one validation plan on `needs_validation`. Hard limits: 5 MiB input, 1,000 findings, 64 nesting levels, 100 errors reported. It escapes control/format characters in diagnostics, which is safe against hostile strings.
- **`validate-coverage-ledger.cjs`** (33.5 KB) enforces the ledger state table (planned / in_progress / blocked / covered / candidate / deferred / not_applicable / out_of_scope with required-empty or required-nonempty fields). It also enforces canonical `coverage_id` derivation (NFC, RFC 3986 percent-encoding, `::` join), duplicate and semantic-collision rejection, agent ID pattern `^[a-z0-9][a-z0-9_-]{0,63}$` (no Windows device names), artifact paths owned by `agents/<check.agent_id>/artifacts/`, `reviewed_paths` = union of check paths, and the append-only `attempts` archive invariants. Limits: 5 MiB, 10,000 units.
- **Tests:** `node --test validate-findings.test.cjs validate-coverage-ledger.test.cjs` gave **65/65 pass** locally (Node, 0.5 s).
- **Factory fit:** these are exactly "mechanical before model". They should run as Phase-1-style scripts, never as agent reading.

### 1.4 Attack-class coverage

`ATTACK-CLASSES.md` (ordinary blocks, always relevant): Injection (incl. second-order, field-name/header injection), Access control (weaker parallel paths, body-field overrides, authn-without-authz, bulk/export per-item checks), Resource and file handling (traversal, SSRF, deserialization, zip slip, TOCTOU), Cryptography and secrets, Business logic (state machines, races/double-spend, numeric manipulation, time logic, fail-open defaults), Feature abuse/data leakage (export, import, search oracles, enumeration, preview leakage, webhook SSRF), Chained vulnerabilities, Wildcard, Obvious things (secrets, debug endpoints, CORS, cookies, open redirects, unpinned deps).

Each companion has the same shape: `When to use this file`, `Core discipline`, class sections, `Universal moves`, `Validation rules`.

| Companion | Classes (abridged) | Factory component |
| --- | --- | --- |
| WEB-PROTOCOL-AND-AUTH | request smuggling, cache poisoning/deception, host/forwarded trust, header injection, CSRF, session fixation, cookie scope, JWT, OAuth/OIDC, SAML, MFA/step-up, WebAuthn, account linking, recovery, API-key scope, mTLS | web API/SaaS, auth |
| CLIENT-SIDE | DOM XSS, DOM clobbering, prototype pollution gadgets, postMessage, CSWSH, credentialed CORS, service-worker scope/cache, browser storage, XS-Leaks, clickjacking, navigation | React/Next.js frontend |
| SUPPLY-CHAIN-AND-RELEASE | namespace confusion, mutable inputs, codegen provenance, build context, untrusted code in privileged workflow, expression injection, cache/artifact trust mixing, CI identity, build-to-promotion substitution, signing policy, updater, plugins | GitHub Actions, supply chain |
| CLOUD-AND-DEPLOYMENT | workload identity, cross-account roles, metadata trust, management-plane reachability, proxy/mesh bypass, IMDS, container capabilities, admission paths, label trust, config precedence drift, secret exposure, signed URLs, event-source identity, edge/origin mismatch | IaC, containers |
| DATA-ISOLATION-AND-LIFECYCLE | tenant enforcement, key collisions, RLS vs query disagreement, blob links, search/cache ACL drift, logs as readers, aggregate oracles, export/import/restore, migration defaults, soft delete, stale authz, retention | multi-tenant SaaS |
| AI-AND-LLM | indirect injection, context bleed, memory poisoning, role/provenance confusion, tool-argument injection, confused deputy, action-confirmation binding, schema/dispatcher disagreement, unbounded loops, sub-agent/MCP trust, MCP identity, metadata-as-policy, output rendering, context extraction | LLM/agent features |
| PROTOCOLS-RPC-AND-MESSAGING | canonicalization, enum/default confusion, envelope vs body identity, interceptor gaps, peer→principal, per-item stream authz, broker isolation, replay/ordering | gRPC, queues, webhooks |
| RESOURCE-EXHAUSTION-AND-AVAILABILITY | superlinear parsing, decompression, query amplification, unbounded buffering, leaks, detached work, quotas, failure/recovery | APIs, LLM spend |
| MEMORY-SAFETY-AND-BINARY | OOB, integer, unit confusion, uninit, UAF, type confusion, concurrency, FFI/ABI, loaders, kernel | Rust `unsafe`/FFI |
| DESKTOP-MOBILE-AND-LOCAL-IPC | deep links, handoff, webview bridges, IPC, privileged helpers | mostly out of scope |

**Gaps for our scope.** It covers the classes but has no framework-specific facts (Next.js Server Actions, middleware matcher gaps, Django `mark_safe`, Go `html/template` vs `text/template`). It has no scanner integration and no smart-contract or on-chain classes. Money logic appears only as generic business logic (race, numeric). That gap is covered by the `fin-*` packs.

### 1.5 Size per file (token cost if loaded whole)

| File | Bytes | ≈ tokens | Loaded by |
| --- | ---: | ---: | --- |
| SKILL.md | 22,026 | 5.5k | parent only |
| RECONNAISSANCE.md | 15,902 | 4.0k | parent, Phase 1 |
| HUNTING.md | 22,446 | 5.6k | parent, Phase 2. Hunters get only the method, the gate and the result-contract blocks (~1.5k) |
| ATTACK-CLASSES.md | 15,695 | 3.9k | hunters get one block (~0.3-0.6k) |
| VALIDATION-AND-REPORTING.md | 17,843 | 4.5k | parent, Phases 3-6. Verifier prompt block ~1k |
| WEB-PROTOCOL-AND-AUTH.md | 12,300 | 3.1k | companion |
| AI-AND-LLM.md | 10,617 | 2.7k | companion |
| MEMORY-SAFETY-AND-BINARY.md | 10,513 | 2.6k | companion |
| DESKTOP-MOBILE-AND-LOCAL-IPC.md | 8,739 | 2.2k | companion |
| CLIENT-SIDE.md | 8,594 | 2.1k | companion |
| CLOUD-AND-DEPLOYMENT.md | 8,291 | 2.1k | companion |
| DATA-ISOLATION-AND-LIFECYCLE.md | 7,798 | 1.9k | companion |
| PROTOCOLS-RPC-AND-MESSAGING.md | 7,483 | 1.9k | companion |
| RESOURCE-EXHAUSTION-AND-AVAILABILITY.md | 7,476 | 1.9k | companion |
| SUPPLY-CHAIN-AND-RELEASE.md | 7,258 | 1.8k | companion |
| report-schema.json | 14,494 | 3.6k | verifier gets one or two branches (~1.2k) |
| validators (.cjs) + tests | 117,195 | 0 | executed, never read into context |
| **All markdown** | **~177k** | **~44k** | never load all of it |

A typical hunter prompt holds the method and gate (~1.5k), one ordinary block (~0.5k), one companion's Core discipline + 1-3 classes + Universal moves + Validation rules (~1-1.5k), and `architecture.md` (≤1.3k). That is **≈ 4-5k tokens**, which fits a "small loaded rule set".

### 1.6 Selective loading, by component

| Component signal (from threat model / profile) | Ordinary block | Companion blocks |
| --- | --- | --- |
| HTTP routes, sessions, JWT/OAuth, API keys | Access control, Injection | WEB-PROTOCOL-AND-AUTH: classes matching the auth mechanism actually present |
| React/Next.js client, `dangerouslySetInnerHTML`, postMessage, service worker | Injection | CLIENT-SIDE |
| Multi-tenant DB, RLS, exports, caches, search | Access control, Feature abuse | DATA-ISOLATION-AND-LIFECYCLE |
| `.github/workflows`, lockfiles, release scripts | Obvious things | SUPPLY-CHAIN-AND-RELEASE |
| Terraform/K8s/Docker, serverless, IAM | (none or Obvious things) | CLOUD-AND-DEPLOYMENT |
| LLM SDK, tool calling, MCP, RAG, memory | Chained vulnerabilities | AI-AND-LLM |
| Queues, webhooks, gRPC, GraphQL | Injection, Access control | PROTOCOLS-RPC-AND-MESSAGING |
| Upload/parse/regex/LLM spend | Resource and file handling | RESOURCE-EXHAUSTION-AND-AVAILABILITY |
| Rust `unsafe`, FFI, Go `unsafe`/cgo | Resource and file handling | MEMORY-SAFETY-AND-BINARY |
| Money paths (balances, payments, on-chain) | Business logic | none. Use the `fin-*` pack as lens 2 |

The skill's own rule fits the factory: "Do not select a companion file merely because the language or dependency name appears. Select it because reconnaissance found the trust-sensitive boundary." Block references (`FILE.md#Class name`) are stable identifiers already. The routing index can point at them directly.

### 1.7 Where it conflicts with factory principles

- **No scanners.** It is entirely model hunting. The factory's scanner layer must feed it.
- **Heavy orchestration in full mode:** 4 recon agents + N hunters + 2 critics per wave + 1-2 verifiers per candidate. Budget gating and percent-encoded canonical IDs are a lot of ceremony for a solo developer's repo. The factory should default to `quick` or scoped runs and reserve `standard` for on-demand full audits.
- **The sandbox and promotion requirements are strict.** If the factory cannot meet them, every local check becomes `needs_validation` and almost nothing reaches `confirmed`. Claude Code's built-in Bash sandbox restricts network and filesystem but does not set the CPU/memory/process limits the skill requires.
- **Output location.** The default is `~/security-audit-skill/<repo>/run-N`. Inside the target is allowed only when the user selects it and VCS ignores the whole directory. The factory wants `.factory/security/`, so it must be git-ignored. Alternatively, findings could live in the `~/.software-factory` branch mechanism the design already has for hidden state.
- **"The audit describes fixes; it does not modify target source."** This is compatible. The factory turns each confirmed record into its own small-track slice.

---

## 2. Trail of Bits skills

**Source:** https://github.com/trailofbits/skills. **CC-BY-SA-4.0**. ~7.5k stars. Last commit 2026-10-09 (`442fc9d`), very active. A separate curated marketplace exists at https://github.com/trailofbits/skills-curated (CC-BY-SA-4.0, last push 2026-07-14), mostly non-security or offensive (ffuf, ghidra).

**Overall quality:** high. Strong anti-rationalization tables, refute-first verifiers, honest coverage reporting ("a partial scan presented as complete is worse than none"), and tests for prompt corpora. Two structural caveats:
- Many plugins run as **Claude Code `Workflow` tool JavaScript pipelines** with plugin-namespaced subagents: `insecure-defaults`, `variant-analysis`, `static-analysis`, `post-patch-validation`, `audit-context-building`, `spec-to-code-compliance`, `c-review`. They are not portable to "any Agent Skills harness" (DESIGN §12). Their reference corpora *are* portable.
- **CC-BY-SA:** redistributing unmodified copies with attribution is fine. Adapted text must stay CC-BY-SA. Keep ToB packs installed and pinned by hash like the other packs, and do not paste their text into MIT factory skills.

### 2.1 Security-relevant plugins, fit for our scope

| Plugin | What it is | Size (md) | Fit | Use in factory-security |
| --- | --- | ---: | --- | --- |
| `insecure-defaults` | Recon → 6 grep sweeps (fallback secrets, default creds, fail-open switches, weak crypto, permissive access, debug leakage) → Opus refuting verifiers (start at `refuted:true`, 5-step kill chain, "incomplete trace = refuted") → report. Seeds are POSIX ERE, plus patterns derived per stack. | 28.6k total. Category files **~2.1-2.3 KB each (~550 tokens)** with "Report when / Skip when" and vulnerable/secure pairs | **High** | Lens 2 for the "Obvious things" and config hunters. Load the one category file. The workflow itself is Claude-only |
| `sharp-edges` | Footgun and misuse-resistance review: algorithm selection, dangerous defaults (`timeout=0`), primitive vs semantic APIs, config cliffs, silent failures, stringly-typed security. Per-language references. | SKILL 11.8k. `lang-go/rust/python/javascript.md` ~6.5-7k each. `auth-patterns`, `crypto-apis`, `config-patterns` | **Medium-high** | Lens 2 for crypto, auth and config hunters, and for the factory's Interface Design security challenge (it fits the challenge-card model) |
| `static-analysis` (semgrep, codeql, sarif-parsing) | Semgrep orchestration: `--metrics=off` always, explicit plan approval gate, third-party rulesets (ToB, 0xdea, Decurity), Pro detection, `scans.json` with failed/skipped. CodeQL DB build with quality checks. SARIF parsing. | 205k | **High as reference for the scanner adapter**, low as a loaded lens | Borrow the ruleset catalog, the `--metrics=off` rule and the "report what didn't run" contract into the Semgrep adapter |
| `variant-analysis` | After a bug is found: root cause → exact-match pattern → generalize one element at a time (stop at >50% noise) → triage → CI rule. Ships Semgrep/CodeQL templates for py/js/java/go/cpp. | refs ~14k total | **High** | Runs after every confirmed high/critical finding. Its CI rule becomes a Phase-1 lint check and a `SYS-C` row |
| `fp-check` | Verify one suspected bug: restate the claim, standard vs deep route, 6 gate reviews, bug-class requirements, devil's advocate. TRUE/FALSE POSITIVE verdict. | 62k. `bug-class-verification.md` 8k | **Medium** | Overlaps Cloudflare Phase 3. Use only `bug-class-verification.md` as the verifier's lens 2. Do not use its verdict vocabulary |
| `differential-review` | PR/diff review: risk-first triage (auth, crypto, value transfer, external calls = HIGH), git blame on removed security code, blast radius by caller count, test-coverage gaps, adversarial modeler. | 44k | **Medium** | Its risk triggers and "git blame removed security code" fit the slice-level trust-boundary lens. The report-file workflow does not fit (factory review writes `review.md`) |
| `supply-chain-risk-auditor` | Deterministic `collect.py`/`render.py` (uv): version-matched advisories, abandoned upstreams, npm publisher concentration, install scripts. "Unavailable data is never evidence of risk." npm/PyPI/Go only. Reads package-lock, uv.lock, go.mod (not yarn/pnpm/poetry). | 10k + scripts | **Medium** | An optional scanner-like step for dependency *health* (not CVEs, which OSV covers). It needs network and `gh` auth |
| `agentic-actions-auditor` | GHA workflows invoking Claude Code Action, Gemini CLI, Codex, AI Inference: env-var intermediary injection, `pull_request_target`, sandbox flags, wildcard allowlists, cross-file composite actions. | 100k | **High when AI agents run in CI** | Lens 2 for SUPPLY-CHAIN hunters on `.github/workflows` with AI steps |
| `rust-review` | Orchestrated worker clusters (unsafe boundary, memory safety, concurrency, panic DoS, FFI, async), dedup judge, FP judge, SARIF. | 295k | **Medium, separate run** | Too heavy as a lens. Offer it as an on-demand sub-audit for crates with `unsafe`/FFI. Otherwise MEMORY-SAFETY companion + `sharp-edges/lang-rust.md` |
| `constant-time-analysis`, `zeroize-audit` | Compiler-level timing side channels and secret zeroization (assembly/IR analysis). | 83k, 285k | Low (niche) | Only for crypto libraries. Route by "implements crypto primitives" |
| `property-based-testing` | Hypothesis, fast-check, proptest, Echidna/Medusa invariants. | 50k | Medium | Better placed in the money pack's verification and the red check than in the audit |
| `post-patch-validation` | Baseline vs patched evidence, variants, regressions, new failures. Pinned inputs. Workflow tool. | 35k | Medium | The factory red check (test fails on base commit) covers the core. Borrow "variants of the root cause must also fail on base" for security-fix packets |
| `audit-context-building` | Per-function assumption dossier ("nothing found" assumptions). | 42k | Low-medium | Overlaps Cloudflare recon and the factory Research stage. Use only for critical modules |
| `vulnerability-triage-brocards` | 7 brocards to filter automated findings or incoming reports. | 21k | Low-medium | Optional pre-filter for scanner output. The Cloudflare gate already does most of this |
| `building-secure-contracts` | Scanners for Algorand, Cairo, Cosmos, Solana, Substrate, TON. Guidelines advisor, token-integration analyzer, secure workflow (Slither), audit prep. | 435k | **Medium for web3 repos** | Route the one chain-specific scanner only. EVM goes through Slither in the scanner layer plus `token-integration-analyzer` |
| `semgrep-rule-creator` / `-variant-creator` | Writing custom Semgrep rules. | 23k | Medium | Turns a confirmed finding into a lint rule (`SYS-C`), together with variant-analysis |
| `spec-to-code-compliance` | One agent per requirement, divergences refuted. | 44k | Medium | Interesting for checking `constraints.md` security rows against code. Later work |
| Not relevant: `c-review`, `dwarf-expert`, `firebase-apk-scanner`, `burpsuite-project-parser`, `yara-authoring`, `trailmark` (code graphs; heavy), `testing-handbook-skills` (fuzzers; only for parsers), `entry-point-analyzer` (smart contracts only), `second-opinion`, `code-improver`, `culture-index`. | | | | |

---

## 3. Other sources found (focused search)

| Source | License / activity | Substance | Fit |
| --- | --- | --- | --- |
| **OpenAI `security-threat-model`**: https://github.com/openai/skills/tree/main/skills/.curated/security-threat-model | Apache-2.0 (per-skill LICENSE.txt). Last change 2026-02-02 | Repo-grounded threat model: system model → boundaries/assets/entry points → **attacker capabilities and explicit non-capabilities** → abuse paths → likelihood × impact → user validation of assumptions → mitigations tied to locations → quality check (every entry point covered, every boundary has a threat, runtime vs CI separated). SKILL 5.6k + prompt template 12.6k | **High as the threat-model template.** The factory feeds it from `.factory/system/` instead of interviewing |
| **OpenAI `security-best-practices`**: https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices | Apache-2.0. 2026-02-02 | Per-framework specs with **stable rule IDs**, version-pinned (e.g. Next.js 16.1.x: `NEXT-AUTH-002` middleware coverage gaps, `NEXT-ACTION-001` Server Actions as public endpoints, `NEXT-CACHE-001` static-render leaks, `NEXT-WEBHOOK-001` raw-body verification). Files: nextjs, react, express, general frontend, vue, jquery, go backend, django, fastapi, flask. **31-49 KB each (8-12k tokens)** | **High as stack depth**, but only per rule-ID section, never whole files. The SKILL.md's "make fixes and commit" guidance must not be loaded (it conflicts with the approved-slice flow). Rule IDs map cleanly to `SYS-C` rows |
| **Sentry `security-review`**: https://github.com/getsentry/skills/tree/main/skills/security-review | Apache-2.0. References derived from the OWASP Cheat Sheet Series (CC BY-SA 4.0). Last push 2026-10-09 | Confidence-gated (report HIGH only, MEDIUM = "needs verification"). Strong "do not flag" tables (server-controlled config, framework auto-escaping). Routing table from code type to reference (authz, injection, ssrf, csrf, business-logic…). Language guides for python and javascript. References 7-13 KB each | Medium. Overlaps Cloudflare ordinary blocks. Its **false-positive tables** are its best part, and fit the scanner-triage step |
| **Sentry `gha-security-review`**: same repo | Apache-2.0 | External-attacker-only threat model for GHA. Every HIGH needs entry point, payload, execution mechanism, impact and PoC sketch. Refs: pwn-request, expression injection, comment-triggered commands, credential escalation, AI prompt injection via CI, runner infra, real-world attacks (HackerBot Claw, StepSecurity 2025) | **High for GHA**, as lens 2 next to zizmor. It and `agentic-actions-auditor` are the two strongest GHA sources. Local `ci-secure` (starslingdev/skills, MIT, 29 stars) is a smaller third option |
| **Anthropic `claude-code-security-review`** (GitHub Action + `/security-review` command): https://github.com/anthropics/claude-code-security-review | MIT. Last push 2026-02-11 | Diff-only single prompt: >80% confidence, excludes DoS, rate limiting and secrets on disk. 3 phases (repo context, comparative analysis, assessment). Python FP filter and eval harness in the Action | Low as core: thin, diff-only, excludes classes we care about (LLM spend DoS). The factory's `/polish` review already covers this tier |
| **Semgrep `skills`** (`code-security`, `llm-security`, `semgrep`): https://github.com/semgrep/skills | **Semgrep Rules License v1.0** (restrictive; https://semgrep.dev/legal/rules-license). Last push 2026-07-28 | 28 rule categories with vulnerable/secure pairs, incl. terraform-aws/azure/gcp, kubernetes, docker, github-actions. `llm-security` mapped to OWASP LLM Top 10 (102 KB AGENTS.md) | Low-medium. Content overlaps, and the license makes vendoring awkward. Use Semgrep the *tool* with registry and third-party rulesets instead |
| **GitHub Security Lab taskflow agent**: https://github.com/GitHubSecurityLab/seclab-taskflow-agent (+ `seclab-taskflows`) | MIT. Active (2026-09) | YAML multi-agent taskflows on the OpenAI Agents SDK with MCP toolboxes (CodeQL-driven variant analysis) | Low. It is a separate runtime, not a skill. Ideas only |
| **Snyk `studio-recipes`**: https://github.com/snyk/studio-recipes | Apache-2.0. Active | Commands, hooks and rules that drive Snyk MCP scans and fixes (`snyk-code-fix`, `snyk-sca-fix`, `create-security-pr`) | Low. Requires a Snyk account. A fit only if the user adopts Snyk as a scanner |
| `mukul975/Anthropic-Cybersecurity-Skills` (817 skills, Apache-2.0) and `Masriyan/Claude-Code-CyberSecurity-Skill` (22 skills, MIT) | Active | Broad SOC/pentest/GRC catalogs, mostly offensive or operational. ~200 of the 817 are installed locally already | Low for AppSec of own code. A few (`auditing-terraform-infrastructure-for-security`, `conducting-api-security-testing`) duplicate Cloudflare companions with less rigor. Keep out of the routing index unless a gap appears |
| **zizmor** (scanner, not a skill): https://github.com/zizmorcore/zizmor | MIT. v1.30.1 (2026-09-09) | GHA static analysis: template injection, pwn requests, impostor commits, excessive permissions, cache poisoning | **Add to the S11 scanner list** (it is missing from the README) |

OWASP itself publishes no maintained agent skill. Its content reaches agents through Sentry's references (Cheat Sheets) and the Semgrep `llm-security` rules (LLM Top 10).

---

## 4. Recommendation

### 4.1 Roles

| Role | Source | Why |
| --- | --- | --- |
| **Core method, evidence bar, verdicts, schema, validators, prior-run carry** | Cloudflare `security-audit` | It is the only source whose bar equals "reproduced before reported", with independent verifiers and machine-checked output. MIT and active |
| **Threat-model template** | OpenAI `security-threat-model` output contract, fed from `.factory/system/` + Cloudflare recon prompts 1a-1d | Adds assets, attacker capabilities and non-capabilities, and abuse paths, which Cloudflare's 1,000-word `architecture.md` only implies |
| **Stack depth** | OpenAI `security-best-practices` per-framework rule-ID sections (Next.js, React, Express, Go, FastAPI/Django/Flask); ToB `sharp-edges/lang-*.md` for Rust/Go/Python/JS footguns | Framework facts Cloudflare lacks |
| **Config defaults** | ToB `insecure-defaults` category files | ~550 tokens each with explicit Report/Skip rules |
| **GitHub Actions** | zizmor (scanner) + Sentry `gha-security-review` refs, or ToB `agentic-actions-auditor` when AI agents run in CI | External-attacker model and real incidents |
| **Supply chain** | OSV-Scanner / stack audit tools / Trivy (scanners) + Cloudflare SUPPLY-CHAIN companion; optional ToB `supply-chain-risk-auditor` for dependency health | Mechanical first |
| **IaC** | Trivy config (or Checkov) + Cloudflare CLOUD-AND-DEPLOYMENT | |
| **LLM/agent** | Cloudflare AI-AND-LLM | Best boundary-based framing found ("prompt injection alone is not a finding") |
| **Money / web3** | Existing `fin-*` packs (already pinned); ToB `building-secure-contracts` chain scanner; Slither for EVM | Factory already routes money through these |
| **Rust `unsafe`/FFI** | Cloudflare MEMORY-SAFETY + `sharp-edges/lang-rust.md`; ToB `rust-review` as an on-demand sub-audit | |
| **After a confirmed finding** | ToB `variant-analysis` → `semgrep-rule-creator` | Turns one finding into a lint rule and a `SYS-C` row |
| **Verifier depth** | ToB `fp-check/references/bug-class-verification.md` | Class-specific proof requirements |

### 4.2 Combining without overlap (≤ 2 lenses per agent)

Treat **"Cloudflare core" as lens 1 for every security agent**: hunter method + candidate gate + structured result, or the verifier prompt + schema branch. The one ordinary block and the selected companion blocks are part of lens 1, because they share one vocabulary and one evidence bar. **Lens 2 is at most one external component file or section**, chosen by the routing index:

| Agent | Lens 1 (Cloudflare) | Lens 2 (one of) |
| --- | --- | --- |
| Threat modeler | RECONNAISSANCE 1a-1d prompts | OpenAI threat-model output contract |
| Hunter: web/auth unit | method + gate + Access control + WEB-PROTOCOL-AND-AUTH blocks | OpenAI Next.js (or Express, FastAPI, Go) rule-ID sections for that boundary |
| Hunter: client unit | … + CLIENT-SIDE | OpenAI React frontend sections |
| Hunter: config/obvious | … + Obvious things | ToB insecure-defaults category file |
| Hunter: CI unit | … + SUPPLY-CHAIN-AND-RELEASE | Sentry gha refs or ToB agentic-actions-auditor |
| Hunter: money unit | … + Business logic | the slice's `fin-*` skill |
| Scanner triage | verifier prompt + gate | Sentry "do not flag" tables (optional) |
| Verifier | verifier prompt + schema branch | fp-check bug-class-verification (optional) |
| Variant hunter | method + gate | ToB variant-analysis references |

**Conflict rules (written into factory-security):**
- Verdicts, severity anchors and evidence bar always come from lens 1. Lens 2 is loaded only as facts and rules, never its report format, severity scale, confidence scale, TRUE/FALSE POSITIVE vocabulary or "fix and commit" instructions. This means loading sections, not SKILL.md files.
- Never load two packs for the same domain in one agent (e.g. Sentry `authorization.md` with OpenAI `NEXT-AUTH-*`).
- External packs never execute their own workflows inside an audit run (ToB Workflow-tool pipelines, Semgrep plan-approval gate). The factory owns orchestration.

### 4.3 What factory-security must add itself

- **A1 Threat model from `.factory/system/`.** Product, ADRs, constraints and the code map go into `threat-model.md`: assets, principals and attacker capabilities/non-capabilities, trust boundaries with the strongest visible control, entry points, abuse paths, and assumptions to confirm. It replaces Cloudflare's `architecture.md` and is reused on track critical (DESIGN §3).
- **A2 Routing index** (`kit/security/index.yaml`). Each entry is a block reference (`CLOUD-AND-DEPLOYMENT.md#Workload identity overreach`, `openai:nextjs#NEXT-ACTION-001`, `tob:insecure-defaults/fallback-secrets.md`) tagged by stack, component and threat class, with the pack hash from `packs.lock.yaml`. The run records loaded blocks and excluded blocks with reasons; Cloudflare's ledger already has `selected_companion_blocks` and `excluded_blocks`.
- **A3 Scanner adapters.** Pinned versions run like the stack adapters: Trivy (fs, config, secret), Semgrep (`--metrics=off`, ToB third-party rulesets), Gitleaks, OSV-Scanner, **zizmor**, govulncheck (reachability is real mechanical evidence), cargo audit, pip-audit, npm audit, and Slither when Solidity is present. Output is normalized SARIF → candidate records (fingerprint `rule:path:symbol`) → Cloudflare verifier. Report what failed or was skipped. A raw scanner hit is never a finding.
- **A4 Sandbox runner.** For example `docker run --network none --read-only --memory --cpus --pids-limit --ulimit fsize` with a scratch tmpfs and an empty env. Plus one small trusted script that does the Cloudflare promotion procedure (O_NOFOLLOW, regular file, nlink==1, size-bounded copy). Without it, declare up front that local checks are blocked, and expect mostly `needs_validation`.
- **A5 Profile mapping to the three plug-in points:**
  - On-demand full audit = Cloudflare `standard`, artifacts written.
  - Track critical = threat model + `quick` scoped to the change's modules.
  - Slice touching a trust boundary = Cloudflare guidance mode on the diff, with the candidate gate and ToB differential-review's risk triggers. Output goes into `review.md` as challenge cards anchored to a threat-model boundary.
- **A6 Run storage.** `.factory/security/run-N/` must be git-ignored (Cloudflare refuses an in-target directory otherwise), or stored in the hidden-state branch. Keep prior `findings.json` and ledgers for the additive re-run logic, and index verdicts in Pond so review does not re-raise rejected claims.
- **A7 Findings to work.**
  - `confirmed` → one small-track slice each. The packet holds the invariant, a regression test that fails on the base commit plus root-cause variants, and Cloudflare `remediation` as a hint. The human approves each one.
  - Lasting invariants → `SYS-C` rows mapped to a test or lint rule (variant-analysis → Semgrep rule in Phase 1).
  - `needs_validation` → owner questions.
  - `rejected` → kept for suppression.
- **A8 Validators in Phase 1.** Run `validate-findings.cjs` and `validate-coverage-ledger.cjs` as scripts from the pinned pack path.

### 4.4 Risks

- **R1 Orchestration cost.** Cloudflare full mode is ~44k tokens of instructions in the parent across phases and many agents. Mitigation: default to `quick`/scoped runs, load phase files only when entering that phase, and give hunters excerpts only.
- **R2 Sandbox gap.** No container-based sandbox means few `confirmed` findings (see A4). This is the largest practical blocker.
- **R3 Licensing.**
  - ToB is CC-BY-SA-4.0: install pinned and unmodified, and do not copy text into factory skills.
  - Semgrep skills use a restrictive rules license: do not vendor.
  - Sentry references inherit OWASP CC BY-SA.
  - OpenAI and Cloudflare (Apache-2.0 / MIT) are clean.
  - README line 275 says packs are "vendored into `~/.software-factory/`, not into this repository", but the kit is now this repository (commit `6b26daa`). Packs are actually installed as pinned skills (`kit/packs.lock.yaml`), so the statement holds only if security packs follow the same install model.
- **R4 Harness lock-in.** ToB Workflow-tool pipelines and plugin-namespaced agents run only in Claude Code. Use their corpora, not their pipelines.
- **R5 Vocabulary drift.** Mixing fp-check, Sentry and OpenAI severity/confidence scales with Cloudflare verdicts produces inconsistent reports. Enforce the conflict rules in 4.2.
- **R6 OpenAI spec size and staleness.** Each spec is 8-12k tokens and pinned to a framework version (Next.js 16.1.x, sources accessed 2026-01-27). Load by rule ID and record the pinned version in the routing index.

## Evidence index

- Cloudflare repo, README, commits: https://github.com/cloudflare/security-audit-skill (`gh api`, HEAD `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`, skill tree `ccbc33ed119b28c3ef7b44a7e2081ab191ad63af`). Local files read in full: `~/.claude/skills/security-audit/*.md`, `report-schema.json`, validator sources (semantic-check section read), tests executed.
- Trail of Bits: https://github.com/trailofbits/skills @ `442fc9d6c89b1e937e6f7a477e7071ea75fcbea4` (shallow clone in scratchpad `src/tob`, read only, nothing executed).
- OpenAI: https://github.com/openai/skills/tree/main/skills/.curated (security-threat-model, security-best-practices, security-ownership-map)
- Sentry: https://github.com/getsentry/skills/tree/main/skills (security-review, gha-security-review)
- Anthropic: https://github.com/anthropics/claude-code-security-review
- Semgrep: https://github.com/semgrep/skills, license https://semgrep.dev/legal/rules-license
- GitHub Security Lab: https://github.com/GitHubSecurityLab/seclab-taskflow-agent
- Snyk: https://github.com/snyk/studio-recipes
- zizmor: https://github.com/zizmorcore/zizmor
- Catalogs named in README S11: https://github.com/mukul975/Anthropic-Cybersecurity-Skills, https://github.com/Masriyan/Claude-Code-CyberSecurity-Skill
- Local: `~/.agents/.skill-lock.json` (install sources), `kit/packs.lock.yaml`, `docs/DESIGN.md`, `README.md` S11.
