# factory-retro: how agents learn from their own sessions, and how that memory fails

Lane B for factory-retro. Date: 2026-10-11. Sources: arXiv papers (abstract and HTML full text, read live), vendor documentation (Claude Code, Claude API, Codex, Cursor, Devin, GitHub Copilot, agents.md), and engineering write-ups from Anthropic, GitHub and two security researchers. Every number below was read from the source named next to it. Sources marked (secondary) were read only through other people's summaries.

## Verdict

Learning from experience works when three things hold, and degrades below no memory at all when they do not:

- **The signal that admits a lesson is external.** Every memory method that gained used a check the agent could not talk its way past: environment success, unit tests, a fine-tuned or strict judge. Adding every experience without a strict filter made all four agents in one controlled study worse than a fixed memory (F11). Self-generated tests with a 16% false-positive rate were the main reason Reflexion lost on MBPP (F1).
- **Memory is itemized, counted and pruned, never rewritten whole.** ExpeL keeps per-insight vote counts and deletes at zero (F2). ACE keeps per-bullet helpful and harmful counters and merges deltas with non-LLM code; a full LLM rewrite collapsed an 18,282-token context to 122 tokens and dropped accuracy below the no-memory baseline (F12).
- **What is loaded is short and relevant.** Repository context files cost about 20% more inference and did not raise success; LLM-written ones lowered it slightly (F14). Every vendor sets a size ceiling (F7 to F9) and tells users to prune.

For the factory this means: environment fixes beat text (a check fires every time, a sentence is advisory), and a playbook entry should exist only when an external signal saw the same failure more than once, it cites where it applies, it has counters, and a human approved it. Session transcripts are untrusted input: query-only attackers planted memories with a 98% injection success rate and no tested detector stopped them (F16).

## Findings

### Methods: what form of memory helped

**F1. Reflexion: verbal self-reflection in a tiny episodic buffer, gains only where feedback is reliable.** Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", NeurIPS 2023, [arXiv:2303.11366](https://arxiv.org/abs/2303.11366). The agent writes a reflection after each failed trial and keeps it for the next trial of the *same* task. Memory is bounded to "a maximum number of stored experiences, Omega (usually set to 1-3)" (section 3); 1 for programming. Results: HumanEval pass@1 91.0 vs 80.1 for GPT-4, ALFWorld 130 of 134 tasks, HotPotQA +20%. Where it did not help: MBPP Python 77.1 vs 80.1, explained by a 16.3% false-positive rate of self-generated tests (1.4% on HumanEval); WebShop showed no improvement after four trials, and the authors conclude it "is unable to solve tasks that require a significant amount of diversity and exploration" (appendix B.1). Without test generation, accuracy fell to 52%, below the 60% baseline. Lesson for retro: reflection is only as good as the pass/fail signal under it, and it was within-task, not cross-task.

