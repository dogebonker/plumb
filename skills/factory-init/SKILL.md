---
name: factory-init
description: Set up the factory in a repository - pick the framework commit, install it, migrate .factory/, write factory.lock and principles.md, link the skills, offer the hard-gate hook.
disable-model-invocation: true
argument-hint: "[commit, tag or dev_path]"
---

# Factory init

Usage: [per-skill accounting](../factory-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Framework: $ARGUMENTS (empty: ask in step 2)

Init makes a repository a factory project: `.software-factory/` with its `factory.lock` and `principles.md`, and the locked framework's skills linked into it ([../factory-shared/gates.md](../factory-shared/gates.md), Paths). It runs before a lock exists, so it does not resolve `<kit>`. `<framework_repo>` is `framework_repo` in `~/.software-factory/user/config.yaml`; when it is missing, ask for the path to the factory checkout. To change the framework of a project that has a lock, use `/factory-upgrade`.

Run it again on a new machine or in a fresh clone: with a lock already committed, it keeps the lock, installs what it names (step 2), fetches its packs (step 4), links the skills (step 5) and makes the offers of steps 6 and 7 that are not done yet. A committed lock whose `dev_path` folder is missing on this machine came from someone developing the factory: say so, point to `/factory-upgrade` to pick a commit, and stop.

`<bin>` is `<framework>/bin` once step 2 has a framework that holds `bin/`, otherwise `<framework_repo>/bin`: the scripts run from the locked commit, not from whatever the checkout holds now.

Edit `.git/info/exclude` and `.claude/settings.local.json` with shell commands (`printf ... >>`, `python3 -c` for the JSON), never Edit or Write: on a branch with a change in progress the hard-gate hook blocks those tools outside `.software-factory/`.

## 1. Detect

For setup questions, follow [gates.md, Explain questions and decisions](../factory-shared/gates.md#explain-questions-and-decisions). Explain committed/ignored as "share the planning files with the project / keep them only on this machine". Explain framework choices as "use the current version (recommended) / use a specific version / develop the factory itself", retaining the exact ref or path beside the label. Keep settled setup facts out of the question list.

- The repository root: `git rev-parse --show-toplevel`. Work from there. The starting point: the branch (`git symbolic-ref --quiet --short HEAD`), or the sha when HEAD is detached.
- The harness: the `CLAUDECODE`, `CODEX_THREAD_ID` and `CURSOR_AGENT` environment variables, and the `.claude`, `.codex` and `.cursor` folders at the root.
- Manifests (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, ...) with their paths, and CI: `.github/workflows/*`.
- `.software-factory/factory.lock`, `.software-factory/principles.md` and `.factory/`, each present or not.
- The mode, from the folder that exists: `.factory/`, or `.software-factory/`. Committed when `git ls-files <folder>` lists files, ignored when `git check-ignore -q <folder>/` succeeds. With neither folder, or neither answer, ask: committed or ignored. After step 3, check again on `.software-factory/`.

Report all of it in one short list. Done when the user has seen it.

## 2. Choose the framework

With a lock, use the commit or `dev_path` it names. Otherwise ask, one of:

- `HEAD` of `<framework_repo>`, the default
- a tag or commit the user names
- `dev_path`, an absolute path to a factory checkout, only to develop the factory itself

For a commit, `<sha>` is `git -C <framework_repo> rev-parse <ref>^{commit}`. Refuse a commit older than `.software-factory/`: when `git -C <framework_repo> cat-file -e <sha>:skills/factory-init` fails, its skills read `.factory/`; say so and stop. For a `dev_path`, the same check is that `<dev_path>/skills/factory-init` exists.

`<framework>` is `~/.software-factory/framework/<sha>`, or the `dev_path`. When that cache folder lacks `kit/`, `skills/` or `hooks/`, install it:

1. First run `[ -L ~/.software-factory ]`. When it is a link, name its target (`readlink ~/.software-factory`), say that other sessions and projects may still read the kit through it and that the install removes the link (never its target), and ask. On a no, stop.
2. `<framework_repo>/bin/factory-install <sha>`. It refuses a link that is not a factory checkout's `kit/`, and writes `config.yaml` when it is missing.

Done when `<framework>/kit`, `<framework>/skills` and `<framework>/hooks` exist.

## 3. Migrate

Only when `.factory/` exists. Run `<bin>/factory-migrate --dry-run` and show its output whole. On the user's yes, run `<bin>/factory-migrate`. It moves the folders, rewrites `.git/info/exclude` and commits nothing. When it refuses, show why and stop.

Keep its lists of other local branches, remote branches and branches checked out in another worktree for step 8.

## 4. Write the project files

- Ignored mode: when `git check-ignore -q .software-factory/factory.lock` fails, append `.software-factory/` to `.git/info/exclude`. Triage then reuses this mode and does not ask again.
- `.software-factory/factory.lock`, unless it exists, in gates.md's format: the framework line, the `packs:` block copied from `<framework>/kit/packs.lock.yaml`, and `skills_linked: [.claude/skills]`. For a commit:

  ```bash
  { echo "framework: { commit: <sha>, installed: $(date +%F) }"; sed -n '/^packs:/,$p' <framework>/kit/packs.lock.yaml; echo "skills_linked: [.claude/skills]"; } > .software-factory/factory.lock
  ```

  For `dev_path`, the first line is `framework: { dev_path: <absolute path> }`.
- `.software-factory/principles.md`, unless it exists:

  ```markdown
  # Principles

  This project's principles and quiet rules: the last of the three principle layers, after the framework defaults and `~/.software-factory/user/principles.md`. A later layer wins on the same `<lens>/<rule>`. Reconcile writes this file from your answers to lens findings; you can edit it by hand.

  ## Principles

  Rules you accepted three times or more. Architecture and interface drafts follow them.

  <!-- example: - Errors are values at module boundaries: callers handle them without try/catch. Source: a-philosophy-of-software-design/define errors out of existence, accepted 3 times. -->

  ## Quiet rules

  Lens rules you overruled three times or more, matched by their exact `<lens>/<rule>` text. The interface panel and review cap their findings at `note`. Money and security rules never go quiet (gates.md, Paths).

  <!-- example: - clean-code/small functions: overruled 3 times, last in checkout-retry -->
  ```

- The packs: run `<bin>/factory-packs-fetch` from the repository root, whether the lock was written now or already existed, when that script exists. It copies matching verified bundled books offline and fetches other missing pins of the lock into the pack cache (`~/.software-factory/packs/<name>@<hash>/`, [../factory-shared/packs.md](../factory-shared/packs.md)). Show each failed pack with its reason and go on: a skill continues without a pack it cannot load.

## 5. Link the skills

1. `mkdir -p .claude/skills`, remove the links there named `factory-*` or `ui-hard-gate` (links only, never a real folder), then `ln -s <framework>/skills/factory-* <framework>/skills/ui-hard-gate .claude/skills/`.
2. Add `.claude/skills/factory-*` and `.claude/skills/ui-hard-gate` to `.git/info/exclude`, each once.
3. List the links in `~/.claude/skills/` named `factory-*` or `ui-hard-gate`, other than `factory-init` and `factory-upgrade`. Claude Code prefers a personal skill to a project skill of the same name, so these would run instead of the locked framework, and Resolve `<kit>` would stop them. Warn that repositories not yet inited still run on those user-level links, and that removing them stops the factory there until each is inited. Offer to remove them, links only.

Codex and Cursor links arrive with S15; say so when step 1 found either.

**Architecture context.** Run `python3 <framework>/kit/archgraph.py doctor` once.
Record the resolved binary, source pin and checksum when available. If absent or
unverified, show its exact pinned install line and keep the skipped status; do not
start a model just to discover tools or silently substitute a same-version build.
This adds no project approval, installs no extra skills and changes no approved
Layout. Build and review use the same adapter once a supported module is known.

## 6. Offer the hard-gate hook

Ask first. On a yes, add to `.claude/settings.local.json`, merging with what is there and replacing any earlier entry whose command ends in `hooks/factory_gate.py`:

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
  "hooks": [{ "type": "command", "command": "python3 <framework>/hooks/factory_gate.py" }] } ] } }
