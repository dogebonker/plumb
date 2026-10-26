---
name: plumb-init
description: Set up Plumb in a repository - pick the framework commit, install it, migrate .software-factory/ or .factory/, write plumb.lock and principles.md, link the skills, offer the hard-gate hook.
disable-model-invocation: true
argument-hint: "[commit, tag or dev_path]"
---

# Plumb init

Usage: [per-skill accounting](../plumb-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Framework: $ARGUMENTS (empty: ask in step 2)

Init makes a repository a Plumb project: `.plumb/` with its `plumb.lock` and `principles.md`, and the locked framework's skills linked into it ([../plumb-shared/gates.md](../plumb-shared/gates.md), Paths). It runs before a lock exists, so it does not resolve `<kit>`. `<framework_repo>` is `framework_repo` in `~/.plumb/user/config.yaml`; when it is missing, ask for the path to a Plumb checkout. To change the framework of a project that has a lock, use `/plumb-upgrade`.

Run it again on a new machine or in a fresh clone: with a lock already committed, it keeps the lock, installs what it names (step 2), fetches its packs (step 4), links the skills (step 5) and makes the offers of steps 6 and 7 that are not done yet. A committed lock whose `dev_path` folder is missing on this machine came from someone developing Plumb: say so, point to `/plumb-upgrade` to pick a commit, and stop.

`<bin>` is `<framework>/bin` once step 2 has a framework that holds `bin/`, otherwise `<framework_repo>/bin`: the scripts run from the locked commit, not from whatever the checkout holds now.

Edit `.git/info/exclude` and `.claude/settings.local.json` with shell commands (`printf ... >>`, `python3 -c` for the JSON), never Edit or Write: on a branch with a change in progress the hard-gate hook blocks those tools outside `.plumb/`.

## 1. Detect

For setup questions, follow [gates.md, Explain questions and decisions](../plumb-shared/gates.md#explain-questions-and-decisions). Explain committed/ignored as "share the planning files with the project / keep them only on this machine". Explain framework choices as "use the current version (recommended) / use a specific version / develop Plumb itself", retaining the exact ref or path beside the label. Keep settled setup facts out of the question list.

- The repository root: `git rev-parse --show-toplevel`. Work from there. The starting point: the branch (`git symbolic-ref --quiet --short HEAD`), or the sha when HEAD is detached.
- The harness: the `CLAUDECODE`, `CODEX_THREAD_ID` and `CURSOR_AGENT` environment variables, and the `.claude`, `.codex` and `.cursor` folders at the root.
- Manifests (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, ...) with their paths, and CI: `.github/workflows/*`.
- `.plumb/plumb.lock`, `.plumb/principles.md`, `.software-factory/` and `.factory/`, each present or not.
- The mode, from the folder that exists: `.software-factory/`, `.factory/`, or `.plumb/`. Committed when `git ls-files <folder>` lists files, ignored when `git check-ignore -q <folder>/` succeeds. With neither folder, or neither answer, ask: committed or ignored. After step 3, check again on `.plumb/`.

Report all of it in one short list. Done when the user has seen it.

## 2. Choose the framework

With a lock, use the commit or `dev_path` it names. A lock only at `.software-factory/factory.lock` names a framework from before the rename, which this init cannot run: treat it as no lock and ask. Otherwise ask, one of:

- `HEAD` of `<framework_repo>`, the default
- a tag or commit the user names
- `dev_path`, an absolute path to a Plumb checkout, only to develop Plumb itself

For a commit, `<sha>` is `git -C <framework_repo> rev-parse <ref>^{commit}`. Refuse a commit older than `.plumb/`: when `git -C <framework_repo> cat-file -e <sha>:skills/plumb-init` fails, its skills read `.software-factory/` or `.factory/`; say so and stop. For a `dev_path`, the same check is that `<dev_path>/skills/plumb-init` exists.

`<framework>` is `~/.plumb/framework/<sha>`, or the `dev_path`. When that cache folder lacks `kit/`, `skills/` or `hooks/`, install it:

1. First run `[ -L ~/.plumb ]`. When it is a link, name its target (`readlink ~/.plumb`), say that other sessions and projects may still read the kit through it and that the install removes the link (never its target), and ask. On a no, stop.
2. `<framework_repo>/bin/plumb-install <sha>`. It refuses a link that is not a Plumb checkout's `kit/`, and writes `config.yaml` when it is missing.

Done when `<framework>/kit`, `<framework>/skills` and `<framework>/hooks` exist.

## 3. Migrate

Only when `.software-factory/` or `.factory/` exists.

1. Repoint the hook first: the old hook knows only the old folders and would stop gating once they move. In `.claude/settings.local.json` and `.claude/settings.json`, replace each command ending in `hooks/factory_gate.py` with `python3 <framework>/hooks/plumb_gate.py`, editing with a shell command as `/plumb-upgrade` does. This is part of the migration, not an offer. When `~/.claude/settings.json` runs a `factory_gate.py`, show the line and ask to repoint it the same way; on a no, stop, since the migration would leave this repository ungated.
2. Run `<bin>/plumb-migrate --dry-run` and show its output whole. On the user's yes, run `<bin>/plumb-migrate`. It moves the folders, rewrites `.git/info/exclude` and commits nothing. When it refuses, show why and stop.
3. A lock that moved in from `.software-factory/factory.lock` still names the old framework: rewrite its framework line and `packs:` block for `<framework>` as `/plumb-upgrade` step 3.2 does, keeping `skills_linked`.

Keep its lists of other local branches, remote branches and branches checked out in another worktree for step 8.

## 4. Write the project files

- Ignored mode: when `git check-ignore -q .plumb/plumb.lock` fails, append `.plumb/` to `.git/info/exclude`. Triage then reuses this mode and does not ask again.
- `.plumb/plumb.lock`, unless it exists, in gates.md's format: the framework line, the `packs:` block copied from `<framework>/kit/packs.lock.yaml`, and `skills_linked: [.claude/skills]`. For a commit:

  ```bash
  { echo "framework: { commit: <sha>, installed: $(date +%F) }"; sed -n '/^packs:/,$p' <framework>/kit/packs.lock.yaml; echo "skills_linked: [.claude/skills]"; } > .plumb/plumb.lock
  ```

  For `dev_path`, the first line is `framework: { dev_path: <absolute path> }`.
- `.plumb/principles.md`, unless it exists:

  ```markdown
  # Principles

  This project's principles and quiet rules: the last of the three principle layers, after the framework defaults and `~/.plumb/user/principles.md`. A later layer wins on the same `<lens>/<rule>`. Reconcile writes this file from your answers to lens findings; you can edit it by hand.

  ## Principles

  Rules you accepted three times or more. Architecture and interface drafts follow them.

  <!-- example: - Errors are values at module boundaries: callers handle them without try/catch. Source: a-philosophy-of-software-design/define errors out of existence, accepted 3 times. -->

  ## Quiet rules

  Lens rules you overruled three times or more, matched by their exact `<lens>/<rule>` text. The interface panel and review cap their findings at `note`. Money and security rules never go quiet (gates.md, Paths).

  <!-- example: - clean-code/small functions: overruled 3 times, last in checkout-retry -->
  ```

- The packs: run `<bin>/plumb-packs-fetch` from the repository root, whether the lock was written now or already existed, when that script exists. It copies matching verified bundled books offline and fetches other missing pins of the lock into the pack cache (`~/.plumb/packs/<name>@<hash>/`, [../plumb-shared/packs.md](../plumb-shared/packs.md)). Show each failed pack with its reason and go on: a skill continues without a pack it cannot load.

## 5. Link the skills

1. `mkdir -p .claude/skills`, remove the links there named `plumb-*` or `ui-hard-gate` (links only, never a real folder), then `ln -s <framework>/skills/plumb-* <framework>/skills/ui-hard-gate .claude/skills/`.
2. Add `.claude/skills/plumb-*` and `.claude/skills/ui-hard-gate` to `.git/info/exclude`, each once.
3. List the links in `~/.claude/skills/` named `plumb-*` or `ui-hard-gate`, other than `plumb-init` and `plumb-upgrade`. Claude Code prefers a personal skill to a project skill of the same name, so these would run instead of the locked framework, and Resolve `<kit>` would stop them. Warn that repositories not yet inited still run on those user-level links, and that removing them stops Plumb there until each is inited. Offer to remove them, links only.

Codex and Cursor links arrive with S15; say so when step 1 found either.

**Architecture context.** Run `python3 <framework>/kit/archgraph.py doctor` once.
Record the resolved binary, source pin and checksum when available. If absent or
unverified, show its exact pinned install line and keep the skipped status; do not
start a model just to discover tools or silently substitute a same-version build.
This adds no project approval, installs no extra skills and changes no approved
Layout. Build and review use the same adapter once a supported module is known.

## 6. Offer the hard-gate hook

An entry whose command ends in `hooks/factory_gate.py`, from before the rename, is replaced without asking, in `.claude/settings.local.json` and `.claude/settings.json`: the old hook does not gate `.plumb/`. For `~/.claude/settings.json`, show the line and ask. Otherwise ask first. On a yes, add to `.claude/settings.local.json`, merging with what is there and replacing any earlier entry whose command ends in `hooks/plumb_gate.py`:

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
  "hooks": [{ "type": "command", "command": "python3 <framework>/hooks/plumb_gate.py" }] } ] } }
