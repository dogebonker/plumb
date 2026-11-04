# Plumb intent architecture: forces, capacity and validation appendix

Proposed, 2026-11-03. Read with [the overview](../ARCHITECTURE.md) and [decision records](../adr/0001-local-cli.md). Numbers below are planning assumptions/acceptance targets unless explicitly labeled measured. No verifier implementation, load test or live model evaluation was performed for this architecture.

## Scope and source of requirements

Clean-slate product design in an existing repository. Preserve useful public evidence/attribution and future access to the factory revision; the new implementation does not preserve factory APIs, approval gates or layout. This session authorizes research/planning, not deleting source or rewriting branches.

Pond recall: session `59e32a8f-3678-4fea-a523-b0c4a9e326ba`, user message `57fda574-a0fc-4535-90a6-be429923d3aa`, 2026-11-01. The latest pasted exchange explicitly narrowed a larger factory/integration idea into a minimal CLI. The current user's clean-slate correction supersedes the earlier suggestion to extract existing helpers unchanged. Source policy, runtime limits, a concrete SDK and release dates were not fixed by that conversation.

## Functional forces

| ID | Flow and outcome | Basis |
| --- | --- | --- |
| FR1 | A developer runs `plumb check` over a committed range and gets a report bound to that exact code/source snapshot | Recalled explicit direction; committed-only first version is an assumption |
| FR2 | A developer supplies repo docs/ADRs and optionally a PR-body file; Plumb identifies cited normative claims and conflicting applicable passages | Recalled direction |
| FR3 | A reviewer sees a concrete mismatch with quoted intent, code/source locations, proposed origin or unresolved origin, and one question | Recalled direction; unresolved representation is a design decision |
| FR4 | A person/CI reads Markdown/JSON and exit status, including incomplete coverage and failures | Recalled minimal CLI + JSON direction |
| FR5 | An agent invokes the shell command using instructions printed by `plumb skill` | Recalled minimal direction; no MCP |
| FR6 | The maintainer evaluates changes against a reproducible baseline and publishes quality, coverage, time and cost with limitations | Recalled portfolio/evaluation direction |

No flow moves money or applies an irreversible change. Source upload to a model endpoint is a real external effect, selected explicitly by the operator; disabling egress precludes that backend. No source edits, PR posts, waivers or merges are part of a check.

## Non-functional forces and constraints

| ID | Target / assumed value and measurement point | Status |
| --- | --- | --- |
| NFR1: operating envelope | 1 maintainer, 1 active check/process; 1 check/hour average, peak 1/minute (60×). Up to 20,000 tracked paths; review packet fits 24,000 input tokens, total generation input <=60,000 and output <=6,000/check; overflows are explicit incomplete outcomes | Assumptions; measure inventory size and request admission |
| NFR2: latency | Local preparation p99 <=5 s on declared reference hardware; whole check p99 <=180 s in envelope; hard 240 s deadline including waits/counting/retries | Unmeasured targets; report hardware/model/network and percentiles |
| NFR3: integrity | 0 retained findings with invalid quotes/revisions/spans or missing required evidence; 0 reviewed-source/spec writes; 0 fabricated authority promotions in boundary suite | Structural acceptance criteria, not semantic accuracy claims |
| NFR4: quality | Held-out finding precision >=0.90 and overall planted-mismatch recall >=0.75; recall >=0.60 in each of code-wrong/spec-stale/source-conflict buckets; <=0.05 false-positive rate on no-drift cases; >=0.90 complete-review rate on declared supported envelope | Proposed predeclared experimental gates; confidence intervals required |
| NFR5: spend | Operator-configured maximum input/output tokens and model price schedule; example admitted worst-case generation budget $1/check, account quota must permit it | Assumed budget, not model pricing or an invoice guarantee |
| NFR6: failure and availability | 100% of dependency/validation failures in fault suite map to explicit error/incomplete, never complete/no-findings; no network needed for `skill` or no-change runs | Acceptance criteria; no hosted uptime/SLA |
| NFR7: team/time/infra | 1 maintainer, 4-week experimental-release target, $0/month Plumb-hosted infrastructure, assumed $100 maximum initial external-model evaluation spend | Assumptions; stop/adapt the experiment before exceeding budget |
| NFR8: security/privacy | 0 model-accessible tools; 0 repo-script execution; no automatic network fetch; credentials only in operator environment/key storage; payload only selected supported sources; default diagnostics omit source content | Acceptance criteria; model receives selected source only after explicit configuration |
| NFR9: consistency/recovery | Pin every input before generation; no mixed revisions; primary source RPO is unchanged Git/operator files; derived run state can be lost (RPO one run), recovery is a rerun bounded by 240 s plus provider availability | Design contract; no persisted state to restore |
| NFR10: compliance/data | Initial fixtures public/synthetic and local owner-controlled repos; 0 customer-data fixtures; no external residency/compliance guarantee | Scope assumption; operator chooses acceptable model endpoint/data policy |
| NFR11: observability | Every request records outcome, elapsed time, model/prompt/schema identity and provider request ID when available; unknown usage explicitly null | Acceptance criteria; no compulsory telemetry collector |
| NFR12: repository growth | Supported packet size is the limit, not annual Git history; zero retained index/cache growth. Reports are stdout artifacts retained under operator control | Design assumption; no retention service |

