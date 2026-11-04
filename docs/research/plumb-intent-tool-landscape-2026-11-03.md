# Tool research for the clean-slate Plumb intent checker

Observed: **2026-11-03**. Scope: dependency choices for a new local CLI, with the existing factory excluded from the implementation. These are recommendations, not measured performance results. The architecture and product contract belong to the accompanying architecture plan.

**Use Python, Git, an official model SDK, strict evidence validation, and JSON/Markdown. Start with a bounded evidence packet and no persistent search index.** Add a parser, retrieval index, second provider, or CI-specific format only when a named evaluation shows why it is needed.

The needed capability is narrow: compare a pinned code change with explicit sources of intent; return useful, auditable questions. The constraints recovered from the brief are a small CLI, repo docs/ADRs and an explicitly supplied PR body first, human resolution of code/spec disagreement, and no MCP server, hosted service, code execution agent, or automatic fixing. Provider portability is a later compatibility commitment, not something one generic endpoint can establish.

## Recommended adoption order

| Need | Start with | Why this earns its place | Boundary / fallback |
|---|---|---|---|
| CLI and records | Python standard library: `argparse`, `dataclasses`, `json`, `pathlib`, `subprocess`, hashing; `tomllib` only if config is needed | No web framework or application runtime required. `argparse` covers basic subcommands. | Dataclasses do **not** validate their annotated types. Validate untrusted JSON/config explicitly. [S01](#s01-python) |
| Snapshot evidence | Installed Git through argument arrays | Read committed blobs and differences without building another repository model. | Resolve immutable revisions; isolate hostile repository configuration; never rely on the current worktree for evidence about a different commit. Detailed semantics belong in the architecture contract. [S05](#s05-git) |
| Model integration | Official `anthropic` Python SDK **2.4.0**, the release observed on PyPI on 2026-11-03 | Native structured output, typed response/error handling, configurable retries/timeouts, token counting. | Support one provider honestly. Keep vendor objects at the adapter. Select the model by Plumb's evaluation, not by this document. [S14](#s14-anthropic) |
| Machine-readable boundary | A small explicit schema, with strict Pydantic validation when using the SDK's parsing helper | Reuse the SDK ecosystem instead of a second extraction framework. | SDK response parsing and schema compliance cannot establish semantic truth. Evidence validation is Plumb code. [S14](#s14-anthropic) |
| Context selection | Explicit paths, changed files, bounded exact search, and enough surrounding source to inspect the behavior | Establishes the simplest reproducible baseline. | Never silently truncate and report a clean result. Report incomplete coverage or request a smaller scope. |
| Human/agent output | Versioned JSON plus Markdown from the same validated result | Works through the shell and ordinary CI exit codes. | Formatting must not create or repair evidence. SARIF can be a later output adapter. [S21](#s21-sarif-and-github) |

No package was installed or added by this research. The SDK version is a research snapshot, not a floating dependency recommendation: implementation should lock an audited release and its transitive dependencies, then rerun the same contract/evaluation tests before upgrades.

## Runtime candidates

| Candidate | Evidence and license | Fit for this CLI | Decision |
|---|---|---|---|
| Python standard library + one provider SDK | `argparse` is the standard basic CLI parser; `dataclasses` supplies record methods; `tomllib` was added in 3.11. Python is PSF-licensed. [S01](#s01-python) | Small I/O-oriented program with a straightforward fixture/evaluation ecosystem. A Python interpreter/package environment remains a distribution requirement. | **Use.** Python >=3.11 is a sensible baseline if TOML config is included; it is not a claim about the latest Python release. |
| TypeScript on Bun + Effect + Zod | Bun runs TypeScript. Effect covers typed failures, concurrency, resource handling and schema validation; Zod 4 exports JSON Schema. Bun itself, Effect and Zod are MIT; Bun's linked components have additional licenses. [S02](#s02-typescript-bun-effect-and-zod) | Credible if the maintainer chooses TS. Effect already has schema facilities, so adopting both full Effect Schema and Zod would require a concrete interoperability reason. | **Alternative.** The extra runtime/framework surface has no demonstrated payoff for the first bounded CLI. No assertion that it would be slower. |
| Go | Official toolchain builds applications; language distribution has BSD-style terms. [S03](#s03-go) | Attractive if single-binary delivery becomes a hard requirement. | **Defer.** The expected model API wait is a design assumption; no measured CPU bottleneck justifies switching languages. |
| Rust + Cargo | Cargo owns build and dependencies; a release build produces an executable. Rust is primarily MIT/Apache-2.0 with third-party exceptions. [S04](#s04-rust) | Strong distribution and explicit data modeling; requires choosing and maintaining HTTP/schema libraries. | **Defer.** Single-binary distribution or measured local analysis cost could reopen it. Pond using Rust does not make Rust a Plumb requirement. |

The current scope is a command-line application, so house rules for an HTTP backend, FastAPI, Next.js, or multiple services do not force a web framework into it. This is a fit judgment, not an external performance claim.

## Code evidence: plain tools before a code intelligence platform

| Tool | Confirmed capability / limits | License / maintenance evidence | Adoption decision |
|---|---|---|---|
| Git | Committed snapshots, diffs, rename metadata and path-based reads. These do not themselves prove behavior. [S05](#s05-git) | Established documented CLI; do not bundle Git code just to call the installed executable. | **Required.** Treat it as a subprocess boundary, not a domain abstraction. |
| ripgrep | Regex search, line locations, ignore handling and JSON output. It searches text, not semantic references. [S06](#s06-ripgrep) | Upstream explicitly offers MIT or Unlicense; mature upstream project. | **Optional accelerator**, with Git/plain-text search fallback. Searching a mutable worktree is unsuitable for a pinned-commit finding. |
| Tree-sitter | Incremental concrete syntax trees, including useful trees for incomplete code; language-specific grammars still matter. Parsing is not cross-file symbol resolution or a proof of behavior. [S07](#s07-tree-sitter) | MIT runtime; grammar licenses/bindings need separate review. Upstream warns some bindings can be incomplete or stale. | **Defer.** Add only the languages needed when source-window selection measurably misses relevant functions. |
| ast-grep | AST-based searching/linting, with JSON and tested rules. It builds on syntax rather than supplying the intended behavior. [S08](#s08-ast-grep) | MIT upstream; documented CLI and rule tests. | **First parser-based candidate** for an explicit named check. Use read-only search; rewriting is outside scope. |
| SCIP | Language-agnostic code intelligence index for definitions, references and implementations; relies on suitable language indexers. [S09](#s09-scip) | Apache-2.0 protocol repository; indexer dependency/license is additional. | **Defer.** Useful if evaluated misses are genuinely cross-file reference misses. An index cannot replace claim authority or semantic assessment. |
| Serena | Semantic navigation and editing toolkit, commonly exposed through MCP. [S10](#s10-serena) | Current application is GPL-3.0-or-later; SolidLSP alone is MIT. Combined distributions are GPL according to upstream. | **Exclude from v0.1.** A persistent agent toolkit and editing tools do not serve the requested narrow read-only CLI. No claim that its retrieval quality is inherently worse. |
| Archgraph | Public upstream fetch failed during this review. No external behavior, current release, or license was independently confirmed. [S11](#s11-archgraph) | **Unverified.** Local usage discovery is a separate evidence task. | **Not a required dependency.** A later integration must have a pinned, independently verified contract and an evaluation benefit. |

Do not implement regex symbol extraction and call it semantic analysis. When a language-specific parser is eventually needed, test it against that language's real syntax and report unsupported constructs.

## Retrieval: what should exist before an index

**Start with bounded full context over explicitly selected sources**, alongside deterministic path/identifier matching. This is the baseline to beat, not a promise that all repositories fit into one model request. Store source bytes, revision/hash, and offsets before extraction. Claim paraphrases are derived data; the source passage remains authoritative.

**SQLite FTS5 is the first retrieval candidate if the corpus grows.** It provides local full-text search and built-in BM25 without an embedding service. Better BM25 results have numerically smaller scores. Default word tokenization is not a code-identifier tokenizer; evaluate identifier splitting, punctuation, prose paraphrases, and zero-match queries. FTS5 availability is a build/runtime capability to probe, not assume. Its index must be disposable and keyed by the exact source set. SQLite is public domain. [S12](#s12-sqlite-fts5)

**A vector database is not needed just because an LLM is involved.** Qdrant is a credible later candidate: the Python client has in-memory and on-disk local modes, so it would be wrong to reject it on the claim that it always needs a server. Nevertheless embeddings introduce a model, embedding versions, refresh/rebuild rules, and a second retrieval evaluation. The client is Apache-2.0. No vector-search recall advantage has been measured for Plumb. [S13](#s13-qdrant)

Proposed promotion gate: evaluate raw context, lexical retrieval and any hybrid candidate on the **same held-out claim-to-evidence cases**, counting missed relevant claims, source-conflict recall, evidence recall@k, final finding precision/recall, model input tokens and wall-clock time. Promote an index only if it meets a predeclared recall floor and improves the actual cost/coverage constraint. Those thresholds must be chosen before comparing results; this research does not invent an achieved improvement.

## LLM integration and framework candidates

Version/release observations below come from the linked registries on 2026-11-03. Release activity establishes that projects are changing; it does not establish reliability, compatibility or issue-response SLAs. Download counts were not sampled, and stars are not used as a quality score.

| Candidate | Observed release and documented capability | License / quality and security evidence | Verdict |
|---|---|---|---|
| Anthropic official SDK | **2.4.0**, 2026-11-02; Python >=3.10. Sync/async clients, parsing helpers, typed response models, configurable retries/timeouts. [S14](#s14-anthropic) | Current Apache-2.0 plus older/contributed MIT portions. Current upstream includes Windows, Bedrock and streaming reports: one SDK is still a dependency to test, not a reliability guarantee. | **Use first**, on the direct API, with a fixed model selected by the eval. |
| OpenAI direct API/SDK | Structured output is also a verified alternative; schema support is restricted and refusals/incomplete responses need explicit handling. [S15](#s15-openai-structured-output) | SDK exact version and its complete dependency/license set were not audited in this comparison. | **Second-provider candidate**, after a named user need; run a provider contract suite before claiming compatibility. |
| LiteLLM | **1.106.6**, 2026-10-28; Python SDK can normalize many providers without deploying its optional gateway. [S16](#s16-litellm) | Core MIT with separately licensed enterprise portions. Upstream publishes a March 2026 package compromise postmortem and proxy advisories. Those do not establish that this release's SDK path is vulnerable. | **Defer.** Broad coverage is useful, but unnecessary normalization, release churn and supply-chain review need a payoff. Do not deploy a gateway for this CLI. |
| Instructor | **1.17.0**, 2026-09-09; schema-first extraction, Pydantic validation and retry handling. [S17](#s17-instructor) | MIT. Official README presents extraction as its core use, distinct from an agent runtime. | **Defer.** Native SDK parsing covers the first provider; don't stack automatic repair retries over SDK retries. |
| PydanticAI | **2.65.0**, 2026-11-03; Python >=3.11. Typed multi-provider agent loop and broader execution features. PyPI exposes provenance for that release. [S18](#s18-pydanticai) | MIT. Provenance supports publication traceability, not semantic correctness or freedom from vulnerabilities. | **Defer.** A fixed comparison pipeline needs no agent loop. If later adopted, evaluate the slim/provider-specific installation first. |
| LangGraph | **1.2.19**, 2026-10-30; durable long-running stateful orchestration. [S19](#s19-langgraph) | MIT; official docs and versioning policies. | **Exclude from the initial design.** Restartable multi-step agents are not a current requirement. |
| OpenAI Agents SDK | **0.24.0**, 2026-10-15; agents, tools, handoffs, sessions and tracing, with provider integrations. [S20](#s20-openai-agents-sdk) | MIT; PyPI exposes publication provenance. | **Exclude from the initial design.** Do not introduce agent handoffs to run a known sequence. |

### First SDK: verified operational contract

Use Anthropic's direct Messages API, with no model-accessible filesystem, shell, external URL fetch, or source mutation tools. `messages.parse(output_format=...)` can use a Pydantic output model; alternatively submit the supported JSON Schema explicitly. Keep strict field/type/size validation and provenance checks in Plumb. [S14](#s14-anthropic)

The request contract needs these cases:

- A refusal can have HTTP 200 and bypass the requested schema. Token-limit truncation can also yield invalid output. Neither is an empty successful review. [Structured output limitations](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- The SDK retries selected transient failures twice by default and defaults to a ten-minute request timeout. Override these deliberately so one shared deadline/attempt budget owns all calls; avoid multiplying retry layers. An upstream report says keepalive events can keep a stalled stream open, so enforce a whole-review deadline independently. [SDK configuration](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python), [reported streaming limitation](https://github.com/anthropics/anthropic-sdk-python/issues/2051)
- Count input tokens before generation and reserve the output allowance. Rate limits vary by organization and model class across requests/input/output tokens. Respect `retry-after` when supplied; spend-cap responses can lack it and need a terminal result. Never put sample quota numbers into the product as guarantees. [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting), [rate limits](https://platform.claude.com/docs/en/api/rate-limits)

Suggested product behavior, not a provider guarantee: bound each generation and share at most one retry across the workflow for an explicit retryable rejection. Do not automatically retry an ambiguous accepted-request timeout, which may already be billable. Invalid semantic evidence is discarded rather than repaired by inventing a quote; the report must retain the resulting validation gap instead of claiming a clean review. Check dollars from current configured model prices and reported usage; this report does not estimate subscription charges or invoice cost.

The hard part remains Plumb's own judgment evaluation. A passage occurring verbatim and a code location existing proves that the citations exist. It does **not** prove the passage governs that code, that the quoted code determines runtime behavior, or that either side should win. Source authority must be explicit, origin labels must remain hypotheses, and missing evidence must permit abstention.

## Output and CI

JSON/Markdown and distinct exit codes are sufficient to invoke the CLI in any CI. Keep output on stdout and progress/errors on stderr. A dedicated GitHub Action wrapper is optional packaging, not a prerequisite for using the checker in Actions.

SARIF can later add code-scanning annotations and stable fingerprints. GitHub supports uploaded third-party SARIF, but private/internal repository availability depends on its code-security product configuration. A spec-stale or source-conflict result can be awkward to anchor to one code line; preserve all evidence in native JSON and treat SARIF as a projection. This is a fit inference, not an unsupported-format claim. [S21](#s21-sarif-and-github)

## Product references, not runtime dependencies

Pond's useful lesson is its declared canonical data schema and structurally preserved provenance. Its current storage, transports, and Rust implementation solve session recall and do not become Plumb requirements. [S22](#s22-pond)

OpenSpec and Spec Kit are openly licensed workflow/specification tools. Their upstream descriptions do not establish a ready-made, independently evaluated drop-in intent verifier. CodeSpeak markets intent capture, mapped requirements and drift checks, but its page still presents a waitlist; no verifier SDK, license or measured accuracy was established here. Treat it as an adjacent product, not as a technical building block. [S23](#s23-adjacent-spec-products)

## Revisit gates and remaining validation

| Addition | Observable reason to reopen it | Smallest trial |
|---|---|---|
| FTS5 | Explicit context no longer fits the input/cost budget | Same held-out cases, full-context oracle against lexical selection; reject silent recall loss. |
| Tree-sitter / ast-grep | Failures come from missing the enclosing syntax or a concrete mechanically checkable rule | One-language fixture set, including malformed/unsupported syntax; compare evidence recall. |
| SCIP / graph | Missed findings require reference/call relationships beyond path/text selection | Evaluate on those specific cross-file cases; include index build time and stale-index rejection. |
| Another provider / LiteLLM | A real user needs another provider, or the evaluated first provider cannot meet cost/quality needs | Golden request/result fixtures plus refusals, truncation, auth, quotas and usage accounting; compare direct SDK adapter first. |
| Agent framework | A fixed evidence workflow demonstrably cannot gather enough context within its bound | Compare a read-only bounded tool workflow to the fixed baseline; include cost, precision and deadline failures. |
| SARIF | Users need code-scanning alerts and their repositories support the feature | Upload a synthetic fixture on a disposable test repository; check locations and deduplication. |
| Rust / Go | Installation friction or measured local CPU/memory dominates the user experience | A representative packaging or analysis spike; keep the same CLI/JSON contract. |

No runtime performance, detection accuracy, issue-response SLA, or complete dependency vulnerability audit was measured. Archgraph's external behavior and model/provider account limits remain unverified for this environment. A local SDK contract spike and the intent evaluation are the next evidence gates; no recommended v0.1 dependency rests on Archgraph, hosted infrastructure, or a model quality claim.

## Source manifest

Primary sources opened on 2026-11-03. Versions shown above are observed snapshots; unversioned documentation may change.

### S01 Python

[argparse](https://docs.python.org/3/library/argparse.html), [dataclasses](https://docs.python.org/3/library/dataclasses.html), [tomllib](https://docs.python.org/3/library/tomllib.html), [PSF license](https://docs.python.org/3/license.html). CLI facilities, record/type-validation distinction, TOML support and license.

### S02 TypeScript, Bun, Effect and Zod

[Bun runtime](https://bun.sh/docs/runtime), [Bun and linked-library licenses](https://bun.sh/docs/project/license), [Effect guides](https://effect.website/docs/v4/getting-started), [Effect license](https://github.com/Effect-TS/effect/blob/main/LICENSE), [Zod 4](https://zod.dev/v4), [Zod license](https://github.com/colinhacks/zod/blob/main/LICENSE). Runtime and validation capabilities; no relative benchmark claim.

### S03 Go

[Official installation/toolchain](https://go.dev/doc/install), [license](https://go.dev/LICENSE). Credible alternate compiled toolchain; no version/performance selection made.

### S04 Rust

[Cargo build system](https://doc.rust-lang.org/book/ch01-03-hello-cargo.html), [copyright and license overview](https://github.com/rust-lang/rust/blob/main/COPYRIGHT). Build/distribution alternative.

### S05 Git

[git diff](https://git-scm.com/docs/git-diff). Snapshot/diff capabilities; architecture plan owns exact revision semantics.

### S06 ripgrep

[Upstream README and license statement](https://github.com/BurntSushi/ripgrep). Text search and licensing.

### S07 Tree-sitter

[Introduction/bindings](https://tree-sitter.github.io/tree-sitter/), [runtime license](https://github.com/tree-sitter/tree-sitter/blob/master/LICENSE). Syntax trees, error tolerance and binding caveats.

### S08 ast-grep

[Introduction and documented tool surface](https://ast-grep.github.io/guide/introduction.html), [license](https://github.com/ast-grep/ast-grep/blob/main/LICENSE). AST search/lint/rule testing; not a behavior oracle.

### S09 SCIP

[Protocol repository](https://github.com/scip-code/scip). Definition/reference/implementation indexing and Apache-2.0 license.

### S10 Serena

[Upstream README](https://github.com/oraios/serena). Semantic coding-tool scope and current per-component licensing.

### S11 Archgraph

[Attempted upstream](https://github.com/dogebonker/archgraph). Retrieval failed with cache miss; current external claims intentionally unverified.

### S12 SQLite FTS5

[FTS5 reference](https://sqlite.org/fts5.html), [copyright](https://sqlite.org/copyright.html). BM25, tokenization, compilation and rebuilding; public-domain status.

### S13 Qdrant

[Python client](https://github.com/qdrant/qdrant-client), [quickstart](https://qdrant.tech/documentation/quickstart/). Local mode, persistence, embeddings and Apache-2.0 client license.

### S14 Anthropic

[PyPI release metadata](https://pypi.org/project/anthropic/), [SDK repository/license](https://github.com/anthropics/anthropic-sdk-python), [SDK configuration](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python), [structured output](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons), [token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting), [rate limits](https://platform.claude.com/docs/en/api/rate-limits), [upstream streaming report](https://github.com/anthropics/anthropic-sdk-python/issues/2051). Current SDK capability and operational limitations; no model quality claim.

### S15 OpenAI structured output

[Official guide](https://developers.openai.com/api/docs/guides/structured-outputs). Verified alternative's schema/refusal/incomplete-output behavior. Exact SDK/version/license audit deferred.

### S16 LiteLLM

[PyPI](https://pypi.org/project/litellm/), [upstream](https://github.com/BerriAI/litellm), [license](https://github.com/BerriAI/litellm/blob/main/LICENSE), [security advisories](https://github.com/BerriAI/litellm/security/advisories), [upstream March 2026 security update](https://github.com/BerriAI/litellm-docs/blob/main/blog/security_update_march_2026/index.md). Library versus gateway, maintenance snapshot, scope-specific licensing and disclosed security history.

### S17 Instructor

[PyPI](https://pypi.org/project/instructor/), [upstream](https://github.com/567-labs/instructor). Release snapshot, extraction scope and MIT license.

### S18 PydanticAI

[PyPI](https://pypi.org/project/pydantic-ai/), [upstream](https://github.com/pydantic/pydantic-ai). Version, Python requirement, provenance, license and agent-runtime scope.

### S19 LangGraph

[PyPI](https://pypi.org/project/langgraph/), [upstream](https://github.com/langchain-ai/langgraph). Version, MIT license and durable stateful orchestration scope.

### S20 OpenAI Agents SDK

[PyPI](https://pypi.org/project/openai-agents/), [upstream](https://github.com/openai/openai-agents-python). Version, publication provenance, MIT license and multi-agent/tool/session scope.

### S21 SARIF and GitHub

[Official upload documentation](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file). Third-party upload, fingerprints and repository eligibility constraints. Separate SARIF support page failed to open; no unverified field-limit claim is used.

### S22 Pond

[Upstream README](https://github.com/tenequm/pond). Canonical-schema/provenance principle and distinct session-recall scope.

### S23 Adjacent spec products

[OpenSpec upstream](https://github.com/Fission-AI/OpenSpec), [Spec Kit upstream](https://github.com/github/spec-kit), [CodeSpeak product page](https://codespeak.dev/). Public workflow descriptions and MIT statements for the first two; CodeSpeak capabilities remain marketing claims, not independently validated implementation evidence.
