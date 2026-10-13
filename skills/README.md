# Skills

The factory skills land here, built in roadmap order. Each follows the open Agent Skills format, so it runs in any compatible harness.

## Install

`bin/factory-install <ref>` installs a factory commit into the framework cache, once per machine; `/factory-init` then links that commit's skills into the project, writes its lock, fetches the packs it pins with `bin/factory-packs-fetch` and migrates an old `.factory/` with `bin/factory-migrate`. By hand, from the repository root, with that commit installed in the framework cache ([kit/](../kit/README.md)):

```bash
[ -L ~/.software-factory ] && rm ~/.software-factory   # the old link to kit/: the cache and the user layer must not write into the factory repository
c=<framework commit>; f=~/.software-factory/framework/$c
mkdir -p .software-factory .claude/skills "$(git rev-parse --git-path info)"
ln -s $f/skills/factory-* $f/skills/ui-hard-gate .claude/skills/
x="$(git rev-parse --git-path info/exclude)"; for p in ".claude/skills/factory-*" .claude/skills/ui-hard-gate; do grep -qxF "$p" "$x" || echo "$p" >> "$x"; done
{ echo "framework: { commit: $c, installed: $(date +%F) }"; sed -n '/^packs:/,$p' $f/kit/packs.lock.yaml; echo "skills_linked: [.claude/skills]"; } > .software-factory/factory.lock
$f/bin/factory-packs-fetch .   # each pin into ~/.software-factory/packs/<name>@<hash>/
```

Self-checks: `python3 bin/test_factory_install.py`, `python3 bin/test_factory_migrate.py`, `python3 bin/test_factory_packs_fetch.py`.

The links are machine-specific, so `.claude/skills/factory-*` and `.claude/skills/ui-hard-gate` stay out of git through `.git/info/exclude`, and a project's own skills there are unaffected: review's committed-source check and rewind's `git clean` would otherwise trip over them or delete them. To develop the factory, link from a checkout's `skills/` instead and write `framework: { dev_path: <that checkout> }` (gates.md, Paths).

The skills read the kit as `<kit>`, the framework cache's `kit/` for that commit, and the project's state under `.software-factory/` ([gates.md](factory-shared/gates.md), Paths).

Install them as a set: the skills share `factory-shared/` (gate rules, pack loading, templates, the playbook contract). Pond is used when its MCP tools are available.

## Hard gates

`hooks/factory_gate.py` is a Claude Code `PreToolUse` hook. On a branch with an active factory change it blocks edits to files outside `.software-factory/` and the root `DESIGN.md` while a gate is unapproved, after an approved gate document changed, or outside the current slice's Allowed files and logged deviations. It also blocks them while an active change's `factory.lock` is missing or names no framework, and whenever `.factory/changes/` holds a change that is not reconciled, whatever `.software-factory/` already holds: run `/factory-init` to migrate that branch, local or remote. Edits under `.factory/` and `.software-factory/` stay open so init can run. `/factory-init` offers to add it to the project's `.claude/settings.local.json`, run from the locked framework (`<framework>` is `~/.software-factory/framework/<commit>` or the `dev_path`); by hand:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{ "type": "command", "command": "python3 <framework>/hooks/factory_gate.py" }]
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
- The operator installs each framework commit the server may run with `bin/factory-install <commit>` (`~/.software-factory/framework/<commit>/`, [kit/](../kit/README.md)). The lock comes from the change's branch, which the harness can write, so it only selects among installed commits: the runner skips a change whose lock is missing, names a `dev_path`, names anything but a full 40-hex commit installed on the server, or pins packs other than that commit's `kit/packs.lock.yaml`. The operator fetches packs with `<framework>/bin/factory-packs-fetch <framework>/kit/packs.lock.yaml` for each installed commit, never from a branch's lock. Link the skills user-level, into `~/.claude/skills/`, from that cache commit: a project's links are untracked, so the throwaway clone has none, and `--setting-sources user` may skip project skills anyway. One server therefore runs one framework commit at a time. The operator also runs that commit's `bin/factory-packs-fetch` on a checkout of each change's branch, so the packs its lock pins are in the pack cache (`~/.software-factory/packs/<name>@<hash>/`); a skill runs without a pack missing there. It also needs `gh` signed in, `pond init` against the shared store, the runtimes the adapters call, and a harness allowed to edit files and run them unattended.
- Interactive triage creates the change and its pull request; the runner takes over from there.
- The hard-gate hook guards the harness's editing tools only. Headless enforcement rests on the runner resetting what no approval backs.

