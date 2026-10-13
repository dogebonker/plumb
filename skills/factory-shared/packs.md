# Factory packs

How a factory skill loads a lens or a language pack. `<kit>` and `<project>` are defined in [gates.md](gates.md), Paths; packs are installed skills under `~/.agents/skills/`.

## Pick

- **Lenses.** The repository profile is `profile` in `.software-factory/system/lenses.yaml`; its lenses per step are in `<kit>/profiles/<profile>.yaml`. One agent loads at most two lenses in any step, in the profile's order; the interface challenge panel gives each reviewer a single lens.
- **Language pack.** Each module's `pack` in `lenses.yaml` names `<kit>/languages/<pack>.yaml`: an `index` pack and optional extra `rules` packs. They load in packets, in the interface panel's APoSD reviewer, and as rubric in review.

## Check the pin

For each pack:

1. Pinned hash: `hash` in the pack's entry under `packs` in `<project>/factory.lock`.
2. Installed hash: `jq -r '.skills["<name>"].skillFolderHash' ~/.agents/.skill-lock.json`
3. Equal: load it. Not installed: tell the user `npx skills add <source>` and continue without it. Different: the installed pack is not the one this project pinned. Tell the user to run `/factory-packs <name>` to read what changed and pin it in the framework, then `/factory-upgrade` to take the new pin into this project, and continue without it. No pin for the pack in `factory.lock`, or no `jq`: say which, and continue without it.

A pin approves a pack's content, so it follows a read: `/factory-packs` shows what changed and writes the pins the user approves into the framework's `kit/packs.lock.yaml`, and a project takes them into its `factory.lock` only through `/factory-upgrade`. Packs are installed once per machine, so two projects pinned to different hashes of one pack cannot both load it; a cache per hash is a later step.

## Load

- A lens: `~/.agents/skills/<name>/<name>.<size>.md`. Size by role: `nano` in packets, `mini` in gates and review, full for APoSD.
- A language pack: `~/.agents/skills/<name>/SKILL.md` for the index and each rules pack. The executor reads the index, then only the one or two rules the slice needs. It applies them to the code the slice writes, leaves rules the module's linter already enforces to the linter, and skips rules that need a newer language version than the module's `language_version`.

Done when each lens and language pack of the step is loaded or reported to the user as skipped, with the reason.

## Simplification ladder

From [Ponytail](https://github.com/DietrichGebert/ponytail). Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
