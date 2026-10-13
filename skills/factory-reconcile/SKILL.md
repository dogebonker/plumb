---
name: factory-reconcile
description: Close a finished factory change before it merges - try its examples on the running product, then fold it into .software-factory/system/ - ADRs, standing constraints, the living product and glossary.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory reconcile

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Reconcile runs once, after the last slice is signed off and before the branch merges, so the project's living documents ship with the code they describe. Below, `<change>` is `.software-factory/changes/<slug>` and `<system>` is `.software-factory/system`.

## 1. Load

Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes. Slug empty: use the only change whose slices are all `done` and whose `reconciled` is not `true`; several or none: ask. Read every gate document that is not `skipped`, `challenges.md`, and each `slices/NN/review.md`.

## 2. Acceptance

The agreed examples are tried on the running product by an agent that did not write its code and does not read it. An `acceptance.md` whose `Tried at` commit differs from HEAD only in `.software-factory/` (`git diff --name-only <Tried at> HEAD -- . ':!.software-factory'` is empty) is reused: resume at its unanswered lines, and try again every line answered `defect`.

1. **Examples.** Each FR of the change with its Example line, from `01-product.md` (track small: `04-slices.md`).
2. **Surfaces.** Every module in `lenses.yaml` whose `dev_command` is not `none`: its path, `dev_command` and `dev_url`. A module with an empty `dev_command` (a `lenses.yaml` from before this step): ask the user how a user runs it, and record the command and local URL, or `none` for a library. When no module has a surface, write `<change>/acceptance.md` as "No runnable surface: the tests are the surface." and go on to ADRs (step 3).
3. **Run them.** Each `dev_url` must be local (`localhost`, `127.0.0.1` or `[::1]`); for any other, ask the user for a local one, and never point the agent at a deployed environment. For each server: if `dev_url` already answers, use it and leave it running; otherwise start `dev_command` from the module directory in the background and wait up to 60 seconds for `dev_url`. Stop the servers you started once the agent returns, on every outcome. A CLI (no `dev_url`) goes to the agent as `cd <absolute module path> && <dev_command>`.
4. **Try.** Make a new empty temp directory `<tmp>` outside the repository and write `<tmp>/examples.md`: a `## Surfaces` list (module path, then its URL or CLI command), then the examples. Start one fresh sub-agent. It receives these instructions, nothing else from this conversation:

   > Try every example in `<tmp>/examples.md` on the running product, through the surfaces it lists: a URL in a real browser (Playwright or your browser tools), or over HTTP for an API; a CLI command in the shell. Work only in `<tmp>`. Do not read the product's source, tests or `.software-factory/` folder: judge only what a user of the product sees. Set up each example's input through the product itself. Save screenshots and other evidence files under `<tmp>/evidence/`. Write `<tmp>/acceptance.md` with one line per example: its ID, the surface used, `pass`, `fail` or `not run`, and the evidence (request and response, command and output, or an evidence file and what it shows). `not run` names what stopped you.

   The agent can still reach the repository: the instruction is the firewall.
5. **Record.** Copy the result to `<change>/acceptance.md` under a line `Tried at: <git rev-parse HEAD>`, move the evidence files to `<change>/acceptance/` and rewrite their paths, then delete `<tmp>`. Ask the user about every `fail` and `not run` line at once (headless mode: wait for the user, gates.md), and write each answer on its line:
   - `defect`
   - `wrong example`, with the corrected example, which step 4 uses as the fit criterion
   - `not run accepted`. A `not run` the user can fix (a missing seed, a server that did not start) is tried again first.

   When any line is a defect, send the change back to `slices` once (gates.md, Send back) with the reason `acceptance: <defect IDs>`, and stop. The fixes come as new slices, and reconcile runs again once they are signed off, trying every example again.

Done when every example is `pass` or carries the user's answer, and none is a defect.

## 3. ADRs

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

## 4. Standing constraints

Draft the changes to `<system>/constraints.md`:

- Each FR, NFR and C of the change (from `01-product.md`; track small: `04-slices.md`) becomes the next free `SYS-FR-NN`, `SYS-NFR-NN` or `SYS-C-NN` row: its statement, its fit criterion (the FR's example, or its corrected example in `acceptance.md`, or the NFR's budget from `02-architecture.md`), Source `<slug>`, and Enforced by from the Coverage of `03-interface.md` (track small: the slice that covers it).
- Each SYS row the change listed under Standing constraints gets its Enforced by updated when the change named a concrete test, monitor or check for it.

