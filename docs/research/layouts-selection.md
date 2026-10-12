# Layouts: which reference tree the architecture gate proposes, and why

Research for the Layout section of the architecture gate ([gates.md, Layout](../../skills/factory-shared/gates.md), [factory-architecture](../../skills/factory-architecture/SKILL.md)). It catalogs reference folder layouts, gives the gate a rule for proposing one or two, and lists real repositories to look at. Every definition comes from its originator or the framework's own docs, read live. Registry versions, release dates and repository facts were checked on 2026-10-12 (npm, PyPI, crates.io, Maven Central, NuGet, the GitHub API). A tool version is recommended only if it was released on or before 2026-09-28, two weeks before that date.

## Summary

- **Pick by the domain first, then by size.** Thin CRUD logic gets the framework's MVC tree or a plain layered tree. A domain with real business rules gets hexagonal (Clean) layers with DDD's domain, application and infrastructure. Several bounded contexts in one deployable get a modular monolith whose modules are those contexts. CQRS is added inside one context when reads and writes really differ, never across a whole CRUD system. Legacy code keeps the layout it has.
- **Hexagonal, Onion and Clean are one idea.** Martin presents Clean Architecture as an integration of Hexagonal, Onion, DCI and BCE, with a single rule: source dependencies point inward ([Martin][clean]). The kit should treat them as one pattern with naming variants.
- **The FSD threshold needs a correction.** FSD's own docs give no screen count and say it fits "projects and teams of any size" ([FSD overview][fsd-overview]). Their test for extracting code out of a page is reuse across pages ([FSD layers][fsd-layers]). Keep "an entity or user action that two or more screens use", drop "more than five screens" (details under pattern 8).
- **The kit's ordered `layers` list cannot express sibling rules.** FSD slices, modular-monolith modules and vertical slices all forbid imports between siblings on the same level, and CQRS queries may not import the domain. Those rules need a tool (table below). import-linter lists layers highest first, the opposite of `lenses.yaml` ([import-linter layers][il-layers]).
- **Gaps:** no well-known, maintained exemplar exists for hexagonal or DDD in Rust, for vertical slices in Python, or for a modular monolith in Go, TypeScript or Rust. Rust has no mature layer-direction linter: Cargo's crate graph is the enforcement.

## Selection table

Inputs: the lens profile from `lenses.yaml` (`kit/profiles/*.yaml`), the size signals, and the stack. The gate proposes the first matching row, and the row's alternative as a second option when a signal is borderline. An existing convention always wins ([factory-architecture](../../skills/factory-architecture/SKILL.md)).

| ID | Profile | Signal | Propose | Alternative | One-line reason |
|---|---|---|---|---|---|
| L1 | legacy | any | **Keep the current tree.** Record it as the Layout, add an import rule with a baseline of known violations | Strangler module beside it in L3 or L5 shape | Rewriting structure at once is the risk the Strangler Fig avoids. It "begins with small additions" ([Fowler][strangler]) |
| L2 | crud-service | A framework with its own folder convention: Rails, Django, Laravel, AdonisJS, Loco | **MVC**, as the framework lays it out (pattern 2) | L3 inside the framework's `app/` | Framework conventions are the documented default, and a view-model-data top level is "OK for smaller systems" ([Fowler][pdd]) |
| L3 | crud-service | No framework convention (Express, Fastify, FastAPI, Go `net/http`, axum), one business area | **Layered** (pattern 1) | L4 when requests change independently | Simple data-driven services use "simple CRUD in a single layer" or a plain stack ([Microsoft DDD][ms-ddd]) |
| L4 | crud-service, or domain-core with many independent use cases | Many distinct requests that change separately, and a team that refactors | **Vertical slice** (pattern 6) | L3 | Slices cut coupling between requests. Bogard says it assumes the team "understands code smells and refactoring" ([Bogard][vsa]) |
| L5 | domain-core | One bounded context | **Hexagonal / Clean with DDD layers** (patterns 3 and 4) | L6 if a second context appears | DDD layering applies "only if" the service has "significant business rules" ([Microsoft DDD][ms-ddd]) |
| L6 | domain-core | Two or more bounded contexts in one deployable: the same word means different things to different groups ([Fowler][bc]) | **Modular monolith**, one module per context, each laid out as L5 (pattern 7) | Separate services, out of scope here | Boundaries are hard to get right first time, and are easier to move inside one process ([Fowler][monolith-first]) |
| L7 | domain-core, on top of L5 or L6 | Inside one context: read shapes differ from the write model, reads far outnumber writes, task-based UI, or concurrent edits | **Add a CQRS split** in that context (pattern 5) | Separate `views` module only ([Cosmic Python][cosmic-cqrs]) | Fowler: use it on "specific portions" (bounded contexts), most systems fit CRUD ([Fowler][cqrs]) |
| L8 | any | A frontend root where no entity or user action is used by two or more screens | **Small frontend tree** (pattern 9) | L9 | React: don't "spend more than five minutes" choosing, split as it grows ([React FAQ][react-faq]) |
| L9 | any | A frontend root with an entity or user action that two or more screens use, or a team that is growing | **Feature-Sliced Design** (pattern 8). Next.js: `_app`, `_pages` | Feature folders (pattern 10) | FSD extracts code from pages when it is "reused on several pages" ([FSD layers][fsd-layers]) |

Profile to rows: `domain-core` (rich domain model) maps to L5, L6, L7. `crud-service` (transaction scripts) maps to L2, L3, L4. `legacy` maps to L1. A frontend root picks L8 or L9 under any profile.

As adopted in `kit/layouts/index.yaml` (decision 29), after review: L6 is evaluated before L5 so two contexts reach the modular monolith first; L4 is crud-service only, with observable signals, and vertical slices became L5's alternative; L1 applies to existing modules only and records `existing`; a no-match fallback gives a crud-service with several business areas a modular monolith with layered modules.

### Enforcement tools

Versions checked 2026-10-12. "Pinned" is the newest stable release on or before 2026-09-28.

