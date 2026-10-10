# Constraints: <project>

Every ID must map to an enforcement by the Interface Design gate. An unmapped ID blocks it.

| ID | Kind | Statement | Fit criterion | Source | Enforced by |
| --- | --- | --- | --- | --- | --- |
| FR-01 | Functional | WHEN <trigger>, the system SHALL <response> | <observable outcome> | Product gate | test: `<test name>` |
| NFR-01 | Performance | <user promise> | p95 under <n> ms on <endpoint> | Architecture gate | monitor: `<name>` |
| C-01 | Constraint | <budget, deadline, regulation, team, existing stack> | <what it rules out> | Product gate | human-verified |
