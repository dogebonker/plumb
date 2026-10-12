# DDD: the inside of a bounded context

Reference, not selected on its own: row L5 lays out one context as `hexagonal`, and row L6 lays out each module of a `modular-monolith` with these layers. This file holds DDD's tactical rules and the exemplars. Sources: `docs/research/layouts-selection.md`, pattern 4.

**Fits:** `domain-core`: invariants, a core domain worth modeling, experts with their own vocabulary. More than one context when the same word means different things to different groups. **Does not fit:** `crud-service`.

## Layers inside one context, innermost first

1. `domain/`: aggregates, value objects, domain events, repository interfaces. No infrastructure
2. `application/`: application services or command handlers, transactions. No domain rules
3. `infrastructure/`: repositories, ORM mapping, outbox, clients. No use-case logic
4. `interfaces/`: controllers and consumers that translate to application calls

Between contexts: a context uses another only through its public API (integration events, query DTOs), never its internals. Base types every context agrees on live in one shared kernel, with no business rules of a single context.

Naming per stack: Python `domain/`, `application/`, `infrastructure/`, `api/`; Go (Three Dots) `domain/`, `app/`, `adapters/`, `ports/`; Rust one crate per ring: `<context>-domain`, `<context>-app`, `<context>-infra`, `<context>-http`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [ThreeDotsLabs/wild-workouts-go-ddd-example](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example) | Go | 6,471, 2026-08 | `internal/trainer/`, `internal/trainings/`: `domain`, `app`, `adapters`, `ports` |
| [ddd-by-examples/library](https://github.com/ddd-by-examples/library) | Java (reference) | 5,873, 2026-09 | two contexts, `catalogue` and `lending`, and the event-storming README |
| [citerus/dddsample-core](https://github.com/citerus/dddsample-core) | Java (reference) | 5,292, 2025-06 (stale) | the cargo sample from Evans's book |
| [pgorecki/python-ddd](https://github.com/pgorecki/python-ddd) | Python | 1,046, 2025-01 (stale) | `src/modules/{bidding,catalog,iam}/{domain,application,infrastructure}`, `src/seedwork` |
| [Sairyss/domain-driven-hexagon](https://github.com/Sairyss/domain-driven-hexagon) | TypeScript | 14,967, 2024-06 (stale) | `src/modules/<module>/domain`, `src/libs/ddd` |

Vernon's [IDDD_Samples](https://github.com/VaughnVernon/IDDD_Samples) is the originator's code (stale since 2023). Rust: no well-known, maintained exemplar.
