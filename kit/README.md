# Plumb kit

The kit every Plumb skill reads as `<kit>`: `~/.plumb/framework/<commit>/kit`, this folder unpacked from one Plumb commit, where `<commit>` is the framework commit in the project's `.plumb/plumb.lock` ([gates.md](../skills/plumb-shared/gates.md), Paths). Projects never edit it. Changes to the kit are commits in this repository (pin bumps from `/plumb-packs`), and a project takes them with `/plumb-upgrade`.

`bin/plumb-install <ref>` installs a commit, and `/plumb-init` links its skills into the project and writes the project's `plumb.lock`. To install a commit by hand instead:

```bash
[ -L ~/.plumb ] && rm ~/.plumb   # the old link to kit/: the cache and the user layer must not write into this repository
c=$(git -C ~/Work/plumb rev-parse HEAD)
mkdir -p ~/.plumb/framework/$c ~/.plumb/user
git -C ~/Work/plumb archive $c kit skills hooks | tar -x -C ~/.plumb/framework/$c
```

Then link its skills into the project and write its `plumb.lock` ([skills/README.md](../skills/README.md), Install).

**Developing Plumb.** A project's lock may hold `framework: { dev_path: <absolute path to a Plumb checkout> }` instead of a commit. `<kit>` is then `<dev_path>/kit`, the skills must be linked from `<dev_path>/skills`, and the version check uses that checkout's HEAD. Use it only in a project where you test changes to Plumb itself.

| Path | What it holds |
| --- | --- |
| `principles.md` | Framework defaults: the first of the three principle layers, before the user layer `~/.plumb/user/principles.md` and the project's `.plumb/principles.md`. It holds no one's taste; `/plumb-init` offers the author's former principles for the user layer. Reconcile writes the project's file, never this one |
| `nfr-catalog/<domain>.md` | Default promises per domain, offered by triage when a project's constraints registry is created |
| `profiles/<profile>.yaml` | Lens profiles: which design-book lenses load in which step, and the default domain model |
| `languages/<pack>.yaml` | Language packs per stack: the index pack, extra rule packs, linter rules to propose, and review checks (React: react-doctor) |
| `layouts/` | Reference layouts the architecture gate proposes: layered, MVC, hexagonal, DDD, CQRS, vertical slice, modular monolith, FDA, FSD, a small frontend tree and feature folders, with Layout lines, layers, sibling rules and checker guidance; existing conventions win and `index.yaml` strongly prefers FDA for new frontends |
| `archgraph.py` | Shared pinned-tool discovery, bounded build/review context and new-violation gates; [commands and evidence rules](../skills/plumb-shared/archgraph.md#shared-adapter) |
| `adapters/<language>.md` | Per language: how to write a signature as a stub, type-check it, run one BDD feature, find step definitions, list imports and find dead code |
| `ui/slop-patterns.yaml`, `ui/slop-metrics.js` | plumb-ui-ux's AI-slop catalog (22 patterns, most with tested code checks) and the computed-style script run in a real browser |
| `ui/tools.yaml` | The pinned UI tools: the DESIGN.md linter, impeccable's detector, Playwright, axe |
| `security/index.yaml` | Routing for `plumb-security`: the method file per component and the approved knowledge sources, with known errors to skip |
| `security/tools.yaml`, `security/gitleaks.toml` | The pinned scanners and how they run |
| `ci/ci_runs.py`, `ci/tools.yaml`, `ci/catalog.md` | plumb-ci's measurement script (with its self-check), its tools, and the catalog of fixes with their guards |
| `packs/` | The ten configured book rubrics as exact `name@hash/` trees, with full, mini and nano files plus the upstream license; shipped with every framework install and isolated snapshot |
| `packs.lock.yaml` | The framework's pin of every pack Plumb loads: its source, its folder there (`path`) and the git tree hash of that folder, bumped by `/plumb-packs`. Init and upgrade copy them into a project's `plumb.lock` and fetch each into `~/.plumb/packs/<name>@<hash>/` with `bin/plumb-packs-fetch` |
