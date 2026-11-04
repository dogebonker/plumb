# OpenProse for Plumb: read-only investigation

Checked 2026-11-04. No installation, execution, model CLI calls, or benchmarking.

## Question

Does OpenProse provide useful reusable workflow execution for a skill-first,
spec-driven Plumb, and would adopting it replace the small Python checks?

## Ranked synthesis

| Rank | Conclusion | Confidence | Basis |
| --- | --- | --- | --- |
| 1 | Start with the existing host agent and one Plumb skill | High for the smaller footprint; usefulness unproven | Current Plumb checks already exist; the next missing evidence is real workflow reuse |
| 2 | OpenProse can be an optional workflow authoring format | Medium for Plumb fit | The language has composable contracts and host-executed sessions, but no host conformance test ran here |
| 3 | Reactor is a separate runtime to evaluate if scheduling/recovery becomes necessary | High about its existence; low about Plumb integration | Executable runtime, alpha maturity, different version and provider integration assumptions |

## Evidence

Canonical repositories are [openprose/prose](https://github.com/openprose/prose)
and [openprose/reactor](https://github.com/openprose/reactor).

The inspected Prose commit is
[0ab7237ced4ac29ca002c94878e69c5cbf6b1ea6](https://github.com/openprose/prose/tree/0ab7237ced4ac29ca002c94878e69c5cbf6b1ea6).
The skill declares version 0.18.1/runtime contract 2. Its commands are interpreted
by a compatible coding-agent host. The host supplies tools, session isolation,
and questions. Contract and ProseScript semantics support session composition,
loops, persistence, and retries. [Skill and host adapter](https://github.com/openprose/prose/blob/0ab7237ced4ac29ca002c94878e69c5cbf6b1ea6/skills/open-prose/SKILL.md#L127),
[ProseScript](https://github.com/openprose/prose/blob/0ab7237ced4ac29ca002c94878e69c5cbf6b1ea6/skills/open-prose/prosescript.md#L295).

Reactor commit
[510af626c2a3a887124b8fe12214f7112633d4dd](https://github.com/openprose/reactor/tree/510af626c2a3a887124b8fe12214f7112633d4dd)
contains a real deterministic orchestration runtime. The SDK is 0.3.3 and CLI
package 0.2.4. Its README describes alpha status and a vendored skill at 0.15.0,
so compatibility with the newer skill is not established here. Both inspected
projects are MIT licensed. [Reactor README](https://github.com/openprose/reactor/blob/510af626c2a3a887124b8fe12214f7112633d4dd/README.md#L1).

Reactor's inspected async drain runs nodes serially. Failure retains prior
published state and emits receipts, which does not demonstrate rollback of tools'
external side effects. [Drain](https://github.com/openprose/reactor/blob/510af626c2a3a887124b8fe12214f7112633d4dd/packages/reactor/src/reactor/index.ts#L772),
[failure handling](https://github.com/openprose/reactor/blob/510af626c2a3a887124b8fe12214f7112633d4dd/packages/reactor/src/reactor/index.ts#L949).

Built-in CLI providers use model APIs. Reuse of the existing Claude CLI login
and subscription is unverified. Turn limits and cost observations do not establish
hard whole-change dollar/token enforcement. [Provider](https://github.com/openprose/reactor/blob/510af626c2a3a887124b8fe12214f7112633d4dd/packages/reactor-cli/src/model/live-provider.ts#L15),
[render backend](https://github.com/openprose/reactor/blob/510af626c2a3a887124b8fe12214f7112633d4dd/packages/reactor/src/adapters/agent-render/render-backend.ts#L104).

## Inference

OpenProse could package a proven Plumb workflow across projects. It would describe
execution rather than replace OKF knowledge, source-version checks, citation
validation, or the host's real permissions. A reusable plain skill already offers
a smaller first experiment. Adopt another format when it solves an observed
composition or execution problem, not merely because the work has several steps.

## Unknowns and next probe

Host compatibility, reliable question/resume behavior, aggregate cost enforcement,
side-effect deduplication, and resource use remain untested. After a real workflow
works on two projects, compare a pinned OpenProse version against the plain skill.
Require serial execution, resolved inputs/outputs, separate review context, a
real decision checkpoint, persisted evidence, and resume without repeated writes.
Do not infer correctness from a workflow's declared postconditions.
