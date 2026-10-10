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

```<language>
<signature>
```
<interface comment: what it promises, its errors, never how>

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 | test: <file> :: <name> |
| NFR-01 | test, lint rule, monitor, or human-verified |
| SYS-NFR-01 | <reuse its registry enforcement, or add one> |

## Open questions
~~~

- Signatures are in the repository's language and style, complete enough to compile.

## 3. The human decides

For each module, show the draft and ask the user to accept, edit or rewrite it. Apply their changes verbatim: their wording of a signature wins over yours. Then ask the open questions.

Done when the user has decided every module, Coverage maps every ID from the earlier gates, listed SYS IDs included, and Open questions is empty. An unmapped ID blocks approval.

## 4. Approve

Approve the `interface` gate as gates.md describes. Next skill: `/factory-slices`.
