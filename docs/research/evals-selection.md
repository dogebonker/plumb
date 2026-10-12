# Evals: proving each stage works, and that a change made it better or worse

Research for a factory eval suite at two levels: **stage evals**, which give one skill a fixture repository with a known answer and score that stage, and **end-to-end evals**, which run a small feature through the whole loop and measure it with retro's metrics ([metrics.md](../../skills/factory-retro/metrics.md)) plus escaped defects. Every claim below links the source it was read from on 2026-10-12. Registry versions were checked the same day (npm, PyPI, the GitHub API). As in [layouts-selection.md](layouts-selection.md), a version is recommended only if it was released on or before 2026-09-28, two weeks earlier.

## Summary

- **One runner: Harbor 0.23.0.** It is the only tool found that takes a whole repository as a fixture (a Docker environment), grades with any script (`tests/test.sh` writes `reward.json` with several labeled numbers), runs Claude Code, Codex, Cursor CLI, OpenCode, Gemini CLI and Pi, and injects a skills folder into each one's native location ([Harbor tasks][harbor-tasks], [verifier][harbor-verifier], [skills][harbor-skills], [agent names][harbor-names]). It also runs several trials per task, regrades stored runs without rerunning the agent when the verifier runs separately, and simulates a user ([run a job][harbor-job], [regrade][harbor-regrade], [simulated user][harbor-user]). Apache-2.0, with a release about every two to three weeks in 2026 ([PyPI][harbor-pypi]).
- **`claude plugin eval` is good, and narrow.** It runs Claude Code only and has no custom-code graders ([plugin evals][cc-evals]). The factory's skills are started by explicit `/factory-*` commands, so its main use, checking that a skill triggers on natural wording, matters little here. Skip it unless a Claude-only smoke check is wanted.
- **Most graders can be deterministic.** The factory writes fixed-format files (`status.yaml`, `review.md` finding lines, `acceptance.md` verdict lines, `Pattern:` lines, challenge cards). A grader parses them and compares closed facts: a track, a pattern id, a file path and line range. A model judges only where nothing else can, as Anthropic's grading order says ([Anthropic, develop tests][anthropic-tests]).
- **Plant the faults, hide the answers.** Review and security recall comes from bugs planted at known file and line ranges, plus decoys and clean controls for precision. That is how Qodo's review benchmark matches findings ([Qodo method][qodo-blog]) and how mutation testing works ([Google][google-mut]). Harbor uploads `tests/` only after the agent has run, so hidden tests stay hidden ([verifier][harbor-verifier]).
- **The user is a script.** Gates are answered from an `answers.yaml` through the factory's own headless mode, where replies and approvals already arrive as text ([gates.md, Headless mode](../../skills/factory-shared/gates.md)). A question the script does not expect is answered with the recommended option and logged. Harbor's LLM user is the fallback for long end-to-end runs ([simulated user][harbor-user]).
- **Better or worse is measured against noise.** Run each case several times, report pass^k for regression cases and the mean for capability cases, and compare versions case by case ([Anthropic, statistics][anthropic-stats], [τ-bench][taubench]). Reuse factory-ci's noise floor: a stage's score may move only within the range measured on the unchanged factory ([ci-selection.md](ci-selection.md)).
- **Skills often add nothing, so always run a baseline.** SkillsBench measured +16.6 points on average from curated skills ([SkillsBench][skillsbench]). SWE-Skills-Bench found 39 of 49 software-engineering skills gave zero improvement ([SWE-Skills-Bench][sweskills]). Each change is scored against the previous factory commit on the same cases.
- **A premise to correct:** there is no per-project `.software-factory/` folder. `~/.software-factory/` is the global kit, and per-repository state lives in `<repo>/.factory/` ([README, Memory](../../README.md)). Project cases go in `<repo>/.factory/evals/`.

## Tool comparison

