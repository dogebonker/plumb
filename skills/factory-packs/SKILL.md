---
name: factory-packs
description: Check the kit's pinned packs against what is installed, read what changed upstream, re-review the changes that relied on it, and bump pins you approve.
disable-model-invocation: true
argument-hint: "[pack name]"
---

# Factory packs

Pack: $ARGUMENTS (empty: every pin)

A pin approves a pack's content as you read it. When the installed pack moves, nothing loads it until you read what changed and bump the pin. Pins live in `~/.software-factory/packs.lock.yaml`; installed packs are in `~/.agents/.skill-lock.json`.

## 1. Compare

For each pin (or the one named):

- Installed hash: `jq -r '.skills["<name>"].skillFolderHash' ~/.agents/.skill-lock.json`
- Equal to the pin: current. Absent: not installed (`npx skills add <source>` installs it). Different: moved.

Also list packs a kit profile or language config names that have no pin.

Done when every pin is current, not installed or moved, and every unpinned pack is listed.

## 2. Read what moved

For each moved pack, and each newly installed pack the user wants pinned:

1. `~/.agents/skills/<name>/CHANGELOG.md` when it exists: the entries above the pin's `version` (all of them for a new pack).
2. Without a changelog: `gh api "repos/<source>/commits?path=<folder>&since=<pinned_at>"`, where `<folder>` is the folder of the pack's `skillPath` in the skills lock (a pack at the repository root has none: leave out `path`), then the changed files of each commit (`gh api repos/<source>/commits/<sha>`).
3. Summarize for the user: rules added, rules changed, rules removed, each by its name or ID.

Done when every moved pack has a summary of its rule changes, or the note that the change could not be read.

## 3. Re-review what relied on a changed rule

A changed or removed rule matters where the factory applied it:

1. Search `.factory/changes/*/` and `.factory/system/` in this repository for the rule's `[<lens>/<rule>]` tag, its name in `challenges.md`, and its file in packets' Rules in scope.
2. Search Pond (read `schema://pond-sql` first) for the same tag in other projects.
3. List each change that relied on the rule, with the finding or decision it shaped.

For each listed change in this repository, the user chooses: re-review it now as a small change (`/factory-triage re-review <slug> against <pack> <rule>`), record it in `.factory/system/rereview.md` for later, or accept it as is.

## 4. Bump

Only for packs the user approves after reading the summary: set the pin to `{ source, hash: <installed hash>, pinned_at: <today>, version: <changelog version, when there is one> }`. Commit it in the factory repository (`~/.software-factory` links into it), staging only `packs.lock.yaml`, and push only when the user asks.

A pack the user does not approve keeps its old pin and stays unloaded until they do.
