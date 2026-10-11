# factory-retro: the evidence a change already leaves, and what it lacks

Lane C for factory-retro. Date: 2026-10-11. Sources: every factory skill, `runner/factory_run.py`, `hooks/factory_gate.py`; the one real factory change on disk (`~/Work/bitxchange-tg`, change `tg-mini-app`); Pond 0.19.5 over MCP (`pond_sql`), read-only. Session content is summarized, never copied; no secrets or personal data below.

## Verdict

One real factory change has run: `tg-mini-app` in `bitxchange-tg`, track standard, four gates approved, slice 01 of 11 green, its `review.md` written and waiting for sign-off. That is enough to test extraction end to end, not enough for a trend.

- **Pond already holds most friction signals, per step:** user questions and human wait time, tokens, turns, tool failures, subagent count and cost, all split by factory step using the `/factory-*` command boundaries. Every query below ran in under 5 s.
- **But Pond cannot find the change by project.** The sessions ran with a different working directory than the repository they changed. They must be found by command name, or recorded in `status.yaml`.
- **The change files hold the decisions, not the friction.** `status.yaml` overwrites its own history (`sent_back`, `rewind`, gate reopen), build outcomes (red retry, green attempts, executor stops) live only in transcript prose, and lens and review findings carry no stable key to count by.
- **Reconcile's calibration premise does not hold.** It counts `challenges.md` and `review.md` "through Pond", but in the real change `challenges.md` was assembled by shell and Python patches, never written whole by a tool call. The files live in git, and git is where to count them.

The smallest fix is one append-only `history:` list in `status.yaml` with a `step_start` event that carries the session id and factory commit, plus a fixed tag on every `review.md` finding. Details in "What to add".

## What exists on disk

| Path | Content |
| --- | --- |
| `~/Work/bitxchange-tg/.factory/changes/tg-mini-app/` | `status.yaml` (35 lines), `01-product.md` 93, `02-architecture.md` 121, `03-interface.md` 200 (at its line budget), `04-slices.md` 83, `research.md` 514, `challenges.md` 521 (6 panel rounds, 36 cards), `slices/01/packet.md` 180, `slices/01/review.md` 49 (uncommitted, sign-off empty) |
| `~/Work/bitxchange-tg/.factory/system/` | `constraints.md`, `lenses.yaml` |
| `~/Work/moneylust-app/.factory/ci/2026-10-11-{0048,0114}/` | `summary.json`, `data.json` from the factory-ci measurement script; no change folder |

Git log of `factory/tg-mini-app` (local time +01:00), the one other timeline:

```
512ed17 22:05:51 chore(factory): triage tg-mini-app
5296cc5 22:07:17 chore(factory): tg-mini-app scope adds /start and chat-only use
ce38c25 22:07:54 chore(factory): tg-mini-app notify-me sends a Telegram message at launch
5e2c32e 22:09:40 chore(factory): tg-mini-app chat flow, status pushes, webhook in prod
5f8930c 22:15:58 chore(factory): product tg-mini-app
a6bdb2a 22:45:46 chore(factory): product and architecture tg-mini-app
17df292 00:11:39 chore(factory): interface tg-mini-app
3235b91 00:48:19 chore(factory): slices tg-mini-app
c76a315 00:55:41 test(tg-mini-app): slice 01 red
7522a3b 00:57:15 feat(tg-mini-app): slice 01
d90933e 01:02:44 fix(tg-mini-app): slice 01 webhook only with a secret
be36bec 01:05:40 chore(factory): slice 01 built
56bb493 01:13:45 fix(tg-mini-app): slice 01 review
```

## Artifacts a change leaves, by skill

