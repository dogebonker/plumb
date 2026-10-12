# Modular monolith (DDD modules)

ID `modular-monolith`, row L6. One deployable split into business-aligned modules, each a bounded context with DDD's layers inside (`ddd.md`) and a public API; everything else is hidden. Row L6 writes one `Pattern: modular-monolith` line for the whole tree. Sources: `docs/research/layouts-selection.md`, pattern 7.

**Fits:** `domain-core` with two or more bounded contexts in one deployable, or a system several teams share. A `crud-service` with several business areas uses the same tree with layered modules (below). **Does not fit:** one small context (`layered` or `hexagonal`).

## Layout lines

TypeScript (Node):
1. `src/shared/`: the shared kernel: cross-module primitives and messaging. No module's rules
2. `src/modules/<module>/domain/`: aggregates, value objects, domain events, repository interfaces. No infrastructure
3. `src/modules/<module>/application/`: application services or command handlers. No domain rules
4. `src/modules/<module>/infrastructure/`: repositories, ORM mapping, outbox, clients. No use-case logic
5. `src/modules/<module>/interfaces/`: controllers and consumers. Translate to application calls
6. `src/modules/<module>/index.ts`: the module's public API: facade, integration events, query DTOs. The only file other modules import
7. `src/main.ts`: wires modules together

Other stacks, same order and descriptions:
- Python: `src/<pkg>/seedwork/`, `src/<pkg>/modules/<module>/domain/`, `src/<pkg>/modules/<module>/application/`, `src/<pkg>/modules/<module>/infrastructure/`, `src/<pkg>/modules/<module>/api/`, `src/<pkg>/modules/<module>/__init__.py`, `src/<pkg>/main.py`
- Go: `internal/common/`, `internal/<module>/internal/domain/`, `internal/<module>/internal/app/`, `internal/<module>/internal/adapters/`, `internal/<module>/internal/ports/`, `internal/<module>/module.go` (the exported facade; the nested `internal/` keeps the rest private), `cmd/<bin>/main.go`
- Rust: `crates/kernel/`, then per module the crates `crates/<module>-domain/`, `crates/<module>-app/`, `crates/<module>-infra/`, `crates/<module>-http/`, the `pub` items of `crates/<module>-app/src/lib.rs`, and `crates/app/`

## Layers

- TypeScript: `["src/shared/**", "src/modules/*/domain/**", "src/modules/*/application/**", "src/modules/*/infrastructure/**", "src/modules/*/interfaces/**", "src/main.ts"]`; each `index.ts` is in no layer, and the checker enforces the index-only rule
- Python: `["src/<pkg>/seedwork/**", "src/<pkg>/modules/*/domain/**", "src/<pkg>/modules/*/application/**", "src/<pkg>/modules/*/infrastructure/**", "src/<pkg>/modules/*/api/**", "src/<pkg>/main.py"]`
- Go: `["internal/common/**", "internal/*/internal/domain/**", "internal/*/internal/app/**", "internal/*/internal/adapters/**", "internal/*/internal/ports/**", "cmd/**"]`
- Rust: the crate graph

Sibling rule: a module imports another only through `src/modules/<other>/index.ts` (Python: the package `__init__`; Go: `internal/<other>/module.go`, which the compiler enforces through the nested `internal/`; Rust: `pub` items).

## Layered modules (crud-service with several business areas)

The same `src/shared/`, `index.ts` public API, `src/main.ts` and sibling rule, with `layered`'s folders inside each module instead of DDD's:
- TypeScript: `src/modules/<module>/models/`, `src/modules/<module>/repositories/`, `src/modules/<module>/services/`, `src/modules/<module>/routes/`; layers `["src/shared/**", "src/modules/*/models/**", "src/modules/*/repositories/**", "src/modules/*/services/**", "src/modules/*/routes/**", "src/main.ts"]`
- Python: `src/<pkg>/modules/<module>/models.py`, `src/<pkg>/modules/<module>/crud.py`, `src/<pkg>/modules/<module>/services/`, `src/<pkg>/modules/<module>/api/`; layers in the same order
- Go: `internal/<module>/internal/model/`, `internal/<module>/internal/repository/`, `internal/<module>/internal/service/`, `internal/<module>/internal/handler/`, with `internal/<module>/module.go`; layers in the same order

## Check

TypeScript: dependency-cruiser. Python: import-linter `independence` with `containers`, or tach. Go: nested `internal/`. Rust: Cargo crates. See `tools.yaml`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [kgrzybek/modular-monolith-with-ddd](https://github.com/kgrzybek/modular-monolith-with-ddd) | .NET (reference) | 14,062, 2024-06 (stale) | `src/Modules/<M>/{Domain,Application,Infrastructure,IntegrationEvents}`, `Tests/ArchTests` |
| [ThreeDotsLabs/wild-workouts-go-ddd-example](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example) | Go | 6,471, 2026-08 | two contexts as `internal/trainer/` and `internal/trainings/` |
| [pgorecki/python-ddd](https://github.com/pgorecki/python-ddd) | Python | 1,046, 2025-01 (stale) | `src/modules/{bidding,catalog,iam}` over `src/seedwork` |
| [marcoturi/fastify-boilerplate](https://github.com/marcoturi/fastify-boilerplate) | TypeScript | 469, 2026-10 | no direct imports between modules; command, query and event buses |
| [spring-projects/spring-modulith](https://github.com/spring-projects/spring-modulith) | Java (reference) | 1,197, 2026-10 | `spring-modulith-examples/spring-modulith-example-full` |

Rust: no well-known exemplar.
