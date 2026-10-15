---
name: factory-reconcile
description: Close a finished factory change before it merges - try its examples on the running product, then fold it into .software-factory/system/ - ADRs, standing constraints, the living product and glossary.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory reconcile

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Reconcile runs once, after the last slice is completed (signed off by the runner in headless mode) and before the branch merges, so the project's living documents ship with the code they describe. Below, `<change>` is `.software-factory/changes/<slug>` and `<system>` is `.software-factory/system`.

## 1. Load

Load the change as [../factory-shared/gates.md](../factory-shared/gates.md) describes. The fast lane ([../factory-shared/gates.md](../factory-shared/gates.md), Milestones and autopilot) loads when every slice is `green` and `slices/<last>/review.md` has a filled Completion under approved scope. Slug empty: use the only change whose slices are all `done`, or ready on the fast lane, and whose `reconciled` is not `true`; several or none: ask. Read every gate document that is not `skipped`, `challenges.md` when it exists, and each `slices/NN/review.md`.

## 2. Acceptance

The agreed FR examples and applicable NFR fit criteria (including touched standing SYS-NFR promises) are independently verified on the running product by an agent that did not write its code and does not read it. An `acceptance.md` whose `Tried at` commit differs from HEAD only in `.software-factory/` (`git diff --name-only <Tried at> HEAD -- . ':!.software-factory' ':!.factory'` is empty) may be reused only for lines whose recorded example/fit criterion still matches the current approved documents and whose evidence remains applicable. Build the complete current ID list first: newly applicable IDs and older lines without a recorded criterion must be verified, even at unchanged source HEAD. Resume unanswered lines and retry every line answered `defect`.

Fast lane: reuse the review step's `acceptance.md` under the `Tried at` rule above, without the input-receipt clause; otherwise acceptance runs as below. A defect goes to the same executor while the slices are still `green`, as factory-review's Fast lane steps 5 and 6 say; the Autonomous local corrections paragraphs below do not apply. Lines the review held stay `fail` for step 8's question, with no further repair round.

1. **Examples and promises.** Each FR with its Example line, from `01-product.md` (track small: `04-slices.md`), and each applicable NFR/SYS-NFR fit criterion from `02-architecture.md` and the standing registry, with its verification procedure from `03-interface.md`. Include the agreed failed-write, recovery and interleaved-writer sequences for saved user data. Retain their IDs; an NFR is not implicitly passed by green FR tests.
2. **Surfaces.** Every module in `lenses.yaml` whose `dev_command` is not `none`: its path, `dev_command` and `dev_url`. A module with an empty `dev_command` (a `lenses.yaml` from before this step): ask the user how a user runs it, and record the command and local URL, or `none` for a library. When no module has a surface, use the existing test/check commands as the verification surface: the independent agent runs the mapped checks without inspecting implementation. Record their command/output for each applicable ID; unavailable checks are `not run`, not automatic passes.
3. **Run them.** Each `dev_url` must be local (`localhost`, `127.0.0.1` or `[::1]`); for any other, ask the user for a local one, and never point the agent at a deployed environment. For each server: if `dev_url` already answers, use it and leave it running; otherwise start `dev_command` from the module directory in the background and wait up to 60 seconds for `dev_url`. Stop the servers you started once the agent returns, on every outcome. A CLI (no `dev_url`) goes to the agent as `cd <absolute module path> && <dev_command>`.
4. **Try.** Make a new empty temp directory `<tmp>` outside the repository and write `<tmp>/examples.md`: a `## Surfaces` list (module path, then its URL or CLI command), then the examples and promise fit criteria with their verification procedures. A prepared browser capability with a fixed workspace and writable roots instead uses a fresh `<repo>/.tmp/acceptance-<unique>/` directory. Pass its exact argument-free `test_command`, the installed browser module path and the local surfaces in `examples.md`. If that command only discovers root `test*.cjs`, reserve one new `<repo>/test_acceptance_<unique>.cjs` for this independent agent; never overwrite an existing file. Start one fresh sub-agent. It receives these instructions, nothing else from this conversation:

   > Verify every FR example and applicable NFR/SYS-NFR fit criterion in `<tmp>/examples.md` on the running product, through the surfaces it lists: a URL in a real browser (Playwright or your browser tools), or over HTTP for an API; a CLI command in the shell. Work only in `<tmp>`. Do not read the product's source, tests or `.software-factory/` folder: judge only what a user of the product sees. Set up each example's input through the product itself. For a failure criterion, inject failure into the named actual dependency using its approved local procedure (for example browser storage, not HTTP for a local-only app). If that procedure is unavailable or a monitor requires an observation window you cannot collect, record `not run` with the missing evidence. Do not infer a promise passes from a happy-path screenshot. Save screenshots and other evidence files under `<tmp>/evidence/`. Write `<tmp>/acceptance.md` with one line per FR example or NFR fit criterion: its ID, the exact example/fit criterion checked, the surface used, `pass`, `fail` or `not run`, and the evidence (request and response, command and output, or an evidence file and what it shows). `not run` names what stopped you.

   For the prepared-browser branch, append only this capability instruction. An edit-hook rejection of the reserved script is `not run`; do not reopen signed-off slices or bypass hooks to obtain acceptance evidence.

   > Author your independent browser checks in the reserved `<repo>/test_acceptance_<unique>.cjs`; this is the sole file you may write outside `<tmp>`. Use the supplied installed browser module and local URL, then invoke the exact argument-free `test_command` directly. It also runs existing workspace checks: attribute each acceptance result only to the independent checks you authored and their evidence, not to unrelated green tests. Store screenshots under `<tmp>/evidence/`. Do not inspect implementation, existing tests or `.software-factory/`. If the capability cannot execute your check or collect its evidence, record `not run`.

   The agent can still reach the repository: the instruction is the firewall.
