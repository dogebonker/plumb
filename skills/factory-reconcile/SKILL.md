---
name: factory-reconcile
description: Close a finished factory change before it merges - try its examples on the running product, then fold it into .factory/system/ - ADRs, standing constraints, the living product and glossary.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory reconcile

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Reconcile runs once, after the last slice is signed off and before the branch merges, so the project's living documents ship with the code they describe. Below, `<change>` is `.factory/changes/<slug>` and `<system>` is `.factory/system`.

## 1. Load

Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes. Slug empty: use the only change whose slices are all `done` and whose `reconciled` is not `true`; several or none: ask. Read every gate document that is not `skipped`, `challenges.md`, and each `slices/NN/review.md`.

## 2. Acceptance

The agreed FR examples and applicable NFR fit criteria (including touched standing SYS-NFR promises) are independently verified on the running product by an agent that did not write its code and does not read it. An `acceptance.md` whose `Tried at` commit differs from HEAD only in `.factory/` (`git diff --name-only <Tried at> HEAD -- . ':!.factory'` is empty) may be reused only for lines whose recorded example/fit criterion still matches the current approved documents and whose evidence remains applicable. Build the complete current ID list first: newly applicable IDs and older lines without a recorded criterion must be verified, even at unchanged source HEAD. Resume unanswered lines and retry every line answered `defect`.

1. **Examples and promises.** Each FR with its Example line, from `01-product.md` (track small: `04-slices.md`), and each applicable NFR/SYS-NFR fit criterion from `02-architecture.md` and the standing registry, with its verification procedure from `03-interface.md`. Include the agreed failed-write, recovery and interleaved-writer sequences for saved user data. Retain their IDs; an NFR is not implicitly passed by green FR tests.
2. **Surfaces.** Every module in `lenses.yaml` whose `dev_command` is not `none`: its path, `dev_command` and `dev_url`. A module with an empty `dev_command` (a `lenses.yaml` from before this step): ask the user how a user runs it, and record the command and local URL, or `none` for a library. When no module has a surface, use the existing test/check commands as the verification surface: the independent agent runs the mapped checks without inspecting implementation. Record their command/output for each applicable ID; unavailable checks are `not run`, not automatic passes.
3. **Run them.** Each `dev_url` must be local (`localhost`, `127.0.0.1` or `[::1]`); for any other, ask the user for a local one, and never point the agent at a deployed environment. For each server: if `dev_url` already answers, use it and leave it running; otherwise start `dev_command` from the module directory in the background and wait up to 60 seconds for `dev_url`. Stop the servers you started once the agent returns, on every outcome. A CLI (no `dev_url`) goes to the agent as `cd <absolute module path> && <dev_command>`.
4. **Try.** Make a new empty temp directory `<tmp>` outside the repository and write `<tmp>/examples.md`: a `## Surfaces` list (module path, then its URL or CLI command), then the examples and promise fit criteria with their verification procedures. A prepared browser capability with a fixed workspace and writable roots instead uses a fresh `<repo>/.tmp/acceptance-<unique>/` directory. Pass its exact argument-free `test_command`, the installed browser module path and the local surfaces in `examples.md`. If that command only discovers root `test*.cjs`, reserve one new `<repo>/test_acceptance_<unique>.cjs` for this independent agent; never overwrite an existing file. Start one fresh sub-agent. It receives these instructions, nothing else from this conversation:

   > Verify every FR example and applicable NFR/SYS-NFR fit criterion in `<tmp>/examples.md` on the running product, through the surfaces it lists: a URL in a real browser (Playwright or your browser tools), or over HTTP for an API; a CLI command in the shell. Work only in `<tmp>`. Do not read the product's source, tests or `.factory/` folder: judge only what a user of the product sees. Set up each example's input through the product itself. For a failure criterion, inject failure into the named actual dependency using its approved local procedure (for example browser storage, not HTTP for a local-only app). If that procedure is unavailable or a monitor requires an observation window you cannot collect, record `not run` with the missing evidence. Do not infer a promise passes from a happy-path screenshot. Save screenshots and other evidence files under `<tmp>/evidence/`. Write `<tmp>/acceptance.md` with one line per FR example or NFR fit criterion: its ID, the exact example/fit criterion checked, the surface used, `pass`, `fail` or `not run`, and the evidence (request and response, command and output, or an evidence file and what it shows). `not run` names what stopped you.

   For the prepared-browser branch, append only this capability instruction. An edit-hook rejection of the reserved script is `not run`; do not reopen signed-off slices or bypass hooks to obtain acceptance evidence.

   > Author your independent browser checks in the reserved `<repo>/test_acceptance_<unique>.cjs`; this is the sole file you may write outside `<tmp>`. Use the supplied installed browser module and local URL, then invoke the exact argument-free `test_command` directly. It also runs existing workspace checks: attribute each acceptance result only to the independent checks you authored and their evidence, not to unrelated green tests. Store screenshots under `<tmp>/evidence/`. Do not inspect implementation, existing tests or `.factory/`. If the capability cannot execute your check or collect its evidence, record `not run`.

   The agent can still reach the repository: the instruction is the firewall.
