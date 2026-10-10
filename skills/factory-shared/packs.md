# Factory packs

How a factory skill loads a lens or a language pack. The kit is `~/.software-factory/`; packs are installed skills under `~/.agents/skills/`.

## Pick

- **Lenses.** The repository profile is `profile` in `.factory/system/lenses.yaml`; its lenses per step are in `~/.software-factory/profiles/<profile>.yaml`. One agent loads at most two lenses in any step, in the profile's order; the interface challenge panel gives each reviewer a single lens.
- **Language pack.** Each module's `pack` in `lenses.yaml` names `~/.software-factory/languages/<pack>.yaml`: an `index` pack and optional extra `rules` packs. They load in packets, in the interface panel's APoSD reviewer, and as rubric in review.

## Check the pin

For each pack:

1. Pinned hash: `hash` in the pack's line of `~/.software-factory/packs.lock.yaml`.
2. Installed hash: `jq -r '.skills["<name>"].skillFolderHash' ~/.agents/.skill-lock.json`
3. Equal: load it. Not installed: tell the user `npx skills add <source>` and continue without it. Different: the pack changed upstream. Tell the user to run `/factory-packs <name>`, and continue without it. No kit, no pin for the pack, or no `jq`: say which, and continue without it.

A pin approves a pack's content, so it follows a read: `/factory-packs` shows what changed and writes pins the user approves.

## Load

- A lens: `~/.agents/skills/<name>/<name>.<size>.md`. Size by role: `nano` in packets, `mini` in gates and review, full for APoSD.
- A language pack: `~/.agents/skills/<name>/SKILL.md` for the index and each rules pack. The executor reads the index, then only the one or two rules the slice needs. It applies them to the code the slice writes, leaves rules the module's linter already enforces to the linter, and skips rules that need a newer language version than the module's `language_version`.

Done when each lens and language pack of the step is loaded or reported to the user as skipped, with the reason.

## Simplification ladder

From [Ponytail](https://github.com/DietrichGebert/ponytail). Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
