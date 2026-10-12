---
name: factory-interface
description: Interface gate of a factory change - the human decides module signatures, promises and depth; every requirement maps to enforcement.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory interface

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). The human owns this gate: you draft, they decide. Agents later implement behind these signatures and cannot change them.

## 1. Load

Load the change as gates.md describes, for the `interface` gate. Read `01-product.md`, `02-architecture.md`, and the modules it names with their callers.

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
Context: <the two cards, by lens>
Decision: <the call>
Consequences: <what gets easier, what gets harder>

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 | test: <file> :: <name>, or scenario: <feature file> :: <scenario> |
| NFR-01 | test, lint rule, monitor, or human-verified |
| SYS-NFR-01 | <reuse its registry enforcement, or add one> |

## Open questions
~~~

- Signatures are in the repository's language and style, complete enough to compile, and follow the Principles in `~/.software-factory/principles.md`.
- Every module the change creates or changes has a section, and so does each frontend root the Layout names (gates.md, Layout). A frontend's interface is each page, and each export another folder imports: components with their props type, hooks, the API client. Each gets an interface comment saying what it shows or does, and sits in its folder from the Layout (gates.md, Layout). On its Cost line, each exported component or hook counts as a public method and each prop as a parameter.
- The Test plan turns every FR example into one test, chosen per module by its `bdd` state in `lenses.yaml`. When `ui` is `true`, it also covers each state the design file's States position names (empty, running, failed, no change, done) for the screens this change touches.
- In a native module that test is a declarative scenario: its steps state business intent, never clicks, fields or URLs, and reuse the wording of existing step definitions (the adapter's BDD step search finds them).
- Elsewhere it is a test name in the repository's framework. Coverage names that scenario or test.

## 3. Compile and cost

Prove the signatures compile against the real code, using `~/.software-factory/adapters/<language>.md` for each module's language. Without an adapter for a language, tell the user that module stays unchecked.

1. Tracked files outside `.factory/` must be unchanged; otherwise ask the user to commit or stash. Record the untracked files (`git status --short`).
2. Set `stubbing: true` in `status.yaml`, so the factory hook lets the stubs through. Write every module's signatures as stubs in their real files, in the adapter's stub form, with any `mod` lines or exports they need.
3. Run the adapter's typecheck. An error in a stub or its imports is a signature problem: fix the draft (with the user when the fix changes a signature's meaning) and repeat. An error from the environment (dependencies not installed, missing toolchain), or a stub file the adapter's typecheck does not cover, leaves the module unchecked: tell the user why.
4. Fill each module's Cost line by counting in the stubs. A pass-through method forwards to another method with nearly the same signature.
5. Undo the stubs: `git restore --worktree -- . ':!.factory'`, then delete every untracked file that was not in the list from step 1. Set `stubbing: false`.

Done when every module type-checks or is reported unchecked with its reason, every Cost line is filled, and `git status --short` matches step 1.

## 4. Challenge panel

Fresh reviewers challenge the draft, one lens each, the way a future reader would: they see the documents, never this conversation.

1. The panel, each lens checked as [../factory-shared/packs.md](../factory-shared/packs.md) describes or reported skipped:

   | Lens | When | File under `~/.agents/skills/<name>/` |
   | --- | --- | --- |
   | `a-philosophy-of-software-design` | always; it also gets each module's language pack index | `<name>.md` (full size) |
   | the profile's `challenge` lenses | always | `<name>.mini.md` |
   | `fin-money-core` | `money: true` in `lenses.yaml` | `SKILL.md` |

2. Make a new temp directory `<tmp>`. Start one fresh sub-agent per lens, all at once (round 3, and the one round after a send-back: the APoSD lens only, on the changed signatures, step 5). Each receives these instructions and nothing else:

   > Challenge the interface in `<change>/03-interface.md` through the rules in `<lens file>`. Read only the files named here.
   > - Constraint IDs: `<change>/01-product.md` (when it exists) and `.factory/system/constraints.md`.
   > - Write at most three cards to `<tmp>/<lens>.md`, each in the form of `<absolute path of challenge-card.md in this skill's folder>`. Lens / rule is `<lens skill folder>/<section heading>: <the rule's first five words>`, copied exactly from the lens file.
   > - Every card quotes a signature from the interface, argues for the current design first, then gives the objection, an alternative signature and what the alternative costs.
   > - Severity `block` or `fix` needs an anchor: a constraint ID or a number on a module's Cost line. Every other card is a `note`.
   > - Zero cards is a valid answer: then write the strongest objection you considered and why you dropped it.
   > - From round 2: challenge only these changed signatures: `<list>`.

3. Collect the cards into `<change>/challenges.md` under `## Round N`, grouped by lens, keeping at most three per lens (`block` before `fix` before `note`). Drop a card whose quoted signature is not in the interface; a `block` or `fix` card whose anchor does not exist becomes a `note`. A card whose lens and rule are listed under Quiet rules in `~/.software-factory/principles.md` (money and security rules excepted, as that file defines) becomes a `note`. Two cards that pull one signature in opposite directions are marked `conflict`; recommend the APoSD side, since APoSD arbitrates at interface level.

Append a `panel_round` event with the round number and card count (gates.md, History). Done when every lens has its cards, or its dropped objection, in `challenges.md`.

## 5. The human decides

For each module, show the draft with its Cost line and its cards, `block` first, and ask the user to accept, edit or rewrite it. A high Cost count is a prompt to ask whether the module hides enough. For each card the user answers accept, modify or overrule with one line, written into its Response in `challenges.md`; each `conflict` they settle becomes an entry under Decisions. Apply their changes verbatim: their wording of a signature wins over yours. Any changed signature goes through step 3 again, and through the panel within a limit of three rounds: round 2 is the full panel on the changed signatures only; round 3 is the APoSD reviewer alone, on what changed since round 2; there is no round 4 unless the user asks for one. A send-back to this gate reopens the panel for one round outside that limit: the APoSD reviewer alone, on the signatures that changed; more only if the user asks. The user can end the rounds at any point by approving. Then ask the open questions.

Done when every card has a Response (`grep -n 'accept / modify / overrule:' challenges.md` finds nothing), the user has decided every module, every FR example has its test or scenario in the Test plan, Coverage maps every ID from the earlier gates, listed SYS IDs included, and Open questions is empty. An unmapped ID blocks approval.

## 6. Approve

Approve the `interface` gate as gates.md describes. Next skill: `/factory-slices`.
