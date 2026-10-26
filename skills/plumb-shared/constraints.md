# Constraints: <project>

Standing requirements, promises and constraints of this project. Every change reads this file. Each row ends mapped to an enforcement.

| ID | Kind | Statement | Fit criterion | Source | Enforced by |
| --- | --- | --- | --- | --- | --- |
| SYS-FR-01 | Functional | WHEN <trigger>, the system SHALL <response> | <observable outcome> | <change slug> | test: `<test name>` |
| SYS-NFR-01 | Performance | <user promise> | p95 under <n> ms on <path> | <catalog or change slug> | monitor: `<name>` |
| SYS-C-01 | Constraint | <budget, deadline, regulation, team, existing stack> | rules out <options> | <who decided> | human-verified |