Self-check: `python3 runner/test_factory_run.py`.

## Run one change

`/factory-triage <task>`, then the gates `/factory-product`, `/factory-architecture`, `/factory-interface`, `/factory-slices` (track small: slices only), then `/factory-build`, which runs on autopilot: each milestone's slices, its review and your sign-off, then the next milestone, then `/factory-reconcile` before merging. Each skill resumes from `.software-factory/changes/<slug>/status.yaml`, so a fresh session can pick up at any step.

## Skills

| Skill | Roadmap step | Purpose |
| --- | --- | --- |
| `factory-init` | S14 | Sets a repository up: detects the harness, stack and CI, installs and locks a framework commit (or a `dev_path`), migrates `.factory/`, writes `factory.lock` and `principles.md`, links the skills, offers the hard-gate hook and the user layer's principles |
| `factory-upgrade` | S14 | Moves the lock to another framework commit or `dev_path`: the log and decisions in between, the install, new pins, relinked skills |
| `factory-triage` | S1, S2 | Track, slug, branch, `status.yaml`; modules, BDD and money detection into `lenses.yaml`. Lens profile in S3 |
| `factory-build` | S1 | Packet, fresh executor, red then green check, mechanical checks per slice, a milestone's slices back to back |
| `factory-review` | S1, S6 | Mechanical checks (files, contract, red/green, lint, language checks, dependency rule, dead code), review agents with lens rubrics, APoSD, UI/UX, Security and Money reviewers, validated fixes applied, regression proofs, human sign-off, once per milestone |
| `factory-product` | S2 | Product gate: problem, rules and examples, promises, constraints |
| `factory-architecture` | S2, S4 | Architecture gate: research behind a firewall, budgets, ADRs |
| `factory-interface` | S2, S4, S6 | Interface gate: signatures that compile through the kit's adapters, cost card, a challenge panel of one lens per reviewer, the human's decisions, coverage |
| `factory-slices` | S2 | Slices gate: vertical slices, tracer bullet first |
| `factory-shared` | S2, S3 | Not a skill: `gates.md` (gate rules), `packs.md` (lens and language pack loading), `constraints.md` (registry template) |
| `factory-reconcile` | S7 | Before merge: the examples tried on the running product, then ADRs, standing constraints, living product and glossary in `.software-factory/system/`; calibration and lessons into the project's `.software-factory/principles.md`, with rules shared by two projects proposed for the user layer |
| `factory-packs` | S7 | Pin check, upstream changes read from changelogs, re-review of changes that relied on a changed rule, pin bumps |
| `factory-ui-ux` | S9 | The repository's DESIGN.md (created by guide, enforced for UI changes), optional mockup screenshots at the product gate, mechanical de-slop, anchored critique of rendered screens |
| `factory-ci` | S10 | Measured CI history (health, strata, critical path, queue, minutes, dollars, noise floor), ranked fixes with labelled savings, posture through zizmor, each approved fix as a small change and verified after merge |
| `ui-hard-gate` | S9 | Not a factory gate skill: the pre-review UI gate (reference first, every state captured, 22 rules, first-pass presentation); factory-ui-ux applies its rules as standing preferences |
| `factory-retro` | S12 | Runs at the end of every change, inside reconcile: friction metrics against earlier changes, environment fixes first, an evidence-gated per-repository playbook every skill reads |
| `factory-security` | S11 | Threat model from the code, pinned scanners, the `security-audit` method with routed knowledge, proven findings as small changes |
| `factory-prune` | S7 | Repository audit with the simplification ladder; protected code filtered out; each approved item runs as a small change |
