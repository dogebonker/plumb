# Reusable workflow: route the work, answer facts, one Goldfish

Status: draft, not approved. Q1 to Q5 answered 2026-10-25 (Q4 replaces Q2). Revised 2026-10-25
after a fresh-context review (findings folded in below), and again after P0 (D10, P3a). P0 done
([benchmark-time-2026-10-25.md](benchmark-time-2026-10-25.md)). Next: P1.

**We're making:** one Plumb workflow to run on every project. One command reads the request and
the repository, picks the lightest path that still holds, asks only what nobody but the user can
answer, and has one zero-context reader check the plan before approval.

**Terms used here:**

- conductor: the session running a Plumb skill, which holds the chat.
- Goldfish: a fresh agent with no chat history that reads only files. The idea comes from EGM,
  Google's Elephant-Goldfish Model plugin (github.com/google/elephant-goldfish-model).
- pstack: Cursor's plugin (github.com/cursor/plugins, `pstack/`), whose `poteto-mode` skill routes
  each request to a playbook.
- SYS rows, ADR inventory, Covers check: as defined in `skills/plumb-shared/adr.md` and
  `skills/plumb-slices/SKILL.md`.
- the brief: the `task:` line in `status.yaml` plus the user's recorded round-1 answers.

**Already decided (2026-10-25, in chat):**

- Keep the question format of `skills/plumb-shared/gates.md`, "Explain questions and decisions"
  (recap, scenario, A/B with a pick and its drawback, reply cue). This plan changes which questions
  are asked, not how they are written.
- Add the Goldfish from EGM, and borrow three detections from pstack: work-type routing, fact vs
  preference, and risk and size.
- Q1, Q3 and Q4 below (Q4 replaced Q2).

**The constraint:** in the 2026-10-19 benchmark
([real-pr-benchmark-2026-10-19.md](real-pr-benchmark-2026-10-19.md)) Factory accepted 9/20 tasks,
against 14/20 for bare and for a good CLAUDE.md. Blind review accepted 12/20 of Factory's work, so
quality was close. Delivery lost: all nine timeouts were Factory, its median was 1,800.1 s against
377.2 to 419.2 s, and its observed token lower bound was over twice either control. Each change
below must cut time or questions. The one change that adds a model call (D5) says so and carries
its own stop condition.

**What P0 found:** the critical track holds 8 of Factory's 9 timeouts and 2 of 9 accepted, against
5 of 9 for each control; its time is 66% planning. On the other 11 tasks Factory accepted 10, one
more than each control, at six to seven times their median time. D10 targets the first; D1 to D5
target the second.

## Before starting

Done: the decision 53 to 55 work landed in `2ed9925`, and the rename to Plumb is decision 56. The
recovery evaluation ([recovery-evaluation-2026-10-20.md](recovery-evaluation-2026-10-20.md)) is
still in progress. P5 runs after it.

## What we borrow, and from where

| Source | Idea | Where it lands |
| --- | --- | --- |
| pstack `poteto-mode/SKILL.md`, Playbooks | Match the task to a playbook before any work | D1 |
| pstack `poteto-mode/SKILL.md`, Non-negotiables | Anything observable by running something is not the human's to answer | D4 |
| EGM `agents/comprehension.md`, `agents/implementation_readiness.md` | Naive reader flags assumed knowledge, Tech Lead flags choices left to the implementer | D5 checks 1 and 2 |
| EGM `resources/document_standards/*.md` | Each standard is one pass bar phrased as "a fresh session can do X on the first attempt" | D6 |
| EGM `skills/egm_resolve/SKILL.md` | The author, who has the memory, marks each Goldfish finding CONTEST (with evidence) or FIX | D7 |
| EGM `docs/designs/review.md`, step 8 | A second zoom-out pass removes defensive bloat that review fixes added | D7 rule 3 |
| EGM `agents/codebase_details.md` | Cross-check every cited path and symbol against live source | D8, scripted |
| EGM `agents/zoom_out.md` and `zoom-out-standard.md` section 0 | Stop the review at once when the objective is unclear | D5 ordering |
| EGM `docs/claude.md`, Reviewer isolation | Fresh spawn, never a fork or resume, read-only tools | D9 |

