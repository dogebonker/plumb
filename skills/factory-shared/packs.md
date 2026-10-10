# Factory packs

How a factory skill loads a lens or a language pack. The kit is `~/.software-factory/`; packs are installed skills under `~/.agents/skills/`.

## Pick

The repository profile is `profile` in `.factory/system/lenses.yaml`; its lenses per step are in `~/.software-factory/profiles/<profile>.yaml`. Load at most two lenses in any step, in the profile's order.

## Check the pin

For each pack:

1. Pinned hash: `packs.<name>.hash` in `~/.software-factory/packs.lock.yaml`.
2. Installed hash: `jq -r '.skills["<name>"].skillFolderHash' ~/.agents/.skill-lock.json`
3. Equal: load it. Not installed: tell the user `npx skills add <source>` and continue without it. Different: the pack changed upstream. Tell the user to read its changes and bump the pin, and continue without it. No kit, no pin for the pack, or no `jq`: say which, and continue without it.

## Load

Read `~/.agents/skills/<name>/<name>.<size>.md`. Size by role: `mini` in gates, `nano` in packets.

Done when each lens of the step is loaded or reported to the user as skipped, with the reason.
