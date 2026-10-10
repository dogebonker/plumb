# Skills

The factory skills land here, built in roadmap order. Each follows the open Agent Skills format, so it runs in any compatible harness.

## Install

```bash
ln -s ~/Work/software-factory/skills/factory-* ~/.claude/skills/
```

The skills read the kit at `~/.software-factory/`. Set it up once from [kit/](../kit/README.md).

Install them as a set: the skills share `factory-shared/` (gate rules, pack loading, templates). Review needs the [`polish`](https://github.com/tenequm/skills/tree/main/skills/polish) skill. Pond is used when its MCP tools are available.

## Hard gates

`hooks/factory_gate.py` is a Claude Code `PreToolUse` hook. On a branch with an active factory change it blocks edits to files outside `.factory/` while a gate is unapproved, after an approved gate document changed, or outside the current slice's Allowed files and logged deviations. Add it to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{ "type": "command", "command": "python3 <factory repo>/hooks/factory_gate.py" }]
      }
    ]
  }
}
```

What it leaves to others:

- It blocks but never changes `status.yaml`: after a hash mismatch, the gate skill it names reverts the gate and everything after it.
- A frozen signature changed inside an allowed file is caught by review's contract check, not by the hook.
- It guards the editing tools only; shell commands that write files pass.

Self-check: `python3 hooks/test_factory_gate.py`.

## Run one change

`/factory-triage <task>`, then the gates `/factory-product`, `/factory-architecture`, `/factory-interface`, `/factory-slices` (track small: slices only), then `/factory-build` and `/factory-review` once per slice, then `/factory-reconcile` before merging. Each skill resumes from `.factory/changes/<slug>/status.yaml`, so start a fresh session whenever a skill tells you to.

## Skills

| Skill | Roadmap step | Purpose |
| --- | --- | --- |
| `factory-triage` | S1, S2 | Track, slug, branch, `status.yaml`; modules, BDD and money detection into `lenses.yaml`. Lens profile in S3 |
| `factory-build` | S1 | Packet, fresh executor, red then green check |
| `factory-review` | S1, S6 | Mechanical checks (files, contract, red/green, language checks, dependency rule, dead code), `/polish` with lens rubrics, APoSD and Money reviewers, regression proofs, human sign-off |
| `factory-product` | S2 | Product gate: problem, rules and examples, promises, constraints |
| `factory-architecture` | S2, S4 | Architecture gate: research behind a firewall, budgets, ADRs |
| `factory-interface` | S2, S4, S6 | Interface gate: signatures that compile through the kit's adapters, cost card, a challenge panel of one lens per reviewer, the human's decisions, coverage |
| `factory-slices` | S2 | Slices gate: vertical slices, tracer bullet first |
| `factory-shared` | S2, S3 | Not a skill: `gates.md` (gate rules), `packs.md` (lens and language pack loading), `constraints.md` (registry template) |
| `factory-reconcile` | S7 | Before merge: ADRs, standing constraints, living product and glossary in `.factory/system/` |
| `factory-prune` | S7 | Repository audit and prune slices |
