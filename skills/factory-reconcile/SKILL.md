---
name: factory-reconcile
description: Fold a finished factory change into .factory/system/ - ADRs, standing constraints, the living product and glossary - before it merges.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory reconcile

Slug: $ARGUMENTS

Reconcile runs once, after the last slice is signed off and before the branch merges, so the project's living documents ship with the code they describe. Below, `<change>` is `.factory/changes/<slug>` and `<system>` is `.factory/system`.

## 1. Load

Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes: the work is a change whose slices are all `done` and whose `reconciled` is not `true`. Read every gate document that is not `skipped`, `challenges.md`, and each `slices/NN/review.md`.

## 2. ADRs

Each entry under Decisions in `02-architecture.md` and `03-interface.md` becomes `<system>/adr/NNNN-<kebab-title>.md`, numbered after the highest existing one:

```markdown
# NNNN <title>

Status: accepted
Change: <slug>
Context: <from the entry>
Decision: <from the entry>
Consequences: <from the entry>
```

An entry that supersedes an earlier ADR sets that ADR's Status to `superseded by NNNN`.

## 3. Standing constraints

In `<system>/constraints.md`:

- Each FR, NFR and C of the change (from `01-product.md`; track small: `04-slices.md`) becomes the next free `SYS-FR-NN`, `SYS-NFR-NN` or `SYS-C-NN` row: its statement, its fit criterion (the FR's example or the NFR's budget from `02-architecture.md`), Source `<slug>`, and Enforced by from the Coverage of `03-interface.md` (track small: the slice that covers it).
- Each SYS row the change listed under Standing constraints gets its Enforced by updated when the change named a concrete test, monitor or check for it.

Show the new and changed rows to the user before writing them.

## 4. Living product and glossary

- `<system>/product.md`: one section per capability the change shipped, titled in the product's words, with the problem in one line and its rules as SYS IDs.
- `<system>/glossary.md`: each domain term the product rules and the interface introduced, with a one-line definition in the product's words. An existing term with a new meaning is a question for the user, not an overwrite.

Done when every Decision has an ADR, every change ID has a SYS row, and every new term has a glossary line.

## 5. Record

1. Set `reconciled: true` and `notes_for_fresh_session: "Reconciled. Ready to merge."` in `status.yaml`.
2. Committed mode: `git add .factory` and commit `chore(factory): reconcile <slug>`.
3. Tell the user the change is ready to merge from `<branch>`.