## 5. Living product and glossary

- `<system>/product.md`: one section per capability the change shipped, titled in the product's words, with the problem in one line and its rules as SYS IDs.
- the design file, when the change touched UI: re-extract its tokens (`design.md diff`), add new screens to the primary-action table, carry new terms into Words, and bump its stamp; principles and positions change only by the user's decision.
- `<system>/layout.md`: the Layout of `02-architecture.md`, merged per module into the existing tree, `Pattern` lines copied verbatim; a folder whose meaning changed is a question for the user, not an overwrite.
- `<system>/glossary.md`: each domain term the product rules and the interface introduced, with a one-line definition in the product's words. An existing term with a new meaning is a question for the user, not an overwrite.

Done when every Decision has an ADR, every change ID has a SYS row, every new term has a glossary line, and every Layout line is in the layout tree, all drafted.

## 6. Calibration and lessons

Your answers to lens findings tune the project's `.software-factory/principles.md`, the last of the principle layers ([../factory-shared/gates.md](../factory-shared/gates.md), Paths).

1. Count, per lens and rule (tags starting with `polish/` are not lens rules and are not counted), how often a finding was accepted (accept, modify, fix) and how often it was rejected (overrule, skip, undone); `auto-fixed` and `auto-skipped` happened without the user's answer and are not counted: in this change's `challenges.md` Responses and the `[lens/rule]` findings and lens cards of its `review.md` files, and in the `.software-factory/changes/*/challenges.md` and `review.md` files of this repository's other changes. Read this change's files from the working tree, and the others from git. Each answer counts once.
2. Draft the changes to the project's `principles.md`:
   - a rule accepted three times or more becomes a principle, with its reason taken from the findings' objections and `Source: <lens>/<rule>`; when the kit or the user layer lists that rule under Quiet rules, this principle takes it out of them for this project (gates.md, Paths)
   - a rule rejected three times or more joins Quiet rules, unless it is a money or security rule (gates.md, Paths)
   - a quiet rule accepted since it went quiet leaves Quiet rules
   - a finding with the same `[lens/rule]` tag, fixed in three changes or more, becomes a lesson: a proposed principle, or a linter rule for the module's language pack (`linter.propose`), which is a proposal for the factory repository
3. **User layer.** Pond (read `schema://pond-sql` first) only finds the other repositories where the factory ran; read their `.software-factory/principles.md` and `.software-factory/system/playbook.md` from each repository's git. Without Pond, skip this step and say so. Draft, for the user to decide one by one:
   - a rule that is a Principle in two or more projects, this change's draft included, and not yet in the user layer: proposed for the Principles of `~/.software-factory/user/principles.md`
   - a rule under Quiet rules in two or more projects, this change's draft included, and not yet in the user layer: proposed for the user layer's Quiet rules, never a money or security rule
   - a playbook entry active in two repositories and seen in three changes or more: a proposed user-layer principle, or a linter rule as a proposal for the factory repository

## 7. Retro

Follow [../factory-retro/SKILL.md](../factory-retro/SKILL.md) for this change. Its drafts join the confirmation below.

## 8. Confirm and write

Show the user every drafted ADR, ADR status change, constraint row, product section, glossary line, layout tree change, principle change and user-layer proposal, and everything retro drafted: `retro.md`, the playbook changes and counters, the environment fixes, proposals for the factory repository and suspicious items. Write them once the user confirms; apply their corrections first. The project's `principles.md` goes into the reconcile commit. An accepted user-layer proposal is written to `~/.software-factory/user/principles.md`, which no repository tracks. Reconcile never edits the framework cache: changes to the factory stay proposals for the factory repository.

## 9. Record

1. Set `reconciled: true` and `notes_for_fresh_session: "Reconciled. Ready to merge."` in `status.yaml`.
2. Committed mode: `git add .software-factory/system .software-factory/changes/<slug>` (the playbook and `retro.md` included), and `.software-factory/principles.md` when it changed, and commit `chore(factory): reconcile <slug>`.
3. Tell the user the change is ready to merge from `<branch>`.