| Skill | Artifact | Fields a retro can use |
| --- | --- | --- |
| triage | `status.yaml` (factory-triage/SKILL.md:88-114), `lenses.yaml`, commit `chore(factory): triage <slug>` | track, three commands, `baseline_failures`, `mode`, `pond_sessions` (prior work only), `ui`, `money` |
| product, architecture, interface, slices | `0N-*.md`, gate line `{ state, approved_by, approved_at, doc_sha256 }`, commit `chore(factory): <gate> <slug>` (gates.md:44-46) | approval time, line count vs budget (gates.md:9-12) |
| architecture | `research.md` (questions and answers, "not found" gaps) | research rounds, unanswered count |
| interface | `challenges.md` cards with Lens / rule, Severity, Response (challenge-card.md) | cards per lens, accept / modify / overrule, conflicts; rounds only as headings |
| slices | slice lines `{ id, name, state, base_commit, test_commit, head_commit }`, `sent_back: null` reset (factory-slices/SKILL.md:69-74) | slice count |
| build | `slices/NN/packet.md`, commits `test(<slug>): slice NN red`, `feat(<slug>): slice NN`, `revert(<slug>): slice NN` (only when something was staged), `chore(factory): slice NN built`; `deviations`, `red_exempt` | red and green commit times, deviations |
| review | `slices/NN/review.md` (factory-review/SKILL.md:73-99), commit `fix(<slug>): slice NN review`, `proposed.md` (headless, deleted after) | Phase 1 pass / fail / skipped with reason, polish findings, lens cards, follow-ups, sign-off time |
| reconcile | ADRs, constraint rows, `principles.md` kit changes, `reconciled: true` | promoted and quieted rules |
| runner (headless) | commits `chore(factory): runner: <notes>` (factory_run.py:335), stderr lines | approvals, resets, timeouts, exit codes (stderr only, factory_run.py:351-354) |
| hook | exit 2 and a stderr line `factory gate (<slug>): <reason>` (factory_gate.py:163-165) | nothing persisted; visible to Pond as a failed tool result |
| Pond | every main and subagent session | turns, questions, waits, tokens, tool calls and failures, timestamps |

## Friction signals: where each can be read today

| Signal | Read today from | Status | Smallest change that records it |
| --- | --- | --- | --- |
| User questions | Pond: `AskUserQuestion` calls (questions per call in `params.questions`) plus free-text user turns; headless: approver PR comments after `waiting_since` (runner already collects them, factory_run.py:319-323) | available | none; filter harness-injected rows (F5) |
| Human wait time | Pond: tool_call timestamp to tool_result timestamp of `AskUserQuestion` | available | none |
| Gate send-backs | `sent_back` in `status.yaml` | **lost**: overwritten to `null` when slices is re-approved (factory-slices/SKILL.md:69) | `history` event `sent_back { gate, slice, reason }` |
| Gate reopen (chain check, or a later gate reopening an earlier one) | nothing; `approved_at` is overwritten on re-approval | **not recorded** (F11) | `history` event `gate_reopened { gate, cause }` |
| Slice rewinds | slice `state: rewind`, then reset to `pending` (factory-build/SKILL.md:32); a `revert(...)` commit only when something was staged | **lost** | `history` event `rewind { slice, cause }` |
| Red failing for the wrong reason | build step 4 retries once, then asks (factory-build/SKILL.md:78-80) | **not recorded**; transcript prose only | `history` event `red_retry { slice, reason }` |
| Green taking several attempts | build step 5 continues the executor (factory-build/SKILL.md:84) | **not recorded** | `history` event `green_retry { slice }` |
| Executor stops and why | executor report in the transcript; `deviations` only for an allowed extra file | **mostly not recorded** | `history` event `executor_stop { slice, reason: signature / file / test / hook / passes-on-stub }` |
| Executor continuations outside the plan | Pond `SendMessage` calls in the build session | available, unlabeled | covered by `executor_stop` or `off_plan_commit` |
| Commits outside the slice pattern | git log against the commit patterns above | available (F12 found one) | none; retro greps |
| Review findings by rule | `review.md` | **not countable**: no tags in practice, free-form categories (F9) | one line per finding with a fixed tag (below) |
| Lens findings by rule | `challenges.md`, review lens cards | **not countable reliably**: lens names vary, rule text is prose (F8) | Lens / rule as `<skill folder> / <rule heading>` |
| Interface panel rounds | `challenges.md` headings `## Round N: <lens>` | available by convention only | `history` event `panel_round { n, cards }` |
| Deviations | `deviations` | available | none |
| Baseline failures | `baseline_failures` | available | none |
| Hook blocks | Pond tool results containing `factory gate (` | available, scoped scan; **zero in practice because the hook was not installed** (F13) | none; retro checks installation |
| Tool and environment failures | Pond `parts.is_failure` with result text | available (F15) | none |
| Time per step | Pond `/factory-*` command timestamps; git commit times | available | none |
| Tokens per step | Pond main session usage by command span; subagent `<usage>` blocks | available with caveats (F6) | none |
| Track override | a comment in `lenses.yaml` | **not recorded** as data (F16) | `track_proposed:` next to `track:` |
| Factory version per step | nothing | **not recorded** (F14) | `factory` sha on `step_start` |
| Which sessions belong to the change | `pond_sessions` holds prior work only; Pond project filter fails (F2) | **not recorded** | `session` on `step_start` |

