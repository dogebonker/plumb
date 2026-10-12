# Factory kit

The kit every factory skill reads at `~/.software-factory/`: a symlink to this folder, so the kit lives in the factory repository and syncs with it. Edits the factory makes here (principles from reconcile, pin bumps from `/factory-packs`) are commits in this repository.

```bash
ln -s ~/Work/software-factory/kit ~/.software-factory
```

| Path | What it holds |
| --- | --- |
| `principles.md` | Your principles and quiet rules, kept up to date by reconcile from your answers |
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
| `packs.lock.yaml` | The pinned hash of every pack the factory loads |
