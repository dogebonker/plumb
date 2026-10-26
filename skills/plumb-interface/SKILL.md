---
name: plumb-interface
description: Interface gate of a Plumb change - the human decides module signatures, promises and depth; every requirement maps to enforcement.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Plumb interface

Usage: [per-skill accounting](../plumb-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../plumb-shared/gates.md](../plumb-shared/gates.md). The human owns this gate: you draft, they decide. Agents later implement behind these signatures and cannot change them.

Track standard, interactive mode: `/plumb-plan` drafts this document from step 2 only, without Cost lines and Decisions. Steps 3 to 5 (compile, cost, challenge panel, rounds) run on every other track and mode.

## 1. Load

Load the change as gates.md describes, for the `interface` gate. An approved matching interface is complete: skip steps 2 to 6 and continue to unfinished work. For a revision, apply gates.md **Change impact** before editing. A changed signature alone does not reopen architecture or security: preserve their bytes and approval records unless the exact delta contradicts a named decision, budget or trust/access rule. Read `01-product.md`, `02-architecture.md`, and the modules it names with their callers.

## 2. Draft `03-interface.md`

~~~markdown
# Interface: <slug>

## <module path>
Depth: <what this module hides, in one line>
Cost: <n> public methods, <n> parameters, <n> error variants exposed, <n> configuration options exposed, <n> pass-through methods

```<language>
<signature>
```
<interface comment: what it promises, its errors, never how>

## Test plan
### <module path> (bdd: native)
```gherkin
Feature: <capability, in the product's words>
  Scenario: <FR-01's example, as a sentence>
    Given <state>
    When <event>
    Then <outcome>
```
### <module path> (bdd: off)
- FR-01: `<test file>` :: <test name that states the example's outcome>

## Decisions
### <lens conflict the human settled>
Supersedes: <earlier ADR number, or none>
Context: <the two cards, by lens>
Decision: <the call>
Enforced by: <named rule, test or monitor from its constraint, or human-verified>
Consequences: <what gets easier, what gets harder>

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 | test: <file> :: <name>, or scenario: <feature file> :: <scenario> |
| NFR-01 | test, lint rule, monitor, or human-verified |
| SYS-NFR-01 | <reuse its registry enforcement, or add one> |

## Open questions
~~~

- Signatures are in the repository's language and style, complete enough to compile, and follow the Principles of the principle layers ([../plumb-shared/gates.md](../plumb-shared/gates.md), Paths).
- Every module the change creates or changes has a section, and so does each frontend root the Layout names: a `Pattern` line with `fda` (the new-root default), or a recorded `frontend-small`, `fsd` or `feature-folders` exception (gates.md, Layout). A frontend's interface is each page, and each export another folder imports: components with their props type, hooks, the API client. Each gets an interface comment saying what it shows or does, and sits in its folder from the Layout (gates.md, Layout). On its Cost line, each exported component or hook counts as a public method and each prop as a parameter.
- The Test plan turns every FR example into one test, chosen per module by its `bdd` state in `lenses.yaml`. When `ui` is `true`, it also covers each state the design file's States position names (empty, running, failed, no change, done) for the screens this change touches.
- UI: carry the selected optional feature-reference patterns and DESIGN.md adaptation into the affected screen/component contract. References do not add behavior or become required acceptance unless explicitly agreed; use the approved design system when none were supplied.
- For applicable persistence promises, interface comments define saved, failed-write/draft, invalid-data recovery and conflict outcomes in the repository’s existing result/error style. The Test plan maps each applicable NFR and SYS-NFR fit criterion to evidence, including sequences: fail the actual storage write then retry/reload; load invalid existing data then attempt a write without destroying recoverable bytes; interleave two writers and save from an already-open editor. Assert both user-visible success/error and retained data. A happy-path reload or HTTP failure injection cannot substitute for these storage boundaries.
- In a native module that test is a declarative scenario: its steps state business intent, never clicks, fields or URLs, and reuse the wording of existing step definitions (the adapter's BDD step search finds them).
- Elsewhere it is a test name in the repository's framework. Coverage names that scenario or test.

Track critical: before approval, run the [draft conformance pass](../plumb-shared/adr.md) against every accepted standing ADR and SYS row. The scripted inventory and one bounded fresh read check drafted Decisions and Frozen contracts; reuse the existing fresh challenge reviewer where available rather than add a parallel panel. Keep at most three evidence-backed conflicts, each quoting the standing decision and the contradictory draft line. Without an explicit `Supersedes: NNNN`, place the conflict in the pending document’s Open questions for the user to answer `supersedes NNNN` or `withdraw`; include it with Assumptions in the approval summary. Record the answer in the pending draft before hashing. Never edit an approved upstream document or silently supersede an ADR; retain compatible architecture/security approvals. Decision enforcement follows the [standing ADR rules](../plumb-shared/adr.md).

## 3. Compile and cost

Prove the signatures compile against the real code, using `<kit>/adapters/<language>.md` for each module's language. Without an adapter for a language, tell the user that module stays unchecked.

1. Tracked files outside `.plumb/` must be unchanged; otherwise ask the user to commit or stash. Record the untracked files (`git status --short`).
2. Set `stubbing: true` in `status.yaml`, so the Plumb hook lets the stubs through. Write every module's signatures as stubs in their real files, in the adapter's stub form, with any `mod` lines or exports they need.
3. Run the adapter's typecheck. An error in a stub or its imports is a signature problem: fix the draft (with the user when the fix changes a signature's meaning) and repeat. An error from the environment (dependencies not installed, missing toolchain), or a stub file the adapter's typecheck does not cover, leaves the module unchecked: tell the user why.
4. Fill each module's Cost line by counting in the stubs. A pass-through method forwards to another method with nearly the same signature.
5. Undo the stubs: `git restore --worktree -- . ':!.plumb' ':!.factory' ':!.software-factory'`, then delete every untracked file that was not in the list from step 1. Set `stubbing: false`.

