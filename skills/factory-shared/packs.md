# Factory packs

How a factory skill loads a lens or a language pack. The kit is `~/.software-factory/`; packs are installed skills under `~/.agents/skills/`.

## Pick

- **Lenses.** The repository profile is `profile` in `.factory/system/lenses.yaml`; its lenses per step are in `~/.software-factory/profiles/<profile>.yaml`. Load at most two lenses in any step, in the profile's order.
- **Language pack.** Each module's `pack` in `lenses.yaml` names `~/.software-factory/languages/<pack>.yaml`: an `index` pack and optional extra `rules` packs. They load in packets only.

## Check the pin

For each pack:

1. Pinned hash: `packs.<name>.hash` in `~/.software-factory/packs.lock.yaml`.
2. Installed hash: `jq -r '.skills["<name>"].skillFolderHash' ~/.agents/.skill-lock.json`
3. Equal: load it. Not installed: tell the user `npx skills add <source>` and continue without it. Different: the pack changed upstream. Tell the user to read its changes and bump the pin, and continue without it. No kit, no pin for the pack, or no `jq`: say which, and continue without it.

After the user installs a pack, add its pin: `<name>: { source, hash }`, the hash taken from the skills lock.

## Load

- A lens: `~/.agents/skills/<name>/<name>.<size>.md`. Size by role: `mini` in gates, `nano` in packets.
- A language pack: `~/.agents/skills/<name>/SKILL.md` for the index and each rules pack. The executor reads the index, then only the one or two rules the slice needs. It applies them to the code the slice writes, leaves rules the module's linter already enforces to the linter, and skips rules that need a newer language version than the module's `language_version`.

Done when each lens and language pack of the step is loaded or reported to the user as skipped, with the reason.
