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

Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes. Slug empty: use the only change whose slices are all `done` and whose `reconciled` is not `true`; several or none: ask. Read every gate document that is not `skipped`, `challenges.md`, and each `slices/NN/review.md`.

## 2. ADRs

Draft each entry under Decisions in `02-architecture.md` and `03-interface.md` as `<system>/adr/NNNN-<kebab-title>.md`, numbered after the highest existing one:

```markdown
# NNNN <title>

Status: accepted
Change: <slug>
Context: <from the entry>
Decision: <from the entry>
Consequences: <from the entry>
```

An entry that supersedes an earlier ADR also drafts that ADR's Status change to `superseded by NNNN`.

## 3. Standing constraints

Draft the changes to `<system>/constraints.md`:

- Each FR, NFR and C of the change (from `01-product.md`; track small: `04-slices.md`) becomes the next free `SYS-FR-NN`, `SYS-NFR-NN` or `SYS-C-NN` row: its statement, its fit criterion (the FR's example or the NFR's budget from `02-architecture.md`), Source `<slug>`, and Enforced by from the Coverage of `03-interface.md` (track small: the slice that covers it).
- Each SYS row the change listed under Standing constraints gets its Enforced by updated when the change named a concrete test, monitor or check for it.

## 4. Living product and glossary

- `<system>/product.md`: one section per capability the change shipped, titled in the product's words, with the problem in one line and its rules as SYS IDs.
- `<system>/glossary.md`: each domain term the product rules and the interface introduced, with a one-line definition in the product's words. An existing term with a new meaning is a question for the user, not an overwrite.

Done when every Decision has an ADR, every change ID has a SYS row, and every new term has a glossary line, all drafted.

## 5. Calibration and lessons

Your answers to lens findings tune the kit's `~/.software-factory/principles.md`.

1. Count, per lens and rule, how often a finding was accepted (accept, modify, fix) and how often it was rejected (overrule, skip): in this change's `challenges.md` Responses and the `[lens/rule]` findings and lens cards of its `review.md` files, and, through Pond (read `schema://pond-sql` first), in every `challenges.md` and `review.md` the factory wrote for other changes, in this project or any other. Each answer counts once: leave this change's own files out of the Pond count.
2. Draft the kit changes:
   - a rule accepted three times or more becomes a principle, with its reason taken from the findings' objections
   - a rule rejected three times or more joins Quiet rules, unless it is a money or security rule as `principles.md` defines
   - a quiet rule accepted since it went quiet leaves Quiet rules
   - a finding with the same `[lens/rule]` tag, fixed in three changes or more, becomes a lesson: a proposed principle, or a linter rule for the module's language pack (`linter.propose`)
3. Without Pond, count this change's files only, and say so.

## 6. Confirm and write

Show the user every drafted ADR, ADR status change, constraint row, product section, glossary line and kit change. Write them once the user confirms; apply their corrections first. Kit changes are committed in `~/.software-factory`, staging only the files reconcile changed, and pushed only when the user asks.

## 7. Record

1. Set `reconciled: true` and `notes_for_fresh_session: "Reconciled. Ready to merge."` in `status.yaml`.
2. Committed mode: `git add .factory/system .factory/changes/<slug>` and commit `chore(factory): reconcile <slug>`.
3. Tell the user the change is ready to merge from `<branch>`.