| Tool | Version to pin (released) | License, upkeep | Whole-repo fixtures | Scoring | Harnesses | Cost controls | Verdict |
|---|---|---|---|---|---|---|---|
| **Harbor** (Terminal-Bench's harness) | 0.23.0 (2026-09-12). 0.24.0 (2026-10-05) is too recent ([PyPI][harbor-pypi]) | Apache-2.0, 6,005 stars, pushed 2026-10-11 ([repo][harbor]) | Yes: per-task Dockerfile or compose. Multi-step tasks give each step its own instruction and tests ([tasks][harbor-tasks]) | Any script writes `reward.txt` or a labeled `reward.json`. A separate verifier sandbox is optional ([verifier][harbor-verifier]). An `oracle` agent runs the reference solution ([names][harbor-names]) | claude-code, codex, cursor-cli, opencode, gemini-cli, pi and more. Each declares skills support and ATIF trajectories ([source][harbor-agents]) | Records `cost_usd` and tokens per agent run ([source][harbor-cost]). No spend ceiling found in its docs | **Use.** It covers both levels and all three harnesses |
| **`claude plugin eval`** | Needs Claude Code ≥ 2.1.269 (2026-09-11). Pin 2.1.284 (2026-09-28) ([npm][cc-npm]) | Proprietary, under Anthropic's Commercial Terms ([license][cc-license]) | A `scaffold_script` builds files or a git repo. It is limited to 120 s and runs only with `--scaffold` ([plugin evals][cc-evals]) | `regex`, `tool_used`, `tool_order`, `file_exists`, `llm` (2 of 3 judge votes) and `baseline`. "There are no custom-code graders". 3 runs per arm by default, and a with/without-plugin Δ ([plugin evals][cc-evals]) | Claude Code only | List-price estimate per run, and `--max-cost-usd` ([plugin evals][cc-evals]) | **Skip.** It cannot run a findings matcher, and it covers one harness |
| **skill-creator evals** | No releases. Pin a commit ([repo][skill-creator]) | Apache-2.0 ([license][skill-creator-lic]) | No. Prompts in `evals/evals.json`, run as subagents ([SKILL.md][skill-creator]) | Assertions graded by a grader agent or a script. Mean ± stddev and Δ against no skill or the old skill. Blind A/B comparator ([SKILL.md][skill-creator]) | Claude Code | None | **Borrow the idea** of the old-version baseline and the blind comparator. Not a runner |
| **Inspect** + **inspect_swe** | inspect-ai 0.3.272 (2026-09-28). inspect-swe 0.2.71 (2026-09-17) ([PyPI][inspect-pypi], [PyPI][inspect-swe-pypi]) | MIT ([PyPI][inspect-pypi]). Built by UK AISI and Meridian Labs ([Inspect][inspect]) | Yes: per-sample files and setup, with Docker sandboxes ([sandboxing][inspect-sandbox]) | Python scorers. `Epochs` with `pass_at_{k}`, `at_least_{k}` and `mode` reducers, and clustered standard errors ([metrics][inspect-metrics]) | `claude_code()`, `codex_cli()`, `gemini_cli()`, `opencode()` and others, bridged to Inspect's model API ([inspect_swe][inspect-swe]). No Cursor. Custom skills only through its `skills` option ([claude_code][inspect-swe-cc]) | Time, message, token and cost limits per sample ([limits][inspect-limits]) | **Second choice.** Its statistics are the strongest of the set, but Cursor is missing and it is Python-only |
| **promptfoo** | 0.123.1 (2026-09-18). 0.124.x is too recent ([npm][pf-npm]) | MIT. OpenAI announced its acquisition on 2026-03-09 and said it expects to keep building the open-source offering ([Yahoo Finance][pf-acq]) | Partly: `working_dir`, with `copy_working_dir` for a fresh copy per test ([Claude Agent SDK provider][pf-claude]) | Deterministic asserts (`equals`, `regex`, `javascript`, `python`, `cost`, `latency`) and model-graded ones (`llm-rubric`, `g-eval`) ([asserts][pf-asserts]). `--repeat 3` for variance ([coding agents][pf-coding]) | Claude Agent SDK (with `plugins` and `skills`), Codex SDK, Codex app server, OpenCode SDK ([Claude][pf-claude], [Codex][pf-codex]). Cursor not listed | `max_budget_usd` ([Claude][pf-claude]) | **Skip.** It fits prompt-level checks, and a second tool would duplicate Harbor |
| **SWE-bench / Verified** (a method, not a runner) | `swebench` 5.0.2 (2026-08-18), MIT ([PyPI][swebench-pypi]) | OpenAI stopped reporting Verified in February 2026 over contamination and flawed tests ([Latent Space][latent]) | Yes: Docker image per instance, patch applied, tests run ([guide][swebench-guide]) | Resolved when `FAIL_TO_PASS` tests now pass and `PASS_TO_PASS` tests still pass ([dataset card][swebench-hf]). 500 human-screened instances ([Verified][swebench-verified]) | Patch-based, so any harness | Modal or `sb-cli` in the cloud ([guide][swebench-guide]) | **Borrow** fail-to-pass and pass-to-pass hidden tests for escaped defects |
| **Terminal-Bench 2.0** (a dataset) | `terminal-bench@2.0` through Harbor ([repo][tb2]) | Apache-2.0 ([repo][tb2]) | 89 tasks, each with its own environment, a human-written solution and tests ([paper][tb-paper]) | Binary reward from tests on the final container state ([Harbor][harbor-verifier]) | Harbor's agents | Same as Harbor | **Borrow** the task shape: environment, instruction, oracle solution, hidden tests |
| **OpenAI Evals platform** | Read-only from 2026-10-31, shut down 2026-11-30 ([deprecations][oai-deprecations]) | OpenAI's suggested migration is promptfoo ([deprecations][oai-deprecations]) | n/a | n/a | n/a | n/a | **Exclude** |
| **Community skill-eval tools** (for example aws-samples/sample-agent-skill-eval) | No releases ([repo][aws-skill-eval]) | MIT-0, 26 stars, last push 2026-05-27 ([repo][aws-skill-eval]) | Not checked | With/without-skill functional runs and a trigger mode ([README][aws-skill-eval]) | Clients that follow agentskills.io | Not checked | **Skip.** It is a sample with little upkeep |

Guidance read alongside the tools:
- **Anthropic** defines task, trial, grader, transcript and outcome. It recommends grading outcomes rather than paths and isolating each trial. It suggests 20 to 50 tasks drawn from real failures as a start, and reading transcripts. Its example is that a 75% per-trial rate over 3 trials gives about 42% pass^3 ([Demystifying evals][anthropic-agents]).
- **OpenAI** recommends evaluating early, on every change, logging to mine cases, pass/fail or pairwise judging over scores, and calibrating judges against humans ([best practices][oai-best]).

## Methods

### Planted faults: measuring recall and precision

- **Mutation testing** is the oldest form of a planted fault. Google ran it on code review over 776,740 changelists. Developers marked 82% of the surfaced mutants that got feedback as productive. Suppressing "arid" lines cut the median mutants per change from 820 to 7 ([Petrović et al.][google-mut]).
- **Do mutants stand for real bugs?** Over 357 real faults, mutant detection correlated with real-fault detection, independently of coverage ([Just et al.][just2014]). Use mutants to generate many cheap review cases. Keep a few hand-written bugs too (a race, a missing authorization check), because a single-token mutant misses that class.
- **What counts as a hit.** Qodo's set is 100 real pull requests holding 580 issues, with 1 to 3 functional bugs injected into each. A comment is a hit only when it describes the issue and points at the right file and line. Unmatched comments are false positives ([Qodo method][qodo-blog]). Qodo matches with an LLM judge. The factory can match by path and line range alone, because each finding line carries its path ([metrics.md, M6](../../skills/factory-retro/metrics.md), [retro-selection, RT-6](retro-selection.md)).
- **Security works the same way.** OWASP Benchmark is a runnable app whose planted vulnerabilities are meant to be "actually exploitable". Its scoring references include the Youden index ([OWASP Benchmark][owasp]). Each planted vulnerability gets a weakness class, a path and a line range, and a decoy that looks vulnerable and is not.
- **Precision needs clean code to look at.** Each review or security fixture carries decoys, and the suite carries clean controls: a correct diff where any `block` or `fix` finding is a false positive.
- **A fix proves itself.** Review step 8 already reverts the fix and requires the new test to fail ([factory-review](../../skills/factory-review/SKILL.md)). An eval adds a hidden test per planted bug that must pass after review's fixes, which checks that the finding was fixed and not just reported.

### Deterministic graders, and where a judge is unavoidable

- **Order of preference:** code-based grading first, then a model, with humans to calibrate it ([Anthropic, develop tests][anthropic-tests], [Anthropic, agents][anthropic-agents]).
- **Judge pitfalls:** position, verbosity and self-enhancement bias, and limited reasoning ([Zheng et al.][zheng]). Pairwise or pass/fail judging is more reliable than a score ([OpenAI][oai-best]). Use one judge per dimension and allow "Unknown" ([Anthropic, agents][anthropic-agents]). Use a different model to judge than the one that produced the output ([Anthropic, develop tests][anthropic-tests]). Judge only short texts, and grade long files with regex ([plugin evals][cc-evals]).
- **Closed questions instead of judgments.** "Which track?", "which `Pattern:` id?", "which FR lines say `fail`?", "does any question contain a forbidden word?", "does each block card name a constraint ID that exists?". Each has one right answer and a parser, and no judge is involved.
- **Path checks only where the path is the requirement.** Anthropic warns that step-sequence checks are brittle ([agents][anthropic-agents]). promptfoo's rule is "Assert the path when the path matters" ([coding agents][pf-coding]). Two factory stages are about the path: the research firewall and acceptance's no-reading rule. Both are graded from the trajectory, which Harbor records as ATIF for every harness used here ([source][harbor-agents]).
- **Validate every grader.** It must score 1 on the case's oracle solution and 0 on a run that does nothing (Harbor's `oracle` and `nop` agents, [source][harbor-agents-dir]). A task that scores 0% across many trials is usually broken ([Anthropic, agents][anthropic-agents]).

