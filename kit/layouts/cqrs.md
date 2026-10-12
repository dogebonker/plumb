# CQRS

ID `cqrs`, row L7. Added inside a `domain-core` context, on top of `hexagonal` or inside the modules of a `modular-monolith`, never across a CRUD system. Its lines go under the host's Pattern line, which becomes `Pattern: <host>+cqrs`. `vertical-slice` needs no addition: its slices are already commands and queries. Sources: `docs/research/layouts-selection.md`, pattern 5.

**Fits:** a context where read shapes differ from the write model, reads far outnumber writes, the UI is task-based, or edits are concurrent. **Does not fit:** `crud-service`, or simple rules. Lighter step: a read-only `views` folder in the host's application layer, with the same sibling rule.

## Layout lines

On `hexagonal`, TypeScript:
1. `src/application/commands/<command>/`: one handler per command. Loads aggregates through repositories. Returns nothing or an id
2. `src/application/queries/<query>/`: read handlers returning DTOs. May not import `src/domain/` or change state
3. `src/adapters/out/read-models/`: projections or SQL views fed by events. No business rules

On `modular-monolith`, only in the modules row L7 chose, with the module's name written in place of `<module>`. TypeScript: `src/modules/<module>/application/commands/<command>/`, `src/modules/<module>/application/queries/<query>/`, `src/modules/<module>/infrastructure/read-models/`, same descriptions.

Other stacks on `hexagonal`, same order: Python `src/<pkg>/service_layer/commands/`, `src/<pkg>/views.py`, `src/<pkg>/adapters/read_models/`; Go `internal/app/command/`, `internal/app/query/`, `internal/adapters/readmodel/`; Rust `crates/application/src/command/`, `crates/application/src/query/`, `crates/postgres/src/read_model/`. On `modular-monolith`, the same names inside each module's application and infrastructure folders.

## Layers

The host's layers. Sibling rule: queries may not import the domain. On `hexagonal`: TypeScript `src/application/queries/**` may not import `src/domain/**`; Python `src/<pkg>/views.py` may not import `src/<pkg>/domain/**`; Go `internal/app/query/**` may not import `internal/domain/**`; Rust `crates/application/src/query/` may not use the `domain` crate. On `modular-monolith`, the same per named module (TypeScript `src/modules/<module>/application/queries/**` and `src/modules/<module>/domain/**`).

## Check

The host's checker, with this rule added (dependency-cruiser `forbidden`, import-linter `forbidden`, go-arch-lint). See `tools.yaml`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [ThreeDotsLabs/wild-workouts-go-ddd-example](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example) | Go | 6,471, 2026-08 | `internal/trainings/app/command/` and `app/query/` |
| [marcoturi/fastify-boilerplate](https://github.com/marcoturi/fastify-boilerplate) | TypeScript | 469, 2026-10 | `src/modules/user/commands/create-user/`, `queries/`, `src/shared/cqrs` |
| [jasontaylordev/CleanArchitecture](https://github.com/jasontaylordev/CleanArchitecture) | .NET (reference) | 20,632, 2026-10 | CQRS without aggregates: `src/Application/TodoLists/{Commands,Queries}` |
| [cosmicpython/code](https://github.com/cosmicpython/code), branch `chapter_12_cqrs` | Python | 2,717, 2025-06 (stale) | `src/allocation/views.py` beside `service_layer/handlers.py`; CC-BY-ND, read only |
