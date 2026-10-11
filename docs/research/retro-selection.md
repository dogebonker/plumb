# factory-retro: what it learns, and how

The decision record for S12. Evidence is in [retro/](retro/):
- A: every retrospective, memory and self-improvement skill installed here or widely used, read in full.
- B: what research and vendors know about agents learning from experience, and how that memory fails.
- C: what friction a factory change leaves on disk and in Pond, tested on the one real change so far (`tg-mini-app` in bitxchange-tg).

Researched 2026-10-11.

## The question

The factory should get better in each repository it runs in, change after change: fewer questions to the user, fewer send-backs, rewinds and retries, fewer repeated review findings, cheaper runs. Reconcile already tunes the kit's global `principles.md` from lens answers. Nothing learned anything per repository, and nothing measured whether the factory got better.

## Decisions

### RT-1. Retro runs at the end of every change, inside reconcile

`/factory-reconcile` step 6 follows `factory-retro`, and its drafts join reconcile's single confirmation step, so a change ends with one approval round. It also runs alone, as `/factory-retro <slug>`. The user chose the trigger.

### RT-2. Matt Pocock's `retro` is the framing, not the engine

- **Borrowed:** its stance (improve the agent's environment, not the code), its categories (navigation, automated checks, review rules, steering text, tool economy, information access), "a mechanical violation gets a deterministic check", and "find the repository's existing check first" (A F1, F6 to F11).
- **Not loaded:** it is user-invoked only, reads one session while a factory change spans many, has no metric, writes to a file model the factory does not use, and shows every candidate unchecked (open upstream issue #1173, where one reporter had to make the agent prove its candidates in 15 of 17 runs) (A F1, F9).
- **Loaded, pinned:** `writing-for-agents` (mattpocock/skills, MIT), as the yardstick for keeping steering text and the playbook small (A F2).
- **Rejected as engines:** the other skills lane A read, from oh-my-claudecode's `self-improve` and `wiki` to Anthropic's `consolidate-memory` and gstack's `retro` and `learn`. They write without asking, grow stores without pruning, call models in the background or send telemetry (A F15 to F28). Six of their ideas are used: a falsification pass before presenting, the "would the mistake repeat without this note" test, proof after applying, staleness from cited files, capped pruning, and no savings claim without a baseline (A F5).

### RT-3. Fix the environment first; the playbook is the last resort

Each lesson takes the first form that holds: a check that fails (a test, a linter rule, a hook, a CI step), then a pointer in a document the agent already reads, then a playbook entry. Checks are deterministic and text is advisory (B F7). Context files cost about 20% more and rarely raised success in a controlled study, and agent-written ones lowered it (B F14). An entry violated twice becomes a check or is retired; it is never just reworded.

### RT-4. The playbook admits only lessons with outside evidence, seen twice

`.factory/system/playbook.md`, read by every skill at Load (`gates.md` step 7, and copied into build packets by scope):

- **Admission:** a lesson must start from a signal the agent could not produce about itself: a user correction, a failing check, an accepted review finding, a revert, a reopened gate or slice. It needs two different changes; one change keeps it as a candidate in that change's `retro.md`. Memory that admitted every experience fell below a fixed memory by 3.7 to 12.1 points, and a strict filter beat adding everything by 15.5 to 25.5 (B F11). Self-generated checks are not enough: Reflexion's own tests passed wrong code 16.3% of the time (B F1). Money, auth, secrets and data loss may enter after one occurrence, with the user's approval.
- **Form:** one imperative line plus fixed fields: scope, why, evidence pointers, code citations, counters (`held`, `violated`, `idle`), status. Itemized entries with counters and pruning are what worked (ExpeL, ACE). A full rewrite once shrank an 18k-token context to 122 tokens and fell below the no-memory baseline (B F2, F6, F12). So entries are edited one at a time, by id.
- **Limits:** at most 25 active entries and about 150 lines. Vendors cap memory too: Claude Code loads the first 200 lines of its auto memory and recommends keeping CLAUDE.md under 200 lines, Codex caps instruction files at 32 KiB, Cursor suggests under 500 lines (B F7 to F9). Citations are checked every run, and a missing one makes the entry `stale` (Copilot validates citations before use, B F9). Idle entries retire after 5 changes; money and security entries never do. Lane B suggested 90 days as a second bound; with a few changes a week, 5 changes comes first, and a time bound adds a rule nothing else needs.
- **Approval:** the user approves every add, edit and retirement.

### RT-5. Session content is data, and the playbook is guarded as an instruction channel

Memory can be poisoned through ordinary inputs: MINJA reached a 98.2% injection success rate, and the defenses tested did not stop it (B F16). So:

- **Read-only reader:** message text is read only by a sub-agent whose tools can only read (Claude Code's `Explore` type), and it returns candidates in fixed fields; the main pass reads only counts and times from Pond, plus the factory's own files.
- **Allowed origins:** only user messages, accepted findings, check results, diffs, gate documents and `history` events can start a candidate. Tool output can only support one.
- **Forbidden content:** entries may not weaken checks, review or gates, name hosts, touch credentials, or hold secrets or personal data. Drafts are scanned with Gitleaks when it is installed.
- **Rollback:** the file is committed, so every entry has an author, a date and a revert.

### RT-6. The factory records what retro needs to count

Lane C found the signals mostly lost (C F11, F12, F8 to F10). The factory now records them:
- **`history`:** an append-only list in `status.yaml`. Events are `step_start` (with session id and factory commit), `gate_reopened`, `sent_back`, `rewind`, `red_retry`, `green_retry`, `executor_stop` and `panel_round`. The hook ignores it, and a new test proves that.
- **`track_proposed`:** stored beside `track`, so a track override is visible (C F16).
- **Tagged findings:** one `review.md` line per finding, `[tag] severity path: finding -> outcome`, where the tag is the lens rule or `polish/<category>`; reconcile counts lens tags only, so polish categories never become principles or quiet rules (C F9).
- **Exact lens names:** a rule is named `<lens skill folder>/<section heading>: <its first five words>`, because the mini lens files group a dozen rules under generic headings; cards go under `## Round N` headings. The interface gate greps for a Response still reading `accept / modify / overrule:` and treats it as unanswered (C F8: three were left that way and the gate was still approved).
- **Counts from git:** reconcile reads the files from git, not Pond. Pond only finds the repositories, because those files are written in pieces that no single tool call holds (C F10).

### RT-7. Better is measured, per entry first

Eight metrics per change (`skills/factory-retro/metrics.md`) go in the change's `retro.md`, committed. Each is compared with the median of the repository's previous 5 changes of the same track, with no verdict below 3 changes. The view notes when the factory commit or the model changed between them, since a model update moves timings on its own (B F20). The strongest signal is per entry: did its failure recur in scope after it went live (B M2). Pond supplies the session numbers, with three corrections from lane C:
- Find a change's sessions by `step_start` or by its command rows, not by Pond's project filter (C F2, F3).
- Read sub-agent tokens from their `<usage>` blocks (C F6).
- Report how far Pond has synced (C F17).

### RT-8. Learning stays per repository; the kit learns through reconcile

A lesson reaches the kit (`principles.md`, a language pack's linter rule) only when it is active in two repositories and seen in three changes, the same bar of three that reconcile already uses (B P9). Personal preferences belong in the user's own CLAUDE.md, never in a repository.

## What the first retro already shows

Lane C's numbers for `tg-mini-app` are the first retro, run by hand. They are listed here as proposals for the factory itself, not applied:

- The interface gate took 49% of wall clock and 42% of output tokens, over 6 challenge-panel rounds with no bound. The user stopped round 7 by hand (C F4, F7). Proposal: cap panel rounds, after which changed signatures get a single reviewer.
- The factory hook was not installed for that change (C F13). Retro now reports it (M7).
- The skills changed mid-change, and `ui` was added to the triage template after this change's `status.yaml` was written, so it never got the field, so UI review did not run on a UI slice (C F14). `step_start` now records the factory commit; the gap itself stays a proposal: pin the skills for a change's lifetime.

## What this does not cover

- **No study measures a per-repository lesson file over weeks of real feature work** (B limits). The thresholds (two changes to admit, 25 entries, 5 idle changes) are judgment based on vendor defaults and the factory's own threshold of three. Retro's own counters will show whether they hold.
- **Few changes, noisy trends:** with a few changes a week, trends stay noisy. Retro reports "no measurable change at n=X" rather than a verdict.
- **Transcript retention:** Claude Code deletes transcripts after 30 days by default. Retro reads Pond, which keeps them, and says when a session is missing.
- **Session id:** each skill carries a `Session: ${CLAUDE_SESSION_ID}` line, which Claude Code fills in when the skill is invoked. Elsewhere it stays unfilled, `step_start` says "unknown", and retro finds the sessions by their command rows.
- **Headless runs:** the runner's default harness starts with `--strict-mcp-config` and no Pond, so retro there measures from the factory's files only (M4 to M8). The runner's own approval resets are commits, not `history` events, and a run that ends without a commit loses its `step_start`.
- **Ignored mode:** with `.factory/` untracked, the trend reads earlier changes from the working tree and there is no git history to revert a playbook entry to.
