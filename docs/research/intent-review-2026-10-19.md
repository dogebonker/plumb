# Intent review implementation and bounded exercise — 2026-10-19

Implemented accepted ADR anchors/enforcement, draft-only conformance, pinned archgraph context/checks, report-only reconciliation drift and retro M12. Decisions 44–48 record the authority and cost boundaries.

The existing hook, runner and review-resume assert suites passed before prompt edits and again afterwards. No hook, runner, workflow state, benchmark harness or pack pin changed for this work. New stdlib ADR helper regressions were written before implementation; four independently reproduced boundary cases were also observed failing before correction.

| Check | Result |
| --- | --- |
| Existing hook suite, including correction scope | pass, unchanged |
| Existing runner suite | pass, unchanged |
| Existing review-resume suite | pass, unchanged |
| ADR executable regressions | 13 pass |
| Archgraph TS / Python / Go clean fixtures | each exit 0 |
| Archgraph TS / Python / Go planted import violations | each exit 1, named rule and planted file |
| Archgraph context / reverse-import impact / observed export addition | pass at published pin |
| Incorrect binary hash / missing installation | reject / explicit skip with install line |
| Ruff, Python compilation, shell syntax, diff whitespace | pass |

ADR regressions cover missing named definitions, failed/unavailable commands, legacy enforcement, drift output and held evidence, unknown Covers IDs, stale/wrong citations, pending-only draft edits, same-Decision supersession, fenced examples, small-track routing, report aliases and output redirection after commands. A named check's definition is checked lexically at HEAD; its semantic mapping to a command remains a conductor responsibility. Commands are explicitly supplied from trusted configuration, never executed from ADR prose. The helper is not a sandbox.

## Reviewer exercise

One fresh `claude-opus-5-5` call, low effort, no tools/MCP, no design lenses, using the current general-review rubric plus the accepted-ADR anchor rule. Both complete tiny file revisions were provided as independent cases. A human-verified ADR 0007 requires integer minor-unit amounts and forbids float conversion. No Factory skill or whole product run was simulated by a scripted answerer.

| Candidate | Changed behavior | Observed finding |
| --- | --- | --- |
| A | `sum(float(amount) for amount in amounts)` | Cited `[adr/0007]`, line 2, explaining the contradictory conversion and precision loss |
| B | `sum(amount for amount in amounts)` | No finding |

Both cases reported complete `money.py` coverage. The actor's raw JSON self-labelled A `block`; the existing general-review report mapping remains `fix` for a fix recommendation, with `block` reserved for lens cards. This exercise establishes anchor citation and silence on this example, **not** severity-routing or full-workflow correctness.

| Provider observation | Value |
| --- | ---: |
| Calls | 1 |
| Uncached input | 2 |
| Cache read | 0 |
| Cache creation | 6,466 |
| Output | 209 |
| Total tokens, disjoint classes | 6,677 |
| Native CLI list cost | $0.055916 |
| Wall time | 3.878 s |
| Exercise spending ceiling | $0.50 |

The call is attributed to `factory-review` through the existing usage receipt helper. These are this actor's provider counters, not the entire implementation's cost or an invoice. No measured savings or generalized review-quality improvement is claimed.

Durable raw evidence: `/Users/dan/.local/state/software-factory/intent-review-20261019/` contains the exact prompt/packet, native stream, execution metadata, usage receipt, checker evidence and summary hashes. This sits outside disposable workspace `.tmp`.

## Deliberate limits

Standard planning has no fresh reviewer to reuse. To preserve the requested no-additional-standard-call constraint, it uses the existing planning invocation's bounded semantic read of the scripted inventory instead of the proposed extra fresh conformance agent. Critical planning retains its fresh read/reuse route. The independent post-build general review remains unchanged in count. Human-only drift uses a fresh read within the existing reconcile allocation; old guessed 6M budgets remain retired.

Archgraph uses published source pin `49464a7ec19fe8402b4258e751f7ba050c6eff19`, verified by remote Git and built from a pristine archive with locked dependencies. The tested macOS arm64 binary SHA-256 is `3a5a71510a1f4fd44827079b22359615be9e9828eb263811eaa26b25dc3af733`. Native TS surface coverage was incomplete even on a small ESM fixture: positive observed additions can inform opted-in review, but negative results require the documented fallback. Plain `check` does not fail cycles/unplanned edges; graph `diff` is required.

No complete feature/reconcile actor run, live monitor observation, historical M12 attribution series, or unrelated checker installations were run. No global/project ADRs were migrated and no product branch was merged or published.