Capability is defined by FR1–FR6. Failure cost is lost review time, false accusations, missed drift and possible source exposure; the tool is advisory, not an authorization or deployment gate. Availability is an error contract for a local command. No real production latency/load data exists for this new product.

The house stack rules were read. Python CLI falls outside their backend/frontend defaults and is selected provisionally from the Team/environment force: Python 3.10 exists locally and the provider SDK supports it. Standard-library JSON config avoids requiring `tomllib`/Python 3.11. A required different team stack reopens D01.

## Capacity arithmetic

The initial operating assumption is one serialized active invocation; this is not a daemon enforcing a global multi-process quota. Independent processes may exceed account limits and must handle quota errors. Concurrency is one inside an invocation; no speculative fan-out.

At the peak **one check/minute**, a three-generation-call check requires **3 generation requests/minute**, up to **60,000 input tokens/minute** and **6,000 output tokens/minute**. Up to three token-count requests and one shared retry add at most **4 more requests/minute**, if those requests count toward the account's relevant quota. Provider quota classification must be checked for the selected account/model; no fabricated universal RPM/ITPM/OTPM is assumed.

For selected generation limits `R`, `I`, `O`, the nominal utilization ratios are `3/R`, `60000/I` and `6000/O`; one retry can raise request utilization to `4/R`. Token-count requests have a separately documented quota that must also be checked; do not automatically add them to generation RPM. The largest ratio is the quota bottleneck; a ratio >1 rejects that peak assumption or requires pacing. With mean check time `T` seconds and local concurrency 1, per-process service capacity is `60/T` checks/minute. At `T=180`, that is **0.33/minute**, so one invocation per minute is an arrival burst, not sustainable serialized throughput; there is no hidden queue. The caller serializes invocations or starts independent processes subject to account limits; the CLI does not pretend to enforce a global busy state.

Generation deadlines are **3 × 60 = 180 seconds**. Token counting, local work and the one allowable retry must fit the remaining **60 seconds** of the **240-second** total deadline; do not start another call when its allowance cannot fit. Admission bounds input/output **per phase** and across the check, including repeated context. A second provider or prompt cache does not enlarge these ceilings.

Repository inventory is at most 20,000 tree entries; body reading is limited to selected text and the packet budget. Zero database writes, zero webhook calls, zero queues, zero held subscriptions. CLI output is one report stream. CPU time and memory limits require measurement on representative fixtures; no language speed claim is inferred from file count. NFR2's 5-second preparation target decides whether bulk Git object reading/optional exact search needs optimization.

