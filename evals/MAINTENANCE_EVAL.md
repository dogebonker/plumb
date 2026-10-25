# Maintenance evaluation

This supplements the published isolated-feature benchmark. Keep that report unchanged.
Quality dimensions are separate from tokens, dollars and time; do not turn missing
measurements into passes or infer history usefulness from an artifact's existence.

## Executable guarantees

Run `python3 evals/guarantees.py --out <persistent-empty-directory>`.
The stdlib runner executes the existing production guard/ADR regression fixtures and
native archgraph planted-violation checker. Every case retains its exact command,
stdout, stderr, return code and elapsed time. The report fingerprints the production
sources and regression fixtures. Missing archgraph returns `unsupported`, never pass.
The checker includes both conforming and forbidden imports in TS, Python and Go.
Scope, frozen bytes, stale proof, actual tool-write denial and unchanged architecture /
security approval reuse are exercised in disposable fixture repositories. These are
mechanical regression guarantees, not evidence that an actor obeys every instruction.

## Consecutive changes

Use `longitudinal.validate_chain(manifest)` and `longitudinal.run(...)` or:

```
python3 evals/longitudinal.py chain.json
python3 evals/longitudinal.py chain.json --config settings.json --out <persistent-empty-directory> --execute
```

Validation alone makes no model calls. `--execute` explicitly invokes paid actors
through the existing `pr_benchmark.trial` host and requires admitted prepared cases.
The manifest contains `cases` in chronological order and one `shared_context` string
with approved requirements, standing policies, historical decisions and facts given
to every arm. Each case uses the existing PR benchmark schema; adjacent historical
`reference_commit` / `base_commit` values must match. For the initial longitudinal
lane, prepare consecutive Bitxchange Telegram PRs 10 → 11 → 12 and predeclare any
scope limitation before running. Ground-truth implementations remain grader-only.

Each arm receives a distinct persistent workspace, seeded from BASE only once. Later
steps use that arm's candidate, including its retained workflow/history artifacts.
Each step has its own trial artifact directory and fresh verified session identifier;
reused/missing session evidence cannot count as completion. The process halts that
arm after a failed or unverified-correct step, preserves its stopped candidate and
marks remaining steps `not_run_inherited_failure`. It never repairs inherited defects
by copying the historical reference implementation.

Later cases with provided acceptance require `acceptance_overlays`: one
`{path, source, sha256}` per admitted immutable acceptance/support file. Overlays may
only replace those paths. Prepare and freeze these files from approved requirements
before actor execution, outside the actor and framework folders. Each overlay's folder
is denied to every step. Production source, historical implementation, agent decisions
and history cannot be overlaid. The normal trial still denies actor edits and grades
against the admitted immutable files. All arms get identical overlay bytes.

The default report measures delivery and the existing correctness checks. Its existing
cycle-only graph result is retained as raw evidence but **not** promoted to strict
architecture compliance. Architecture, rule compliance and semantic history remain
`unmeasured` until supplied through `score_fn(case, result, workspace)`. That host
returns per-dimension `{verdict: pass|fail|unmeasured, evidence: ...}` receipts; every
measured judgment needs evidence. This callback is a trusted evaluator boundary,
not an automatic semantic proof.

For history, run a fresh follow-up actor, have it extend the previous result against
a predeclared decision-sensitive scenario, and verify its behavior and cited source
lines against the approved decisions. Read-event traces demonstrate access; executable
checks and blind review establish use and accuracy. Keywords or file presence alone
are insufficient. Give all three arms the same historical facts and question target.
For architecture, supply actual standing forbidden-edge/layout rules to the native
checker and retain source/tool/policy bindings. For rule compliance, retain real guard
results. Report blind reviewer identity and coverage; missing judgments stay unmeasured.

The harness records tokens and seconds separately. Before publishing a quality gain,
complete the semantic host judgments and matched blind review; a smoke run of this
harness alone establishes neither a Factory advantage nor production readiness.

Successful candidates receive a local host Git savepoint before the next step.
Approved acceptance overlays receive a separate commit containing only their
pinned paths. These commits preserve each arm's own implementation and history;
they are provenance, not agent completion or approval evidence. Failed candidates
remain untouched. The host rejects unsafe Git metadata, filters, external redirects
and linked overlay destinations before committing or writing.

## Anonymous review and separate scorecards

After trials stop, freeze the normal PR packets, then run an independent reviewer:

```
python3 evals/pr_benchmark.py blind-packets --out STUDY
python3 evals/blind_quality.py run --packet STUDY/blind/ID --out STUDY/judges/ID --model claude-opus-5-5
python3 evals/blind_quality.py export --judges STUDY/judges --out STUDY/native-verdicts.json
python3 evals/pr_benchmark.py blind-verdict --out STUDY --input STUDY/native-verdicts.json
python3 evals/quality_report.py --out STUDY --judges STUDY/judges
```

Review every anonymous packet once. The judge cannot read the arm key, edit files,
run commands or delegate. Its native model/session, packet and evidence citations
are checked; invalid judgments remain missing evidence. Ordinary product and
history docs remain readable. Internal workflow artifacts and Git history are
excluded, so those cannot establish a history pass. Code or ordinary prose may
still suggest the producing method; anonymity is not proof of perfect blinding.

The original PR report owns delivery acceptance. `quality.md` separately reports
provided tests, static correctness, pinned architecture policies, immutable bytes,
semantic history and rules, with measured denominators. No weighted score replaces
the original acceptance rule. A green graph means no new violations under the
supplied policy and parser coverage; it does not erase baseline debt or establish
complete architectural correctness.

Task costs use final cumulative native receipts. Probes and judge calls remain
separate evaluation overhead; incomplete totals stay unknown. Current forwarded
assistant-message streams lack final output-token counts. Finalized persisted
session records can recover per-response counters only with exact session/cwd and
child linkage, finality checks and reconciliation of every token class against the
native totals. Observed intervals following explicit Skill markers remain distinct
from semantic per-skill costs; incomplete linkage stays unattributed. Neither
timestamps nor document access establish model compute time or prove a stage ran.

For future runs, native OpenTelemetry exposes token classes, `query_source` and
`skill.name`, with skill attribution inherited by spawned agents. Validate the
pinned exporter against terminal totals before using those request tags for cost
reporting; they do not establish marginal causal skill cost. This study did not
enable that exporter. See the [native token counters](https://code.claude.com/docs/en/monitoring-usage#token-counter).

The study pins Claude Code 2.1.304. Its successful resumed totals were verified
against two retained chains: prior totals plus new main/child input and cache
usage exactly equal the latest `modelUsage`. This matches the
[documented carryover introduced in 2.1.277](https://code.claude.com/docs/en/agent-sdk/cost-tracking#accumulate-costs-across-multiple-calls).
Summing resumed terminal totals would double-count. Interrupted-process carryover
remains unverified; missing receipts cannot establish zero consumption.
