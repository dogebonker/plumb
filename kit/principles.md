# Principles

Engineering taste, with reasons. Reconcile proposes entries from how you answer lens findings; you can edit this file by hand at any time.

## Principles

Rules you accepted three times or more. Architecture and interface drafts follow them.

<!-- example: - Errors are values at module boundaries: callers handle them without try/catch. Source: a-philosophy-of-software-design/define errors out of existence, accepted 3 times. -->

- Write each rule once: a rule kept in several places drifts (the network-logo rule lived in three places and ADA on Cardano lost its badge). Source: refactoring-guru/duplicate-code, accepted 13 times.
- Name timing and size constants so values that must match across CSS and JS can be found and cross-checked. Source: refactoring-guru/magic-number, accepted 4 times.
- Delete unused parameters and counters instead of keeping them for later callers. Source: refactoring-guru/speculative-generality, accepted 3 times.
- Names must not clash or nearly collide (orderLine vs OrderLine, NO_ORDER vs NO_ORDERS) and must say what they limit. Source: clean-code/naming, accepted 3 times.
- Use what the platform, toolchain or codebase already provides (column DEFAULT, Vite defaults, existing helpers) instead of restating it. Source: ponytail/ladder, accepted 6 times.
- Keep identity explicit: a version is a concurrency token, not an identity, and a row keyed by two fields cannot be updated by one. Source: patterns-of-enterprise-application-architecture/keep identity explicit, accepted 3 times.
- State where client session state lives and for how long: an app key with no stated store or lifetime can create a second order after a reload. Source: patterns-of-enterprise-application-architecture/session state, accepted 3 times.

## Quiet rules

Lens rules you overruled three times or more, matched by their exact `<lens>/<rule>` text. The interface panel and review cap their findings at `note`.

Money and security rules never go quiet, even when listed here: rules from a `fin-*` pack, and rules that guard authentication, authorization, secrets, injection, cross-site attacks or path traversal.

<!-- example: - clean-code/small functions: overruled 3 times, last in checkout-retry -->

- a-philosophy-of-software-design/booleans and mode parameters switching internal behavior: overruled 4 times, last in tg-mini-app
- a-philosophy-of-software-design/exposing half-valid objects: overruled 4 times, last in tg-mini-app
- patterns-of-enterprise-application-architecture/layering: overruled 3 times, last in tg-mini-app
