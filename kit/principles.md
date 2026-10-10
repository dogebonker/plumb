# Principles

Engineering taste, with reasons. Reconcile proposes entries from how you answer lens findings; you can edit this file by hand at any time.

## Principles

Rules you accepted three times or more. Architecture and interface drafts follow them.

<!-- example: - Errors are values at module boundaries: callers handle them without try/catch. Source: a-philosophy-of-software-design/define errors out of existence, accepted 3 times. -->

## Quiet rules

Lens rules you overruled three times or more, matched by their exact `<lens>/<rule>` text. The interface panel and review cap their findings at `note`.

Money and security rules never go quiet, even when listed here: rules from a `fin-*` pack, and rules that guard authentication, authorization, secrets, injection, cross-site attacks or path traversal.

<!-- example: - clean-code/small functions: overruled 3 times, last in checkout-retry -->
