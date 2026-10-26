# Changelog

All notable changes to Plumb, named Software Factory before October 2026. Dates are when the change landed on `main`. Entries before the rename keep the old names.

## Unreleased

- Wire pinned archgraph context and regression evidence into build, milestone review, standalone review and setup through one shared CLI adapter; preserve source/scope bindings, explicit gaps and existing stack checkers.

### Added
- Standalone `factory-code-review`: polish lenses, bundled defect scanners/checklist, Factory intent/ADR/contract checks, local and PR modes, and explicitly authorized follow-through.
- ADR enforcement, draft-only conformance, report-only drift and M12 defect-origin attribution; pinned archgraph checks and bounded review context for TypeScript, Python and Go.
- Experimental v2 slice contracts, one isolated implementation clone, mechanical gates, bounded independent Opus review, metrics and an optional budgeted post-integration replanning checkpoint.
- Signed GitHub/Linear webhook intake and a durable queue for the existing headless runner, with structured progress, coalescing and conservative failure recovery. Live subscriptions and automatic v2 queue recovery remain integration work.
- Durable v2 host-API recovery with an atomic checkpoint, chained journal, original approval/runtime bindings and preserved usage, sessions, retry counts and accepted commits. Crash regressions pass; live provider restart recovery remains unvalidated.
- Post-merge defect, recovery and adoption reporting, plus evidence-backed skill deprecation proposals. Unmerged or unobserved outcomes remain unknown.
- Historical 20-PR benchmark results, protocol and harness; quality remains separate from cost/time, with the deleted raw-evidence limitation retained. Extended evaluation adapters and fixtures include explicit accounting/isolation limitations.

### Fixed
- Resume approved stages without redrafting, enriching or asking architecture/security approval again; supplemental evidence stays separate and pending-only plan approval preserves earlier approvals.
- The edit hook freezes approved gate documents and the current change's approved threat model, while permitting exact-byte writes/restores and pending drafts. Hash validation and headless approval provenance remain intact.
- Interactive interface/product corrections retain unchanged compatible architecture/security approvals after a focused impact check, instead of forcing every later gate through approval again. Affected tests and reviews still rerun; headless snapshot rules stay intact.

### Changed
- Renamed Software Factory to Plumb: `/factory-*` skills are `/plumb-*`, project state moves from `.software-factory/` to `.plumb/` with `factory.lock` becoming `plumb.lock`, the machine cache is `~/.plumb/`, new branches start `plumb/`, `FACTORY_*` variables are `PLUMB_*`, and the repository is `plumb`. `/plumb-init` repoints an old `factory_gate.py` hook entry and migrates the project with `bin/plumb-migrate`, which refuses while an old hook entry, a worktree under the old folder or both old folders remain; until then the hook keeps gating its unreconciled changes and freezes its gate documents, and the runner still serves `factory/` branches. Runner state under `.git/factory-*` is not read after the rename, so finish headless and v2 runs first. The `factory:design-schema` stamp, `factory/<name>` principle tags and `factory_*` keys in `status.yaml` keep their names, since existing projects hold them. Historical research, pilots and decisions keep the old names, as does the benchmark's `factory` arm.
- Slice execution now uses a persistent Opus 5.5 lead with bounded native Opus subagents, including parallel subtasks when useful, with separate review after mechanical gates before advancing slices. The prescribed Sonnet swarm and parallel worktree pool are removed. The v2 native adapter explicitly resumes the same session and accounts cumulative lead and helper usage as deltas. New plans omit the Opus share ceiling; explicit ceilings on already-approved plans remain binding. Native execution and improved quality/cost are not yet demonstrated.
- Design books now require explicit task-local opt-in. Small/medium tasks default to no book reads or panels; large tasks may recommend one lens in the existing approval summary. Selected excerpts are size-capped and reuse the general reviewer; APoSD no longer automatically spawns a reviewer, and Refactoring.Guru/pattern maps are not baseline loads.
- Provider-backed per-task/per-skill token receipts and reports replace guessed token budgets. The headless runner captures raw usage outside the harness clone even on failure; resumes and child rollups are deduplicated, and unknown attribution stays visible. No claimed dollar savings without measured evidence.
- New standard interactive approvals authorize bounded repair/review/acceptance rounds until required proof passes or a real blocker remains. Completed stages advance automatically; actual decision changes and final sign-off still return to the user.
- Pre-build questions use everyday wording, a short goal/decided recap and a concrete scenario describing the person's steps before asking what they should see or do next. Inline behavior diagrams, access tables or screen previews appear by default. Recommendations include drawbacks and simple answer labels; existing question rounds, rendering budgets and approval boundaries remain unchanged.

## 2026-10-15

### Added
- **Fast lane for track standard.** New `/factory-plan` skill: at most two batched rounds of discovery questions from a fixed checklist (users and roles, who may see or do what, data lifecycle, failure and durability, vocabulary, brand voice and where it must stay plain, visual direction and quality bar, non-goals), then all planning documents, the design file and one representative mockup, approved once. Slice 01 builds first, then independent slices build red then green in parallel, one executor each in its own git worktree, merged back with one check per group; one review at the end runs alongside independent acceptance; reconcile follows. Target: a small multi-user web app in 60 to 90 minutes.
- **Named principles.** `kit/principles.md` defines DRY, SOLID, YAGNI and KISS, each with a test a reviewer applies to the diff, and the order when they conflict. Review tags findings against them as `factory/<name>`.
- **Gang of Four map.** A Factory-written `gang-of-four` pack maps smells to patterns, with when each fits and the smaller treatment otherwise. Review reads it only when a finding names one of its smells.

### Changed
- **Track critical** now means money, changes to an existing sign-in or permission system, or migrations of existing stored data. A new product's first sign-in is standard, with a `## Threats` section and a mandatory security reviewer.
- `ui-hard-gate` H12: tone follows the design file's Voice; neutral only when the design file has none.
- Headless standard runs keep the per-gate pull-request route; critical and small tracks are unchanged.

## 2026-10-14

### Added
- Review of milestone N while milestone N+1 builds.
- Autonomous local Factory development and bundled book rubrics in `kit/packs/`.