Known bottleneck class: model request latency, context budget and account quotas. The tightest numerical account ratio is **unknown until preflight reads the operator's limits**. The safe fallback is serialized calls and an explicit quota/incomplete outcome, not more services or a different language.

For current configured uncached input/output prices `p_in` and `p_out` in dollars per million tokens, the generation ceiling is `0.060*p_in + 0.006*p_out`. Reserve any separately billed request/counting/rounding costs too; require the total <= the configured cap before admission. Do not assume cache discounts. This formula may rule out a model at $1; select another evaluated model or reduce a predeclared supported packet, rather than silently exceeding the budget. Token estimates can differ from actual provider accounting, so distinguish conservative admission bounds, reported usage and actual invoice charges. An ambiguous timed-out accepted request consumes its reservation and is not automatically retried.

The proposed $100 evaluation budget cannot support unlimited repeated 200-case runs. Stage the experiment: 40 development cases, choose finalists, then allocate remaining budget across baseline/target/ablation on held-out cases. Lower the admitted per-case cap or stop before the projected total exceeds $100; do not claim 200×3×many trials were run. The architecture does not rely on an assumed completed benchmark.

## As-is evidence and change cost

Inspected repository revision: `2f79d5845e98993ea8023812c222c6a6ee718698`, clean at task start. These are implemented surfaces, not proof of a hosted deployment:

| Surface/store | Actual writer / behavior evidence |
| --- | --- |
| Skills/edit gate; `.plumb` documents/status | `hooks/plumb_gate.py:557` checks branch-matching state and permits/blocks edits |
| Headless runner; clone/status/remote branch | `runner/plumb_run.py:383` runs a harness in a clone; `:459` queries GitHub; `:524` writes status/commits/pushes |
| Experimental v2; isolated run records | `runner/plumb_v2.py:295` invokes Claude CLI; `:450` onward writes inputs/events; `runner/v2_checkpoint.py:69` owns checkpoint/journal output |
| Optional event receiver; SQLite queue | `runner/plumb_events.py:27` defines deliveries/jobs; `:105` admits signed events; `:242` serves/polls |
| ADR helper; drafts/reports | `kit/adr.py:12` imports hook/runtime; `:58` hardcodes factory ADR layout; `:271` and `:334` write drafts/reports |
| Archgraph adapter; external artifacts | `kit/archgraph.py:123` drives tool/context/report handling; `:125` limits proof claims |

Current outside systems include Git/GitHub CLI and reviews, Claude CLI, optional GitHub/Linear webhooks, optional pinned archgraph and local sandbox/toolchains. None except Git becomes a fixed integration requirement of the new CLI. The new SDK endpoint is independently researched.

Measured pain P1: factory accepted **9/20** versus **14/20** in either control; medians **1,800.1/419.2/377.2 seconds**. P2: planning accounted for **46.7%** of factory task time and critical tasks held **8/9** timeouts. These argue against carrying orchestration overhead, not for any verifier accuracy claim. [Benchmark](real-pr-benchmark-2026-10-19.md), [timing](benchmark-time-2026-10-25.md).

Integrity limit P3: intent exercise was **one call/two tiny revisions**; correctness/coverage generalization is unsupported. Historical raw benchmark packets were deleted; published aggregates/hashes remain. P4: helper coupling is observed in code; the cost of extracting it is unmeasured. Clean-slate is the user's explicit direction, not a fabricated extraction benchmark.

Change cost is a new package plus a breaking product surface, with no user-data migration. Retain/rewrite the narrow tests for invented quotes, stale snapshots, wrong revisions, unknown status, odd paths, deleted lines and omitted coverage. Preserve experiment writeups/license attribution deliberately. Factory approval/build semantics are non-goals. No feature freeze or compatibility promise has been requested.

