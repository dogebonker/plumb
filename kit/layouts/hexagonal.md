# Hexagonal / Clean (ports and adapters, Onion)

ID `hexagonal`, row L5: one bounded context. One rule in three vocabularies: source dependencies point inward. Hexagonal names the boundary (ports); Onion and Clean add the inner rings. With DDD's domain and application inside, this is one bounded context (`ddd.md` covers the tactical rules). Sources: `docs/research/layouts-selection.md`, pattern 3.

**Fits:** `domain-core` with rules worth testing without a database, or several entry points (HTTP, CLI, queue, tests). **Does not fit:** thin CRUD, where every port has one adapter and the layers only copy data.

## Layout lines

TypeScript (Node):
1. `src/domain/`: entities, value objects, rules, domain events. No framework, ORM, HTTP or I/O imports
2. `src/application/`: use cases, one per file, and `ports/` with the interfaces they need (repository, mailer). No adapter imports
3. `src/adapters/in/<tech>/`: driving adapters (HTTP, CLI, queue consumers). Call use cases, never the database
4. `src/adapters/out/<tech>/`: driven adapters implementing the ports. No use-case logic
5. `src/main.ts`: the composition root, the only place that wires adapters to ports

Other stacks, same order and descriptions:
- Python (Cosmic Python naming): `src/<pkg>/domain/`, `src/<pkg>/service_layer/` (ports as abstract base classes), `src/<pkg>/entrypoints/`, `src/<pkg>/adapters/`, `src/<pkg>/bootstrap.py`
- Go (Three Dots naming): `internal/domain/`, `internal/app/` (port interfaces here or in `internal/domain/`), `internal/ports/`, `internal/adapters/`, `cmd/<bin>/main.go`
- Rust, one workspace crate per ring: `crates/domain/`, `crates/application/` (ports as traits), `crates/http/`, `crates/postgres/`, `crates/app/`

## Layers

- TypeScript: `["src/domain/**", "src/application/**", "src/adapters/**", "src/main.ts"]`
- Python: `["src/<pkg>/domain/**", "src/<pkg>/service_layer/**", "src/<pkg>/{adapters,entrypoints}/**", "src/<pkg>/bootstrap.py"]`
- Go: `["internal/domain/**", "internal/app/**", "internal/{adapters,ports}/**", "cmd/**"]`
- Rust: the crate graph; `Cargo.toml` dependencies point inward only

Sibling rules: driving and driven adapters do not import each other.

## Check

TypeScript: dependency-cruiser. Python: import-linter `layers`. Go: `internal/` plus go-arch-lint. Rust: Cargo crates. See `tools.yaml`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [evrone/go-clean-template](https://github.com/evrone/go-clean-template) | Go | 7,690, 2026-10 | `internal/entity`, `usecase`, `repo`, `controller/{restapi,grpc,amqp_rpc}` |
| [ivan-borovets/fastapi-clean-example](https://github.com/ivan-borovets/fastapi-clean-example) | Python | 593, 2026-10 | `src/app/core/` (commands, queries, ports), `inbound/http`, `outbound/` |
| [Sairyss/domain-driven-hexagon](https://github.com/Sairyss/domain-driven-hexagon) | TypeScript | 14,967, 2024-06 (stale) | `src/modules/user/{domain,commands,queries,database}`, `src/libs/ports` |
| [bxcodec/go-clean-arch](https://github.com/bxcodec/go-clean-arch) | Go | 10,171, 2024-04 (stale) | `domain/`, `article/`, `internal/repository`, `internal/rest` |
| [microsoft/cookiecutter-rust-actix-clean-architecture](https://github.com/microsoft/cookiecutter-rust-actix-clean-architecture) | Rust | 265, 2024-07 (stale) | the best Rust option found, small and stale: `src/{domain,services,infrastructure,api}` |
