# Vertical slice

ID `vertical-slice`, row L4. Code is grouped by request, from endpoint to storage: minimize coupling between slices, maximize it inside one. Every slice is a command or a query. Sources: `docs/research/layouts-selection.md`, pattern 6.

**Fits:** many requests that each touch their own data and change separately. Also inside the modules of a `modular-monolith` for `domain-core`, once shared logic moves to `domain/`. **Does not fit:** requests that share most of their models, or mandatory shared repositories and services.

## Layout lines

TypeScript (Node):
1. `src/shared/`: DB connection, HTTP plumbing, config. No business rules
2. `src/domain/`: logic extracted when two slices need it. No slice imports
3. `src/features/<feature>/<request>/`: endpoint, request, handler, response and test for one request
4. `src/main.ts`: registers slices

Other stacks, same order and descriptions:
- Python: `src/<pkg>/shared/`, `src/<pkg>/domain/`, `src/<pkg>/features/<feature>/`, `src/<pkg>/main.py`
- Go: `internal/pkg/`, `internal/<feature>/models/`, `internal/<feature>/features/<request>/`, `cmd/<bin>/main.go`
- Rust: `src/shared/`, `src/domain/`, `src/features/<feature>/`, `src/main.rs`

## Layers

- TypeScript: `["src/shared/**", "src/domain/**", "src/features/**", "src/main.ts"]`
- Python: `["src/<pkg>/shared/**", "src/<pkg>/domain/**", "src/<pkg>/features/**", "src/<pkg>/main.py"]`
- Go: `["internal/pkg/**", "internal/*/models/**", "internal/*/features/**", "cmd/**"]`
- Rust: `["src/shared/**", "src/domain/**", "src/features/**", "src/main.rs"]`

Sibling rule: slices may not import each other.

## Check

TypeScript: dependency-cruiser or eslint-plugin-boundaries. Python: import-linter `independence`. Go: go-arch-lint. See `tools.yaml`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [mehdihadeli/go-vertical-slice-template](https://github.com/mehdihadeli/go-vertical-slice-template) | Go | 131, 2025-07 | `internal/catalogs/products/features/creatingproduct/` |
| [marcoturi/fastify-boilerplate](https://github.com/marcoturi/fastify-boilerplate) | TypeScript | 469, 2026-10 | `src/modules/user/commands/create-user/` |
| [jbogard/ContosoUniversityDotNetCore-Pages](https://github.com/jbogard/ContosoUniversityDotNetCore-Pages) | .NET (originator) | 1,807, 2026-04 | `ContosoUniversity/Pages/{Courses,Students}`, a handler per page |
| [nadirbad/VerticalSliceArchitecture](https://github.com/nadirbad/VerticalSliceArchitecture) | .NET | 604, 2026-08 | `src/Application/Scheduling/` beside `Application/Domain` |

Python and Rust: no well-known exemplar.
