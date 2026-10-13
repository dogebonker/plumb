---
name: factory-packs
description: Check the framework's pinned packs against their sources upstream, read what changed, re-review the changes that relied on it, and bump pins you approve.
disable-model-invocation: true
argument-hint: "[pack name]"
---

# Factory packs

Pack: $ARGUMENTS (empty: every pin)

A pin approves a pack's content as you read it. Upstream moves on, and nothing loads the new content until you read what changed and bump the pin. This skill maintains the framework's pins, in `kit/packs.lock.yaml` of the factory repository: the clone `framework_repo` names in `~/.software-factory/user/config.yaml` (no `framework_repo`: say so and stop). A pin is `{ source, path, hash, pinned_at, version }`: `path` is the pack's folder in the `source` repository (`.` for its root), `hash` is the git tree of that folder, and `version` is there only when the pack has a changelog. A pin made by the skills CLI for a pack at a repository's root names a commit instead; its tree is `<hash>^{tree}`. A project's own pins are in its `.software-factory/factory.lock` and change only through `/factory-upgrade`, which copies the framework's pins; the framework cache and the pack cache are never edited.

`<mirror>` is the source's bare mirror, `~/.software-factory/packs/.mirrors/<owner>__<repo>.git`. Only `bin/factory-packs-fetch` creates mirrors, never this skill in place: run `<framework_repo>/bin/factory-packs-fetch <framework_repo>/kit/packs.lock.yaml` first, which mirrors every pinned source and caches every pin. `<at>:<path>` is `<at>:` for path `.`.

## 1. Compare

For each pin (or the one named), once per source: `git -C <mirror> fetch --quiet origin`. Then:

- Upstream hash: `git -C <mirror> rev-parse HEAD:<path>`, the tree of the pack's folder at the head of the source's default branch.
- Equal to the pin's tree: current. The folder is gone upstream: gone. Different: moved.

Also list packs a kit profile or language config names that have no pin.

Done when every pin is current, moved or gone, and every unpinned pack is listed.

## 2. Read what moved

For each moved pack, and each unpinned pack the user wants pinned. For an unpinned pack the user names its `source` and `path`; its upstream hash is `gh api repos/<source>/git/trees/HEAD:<path> --jq .sha`. Write that entry, in the lock's format, to a lock file in a new temp directory and run `<framework_repo>/bin/factory-packs-fetch <that file>`, which mirrors its source and caches it. Then:

1. The changelog at the upstream tree, `git -C <mirror> show <upstream hash>:CHANGELOG.md`, when it exists: the entries above the pin's `version` (all of them for a new pack).
2. Without a changelog: the commits, `git -C <mirror> log --date=short --format='%h %ad %s' <range> -- <path>`, where `<range>` is `<pinned commit>..HEAD` for a pin that names a commit and `--since=<pinned_at> HEAD` otherwise; then what changed, `git -C <mirror> diff --stat <pin's tree> <upstream hash>`, and the diff of each changed rule file.
3. Summarize for the user: rules added, rules changed, rules removed, each by its name or ID.

Done when every moved pack has a summary of its rule changes, or the note that the change could not be read.

## 3. Re-review what relied on a changed rule

A changed or removed rule matters where the factory applied it:

1. Search `.software-factory/changes/*/` and `.software-factory/system/` in this repository for the rule's `[<lens>/<rule>]` tag, its name in `challenges.md`, and its file in packets' Rules in scope.
2. Search Pond (read `schema://pond-sql` first) for the same tag in other projects.
3. List each change that relied on the rule, with the finding or decision it shaped.

For each listed change in this repository, the user chooses: re-review it now as a small change (`/factory-triage re-review <slug> against <pack> <rule>`), record it in `.software-factory/system/rereview.md` for later, or accept it as is.

## 4. Bump

Only for packs the user approves after reading the summary: set the pin to `{ source, path, hash: <upstream hash>, pinned_at: <today>, version: <changelog version, when there is one> }`. Commit it in the factory repository, staging only `kit/packs.lock.yaml`, and push only when the user asks. Tell the user that each project takes the new pin with `/factory-upgrade`, which fetches it into the pack cache.

A pack the user does not approve keeps its old pin, and projects keep loading the content that pin names.