Considered and rejected:

- EGM's five-stage review pipeline. Five sequential agent stages is the overhead that lost the
  benchmark.
- EGM brainstorm's six-lens Goldfish swarm on the raw concept, before questions. It adds a call
  before discovery. Revisit only if P3 shows the Goldfish catching misunderstandings that started
  in discovery.
- EGM's artifact-first rule (long content in a file, two or three points in chat). It conflicts with
  gates.md's rule that a question never makes the user open a document.
- EGM bootstrap and drift report. Decision 47 already covers drift, and per-directory contracts are
  separate work.
- EGM's `test_scenarios.yaml` regex assertions (they match almost any reply), pstack's per-role
  model routing (decision 53 pins Opus 5.5), and pstack's other playbooks.

## Decisions

- D1. **Triage routes by work type, after the critical check and before the track.** The critical
  criteria of decision 6 (`docs/DECISIONS.md:91`, `skills/plumb-triage/SKILL.md:48`) apply
  first: money, a change to existing auth, or a migration of stored data is critical whatever the
  work type. Otherwise:

  | Work type | Signal | Route |
  | --- | --- | --- |
  | question | asks how, why or whether, names no change | read-only answer with `file:line` citations, no change folder |
  | trivial | today's trivial row (`skills/plumb-triage/SKILL.md:45`) | do it in this session (D2) |
  | bug | reports wrong behavior against an expected one | track small (Q1), slice 01's RED test reproduces the report |
  | refactor | behavior-preserving restructure | track small, slice 01 proves the existing tests stay green, plus the layout check when the repository has one |
  | feature | new or changed behavior | today's track rules |

  The recap's first line names the route and one sentence of evidence. A reply naming another route
  overrides it (Q3). Decision 57 records this as amending decision 6's track selection, not its
  critical criteria.
- D2. **Trivial does the work.** Today triage tells the user to hand a trivial task to an agent and
  stops (`skills/plumb-triage/SKILL.md:45`). Instead, on a branch with no unreconciled change,
  after triage's clean-tree check (`:74`), the session makes the edit, runs the full test and lint
  commands, and reports the diff without committing. On a branch with an active change, the hook
  (`hooks/plumb_gate.py:555-571`) gates the edit, so triage says so and stops.
  `skills/plumb-ci/SKILL.md:69` relies on the stopping behavior and moves in the same commit.
- D3. **Size rules may be tuned on the old 20 tasks, because P5 scores new ones (Q4).** P0 shows
  which 2026-10-19 tasks triage put on a heavier track than the work needed. P1 corrects the track
  wording, and may set explicit size thresholds, from that evidence. The decision entry records
  each threshold with the P0 rows behind it. The old 20 tasks are never used to score the result.
  P0 found none: every critical task met decision 6's money criteria, and no small or standard
  task looked over-tracked. P1 sets no thresholds.
- D4. **Answer facts before asking.** Before a question enters any pre-build batch, classify it:
  - repository fact: answer from code, config or git history with a `file:line` citation, or from
    Pond with a session id
  - runtime fact: answer with a bounded probe (a command, an existing test, or a script in a temp
    directory, never a source edit), at most three per round and two minutes each
  - preference: product, scope, taste or risk acceptance that no probe settles. Only these are asked.

  Answered facts go into the recap as **Current — observed** with their evidence. A probe that
  fails or times out becomes a preference question that carries what it showed. This replaces the
  one-experiment rule in `skills/plumb-plan/SKILL.md` step 2 (line 25). In triage, the "What I
  found" table and its rule already exist (`:54`). The change is the ask list (`:60` onward): the
  three commands move into the table. Slug and mode are defaults, shown once and correctable, and
  not asked. Money stays a confirmation, as `:63` requires.
