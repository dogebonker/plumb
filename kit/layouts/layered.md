# Layered (n-tier)

ID `layered`, row L3. Sources and reasoning: `docs/research/layouts-selection.md`, pattern 1, in the Plumb repository.

**Fits:** `crud-service` with no framework convention, one business area, a small team. **Does not fit:** several business areas growing in one tree (`modular-monolith`), or rules that must stay free of the database (`hexagonal`).

## Layout lines

TypeScript (Node):
1. `src/models/`: data shapes and ORM mapping. May not import services or routes
2. `src/repositories/`: queries. May not import services or routes
3. `src/services/`: transaction scripts. May not import routes or HTTP types
4. `src/routes/`: parse, validate, call a service, respond. May not run queries
5. `src/main.ts`: wiring and startup only

Other stacks, same order and descriptions:
- Python: `src/<pkg>/models.py`, `src/<pkg>/crud.py`, `src/<pkg>/services/`, `src/<pkg>/api/routes/`, `src/<pkg>/main.py`
- Go: `internal/model/`, `internal/repository/`, `internal/service/`, `internal/handler/`, `cmd/<bin>/main.go`
- Rust: `src/models/`, `src/db/`, `src/services/`, `src/routes/`, `src/main.rs` (promote a layer to a workspace crate for a hard boundary)

## Layers

- TypeScript: `["src/models/**", "src/repositories/**", "src/services/**", "src/routes/**", "src/main.ts"]`
- Python: `["src/<pkg>/models.py", "src/<pkg>/crud.py", "src/<pkg>/services/**", "src/<pkg>/api/**", "src/<pkg>/main.py"]`
- Go: `["internal/model/**", "internal/repository/**", "internal/service/**", "internal/handler/**", "cmd/**"]`
- Rust: `["src/models/**", "src/db/**", "src/services/**", "src/routes/**", "src/main.rs"]`

Sibling rules: none.

## Check

TypeScript: dependency-cruiser or eslint-plugin-boundaries. Python: import-linter `layers`. Go: go-arch-lint. Rust: Cargo, with layers as crates. See `tools.yaml`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | Python | 45,946, 2026-10 | `backend/app/`: `api/routes/`, `crud.py`, `models.py`, `core/` |
| [go-nunu/nunu-layout-advanced](https://github.com/go-nunu/nunu-layout-advanced) | Go | 69 (the nunu generator: 2,607, pushed 2026-08) | `internal/handler`, `service`, `repository`, `model` |
| [rust-lang/crates.io](https://github.com/rust-lang/crates.io) | Rust | 3,721, 2026-10 | `src/controllers/` over the `crates/crates_io_database` crate |
| [santiq/bulletproof-nodejs](https://github.com/santiq/bulletproof-nodejs) | TypeScript | 5,775, 2024-06 (stale) | `src/api`, `services`, `models`, `loaders` |
