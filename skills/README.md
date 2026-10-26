# Skills

Plumb skills land here, built in roadmap order. Each follows the open Agent Skills format, so it runs in any compatible harness.

## Install

`bin/plumb-install <ref>` installs a Plumb commit into the framework cache, once per machine; `/plumb-init` then links that commit's skills into the project, writes its lock, fetches the packs it pins with `bin/plumb-packs-fetch` and migrates an old `.software-factory/` or `.factory/` with `bin/plumb-migrate`. By hand, from the repository root, with that commit installed in the framework cache ([kit/](../kit/README.md)):

```bash
[ -L ~/.plumb ] && rm ~/.plumb   # the old link to kit/: the cache and the user layer must not write into the Plumb repository
c=<framework commit>; f=~/.plumb/framework/$c
mkdir -p .plumb .claude/skills "$(git rev-parse --git-path info)"
ln -s $f/skills/plumb-* $f/skills/ui-hard-gate .claude/skills/
x="$(git rev-parse --git-path info/exclude)"; for p in ".claude/skills/plumb-*" .claude/skills/ui-hard-gate; do grep -qxF "$p" "$x" || echo "$p" >> "$x"; done
{ echo "framework: { commit: $c, installed: $(date +%F) }"; sed -n '/^packs:/,$p' $f/kit/packs.lock.yaml; echo "skills_linked: [.claude/skills]"; } > .plumb/plumb.lock
$f/bin/plumb-packs-fetch .   # each pin into ~/.plumb/packs/<name>@<hash>/
```

Self-checks: `python3 bin/test_plumb_install.py`, `python3 bin/test_plumb_migrate.py`, `python3 bin/test_plumb_packs_fetch.py`.

The links are machine-specific, so `.claude/skills/plumb-*` and `.claude/skills/ui-hard-gate` stay out of git through `.git/info/exclude`, and a project's own skills there are unaffected: review's committed-source check and rewind's `git clean` would otherwise trip over them or delete them. To develop Plumb, link from a checkout's `skills/` instead and write `framework: { dev_path: <that checkout> }` (gates.md, Paths).

The skills read the kit as `<kit>`, the framework cache's `kit/` for that commit, and the project's state under `.plumb/` ([gates.md](plumb-shared/gates.md), Paths).

Install them as a set: the skills share `plumb-shared/` (gate rules, pack loading, templates, the playbook contract). Pond is used when its MCP tools are available.

## Hard gates