## Findings

**F1. One real change, partly done.** `bitxchange-tg` change `tg-mini-app`: track standard, gates approved 2026-10-10 21:45Z (product and architecture), 23:11Z (interface), 23:48Z (slices); slice 01 green, review written, not signed off; slices 02 to 11 pending (`status.yaml:11-27`). `moneylust-app/.factory/` holds only factory-ci measurement output. No other `.factory/` under `~/Work` at depth 4.

**F2. Pond's project filter misses the change.** All factory steps ran from sessions whose project is `~/Work/BitXchange-redesign`; the code lives in `~/Work/bitxchange-tg`. The 15 sessions Pond files under `bitxchange-tg` last 2 to 30 seconds each: they are Claude Code's background security review side calls, not factory steps (Q2, Q3). `pond_sessions` in `status.yaml` holds only prior work (factory-triage/SKILL.md:112), so nothing links the change to its own sessions.

**F3. Command invocations are invisible to search but findable by SQL.** The `<command-name>/factory-*</command-name>` user rows have `search_text` null, so `pond_search` for "factory-triage" finds nothing. A field-level scan of `parts` since 2026-09-01 found both sessions in 2.9 s (Q4): `94c8a3cf...` (triage, product, architecture, interface, slices) and `c8e025ee...` (build, review). Triage's arguments carry the task, not the slug; later steps carry the slug.

**F4. Per-step attribution works.** Splitting the main sessions at the command timestamps (Q5, Q6, Q7):

| Step | Wall clock (to next command) | Main turns | Main output tokens | Cache read | Questions (calls / items) | Human wait |
| --- | --- | --- | --- | --- | --- | --- |
| triage | 15.0 min | 28 | 21,718 | 3.35 M | 3 / 8, plus 3 free-text replies | 7.1 min |
| product | 6.0 min | 13 | 11,594 | 2.00 M | 2 / 8 | 1.3 min |
| architecture | 37.8 min | 29 | 32,439 | 6.04 M | 2 / 6 | 9.9 min |
| interface | 96.9 min | 69 | 89,452 | 22.95 M | 8 / 12 | 50.9 min |
| slices | 17.9 min | 8 | 12,615 | 3.31 M | 1 / 4 | 10.0 min |
| build | 17.3 min | 27 | 21,088 | 3.49 M | 1 / 1 (live check) | 4.1 min |
| review | 8.1 min | 18 | 23,346 | 3.66 M | 0, 1 free-text reply | n/a |
| total | 199 min | 192 | 212,252 | 44.8 M | 17 / 39 | 83 min |

The interface gate took 42% of main output tokens, 51% of cache reads and 49% of wall clock, over 6 panel rounds with 12 reviewer sub-agents (Q8). Wall clock minus human wait is the agent time: 116 of 199 minutes.