5. **Record.** Remove only the reserved acceptance script you created, on every outcome. Copy the result to `<change>/acceptance.md` under a line `Tried at: <git rev-parse HEAD>`, move the evidence files to `<change>/acceptance/` and rewrite their paths, then delete `<tmp>`. Ask the user about every `fail` and `not run` line at once (headless mode: wait for the user, gates.md), and write each answer on its line:
   - `defect`
   - `wrong example`, with the corrected example, which step 4 uses as the fit criterion
   - `not run accepted`. A `not run` the user can fix (a missing seed, a server that did not start) is tried again first.

   When any line is a defect, send the change back to `slices` once (gates.md, Send back) with the reason `acceptance: <defect IDs>`, and stop. The fixes come as new slices, and reconcile runs again once they are signed off, trying every example again.

Done when every current FR example and applicable NFR/SYS-NFR fit criterion has its own evidence and is `pass` or carries the user's answer, and none is a defect.

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

Your answers to lens findings tune the kit's `~/.software-factory/principles.md`.

1. Count, per lens and rule (tags starting with `review/` are not lens rules and are not counted), how often a finding was accepted (accept, modify, fix) and how often it was rejected (overrule, skip, undone); `auto-fixed` and `auto-skipped` happened without the user's answer and are not counted: in this change's `challenges.md` Responses and the `[lens/rule]` findings and lens cards of its `review.md` files, and in the `.factory/changes/*/challenges.md` and `review.md` files of this repository's other changes and of every other repository where the factory ran. Read this change's files from the working tree, and the others from each repository's git; Pond (read `schema://pond-sql` first) only finds the repositories, because the files are often written in pieces that no single tool call holds. Each answer counts once.
2. Draft the kit changes:
   - a rule accepted three times or more becomes a principle, with its reason taken from the findings' objections
   - a rule rejected three times or more joins Quiet rules, unless it is a money or security rule as `principles.md` defines
   - a quiet rule accepted since it went quiet leaves Quiet rules
   - a finding with the same `[lens/rule]` tag, fixed in three changes or more, becomes a lesson: a proposed principle, or a linter rule for the module's language pack (`linter.propose`)
   - a playbook entry active in two repositories' `.factory/system/playbook.md` and seen in three changes or more becomes a proposed principle or linter rule the same way
3. Without Pond, count this repository's changes only, and say so.

## 7. Retro

Follow [../factory-retro/SKILL.md](../factory-retro/SKILL.md) for this change. Its drafts join the confirmation below.

## 8. Confirm and write

Show the user every drafted ADR, ADR status change, constraint row, product section, glossary line, layout tree change and kit change, and everything retro drafted: `retro.md`, the playbook changes and counters, the environment fixes, proposals for the factory repository and suspicious items. Write them once the user confirms; apply their corrections first. Kit changes are committed in the factory repository (`~/.software-factory` links into it), staging only the files reconcile changed, and pushed only when the user asks.

## 9. Record

1. Set `reconciled: true` and `notes_for_fresh_session: "Reconciled. Ready to merge."` in `status.yaml`.
2. Committed mode: `git add .factory/system .factory/changes/<slug>` (the playbook and `retro.md` included) and commit `chore(factory): reconcile <slug>`.
3. Tell the user the change is ready to merge from `<branch>`.
