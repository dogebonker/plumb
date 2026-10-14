---
name: factory-upgrade
description: Move a factory project to another framework commit or dev_path - show what changed, install it, bump factory.lock and the pack pins, fetch the packs, relink the skills.
disable-model-invocation: true
argument-hint: "[commit, tag or dev_path]"
---

# Factory upgrade

Framework: $ARGUMENTS (empty: `HEAD` of `<framework_repo>`)

An upgrade makes a framework change a reviewed commit of the project's own ([../factory-shared/gates.md](../factory-shared/gates.md), Paths). It changes `.software-factory/factory.lock` on the current branch, then offers the other branches (step 6). `<framework_repo>` is `framework_repo` in `~/.software-factory/user/config.yaml`. Without `.software-factory/factory.lock`, point to `/factory-init` and stop. `<bin>` is `<framework>/bin` once step 3 has a framework that holds `bin/`, otherwise `<framework_repo>/bin`.

Edit `.claude/settings.local.json` with a shell command (`python3 -c`), never Edit or Write: on a branch with a change in progress the hard-gate hook blocks those tools outside `.software-factory/`.

## 1. Old and new

- `<old>`: the lock's `framework.commit`, or `git -C <dev_path> rev-parse HEAD` for a `dev_path`. A `dev_path` folder missing on this machine leaves `<old>` unknown; say so and go on.
- `<new>`: the argument. A commit or tag resolves with `git -C <framework_repo> rev-parse <ref>^{commit}`; an absolute path to a factory checkout is a `dev_path`, and `<new>` is its HEAD.

The project is current only when the new framework line would name the same commit, or the same `dev_path`, as the lock: say so and stop. Any other move is an upgrade: commit to commit, commit to `dev_path` and back, and one `dev_path` to another even at the same HEAD.

Refuse a commit older than `.software-factory/`: when `git -C <framework_repo> cat-file -e <sha>:skills/factory-init` fails (for a `dev_path`, when `<dev_path>/skills/factory-init` is missing), say so and stop.

## 2. Show what changed

- `git -C <framework_repo> log --oneline <old>..<new> -- kit skills hooks`
- the DECISIONS.md entries added in between: the `+` lines of `git -C <framework_repo> diff <old>..<new> -- docs/DECISIONS.md`, from each added `## ` heading to the next one

When `<new>` is older than `<old>` (`git merge-base --is-ancestor <new> <old>`), say it is a downgrade and show `<new>..<old>` instead. When `<old>` is unknown or `<framework_repo>` lacks either commit, say so and show nothing. Ask the user to go on.

## 3. Install and write the lock

1. A commit: `<framework>` is `~/.software-factory/framework/<sha>`. When it lacks `kit/`, `skills/` or `hooks/`, run `<framework_repo>/bin/factory-install <sha>`, after the link check of `/factory-init` step 2. A `dev_path`: `<framework>` is that path.
2. Rewrite `.software-factory/factory.lock`: the framework line (`{ commit: <sha>, installed: <today> }` or `{ dev_path: <absolute path> }`), the `packs:` block copied anew from `<framework>/kit/packs.lock.yaml`, and `skills_linked` as it was.
3. Show the pins that changed, were added or were dropped.
4. Run `<bin>/factory-packs-fetch` from the repository root, when that script exists, to copy matching verified bundled books offline and fetch other missing pins into the pack cache ([../factory-shared/packs.md](../factory-shared/packs.md)). Show each failed pack with its reason and go on: a skill continues without a pack it cannot load.

## 4. Relink

Relink the skills as `/factory-init` step 5 does, from `<framework>/skills`, into each folder in `skills_linked`. When `.claude/settings.local.json` runs a `hooks/factory_gate.py`, ask separately whether to point that command at `<framework>/hooks/factory_gate.py`, and change it only on a yes.

## 5. In-flight changes

List each change under `.software-factory/changes/` with `reconciled: false`. Each takes the new framework on its next step: the Factory version check at Load (gates.md, Load a change, step 2) shows the log, adds the `status.yaml` fields it lacks and records `factory_updated`. Nothing is edited now.

## 6. Commit, then the other branches

Committed mode: stage `.software-factory/factory.lock` and commit `chore(factory): upgrade <old>..<new>`, each the first seven characters of its sha, followed by ` (dev)` for a `dev_path`. Ignored mode commits nothing and skips the other branches: the lock is not in any branch. A commit that fails to sign: ask the user to unlock their signing agent, then retry. Never commit unsigned.

Then list the other local branches that hold a change without `reconciled: true` (`git ls-tree -r --name-only <branch> .software-factory/changes`, then `git show <branch>:<status.yaml>`) and whose `factory.lock` framework line differs from the new one. Warn that each stops at Resolve `<kit>` until it is upgraded, since the linked skills are now the new framework's. Offer each, one at a time, as `/factory-init` step 8 does: a clean tree, skip a branch checked out in another worktree, `git checkout <branch>`, rewrite its lock as in step 3.2 from its own `skills_linked`, commit with the same message, push when it has a pull request and the user agrees, and return to the starting branch, or its sha when HEAD was detached, at the end and after any failure.

Hand off: name the new framework, the branches upgraded and left behind, and the next step of each in-flight change.