**F5. Raw user-turn counts are wrong without a filter.** Rows with `role = 'user'` include skill bodies ("Base directory for this skill"), command tags, `<task-notification>`, subagent hand-backs ("Another Claude session sent a message") and `<system-reminder>` text. Counting `search_text IS NOT NULL` already drops most of them (9 rows over both sessions), but one of the 9 is a system reminder joined to "approve both gates". Count a user turn only when the text does not start with `<` and is not a hand-back.

**F6. Subagent output tokens in Pond are unusable.** The executor wrote the whole slice, yet its largest per-turn `output_tokens` is 36 (Q9): subagent rows keep the stream-start snapshot. Reliable sources: the `<usage>subagent_tokens / tool_uses / duration_ms</usage>` block in the Agent tool result (all 5 in the build session, 556,992 tokens, 67 tool uses) or in `<task-notification>` text for background agents (6 of 13 background agents in the gate session); otherwise the input side (`input + cache_read + cache_write`) of the subagent's own rows. Main-session output tokens look plausible.

**F7. The interface panel loop has no bound and no record.** "Any changed signature goes through steps 3 and 4 again" (factory-interface/SKILL.md:104) ran 6 rounds; the user stopped round 7 by hand ("Approve now", 23:11Z), recorded only as prose at `challenges.md:5`. Rounds 5 and 6 waited 17 and 27 minutes on the user. Rounds per change and cards per round are the clearest friction metric this change shows, and today they can only be parsed from headings.

**F8. `challenges.md` cannot be counted by lens and rule as written.** 36 cards: 24 fix, 12 note; Responses 19 accept, 2 modify, 12 overrule, **3 left as the template `accept / modify / overrule:`** (`challenges.md:192,206,220`) although the gate requires every card answered (factory-interface/SKILL.md:106) and was approved. The APoSD lens is named four ways ("A Philosophy of Software Design" 12, "a-philosophy-of-software-design" 3, and section names "Interface Design Rules", "Forbidden Patterns", "Avoid Shallow Modules"), and rules are whole sentences that differ between rounds. Reconcile's "rule accepted three times" count (factory-reconcile/SKILL.md:53-58) would split one rule into several keys.

**F9. `review.md` findings carry no tag.** Slice 01 review: 12 polish findings, all fixed in `56bb493`, grouped as Correctness 9, Cleanliness 1, Design 2 (`review.md:18-34`); 12 more dropped after validation in one prose line (`review.md:36`); 0 `[lens/rule]` tags; all 4 lens reviewers "not run". Severity is absent. A repeated-finding metric needs a key on every finding, rubric or not.

**F10. Reconcile's Pond count would find nothing.** `challenges.md` was built by `cat` of reviewer temp files and edited by inline Python (Q10: 4 Write calls for gate documents, the rest Bash). No tool call ever carries the whole file, so "every challenges.md and review.md the factory wrote for other changes" (factory-reconcile/SKILL.md:53) cannot be read from Pond. The files are in each repository's git history; Pond is only useful to find which repositories ran the factory (Q4).

**F11. `status.yaml` erases its own history.** `sent_back` returns to `null` at re-approval, `rewind` returns to `pending`, and a reopened gate's new `approved_at` replaces the old one. Real case: during architecture the user chose "Merge, reopen product" (Q11); product was re-approved with architecture at the same instant (`status.yaml:12-13`, commit `a6bdb2a` "product and architecture"). The reopen survives only in the Pond answer text.

**F12. Build outcomes live in prose only.** From the transcript: red held first try (23:57:50Z), green first try (23:58:02Z), no executor stop, one continuation of the executor (`SendMessage`) to fix a finding from Claude Code's background security review. That fix became commit `d90933e fix(tg-mini-app): slice 01 webhook only with a secret`, outside every factory commit pattern and absent from `deviations`; `review.md:16` mentions it. A retro can catch such commits by pattern, but not their cause.

**F13. The factory hook was not installed.** `~/.claude/settings.json` has no `factory_gate` entry, and Pond holds no `factory gate (` tool result in the change's sessions (Q12). The real change ran without its source-edit gate. Hook blocks are a usable signal once installed (failed tool result, scoped scan), but retro must first report whether the hook was active.