### Variance: how many trials

- **pass@k** is the chance that at least one of k samples passes. Estimate it as 1 − C(n−c, k)/C(n, k) from n ≥ k samples. The plug-in form 1 − (1 − p̂)^k is biased ([Chen et al.][codex]).
- **pass^k** is the chance that all k trials pass. It measures consistency: gpt-4o's retail pass^8 fell below 25% ([τ-bench][taubench], [Anthropic, agents][anthropic-agents]).
- **Report uncertainty.** Give the mean ± 1.96 × SEM. Cluster standard errors when cases share a fixture, since clustered errors were over three times the naive ones. Compare two versions by paired differences on the same cases, and size the suite with a power analysis ([Anthropic, statistics][anthropic-stats]). Inspect has `stderr(cluster=...)` ([metrics][inspect-metrics]).
- **Default trials:** 3 per case. That is `claude plugin eval`'s default ([plugin evals][cc-evals]) and promptfoo's advice ([coding agents][pf-coding]). Raise it when the measured noise is wider than the change you need to see.
- **Noise floor:** factory-ci splits unchanged history into two random halves 2,000 times and takes the 95th percentile of the gap between their medians ([ci-selection.md](ci-selection.md)). The same procedure over repeated runs of an unchanged factory gives each stage's noise floor.

