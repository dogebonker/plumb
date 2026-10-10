# Factory kit

Starter content for `~/.software-factory/`, the kit every factory skill reads. Copy it once (`-n` keeps any file you already have), then keep it as your own git repository: your edits there are your taste, synced to every machine and server you run the factory on.

```bash
mkdir -p ~/.software-factory
cp -Rn ~/Work/software-factory/kit/. ~/.software-factory/
git -C ~/.software-factory init
```

| Path | What it holds |
| --- | --- |
| `nfr-catalog/<domain>.md` | Default promises per domain, offered by triage when a project's constraints registry is created |
| `profiles/<profile>.yaml` | Lens profiles: which design-book lenses load in which step, and the default domain model |
| `languages/<pack>.yaml` | Language packs per stack: the index pack, extra rule packs, linter rules to propose, and review checks (React: react-doctor) |
| `adapters/<language>.md` | Per language: how to write a signature as a stub and how to type-check it |
| `packs.lock.yaml` | The pinned hash of every pack the profiles name |