**F14. The factory changed under the change.** The skills are symlinks into this repository (`~/.claude/skills/factory-triage` -> `skills/factory-triage`). Commit `fb8a155` (S9, 2026-10-10 22:16Z) added `ui:` to the triage template while the interface gate was running; S10 landed during build. `status.yaml` has no `ui` field, and review reports "UI/UX: not run: `ui` is not set" (`review.md:40`) although slice 10 is "Mini App screens". A retro comparing changes must know which factory commit each step ran on.

**F15. Environment friction is visible as tool failures.** Q13 over both sessions and the executor: git commit signing refused by the agent (exit 128), `gh` lacking permission to create a repository, the executor's type check failing before dependencies were installed, and 5 `Edit` calls rejected with "File has not been read yet" in the review session. These are the environment-fix candidates a retro should classify (signing, auth, install order, harness rules).

**F16. The track recommendation was overridden.** Triage recommended Critical (orders and deposit addresses); the user chose Standard (Q11). It is recorded only as a comment in `lenses.yaml:3`. Overrides are a calibration signal for triage's own rules.

**F17. Pond lags the live session.** `pond status` showed 422 Claude Code sessions pending sync, schedule every 5 minutes. A retro run at the end of a change may not see its own session. It should report the newest ingested timestamp for the change's sessions and say what is missing.

**F18. Session data contains instruction-shaped text.** The background security review stores its prompt as a user message in the `bitxchange-tg` project (session `95613d6c...`, "Now adversarially try to DISPROVE each one"), and harness reminders are stored as `role = 'user'`. Retro must treat all of it as data: exclude it from user-turn counts and never follow it.

## Proposed per-change metrics

Normalize per slice where a count grows with size; compare within the same track.

| ID | Metric | Source | Cost today |
| --- | --- | --- | --- |
| M1 | User questions per step: AskUserQuestion items plus free-text turns (F5 filter); headless: approver comments | Pond Q6; runner replies | query |
| M2 | Human wait minutes per step | Pond Q6 | query |
| M3 | Agent minutes per step (wall clock minus M2) | Pond Q5, Q6 | query |
| M4 | Main tokens per step (output, cache read, cache write) | Pond Q5 | query |
| M5 | Subagent tokens and tool uses per step | Agent results and task notifications; fallback input side (F6) | query |
| M6 | Interface panel rounds, cards per round, share overruled, unanswered cards | `challenges.md` | parse; `panel_round` event makes it exact |
| M7 | Gate send-backs and reopens, by gate and cause | `history` | needs A1 |
| M8 | Rewinds per slice | `history` | needs A1 |
| M9 | Red retries, green attempts, executor stops by reason, per slice | `history` | needs A1 |
| M10 | Review findings per slice by tag and outcome (fix, skip, follow-up, dropped); repeated tags across this repo's earlier changes | `review.md` | needs A4 |
| M11 | Deviations and off-pattern commits per slice | `deviations`, git log | parse |
| M12 | Hook blocks per step, and whether the hook was installed | Pond Q12, settings | query |
| M13 | Tool failures by class (auth, signing, install, harness rule, test) | Pond Q13 | query plus a small classifier on result text |
| M14 | Gate document lines vs budget | `wc -l` | free |
| M15 | Track proposed vs chosen | `track_proposed` | needs A3 |

## Trend view

- **Store each change's numbers with the change**, as one table in `.factory/changes/<slug>/retro.md`, committed like the rest. The trend reads the previous N changes' `retro.md` from git; no new store. The factory commit and track go in the table header, so a comparison can say "factory changed between these".
- **Compare** each metric with the median of the repository's previous 5 changes of the same track (fewer: say n), per slice where it applies, and flag only moves beyond a stated threshold; with n under 3, show values without a verdict.
- **Order the view by cost to the user**: M1 and M2 first, then M7 to M9 (rework), then M10 repeats (what the playbook should prevent), then M4 and M5.
- **Link each playbook entry to the metric it should move**, so the next retro can check whether it did.

