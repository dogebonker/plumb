# Changelog

All notable changes to Software Factory. Dates are when the change landed on `main`.

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
