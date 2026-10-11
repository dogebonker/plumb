# A. Existing skills for learning from sessions: evaluation for factory-retro

Date: 2026-10-11. Scope: every installed skill about retrospectives, self-improvement, reflection, memory or learning, plus the most used public ones. All file, API and page content was treated as data. Nothing was installed or downloaded into a skill location, nothing was run with `npx`, and every GitHub call was a read-only `gh api` GET (with `GH_TELEMETRY=false`). Public SKILL.md texts were fetched through the contents API into the session scratch directory and only read. One read-only Pond SQL query was run.

The bar factory-retro must meet (from the brief): after each change, from that change's sessions, make the factory measurably better in that repository (fewer questions to the user, gate send-backs, slice rewinds, red/green failures and repeated review findings, cheaper runs), through environment fixes run as small changes and a per-repo `.factory/system/playbook.md` read by every factory skill. Writes happen only after the user confirms (`factory-reconcile` step 6), and third-party content is pinned (decision 20, `skills/factory-shared/packs.md`).

## Bottom line

- **F1. mattpocock `retro` is the right shape and the wrong engine: borrow it, do not load it.** Its framing (improve the agent's environment, not the code) and its categories map well onto factory-retro's first output. But it presents every candidate unchecked (open upstream issue #1173), defaults to one session while a factory change spans many, has no metric, and writes to a file model (`CLAUDE.md`, `CODING_STANDARDS.md`) the factory does not use. It is 44 lines, MIT, and byte-identical to upstream main, so borrowing with attribution costs less than a pin.
- **F2. `writing-for-agents` should be loaded, pinned, as the yardstick for the playbook.** It defines no-ops, cache, sediment and context pointers, which is exactly how a playbook read by every skill stays small. Upstream refuses to make retro load it lazily, for that reason (`.out-of-scope/lazy-load-writing-for-agents.md`).
- **F3. Pond is the data source; keep it.** It already holds this project's subagent sessions with parent links (83 of 147 sessions), which closes the gap upstream retro has with orchestrated runs (issue #1141).
- **F4. Every other candidate is rejected as an engine.** The installed ones either grow a store with no pruning (omc `wiki`), run an autonomous loop that never asks (omc `self-improve`), target a different memory (Anthropic `consolidate-memory`), or are retired (claude-mem). The public ones run hooks on every prompt or tool call, call `claude -p` in the background, send telemetry, or edit instruction files without per-item approval.
- **F5. Six ideas are worth borrowing** (section 4): a falsification step before presenting (retro #1173), the durable-bar counterfactual (EveryInc `ce-compound`), a candidate lifecycle with proof after applying (zhaono1 `self-improving-agent`), staleness by referenced files (gstack `learn`), pruning rules for a capped file (Anthropic `consolidate-memory`), and an honesty boundary on savings (Ponytail `ponytail-gain`).

## Per-skill summary

| Skill | Source, license, pin | Reads | Writes | Executes / network | Verdict |
| --- | --- | --- | --- | --- | --- |
| retro | mattpocock/skills, MIT, tree `335c1862` = upstream main | session logs, steering files, repo checks | nothing (presents only) | none | **Borrow** (F1, F6 to F11) |
| writing-for-agents | mattpocock/skills, MIT, tree `ad292585` = upstream main | nothing | nothing | none | **Load, pinned** (F12) |
| pond | tenequm/pond, Apache-2.0, pond 0.19.5 | session store over MCP | nothing (read-only SQL) | local MCP server | **Load** (already the memory layer, F13) |
| self-improve | oh-my-claudecode 5.6.1, MIT | repo, benchmark | `.omc/self-improve/`, git branches, merges | runs benchmark, `git reset --hard`, optional push | **Reject**, borrow sealed evaluator and stop conditions (F15) |
| wiki | oh-my-claudecode 5.6.1, MIT | `.omc/wiki/` | a page per session, gitignored | SessionEnd hook | **Reject** (F16) |
| autoresearch, remember, skillify | oh-my-claudecode 5.6.1, MIT | varies | `.omc/` | evaluator loop | **Reject** (F17) |
| consolidate-memory | Anthropic desktop skills | auto-memory dir | `MEMORY.md` and topic files | none | **Reject**, borrow pruning rules (F18) |
| skill-creator | Anthropic, Apache-2.0 | skill, eval prompts | workspace, evals | subagents, `claude -p` loop, local viewer | **Reject**, borrow baseline comparison (F19) |
| claude-md-management | Anthropic, Apache-2.0, not installed | session, CLAUDE.md | CLAUDE.md after approval | none | **Reject**, borrow per-item diff with reason (F20) |
| ponytail-debt, ponytail-gain | DietrichGebert/ponytail 4.11.0, MIT | `ponytail:` comments | nothing | grep | **Reject**, borrow honesty boundary (F21) |
| claude-mem skills | thedotmack/claude-mem 13.25.3, Apache-2.0 | local worker on localhost | varies | curl to worker | **Reject** (retired, F22) |
| conducting-post-incident-lessons-learned | mukul975, Apache-2.0 | ticketing, SIEM | Jira issues | `curl -X POST` | **Reject** (F23) |
| gstack retro, learn | garrytan/gstack `45a67832`, MIT | git log, learnings JSONL | `.context/retros/`, learnings | preamble binary, telemetry sync | **Reject**, borrow file-based staleness (F24) |
| ce-compound, ce-compound-refresh | EveryInc/compound-engineering-plugin, MIT | session, repo | `docs/solutions/`, `CONCEPTS.md`, instruction file, commits | subagents | **Reject**, borrow durable bar (F25) |
| claude-reflect | BayramAnnakov/claude-reflect `25d53381`, MIT | every prompt | queue, CLAUDE.md files incl. global | 4 hooks, `claude -p` | **Reject** (F26) |
| continuous-learning-v2 | affaan-m/ECC `afa0b356`, MIT | every tool call | instincts under XDG data dir | hooks, background Haiku observer | **Reject** (F27) |
| self-improving-agent | zhaono1/agent-playbook `be7a9d7d`, MIT | evidence | candidates under `~/.agent-playbook/` | `apb` CLI | **Reject**, borrow lifecycle (F28) |

## 1. mattpocock `retro`

Installed at `~/.agents/skills/retro/` (symlinked from `~/.claude/skills/retro`): `SKILL.md` (44 lines) and `agents/openai.yaml` (`allow_implicit_invocation: false`).

### Upstream, pin and history

- **F6. The installed copy is byte-identical to upstream main.** `~/.agents/.skill-lock.json` records `skillFolderHash` `335c1862a43da9d629abafdb79ca0c0de118be08` (installed 2026-10-06). `gh api repos/mattpocock/skills/contents/skills/engineering` returns that tree SHA for `retro` on main; `git hash-object` of `SKILL.md` (`12149acf`) and `agents/openai.yaml` (`a2f0bac3`) match the upstream tree blobs. Same for `writing-for-agents`: lock `ad2925850efb8973a72d2e666f7a975f9a2d4a9b`, three of three blobs match main.
- **F7. Upstream is large, active and versioned.** `repos/mattpocock/skills`: MIT (`LICENSE`: "Copyright (c) 2026 Matt Pocock"), created 2026-02-03, about 284k stars and 24k forks, 9 tags and 9 releases, last push 2026-10-09, top contributor mattpocock with 499 commits. skills.sh lists `retro` at 205,950 installs, the most installed retrospective skill by far (next: `bmad-retrospective`, 8,174; not read).
- **Retro path history:** created in `skills/in-progress/retro` on 2026-08-24 (`8fa18865`), "Information access" added the same day (`6654f6b6`), "push mechanical coding-standards findings toward deterministic checks" on 2026-09-15 (`0243b6ec`), graduated to `skills/engineering/retro` on 2026-09-24 (`a7d038f6`). No retro commit since. On 2026-10-09 upstream recorded as out of scope a request to load `writing-for-agents` only before writing (`82672251`, `.out-of-scope/lazy-load-writing-for-agents.md`): "`retro` uses those definitions to judge the steering files it reads, before it writes anything."

### What it does

- **F8. Read-only, no execution, no network, no writes.** Step 1 calls the Skill tool for `writing-for-agents` (`SKILL.md:11`). Step 2 reads "the primary sources for the session the user specifies ... searching through session logs on this machine", defaulting to the current session (`:13`). Step 3 looks for candidates in seven categories (`:17-23`). Step 4 presents them by severity (`:25`). It is user-invoked only (`:4`), so by its own reference no other skill can fire it (`writing-for-agents/SKILL-MECHANICS.md:10`): factory-reconcile could only read it as a file, the way packs are loaded.
- What is good, with evidence:
  - Environment, not code, is the target (`:7`). That matches output (1) of factory-retro.
  - "Read the repo's own check command first ... so a check that already exists but sits unwired or silently broken is the finding, not a reinvention" (`:18`).
  - A mechanical violation "gets a deterministic check, full stop", and judgement calls go to the reviewer's standards (`:19`). This matches the factory's "mechanical before model" and its `linter.propose` lesson route (`factory-reconcile/SKILL.md:58`).
  - Implementation carries the most context pressure, so standards belong to review (`:31-35`).
  - `CLAUDE.md`/`AGENTS.md` "used incredibly sparingly, usually only for navigation pointers" (`:41`).

### Gaps against factory-retro

- **F9. No candidate is checked before it is shown.** Open issue #1173 (2026-10-05, mecampbellsoup) reports that in 15 of 17 runs over two weeks the user then asked the agent to prove the candidates, that one check usually killed a candidate, and that counting recurrence is not the test: "did it ever cost anything?". It proposes stating what you would observe if the change were needed, running the narrowest check against logs, repo or git history, presenting only survivors with their check, and accepting zero survivors as a complete retro. No upstream response yet.
- **F10. One session is the wrong unit.** A factory change runs triage, four gates, then build and review per slice, each in a fresh session, with subagents inside. Issue #1141 (subagent sessions as primary sources) was closed as completed on 2026-10-05, but the retro text at main still says only "the session the user specifies" (`:13`), and no retro commit followed. Pond already covers this (F13).
- **F11. Its categories miss most of factory-retro's metrics, and its file model is not the factory's.** None of the seven categories counts questions to the user, gate send-backs (`sent_back` in `status.yaml`, `gates.md` "Send back"), slice rewinds, red/green failures or cost, and nothing compares before and after. Its destinations are `CLAUDE.md`, `CODING_STANDARDS.md`, docs and skills (`:41-44`); the factory's are the review rubric and lenses, `principles.md` (Quiet rules, Principles), language-pack `linter.propose`, `.factory/system/` documents, and now the playbook. Loading it as written would point the agent at files the factory does not read.

**Verdict: borrow.** Take the framing, the "existing check first" rule, the mechanical-to-check rule, the implementation/review split, and the categories Navigation, Automated checks, Tool economy, No-ops and Information access, with attribution (MIT). Add what it lacks: the falsification step of #1173, multi-session input from Pond, factory metrics, and the factory's destinations.

## 2. `writing-for-agents`

- **F12. Load it, pinned at `ad292585`, when drafting or pruning the playbook and when judging steering files.** Source `mattpocock/skills/skills/productivity/writing-for-agents` (MIT), renamed from `writing-great-skills` on 2026-07-23 (`1fc6573e`), last changed 2026-08-19 (`32165827`, em-dash removal). Pure reference, 81 + 22 lines, no steps that execute or write. The rules factory-retro needs most:
  - a document that restates the environment is a **cache**, worth keeping only for what the agent cannot find by looking (`SKILL.md:79`)
  - **sediment**: without pruning, stale layers settle "because adding feels safe and removing feels risky" (`:80`)
  - **no-ops**: delete an instruction that does not change behaviour versus the default (`:81`)
  - **context pointers** and their wording decide whether material is reached (`:10-18`)
  - prompt the positive target rather than the prohibition (`:74`)
  - user-invoked skills cannot be reached by other skills (`SKILL-MECHANICS.md:10`)
- Fits the factory's pack mechanism unchanged: `packs.md` "Check the pin" compares `packs.lock.yaml` with `skillFolderHash`, and this skill has one.
- Side finding: the older `writing-great-skills` is still installed (`~/.agents/skills/writing-great-skills`, lock `81d36946`), although its upstream path now returns 404. It is user-invoked, so it costs no context, but it is stale.

## 3. Installed skills

- **F13. Pond (load).** `~/.claude/skills/pond/SKILL.md`, pond 0.19.5 (latest release v0.19.5, 2026-10-02, Apache-2.0). Read-only tools; the skill warns that search covers conversational text only and that token usage must be grouped per provider turn (`SKILL.md:32-42`), both of which matter for counting cost and questions. Query on 2026-10-11: `sessions` with project `software-factory` = 147, of which 83 have a `parent_session_id`. Side finding: `~/.agents/skills/pond/SKILL.md` is a mangled copy in which "Claude" became "Codex" (`:3`, `:53-54`); the `~/.claude` copy is intact.
- **F14. Factory-reconcile already does part of the counting.** Step 5 counts lens accepts and rejects through Pond across all changes (`factory-reconcile/SKILL.md:53`). Factory-retro should reuse that count rather than repeat it.
- **F15. omc `self-improve`: reject.** A tournament loop for raising a benchmark score: planners, critics and executors in worktrees, winners merged. "NEVER stop or pause to ask the user during the improvement loop" (`SKILL.md:15`), reverts with `git reset --hard HEAD~1` (`:276`), and can push and open PRs when settings allow (`:278`, `:347`). It conflicts with the factory's approval model. Worth borrowing: evaluation files the loop cannot modify ("sealed files", `:25`) and explicit stop conditions (plateau, circuit breaker, `:306-316`).
- **F16. omc `wiki`: reject.** Keyword-matched pages under `.omc/wiki/`, git-ignored by default (`SKILL.md:65-67`), so nothing is shared with the team or other machines. Auto-capture is on by default (`:62-63`): the SessionEnd hook writes a page per session holding only the session ID and "Review and promote significant findings" (`dist/hooks/wiki/session-hooks.js:71-115` in `oh-my-claude-sisyphus` 5.6.1). That is growth with no content and no pruning.
- **F17. omc `autoresearch`, `remember`, `skillify`: reject.** `autoresearch` needs a pre-built evaluator and keeps iterating on failure (`SKILL.md:25-31`). `remember` and `skillify` are in the npm package but not installed in `~/.claude/skills`; `remember` writes to omc notepad and project memory (`:13-17`), `skillify` writes learned skills to `~/.claude/skills/omc-learned/` (`:47-49`). Neither measures anything.
- **F18. Anthropic `consolidate-memory`: reject, borrow pruning.** It works on the desktop auto-memory directory and `MEMORY.md`, not on a repository. Its rules carry over to a capped playbook: separate the durable from the dated (`SKILL.md:19`), "Drop what's easy to re-find" (`:25`), keep the index under 200 lines and about 25 KB, one line per entry (`:29`).
- **F19. Anthropic `skill-creator`: reject, borrow the comparison.** Built for writing skills, with subagent eval runs, a browser viewer and a `claude -p` description loop (`SKILL.md:382-394`). Useful method: run the same tasks with and without the change (`:169-186`), watch for assertions that pass either way (`:234`), and pick by a held-out set, not the training set (`:394`). Its advice to make descriptions "a little bit pushy" (`:67`) contradicts `writing-for-agents`' pruning of always-loaded pointers.
- **F20. `claude-md-management` (`revise-claude-md`, `claude-md-improver`): reject, borrow the proposal shape.** Present in the official marketplace clone but not in `installed_plugins.json`. Each addition is shown as a diff with a one-line reason and applied only with approval (`commands/revise-claude-md.md:38-54`), and one-off fixes are excluded (`:36`). It targets `CLAUDE.md`, which retro (F8) and the factory both keep minimal, and its letter grades (`claude-md-improver/SKILL.md:50-56`) clash with the factory's no-score stance (CI-5).
- **F21. Ponytail `ponytail-debt` and `ponytail-gain`: reject, borrow the honesty boundary.** `ponytail-gain` refuses to print a per-repo savings number because "the unbuilt version was never written, so there is no real baseline" (`SKILL.md:41-45`). Factory-retro has the same trap when it claims an environment fix saved questions or tokens. `ponytail-debt` tags markers with no upgrade trigger as rot risk (`SKILL.md:35-36`), the same test a playbook line needs.
- **F22. claude-mem leftovers: reject.** The plugin is retired by the user's own instructions and absent from `installed_plugins.json`, but `~/.claude/plugins/cache/thedotmack/claude-mem/13.25.3/skills/` still holds 20 skills. The memory ones depend on a worker on localhost (`timeline-report/SKILL.md:25`, `:61`) and read derived observations, not transcripts.
- **F23. mukul975 `conducting-post-incident-lessons-learned`: reject.** A security incident review that posts Jira issues with a bearer token (`SKILL.md`, Step 5 `curl -X POST`). Wrong domain.
- Not relevant: superpowers 6.4.1 has no learning skill; mattpocock `handoff` writes a handoff doc to the OS temp directory; `teach`, `improve-codebase-architecture` and `autopilot`/`ralph`/`team` mention lessons only in passing.

## 4. Public skills

Searched with `gh search code --filename SKILL.md` for "retrospective", "self-improve", "lessons learned", "learn from session", and the skills.sh search API for "retro" and "self-improving". Read in full: the four highest by stars or installs that target coding sessions, plus the most installed self-improving skill.

- **F24. garrytan/gstack `retro` and `learn` (MIT, 135k stars, read at `45a67832`, 2026-10-10): reject, borrow staleness by file.** `retro` is a weekly git-commit productivity report with per-person praise and streaks (`retro/SKILL.md:41-47`, `:416-433`), not a session retro. Every run starts by executing `gstack-skill-start` (`:51-53`) and ends with telemetry (`:352-371`); `bin/gstack-telemetry-sync` sends events with curl to a remote host by privacy tier. The learnings store borrowable parts: each learning carries a type, a source (`observed`, `user-stated`, `inferred`), a confidence and the files it references "to enable staleness detection" (`:866-891`); `learn prune` flags a learning whose files are gone and same-key contradictions (`learn/SKILL.md:408-436`); a run with nothing learned says so explicitly (`retro/SKILL.md:339-344`).
- **F25. EveryInc `ce-compound` and `ce-compound-refresh` (MIT, 25k stars): reject, borrow the durable bar.** They write `docs/solutions/` docs, `CONCEPTS.md`, a line in a project instruction file after consent, and commit (`ce-compound/SKILL.md:56-60`, `ce-compound-refresh/SKILL.md:82-88`); non-interactive mode "asks nothing" (`ce-compound/SKILL.md:42`). Borrow: the counterfactual "if the learning document disappeared, would a future engineer ... still be likely to repeat the mistake or redo substantial investigation?", with "Completion, effort, and diff size do not establish eligibility" (`:20-24`); one learning per run (`:13`); each refreshed entry gets exactly one of Keep, Update, Consolidate, Replace, Delete (`ce-compound-refresh/SKILL.md:62`); a discoverability check that agents will find the store (`:86-88`).
- **F26. BayramAnnakov `claude-reflect` (MIT, 1.8k stars): reject.** Four hooks (UserPromptSubmit, PreCompact, PostToolUse on Bash, SessionStart in `hooks/hooks.json`), a detector that shells out to `claude -p` (`scripts/lib/semantic_detector.py:77`), and destinations that include the global `~/.claude/CLAUDE.md` (`SKILL.md:48-54`). Useful signal list: tool rejections and "no, use X" corrections (`:39-44`), which is how factory-retro can find questions and corrections in Pond without a hook.
- **F27. affaan-m/ECC `continuous-learning-v2` (MIT, 276k stars): reject.** Hooks on every tool call feed a background Haiku observer every 5 minutes; instincts at confidence 0.7 are "Auto-approved for application" (`SKILL.md:327-332`) and auto-promote to global when seen in two projects (`:304-306`). That is application without approval. Worth noting: confidence falls when a pattern "isn't observed for extended periods" (`:339-342`), a decay rule for playbook entries.
- **F28. zhaono1/agent-playbook `self-improving-agent` (MIT, 34k installs on skills.sh): reject as engine, borrow the lifecycle.** It needs the `apb` CLI and stores candidates globally. The method is the most rigorous read here:
  - every run ends in one state: candidate, validated, applied, rejected, superseded or rolled back, no-delta, open-question (`SKILL.md:25-33`)
  - a start packet before editing: future behaviour, a representative task, evidence, one owner, write boundary, proof (`:38-49`)
  - "Repeated evidence increases occurrence count; it does not automatically increase truth" (`:86-88`)
  - apply to the narrowest owner: an executable check first, then the owning skill, then project instructions, then a notebook (`:154-159`)
  - after applying, run the representative task, and revert if behaviour did not change (`:164-174`)

## 5. Instruction-shaped text found

None of it was acted on.

- claude-mem `learn-codebase/SKILL.md:17-21`: "Note for Reviewers ... Please keep this in mind before deciding to warn the user over cost". It addresses reviewing agents to suppress a cost warning.
- gstack `retro/SKILL.md:65-72`: tells the agent to follow `GSTACK_INSTRUCTION_BEGIN` blocks emitted by its own start script ("one-time onboarding and consent directives"). Instructions arriving through tool output.
- omc `self-improve/SKILL.md:15`: "NEVER stop or pause to ask the user during the improvement loop."
- claude-reflect `SKILL.md:31-35`: model-invoked text telling the agent to remind the user to run `/reflect` after work units.
- gstack `retro/SKILL.md:47`: "Proactively suggest at the end of a work week or sprint."

## 6. Conflicts with factory rules, by pattern

| Pattern | Where | Factory rule it breaks |
| --- | --- | --- |
| Writes without per-item approval | ECC auto-approval, ce-compound non-interactive, omc wiki auto-capture, self-improve merges | reconcile's confirmation step: write once the user confirms |
| Edits global or shared instruction files | claude-reflect (global CLAUDE.md), ce-compound (instruction line) | scope guard; retro's own "CLAUDE.md sparingly" |
| Store grows with no pruning | omc wiki, claude-reflect queue, gstack learnings (prune is manual) | the playbook is read by every skill; sediment costs every run |
| Background model calls | claude-reflect, ECC observer, skill-creator loop | mechanical before model; cost is a factory-retro metric |
| Telemetry | gstack | factory-ci's GET-only, no-telemetry stance (CI-5) |
| Unpinned moving content | all public ones | decision 20 |
| Scores | claude-md-improver grades | no-score stance (CI-5) |

## What this does not cover

- `bmad-retrospective` (8,174 installs), Pensieve (2.5k stars), Continuous-Claude `compound-learnings` and the long tail of `self-improving-agent` forks were listed by the searches but not read.
- No skill was run. Verdicts rest on reading the text, the scripts named above and upstream metadata.
- Whether Pond's schema can attribute sessions to one factory change (branch, slug) is not checked here.