## What to add, smallest first

- **A1. `history:` in `status.yaml`**, append-only, one line per event in the flow-map style the hook parses:
  `- { at: <ISO>, step: <skill>, event: <name>, ref: <gate or slice NN>, detail: "<short>" }`
  Events: `step_start` (detail: session id and factory commit), `gate_reopened` (cause: chain, sent_back, user), `sent_back`, `rewind`, `red_retry`, `green_retry`, `executor_stop` (reason), `panel_round` (n, cards), `off_plan_commit` (sha). `parse_status` only reads the `gates` and `slices` sections (factory_gate.py:39-61), so a new top-level key should not change the hook or runner; prove it with a case in `hooks/test_factory_gate.py`. The places that write each event are the lines cited in the signals table.
- **A2. Session and factory version** on `step_start`: the skill writes its own session id (Claude Code substitutes `${CLAUDE_SESSION_ID}` in skill text; verify on the installed version) and `git -C <factory repo> rev-parse HEAD`. Fallback when missing: the command scan Q4.
- **A3. `track_proposed:`** next to `track:` in the triage template.
- **A4. `review.md` finding lines with a fixed shape**: `- [<source>/<rule>] <severity> <path>: <finding> -> fix | skip | follow-up | dropped`, where source is the rubric lens, or the polish reviewer (`correctness`, `cleanliness`, `design`, `efficiency`, `gating`) when no rubric applies. Dropped findings get their own lines.
- **A5. `challenges.md`**: Lens / rule names the lens by its skill folder name and the rule by its heading in the lens file; each card gets `Round`. Approval greps for an unanswered Response (`accept / modify / overrule:`) and refuses, as the rule already requires.
- **A6. Reconcile counts from git, not Pond**: the repositories come from Q4's project paths and the `.factory/` folders they hold.

## Appendix: queries and outputs

All via `pond_sql` (Pond 0.19.5, local store), read-only. Session ids abbreviated in prose; full ids in the queries.

**Q1. Projects and session counts.**
```sql
SELECT project, source_agent, COUNT(DISTINCT session_id) AS sessions, MIN(timestamp) AS first, MAX(timestamp) AS last, COUNT(*) AS msgs
FROM messages WHERE project LIKE '%bitxchange-tg%' OR project LIKE '%software-factory%'
GROUP BY project, source_agent ORDER BY project, sessions DESC
```
`~/Work/bitxchange-tg` claude-code: 15 sessions, 449 rows. `~/Work/software-factory`: 51 main, 79 subagent sessions.

**Q2. The 15 `bitxchange-tg` sessions**: each 2 to 30 s, one user message (grouped by session_id with MIN/MAX timestamp). Reading one (`95613d6c-4e6b-436f-bc34-7b6757501e54`) shows a security-review side call over the slice diff.

**Q3. Sessions mentioning the slug.**
```sql
SELECT session_id, project, source_agent, MIN(timestamp), MAX(timestamp), COUNT(*)
FROM messages WHERE contains_tokens(search_text, 'tg-mini-app') GROUP BY 1,2,3 ORDER BY 4
```
Main sessions `94c8a3cf-fc32-4c3e-8b04-6d821940bed6` and `c8e025ee-b517-4e98-91b2-6e94a167c2bf`, project `~/Work/BitXchange-redesign`, with their subagents.

**Q4. Every session that invoked a factory skill** (2.9 s):
```sql
SELECT p.session_id, MIN(m.project) AS project, MIN(m.timestamp) AS first, COUNT(*) AS invocations,
  string_agg(regexp_replace(json_extract(p.variant_data, '$.text'), '(?s).*<command-name>/(factory-[a-z-]+)</command-name>.*', '\1'), ',') AS skills
FROM parts p JOIN messages m ON m.session_id=p.session_id AND m.message_id=p.message_id
WHERE p.type='text' AND m.role='user' AND m.timestamp >= '2026-09-01'
  AND json_extract(p.variant_data, '$.text') LIKE '%<command-name>/factory-%'
GROUP BY p.session_id ORDER BY first
```
```
94c8a3cf-...  ~/Work/BitXchange-redesign  2026-10-10T20:55:10Z  5  factory-product,factory-interface,factory-triage,factory-slices,factory-architecture
c8e025ee-...  ~/Work/BitXchange-redesign  2026-10-10T23:48:49Z  2  factory-build,factory-review
```

