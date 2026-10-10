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
| `adapters/<language>.md` | Per language: how to write a signature as a stub, type-check it, run one BDD feature, find step definitions, list imports and find dead code |
| `security/index.yaml` | Routing for `factory-security`: the method file per component and the approved knowledge sources, with known errors to skip |
| `security/tools.yaml`, `security/gitleaks.toml` | The pinned scanners and how they run |
| `packs.lock.yaml` | The pinned hash of every pack the factory loads |
