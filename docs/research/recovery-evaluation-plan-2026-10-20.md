# Factory recovery and engineering-quality evaluation

The user approved all four next steps on 20 October 2026: diagnose representative
failures, implement durable recovery, exercise Factory guarantees, and evaluate
successive changes before repeating the full three-arm comparison.

## Frozen historical result

The 19 October result remains 14/20 bare, 14/20 CLAUDE.md and 9/20 Factory. Neither
its scores nor its acceptance rule will be rewritten. Its private inputs and raw
logs were deleted. All published source commits survive locally, so this study
reconstructs the same twenty PRs with **new calibration**, not an exact replay of
the deleted run. Any test-scope/input difference is disclosed.

## Execution order

1. Reconstruct the published corpus from PR metadata and local Git objects; prove
   supplied acceptance is feature-RED on base and GREEN on the actual PR. Keep
   actual implementations hidden from actors. Do not replace tasks after outcomes.
2. Add opt-in timestamped native receipts and an offline diagnostic report. Fixed
   diagnostic tasks: goldengate-1038, limitless-4798, bot-10, limitless-4795. Run the
   Factory arm first for diagnosis; these four runs do not establish superiority.
3. Complete same-directory durable v2 recovery. Preserve genuine approval, exact
   source/tool/policy bindings, accepted commits, attempt/review counts, native
   session, elapsed and spent budgets. A second run directory cannot reset them.
   Ambiguous pending native work or interrupted mutation stays held with evidence.
4. Execute actual guard/enforcement fixtures: conforming and violating imports,
   cycles, ADR conflicts/enforcement, scope/frozen-scenario writes, stale proof and
   unchanged architecture/security approval reuse. Report limitations explicitly.
5. Execute a maintenance chain on the consecutive real bot PRs 10 -> 11 -> 12.
   Every arm starts from the same base and receives the same approved requirements,
   standing constraints and initial historical facts. Each subsequent step uses
   that arm's own previous implementation and a fresh agent session. Never restore
   a failed arm from the historical reference. Score cumulative behavior and use
   of prior decisions separately from completion. Inherited failures stay visible.
6. Run all twenty cases in the same three arms against a final frozen framework
   and controller snapshot, then obtain anonymous independent judgments. Reuse a
   diagnostic run only if every treatment/input/budget binding is identical; any
   relevant fix requires a fresh run. Never select a favorable attempt.

## Fair comparison and scoring

- Model: explicit `claude-opus-5-5`, same effort and subagent model for every arm.
- Give each arm identical task facts, immutable acceptance, standing policy and
  historical evidence. Only CLAUDE.md guidance and Factory machinery differ.
- Predeclare treatment: the historical PR harness drives the default skills,
  not the experimental v2 controller. V2 crash recovery is tested separately;
  passing it is not evidence of improved default-Factory feature delivery.
- Record whether full Factory edit hooks actually run. A skills-only experiment
  cannot establish hook enforcement. Synthetic operator replies apply only to
  isolated benchmark repositories; they grant no production authority.
- Keep comparable delivery acceptance, provided tests, independent correctness
  review, architecture policy/cycles, strict-rule compliance, history usefulness,
  tokens and wall time as separate columns. No weighted score is invented.
- The historical comparable delivery target stays +10 percentage points over
  the good-CLAUDE.md control. Additional quality findings are reported separately;
  costs and time are not a quality-margin ceiling.
- Preserve shared execution guards; retain stopped artifacts and score their code
  independently without promoting unfinished work to completed delivery.
- Native root totals include children. Resume accounting uses cumulative deltas;
  unknown usage is not zero. Observed log receipt times are not model compute time.
- Blind judgment must come from a reviewer that has not seen arm identities or
  scores. Require concrete evidence; missing integration/history proof is unknown.

## Evidence and completion

Private sources, actor clones, logs and review keys live under
`~/.local/state/software-factory/recovery-evaluation-20261020/`, outside `.tmp`.
Controllers retain their own source/framework/tool hashes. Preserve earlier work
in this repository and do not publish private source or conversations.

Done means implemented recovery with crash regressions, executed guarantee report,
four-task diagnostic report, real maintenance-chain results and a fresh twenty-task
three-arm table with independent review. A harness alone is not completion. No
application deployment or final feature merge is part of this evaluation.