**Q5. Main-session tokens per factory step.**
```sql
WITH cmds AS (
  SELECT p.session_id, m.timestamp AS at,
    regexp_replace(json_extract(p.variant_data, '$.text'), '(?s).*<command-name>/(factory-[a-z-]+)</command-name>.*', '\1') AS step
  FROM parts p JOIN messages m ON m.session_id=p.session_id AND m.message_id=p.message_id
  WHERE p.session_id IN ('94c8a3cf-fc32-4c3e-8b04-6d821940bed6','c8e025ee-b517-4e98-91b2-6e94a167c2bf')
    AND p.type='text' AND m.role='user' AND json_extract(p.variant_data, '$.text') LIKE '%<command-name>/factory-%'),
spans AS (SELECT session_id, step, at AS start, LEAD(at) OVER (PARTITION BY session_id ORDER BY at) AS stop FROM cmds),
turns AS (
  SELECT m.session_id, json_get_string(m.options, 'anthropic', 'id') AS turn_id, MIN(m.timestamp) AS at,
    MAX(json_get_int(m.options, 'anthropic', 'usage', 'output_tokens')) AS out_tok,
    MAX(json_get_int(m.options, 'anthropic', 'usage', 'cache_read_input_tokens')) AS cache_read
  FROM messages m
  WHERE m.session_id IN ('94c8a3cf-fc32-4c3e-8b04-6d821940bed6','c8e025ee-b517-4e98-91b2-6e94a167c2bf')
    AND m.role='assistant' AND json_get_string(m.options, 'anthropic', 'id') IS NOT NULL
  GROUP BY m.session_id, turn_id)
SELECT s.step, s.start, COUNT(t.turn_id) AS turns, SUM(t.out_tok) AS output, SUM(t.cache_read) AS cache_read, MAX(t.at) AS last_turn
FROM spans s LEFT JOIN turns t ON t.session_id=s.session_id AND t.at >= s.start AND (s.stop IS NULL OR t.at < s.stop)
GROUP BY s.step, s.start ORDER BY s.start
```
Output in the F4 table. A correlated subquery for the same split is rejected ("Physical plan does not support logical expression ScalarSubquery"); use `LEAD` spans.

**Q6. Questions and human wait.**
```sql
SELECT mc.timestamp AS asked, mr.timestamp AS answered,
  CAST(EXTRACT(EPOCH FROM (mr.timestamp - mc.timestamp)) AS INT) AS wait_s,
  json_extract(c.variant_data, '$.params.questions[0].header') AS header,
  json_array_length(json_get(c.variant_data, 'params'), 'questions') AS n_questions
FROM parts c
JOIN messages mc ON mc.session_id=c.session_id AND mc.message_id=c.message_id
JOIN parts r ON r.session_id=c.session_id AND r.type='tool_result' AND r.call_id=c.call_id
JOIN messages mr ON mr.session_id=r.session_id AND mr.message_id=r.message_id
WHERE c.type='tool_call' AND c.tool_name='AskUserQuestion'
  AND c.session_id IN ('94c8a3cf-fc32-4c3e-8b04-6d821940bed6','c8e025ee-b517-4e98-91b2-6e94a167c2bf')
ORDER BY asked
```
17 calls, 39 questions, waits from 7 s to 1,635 s, total 4,996 s. Free-text turns: `role='user' AND search_text IS NOT NULL`, 9 rows (F5).