`hooks/plumb_gate.py` is a Claude Code `PreToolUse` hook. On a branch with an active Plumb change it blocks edits to files outside `.plumb/` and the root `DESIGN.md` while a gate is unapproved, after an approved gate document changed, or outside the current slice's Allowed files and logged deviations. It also blocks them while an active change's `plumb.lock` is missing or names no framework, and whenever `.software-factory/changes/` or `.factory/changes/` holds a change that is not reconciled, whatever `.plumb/` already holds: run `/plumb-init` to migrate that branch, local or remote. Edits under those folders and `.plumb/` stay open so init can run, except the old folders' gate documents and threat model. `/plumb-init` offers to add it to the project's `.claude/settings.local.json`, run from the locked framework (`<framework>` is `~/.plumb/framework/<commit>` or the `dev_path`); by hand:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{ "type": "command", "command": "python3 <framework>/hooks/plumb_gate.py" }]
      }
    ]
  }
}
```

Approved gate documents and the active change's approved threat model are frozen against editing tools, so an agent cannot append progress and accidentally trigger reapproval. A full Write of the recorded approved bytes is allowed for an idempotent write or proven restore. Status and separate evidence files remain editable; an intentional gate revision must be authorized and opened first. This does not make editable status an approval authority.

What it leaves to others:

- It blocks but never changes `status.yaml`: after a hash mismatch, the skill first checks for a proven incidental edit it can restore exactly; an intentional decision change reopens its gate and affected dependents. Interactive impact checks can retain unchanged compatible approvals; headless PR snapshots retain the strict chain.
- A frozen signature changed inside an allowed file is caught by review's contract check, not by the hook.
- It guards the editing tools only; shell commands that write files pass.

Self-check: `python3 hooks/test_plumb_gate.py`.

## Headless mode

Every skill records token coverage under [per-skill accounting](plumb-shared/gates.md#skill-token-accounting). Design books default off through task-local `design_lenses: []`; profile lists are opt-in candidates and task size caps the selected excerpt/reviewer cost. Correctness, required risk review and mechanical import/contract checks remain.

The headless runner retains Claude stream evidence and its per-task/per-skill ledger under `.git/plumb-usage/`, including failed attempts. Summarize it with `python3 <framework>/kit/usage.py report --ledger <clone>/.git/plumb-usage/usage.jsonl`. Interactive skills use change/run-local ledgers. Shared-session attribution needs actual entry baselines and exit counters; missing or nested attribution is reported unknown. No extra model call or full retrospective is needed to produce the report. Receipts are measurements, not approval provenance or actual invoice dollars.

`runner/plumb_run.py` drives changes whose `mode` is `headless` through their pull request, one `plumb/<slug>` branch and one pull request per change. On every pass it re-derives approvals from approvers' APPROVED reviews (`approve <gate>`, `sign off slice NN`) and resets any it cannot back, passes approvers' replies to a waiting change, and runs the next skill through a headless harness (default `claude -p`). Run one pass per cron tick or CI job, in a clone used only by the runner:

```bash
python3 runner/plumb_run.py <clone> --approvers alice,bob
```

- The runner works on a change only after an approver starts it with an APPROVED review whose first line is `start`. After that it runs the harness only on a branch head that the runner or the harness itself left, or that an approver reviewed: a push by anyone else waits for an approver's review. A later CHANGES_REQUESTED review by an approver revokes their earlier approvals.
- Each skill run happens in a fresh throwaway clone of the branch, so nothing the harness writes, including `.git` config, reaches the runner's clone; `--setup` (for example `npm ci`) prepares that clone, and uncommitted work is discarded with it. A new branch head counts as the harness's own only when it fast-forwards the head the harness started from with commits created in that clone. A harness that pulls someone else's concurrent push and then rewrites it (amend, squash) can still launder it: protect `plumb/*` so only the runner's account can push there.
- The default harness, `claude -p --setting-sources user --strict-mcp-config`, ignores the repository's own Claude settings and MCP servers. The skills still run the repository's tests and dev commands, so run the harness in a container or VM with a token scoped to this repository.
- Gate approvals are also GitHub pull-request approvals: protect the default branch with "dismiss stale approvals" so an early `approve product` cannot merge later code.
- Approvers come only from `--approvers`. The login `gh` runs as on the server never counts, even when listed, so give the runner its own GitHub account.
- Gates skipped in the change's first commit stay skipped only when an approver's `start` review covers that commit; any other `skipped` gate is reset to pending.
- The operator installs each framework commit the server may run with `bin/plumb-install <commit>` (`~/.plumb/framework/<commit>/`, [kit/](../kit/README.md)). The lock comes from the change's branch, which the harness can write, so it only selects among installed commits: the runner skips a change whose lock is missing, names a `dev_path`, names anything but a full 40-hex commit installed on the server, or pins packs other than that commit's `kit/packs.lock.yaml`. The operator fetches packs with `<framework>/bin/plumb-packs-fetch <framework>/kit/packs.lock.yaml` for each installed commit, never from a branch's lock. Link the skills user-level, into `~/.claude/skills/`, from that cache commit: a project's links are untracked, so the throwaway clone has none, and `--setting-sources user` may skip project skills anyway. One server therefore runs one framework commit at a time. The operator also runs that commit's `bin/plumb-packs-fetch` on a checkout of each change's branch, so the packs its lock pins are in the pack cache (`~/.plumb/packs/<name>@<hash>/`); a skill runs without a pack missing there. It also needs `gh` signed in, `pond init` against the shared store, the runtimes the adapters call, and a harness allowed to edit files and run them unattended.
- Book rubrics bundled under the installed framework's `kit/packs/` are directly available at matching pins, including on a fresh runner host. Other packs retain cache preparation, and branch/framework pin equality remains mandatory.
- Interactive triage creates the change and its pull request; the runner takes over from there.
- The hard-gate hook guards the harness's editing tools only. Headless enforcement rests on the runner resetting what no approval backs.

Self-check: `python3 runner/test_plumb_run.py`.

## Run one change

`/plumb-triage <task>`, then the gates `/plumb-product`, `/plumb-architecture`, `/plumb-interface`, `/plumb-slices` (track small: slices only), then `/plumb-build`, which runs on autopilot: each milestone's slices and independent review, then the next milestone, then `/plumb-reconcile` with one final human sign-off before merging. Headless mode retains per-slice PR sign-off. One Opus 5.5 lead handles slices and repairs in dependency order, using ordinary bounded Opus subagents for independent approved work; independent review finishes before the next milestone. Each skill resumes from `.plumb/changes/<slug>/status.yaml`, so a fresh session can pick up at any step. Track standard in interactive mode runs `/plumb-triage`, `/plumb-plan`, then `/plumb-build` through reconcile.

## Skills

| Skill | Roadmap step | Purpose |
| --- | --- | --- |
| `plumb-init` | S14 | Sets a repository up: detects the harness, stack and CI, installs and locks a framework commit (or a `dev_path`), migrates `.software-factory/` or `.factory/`, writes `plumb.lock` and `principles.md`, links the skills, offers the hard-gate hook and the user layer's principles |
| `plumb-upgrade` | S14 | Moves the lock to another framework commit or `dev_path`: the log and decisions in between, the install, new pins, relinked skills |
| `plumb-triage` | S1, S2 | Track, slug, branch, `status.yaml`; modules, BDD and money detection into `lenses.yaml`. Lens profile in S3 |
| `plumb-build` | S1 | Packet, Opus 5.5 lead with bounded native subagents, slice evidence barriers, red then green check, mechanical checks per slice, a milestone's slices back to back |
| `plumb-review` | S1, S6 | Mechanical checks (files, contract, red/green, lint, language checks, dependency rule, dead code), review agents with lens rubrics, APoSD, UI/UX, Security and Money reviewers, validated fixes routed to the executor, regression proofs, approved-scope completion and final human sign-off; once per milestone |
| `plumb-code-review` | Standalone | Local/PR pre-release review: polish lenses, bundled bug scanners/checklist, Plumb docs/ADRs/contracts/approval integrity, archgraph context, one verified report and explicitly authorized follow-through; no active change required |
| `plumb-plan` | S2 | Track standard, interactive: one discovery pass, the four gate documents drafted together, one approval |
| `plumb-product` | S2 | Product gate: problem, rules and examples, promises, constraints |
| `plumb-architecture` | S2, S4 | Architecture gate: cited baseline research by the Opus lead or bounded helpers, budgets, ADRs |
| `plumb-interface` | S2, S4, S6 | Interface gate: signatures that compile through the kit's adapters, cost card, a challenge panel of one lens per reviewer, the human's decisions, coverage |
| `plumb-slices` | S2 | Slices gate: vertical slices, tracer bullet first |
| `plumb-shared` | S2, S3 | Not a skill: `gates.md` (gate rules), `packs.md` (lens and language pack loading), `constraints.md` (registry template) |
| `plumb-reconcile` | S7 | Before merge: the examples tried on the running product, then ADRs, standing constraints, living product and glossary in `.plumb/system/`; calibration and lessons into the project's `.plumb/principles.md`, with rules shared by two projects proposed for the user layer |
| `plumb-packs` | S7 | Pin check, upstream changes read from changelogs, re-review of changes that relied on a changed rule, pin bumps |
| `plumb-ui-ux` | S9 | The repository's DESIGN.md (created by guide, enforced for UI changes), optional mockup screenshots at the product gate, mechanical de-slop, anchored critique of rendered screens |
| `plumb-ci` | S10 | Measured CI history (health, strata, critical path, queue, minutes, dollars, noise floor), ranked fixes with labelled savings, posture through zizmor, each approved fix as a small change and verified after merge |
| `ui-hard-gate` | S9 | Not a Plumb gate skill: the pre-review UI gate (reference first, every state captured, 22 rules, first-pass presentation); plumb-ui-ux applies its rules as standing preferences |
| `plumb-retro` | S12 | Runs at the end of every change, inside reconcile: friction metrics against earlier changes, environment fixes first, an evidence-gated per-repository playbook every skill reads |
| `plumb-security` | S11 | Threat model from the code, pinned scanners, the `security-audit` method with routed knowledge, proven findings as small changes |
| `plumb-prune` | S7 | Repository audit with the simplification ladder; protected code filtered out; each approved item runs as a small change |

Autonomous local development uses the approved slices mandate, bounded corrective records and `plumb_gate.py repair-check` to loop after acceptance defects. Older plans and headless PR approval protocols retain their existing route. The validator bounds scope and provenance; actual independent review, RED/GREEN and complete acceptance still decide technical success.
