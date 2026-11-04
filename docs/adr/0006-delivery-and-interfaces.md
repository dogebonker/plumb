# D06 — Small CLI contract and evaluation-led clean-slate delivery

Status: proposed, 2026-11-03.

## Output decision

Options: terminal prose only; one JSON report plus Markdown rendering; SARIF and a custom GitHub application. Select versioned JSON plus Markdown. Both consume the same validated report. `plumb skill` prints static instructions. Shell exit codes suffice for initial CI; no Action-specific runtime, MCP or hosted state.

Force: FR1/FR4/FR5 and NFR4. A failed/incomplete analysis must remain visible to shell callers.

Owner: `release-it/release-it.mini.md`:

> When designing API or integration contracts, make material failure modes explicit, distinguish retryable from non-retryable outcomes, prefer coarse-grained resilient interactions, and document timeout, retry, version, and compatibility expectations.

Exit 0 means a complete review of the declared scope with no retained findings; it is not proof that the code is correct. Exit 1 means complete with findings. Exit 2 is invalid input/configuration/preflight or Git acquisition error. Exit 3 is partial/incomplete review after admitted analysis begins, including model/API failure, with any valid findings preserved. Missing docs, unsupported required files, unresolved substantive intent revisions, failed model phases and undisclosed omissions cannot become exit 0. No-op diffs are a separate complete no-change outcome with zero model calls.

Revisit when a user needs inline code-scanning annotations; SARIF is then another renderer, and its code-location limitations must be respected for pure source conflicts. A dedicated Action follows only if a shell invocation causes real adoption friction.

## Delivery decision and protection

The user explicitly requires a new implementation. This overrides the usual preference for incremental refactoring. Preserve the old revision/tag/branch before later removal work; **this planning task does not create refs or delete files**. There is no obligation to preserve factory APIs in the new CLI.

Owner: `working-effectively-with-legacy-code/working-effectively-with-legacy-code.mini.md`:

> Before editing, state the requested behavior change and the current behavior that must remain; characterize uncertain or suspicious behavior instead of silently fixing it.

What must remain is provenance and useful failure-case evidence, not hooks, gates or runner behavior. Reimplement narrow evidence tests against the new schema. Keep published benchmark limits visible and retain license/attribution for any deliberately copied fixture. Existing installation users get a clear breaking-change note and old-version instructions.

| Slice | Observable completion | Rollback |
| --- | --- | --- |
| 1. Contract + labels | Golden reports and 40 development fixtures, origin/unknown rubric, repository-disjoint holdout plan | Revert new contract/eval artifacts; old product remains untouched |
| 2. Read-only skeleton | Commit-range, deleted/renamed path, odd-name, symlink and dirty-tree checks; Markdown/JSON parity | Revert new package slice; no migration of user data |
| 3. Naive baseline | Reproducible diff+docs run, source/model/prompt identities and measured cost/time | Keep skeleton; remove only provider implementation |
| 4. Validated workflow | Strict citations/relationships and bounded failure tests; raw/validated baseline results retained | Route experimental command back to baseline, clearly versioned |
| 5. Candidate disproof | Ablation demonstrates additional benefit within the same maximum budget | Omit disproof if the simpler workflow wins |
| 6. Experimental release | 200-case report, held-out comparison, real-repo dogfood, reproducible install | Restore previous release/tag; no source/database rollback needed |

No permanent dual implementation lives in the runtime. Baseline and ablations remain evaluation modes, not user-facing provider/workflow choices. An assumed four-week release puts slices 1–2 in week 1, baseline and held-out preparation in week 2, validation/ablations in week 3 and dogfood in week 4. Quality gates take precedence over dates.

Advisory: KISS opposes compatibility machinery without a required caller; the clean-slate instruction settles that tradeoff. Add no background service or connector to fill the schedule.

Revisit release readiness only on fresh held-out measurements. If the workflow does not beat the same-model/same-budget baseline, publish that result and ship the simpler baseline or keep the release experimental; do not claim validated superiority.
