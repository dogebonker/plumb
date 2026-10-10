# Skills

The factory skills land here, built in roadmap order. Each follows the open Agent Skills format, so it runs in any compatible harness.

## Install

```bash
ln -s ~/Work/software-factory/skills/factory-* ~/.claude/skills/
```

Install them as a set: the skills share `factory-shared/gates.md`. Review needs the [`polish`](https://github.com/tenequm/skills/tree/main/skills/polish) skill. Pond is used when its MCP tools are available.

## Run one change

`/factory-triage <task>`, then the gates `/factory-product`, `/factory-architecture`, `/factory-interface`, `/factory-slices` (track small: slices only), then `/factory-build` and `/factory-review` once per slice. Each skill resumes from `.factory/changes/<slug>/status.yaml`, so start a fresh session whenever a skill tells you to.

## Skills

| Skill | Roadmap step | Purpose |
| --- | --- | --- |
| `factory-triage` | S1 | Track, slug, branch, `status.yaml`. Money and BDD detection in S2, lens profile in S3 |
| `factory-build` | S1 | Packet, fresh executor, red then green check |
| `factory-review` | S1 | Allowed-files and frozen-contract checks, `/polish`, human sign-off |
| `factory-product` | S2 | Product gate: problem, rules and examples, promises, constraints |
| `factory-architecture` | S2 | Architecture gate: research facts, budgets, ADRs |
| `factory-interface` | S2 | Interface gate: human-decided signatures, coverage. Cost card and challenge panel in S4 |
| `factory-slices` | S2 | Slices gate: vertical slices, tracer bullet first |
| `factory-shared` | S2 | Not a skill: `gates.md`, the gate rules every skill follows |
| `factory-research` | S4 | Research firewall |
| `factory-reconcile` | S7 | Fold shipped work back into specs, ADRs and lessons |
| `factory-prune` | S7 | Repository audit and prune slices |
