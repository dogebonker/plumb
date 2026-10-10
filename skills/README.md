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

## Headless mode

`runner/factory_run.py` drives changes whose `mode` is `headless` through their pull request, one `factory/<slug>` branch and one pull request per change. On every pass it re-derives approvals from approvers' APPROVED reviews (`approve <gate>`, `sign off slice NN`) and resets any it cannot back, passes approvers' replies to a waiting change, and runs the next skill through a headless harness (default `claude -p`). Run one pass per cron tick or CI job, in a clone used only by the runner:

```bash
python3 runner/factory_run.py <clone> --approvers alice,bob
```

- The runner works on a change only after an approver starts it with an APPROVED review whose first line is `start`. After that it runs the harness only on a branch head that the runner or the harness itself left, or that an approver reviewed: a push by anyone else waits for an approver's review. A later CHANGES_REQUESTED review by an approver revokes their earlier approvals.
- Each skill run happens in a fresh throwaway clone of the branch, so nothing the harness writes, including `.git` config, reaches the runner's clone; `--setup` (for example `npm ci`) prepares that clone, and uncommitted work is discarded with it. A new branch head counts as the harness's own only when it fast-forwards the head the harness started from with commits created in that clone. A harness that pulls someone else's concurrent push and then rewrites it (amend, squash) can still launder it: protect `factory/*` so only the runner's account can push there.
- The default harness, `claude -p --setting-sources user --strict-mcp-config`, ignores the repository's own Claude settings and MCP servers. The skills still run the repository's tests and dev commands, so run the harness in a container or VM with a token scoped to this repository.
- Gate approvals are also GitHub pull-request approvals: protect the default branch with "dismiss stale approvals" so an early `approve product` cannot merge later code.
- Approvers come only from `--approvers`. The login `gh` runs as on the server never counts, even when listed, so give the runner its own GitHub account.
- Gates skipped in the change's first commit stay skipped only when an approver's `start` review covers that commit; any other `skipped` gate is reset to pending.
- The server needs the skills installed, the kit, `gh` signed in, `pond init` against the shared store, the runtimes the adapters call, and a harness allowed to edit files and run them unattended.
- Interactive triage creates the change and its pull request; the runner takes over from there.
- The hard-gate hook guards the harness's editing tools only. Headless enforcement rests on the runner resetting what no approval backs.

Self-check: `python3 runner/test_factory_run.py`.

## Run one change

`/factory-triage <task>`, then the gates `/factory-product`, `/factory-architecture`, `/factory-interface`, `/factory-slices` (track small: slices only), then `/factory-build` and `/factory-review` once per slice, then `/factory-reconcile` before merging. Each skill resumes from `.factory/changes/<slug>/status.yaml`, so start a fresh session whenever a skill tells you to.

## Skills

| Skill | Roadmap step | Purpose |
| --- | --- | --- |
| `factory-triage` | S1, S2 | Track, slug, branch, `status.yaml`; modules, BDD and money detection into `lenses.yaml`. Lens profile in S3 |
| `factory-build` | S1 | Packet, fresh executor, red then green check |
| `factory-review` | S1, S6 | Mechanical checks (files, contract, red/green, lint, language checks, dependency rule, dead code), `/polish` with lens rubrics, APoSD and Money reviewers, regression proofs, human sign-off |
| `factory-product` | S2 | Product gate: problem, rules and examples, promises, constraints |
| `factory-architecture` | S2, S4 | Architecture gate: research behind a firewall, budgets, ADRs |
| `factory-interface` | S2, S4, S6 | Interface gate: signatures that compile through the kit's adapters, cost card, a challenge panel of one lens per reviewer, the human's decisions, coverage |
| `factory-slices` | S2 | Slices gate: vertical slices, tracer bullet first |
| `factory-shared` | S2, S3 | Not a skill: `gates.md` (gate rules), `packs.md` (lens and language pack loading), `constraints.md` (registry template) |
| `factory-reconcile` | S7 | Before merge: ADRs, standing constraints, living product and glossary in `.factory/system/`; calibration and lessons into the kit's `principles.md` |
| `factory-packs` | S7 | Pin check, upstream changes read from changelogs, re-review of changes that relied on a changed rule, pin bumps |
| `factory-security` | S11 | Threat model from the code, pinned scanners, the `security-audit` method with routed knowledge, proven findings as small changes |
| `factory-prune` | S7 | Repository audit with the simplification ladder; protected code filtered out; each approved item runs as a small change |
