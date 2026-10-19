# Factory packs

How a factory skill loads a lens or a language pack. `<kit>` and `<project>` are defined in [gates.md](gates.md), Paths. `<pack>` is the exact pinned pack resolved below: a matching book bundle at `<kit>/packs/<name>@<hash>/`, otherwise `~/.software-factory/packs/<name>@<hash>/`. The framework ships its configured book rubrics; `<framework>/bin/factory-packs-fetch` can hydrate the shared cache from those verified copies offline. Each project loads its own pins, so two projects pinned to different hashes of one pack each load their own.

## Pick

- **Design lenses are opt-in.** `design_lenses` in this task's `status.yaml` lists the explicitly selected book pack names, default `[]`, including on older changes where the field is absent. The profile's lists are candidates, not automatic loads; a pin, repository profile, task size or critical risk track never opts in. This covers Refactoring.Guru, APoSD, Clean Architecture and other book rubrics. Required security/money review, tests and mechanical import/contract checks remain independent.
- **Task size controls cost, not consent.** Record `task_size` from the actual planned footprint: small = up to three source/test files in one module with no public-contract change; medium = a bounded feature or one changed public contract; large = more than ten source/test files, three or more modules, or several new public contracts. Small/medium: no unsolicited lens question. Large: recommend at most one relevant lens with a reason in the existing plan summary, default off. Honor explicit user selection at any size; never create a separate approval gate or repeat the offer on resume.
- **Load only selected applicable excerpts.** Small: one selected lens, `nano`; medium: one selected lens, `mini`; large: at most two selected lenses, `mini`. Full books require an explicit deep-review request. More selected names than the cap: use the highest-priority relevant selection and defer the rest visibly; do not launch extra panels. APoSD fits public-interface changes, Clean Architecture fits changed module/import boundaries, Refactoring.Guru fits an actual refactor/smell. The general reviewer carries selected review lenses; one optional design reviewer handles selected interface challenges, never one agent per book. Keep selection in task metadata/evidence, not approved gate documents.
- **Pattern map.** `gang-of-four` is no default lens. Only a selected Refactoring.Guru review with a concrete matching smell may read its relevant row; no standalone pattern survey or agent.
- **Language pack.** Each module's `pack` in `lenses.yaml` names `<kit>/languages/<pack>.yaml`: an index and applicable extra rules. Read the index plus one or two relevant rules; mechanical lint owns everything it can enforce. No APoSD opt-in is needed for language correctness.

## Check the pin

For each pack:

1. Pin: the pack's entry under `packs` in `<project>/factory.lock`. No pin: say so, and continue without the pack.
2. For a pin whose `source`, `path` and `hash` match `<kit>/packs.lock.yaml`, prefer the exact `<kit>/packs/<name>@<hash>/` bundle. Bundles retain the upstream Git tree, full/mini/nano files and modes; fetch and benchmark preparation verify that tree, and benchmark preparation refuses missing or corrupt required books. Otherwise use the exact shared-cache directory. Never substitute an unversioned global skill or relabel another revision. Headless branch pins must still match the installed framework's pins.
3. Missing: run `<framework>/bin/factory-packs-fetch` from the repository root, where `<framework>` is the folder that holds `<kit>` (gates.md, Resolve `<kit>`), or tell the user to when this session cannot run it. It copies matching verified bundles into the cache without network, and fetches other missing pins of the lock. Under the headless runner (`FACTORY_RUNNER_MANAGED=1`) the harness does not fetch: the runner host's operator fetches each installed framework's own `kit/packs.lock.yaml`, never a branch's lock, and the runner skips a change whose pins differ from its framework's (`runner/factory_run.py`). Still missing: say which pack and the reason it printed, and continue without it.

A pin approves a pack's content, so it follows a read: `/factory-packs` shows what changed upstream and writes the pins the user approves into the framework's `kit/packs.lock.yaml`, and a project takes them into its `factory.lock` only through `/factory-upgrade`.

## Load

- A selected lens: `<pack>/<name>.<size>.md`, using the task-size cap above. Reuse the same loaded excerpt within the invocation; do not reread a full book to apply one rule. Packets carry selected rule references only; no copied whole rubrics.
- A language pack: `<pack>/SKILL.md` for the index and each rules pack. The executor reads the index, then only the one or two rules the slice needs. It applies them to the code the slice writes, leaves rules the module's linter already enforces to the linter, and skips rules that need a newer language version than the module's `language_version`.
- The pattern map: `<pack>/SKILL.md`.
- Any other pack: the files the calling skill names, under `<pack>`.

Done when selected applicable lenses and language rules are loaded or their unavailability is recorded. Unselected books are intentionally off, not a missing dependency or a report item per book. Do not pin-check, fetch or read them.

## Simplification ladder

From [Ponytail](https://github.com/DietrichGebert/ponytail). Stop at the first rung that holds: does it need to exist; is it already in the codebase; does the standard library do it; does the platform; does an installed dependency; can it be one line; only then the minimum code.
