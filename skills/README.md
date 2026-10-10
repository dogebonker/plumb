# Skills

The factory skills land here, built in roadmap order. Each follows the open Agent Skills format, so it runs in any compatible harness.

## Install

```bash
ln -s ~/Work/software-factory/skills/factory-* ~/.claude/skills/
```

S1 review needs the [`polish`](https://github.com/tenequm/skills/tree/main/skills/polish) skill. Pond is used when its MCP tools are available.

## Run one change

`/factory-triage <task>`, then `/factory-plan`, then `/factory-build` and `/factory-review` once per slice. Each skill resumes from `.factory/changes/<slug>/status.yaml`, so start a fresh session whenever a skill tells you to.

## Skills

| Skill | Roadmap step | Purpose |
| --- | --- | --- |
| `factory-triage` | S1 | Track, slug, branch, `status.yaml`. Money and BDD detection in S2, lens profile in S3 |
| `factory-plan` | S1 | One combined plan doc for the tracer bullet; split into gates in S2 |
| `factory-build` | S1 | Packet, fresh executor, red then green check |
| `factory-review` | S1 | Allowed-files and frozen-contract checks, `/polish`, human sign-off |
| `factory-product` | S2 | Product gate |
| `factory-architecture` | S2 | Architecture gate |
| `factory-slices` | S2 | Vertical slice plan |
| `factory-research` | S4 | Research firewall |
| `factory-interface` | S4 | Interface Design, cost card, challenge panel |
| `factory-reconcile` | S7 | Fold shipped work back into specs, ADRs and lessons |
| `factory-prune` | S7 | Repository audit and prune slices |