```

`<framework>` is written out as an absolute path. When `git check-ignore -q .claude/settings.local.json` fails, add `.claude/settings.local.json` to `.git/info/exclude`. When `~/.claude/settings.json` already runs a `plumb_gate.py`, say that both would run.

## 7. The user layer

Only when `~/.plumb/user/principles.md` is missing. When `~/.software-factory/user/` exists, this machine ran Plumb under its old name: offer to copy that folder's `principles.md` and `config.yaml` into `~/.plumb/user/` (keeping a `config.yaml` that `plumb-install` already wrote, and setting its `framework_repo` to `<framework_repo>`), ask first, and on a yes skip the rest of this step. Otherwise it is the machine's first init: offer to copy the personal principles and quiet rules Plumb's author kept in the kit before they moved out of it. Ask first. On a yes:

```bash
git -C <framework_repo> show 4820651b2eab869797f277d2d1d2f2c1b1ba2016:kit/principles.md > ~/.plumb/user/principles.md
```

On a no, write the template from step 4 with "the user's taste across projects, the middle layer" in place of its first paragraph.

## 8. Commit

Committed mode: stage `.plumb/plumb.lock` and `.plumb/principles.md`, and a tracked `.claude/settings.json` that step 3 repointed (the migration is already staged), and commit `chore(plumb): init <the first seven characters of the sha>`, or `chore(plumb): init dev` for a `dev_path`. Ignored mode commits nothing. A commit that fails to sign: ask the user to unlock their signing agent, then retry. Never commit unsigned.

Then offer each branch step 3 listed, one at a time:

- The tree must be clean: `git status --porcelain` shows no tracked change and nothing under `.plumb/`. Otherwise say what is in the way and skip the branches.
- A local branch: `git checkout <branch>`, repoint its tracked `.claude/settings.json` as step 3 item 1 does, `<bin>/plumb-migrate`, commit `chore(plumb): migrate to .plumb` with that file staged. When the branch has a pull request (`gh pr list --head <branch>`), push it, asking first: the pull request and the runner read the remote branch, and the runner reports a branch that still uses `.software-factory/` or `.factory/`.
- A remote branch with no local branch of the same name: offer it the same way after `git checkout --track <remote>/<branch>`.
- A branch checked out in another worktree: skip it, and say to run `/plumb-init` in that worktree.

Return to the starting point at the end and after any failure: the branch, or `git checkout <sha>` when HEAD was detached.

## 9. Hand off

Name what ran: the commit or `dev_path`, the packs fetched and any that failed, the links, the hook, the user layer. The next skill is `/plumb-triage <task>`, or, when a change on this branch has `reconciled: false`, the skill its `notes_for_fresh_session` names.