## Outside-system contracts and gotchas

| System | Verified behavior / design consequence | Unverified/environment-specific part |
| --- | --- | --- |
| Git | Tree comparisons differ from merge-base comparison; blob reads use immutable objects; external diff/textconv are optional mechanisms to disable; replacement/lazy-fetch controls are documented. [diff](https://git-scm.com/docs/git-diff), [cat-file](https://git-scm.com/docs/git-cat-file), [execution controls](https://git-scm.com/docs/git) | Minimum supported installed version/hostile-config matrix needs new boundary tests |
| Anthropic SDK/API | Structured parsing, schema restrictions, refusal/truncation, configurable retries/timeouts and token counting are documented. SDK defaults must be overridden. [SDK](https://github.com/anthropics/anthropic-sdk-python), [structured output](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) | Selected model's quality, account quotas, configured prices and endpoint data policy; trial/eval before release |
| Python/Pydantic | Plain records do not validate annotations; strict boundary models validate response shape. [dataclasses](https://docs.python.org/3/library/dataclasses.html), [strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/) | Actual locked dependency set and compatibility suite at implementation time |
| PR body | Explicit local UTF-8 bytes, digest and supplied origin; no GitHub API required | Approval state/authority is not established by supplying text |
| JSON/Markdown/CI shell | Native report plus exit status; no external state/protocol required | No CI platform integration smoke test yet |
| SARIF/GitHub (deferred) | Uploads are supported; code-security eligibility applies. [official guide](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file) | Annotation/upload behavior not tried; not a v0.1 dependency |

All additional research candidates and license/maintenance caveats live once in [the tool study](plumb-intent-tool-landscape-2026-11-03.md). Confluence, Jira, Linear, Notion, Pond adapters, MCP, hosted auth and webhooks are not current integrations. Future connectors must bring their own permissions, rate/freshness/deletion and source-identity contracts.

## Red-flag screen

Candidates A/B/C are defined once in D01. This screen covers the full `choose-architecture` checklist; “avoided” is a design requirement, not verified running code.

| Flag family | A: local CLI | B: indexed daemon | C: hosted workers |
| --- | --- | --- | --- |
| Distributed monolith / split by layer | Avoided: one deployable | Risk if CLI/daemon releases share internals | Risk if API/worker share mutable models/schema; extra protocol needed |
| Unenforced modules / shared models | Needs CI import check; plain translated boundary data | Needs index ownership and IPC checks | Needs tenant/service data ownership and versioning |
| Ceremony / too many operations | Few functions; no framework | Daemon, schema and recovery exceed current force | Several deployables/stores/queue exceed one-maintainer/local-only force |
| Shallow/chatty/leaky interfaces | One use case; packet/result records | Deep if one submit operation; shallow if index internals leak | Potential deep job interface, but transport adds no present value |
| Framework-shaped core | Avoid by translating SDK/Pydantic at edge | Avoid by not leaking SQL rows | Avoid by not leaking ORM/queue payloads |
| Single-writer / dual-write / exactly-once | Invocation owns derived results; no remote action to replay | Need daemon sole writer, job dedupe/restart rules | Need per-tenant ownership/outbox; no exactly-once assumptions |
| Orphan copy / weak consistency | No persistent copy; pinned inputs | Index freshness/rebuild/version binding required | Connector/index freshness and deletion/permissions propagation required |
| Unguarded calls / resource bounds | Explicit deadline, budget, one shared retry | Same plus finite queue and saturation behavior | Same plus worker isolation, queue age and load shedding |
| Cascading failures / hollow health | No shared server pool/health endpoint | Daemon readiness must test real ability to check | Model/connector failures must not exhaust shared worker pools |
| LLM rules / agent overuse | Deterministic validity/authority policy; fixed sequence | No reason to add an agent | No reason to add one just because hosted |
| Unvalidated/untrusted input | Strict schema and quote binding; no model tools | Same plus IPC/DB input validation | Same plus remote admission/auth and tenant boundaries |
| No eval before build | Contract fixtures and baseline first | Index needs a retrieval eval too | Connector and multitenancy tests beyond current plan |
| Big-bang/target without pain | User explicitly requests new code; small independently testable slices | No measured repeated-index pain yet | Violates explicit no-hosting scope |
| Rollback/dual writes/unprotected seam | New package slices revert; old history preserved | No old/new primary-data dual writes; protect readers first | Source/connector migration must have rollback before reconsideration |
| Endless strangler | No parallel production runtimes | Not selected | Not selected |

## Evaluation design and release evidence

The unit of labeling is a specific claim/code or claim/claim mismatch, with accepted evidence spans and a human-reviewed applicability explanation. Category labels describe deliberately seeded ground truth; unknown-origin real cases measure abstention rather than forcing a winner. Include harmless refactors, a spec intentionally revised with approval, contradictory same-source passages, deleted guards, renamed paths, absent intent, override/exception clauses and prompt injection.

Prepare **200 cases**: 50 code-wrong, 50 spec-stale, 50 sources-conflict and 50 no-drift. Split by source repository/template family: 40 development, 40 calibration and 120 frozen holdout (30/bucket), with no near-duplicate transformations across splits. Include multi-file and doc-only changes in every applicable bucket. Public/synthetic examples avoid importing private project material.

Compare (a) naive same-model diff+docs, (b) validated fixed workflow, (c) workflow with disproof and later retrieval ablations. Give each the same source scope and maximum token/spend budget. Report the deterministic citation filter's effect separately: throwing out invalid outputs can raise precision while harming recall. Freeze prompts, matching rubric, thresholds and exclusions before opening holdout results.

Score finding-level precision/recall, no-drift false-positive rate, per-origin recall/confusion, abstention/incomplete rate, invalid-citation rate, total scope coverage, latency p50/p95/p99 where sample size supports it and provider-reported token/cost classes. Count failed/incomplete cases against end-to-end coverage and end-to-end recall; also show quality conditional on completion. An empty report from a failed call cannot improve precision. With 120 held-out cases, tail latency and per-bucket estimates have wide uncertainty; publish intervals rather than implying production p99 assurance.

Before claiming the complex workflow wins, require NFR4 floors and either >=10 percentage-point recall gain at precision >=0.90 over the baseline, or >=20% cost reduction with precision/recall no more than 2 percentage points lower. These are proposed selection rules, not achieved effects. If the interval includes no improvement, state the comparison is inconclusive and gather more independent cases. Repeat stochastic trials on a budgeted subset, report variation and seed/task identity, and have a human resolve disagreements. LLM grading alone is not the ground truth.

Every prompt/model/schema/tool/retrieval change reruns deterministic boundary tests and the fixed development regression set; a final candidate runs the protected holdout under the frozen protocol. Preserve case manifests, inputs where permitted, raw responses, model/request metadata and scorer output so the published chart can be rerun. Do not repeat the old loss of raw trial evidence.

## Validation performed for this architecture task

- Pond retrieval read the user's actual narrowed intent, not just an old assistant summary.
- Read-only source inventory established coupling and measured-evidence limits; the bounded pattern review scanned four files/all 136 hits and ran 34 existing reference tests.
- Official-source research compared the proposed stack and alternatives; no dependency was installed and no model quality result is claimed.
- A temporary Git fixture on Git 2.54.0 / Python 3.10 verified committed blob identity despite a dirty worktree, citation of a deleted file at base, symlink-target bytes without following the link, and a base/head diff excluding dirty content. The first fixture attempt encountered local commit-signing configuration; the successful isolated run disabled signing/hooks for its temporary commits.
- Final document/reference checks and design review are reported in the task completion. No new product tests, SDK live calls or timing/accuracy benchmarks were run.