Done when every module type-checks or is reported unchecked with its reason, every Cost line is filled, and `git status --short` matches step 1.

## 4. Challenge panel

Book challenges are optional, under packs.md's explicit task selection and size caps. With no selected applicable design lens and no required money review, skip this step entirely: compile/coverage checks and the human's contract decision still run. No empty panel report or extra question.

1. The panel, each lens checked as [../plumb-shared/packs.md](../plumb-shared/packs.md) describes or reported skipped:

   | Lens | When | File under resolved `<pack>` (bundled exact pin or cache; packs.md) |
   | --- | --- | --- |
   | selected applicable design lenses, including APoSD | only explicit `design_lenses` opt-in; one reviewer within the task-size cap | `<name>.nano.md` or `<name>.mini.md`; full only by explicit deep-review request |
   | `fin-money-core` | `money: true` in `lenses.yaml` | `SKILL.md` |

2. Make a new temp directory `<tmp>`. Start at most one design reviewer for the selected excerpts; required money review remains separate. Each sees only the applicable changed signatures, named constraints and its selected excerpts, never this conversation. A later revision reuses affected selected reviewers; it never activates an unselected APoSD reviewer. Each receives:

   > Challenge the interface in `<change>/03-interface.md` through the rules in `<lens file>`. Read only the files named here.
   > - Constraint IDs: `<change>/01-product.md` (when it exists) and `.plumb/system/constraints.md`.
   > - Write at most three cards to `<tmp>/<lens>.md`, each in the form of `<absolute path of challenge-card.md in this skill's folder>`. Lens / rule is `<lens skill folder>/<section heading>: <the rule's first five words>`, copied exactly from the lens file.
   > - Every card quotes a signature from the interface, argues for the current design first, then gives the objection, an alternative signature and what the alternative costs.
   > - Severity `block` or `fix` needs an anchor: a constraint ID or a number on a module's Cost line. Every other card is a `note`.
   > - Zero cards is a valid answer: then write the strongest objection you considered and why you dropped it.
   > - From round 2: challenge only these changed signatures: `<list>`.

3. Collect the cards into `<change>/challenges.md` under `## Round N`, grouped by lens, keeping at most three per lens (`block` before `fix` before `note`). Drop a card whose quoted signature is not in the interface; a `block` or `fix` card whose anchor does not exist becomes a `note`. A card whose lens and rule are listed under Quiet rules of the principle layers ([../plumb-shared/gates.md](../plumb-shared/gates.md), Paths) becomes a `note`, unless it is a money or security rule. Conflicts are decided against the agreed constraints and smaller public surface; no unselected book arbitrates them.

Append a `panel_round` event with the round number and card count (gates.md, History). Done when every lens has its cards, or its dropped objection, in `challenges.md`.

## 5. The human decides

Use gates.md **Explain questions and decisions**: recap the goal and relevant answers, then show a concrete input → result sketch or before/after table for each changed behavior, with the recommendation and drawback. Lead with "What you give it / What you get back"; keep exact changed signatures and Cost lines in the supporting draft. Translate challenge cards into the user-visible problem and proposed fix before asking for a response. For revisions, state which approvals stay valid and which tests rerun. A new response field or changed parameter stays an interface question unless its actual semantics require a named upstream/security decision to change; do not backfill interface detail into approved architecture or rerun the security approval ceremony.

For each module, show the draft with its Cost line and its cards, `block` first, and ask the user to accept, edit or rewrite it. For a high Cost count, show one concrete example of the extra steps a caller must know and the simpler alternative; ask which behavior is needed. For each card the user answers accept, modify or overrule with one line, written into its Response in `challenges.md`; each `conflict` they settle becomes an entry under Decisions. Apply their changes verbatim: their wording of a signature wins over yours. Any changed signature goes through step 3 again. Only affected opted-in design reviewers and required money coverage recheck the changed signatures; no automatic APoSD pass. Keep the panel to one initial pass and one scoped confirmation; further optional design critique runs only if the user requests it. Required correctness, contract, money and security failures still need proof and repair. The user can end the rounds at any point by approving. Then ask the open questions.

Done when every card has a Response (`grep -n 'accept / modify / overrule:' challenges.md` finds nothing), the user has decided every module, every FR example and applicable NFR failure sequence has its test, scenario or stated verification procedure in the Test plan, Coverage maps every ID from the earlier gates, listed SYS IDs included, and Open questions is empty. An unmapped ID blocks approval.

## 6. Approve

Approve the `interface` gate as gates.md describes. Next skill: `/plumb-slices`.