- D5. **One Goldfish reads the plan before approval, as an added call.** On track standard,
  after `/plumb-plan` step 5 (line budgets) and before step 6, the conductor writes the approval
  message to `<change>/approval-draft.md` and dispatches one Goldfish. This adds one Opus call where
  today's conformance read adds none (`skills/plumb-plan/SKILL.md:65`, `adr.md:40`). One prompt,
  in this order:
  1. Restate in at most five lines what will be built and what the user tries first. If it cannot
     say what is being built and why, it stops here and reports that alone (EGM zoom-out, section 0).
  2. List every point where it had to guess a term, a rule, or a design choice an implementer would
     have to make, judged against the pass bars in D6.
  3. Today's conformance pass against the scripted ADR and SYS inventory, with its limit of three
     conflict cards (`adr.md:40`).

  At most eight findings in total, the three cards included, each anchored to a document line. It
  returns its report as text, and the conductor writes `<tmp>/adr-conflicts.json` from check 3, as
  `adr.md:42` requires. `approval-draft.md` stays change-local evidence, outside the gate hashes.
  Small track keeps its scripted Covers check. Critical keeps its panel, unchanged.
- D6. **One pass bar per document, phrased as a fresh-session test.** From EGM's standards, the
  Goldfish judges each draft by one line:
  - `01-product.md`: a fresh session can say what the user gets, what is out of scope, and why each
    rejected alternative was rejected (feature-spec standard, Alternatives Rule).
  - `02-architecture.md`: it solves the stated problem the simplest way and reuses what the
    repository already has (zoom-out standard).
  - `03-interface.md` and `04-slices.md`: a fresh session can build each slice on the first attempt
    without making a design choice (implementation-readiness standard, Zero-Decision Rule).
- D7. **The conductor resolves findings, and fixes cannot grow the plan.** Following EGM
  `egm_resolve`:
  1. Each finding is marked FIX or CONTEST. CONTEST needs evidence (`file:line` or a quoted
     decision). The approval message lists contested findings in one line each, so the user can
     overrule them.
  2. A finding that needs a user answer becomes an Open question in the same approval message.
     There is no second approval round.
  3. A fix may clarify, cite or cut. A fix that adds a requirement, a module or a defensive path
     becomes an Open question instead (EGM step 8: review fixes breed bloat).
  4. After fixes, the scripted inventory reruns, and the conductor rereads only the changed lines
     against it, reusing unchanged evidence as `plumb-plan:65` already says. No second Goldfish
     runs. Line budgets are checked again with `wc -l`.
