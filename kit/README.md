# Factory kit

The kit every factory skill reads as `<kit>`: `~/.software-factory/framework/<commit>/kit`, this folder unpacked from one factory commit, where `<commit>` is the framework commit in the project's `.software-factory/factory.lock` ([gates.md](../skills/factory-shared/gates.md), Paths). Projects never edit it. Changes to the kit are commits in this repository (pin bumps from `/factory-packs`), and a project takes them with `/factory-upgrade`.

`/factory-init` installs a commit, links its skills into the project and writes the project's `factory.lock`. To install a commit by hand:

```bash
[ -L ~/.software-factory ] && rm ~/.software-factory   # the old link to kit/: the cache and the user layer must not write into this repository
c=$(git -C ~/Work/software-factory rev-parse HEAD)
mkdir -p ~/.software-factory/framework/$c ~/.software-factory/user
git -C ~/Work/software-factory archive $c kit skills | tar -x -C ~/.software-factory/framework/$c
```

Then link its skills into the project and write its `factory.lock` ([skills/README.md](../skills/README.md), Install).

**Developing the factory.** A project's lock may hold `framework: { dev_path: <absolute path to a factory checkout> }` instead of a commit. `<kit>` is then `<dev_path>/kit`, the skills must be linked from `<dev_path>/skills`, and the version check uses that checkout's HEAD. Use it only in a project where you test changes to the factory itself.

| Path | What it holds |
| --- | --- |
| `principles.md` | Framework defaults: the first of the three principle layers, before the user layer `~/.software-factory/user/principles.md` and the project's `.software-factory/principles.md`. It still holds one user's principles and quiet rules until they move to the user layer; reconcile writes the project's file, never this one |
| `nfr-catalog/<domain>.md` | Default promises per domain, offered by triage when a project's constraints registry is created |
| `profiles/<profile>.yaml` | Lens profiles: which design-book lenses load in which step, and the default domain model |
| `languages/<pack>.yaml` | Language packs per stack: the index pack, extra rule packs, linter rules to propose, and review checks (React: react-doctor) |
| `layouts/` | Reference layouts the architecture gate proposes: layered, MVC, hexagonal, DDD, CQRS, vertical slice, modular monolith, FSD, a small frontend tree and feature folders, each with Layout lines per stack, layers, sibling rules, a pinned checker and exemplar repositories; `index.yaml` picks by profile and size |
| `adapters/<language>.md` | Per language: how to write a signature as a stub, type-check it, run one BDD feature, find step definitions, list imports and find dead code |
| `ui/slop-patterns.yaml`, `ui/slop-metrics.js` | factory-ui-ux's AI-slop catalog (22 patterns, most with tested code checks) and the computed-style script run in a real browser |
| `ui/tools.yaml` | The pinned UI tools: the DESIGN.md linter, impeccable's detector, Playwright, axe |
| `security/index.yaml` | Routing for `factory-security`: the method file per component and the approved knowledge sources, with known errors to skip |
| `security/tools.yaml`, `security/gitleaks.toml` | The pinned scanners and how they run |
| `ci/ci_runs.py`, `ci/tools.yaml`, `ci/catalog.md` | factory-ci's measurement script (with its self-check), its tools, and the catalog of fixes with their guards |
| `packs.lock.yaml` | The framework's pinned hash of every pack the factory loads, bumped by `/factory-packs`; init and upgrade copy them into a project's `factory.lock` |