5. **Record.** Remove only the reserved acceptance script you created, on every outcome. Copy the result to `<change>/acceptance.md` under a line `Tried at: <git rev-parse HEAD>`, move the evidence files to `<change>/acceptance/` and rewrite their paths, then delete `<tmp>`. Classify reproducible failures against the unchanged approved criterion as implementation defects, without requesting the same authority again. Missing evidence stays `not run`: repair local setup within existing scope and retry first. A changed or ambiguous requirement, relaxed NFR, unavailable proof needing waiver, or security/money outcome decision is held for the final actual question; never auto-accept it.

   Headless mode retains the existing user classification/wait: ask about all `fail` and `not run` lines together and record actual answers (`defect`, `wrong example` with correction, or `not run accepted`). No headless approval is inferred.

   For a defect in an active green milestone, validate its unchanged authorized scope and resume the existing executor with one bounded reproduced finding batch, add isolated regression proof, obtain affected independent review/checks and rerun acceptance. The conductor and independent reviewers do not write routine source/test fixes.

   After all original slices are `done`, use gates.md **Autonomous local corrections** only when actual interactive initial approval includes frozen `## Development` / `Mode: autonomous-local` / `Repairs: approved-slice-files`, the independent failure contradicts an unchanged approved criterion, and exact required paths (including tests) are a subset of selected original parents' Allowed files. Confirm all four gates genuinely approved or legitimate small-track skipped, with unchanged hashes and actual approval authority. Batch related failures and retain their complete evidence. On clean committed source, capture fixed start/source commits, immutable failure/input snapshots and exact schema `repair.json`; append the next unused ordinary slice ID with its own new milestone, `base_commit: <start_commit>` fixed immediately, null test/head receipts, and state `pending`. Original parents remain done with unchanged heads/receipts; all original gate bytes/hashes remain untouched.

   Derive a candidate packet from the record paths and original approved criteria/contracts, not a nonexistent correction heading in `04-slices.md`. Run `repair-check --checkpoint edit` before building/dispatch and on every resume. Invalid metadata, off-branch/stale inputs or unrelated dirty source block while preserving work. Then automatically invoke `/factory-build <slug>` → `/factory-review <slug>` → `/factory-reconcile <slug>` under that real approval, honoring explicit manual/one-step preferences. The correction gets its own isolated RED/GREEN, fresh native executor completion and independent general/applicable-risk review. Before its `done` write run `repair-check --checkpoint complete` and actual current proof checks; validation alone is structural scope/provenance, never quality or approval.

   Missing mandate/authority, legacy/headless plans, changed or ambiguous promises/contracts, expanded paths (including a new regression file or typecheck caller), and waivers retain existing genuine gate/send-back behavior. If no authorized open slice can represent the defect, send back to `slices` once with `acceptance: <defect IDs>`. Never reopen completed parents or silently rehash approved documents. Real publication, credential, destructive and security/money outcome decisions stay separate.

   Continue bounded repairs until all required quality passes or a real unresolved decision/verification blocker remains. Identical failures trigger one bounded evidence-based diagnosis then an authorized recovery; no retry-count permission question, whole-source rewind, endless unchanged full panels or arbitrary time-limit waiver.

   Changed source reruns affected criteria and shared-state regressions; require a final complete current acceptance matrix. Reuse only evidence applicable to the current source, exact criterion, commands/dependencies/environment and approved/effective input receipt; unchanged source alone is insufficient. Timeout, setup failure and missing proof remain `not run`, never pass. Unresolved defects or required proof block completion.