| Stack | Tool | Pinned (released) | Newer, too recent | Checks | Command |
|---|---|---|---|---|---|
| TypeScript | [dependency-cruiser][depcruise] | 18.4.0 (2026-09-20) | 18.6.0 (2026-10-11) | Path-regex `forbidden` rules, cycles, baseline of known violations (`depcruise-baseline`, `--ignore-known`) | `npx --no-install depcruise src` |
| TypeScript | [eslint-plugin-boundaries][boundaries] | 7.2.0 (2026-08-09) | none | Element types by glob, `boundaries/dependencies` allow/deny policies | `npx --no-install eslint .` |
| TypeScript (FSD) | [steiger][steiger] + `@feature-sliced/steiger-plugin` | 0.7.0 and 0.8.0 (both 2026-09-25) | none | FSD rules incl. `forbidden-imports`, `no-cross-imports`, `public-api` ([plugin source][steiger-rules]) | `npx --no-install steiger ./src` |
| TypeScript (feature folders) | eslint-plugin-import-x, `import-x/no-restricted-paths` | 4.17.1 (2026-06-28) | none | Zones: target folder may not import from folder | `npx --no-install eslint .` |
| Python | [import-linter][il-layers] | 2.15 (2026-09-04) | none | `layers` (with `containers` per module), `independence`, `forbidden`, `acyclic_siblings`, `ignore_imports` | `lint-imports` |
| Python | [tach][tach] | 0.35.1 (2026-09-14) | 0.35.3 (2026-10-06) | Declared module dependencies, public interfaces, no cycles | `tach check` |
| Go | compiler | Go 1.27.1 here | n/a | `internal/` is importable only from the tree above it ([cmd/go][go-internal]). Import cycles are illegal ([Go spec][go-spec]) | `go build ./...` |
| Go | [go-arch-lint][go-arch-lint] | v1.19.0 (2026-09-07) | none | Components by path, `mayDependOn` | `go-arch-lint check` |
| Rust | Cargo | cargo 1.95.0 here | n/a | A crate uses only what its `Cargo.toml` lists, and Cargo rejects cycles (verified: two path crates depending on each other fail with "cyclic package dependency") | `cargo check --workspace` |
| Rust | [cargo-modules][cargo-modules] | 0.27.0 (2026-08-03), MPL-2.0 | none | Module cycles inside one crate (`--acyclic`), not layer direction | `cargo modules dependencies --lib --acyclic` |
| Ruby | [packwerk][packwerk-repo] | v3.3.1 (2026-08-26) | none | Package dependencies and privacy, `package_todo.yml` baseline | `bin/packwerk check` |
| Java (reference) | ArchUnit, [Spring Modulith][modulith] | 1.5.1 (2026-09-25), 2.1.1 (2026-08-26) | 2.2.0-M2 (milestone) | Layer and module rules as tests | `ApplicationModules.of(App.class).verify()` |
| .NET (reference) | NetArchTest.Rules, NetArchTest.eNhancedEdition | 1.3.2 (2021-05-23), 1.4.5 (2025-06-04) | none | Layer rules as tests | test runner |

