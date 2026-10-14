# Factory packs

How a factory skill loads a lens or a language pack. `<kit>` and `<project>` are defined in [gates.md](gates.md), Paths. `<pack>` is the exact pinned pack resolved below: a matching book bundle at `<kit>/packs/<name>@<hash>/`, otherwise `~/.software-factory/packs/<name>@<hash>/`. The framework ships its configured book rubrics; `<framework>/bin/factory-packs-fetch` can hydrate the shared cache from those verified copies offline. Each project loads its own pins, so two projects pinned to different hashes of one pack each load their own.

## Pick

- **Lenses.** The repository profile is `profile` in `.software-factory/system/lenses.yaml`; its lenses per step are in `<kit>/profiles/<profile>.yaml`. One agent loads at most two lenses in any step, in the profile's order; the interface challenge panel gives each reviewer a single lens.
- **Language pack.** Each module's `pack` in `lenses.yaml` names `<kit>/languages/<pack>.yaml`: an `index` pack and optional extra `rules` packs. They load in packets, in the interface panel's APoSD reviewer, and as rubric in review.

## Check the pin

For each pack:

1. Pin: the pack's entry under `packs` in `<project>/factory.lock`. No pin: say so, and continue without the pack.
2. For a book pin whose `source`, `path` and `hash` match `<kit>/packs.lock.yaml`, prefer the exact `<kit>/packs/<name>@<hash>/` bundle. Bundles retain the upstream Git tree, full/mini/nano files and modes; fetch and benchmark preparation verify that tree, and benchmark preparation refuses missing or corrupt required books. Otherwise use the exact shared-cache directory. Never substitute an unversioned global skill or relabel another revision. Headless branch pins must still match the installed framework's pins.
3. Missing: run `<framework>/bin/factory-packs-fetch` from the repository root, where `<framework>` is the folder that holds `<kit>` (gates.md, Resolve `<kit>`), or tell the user to when this session cannot run it. It copies matching verified bundles into the cache without network, and fetches other missing pins of the lock. Under the headless runner (`FACTORY_RUNNER_MANAGED=1`) the harness does not fetch: the runner host's operator fetches each installed framework's own `kit/packs.lock.yaml`, never a branch's lock, and the runner skips a change whose pins differ from its framework's (`runner/factory_run.py`). Still missing: say which pack and the reason it printed, and continue without it.

A pin approves a pack's content, so it follows a read: `/factory-packs` shows what changed upstream and writes the pins the user approves into the framework's `kit/packs.lock.yaml`, and a project takes them into its `factory.lock` only through `/factory-upgrade`.

## Load

- A lens: `<pack>/<name>.<size>.md`, or `<pack>/<name>.md` at full size. Size by role: `nano` in packets, `mini` in gates and review, full for APoSD.
- A language pack: `<pack>/SKILL.md` for the index and each rules pack. The executor reads the index, then only the one or two rules the slice needs. It applies them to the code the slice writes, leaves rules the module's linter already enforces to the linter, and skips rules that need a newer language version than the module's `language_version`.
- Any other pack: the files the calling skill names, under `<pack>`.

Done when each lens and language pack of the step is loaded or reported to the user as skipped, with the reason.

## Simplification ladder

From [Ponytail](https://github.com/DietrichGebert/ponytail). Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