**Q7. Tool calls and failures per session.**
```sql
SELECT c.session_id = 'c8e025ee-b517-4e98-91b2-6e94a167c2bf' AS build_session, c.tool_name, COUNT(*) AS calls,
  SUM(CASE WHEN r.is_failure THEN 1 ELSE 0 END) AS failures
FROM parts c LEFT JOIN parts r ON r.session_id = c.session_id AND r.type='tool_result' AND r.call_id = c.call_id
WHERE c.type='tool_call' AND c.session_id IN ('94c8a3cf-fc32-4c3e-8b04-6d821940bed6','c8e025ee-b517-4e98-91b2-6e94a167c2bf')
GROUP BY 1, c.tool_name ORDER BY 1, calls DESC
```
Gate session: Bash 82 (2 failed), AskUserQuestion 16, Agent 15, Write 5. Build and review session: Bash 29 (2 failed), Edit 15 (5 failed), Agent 5, Skill 1 (`polish`), SendMessage 1, AskUserQuestion 1.

**Q8. Subagent sessions** (`sessions.parent_session_id` in the two main ids): 19 under the gate session (3 Explore, 1 document-specialist, 15 general-purpose, of which 12 are panel reviewers), 5 under build (1 executor, 4 polish reviewers).

**Q9. Subagent output tokens are stream-start snapshots.**
```sql
SELECT json_get_string(options, 'anthropic', 'id') AS turn_id, COUNT(*) AS rows,
  MAX(json_get_int(options, 'anthropic', 'usage', 'output_tokens')) AS max_out
FROM messages WHERE session_id = 'c8e025ee-b517-4e98-91b2-6e94a167c2bf/agent-ac475e87759013ae0' AND role='assistant'
GROUP BY turn_id ORDER BY max_out DESC LIMIT 5
```
Largest per-turn output: 36. Reliable alternative, from Agent results:
```sql
WITH a AS (SELECT r.session_id, json_extract(r.variant_data, '$.result') AS res FROM parts r
  WHERE r.type='tool_result' AND r.tool_name='Agent' AND r.session_id IN (...two main ids...))
SELECT session_id, COUNT(*),
  SUM(CAST(regexp_replace(res, '(?s).*subagent_tokens: ([0-9]+).*', '\1') AS BIGINT)) AS subagent_tokens,
  SUM(CAST(regexp_replace(res, '(?s).*tool_uses: ([0-9]+).*', '\1') AS BIGINT)) AS tool_uses
FROM a WHERE res LIKE '%subagent_tokens%' GROUP BY session_id
```
Build session: 5 agents, 556,992 tokens, 67 tool uses, 12 agent-minutes. Gate session: 2 of 15 (the rest ran in the background; their `<task-notification>` text carries `<usage>` for 6 of them).

**Q10. How the gate documents were written.** Tool calls in the gate session whose `file_path` or Bash command names a change file: `Write` for `01-product.md`, `02-architecture.md`, `03-interface.md`, `04-slices.md`; `challenges.md` only through Bash (`cat` of panel temp files, inline Python patches).

**Q11. Answers that changed the plan** (tool_result text of `AskUserQuestion` with header `Track`, `Decisions`, `Round 7`): track Standard against a Critical recommendation; "Merge, reopen product" during architecture; "Approve now" instead of panel round 7.

**Q12. Hook blocks.**
```sql
SELECT session_id, tool_name, is_failure FROM parts
WHERE type='tool_result' AND session_id IN (...two main ids..., 'c8e025ee-b517-4e98-91b2-6e94a167c2bf/agent-ac475e87759013ae0')
  AND json_extract(variant_data, '$.result') LIKE '%factory gate%'
```
0 rows. `grep factory_gate ~/.claude/settings*.json`: no match.

**Q13. Failed tool results** (`is_failure` in the two main sessions and the executor): Artifact parameter error 1, git signing refused 1, `gh` permission 1, executor type check before install 1, a Bash grep with no match 1, a Bash file read reported as failure 1, `Edit` before `Read` 5.

**Pond freshness.** `pond status`: 17,175 Claude Code sessions stored, 422 pending sync, last sync 5 minutes earlier, schedule every 5 minutes.
