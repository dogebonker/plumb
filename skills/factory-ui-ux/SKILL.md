---
name: factory-ui-ux
description: Product-grounded UI/UX for the factory - create the repository's DESIGN.md, de-slop mechanically, and critique rendered screens against it with anchored, checkable opinions.
disable-model-invocation: true
argument-hint: "[design-md | critique <routes> | lens <slug>]"
---

# Factory UI/UX

Mode: $ARGUMENTS (empty, or only a change slug as the headless runner sends it: `design-md` when the design file is missing, otherwise `critique` of the main routes)

Why each source and tool is here: `docs/research/ui-ux-selection.md` in the factory repository. Patterns and tools: `~/.software-factory/ui/slop-patterns.yaml` and `tools.yaml`.

The design file is the repository's `DESIGN.md`, or `.factory/system/design.md` when the root name already holds something else ([../factory-shared/gates.md](../factory-shared/gates.md)). It is the arbiter: every finding cites it, and where a design skill, a pattern or taste disagrees with it, the design file wins.

Restraint is the default: one filled primary action per surface, headline first and detail on demand, honest states, the work named rather than the machinery. Expression (display type, motion, illustration) appears only where the design file opts in with a principle.

| Mode | When | Runs |
| --- | --- | --- |
| `design-md` | the design file is missing, stale, or the user asks | the guide in [design-md-guide.md](design-md-guide.md) |
| `critique <routes>` | on demand | steps 1 to 4 for the routes |
| `lens <slug>` | factory-review, on a slice that changes UI files | steps 1 to 4 for the routes the slice touches, slice rules in step 4 |

## 1. Prepare

- Read the design file, `.factory/system/product.md`, `glossary.md`, `constraints.md`, and for a change its `01-product.md` (or `04-slices.md`). No design file: run `design-md` first.
- Make the run folder `.factory/ui/<YYYY-MM-DD-HHMM>/` and make sure `.factory/ui/` is ignored by git (`git check-ignore -q .factory/ui/x`; otherwise append it to the file `git rev-parse --git-path info/exclude` names). Lens mode keeps its outputs in the review's own folder.
- Check each tool in `tools.yaml`; a missing one is skipped with its install line. Find the running app: the module's `dev_url` in `lenses.yaml`, or ask; in lens mode without one, run only the code checks and say the screens were not seen.

## 2. Mechanical pass

Run, as `tools.yaml` says and from a fresh empty working directory:

1. Impeccable's detector over the UI source, then the catalog's code patterns with ripgrep, then the repository checks (S18, S20, S22).
2. For each route, at each viewport and color scheme: screenshots, `slop-metrics.js`, axe for WCAG 2.2 AA, console errors, then the forced empty, failing and slow states.
3. Impeccable's detector against the rendered routes.

Drop every hit the design file waives, and record the waiver. The rest are candidates for step 3; mechanical results are facts there, never re-judged.

## 3. Walk and cut

Follow [critique.md](critique.md): walk the primary job of each screen on the rendered pages, apply the cut test to each element, answer the catalog's model questions with quoted evidence, then sweep the remaining heuristics and the WCAG table in [wcag22-aa.md](wcag22-aa.md) for what the walkthrough did not explain.

## 4. Findings

Write each finding as a challenge card (`factory-interface/challenge-card.md`) with the extra Prediction / check field, ranked and capped as `critique.md` says, plus one line on what works. Write `report.md` in the run folder: findings, waivers applied, tools run or skipped, and the screenshots each finding cites.

- `critique`: show the report to the user. Each finding they accept becomes a small change (`/factory-triage ui: <finding>`); a finding against a position of the design file is instead a proposal to amend the design file, decided by the user.
- `lens`: return only findings that make the slice unsafe to ship (a broken refusal or primary action, a state that lies, a WCAG A or AA failure) as cards anchored to a principle, position or WCAG criterion; everything else becomes a follow-up line.