```

`<framework>` is written out as an absolute path. When `git check-ignore -q .claude/settings.local.json` fails, add `.claude/settings.local.json` to `.git/info/exclude`. When `~/.claude/settings.json` already runs a `factory_gate.py`, say that both would run.

## 7. The user layer

Only when `~/.software-factory/user/principles.md` is missing, which happens on a machine's first init. Offer to copy the personal principles and quiet rules the factory's author kept in the kit before they moved out of it. Ask first. On a yes:

```bash
git -C <framework_repo> show 4820651b2eab869797f277d2d1d2f2c1b1ba2016:kit/principles.md > ~/.software-factory/user/principles.md
```

On a no, write the template from step 4 with "the user's taste across projects, the middle layer" in place of its first paragraph.

## 8. Commit

Committed mode: stage `.software-factory/factory.lock` and `.software-factory/principles.md` (the migration is already staged) and commit `chore(factory): init <the first seven characters of the sha>`, or `chore(factory): init dev` for a `dev_path`. Ignored mode commits nothing. A commit that fails to sign: ask the user to unlock their signing agent, then retry. Never commit unsigned.

Then offer each branch step 3 listed, one at a time:

- The tree must be clean: `git status --porcelain` shows no tracked change and nothing under `.software-factory/`. Otherwise say what is in the way and skip the branches.
- A local branch: `git checkout <branch>`, `<bin>/factory-migrate`, commit `chore(factory): migrate to .software-factory`. When the branch has a pull request (`gh pr list --head <branch>`), push it, asking first: the pull request and the runner read the remote branch, and the runner reports a branch that still uses `.factory/`.
- A remote branch with no local branch of the same name: offer it the same way after `git checkout --track <remote>/<branch>`.
- A branch checked out in another worktree: skip it, and say to run `/factory-init` in that worktree.

Return to the starting point at the end and after any failure: the branch, or `git checkout <sha>` when HEAD was detached.

## 9. Hand off

Name what ran: the commit or `dev_path`, the packs fetched and any that failed, the links, the hook, the user layer. The next skill is `/factory-triage <task>`, or, when a change on this branch has `reconciled: false`, the skill its `notes_for_fresh_session` names.
