---
name: factory-ui-ux
description: Product-grounded UI/UX for the factory - create the repository's DESIGN.md, render representative previews at the product gate, de-slop mechanically, and critique rendered screens against it with anchored, checkable opinions.
disable-model-invocation: true
argument-hint: "[design-md | mockups <slug> | critique <routes> | lens <slug>]"
---

# Factory UI/UX

Mode: $ARGUMENTS (empty, or only a change slug as the headless runner sends it: `design-md` when the design file is missing, otherwise `critique` of the main routes)

Why each source and tool is here: `docs/research/ui-ux-selection.md` in the factory repository. Patterns and tools: `<kit>/ui/slop-patterns.yaml` and `tools.yaml`.

The design file is the repository's `DESIGN.md`, or `.software-factory/system/design.md` when the root name already holds something else ([../factory-shared/gates.md](../factory-shared/gates.md)). It is the arbiter: every finding cites it, and where a design skill, a pattern or taste disagrees with it, the design file wins.

Restraint is the default: one filled primary action per surface, headline first and detail on demand, honest states, the work named rather than the machinery. Expression (display type, motion, illustration) appears only where the design file opts in with a principle.

| Mode | When | Runs |
| --- | --- | --- |
| `design-md` | the design file is missing, stale, or the user asks | the guide in [design-md-guide.md](design-md-guide.md) |
| `mockups <slug>` | the product gate of a change with `ui: true`, for the representative preview and any required visual acceptance states | [Mockups](#mockups) |
| `critique <routes>` | on demand | steps 1 to 4 for the routes |
| `lens <slug>` | factory-review, on a slice that changes UI files | steps 1 to 4 for the routes the slice touches, slice rules in step 4 |

## 1. Prepare

- Read the design file, `.software-factory/system/product.md`, `glossary.md`, `constraints.md`, and for a change its `01-product.md` (or `04-slices.md`). No design file: run `design-md` first. Distinguish observed starter styling from the approved target; a release quality bar in the brief or design file is required acceptance work.
- Make the run folder `.software-factory/runs/ui/<YYYY-MM-DD-HHMM>/` and make sure `.software-factory/runs/ui/` is ignored by git (`git check-ignore -q .software-factory/runs/ui/x`; otherwise append it to the file `git rev-parse --git-path info/exclude` names). Lens mode keeps its outputs in the review's own folder.
- Check each tool in `tools.yaml`; a missing one is skipped with its install line. Find the running app: the module's `dev_url` in `lenses.yaml`, or ask; in lens mode without one, run only the code checks and say the screens were not seen.

## 2. Mechanical pass

Run, as `tools.yaml` says and from a fresh empty working directory:

1. Impeccable's detector over the UI source, then the catalog's code patterns with ripgrep, then the repository checks (S18, S20, S22).
2. For each route, at each viewport and color scheme (baseline widths, brief minimum, and CSS media boundaries ±1px using `render-checks.cjs`): screenshots, `slop-metrics.js`, axe for WCAG 2.2 AA, console errors, then dependency-specific forced empty, failing and slow states. Run `readabilityMetrics` as rendered evidence: inspect narrow long text, clipping and overflow; check the primary job at breakpoint transitions, not just screenshot presence.
3. Impeccable's detector against the rendered routes.

Drop every hit the design file waives, and record the waiver. The rest are candidates for step 3; mechanical results are facts there, never re-judged.

## 3. Walk and cut

Follow [critique.md](critique.md): walk the primary job of each screen on the rendered pages, apply the cut test to each element, answer the catalog's model questions with quoted evidence, then sweep the remaining heuristics and the WCAG table in [wcag22-aa.md](wcag22-aa.md) for what the walkthrough did not explain.

## 4. Findings

Write each finding as a challenge card (`factory-interface/challenge-card.md`) with the extra Prediction / check field, ranked and capped as `critique.md` says, plus one line on what works. Write `report.md` in the run folder: findings, waivers applied, tools run or skipped, and the screenshots each finding cites.

- `critique`: show the report to the user. Each finding they accept becomes a small change (`/factory-triage ui: <finding>`); a finding against a position of the design file is instead a proposal to amend the design file, decided by the user.
- `lens`: when the change has mockup screenshots, compare the rendered slice with them as `critique.md` says. Return only findings that make the slice unsafe to ship (a broken refusal or primary action, a state that lies, a WCAG A or AA failure) as cards anchored to a principle, position or WCAG criterion; failures of explicit visual acceptance criteria also block delivery, anchored to the approved design/product criterion. Other taste improvements become a follow-up line.

## Mockups

Preview the representative primary-job screen early, before implementation expands; capture additional screens/states required by the product gate. Pictures of the behavior the product gate agrees, before implementation: the screens `01-product.md` changes, built from the design file. Not a design exploration and not the implementation.

1. Read `01-product.md` (rules and examples) and the design file (tokens, principles, primary-action table, states contract, Words). No design file: `design-md` first.
2. Write one static HTML file per screen and state to `.software-factory/changes/<slug>/mockups/<screen>-<state>.html`: the design file's tokens as CSS variables, no scripts, no external requests. Each screen gets its default state and every state of the design file's states contract it can reach (empty, error, loading). Copy comes from the product examples and the design file's Words, never filler.
3. Run the catalog's code patterns over the mockups folder (the `ripgrep` line in `tools.yaml`, with that folder as the path and a fresh `mktemp -d` as `$OUT`) and answer its model questions with quoted evidence. Fix every hit the design file does not waive before capturing.
4. Capture each file as `mockup_capture` in `tools.yaml` says, to `mockups/<screen>-<state>-<width>-<scheme>.png`. Without a working renderer, keep the HTML files and record the precise blocker and install line; required visual acceptance stays pending until rendered evidence exists.
5. Under Mockups in `01-product.md`, list each screen with its primary action and its screenshot paths.

Each capture retains a manifest in the same folder: source HEAD plus dirty diff/source-file hashes, route/state, viewport, color scheme, renderer version, screenshot paths, and applicable criterion IDs. Keep screenshot and manifest files until review/reconcile is complete. Recapture changed source; do not use stale screenshots as evidence for a new revision.

Done when every screen and state named in step 2 has its HTML file and its required screenshots, and none carries an unwaived catalog hit. The user approves them with the product gate; lens mode later compares the rendered slice with them, in both orders.
