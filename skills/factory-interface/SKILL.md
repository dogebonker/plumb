---
name: factory-interface
description: Interface gate of a factory change - the human decides module signatures, promises and depth; every requirement maps to enforcement.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory interface

Slug: $ARGUMENTS

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

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 | test: <file> :: <name> |
| NFR-01 | test, lint rule, monitor, or human-verified |
| SYS-NFR-01 | <reuse its registry enforcement, or add one> |

## Open questions
~~~

- Signatures are in the repository's language and style, complete enough to compile.
- The Test plan turns every FR example into one test, per module by its `bdd` state in `lenses.yaml`: a declarative scenario in native modules, reusing the wording of existing step definitions (the adapter's BDD step search finds them); a test name in the repository's framework elsewhere. Coverage names that scenario or test.

## 3. Compile and cost

Prove the signatures compile against the real code, using `~/.software-factory/adapters/<language>.md` for each module's language. Without an adapter for a language, tell the user that module stays unchecked.

1. Tracked files outside `.factory/` must be unchanged; otherwise ask the user to commit or stash. Record the untracked files (`git status --short`).
2. Write every module's signatures as stubs in their real files, in the adapter's stub form, with any `mod` lines or exports they need.
3. Run the adapter's typecheck. An error in a stub or its imports is a signature problem: fix the draft (with the user when the fix changes a signature's meaning) and repeat. An error from the environment (dependencies not installed, missing toolchain) leaves the module unchecked: tell the user why.
4. Fill each module's Cost line by counting in the stubs. A pass-through method forwards to another method with nearly the same signature.
5. Undo the stubs: `git restore --worktree -- . ':!.factory'`, then delete every untracked file that was not in the list from step 1.

Done when every module type-checks or is reported unchecked with its reason, every Cost line is filled, and `git status --short` matches step 1.

## 4. The human decides

For each module, show the draft with its Cost line and ask the user to accept, edit or rewrite it. A high count is a prompt to ask whether the module hides enough. Apply their changes verbatim: their wording of a signature wins over yours. Any changed signature goes through step 3 again. Then ask the open questions.

Done when the user has decided every module, Coverage maps every ID from the earlier gates, listed SYS IDs included, and Open questions is empty. An unmapped ID blocks approval.

## 5. Approve

Approve the `interface` gate as gates.md describes. Next skill: `/factory-slices`.
