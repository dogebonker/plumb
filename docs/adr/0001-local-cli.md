# D01 — One local CLI, Python, no service runtime

Status: proposed, 2026-11-03.

## Options

**A: Local modular CLI, selected.** One installed package/process. Intent/evidence, review, source reading and presentation are modules in one deployable. Git/supplied bytes own source truth; the invocation owns derived results. Function calls are synchronous; only model requests cross a network. Failure returns a bounded incomplete/error report. LLM work is a fixed workflow.

**B: Local index plus background worker.** A daemon owns a SQLite source/claim index and work queue; a CLI submits checks. Inputs still belong to Git; derived records have one daemon writer. IPC/jobs require versioning, duplicate handling, recovery and freshness checks; model failures remain job outcomes. This could serve repeated large-repo checks, but the current forces do not justify installation, lifecycle and stale-index complexity.

**C: Hosted application plus workers.** An API owns tenants/review records; workers receive jobs; a transactional outbox would link database state to dispatch. Webhooks import GitHub/docs and models review asynchronously. Timeouts, tenant isolation and retries become service concerns. It requires credentials and source uploads beyond the local command's scope. No team/availability force warrants these deployables; the user explicitly excluded hosting.

## Deployment decision

Force: FR1/FR5 and NFR1/NFR7; one maintainer, no service operations, bounded local checks. Capacity is dominated by context and external inference (see appendix), not CPU throughput.

Owner: `release-it/release-it.mini.md`:

> Prefer designs that fail visibly, limit blast radius, shed load, preserve core service, and make diagnosis possible over designs that maximize coupling or ideal-path elegance.

Advisory: DDIA favors explicit recoverable derived state when it exists; here recomputation and a report suffice. No queue is created.

Revisit when repeated-source reads exceed the measured local preparation target, or a real user requires concurrent/background checks with retained history. That reopens B before C.

## Language decision

Use Python >=3.10, `argparse`, standard-library JSON/path/process facilities, a small plain core, Pydantic for the external schema boundary and the official Anthropic SDK. Lock tested dependency versions at implementation time. This is a CLI, not a Python HTTP backend; FastAPI does not apply.

Options: Python; TypeScript/Bun/Effect; Go; Rust. Python matches the existing local runtime and avoids a new execution/toolchain requirement. It can express the proposed CPU-light workflow directly. The SDK supports this runtime; see the linked [tool study](../research/plumb-intent-tool-landscape-2026-11-03.md).

Owning house rule, `choose-architecture/references/stack.md`:

> A deployable no rule covers: pick by the Team force (what the team already runs in production) and label the choice "not a house rule".

This choice is **not a house rule** and the Team force remains an assumption. Bun/Effect is the house TypeScript-backend choice, but no backend is proposed. Go's CPU/parallel capacity trigger has not been met. Revisit if the user's required stack differs, cold-start/distribution measurements fail, or a measured CPU bottleneck survives simpler fixes.