### Contamination

- Public benchmarks leak into training. OpenAI stopped reporting SWE-bench Verified after models reproduced gold patches verbatim. Its audit of 138 problems found tests too narrow (49) or too wide (26) ([Latent Space on OpenAI's post][latent]). OpenAI's own page returned 403 to this fetch.
- **Defenses:**
  - Fresh items over time ([LiveCodeBench][livecodebench]).
  - Canary strings in every task file, so scrapers can filter them ([BIG-bench][bigbench]).
  - Synthetic fixtures written for this suite, never popular open-source repositories.
  - Mutants placed at a seeded random site on each run, so the planted answer changes between runs.
  - A held-out set in each project's own folder.

### Small and cheap fixtures

- **Size:** start with 20 to 50 tasks from real failures ([Anthropic, agents][anthropic-agents]). The retro already lists real failures: the six-round interface panel, UI review missing on a UI slice, and twelve flat files in `web/src` ([DECISIONS 25, 28](../DECISIONS.md)).
- **Fixtures:** a few hundred lines each, built by a script from a pinned base image. `claude plugin eval` caps scaffolds at 120 s ([plugin evals][cc-evals]).
- **Reuse instead of rerunning:**
  - Regrade stored runs when only a grader changes ([Harbor regrade][harbor-regrade]).
  - Replay recorded mock answers ([plugin evals][cc-evals]).
  - Cache responses ([promptfoo][pf-claude]).
  - Cache Docker layers (SWE-bench's `--cache_level`, [guide][swebench-guide]).
- **Start mid-loop.** A stage case starts from prepared factory files (for example `status.yaml` at "slices approved"), so it pays for one skill run, not the loop before it.

### Human-in-the-loop steps, simulated

- **Scripted answers to `AskUserQuestion`.** The Claude Agent SDK's `canUseTool` callback receives each `AskUserQuestion` call: 1 to 4 questions, each with 2 to 4 options. It returns `answers` keyed by question text, or a free-text `response`. `AskUserQuestion` is not available in subagents ([Agent SDK, user input][sdk-input]). This works for Claude Code only.
- **LLM users.** Harbor pairs a user agent, which holds the instruction and an optional persona file, with the target agent over ACP. Targets are claude-code, gemini-cli, codex and opencode, so not Cursor. The example run takes about 50 minutes ([simulated user][harbor-user]). τ-bench also uses an LLM user, and checks the final database state rather than the dialogue ([τ-bench][taubench]).
- **The factory's own channel.** In headless mode every question is one pull-request comment and the skill stops. The runner passes approvers' replies into the next run's prompt. Approvals are pull-request reviews whose first line is `approve <gate>` or `sign off slice NN` ([gates.md](../../skills/factory-shared/gates.md), [factory_run.py](../../runner/factory_run.py)). This is text in, text out, so it is the same for every harness. A scripted approver only needs to stand in for `gh`.

## Proposed design

### D1. Layout in this repository

```
evals/
  base/Dockerfile            # pinned OS, git, runtimes, the kit at ~/.software-factory, polish, a fake `gh` (D6)
  fixtures/<name>/build.sh   # creates a small repository at a known commit, versioned by name: notes-api@3
  cases/<stage>/<id>/        # one Harbor task each
    task.toml                # timeouts, resources, [verifier] environment_mode = "separate"
    instruction.md           # the /factory-* command, plus scripted replies when the stage needs them
    case.yaml                # D2: planted faults, expected facts, answers, budget
    environment/Dockerfile   # FROM the base image, runs the fixture's build.sh, puts factory state in place
    solution/solve.sh        # oracle: writes the known-good output, to validate the grader
    tests/test.sh            # calls the shared grader, writes /logs/verifier/reward.json
  graders/                   # standard-library Python, one per output format, each with a self-check
  e2e/<id>/                  # multi-step tasks: one step per factory step
  baselines/<harness>-<model>.json   # committed scores and noise floors per factory commit
  results/                   # Harbor job folders, gitignored
```

The shared graders are copied into each case's `tests/`, or baked into a verifier image, because Harbor uploads only `tests/` ([verifier][harbor-verifier]). The `--skill skills` flag passes the factory's own skills, since that flag accepts "a root whose immediate child directories each contain `SKILL.md`" ([Harbor skills][harbor-skills]).

### D2. Case schema

```yaml
id: REV-01
stage: review                 # triage | firewall | interface | red | review | security | acceptance | layout-check | layout-select | e2e
kind: regression              # regression: every trial must pass (pass^k). capability: tracked as a rate
fixture: notes-api@3
start: { gates: approved, slices_done: ["01"], milestone: 2, mode: headless }
run: /factory-review notes-api-archive
answers:                      # the scripted user (D6), matched in order, unmatched ones logged
  - { match: "^Ready for review", reply: "approve slices" }
  - { match: "sign off", reply: "sign off slice 02" }
  - { default: recommended }
planted:                      # known faults. Lines are a range, so a finding one line off still counts
  - { id: B1, path: src/notes/list.ts, lines: [41, 43], kind: off-by-one, hidden_test: tests/hidden/b1.test.ts }
  - { id: B2, path: src/notes/archive.ts, lines: [17, 18], kind: missing-await, hidden_test: tests/hidden/b2.test.ts }
decoys:
  - { id: D1, path: src/notes/query.ts, lines: [9, 9] }   # looks wrong, is right
expect:                       # closed facts the grader checks
  found: [B1, B2]             # each needs a block or fix finding inside its range
  false_positives: 0          # block or fix findings on decoys or outside every range
  hidden_tests_pass: true     # after review's fixes
grader: findings.py
trials: 3
budget: { max_turns: 200, timeout_s: 3600 }
canary: "factory-evals canary 6f1c..."   # in every file of the case
```

`reward.json` carries one number per expected fact (for example `recall`, `false_positives`, `hidden_tests_pass`), plus `pass`: 1 only when all of them hold. Harbor's verifier supports labeled reward files ([verifier][harbor-verifier]).

### D3. Example cases per stage

| ID | Stage | Fixture and planted fault | Expected outcome | Grader |
|---|---|---|---|---|
| TRI-01 | triage | `notes-api` (TypeScript CRUD). Task: "change the log text in `getNote`" | `track_proposed: trivial`, `profile: crud-service` | parse `status.yaml`, `lenses.yaml` |
| TRI-02 | triage | `payouts` (Python, `Decimal` ledger writes in `payout.py`). Task: "add a weekly payout cap" | `track_proposed: critical`. A money signal located in `payout.py`. `profile: domain-core` | parse, path match |
| FW-01 | firewall | `notes-api` with an approved `01-product.md` whose rules use words absent from the code ("tombstone", "grace period") | No forbidden word in `questions.md` or in the sub-agent's prompt. The worktree has no `.factory/changes/`. Every question answered or "not found" | word list against the files and the trajectory |
| IF-01 | interface | Draft `03-interface.md` with one exposed config parameter (cost card), `SYS-C-03` in constraints, and a naming quirk no constraint covers | Every `block`/`fix` card names an anchor that exists. Its `Where` quotes a stub line verbatim. The naming card is a `note`. At most 3 cards per lens | parse `challenges.md` against `constraints.md`, the stubs and the cost card |
| RED-01 | red | Packet whose Tests first says "archiving a note older than 30 days sets `archived_at`" | Every new test fails at the red commit by assertion (not by an import or compile error). Old tests still pass. The oracle implementation turns them green | run tests at the red commit and with `solution/` applied, SWE-bench style ([dataset card][swebench-hf]) |
| RED-02 | red | The same packet plus a negative case ("rejects an empty title") that passes against the stub | The executor lists that test in its report and does not change it ([factory-build](../../skills/factory-build/SKILL.md)) | regex on the report, diff of the test |
| REV-01 | review | Milestone diff with B1 (off-by-one), B2 (missing `await`) and decoy D1 | Both found inside their ranges, 0 false positives, hidden tests pass after the fix commit | `findings.py` |
| REV-02 | review | A correct milestone diff (clean control) | No `block` or `fix` findings | `findings.py` |
| REV-03 | review | A test added by review that only calls the code | A `[factory/example-asserted]` finding ([DECISIONS 26](../DECISIONS.md)) | tag match |
| SEC-01 | security | Small web app with SQL built by concatenation (CWE-89), a path traversal in download (CWE-22), a hardcoded key (CWE-798), and a parameterized-query decoy | Each found with its class, path and line range. Validators pass on `findings.json` ([factory-security](../../skills/factory-security/SKILL.md)). No finding on the decoy | `findings.py` in security mode |
| ACC-01 | acceptance | Running `notes-api`. FR-2's example says `?archived=true` returns only archived notes, but the code returns all notes | `acceptance.md`: FR-1 `pass`, FR-2 `fail` with evidence, FR-3 `pass`. The agent never read `src/`, `tests/` or `.factory/` ([factory-reconcile](../../skills/factory-reconcile/SKILL.md)) | verdict lines, plus a trajectory check for reads |
| LAY-01 | layout check (no model) | For each checker in `kit/layouts/tools.yaml`: a config written from a pattern, plus a new file importing domain → infrastructure | The checker exits non-zero naming that file. The clean variant exits 0 | plain script |
| LAY-02 | layout check | Milestone diff adds `src/utils2.ts`, outside the Layout | Review Phase 1 check 9 reports it ([factory-review](../../skills/factory-review/SKILL.md)) | finding path match |
| SEL-01 | layout selection | `crud-service`, FastAPI, one business area with shared models | `Pattern: layered`, alternative vertical-slice (row L3 of `kit/layouts/index.yaml`) | regex on the `Pattern:` line |
| SEL-02 | layout selection | `domain-core`, "account" means different things in billing and identity | `Pattern: modular-monolith` (L6) | same |
| SEL-03 | layout selection | `legacy`, an existing module | `Pattern: existing` (L1) | same |
| SLC-01 | slices | Approved interface with FR-1 to FR-4 | Every FR covered by a slice. Slice 01 is its own milestone ([DECISIONS 27](../DECISIONS.md)). Allowed files are exact paths that fit the Layout | parse `04-slices.md` |
| E2E-01 | end to end, standard | `notes-api`: "archive notes older than N days". Hidden `FAIL_TO_PASS` and `PASS_TO_PASS` tests ([dataset card][swebench-hf]) | Hidden tests pass. M1 to M8 recorded. Escaped defects = hidden tests failing after reconcile | multi-step task, one step per factory step |
| E2E-02 | end to end, small | Python CLI: "add `--json` output" | Same, on the small track | same |
| E2E-03 | end to end, critical | `payouts`: weekly cap, with hidden tests on rounding and on paying twice for one request | Same, plus the Money reviewer ran | same |
| E2E-04 | end to end, rework | E2E-01 with a scripted send-back at the interface gate | One `sent_back` event, at most one APoSD-only round after it ([DECISIONS 27](../DECISIONS.md)) | `history` events |

### D4. Which stages first, by value and cost

| Rank | Case | Why here | Model runs per trial |
|---|---|---|---|
| 1 | LAY-01 | Free, and it closes a gap decision 29 names: the checkers "were checked against their registries and docs, not run on a real repository" ([DECISIONS 29](../DECISIONS.md)) | 0 |
| 2 | REV-01, REV-02 | Review is where the user's hours went: build and review took about 7 of 13 active hours on the first change ([DECISIONS 27](../DECISIONS.md)). Recall and precision on planted bugs is the stage's core claim | one review: polish's agents plus lens reviewers |
| 3 | RED-01 | Every later check rests on red being real. Decision 26 notes that a red test can fail only because it calls a stub, then pass green with no assertion | one executor |
| 4 | ACC-01 | The only check on the running product. It is new (decision 26) and has never been measured | one acceptance agent |
| 5 | FW-01 | A leak is invisible to the user and biases every architecture fact. Cheap, and graded without a judge | one research sub-agent on the smaller model |
| 6 | TRI-01/02 | Cheap, but the user confirms the track anyway (M8 tracks overrides) | one |
| 7 | SEL-01..03, LAY-02, SLC-01 | Cheap parses. Selection is judgment until a retro calibrates it ([DECISIONS 29](../DECISIONS.md)) | one each |
| 8 | IF-01 | Valuable, but the panel is the costliest stage: 49% of wall clock on the first change ([DECISIONS 25](../DECISIONS.md)) | panel lenses × rounds |
| 9 | SEC-01 | High value, high cost: scanners plus routed hunters | audit |
| 10 | E2E-01..04 | Proves the loop. Run after stage cases are stable | the whole loop |

### D5. Graders, by output

All graders are standard-library Python, each with an `assert`-based self-check like the runner's ([test_factory_run.py](../../runner/test_factory_run.py)).
- `facts.py`: YAML keys and regex lines (track, profile, `Pattern:`, verdict lines, `history` events).
- `findings.py`: parses `[tag] severity path: finding -> outcome` lines and security findings. It matches each to a planted range by path and line, and reports recall, false positives on decoys, and unmatched findings.
- `leak.py`: forbidden words against the questions and the trajectory's prompts and file reads.
- `tests.py`: runs a command at a commit and returns per-test pass or fail, with the failure kind.
- `trajectory.py`: reads ATIF for reads under forbidden paths, questions asked, and tokens per step. This replaces Pond for M1 to M3 inside an eval.

A model judge is used only where no parser can decide, for example "does this challenge card argue for the current design first?". It runs on the short card, with PASS/FAIL criteria, on a model other than the one under test.

### D6. The simulated user

- **Default: headless mode with a fake `gh`.** The runner and the skills call only a few `gh` commands:
  - `gh pr list`, `gh pr view --json reviews,comments`, `gh api .../pulls/N/comments` and `gh api user` ([factory_run.py](../../runner/factory_run.py)).
  - `gh pr comment` and `gh api .../issues/comments/<id>` ([gates.md](../../skills/factory-shared/gates.md)).

  A fake `gh` on `PATH` in the base image serves these from a local JSON file, with a local bare repository as `origin`. Between passes, a driver reads the newest question and posts the scripted reply or approval review from `answers`. The runner runs unchanged, with `--harness` set per harness:
  - `claude -p --setting-sources user --strict-mcp-config` (the runner's default).
  - `codex exec` (local `codex exec --help`, codex-cli 0.162.0).
  - `cursor-agent --print` ([Harbor's integration][harbor-cursor]).

  End-to-end evals run this driver as a Harbor custom agent. A question that matches no rule gets the recommended option and is logged as unexpected. Unexpected questions are a scored output (M1).
- **Stage cases need no driver.** They start in headless mode, run one skill, and stop at its question. Where the stage needs answers mid-step (the interface panel's responses), `instruction.md` appends them the way the runner passes replies.
- **Fallback: Harbor's LLM user** with a persona file that holds the answer sheet ([simulated user][harbor-user]). Use it only for interactive-mode E2E runs. It is non-deterministic and does not cover Cursor.

### D7. Running per harness and model

```bash
harbor run -p evals/cases/review -a claude-code -m anthropic/<model> --skill skills -k 3 -n 4 -o evals/results
harbor run -p evals/cases/review -a codex       -m openai/<model>    --skill skills -k 3 -n 4 -o evals/results
harbor run -p evals/cases/review -a cursor-cli  -m <model>           --skill skills -k 3 -n 4 -o evals/results
```

Flags from Harbor's docs: `-k` attempts, `-n` concurrency, `--skill` ([run a job][harbor-job], [skills][harbor-skills]). Pin the harness version: Harbor's Claude Code integration installs a requested version ([source][harbor-cc]). Pin the model, because a model rollout can otherwise look like a factory regression ([plugin evals][cc-evals]). Record both, with the factory commit, in every result, as retro already does ([metrics.md, The trend](../../skills/factory-retro/metrics.md)).

### D8. Budget per run

No cost figures are given here, because none have been measured. The first baseline run measures them, and they go into `baselines/`.
- **Tier 0, every commit:** LAY-01 and the graders' self-checks. No model.
- **Tier 1, on a skill change:** the cases of the stages the changed files feed, k = 3.
- **Tier 2, before a release or a model or harness change:** every stage case, k = 3, on each harness in use.
- **Tier 3, manual or nightly:** E2E cases, k = 3.

Each trial has turn and time caps in `task.toml`. Harbor records `cost_usd` per trial but has no documented ceiling ([source][harbor-cost]). The driver sums cost after each trial and stops starting new trials past the tier's ceiling, which the user sets from the first measured run. A run cut short is marked partial and left out of trends, as `claude plugin eval` does with `partial: true` ([plugin evals][cc-evals]).

### D9. How results feed decisions

- **A stage score** is the mean over its cases of each case's mean over k trials, the same aggregation as `claude plugin eval` ([plugin evals][cc-evals]). Regression cases must also hold pass^k = 1.
- **Noise floor per stage, harness and model:** repeat Tier 2 on the unchanged factory and apply factory-ci's split-half procedure ([ci-selection.md](ci-selection.md)). Until enough repeats exist, report "no verdict at n=X", as retro and factory-ci do.
- **The rule for a skill, model or harness change:**
  - It is accepted only if no regression case drops below pass^k = 1.
  - No stage's score may fall by more than that stage's noise floor.
  - Compare case by case against the previous factory commit on the same harness and model: paired differences, with standard errors clustered by fixture ([Anthropic, statistics][anthropic-stats]).
  - A gain counts only past the noise floor.
- **Where the numbers go:**
  - A pull request to `skills/` or `kit/` shows the Tier 1 table.
  - A decision in `docs/DECISIONS.md` that claims an improvement cites its eval result, as decisions 25 and 27 cite retro numbers.
  - Retro on real changes stays the ground truth for end-to-end friction. An escaped defect or a retro finding becomes a new regression case, which is Anthropic's advice to build tasks from real failures ([agents][anthropic-agents]).
- **Capability cases graduate** to regression once they pass consistently ([Anthropic, agents][anthropic-agents]).

### D10. A project's own cases

A project keeps cases in `<repo>/.factory/evals/cases/<stage>/<id>/`, in the same task format, with fixtures built from its own code at a pinned commit. The driver merges them with the factory's cases when run from that repository. Their results go to `.factory/evals/baselines/` and stay per repository, as playbook lessons do ([retro-selection, RT-8](retro-selection.md)). The good first project case is a failure retro already found there: its correction, failing check or reverted change becomes the planted fault. Project cases stay out of this repository, which keeps them unpublished, the strongest defense against contamination listed above.

## What this does not cover

- **Nothing here has been run.** The fake `gh`, the driver, the graders and the Harbor base image are proposals. Harbor's multi-step tasks, custom agents and skills injection are read from its docs and source, not tried with the factory's skills.
- **Costs and noise floors are unknown** until the first baseline. With 3 trials and a handful of cases per stage, expect wide floors and many "no verdict" results at first.
- **Pond is absent from evals.** The runner's default harness has no Pond either ([retro-selection](retro-selection.md)). Gates' Pond lookups return nothing in a fixture, so stages that rely on prior sessions are scored without them.
- **Mutants are not every bug.** The coupling study supports mutants as a proxy for real faults, not as a replacement ([Just et al.][just2014]). Hand-written cases remain necessary for races, authorization and design faults.
- **Interface and UI quality** have no closed answer beyond anchors and format. Taste stays with the user, and the UI/UX skill's rendered critique is not covered here.
- **Cross-harness parity:** Harbor maps skills into each harness's native folder ([skills][harbor-skills]). Whether Codex and Cursor follow the factory's skills as Claude Code does is exactly what the suite will measure. It is not assumed.
- **Vendor review benchmarks** (Qodo, and others in search results) are run by the vendors themselves, with matching rules that differ ([Qodo method][qodo-blog]). Their numbers are not used here.
- **OpenAI's SWE-bench post** could not be fetched (HTTP 403). Its claims are taken from Latent Space's write-up ([latent]).

[harbor]: https://github.com/harbor-framework/harbor
[harbor-pypi]: https://pypi.org/project/harbor/#history
[harbor-tasks]: https://docs.harborframework.com/tasks/overview
[harbor-verifier]: https://github.com/harbor-framework/harbor/blob/main/docs-mintlify/tasks/verifier.mdx
[harbor-skills]: https://github.com/harbor-framework/harbor/blob/main/docs-mintlify/jobs/skills.mdx
[harbor-user]: https://github.com/harbor-framework/harbor/blob/main/docs-mintlify/jobs/simulate-a-user.mdx
[harbor-job]: https://github.com/harbor-framework/harbor/blob/main/docs-mintlify/jobs/run-a-job.mdx
[harbor-regrade]: https://github.com/harbor-framework/harbor/blob/main/docs-mintlify/jobs/regrade.mdx
[harbor-agents]: https://github.com/harbor-framework/harbor/blob/main/src/harbor/agents/installed/claude_code.py
[harbor-agents-dir]: https://github.com/harbor-framework/harbor/tree/main/src/harbor/agents
[harbor-names]: https://github.com/harbor-framework/harbor/blob/main/src/harbor/models/agent/name.py
[harbor-cost]: https://github.com/harbor-framework/harbor/blob/main/src/harbor/models/agent/context.py
[harbor-cc]: https://github.com/harbor-framework/harbor/blob/main/src/harbor/agents/installed/claude_code.py
[harbor-cursor]: https://github.com/harbor-framework/harbor/blob/main/src/harbor/agents/installed/cursor_cli.py
[tb2]: https://github.com/laude-institute/terminal-bench-2
[tb-paper]: https://arxiv.org/abs/2601.11868
[cc-evals]: https://code.claude.com/docs/en/plugin-evals
[cc-npm]: https://www.npmjs.com/package/@anthropic-ai/claude-code?activeTab=versions
[cc-license]: https://github.com/anthropics/claude-code/blob/main/LICENSE.md
[skill-creator]: https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
[skill-creator-lic]: https://github.com/anthropics/skills/blob/main/skills/skill-creator/LICENSE.txt
[inspect]: https://inspect.aisi.org.uk/
[inspect-pypi]: https://pypi.org/project/inspect-ai/#history
[inspect-swe-pypi]: https://pypi.org/project/inspect-swe/#history
[inspect-swe]: https://meridianlabs-ai.github.io/inspect_swe/
[inspect-swe-cc]: https://meridianlabs-ai.github.io/inspect_swe/claude_code.html
[inspect-metrics]: https://inspect.aisi.org.uk/metrics.html
[inspect-sandbox]: https://inspect.aisi.org.uk/sandboxing.html
[inspect-limits]: https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/setting-limits.qmd
[pf-npm]: https://www.npmjs.com/package/promptfoo?activeTab=versions
[pf-acq]: https://finance.yahoo.com/news/openai-acquires-promptfoo-secure-ai-174904138.html
[pf-claude]: https://www.promptfoo.dev/docs/providers/claude-agent-sdk/
[pf-codex]: https://www.promptfoo.dev/docs/providers/openai-codex-sdk/
[pf-coding]: https://www.promptfoo.dev/docs/guides/evaluate-coding-agents/
[pf-asserts]: https://www.promptfoo.dev/docs/configuration/expected-outputs/
[swebench-pypi]: https://pypi.org/project/swebench/#history
[swebench-guide]: https://www.swebench.com/SWE-bench/guides/evaluation/
[swebench-hf]: https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified
[swebench-verified]: https://www.swebench.com/verified.html
[latent]: https://www.latent.space/p/swe-bench-dead
[oai-deprecations]: https://developers.openai.com/api/docs/deprecations
[oai-best]: https://developers.openai.com/api/docs/guides/evaluation-best-practices
[aws-skill-eval]: https://github.com/aws-samples/sample-agent-skill-eval
[anthropic-agents]: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
[anthropic-tests]: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
[anthropic-stats]: https://www.anthropic.com/research/statistical-approach-to-model-evals
[sdk-input]: https://code.claude.com/docs/en/agent-sdk/user-input
[taubench]: https://arxiv.org/abs/2406.12045
[codex]: https://ar5iv.labs.arxiv.org/html/2107.03374
[zheng]: https://arxiv.org/abs/2306.05685
[google-mut]: https://ar5iv.labs.arxiv.org/html/2102.11378
[just2014]: https://homes.cs.washington.edu/~mernst/pubs/mutation-effectiveness-fse2014-abstract.html
[qodo-blog]: https://www.qodo.ai/blog/how-we-built-a-real-world-benchmark-for-ai-code-review/
[owasp]: https://owasp.org/www-project-benchmark/
[livecodebench]: https://arxiv.org/abs/2403.07974
[bigbench]: https://github.com/google/BIG-bench/blob/main/README.md
[skillsbench]: https://arxiv.org/abs/2602.12670
[sweskills]: https://arxiv.org/abs/2603.15401
