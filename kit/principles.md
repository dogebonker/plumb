# Principles

Framework defaults: the first of the three principle layers, before the user layer `~/.software-factory/user/principles.md` and the project's `.software-factory/principles.md` ([gates.md](../skills/factory-shared/gates.md), Paths). A later layer wins on the same `<lens>/<rule>`. Reconcile writes the project's file and proposes entries for the user layer; it never edits this one.

## Principles

Rules you accepted three times or more. Architecture and interface drafts follow them, and review tags a finding against one by its `<lens>/<rule>`.

The framework's four named principles. A later layer overrides one with an entry of the same `factory/<name>`, or quiets it.

- **YAGNI** (`factory/yagni`). Build only what a requirement or caller in this change needs. Test: every interface, parameter, flag, config key and extension point the diff adds has a caller or a requirement in the change.
- **KISS** (`factory/kiss`). Take the first rung of the simplification ladder ([packs.md](../skills/factory-shared/packs.md)) that holds. Test: for each layer, wrapper, indirection or dependency the diff adds, name what breaks without it. When nothing breaks, it is a finding.
- **DRY** (`factory/dry`). One place owns each piece of knowledge: a business rule, a constant, a format, a schema. Test: after the diff, one change to a rule needs edits in three or more places.
- **SOLID** (`factory/solid`). Single responsibility, open/closed, substitution, segregated interfaces and dependency inversion hold at module boundaries. Test: each public interface the diff adds or changes gains no second, unrelated job. Callers use the interface, not the module's internals, and depend on no method they do not use. A subtype keeps its parent's contract. An inner layer imports no outer one, which review's Dependency rule check reports. Code inside a module raises no SOLID finding.

When they conflict, in this order. These rules also decide between a lens rule and these principles.

1. YAGNI and KISS win by default: no interface with one implementation, no abstraction for a single caller. A DRY or SOLID finding whose fix adds one is recommended as skip. The exception is a port that keeps an inner layer from importing an outer detail.
2. DRY means duplicated knowledge, not code that looks similar. The second copy is fine, and the third consolidates (refactoring-guru's Rule of Three). Code that changes for different reasons stays apart however alike it reads.
3. SOLID applies at module boundaries, not as ceremony inside a module. Open/closed means an extension point only where a second variant exists.
4. A smell that maps to a design pattern is a suggestion, never a requirement: the pattern goes in only when rules 1 to 3 allow it (the `gang-of-four` pack, [packs/README.md](packs/README.md)).

<!-- example: - Errors are values at module boundaries: callers handle them without try/catch. Source: a-philosophy-of-software-design/define errors out of existence, accepted 3 times. -->

## Quiet rules

Lens rules you overruled three times or more, matched by their exact `<lens>/<rule>` text. The interface panel and review cap their findings at `note`.

Money and security rules never go quiet, even when listed here: rules from a `fin-*` pack, and rules that guard authentication, authorization, secrets, injection, cross-site attacks or path traversal.

<!-- example: - clean-code/small functions: overruled 3 times, last in checkout-retry -->
