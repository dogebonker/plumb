# Development simplification results — 14 October 2026

Implemented the independently reviewed cleanup plan. Product/architecture discovery and approval questions remain. Interactive development now dispatches one executor directly, resumes repairable failures, runs one fresh general reviewer with risk specialists, and completes intermediate milestones under the actual approved scope. Final human acceptance/reconciliation is separate. Headless PR approval derivation is unchanged.

The old whole-source rewind and live-production restoration for regression proof are removed. Corrected tests and review regressions overlay exact committed test files into an isolated earlier source checkout with original/corrected hashes, then prove GREEN. Legitimate already-green negative tests retain their expectations with evidence and independent review. No retry-count permission loop. Unknown/missing proof stays visible.

Retaining work required two boundary repairs: original and correction commit spans distinguish each slice's ownership, while final milestone coverage uses the packet union; changed criteria/budgets/contracts/rules invalidate stale downstream evidence even with identical IDs/source. Progress/history metadata is excluded from effective-input fingerprints so normal continuation does not invalidate valid proof.

## Bounded actor evidence

- [OLD exercise](/Users/dan/Work/benchmark-results/development-simplification-20261014/old/.software-factory/changes/exercise/outcome.json): wrong executable keyword required slices send-back/reapproval; no source repair.
- [NEW exercise](/Users/dan/Work/benchmark-results/development-simplification-20261014/new/.software-factory/changes/exercise/outcome.json): zero routine questions; corrected keyword under unchanged contract, kept the negative boundary case, and repaired timestamp preservation with isolated assertion RED and three-test GREEN. Stopped at the genuine return-type conflict. It did not claim independent milestone review or acceptance.
- [Retained-work exercise](/Users/dan/Work/benchmark-results/development-simplification-20261014/retained-repair/outcome.json): real Git A→B→A repair retained B and checked original/correction ownership separately; changed budget at unchanged source/IDs invalidated old receipts; progress/history left the effective projection unchanged, while command/baseline changes invalidated it. [Fresh confirmation against the final policy files](/Users/dan/Work/benchmark-results/development-simplification-20261014/retained-repair/confirmation.json) reran those assertions after the milestone description changed, retaining the original result. This is actor interpretation with real Git/hashes, not automated runtime enforcement of every prompt rule.

The initial exercise accidentally treated an unrelated untracked sentinel as source. New policy correctly stopped without altering it. Both original attempts are retained under `preflight`; the fixture then declared that unchanged sentinel as an ignored exercise artifact for both arms. These attempts are excluded from the routing comparison. No user-file discard was used.

The OLD and NEW timers cover different work and boundaries. Usage/price are unavailable. These exercises establish bounded routing/recovery behavior, not comparable completion-time or cost gains, and not a complete full-stack delivery.

## Verification and independent review

Fresh runtime tests: 12 passed (actual CLI overlays, ancestry/path rejection, executable modes, timeout and staged/dirty/untracked preservation). Existing fixed-browser compatibility tests: 5 passed. Hook, headless runner, review-resume and stage self-checks passed; all stage oracles passed and planted invalid submissions were rejected. Default Ruff, Python syntax, diff checks, the eleven-layout catalog/caller check and SVG XML validation passed.

Independent code review: **APPROVE**, 23 files, no remaining findings. Independent architecture review: **CLEAR** after fixing retained-work ownership, stale gate-input proof, mutable fingerprint loops and FDA public-barrel ordering. The general review count was reduced; its real defect recall still needs a comparable large-task benchmark.

## Remaining limits

- The 2–3× development and 60–90-minute complete-task targets are **unverified**. No new full comparison was launched.
- Completed slices stay edit-protected. Acceptance defects that require a new corrective slice still use the actual slices approval path; this remaining reapproval was not silently bypassed.
- Fixed browser RED requests keep their two-field schema and cannot overlay corrected tests. If no valid committed pre-fix proof can be prepared, report a verification blocker rather than use live GREEN output as RED.
- FDA's first real implementation must calibrate its checker with allowed public imports and forbidden direct/re-export/internal imports, plus the framework build. Catalog checks do not prove a production checker.
- No new dependencies, global writes, commit/push or deployment. Existing benchmark modifications were preserved.