After LAY-01 ran these tools (decision 29's untested claim): eslint-plugin-import 2.32.0 does not install beside ESLint 10, so the kit uses eslint-plugin-import-x 4.17.1 (`import-x/no-restricted-paths`), steiger 0.7.0 needs Node 22.18.0 or later, and dependency-cruiser and both ESLint checkers need typescript 6.0.x (6.0.3): TypeScript 7 has no compiler API, so dependency-cruiser checks 0 modules and exits 0, and typescript-eslint requires <6.1. Evidence: `evals/checkers/FINDINGS.md`.

Not recommended: [cargo-pup][cargo-pup] 0.1.8 (2026-06-09, 64 stars) needs a pinned nightly toolchain because it uses compiler internals. pytestarch's only release old enough is 4.0.1 (2025-08-08), and 5.0.0 came out 2026-10-11. tsarch has had no release since 5.4.1 (2024-12-23).

## Patterns

Tree tables give one line per folder: the folder in each stack, then what lives there and what may not. `<x>` is a name placeholder, as in [gates.md](../../skills/factory-shared/gates.md). Layer lists are path globs, innermost first, in the TypeScript paths. Swap in the stack's column for the others. Exemplar facts are from `gh api repos/<owner>/<repo>` on 2026-10-12. "Stale" marks a last push over a year ago: a finished sample, still worth reading for structure.

### 1. Layered (n-tier)

**Sources.** Fowler splits a program into presentation, domain and data source, dependencies running top to bottom, as "logical layers not physical tiers". He calls framework-style top-level layers "OK for smaller systems" and says larger systems should split the top level "into domain oriented modules which are internally layered". Organizing teams by layer is an antipattern ([Fowler][pdd]).

**Fits:** `crud-service` with no framework convention, one business area, a small team. **Does not fit:** several business areas growing in one tree (move to L6), or rules that need the domain free of the database (move to L5).

| Folder | TypeScript (Node) | Python | Go | Rust | Holds / may not |
|---|---|---|---|---|---|
| models | `src/models/` | `src/<pkg>/models.py` | `internal/model/` | `src/models/` | Data shapes and ORM mapping. May not import services or routes |
| data access | `src/repositories/` | `src/<pkg>/crud.py` | `internal/repository/` | `src/db/` | Queries. May not import services or routes |
| business logic | `src/services/` | `src/<pkg>/services/` | `internal/service/` | `src/services/` | Transaction scripts. May not import routes or HTTP types |
| presentation | `src/routes/` | `src/<pkg>/api/routes/` | `internal/handler/` | `src/routes/` | Parse, validate, call a service, respond. May not run queries |
| entry | `src/main.ts` | `src/<pkg>/main.py` | `cmd/<bin>/main.go` | `src/main.rs` | Wiring and startup only |

Per language: Go keeps everything but `main` under `internal/` ([Go layout][go-layout]). Python uses the `src/` layout so tests run against the installed package ([PyPA][src-layout]). Rust can promote a layer to a workspace crate when it needs a hard boundary ([Cargo workspaces][cargo-ws]).

**Layers:** `["src/models/**", "src/repositories/**", "src/services/**", "src/routes/**", "src/main.ts"]`

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | Python | 45,946 | 2026-10-08 | MIT | no | `backend/app/`: `api/routes/`, `crud.py`, `models.py`, `core/` |
| [go-nunu/nunu](https://github.com/go-nunu/nunu) | Go | 2,607 | 2026-08-14 | MIT | no | Its generated layout, [nunu-layout-advanced](https://github.com/go-nunu/nunu-layout-advanced) (69 stars, MIT): `internal/handler`, `service`, `repository`, `model` |
| [rust-lang/crates.io](https://github.com/rust-lang/crates.io) | Rust | 3,721 | 2026-10-12 | Apache-2.0 | no | `src/controllers/` over the `crates/crates_io_database` crate (`models/`, `schema.rs`) |
| [santiq/bulletproof-nodejs](https://github.com/santiq/bulletproof-nodejs) | TypeScript | 5,775 | 2024-06-19 (stale) | MIT | no | `src/api`, `services`, `models`, `loaders`, `subscribers` |

### 2. MVC (framework conventions)

**Sources.** Rails: `app/` holds "the controllers, models, views, helpers, mailers, jobs", under convention over configuration ([Rails guide][rails]). Django: a project is a set of apps, each with `models.py`, `views.py`, `admin.py`, `migrations/` ([Django tutorial][django]), and Django calls itself "MTV" since its view picks the data and the template renders it ([Django FAQ][django-faq]). Laravel: `app/Http` (controllers), `app/Models` (Eloquent, one model per table), `resources/views`, `routes/`. You are "free to organize your application however you like" ([Laravel][laravel]). Express prescribes nothing: "Express makes no assumptions in terms of structure", and links an MVC example ([Express FAQ][express-faq]). AdonisJS: `app/controllers`, `app/models`, `resources/views`, `start/routes.ts` ([AdonisJS][adonis]). Loco is "Rust on Rails" ([Loco README](https://github.com/loco-rs/loco)).

**Fits:** `crud-service` on a framework that has the convention. Django apps double as modules, so a Django project is already modular. **Does not fit:** a rich domain. ActiveRecord ties each model to a table ([Laravel][laravel]), while hexagonal keeps the domain free of its data source ([Cockburn][hexagonal]). Go has no MVC convention: the Go guide organizes by package ([Go layout][go-layout]).

| Folder | Rails | Django | Laravel | TypeScript (Express, AdonisJS) | Rust (Loco) | Holds / may not |
|---|---|---|---|---|---|---|
| models | `app/models/` | `<app>/models.py` | `app/Models/` | `app/models/` | `src/models/` | Persistence and model rules. May not reference controllers or views |
| views | `app/views/` | `<app>/templates/<app>/` ([tutorial 3][django-3]) | `resources/views/` | `resources/views/` or `views/` | `src/views/` | Rendering only. No queries beyond what the controller passes |
| controllers | `app/controllers/` | `<app>/views.py` | `app/Http/Controllers/` | `app/controllers/` | `src/controllers/` | One action per request. May not hold domain rules a second controller needs |
| routes | `config/routes.rb` | `<app>/urls.py` | `routes/web.php` | `start/routes.ts` | `src/app.rs` | URL to action only |
| migrations | `db/migrate/` | `<app>/migrations/` | `database/migrations/` | `database/migrations/` ([Lucid][lucid]) | not checked | Schema changes only |

**Layers:** `["app/models/**", "app/views/**", "app/controllers/**"]` (Rails paths. Laravel and AdonisJS map one to one).

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [rubygems/rubygems.org](https://github.com/rubygems/rubygems.org) | Rails | 2,441 | 2026-10-11 | MIT | no | `app/models`, `app/controllers`, `app/views`, plus `app/policies`, `app/jobs` |
| [django/djangoproject.com](https://github.com/django/djangoproject.com) | Django | 2,021 | 2026-10-09 | BSD-3-Clause | no | One app per area: `blog/`, `releases/`, `members/`, `fundraising/` |
| [koel/koel](https://github.com/koel/koel) | Laravel | 17,277 | 2026-10-11 | MIT | no | `app/Http`, `app/Models`, with `app/Services` and `app/Repositories` added |
| [expressjs/express](https://github.com/expressjs/express) | TypeScript/JS | 69,624 | 2026-10-09 | MIT | no | `examples/mvc/`: `controllers/`, `views/`, `lib/` |
| [loco-rs/loco](https://github.com/loco-rs/loco) | Rust | 9,426 | 2026-09-24 | Apache-2.0 | no | The framework. Its reference apps under `evals/tasks/*/reference/src/` show `controllers`, `models`, `views` |

### 3. Hexagonal (ports and adapters) and Clean Architecture

**Sources.** Cockburn (2005): the application is driven equally by users, programs, tests or batch jobs, and runs isolated from databases. A port is "a purposeful conversation" named by purpose, an adapter converts one technology to it. Primary (driving) adapters such as HTTP call in, secondary (driven) adapters such as databases are called by the application ([Cockburn][hexagonal]). Palermo's Onion: "all coupling is toward the center", same premise as hexagonal ([Palermo][onion]). Martin's Clean Architecture has four circles (Entities, Use Cases, Interface Adapters, Frameworks and Drivers), says "source code dependencies can only point inwards", and allows more circles ([Martin][clean]).

**How they relate.** One rule, three vocabularies. Hexagonal names the boundary (ports) and is silent on the inside. Onion and Clean add rings inside: domain model, then application or use cases. A hexagonal app with a domain folder and an application folder is a Clean app.

**Fits:** `domain-core` with business rules worth testing without a database, or several entry points (HTTP, CLI, queue, tests). **Does not fit:** thin CRUD, where every port has one adapter and the layers only copy data. Bogard finds these architectures "mock-heavy, with rigid rules around dependency management" and right for only a minority of requests ([Bogard][vsa]), Microsoft says CRUD needs simpler approaches ([Microsoft DDD][ms-ddd]).

| Folder | TypeScript (Node) | Python | Go | Rust (workspace) | Holds / may not |
|---|---|---|---|---|---|
| domain | `src/domain/` | `src/<pkg>/domain/` | `internal/domain/` | `crates/domain/` | Entities, value objects, rules. No framework, ORM, HTTP or I/O imports |
| application | `src/application/` | `src/<pkg>/service_layer/` | `internal/app/` | `crates/application/` | Use cases, one per file. Calls the domain and driven ports. No adapter imports |
| driven ports | `src/application/ports/` | abstract base classes, as Cosmic Python's `AbstractRepository` in `adapters/repository.py` | interfaces in `internal/domain/` (Wild Workouts keeps `repository.go` there) or `internal/app/` | traits in `crates/application/` | Interfaces the application needs (repository, mailer). No implementations |
| driving adapters | `src/adapters/in/http/` | `src/<pkg>/entrypoints/` | `internal/ports/` (Three Dots naming) | `crates/http/` | HTTP, CLI, queue consumers. Call use cases, never the database |
| driven adapters | `src/adapters/out/<tech>/` | `src/<pkg>/adapters/` | `internal/adapters/` | `crates/postgres/` | Implement driven ports. No use-case logic |
| composition root | `src/main.ts` | `src/<pkg>/bootstrap.py` (Cosmic Python, chapter 13) | `cmd/<bin>/main.go` | `crates/app/src/main.rs` | The only place that wires adapters to ports |

Per language: Go's `internal/` keeps the core unimportable from other modules ([Go layout][go-layout]). In Rust, a crate per ring makes the direction a compile error, since a crate sees only declared dependencies and Cargo rejects cycles (verified locally, table above). Names vary in the wild: Cosmic Python says `service_layer` and `entrypoints`, Three Dots Labs says `ports` for the driving side.

**Layers:** `["src/domain/**", "src/application/**", "src/adapters/**", "src/main.ts"]`

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [Sairyss/domain-driven-hexagon](https://github.com/Sairyss/domain-driven-hexagon) | TypeScript (NestJS) | 14,967 | 2024-06-11 (stale) | MIT | no | `src/modules/user/{domain,commands,queries,database}`, `src/libs/ports` |
| [ivan-borovets/fastapi-clean-example](https://github.com/ivan-borovets/fastapi-clean-example) | Python | 593 | 2026-10-06 | MIT | no | `src/app/core/` (commands, queries, ports), `inbound/http`, `outbound/`, `main/ioc` |
| [evrone/go-clean-template](https://github.com/evrone/go-clean-template) | Go | 7,690 | 2026-10-11 | MIT | no | `internal/entity`, `usecase`, `repo`, `controller/{restapi,grpc,amqp_rpc}`, `cmd/app` |
| [bxcodec/go-clean-arch](https://github.com/bxcodec/go-clean-arch) | Go | 10,171 | 2024-04-24 (stale) | MIT | no | `domain/`, `article/` (use case), `internal/repository`, `internal/rest` |
| [microsoft/cookiecutter-rust-actix-clean-architecture](https://github.com/microsoft/cookiecutter-rust-actix-clean-architecture) | Rust | 265 | 2024-07-26 (stale) | MIT | no | Template `src/{domain,services,infrastructure,api}`. The best Rust option found, small and stale |

### 4. DDD: bounded contexts and tactical layers

**Sources.** Evans's patterns are summarized in the free [DDD Reference][ddd-ref]. A bounded context is a boundary inside which one model applies. Signals for more than one: the same word means different things to different groups, and language changes across the organization ([Fowler][bc]). Evans's layers, as quoted by Microsoft: the domain layer is "the heart of business software", the application layer "is kept thin" and coordinates, infrastructure persists. Domain depends on nothing, infrastructure depends on domain ([Microsoft DDD][ms-ddd]). Vernon's own sample code puts each context in `domain/model`, `application` and `port/adapter`, which is DDD layers inside hexagonal ([IDDD_Samples](https://github.com/VaughnVernon/IDDD_Samples)). His book's chapter 4, "Architecture", covers hexagonal, CQRS and event-driven styles ([InformIT][iddd]).

**Fits:** `domain-core`: invariants, a core domain worth modeling, experts with their own vocabulary. Microsoft: apply DDD "only if" the service has "significant business rules". **Does not fit:** `crud-service` ([Microsoft DDD][ms-ddd]).

| Folder | TypeScript (Node) | Python | Go | Rust | Holds / may not |
|---|---|---|---|---|---|
| context | `src/<context>/` | `src/<pkg>/modules/<context>/` | `internal/<context>/` | `crates/<context>-domain/`, `crates/<context>-app/` ... | One bounded context. May not import another context's internals |
| domain | `src/<context>/domain/` | `.../<context>/domain/` | `internal/<context>/domain/` | `<context>-domain` crate | Aggregates, value objects, domain events, repository interfaces. No infrastructure |
| application | `src/<context>/application/` | `.../<context>/application/` | `internal/<context>/app/` | `<context>-app` crate | Application services or command handlers, transactions. No domain rules |
| infrastructure | `src/<context>/infrastructure/` | `.../<context>/infrastructure/` | `internal/<context>/adapters/` | `<context>-infra` crate | Repositories, ORM mapping, outbox, clients. No use-case logic |
| interfaces | `src/<context>/interfaces/` | `.../<context>/api/` | `internal/<context>/ports/` | `<context>-http` crate | Controllers, consumers. Translate to application calls |
| contracts | `src/<context>/contracts/` | `.../<context>/contracts.py` | exported types in `internal/<context>/app/` | `<context>-contracts` crate | What other contexts may use: integration events, query DTOs |
| shared kernel | `src/shared-kernel/` | `src/<pkg>/seedwork/` | `internal/common/` | `crates/kernel/` | Base types every context agrees on. No business rules of one context |

**Layers (per context):** `["src/shared-kernel/**", "src/*/domain/**", "src/*/application/**", "src/*/infrastructure/**", "src/*/interfaces/**", "src/main.ts"]`. Between contexts: only `src/<other>/contracts/**` (a sibling rule, needs a tool).

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [citerus/dddsample-core](https://github.com/citerus/dddsample-core) | Java (reference) | 5,292 | 2025-06-02 (stale) | MIT | no | The cargo sample from Evans's book: `se/citerus/dddsample/{domain/model,application,infrastructure,interfaces}` |
| [ThreeDotsLabs/wild-workouts-go-ddd-example](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example) | Go | 6,471 | 2026-08-27 | MIT | no | `internal/trainer/` and `internal/trainings/`: `domain`, `app`, `adapters`, `ports` |
| [pgorecki/python-ddd](https://github.com/pgorecki/python-ddd) | Python | 1,046 | 2025-01-03 (stale) | MIT | no | `src/modules/{bidding,catalog,iam}/{domain,application,infrastructure}`, `src/seedwork` |
| [ddd-by-examples/library](https://github.com/ddd-by-examples/library) | Java (reference) | 5,873 | 2026-09-17 | MIT | no | Two contexts, `catalogue` and `lending`, with the event-storming docs in the README |
| [Sairyss/domain-driven-hexagon](https://github.com/Sairyss/domain-driven-hexagon) | TypeScript | 14,967 | 2024-06-11 (stale) | MIT | no | `src/modules/<module>/domain`, `src/libs/ddd` |

Vernon's [IDDD_Samples](https://github.com/VaughnVernon/IDDD_Samples) (3,945 stars, last push 2023-09-09, Apache-2.0 in `LICENSE.txt`, which GitHub does not detect) is the originator's code but stale. Rust: no well-known DDD exemplar found. The largest candidate, `jdomenechb/rust-ddd-example`, has 280 stars and no push since 2022-07.

### 5. CQRS

**Sources.** CQRS uses one model to update and another to read. Fowler heard it from Greg Young, calls it "a significant mental leap", says most systems should stay CRUD, and says to apply it to specific bounded contexts only ([Fowler][cqrs]). Microsoft: commands are business tasks, queries "never alter data" and return DTOs with no domain logic. Use it for collaborative editing, task-based UIs, separate read tuning, read-heavy loads. Not when "the domain or the business rules are simple" ([Microsoft CQRS][ms-cqrs]). Cosmic Python: a separate read-only `views` module is "probably a good idea, even if you don't want to go to full-blown CQRS" ([Cosmic Python][cosmic-cqrs]).

**Fits:** inside one `domain-core` context with read/write asymmetry or read shapes that differ from aggregates. **Alone:** CQRS works without DDD, as a commands/queries split per feature (jasontaylordev, below). **On DDD:** commands go through aggregates, queries bypass them. **Does not fit:** `crud-service` ([Fowler][cqrs], [Microsoft CQRS][ms-cqrs]).

| Folder | TypeScript (Node) | Python | Go | Rust | Holds / may not |
|---|---|---|---|---|---|
| commands | `src/<context>/application/commands/<command>/` | `.../<context>/application/commands/` | `internal/<context>/app/command/` | `<context>-app/src/command/` | One handler per command. Loads aggregates through repositories. Returns nothing or an id |
| queries | `src/<context>/application/queries/<query>/` | `.../<context>/views.py` or `queries/` | `internal/<context>/app/query/` | `<context>-app/src/query/` | Read handlers returning DTOs. May not import `domain/` or change state |
| read models | `src/<context>/infrastructure/read-models/` | `.../<context>/adapters/` | `internal/<context>/adapters/` | `<context>-infra` | Projections or SQL views fed by events. No business rules |

**Layers:** as pattern 4, plus the rule `src/*/application/queries/**` may not import `src/*/domain/**` (not linear, needs a tool).

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [ThreeDotsLabs/wild-workouts-go-ddd-example](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example) | Go | 6,471 | 2026-08-27 | MIT | no | `internal/trainings/app/command/` and `app/query/` |
| [marcoturi/fastify-boilerplate](https://github.com/marcoturi/fastify-boilerplate) | TypeScript (Fastify) | 469 | 2026-10-11 | MIT | no | `src/modules/user/commands/create-user/`, `queries/`, `src/shared/cqrs` |
| [jasontaylordev/CleanArchitecture](https://github.com/jasontaylordev/CleanArchitecture) | .NET (reference) | 20,632 | 2026-10-11 | MIT | no | CQRS without DDD aggregates: `src/Application/TodoLists/{Commands,Queries}` |
| [cosmicpython/code](https://github.com/cosmicpython/code), branch `chapter_12_cqrs` | Python | 2,717 | 2025-06-10 (stale) | CC-BY-ND (not a code license, read only) | no | `src/allocation/views.py` beside `service_layer/handlers.py` |

### 6. Vertical slice architecture

**Sources.** Bogard organizes code by request, "encapsulating and grouping all concerns from front-end to back". Rule: "Minimize coupling between slices, and maximize coupling in a slice". Slices are commands and queries, so CQRS comes with it. Each slice picks its own approach, starting with a transaction script and refactoring toward a domain model when smells appear. Shared repositories and services are avoided ([Bogard][vsa]).

**Fits:** many distinct requests that change independently. Works for `crud-service`, and for `domain-core` once complex logic moves into a shared `domain/`. **Does not fit:** a team that does not refactor, by Bogard's own condition ([Bogard][vsa]).

| Folder | TypeScript (Node) | Python | Go | Rust | Holds / may not |
|---|---|---|---|---|---|
| slices | `src/features/<feature>/<request>/` | `src/<pkg>/features/<feature>/<request>.py` | `internal/<feature>/features/<request>/` | `src/features/<feature>/<request>.rs` | Endpoint, request, handler, response, test for one request. May not import another slice |
| domain | `src/domain/` | `src/<pkg>/domain/` | `internal/<feature>/models/` | `src/domain/` | Logic extracted when two slices need it. No slice imports |
| shared | `src/shared/` | `src/<pkg>/shared/` | `internal/pkg/` | `src/shared/` | DB connection, HTTP plumbing, config. No business rules |
| entry | `src/main.ts` | `src/<pkg>/main.py` | `cmd/<bin>/main.go` | `src/main.rs` | Registers slices |

**Layers:** `["src/shared/**", "src/domain/**", "src/features/**", "src/main.ts"]`, plus slices may not import each other (sibling rule).

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [jbogard/ContosoUniversityDotNetCore-Pages](https://github.com/jbogard/ContosoUniversityDotNetCore-Pages) | .NET (originator) | 1,807 | 2026-04-30 | MIT | no | `ContosoUniversity/Pages/{Courses,Students,...}`, each page with its own handler |
| [nadirbad/VerticalSliceArchitecture](https://github.com/nadirbad/VerticalSliceArchitecture) | .NET | 604 | 2026-08-09 | MIT | no | `src/Application/Scheduling/` slices beside `Application/Domain` |
| [mehdihadeli/go-vertical-slice-template](https://github.com/mehdihadeli/go-vertical-slice-template) | Go | 131 | 2025-07-26 | MIT | no | `internal/catalogs/products/features/creatingproduct/{commands,dtos,endpoints,events}` |
| [marcoturi/fastify-boilerplate](https://github.com/marcoturi/fastify-boilerplate) | TypeScript | 469 | 2026-10-11 | MIT | no | README states modules follow vertical slices: `src/modules/user/commands/create-user/` |

Python and Rust: no well-known exemplar. The largest Python result (`wirio-org/python-template`) has 14 stars.

### 7. Modular monolith

**Sources.** A monolith is one deployment unit, which says nothing about its quality. Modules should be business-aligned, built from vertical slices rather than technical layers, with an explicit contract and everything else hidden ([Grzybek][grzybek]). Fowler: design the monolith with "modularity within the software", because boundaries are hard to get right at the start and easier to move inside one process ([Fowler][monolith-first]). Shopify split a Rails monolith into components with public entry points and built Packwerk to "reject changes that break the dependency graph" ([Shopify][shopify]). Spring Modulith makes each top-level package a module, with sub-packages internal ([Spring Modulith][modulith]). NestJS: feature modules, providers private unless exported ([NestJS][nest-modules]).

**Fits:** `domain-core` with two or more bounded contexts in one deployable, or any system several teams share. **Does not fit:** one small context (L3 or L5 is enough).

| Folder | TypeScript (Node) | Python | Go | Rust | Holds / may not |
|---|---|---|---|---|---|
| modules | `src/modules/<module>/` | `src/<pkg>/modules/<module>/` | `internal/<module>/` | `crates/<module>/` | One bounded context, laid out as pattern 3 or 4 inside. May not import another module's internals |
| public API | `src/modules/<module>/index.ts` | `.../<module>/__init__.py` | `internal/<module>/` exported identifiers, privates in `internal/<module>/internal/` | `crates/<module>/src/lib.rs` `pub` items | Facade and integration events. The only thing other modules import |
| shared kernel | `src/shared/` | `src/<pkg>/seedwork/` | `internal/common/` | `crates/kernel/` | Cross-module primitives, messaging. No module's rules |
| composition | `src/main.ts` | `src/<pkg>/main.py` | `cmd/<bin>/main.go` | `crates/app/` | Wires modules together |

Per language: Go's nested `internal/` makes module privacy a compiler rule ([cmd/go][go-internal]). In Rust, a crate per module plus Cargo's ban on cycles makes the module graph explicit. Python needs import-linter's `independence` contract or tach.

**Layers:** `["src/shared/**", "src/modules/**", "src/main.ts"]`, with each module's inner layers from pattern 4 and module independence as a sibling rule.

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [kgrzybek/modular-monolith-with-ddd](https://github.com/kgrzybek/modular-monolith-with-ddd) | .NET (reference) | 14,062 | 2024-06-04 (stale) | MIT | no | `src/Modules/<M>/{Domain,Application,Infrastructure,IntegrationEvents}`, and `Tests/ArchTests` |
| [pgorecki/python-ddd](https://github.com/pgorecki/python-ddd) | Python | 1,046 | 2025-01-03 (stale) | MIT | no | `src/modules/{bidding,catalog,iam}` over `src/seedwork` |
| [Shopify/packwerk](https://github.com/Shopify/packwerk) | Ruby (tool) | 1,923 | 2026-08-26 | MIT | no | `USAGE.md`: `package.yml`, privacy, `package_todo.yml` baseline |
| [spring-projects/spring-modulith](https://github.com/spring-projects/spring-modulith) | Java (reference) | 1,197 | 2026-10-10 | Apache-2.0 | no | `spring-modulith-examples/spring-modulith-example-full` |
| [marcoturi/fastify-boilerplate](https://github.com/marcoturi/fastify-boilerplate) | TypeScript | 469 | 2026-10-11 | MIT | no | README: "No direct imports between modules". They talk through command, query and event buses |

Go, TypeScript and Rust: no well-known exemplar. The Go candidates found have under 40 stars, and the TypeScript ones are small, stale or unlicensed (`mgce/modular-monolith-nodejs`: 309 stars, no license, last push 2022-08). rust-lang/crates.io splits infrastructure into workspace crates but is not organized by business module.

### 8. Feature-Sliced Design (frontend)

**Sources.** Layers from top: app, pages, widgets, features, entities, shared (processes is deprecated). A module may import only from layers "strictly below", and "Slices cannot use other slices on the same layer". App and shared have segments, no slices ([FSD overview][fsd-overview]). "You don't have to use every layer", most projects have at least shared, pages and app. A block that "is never reused" should stay in the page, and "not everything needs to be a feature" ([FSD layers][fsd-layers]). With Next.js, rename the FSD layers to `_app` and `_pages` and keep Next's `app/` or `pages/` at the root as thin re-exports ([FSD with Next.js][fsd-next]).

**Threshold check.** The kit's current rule is "more than five screens, or an entity that two or more screens use". FSD claims to fit "projects and teams of any size", lists no screen count, and names two signals: a project "grown too large and inter-connected" and a team taking on many new members ([FSD overview][fsd-overview]). Its extraction test is reuse across pages ([FSD layers][fsd-layers]). So:
- **Keep:** "an entity that two or more screens use". It is FSD's own reuse test.
- **Widen:** to "an entity or a user action". A shared action is what the features layer is for.
- **Drop:** "more than five screens". No source supports the number. Five screens with nothing shared fit the small tree.
- **Add:** a team that is growing, FSD's second signal.
- **Note:** the small tree is already FSD's minimal form (shared, pages, app) under other names, so moving up is renames, not a rewrite: `components/` to `shared/ui/`, `lib/` to `shared/api/` and `shared/lib/`, `src/` entry to `app/`.

The `fsd` tree, `layers` list and steiger install the kit had in `kit/languages/react.yaml` (now `kit/layouts/fsd.md`) match these sources and the registry (steiger 0.7.0, plugin 0.8.0, both 2026-09-25).

**Layers:** `["src/shared/**", "src/entities/**", "src/features/**", "src/widgets/**", "src/pages/**", "src/app/**"]` (as in the kit), plus no imports between slices of one layer (steiger `no-cross-imports`). steiger resolves underscore-prefixed layers such as `_pages` and `_app`, preferring them over unprefixed ones: `@feature-sliced/steiger-plugin` 0.8.0 depends on `@feature-sliced/filesystem` ^3.1.0, which added them ([steiger PR #233](https://github.com/feature-sliced/steiger/pull/233), test `packages/steiger-plugin-fsd/src/prefixed-layers.spec.ts`).

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [noveogroup-amorgunov/nukeapp](https://github.com/noveogroup-amorgunov/nukeapp) | React | 414 | 2026-09-28 | MIT | no | `src/{app,pages,features,entities,shared}`, and steiger in `package.json` |
| [yurisldk/realworld-react-fsd](https://github.com/yurisldk/realworld-react-fsd) | React | 532 | 2026-05-25 | MIT | no | FSD's minimal form: only `src/{app,pages,shared}` |
| [Snouzy/workout-cool](https://github.com/Snouzy/workout-cool) | Next.js | 8,595 | 2026-09-20 | MIT | no | A real product: `src/{entities,features,widgets,shared}` beside Next's routing, with some `src/components` left over |

The official [feature-sliced/examples](https://github.com/feature-sliced/examples) has no license, so it is not listed.

### 9. Small frontend tree

**Sources.** React's FAQ: group by feature or route, or by file type. Keep nesting to "a maximum of three or four nested folders". Don't "spend more than five minutes" choosing, and split as the app grows ([React FAQ][react-faq]). Next.js is "unopinionated", keeps routing in `app/`, and lists keeping project files outside `app/` as one strategy. Private `_folders` colocate non-route files ([Next.js][next-structure]).

**Fits:** a frontend where no entity or user action is shared by two or more screens. **Does not fit:** past that point (L9).

| Folder | React (Vite) | React (Next.js App Router) | Holds / may not |
|---|---|---|---|
| entry | `src/main.tsx`, `src/app.tsx` | `app/layout.tsx` | Entry and routing shell, nothing else |
| screens | `src/pages/<page>/` | `app/<route>/page.tsx`, `app/<route>/_components/` | One folder per screen with parts only it uses. May not import another page |
| shared components | `src/components/` | `src/components/` | Used by two or more pages. No data fetching |
| lib | `src/lib/` | `src/lib/` | API client, platform bindings, helpers. No JSX |
| styles | `src/styles/` | a global CSS file imported by `app/layout.tsx` | Tokens and global CSS |

**Layers (proposed for the kit, which had none for the small tree; now in `kit/layouts/frontend-small.md`):** `["src/styles/**", "src/lib/**", "src/components/**", "src/pages/**", "src/*.tsx"]`, plus pages may not import each other.

**Exemplars**

| Repo | Stack | Stars | Last push | License | Archived | Look at |
|---|---|---|---|---|---|---|
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | React (Vite) | 45,946 | 2026-10-08 | MIT | no | `frontend/src/{routes,components,hooks,lib,client}`: a real small tree |
| [vitejs/vite](https://github.com/vitejs/vite) | React (Vite) | 83,312 | 2026-10-09 | MIT | no | `packages/create-vite/template-react-ts/`: the starting point the kit's tree grows from |

### 10. Feature folders (bulletproof-react)

Added because it is popular and distinct: one layer of features between shared code and the app, no entities or widgets. **Source:** `src/{app,features,components,hooks,lib,stores,types,utils,config}`. Features do not import each other, code flows from shared to features to app, enforced with `import/no-restricted-paths` zones ([bulletproof-react][bulletproof]).

**Fits:** a team that wants feature isolation without FSD's six layers. **Does not fit:** many entities shared across features, which FSD's entities layer exists for.

**Layers:** `["src/{components,hooks,lib,stores,types,utils,config}/**", "src/features/**", "src/app/**"]`, plus features may not import each other.

**Exemplar:** [alan2207/bulletproof-react](https://github.com/alan2207/bulletproof-react), React, 35,967 stars, last push 2026-05-14, MIT, not archived. Look at `apps/react-vite/src/` and `docs/project-structure.md`.

## Combinations

**Compose well**
- **DDD inside hexagonal.** The domain layer is the hexagon's center, the application layer holds use cases and ports, infrastructure holds the adapters. Vernon's own samples use `domain/model`, `application`, `port/adapter` ([IDDD_Samples](https://github.com/VaughnVernon/IDDD_Samples)). Microsoft's layering is the same with domain depending on nothing ([Microsoft DDD][ms-ddd]).
- **CQRS inside one bounded context.** Fowler limits CQRS to specific contexts ([Fowler][cqrs]). Wild Workouts puts `app/command` and `app/query` in each context ([wild-workouts](https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example)).
- **Modular monolith whose modules are bounded contexts,** each laid out as DDD plus hexagonal: kgrzybek and python-ddd above. Grzybek's modules are business-aligned and built from vertical slices ([Grzybek][grzybek]).
- **Vertical slices with CQRS,** since every slice is a command or a query ([Bogard][vsa]). Vertical slices inside each module of a modular monolith: fastify-boilerplate.
- **FSD or the small tree on the frontend, any of these on the backend.** They are separate roots with separate `layers` lists. FSD `entities` are UI-side models with their own `api` segment ([FSD layers][fsd-layers]), not the backend's aggregates. The two share only the wire contract.

**Conflict**
- **Technical layers at the top level of a growing system.** Fowler wants domain modules at the top, layered inside ([Fowler][pdd]). Grzybek wants modules from vertical slices, not technical layers ([Grzybek][grzybek]). `src/controllers/` plus `src/modules/` in one tree has two answers to where code goes.
- **Vertical slices with mandatory shared repositories and services.** Bogard avoids exactly those shared abstractions ([Bogard][vsa]). A shared `domain/` that slices refactor into is fine.
- **CQRS on a CRUD system.** Both Fowler and Microsoft advise against it ([Fowler][cqrs], [Microsoft CQRS][ms-cqrs]).
- **A hexagonal core inside framework ActiveRecord models.** An ActiveRecord model is a table ([Laravel][laravel]), while the hexagon's inside must not depend on its data source ([Cockburn][hexagonal]). Either keep the framework's MVC (L2) or put the domain in plain classes outside `app/models`.
- **FSD's `app` and `pages` with Next.js routing folders,** unless the FSD layers are renamed `_app` and `_pages` ([FSD with Next.js][fsd-next]).
- **Mutual dependencies between Rust crates.** Cargo rejects them, so two modules that call each other need a contracts crate or events.

## What this does not cover

- **Deployment topology:** microservices, serverless and monorepo build tools (Nx, Turborepo, Bazel). These shape repositories, not folders inside one module.
- **Event sourcing,** beyond its link with CQRS ([Microsoft CQRS][ms-cqrs]).
- **Native mobile layouts** (Swift, Kotlin) and Java/.NET trees. Java and .NET appear only as reference exemplars and tools.
- **Size numbers.** No source gives a team size, screen count or use-case count for any switch. The table uses observable signals instead, and none of the rows has been calibrated on the user's own repositories.
- **Tool trials.** Versions, release dates and commands come from the registries and each tool's README. Only Cargo's cycle rejection was run here (cargo 1.95.0). None of the linters has been run on a real repository for this record.
- **Kit changes.** Applied in decision 29: the catalog in `kit/layouts/` replaces the `layout` key of `kit/languages/react.yaml`, the FSD threshold follows the reuse rule, the small tree has `layers`, and sibling rules are named in the Layout Decision and enforced by the pattern's checker.

[pdd]: https://martinfowler.com/bliki/PresentationDomainDataLayering.html
[hexagonal]: https://alistair.cockburn.us/hexagonal-architecture/
[onion]: https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/
[clean]: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
[ddd-ref]: https://www.domainlanguage.com/ddd/reference/
[bc]: https://martinfowler.com/bliki/BoundedContext.html
[ms-ddd]: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice
[iddd]: https://www.informit.com/store/implementing-domain-driven-design-9780321834577
[cqrs]: https://martinfowler.com/bliki/CQRS.html
[ms-cqrs]: https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs
[cosmic-cqrs]: https://www.cosmicpython.com/book/chapter_12_cqrs.html
[vsa]: https://www.jimmybogard.com/vertical-slice-architecture/
[grzybek]: https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer
[monolith-first]: https://martinfowler.com/bliki/MonolithFirst.html
[strangler]: https://martinfowler.com/bliki/StranglerFigApplication.html
[shopify]: https://shopify.engineering/shopify-monolith
[modulith]: https://docs.spring.io/spring-modulith/reference/fundamentals.html
[nest-modules]: https://docs.nestjs.com/modules
[fsd-overview]: https://feature-sliced.design/docs/get-started/overview
[fsd-layers]: https://feature-sliced.design/docs/reference/layers
[fsd-next]: https://feature-sliced.design/docs/guides/tech/with-nextjs
[react-faq]: https://legacy.reactjs.org/docs/faq-structure.html
[next-structure]: https://nextjs.org/docs/app/getting-started/project-structure
[bulletproof]: https://github.com/alan2207/bulletproof-react/blob/master/docs/project-structure.md
[rails]: https://guides.rubyonrails.org/getting_started.html
[django]: https://docs.djangoproject.com/en/5.2/intro/tutorial01/
[django-faq]: https://docs.djangoproject.com/en/5.2/faq/general/
[laravel]: https://laravel.com/docs/structure
[express-faq]: https://expressjs.com/en/starter/faq.html
[adonis]: https://docs.adonisjs.com/guides/getting-started/folder-structure
[go-layout]: https://go.dev/doc/modules/layout
[go-internal]: https://pkg.go.dev/cmd/go#hdr-Internal_Directories
[go-spec]: https://go.dev/ref/spec#Import_declarations
[src-layout]: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
[cargo-ws]: https://doc.rust-lang.org/cargo/reference/workspaces.html
[depcruise]: https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md
[boundaries]: https://github.com/javierbrea/eslint-plugin-boundaries
[steiger]: https://github.com/feature-sliced/steiger
[steiger-rules]: https://github.com/feature-sliced/steiger/tree/master/packages/steiger-plugin-fsd/src
[il-layers]: https://github.com/seddonym/import-linter/blob/main/docs/contract_types/layers.md
[lucid]: https://lucid.adonisjs.com/docs/migrations
[django-3]: https://docs.djangoproject.com/en/5.2/intro/tutorial03/
[tach]: https://github.com/gauge-sh/tach
[go-arch-lint]: https://github.com/fe3dback/go-arch-lint
[cargo-modules]: https://github.com/regexident/cargo-modules
[cargo-pup]: https://github.com/DataDog/cargo-pup
[packwerk-repo]: https://github.com/Shopify/packwerk/blob/main/USAGE.md