- D8. **Cited paths are checked by script, not by a model.** Before the Goldfish runs, every
  repository path and `path:line` cited in the four drafts must resolve at `change_base_commit`
  (EGM's Codebase Auditor, scripted). A miss is fixed or removed before dispatch. Symbol meaning
  stays with the Goldfish (check 2).
- D9. **Goldfish isolation.** A fresh agent spawn, never a fork or a resume. Its prompt holds file
  paths only: the four drafts, `approval-draft.md`, `research.md` when present, the inventory
  output, and read access to the repository. No chat, no conductor reasoning, no write tools. It
  keeps the repository's CLAUDE.md or AGENTS.md, because the question is whether a fresh session
  could continue from the files, and a fresh session loads those. No agent definition and no
  `plumb-init` change. It runs on Opus 5.5 (decision 53).
- D10. **Critical plans in one pass too (Q5).** On track critical in interactive mode, `/plumb-plan`
  runs instead of the four gate skills one at a time. What critical keeps, inside that one pass:
  - round 1 adds one topic, "What must never happen?": for money, amounts, rounding, a movement
    lost or made twice, and limits; for auth, who gains or loses access; for a migration, what must
    survive and how to roll back
  - `02-architecture.md` holds at least one NFR budget and points Threats at the threat model
    (`skills/plumb-architecture/SKILL.md:107-108`)
  - the threat model is drafted in the same pass, from `/plumb-security threat-model` step 2, to
    `<change>/threat-model-draft.md`
  - `03-interface.md` keeps its compile check, Cost lines and Decisions
  - the money challenge panel and the fresh conformance read (`plumb-interface:75`) run as bounded
    agents in parallel once the drafts exist; their cards go into the one approval message instead
    of separate rounds

  One approval approves the four gates and the threat model: it is written to
  `.plumb/system/threat-model.md` and `threat_model_approved` records its hash, as gates.md
  requires. Headless critical keeps its per-gate pull requests, and review keeps the Money
  reviewer. Evidence: on the 2026-10-19 critical tasks the architecture and interface gate agents
  alone ran 459 to 1,288 s, and three tasks never reached build.

## Phases (one commit each)

### P0. `docs(research): measure where Factory's benchmark time went` (done)

Result: [benchmark-time-2026-10-25.md](benchmark-time-2026-10-25.md). All 20 transcripts match the
report within 1%. Planning is 46.7% of Factory's time, so the gate passes; the critical track holds
8 of the 9 timeouts.

The raw run directory was deleted (`real-pr-benchmark-2026-10-19.md:88-91`). The native Claude
Code transcripts of 20 Factory-arm sessions remain under
`~/.claude/projects/*pr-benchmark-actors-azzaa964-*-factory-work/` (dated 2026-10-18).

1. Confirm they are the scored run: each task's elapsed time from the transcript timestamps must
   match the report's per-task execution time (`:108-169`) within 5%. If they match only the
   excluded pilot, stop and report.
2. From the transcripts, write one row per task: the track triage picked, the route D1 would pick,
   seconds per skill invocation, question and resume turns, and the skill running when a timeout
   hit. Add one summary line per skill.

Gate: if planning and questions take under a quarter of Factory's time, D3 and D4 cannot close
the gap on their own. Stop and report the dominant stage before P1.

### P1. `feat(triage): route by work type and do trivial work in place`

Files: `skills/plumb-triage/SKILL.md` (critical check first, routing step, trivial row, recap's
first line, any track wording P0 shows misapplied), `skills/plumb-ci/SKILL.md:69`, `README.md`
(track row), `docs/DECISIONS.md` (decision 57, amending decision 6's track selection).

Proof: five illustrative requests on one fixture from `evals/cases/`, one per route, plus one money
bug. Each lands on the expected route, and the money bug lands on critical. Record the requests and
routes in decision 57.

### P2. `feat(gates): answer facts before asking`

Files: `skills/plumb-shared/gates.md` (D4 classification and probe budget),
`skills/plumb-plan/SKILL.md` steps 2 and 3, `skills/plumb-triage/SKILL.md` ask list,
`docs/DECISIONS.md` (decision 57).

Proof: on the same fixture and one fixed brief, count questions asked before and after. None may
ask a detected command, module, BDD state or committed mode. Record probe seconds separately.

### P3a. `feat(plan): plan the critical track in one pass`

Files: `skills/plumb-plan/SKILL.md` (track critical: the D10 topic, drafts, parallel panel and
conformance read, one approval covering the threat model), `skills/plumb-triage/SKILL.md:48`
(critical's "What runs"), `skills/plumb-security/SKILL.md` (threat-model step 2 callable from
`/plumb-plan`), `skills/plumb-shared/gates.md` (critical dispatch at `:280`), the critical lines of
`skills/plumb-architecture/SKILL.md` and `skills/plumb-interface/SKILL.md`, `docs/DECISIONS.md`
(decision 58).

Proof: the hook test suite still passes with one critical change approved in a single commit
(four gate hashes plus `threat_model_approved`). One `/plumb-plan` run on a money fixture from
`evals/cases/` reaches build with one approval message; record its planning seconds against P0's
critical planning median.

### P3b. `feat(plan): one Goldfish reads the plan before approval`

Files: `skills/plumb-plan/SKILL.md` (steps 4 to 6: D5 to D9), `skills/plumb-shared/adr.md`
(conformance runs inside the Goldfish, conductor rereads changed lines), a path-check script in
`kit/` if none exists (D8), `docs/DECISIONS.md` (decision 59, superseding decision 45's Cost line
and the "no model call" sentence at `plumb-plan:65`).

Proof:

- Run `/plumb-plan` on a fixture brief with one planted undefined term, one design choice left
  open and one dead path. The script catches the path. The Goldfish reports the other two, and the
  approval message carries them.
- The Goldfish transcript's first message holds only paths and instructions (EGM's isolation test,
  checked by hand).
- Record the Goldfish's tokens and seconds.

Stop condition: across the P3 fixture and the first two real standard changes, if the Goldfish
raises nothing the conductor kept as FIX, remove it and restore the conductor read.

### P4. `docs: describe the routed workflow`

Files: `README.md` (one paragraph), `CHANGELOG.md`, `skills/README.md` if it lists triage behavior.

Proof: every link in the changed files resolves.

### P5. `docs(research): rerun the real-PR benchmark with the routed workflow`

A paid run on 20 new tasks with all three arms (Q4): bare, the same frozen CLAUDE.md, and the
routed Plumb (still the benchmark's `factory` arm).

1. Before P0's results are read, select 20 new merged PRs with `evals/pr_corpus.py`, using the
   2026-10-19 selection protocol (`evals/REAL_PR_BENCHMARK.md`). None may be one of the old 20.
   Commit the task list before any arm runs.
2. Run all three arms with the same pinned CLI, model, guards and blind rubric.

The protocol selects features, so only D4, D5 and D10 are exercised. The bug, refactor and question
routes need real use.

Predeclared targets: at most one Plumb timeout, Plumb accepted ≥ the better control's count,
and Plumb median time ≤ 2× the CLAUDE.md arm's median on the same new tasks. The benchmark's synthetic operator answers instantly (`evals/REAL_PR_BENCHMARK.md:72`), so
report probe time and Goldfish time as their own lines. Report the result even when it misses.

## Non-goals

- Perf, hillclimb or investigation playbooks with their own steps.
- Changing the question format, the four gates, approval hashes or headless approvals. D10
  changes how many messages approve them on critical, not what is approved.
- A Goldfish on track critical, on handoffs, or on review and acceptance (acceptance already uses a
  fresh agent that does not read code).
- A new `/factory` entry skill (A1).

## Answered questions (2026-10-25)

- Q1. **A bug skips the planning gates.** Track small, slice 01's test reproduces the report. Money,
  auth and migration bugs stay critical (D1). Accepted drawback: a bug that is really a missing
  feature gets no product gate until review sends it back.
- Q2. Replaced by Q4. (Was: rerun only the Factory arm on the old 20 tasks against the frozen
  controls.)
- Q3. **Triage states the route and continues.** A reply naming another route overrides it.
  Accepted drawback: a wrong route costs a send-back.

- Q4. **P5 runs all three arms on 20 new merged PRs.** P0 and D3 may tune on the old 20 tasks,
  and the new tasks score the result. Accepted drawback: roughly twice Q2's cost (the old controls
  cost about $52 to $54 each, Factory at least $127). Rejected: reusing the old 20 tasks with no new
  thresholds, which hides any tuning leak but caps the speedup.

- Q5. **Critical plans in one pass (D10).** Chosen after P0. Accepted drawback: it changes the
  track that guards money, so P3a needs its own review and a money-fixture run. Rejected: keeping
  the plan as written (P1 to P3 reach one of the nine timeouts) and pausing to replan.

## Open questions

None.

## Assumptions

- A1. The entry stays `/plumb-triage`. Rejected: a `/factory` alias, one more skill for a shorter
  name.
- A2. The Goldfish keeps CLAUDE.md and AGENTS.md (D9). Rejected: EGM's `omitClaudeMd: true`
  adapter, which needs agent definitions linked by `plumb-init` and tests a reader with less
  context than any real session has.
- A3. Five illustrative requests plus one money bug are enough proof for P1. Rejected: a routing
  eval suite, which is new test infrastructure for one step.

## Risks

- R1. The transcripts do not match the scored run, or the time went to build and review. P0's
  steps 1 and 2 stop the plan before any skill changes.
- R2. Probes report false facts from a dirty or unbuilt repository. A failed probe becomes a
  preference question carrying its output, never an answer.
- R3. The Goldfish adds time and finds little. P3's stop condition removes it.
- R4. Goldfish false positives, which are likely because it lacks context on purpose. D7's
  CONTEST-with-evidence rule keeps them out of the plan, and the user sees them in one line each.
- R5. One pass on critical misses a money risk that a separate threat-model round would have
  caught. The threat model is still drafted and approved by hash, the money panel still runs, and
  review keeps the Money reviewer; only the number of approval rounds drops.
- R6. Critical still times out in build and review: five of the eight critical timeouts were
  running build or review, after spending 34% to 88% of their time planning. D10 returns that
  planning time to build, but does not shorten build itself. P5 reports the stage at each timeout.
