# Retro metrics

What `/factory-retro` measures for a change, and where each number comes from. Normalize per slice where a count grows with size. Queries that work on Pond, with their outputs: `docs/research/retro/C-signals.md` (appendix) in the factory repository.

| ID | Metric | Source |
| --- | --- | --- |
| M1 | Questions to the user, per step: AskUserQuestion items plus free-text user turns. Headless: approver comments after each `waiting_since` | Pond, split at the `step_start` times in `history` (the autopilot orchestrator's session holds every step's questions, and reconcile), or at the `/factory-*` command rows when `history` has none. A user turn counts only when its text does not start with `<` and is not a skill body or an agent hand-back |
| M2 | Wall clock and minutes waiting for the user, per step | Pond: `step_start` times, or command timestamps; AskUserQuestion call to its result |
| M3 | Tokens per step: main session, and sub-agents from the `<usage>` block of each Agent result or task notification (Pond's sub-agent output counts are not usable), with each step against its budget (below) | Pond usage rows; Agent results; `step_tokens` events |
| M4 | Interface panel rounds, cards per round, share overruled, cards left unanswered | `panel_round` events, `challenges.md` |
| M5 | Rework: gate send-backs and reopens by gate and cause; rewinds, red retries, green retries, check retries and executor stops by reason, per slice (a rewind caused by a red retry counts once, as the retry) | `history` |
| M6 | Review findings per slice by tag and outcome; tags already seen in this repository's earlier changes | `slices/*/review.md` |
| M7 | Whether the factory hook was installed | `~/.claude/settings.json`, and the repository's `.claude/settings.json` and `.claude/settings.local.json` |
| M8 | Track proposed against track chosen | `track_proposed`, `track` |

## Token budgets

Retro flags every step over its budget, with what filled it (the largest tool results, the number of turns). Tokens are counted the way the budgets were set: each turn's input, cache read, cache write and output, summed over the step agents' turns and their own sub-agents' turns, from Pond's sub-agent sessions found by the agent ids in `step_tokens` (whose usage totals are a cross-check). The orchestrator's count runs from its first `step_start` to reconcile's. The budgets are guesses from the first measured change, `tg-mini-app`, where build took 8.8M tokens and review 11.7M per slice in the main session, before the thin orchestrator. Once this repository has three changes of a track, the median of each step there replaces its guess.

| Step | Budget |
| --- | --- |
| Orchestrator, up to reconcile | 2M |
| Build step agent, per slice | 3M |
| Review step agent, per milestone | 6M |
| Each gate step | 6M |
| Reconcile, with retro | 6M |

## Finding the change's sessions

The `step_start` events name each step's session. Without them, scan Pond for the `/factory-*` command rows whose arguments carry the slug: Pond's project filter is unreliable, because a step can run from a session started in another directory. Say how far Pond has synced; a session it has not synced yet is reported as missing, not as zero.

## The trend

Each change's numbers go in its `retro.md`, with the factory commits from its `step_start` events and the model when known. Compare each metric with the median of this repository's previous 5 changes of the same track, read from their `retro.md` files in git (in ignored mode, from the working tree). With fewer than 3, show the values without a verdict. Call a move better or worse only when it leaves the range of those previous changes, and say when the factory commit or the model changed between them.