Done when every current FR example and applicable NFR/SYS-NFR fit criterion has its own evidence and is `pass` or carries the user's answer, and none is a defect, apart from fast-lane lines held for step 8.

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
- `<system>/glossary.md`: each domain term the product rules and the interface introduced, starting from the `## Glossary` of `01-product.md`, whose terms the design file's Words also carry, with a one-line definition in the product's words. An existing term with a new meaning is a question for the user, not an overwrite.

Done when every Decision has an ADR, every change ID has a SYS row, every new term has a glossary line, and every Layout line is in the layout tree, all drafted.

## 6. Calibration and lessons

Not on the fast lane, unless the user asks; the same holds for step 7.

Your answers to lens findings tune the project's `.software-factory/principles.md`, the last of the principle layers ([../factory-shared/gates.md](../factory-shared/gates.md), Paths).

1. Count, per lens and rule (tags starting with `review/`, or `polish/` in changes from before decision 32, are not lens rules and are not counted), how often a finding was accepted (accept, modify, fix) and how often it was rejected (overrule, skip, undone); `auto-fixed` and `auto-skipped` happened without the user's answer and are not counted: in this change's `challenges.md` Responses and the `[lens/rule]` findings and lens cards of its `review.md` files, and in the `.software-factory/changes/*/challenges.md` and `review.md` files of this repository's other changes. Read this change's files from the working tree, and the others from git. Each answer counts once.
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

Not on the fast lane, unless the user asks. Follow [../factory-retro/SKILL.md](../factory-retro/SKILL.md) for this change. Its drafts join the confirmation below.

## 8. Confirm and write

Ask one consolidated final question: present acceptance results, held review/requirement/waiver decisions and every drafted ADR, ADR status change, constraint row, product section, glossary line, layout tree change, principle change and user-layer proposal, and everything retro drafted: `retro.md`, the playbook changes and counters, the environment fixes, proposals for the factory repository and suspicious items. Write local drafts once the user confirms; apply their corrections first. Only actual explicit final approval fills the milestone reviews' `Sign-off` lines; retain their original completion records. An answer changing a promise follows the appropriate gate and invalidation path before completion. Fast lane: the question also covers the review's held items. On approval, set every slice `done` and fill the review's Sign-off; then step 9 sets `reconciled: true`. A defect the user reports at this question goes to the same or a fresh executor while slices are still `green`, then Phase 1 checks 2 to 5 rerun at the fix HEAD, as factory-review step 9 says, and the affected review and acceptance lines rerun once. The project's `principles.md` goes into the reconcile commit. Global user-layer changes need explicit separate authority; a local reconcile confirmation alone does not authorize them. An explicitly accepted user-layer proposal is written to `~/.software-factory/user/principles.md`, which no repository tracks. Reconcile never edits the framework cache: changes to the factory stay proposals for the factory repository.

## 9. Record

1. Set `reconciled: true` and `notes_for_fresh_session: "Reconciled. Ready to merge."` in `status.yaml`.
2. Committed mode: `git add .software-factory/system .software-factory/changes/<slug>` (the playbook and `retro.md` included), and `.software-factory/principles.md` when it changed, and commit `chore(factory): reconcile <slug>`.
3. Tell the user the change is ready to merge from `<branch>`.