**F2. ExpeL: cross-task natural-language insights plus retrieved trajectories, with vote counts.** Zhao et al., "ExpeL: LLM Agents Are Experiential Learners", AAAI 2024, [arXiv:2308.10144](https://arxiv.org/abs/2308.10144). Insights are extracted by comparing failed and successful trajectories, and maintained with four operations: ADD, EDIT, UPVOTE, DOWNVOTE. A new insight starts at importance 2; it is removed at 0 because "even successful trajectories can be suboptimal and mislead the generated insights" (section 4.2). Successful trajectories are retrieved by task similarity (Faiss, top-k 2 to 6). Gains: ALFWorld 40% (ReAct) to 59%, HotpotQA 28% to 39%. Ablations: insights alone and retrieval alone are each weaker than both; hand-crafted insights scored 32% vs 39% for extracted ones; task-similarity retrieval 59% vs random 42.5% (table 3). Transfer from HotpotQA to FEVER: 63% (ReAct) to 70%. Limitation the authors name: insights fit in context only while they are few; lifelong use "might" need retrieval.

**F3. Voyager: a skill library of executable code, admitted only after verification.** Wang et al., "Voyager: An Open-Ended Embodied Agent with Large Language Models", [arXiv:2305.16291](https://arxiv.org/abs/2305.16291). A skill is added only "until self-verification validates the task's completion" (section 2.3); skills are indexed by an embedding of their description and the top 5 are retrieved. Without self-verification, discovered items dropped 73%, the largest ablation effect; without the library, progress plateaus (section 3.4). The library transferred to a new world. Lesson: code that runs is a more durable lesson form than prose, and the admission gate mattered more than the library.

**F4. Agent Workflow Memory: abstracted workflows; mixing sources hurt.** Wang, Mao, Fried, Neubig, [arXiv:2409.07429](https://arxiv.org/abs/2409.07429). Workflows are step sequences with example values replaced by placeholders, induced from successful trajectories and appended to memory per website. Relative success +24.6% on Mind2Web and +51.1% on WebArena, with fewer steps. Cross-domain step success 18.6 to 35.5; cross-website gains were only 3.6 to 3.8 points (table 4). Online induction from model-judged trajectories "can lead to incorrect workflows that degrade model performance" (section 3.2.2). Combining offline and online workflows did worse than either: "not fully compatible" (appendix C). Exposing workflows as callable actions was used in only 18.5% of tasks and lowered task success.

**F5. Self-Refine: in-session iteration, no persistence.** Madaan et al., NeurIPS 2023, [arXiv:2303.17651](https://arxiv.org/abs/2303.17651). Generate, self-critique, refine, about 20% absolute average gain over one-shot generation on 7 tasks. Nothing is kept across tasks, so it is a within-slice technique (what factory-build and review already do), not a retro technique.

**F6. Dynamic Cheatsheet and ACE: curated, label-free memory; weak signal pollutes it.** Suzgun et al., [arXiv:2504.07952](https://arxiv.org/abs/2504.07952): a curator keeps "concise, transferable snippets rather than entire transcript"; GPT-4o Game of 24 went from 10% to 99% by reusing one code snippet. But smaller models "showed more limited and inconsistent gains" (section 4.5), and "faulty heuristics that slip into memory can be equally amplified" (section 5). Zhang et al., "Agentic Context Engineering", ICLR 2026, [arXiv:2510.04618](https://arxiv.org/abs/2510.04618), calls the evolving context a "playbook": itemized bullets with an ID and helpful/harmful counters, updated by deltas merged "by lightweight, non-LLM logic", de-duplicated by embedding. Without ground-truth labels, finance accuracy fell (FiNER 70.7 to 67.3 online) because the context "can be polluted by spurious or misleading signals"; on AppWorld it still gained because code execution itself gives a pass/fail.

### Vendor memory: forms, scope, limits

**F7. Claude Code: CLAUDE.md is advisory context with a 200-line target; auto memory is machine-local and capped at load.** [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory):
- Hierarchy: managed policy, user, project, local, plus `.claude/rules/` with `paths:` globs that load only for matching files. Files are concatenated, not overridden; conflicting instructions mean "Claude may pick one arbitrarily". Imports reach four hops and "don't reduce its context cost".
- Size: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."
- When to add: "Claude makes the same mistake a second time", or "A code review catches something Claude should have known".
- Status: "Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook."
- Auto memory: `~/.claude/projects/<project>/memory/`, a `MEMORY.md` index plus topic files; only "the first 200 lines of MEMORY.md, or the first 25KB" load; it skips "anything it can derive from the codebase" and anything CLAUDE.md already says; machine-local, not shared.
- External imports in a project file need a one-time approval dialog "to protect you from files other people commit to a shared project".
- `/doctor prompt-audit` finds instructions for older models, references to missing files, and contradictions, and changes nothing until asked.

[Best practices](https://code.claude.com/docs/en/best-practices): for each line ask "Would removing this cause Claude to make mistakes?"; "If Claude already does something correctly without the instruction, delete it or convert it to a hook"; hooks are "deterministic", CLAUDE.md is "advisory"; emphasizing many lines makes none stand out. Transcripts are deleted after `cleanupPeriodDays`, default 30 ([settings reference](https://code.claude.com/docs/en/settings-reference)); this machine does not override it, so retro reading raw transcripts must run within 30 days or read Pond.

**F8. Codex and AGENTS.md: nearest file wins, 32 KiB cap; memories are generated state, not rules.** [agents.md](https://agents.md/): nearest AGENTS.md to the edited file wins, explicit chat prompts override; listed test and lint commands are run. Stewarded by the Agentic AI Foundation under the Linux Foundation. Codex ([AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)): one file per directory from root to cwd, later files override earlier, combined size stops at `project_doc_max_bytes`, default 32 KiB. Codex Memories ([docs](https://learn.chatgpt.com/docs/customization/memories)): off by default, generated in the background from idle chats into `~/.codex/memories/`, secrets redacted; the docs say to keep required team guidance in AGENTS.md because memories are a recall aid, and give no approval step.

**F9. Cursor, Devin, Copilot: scoping, suggest-then-approve, and citations with expiry.**
- Cursor ([rules](https://cursor.com/docs/context/rules)): Always, Apply Intelligently, glob-scoped, Manual; "Keep rules under 500 lines"; add rules when the agent "repeats the same mistake"; use a linter instead of copying a style guide; reference files instead of copying them so rules do not go stale. The page documents no auto-generated memories.
- Devin ([knowledge](https://docs.devin.ai/product-guides/knowledge)): items have a trigger and are retrieved when work matches it; suggested from chat feedback, and the user can edit before saving or dismiss; content "should be a handful of sentences", one workflow per item. Knowledge is now deprecated in favor of skills.
- GitHub Copilot Memory ([docs](https://docs.github.com/en/copilot/concepts/agents/copilot-memory); [engineering post, 2026-01-15](https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/)): each repository fact carries citations to code locations; before use the agent checks them against the current branch and "Only validated facts are used"; unused entries are deleted after 28 days, and validated use resets the timer. Only users with write access create repository memories. Adversarial memories seeded with bad citations were found and corrected in stress tests ("The memory pool self-healed"). Measured: coding-agent PR merge rate 90% vs 83% (A/B, p < 0.00001), code review +3% precision and +4% recall offline.

**F10. Anthropic memory tool guidance: strip secrets, cap size, expire.** [Memory tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool), security section: Claude usually refuses to write sensitive data, but "add validation that strips sensitive data before your handler writes the file"; "cap how large a file can grow"; "Periodically delete memory files that haven't been accessed in a long time"; validate every path. [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (2025-09-29): aim for "the smallest possible set of high-signal tokens"; instead of a laundry list of edge cases, "curate a set of diverse, canonical examples".

### Failure modes

**F11. Unfiltered addition makes agents worse than no learning; deletion recovers some.** Xiong et al., "How Memory Management Impacts LLM Agents", [arXiv:2505.16067](https://arxiv.org/abs/2505.16067). Agents copy retrieved memories when inputs look alike ("experience-following"), so stored errors propagate. Add-all fell below a fixed memory on all four agents, by 3.7 to 12.1 points; strict addition beat add-all by 15.5 to 25.5 points with 13 to 58% fewer records (table 1). History-based deletion of records that later led to failures added up to +4.2 points; combined deletion cut memory about 70 to 79% with small losses (table 2). The authors note future task outcomes are "free quality labels for stored memory", and that unbounded growth is "unnecessary".

**F12. Rewriting the whole memory collapses it.** ACE, section 2.2: at step 60 the context held 18,282 tokens and scored 66.7; the next full rewrite left 122 tokens and 57.1, below the 63.7 no-memory baseline. The fix is incremental, ID-addressed deltas (F6).

**F13. Overgeneralization and narrow transfer.** AWM's cross-website gain was a fraction of its in-domain gain (F4); ExpeL's ablation shows insights need retrieved examples to work (F2); Reflexion helped retries of one task, not new tasks (F1). Vendors converge on a count of at least two: Claude Code adds on "the same mistake a second time" (F7), Cursor on repeats (F9). The factory already uses three for principles (`skills/factory-reconcile/SKILL.md` step 5).

**F14. No-op and harmful instructions: followed, paid for, not useful.** Gloaguen et al., "Evaluating AGENTS.md", ICLR 2026, [arXiv:2602.11988](https://arxiv.org/abs/2602.11988). LLM-generated context files lowered resolution in 5 of 8 settings (about -0.5% on SWE-bench Lite, -2% on AGENTbench) and raised cost about 20 to 23% (2.45 to 3.92 more steps). Developer-written files gained about 4% on average but not for Claude Code, at up to 19% more cost. Agents obey: `uv` was used 1.6 times per task when mentioned vs under 0.01 when not. Repository overviews did not shorten the path to the right file. When existing docs were removed, generated files helped (+2.7%): they were "redundant documentation". Recommendation: limit files to minimal requirements, because "unnecessary requirements from context files make tasks harder". ExpeL's hand-written insights also scored below extracted ones (F2).

**F15. Stale and contradicted lessons.** Copilot's design treats staleness as the main problem: knowledge must stay "valid as code evolves", solved by cited locations checked at use time (F9). Claude Code warns that contradictions resolve arbitrarily and offers an audit for references to files that no longer exist (F7). Cursor: reference files, do not copy them (F9).

**F16. Memory poisoning needs no write access.** MINJA, Dong et al., [arXiv:2503.03704](https://arxiv.org/abs/2503.03704): an attacker who can only send queries gets malicious records stored, with average injection success 98.2% and attack success 76.8%. Embedding-level sanitization "fails in practice" because malicious and benign records are entangled; an LLM detector flagged 0 of 135 and 0 of 90 on two agents with a targeted prompt, and a general prompt flagged 34 of 50 benign records on another; no evaluated defense stopped it (section 5.4). AgentPoison, Chen et al., NeurIPS 2024, [arXiv:2407.12784](https://arxiv.org/abs/2407.12784): over 80% attack success with under 0.1% poisoned records and under 1% benign impact. SpAIware, Rehberger, [embracethered.com, 2024-09-20](https://embracethered.com/blog/posts/2024/chatgpt-macos-app-persistent-data-exfiltration/): a prompt injection in a web page or document made ChatGPT store attacker instructions as a long-term memory that exfiltrated every later chat; the exfiltration channel was fixed, the memory write was not, and the author's advice is to review stored memories regularly. OWASP lists this as ASI06 Memory and Context Poisoning in the Top 10 for Agentic Applications, published 2025-12-09 ([OWASP](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)); mitigations cited by others are write-time validation, provenance, segmentation, snapshots and rollback (secondary: [vectorize.io](https://vectorize.io/articles/owasp-asi06), [OWASP Agent Memory Guard](https://owasp.org/www-project-agent-memory-guard/); the PDF text was not extractable here).

**F17. The structural defense: untrusted input never reaches a decision.** Beurer-Kellner et al., "Design Patterns for Securing LLM Agents against Prompt Injections", [arXiv:2506.08837](https://arxiv.org/abs/2506.08837): once an agent has read untrusted input, "it must be constrained so that it is impossible for that input to trigger any consequential actions" (section 3). Relevant patterns: Dual LLM (a quarantined reader with no tools), Plan-Then-Execute, Context-Minimization. Willison, ["The lethal trifecta", 2025-06-16](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/): private data, untrusted content and outbound communication together are exploitable, and a filter that catches 95% is "very much a failing grade". A playbook read by every skill is a durable instruction channel, so writing to it is the consequential action.

**F18. Privacy: memory is an extraction target.** MEXTRA, Wang et al., ACL 2025, [arXiv:2502.13172](https://arxiv.org/abs/2502.13172): black-box prompts extract private user-agent interactions stored in agent memory. Codex redacts secrets from generated memories and still says to review them (F8); Anthropic says to strip sensitive data before writing (F10). Copilot keeps "direct user quotes" only in per-user preferences, not in repository facts (F9).

### Measuring improvement

**F19. What studies and vendors measure.** Benchmarks measure success rate on fixed task sets over repeated trials (F1 to F6), plus steps per success (AWM). Copilot used an online A/B test on PR merge rate and positive reactions to review comments, with large n (F9). SWE-Bench-CL, [arXiv:2507.00014](https://arxiv.org/abs/2507.00014), orders SWE-bench Verified issues chronologically per repository and proposes forward transfer, backward transfer and forgetting, comparing memory-on and memory-off agents; the abstract reports no results yet.

**F20. Confounds.** Perception: in METR's RCT ([arXiv:2507.09089](https://arxiv.org/abs/2507.09089), 16 developers, 246 tasks randomized per task), developers forecast 24% faster, believed 20% faster afterwards, and were measured 19% slower. Self-report is not a metric. Model and serving changes: Anthropic's [postmortem](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues) (2025-09-17) describes three infrastructure bugs that degraded quality from early August to mid September 2025, and "The evaluations we ran simply didn't capture the degradation users were reporting". Cost: instructions raise steps and tokens even when success does not change (F14), so tokens and wall time must be read next to success. Task mix: each change differs, and factory tracks (small, standard, critical) differ by design.

## Proposed rules for factory-retro

P1 to P10 are the entry contract and lifecycle; M1 to M6 are the measurement protocol.

**P1. Environment fix first, playbook entry last.** For each lesson, take the first form that holds: a check that fails (test, linter rule through `linter.propose`, hook, CI step), a navigation pointer (a path in an existing doc or a path-scoped rule), a review rule for factory-review, and only then a playbook entry. Grounds: hooks are deterministic and text is advisory (F7); code skills outlasted prose (F3); context files cost about 20% more and rarely raised success (F14). An entry that keeps being violated (P5) is promoted to a check, not reworded.

**P2. An entry is one line of rule plus fixed fields.** Per-repo file `.factory/system/playbook.md`, committed:

```markdown
- PB-07 [scope: src/billing/**] Use Money.of(), never float arithmetic, for amounts.
  why: two slices rounded totals with float (review finding, then a failing test)
  evidence: checkout-retry/slices/02/review.md#F3; refund-flow/slices/01/review.md#F1
  cites: src/billing/money.ts:Money.of
  seen: 2 (first 2026-09-30, last 2026-10-11)  held: 1  violated: 0  idle: 0
  status: active  approved: 2026-10-11
```

- The rule is imperative and checkable, in retro's own words, never pasted session text.
- `evidence` points to factory files or Pond message IDs, never quotes them.
- `cites` names the code it applies to, checked at every retro (P6).
- `scope` is a path glob or `all`.
- The counters are only changed by retro.

**P3. Admission needs an external signal, seen twice.** A failure counts only from a signal the agent could not produce about itself: a red check, a review finding the user accepted, a user correction, a revert, or a reopened slice. The agent's own "done" or self-review does not count (F1, F6, F11). One occurrence makes a `candidate`, kept in retro's ledger and not loaded by skills. Two occurrences in two different changes make it eligible for `active` (F7, F9, F13). Exception: one occurrence that touched money, auth, secrets or data loss may go active at once if the user approves.

**P4. No-op test before activation.** Retro drops a candidate when the base agent already behaves correctly: the evidence shows the failure only under a cause that is gone (a removed file, an older model), or a later change in the same scope did the right thing without the entry. "Would removing this cause mistakes?" (F7). Restating the language default or the existing docs is also a drop (F14).

**P5. Counters drive demotion.**
- `held`: a change in scope where the entry applied and no matching failure occurred.
- `violated`: the failure recurred with the entry loaded. Two violations: convert to a check (P1) or retire; the text does not work.
- `idle`: changes in scope where the entry never applied. After 5 idle changes, or 90 days without `held`, retro proposes retiring it. Copilot uses 28 days and Anthropic recommends expiring unused memory (F9, F10); the factory sees a few changes a week, so the window is longer.
- Money and security entries never retire on idleness, matching `principles.md`.

**P6. Citations are validated every run.** Before loading or editing, retro checks each `cites` path and symbol on the current branch. If one is missing, the entry is marked `stale` and proposed for edit or retirement (F9, F15). Retro also flags two active entries with overlapping scope that contradict each other (F7).

**P7. Delta edits only, with a hard cap.** Retro proposes `add`, `edit`, `retire` by ID and writes them with plain text edits, never by regenerating the file (F12). Active entries cap at 25, and the file at about 150 lines including fields. Adding past the cap requires retiring the entry with the oldest `held`. Grounds: vendor ceilings of 200 lines (Claude Code), 32 KiB (Codex), 500 lines (Cursor) apply to the whole instruction set, and the playbook sits on top of CLAUDE.md and the factory's own skill text (F7 to F9). Skills load only entries whose scope matches the slice's files.

**P8. The user approves every delta.** Same flow as reconcile's confirmation step: retro shows each proposed add, edit, retire and environment fix with its evidence, and writes only what the user confirms. Repository entries come only from changes in that repository (Copilot's write-access rule, F9). Suggest-then-approve is also Devin's model (F9).

**P9. Per-repo vs global.** Repo-specific facts live in `.factory/system/playbook.md`. A lesson reaches the kit (`principles.md`, a language pack linter rule, a lens rubric) only when the same lesson is active in at least two repositories and seen in three changes or more, matching reconcile's threshold of three. Personal working preferences go to the user's own CLAUDE.md, never a repository file (F9: Copilot separates them). Retro never writes Claude Code auto memory; it is machine-local (F7).

**P10. Session content is data; the playbook is an instruction channel.**
- **Quarantined reader.** The pass that reads transcripts has no write tools. It returns structured candidates whose fields come from a fixed set (signal type, file path, finding ID, message ID, one-sentence failure description). Retro drafts the rule text itself from those fields (F17: Dual LLM, Plan-Then-Execute).
- **Allowed sources.** Retro learns from user messages, review findings, check exit codes, diffs and gate documents. Tool results (web pages, issue bodies, logs, dependency files, fetched docs) can corroborate, never originate, an entry. MINJA shows memories can be planted through ordinary inputs, and detectors fail (F16).
- **Forbidden content.** An entry may not grant permissions, weaken or skip a check or review, name a URL or host to contact, touch credentials, or change gate rules. A candidate that would do so is shown to the user as a suspicious item with its source, not drafted.
- **Secret and personal-data scan.** Drafted entries pass factory-security's gitleaks line, and retro rejects any email address, person's name, customer identifier or home-directory path before showing them (F10, F18).
- **Git as the rollback.** The playbook is committed, so every entry has an author, a date and a revert (OWASP's snapshot and rollback, F16).

**M1. Record per slice, from files and Pond, no new telemetry:** outcome (signed off, reopened, sent back to interface), review rounds, review findings by severity, red-check reruns during build, user corrections in the build and review sessions, tokens and wall time. Tag each record with model ID, Claude Code version, kit commit and track.

**M2. The primary signal is per-entry recurrence.** For each active entry, count matching failures in its scope before and after activation (its `violated` vs the pre-activation `seen` rate). This is the cheapest test with a direct causal story, and it needs no comparison across changes.

**M3. Trend only within strata.** Compare medians per track, over the last 10 changes vs the 10 before, and only when both windows share a model. Mark the window broken on any model or Claude Code major update (F20).

**M4. Read cost next to success.** An entry that adds steps or tokens without reducing recurrence is a no-op with a price (F14), and goes to P4.

**M5. No self-report.** "It felt faster" is not evidence (F20). Retro reports counts and says "no measurable change at n=X" when the windows are too small.

**M6. Occasional ablation when it matters.** For an entry the user doubts, run the next comparable slice's build in a worktree without the entry and compare review findings. This is optional and manual; the factory has too few changes for A/B testing (Copilot's design, F9, needs volume).

## Limits of this lane

- Every quantitative result comes from benchmarks (web, household, QA, SWE-bench) or from one vendor A/B test. No study measures a per-repository lesson file across weeks of real feature work. The thresholds in P3, P5 and P7 are judgment grounded in vendor defaults and the factory's existing threshold of three, not measured optima.
- The DGM self-modification paper ([arXiv:2505.22954](https://arxiv.org/abs/2505.22954): SWE-bench 20.0% to 50.0%) was read but not used: it changes the agent's code, not a memory file. Its objective-hacking appendix could not be read here.
- OWASP's ASI06 text was not extractable from the PDF without installing a tool; its mitigations are cited only from secondary sources.
- The Cursor rules page does not document a memories feature; Cursor's behavior there is unverified.
- No transcripts of the user's own sessions were read in this lane.
