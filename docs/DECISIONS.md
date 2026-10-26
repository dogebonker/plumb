# Decisions

Every decision that shaped the factory, in the order it was made. Each one says what was decided, why, and what it costs. Superseded decisions stay in the log, marked as such.

| # | Decision | Status |
| --- | --- | --- |
| 1 | Four gates from Dex Horthy's talk, plus a research step | Accepted |
| 2 | Skills plus files, not a platform | Accepted |
| 3 | Decisions in files, recall in Pond | Accepted, amended by 33 |
| 4 | Hard gates tied to a document hash | Accepted |
| 5 | A constraints registry that must map to enforcement | Accepted |
| 6 | Tracks that scale process to risk | Accepted |
| 7 | One handoff packet per slice | Accepted |
| 8 | Design-book lenses, chosen by profile | Accepted |
| 9 | APoSD as the spine of Interface Design | Accepted |
| 10 | A fair challenge panel with calibration | Accepted, amended by 33 |
| 11 | No design-it-twice step | Accepted |
| 12 | Review built on `/polish` | Superseded by 32 |
| 13 | A converging multi-round reviewer | Rejected |
| 14 | Mechanical checks replace two review agents | Accepted |
| 15 | Money pack only where money moves | Accepted |
| 16 | BDD discovery everywhere, Gherkin only where it exists | Accepted |
| 17 | Language packs per module | Accepted |
| 18 | Python pack chosen for maintenance and adoption | Accepted |
| 19 | Prune as a scheduled, approved job | Accepted |
| 20 | Third-party packs vendored and pinned | Accepted |
| 21 | factory-security: Cloudflare method, five scanners, routed knowledge | Accepted |
| 22 | factory-ui-ux: an enforced DESIGN.md, mechanical de-slop, anchored critique | Accepted |
| 23 | factory-ci: its own measurement, a catalog with guards, savings that must beat the noise | Accepted |
| 24 | factory-retro: measured friction, environment fixes first, an evidence-gated playbook per repository | Accepted |
| 25 | The first retro's two fixes: at most three interface panel rounds, and a factory version per change | Accepted |
| 26 | From Factory's talk: acceptance on the running product, flaky tests at triage, tests that assert the example, a smaller model for checked work | Accepted |
| 27 | The tg-mini-app retro: milestone review, an autopilot build loop, fewer questions and commits | Accepted, amended by 30 |
| 28 | A Layout every gate holds: folder trees at architecture, frontend interfaces, exact Allowed files, a layout check; FSD only for a big frontend | Accepted, amended by 29 |
| 29 | A catalog of reference layouts the architecture gate proposes from, with exemplars and pinned checkers | Accepted |
| 30 | A thin orchestrator for the autopilot, and token budgets per step | Accepted |
| 31 | A framework on top of harnesses: evals first, one `.software-factory/` per project, harness adapters, a Slack channel | Accepted (planned) |
| 32 | Review agents owned by factory-review, with a defect rubric and file coverage | Accepted |
| 33 | S14 P1 to P3: `.software-factory/` per project, a framework cache per commit, three principle layers, init and upgrade | Accepted, amended by 34 |
| 34 | Packs per project, in a cache per pinned hash | Accepted |
| 35 | FDA as the strong default for new frontend roots | Accepted |
| 36 | Approved development scope, direct execution and consolidated independent review | Accepted |
| 37 | Bundle pinned book rubrics with every framework and benchmark snapshot | Accepted |
| 38 | An autonomous local implementation–review–repair–acceptance loop | Accepted |
| 39 | Optional feature visual references, adapted to the approved brand | Accepted |

---

## 1. Four gates from Dex Horthy's talk, plus a research step

**Decision.** The loop runs Product, Architecture, Program Design (here called Interface Design) and Vertical Slices, each with an approval gate. A research step sits between Product and Architecture.

**Why.** The talk's argument holds up in practice: agents optimize for passing tests, and design quality only shows up months later, so the cheapest place to steer is before code exists. The research step comes from Dex's later workflow: a sub-agent that only sees neutral questions, never the task, reports facts about the codebase without bias toward a solution. Architecture then gets designed against the real system, not an imagined one.

**Cost.** Up-front time per feature. Tracks (decision 6) keep that time off small changes.

## 2. Skills plus files, not a platform

**Decision.** The factory is a set of skills in the open Agent Skills format, plus markdown files. No server, no database, no UI.

**Why.** The same loop must run across every repository and stack, on a laptop or a server, in whichever agent harness is best that month. Skills and files are the most portable thing there is.

**Cost.** No dashboard. Status lives in `status.yaml` files, which is fine for one person and a small team.

## 3. Decisions in files, recall in Pond

**Decision.** Approved decisions are markdown in git: the global kit in `~/.software-factory/`, the project's `.factory/system/`, and one folder per change. Memory is [Pond](https://github.com/tenequm/pond): every agent session, stored losslessly in one shared store and queried by search, SQL or MCP. Lessons and calibration are computed at reconcile from the factory's own files, found across repositories through Pond, not maintained by hand.

**Why.** Decisions need to be read, diffed and reviewed in pull requests like code, so they stay in files. Recall is a different job. Hand-written lesson files only hold what someone remembered to write down, and grep over them misses what was said in a review three repositories ago. Pond keeps the full record across every harness and machine, and its SQL makes counts like "how often was this lens rule overruled" a query instead of a file to keep in sync. It also leaves agent beliefs inspectable: everything in it is a transcript, not an opaque vector memory.

**Cost.** One more tool on every machine and server, and a shared store to run. Pond's answers are history, not decisions: anything that should bind future work is promoted into a file and reviewed.

## 4. Hard gates tied to a document hash

**Decision.** Approval is a token stored with the hash of the gate document. Editing the document after approval reverts that gate and everything downstream. A hook blocks source edits until the slice plan is approved.

**Why.** Every surveyed tool treats approval as a convention: the plan exists, so the agent moves on. That is exactly how a plan that only looks finished turns into code nobody agreed to.

**Cost.** Friction. Small and trivial tracks skip most gates.

## 5. A constraints registry that must map to enforcement

**Decision.** Every functional requirement, NFR and constraint gets an ID in one `constraints.md`. By the Interface Design gate, every ID maps to a test, a lint rule, a monitor, or an explicit "human-verified". An unmapped ID blocks the gate.

**Why.** Think of building a house. Functional requirements are the rooms. NFRs are how warm and quiet it is. Constraints are the plot, the budget and the zoning law, and they rule options out before anyone draws. Most tools only capture rooms. A requirement without enforcement is a wish.

**Cost.** Writing fit criteria takes thought. Domain NFR catalogs in `~/.software-factory/` make most of them a copy, not a blank page.

## 6. Tracks that scale process to risk

**Decision.** Trivial, small, standard and critical tracks. Anything that moves money, touches auth or migrates data is critical.

**Why.** The heaviest frameworks lose people because a three-line change produces hundreds of lines of planning. Process should match the cost of being wrong.

**Cost.** Triage can misjudge. You can always override the track.

## 7. One handoff packet per slice

**Decision.** Each slice gets a packet: goal, requirement IDs with fit criteria, frozen signatures, allowed files, tests that must fail first, verify commands, and only the smallest versions of the relevant rules. The executor sees the packet and research excerpts, nothing else.

**Why.** Fresh context per slice keeps the executor sharp. The packet is also the portability boundary: any harness, local or remote, can build from it.

**Cost.** Packets must be complete. A missing fact shows up as an executor question, which is cheap to fix.

## 8. Design-book lenses, chosen by profile

**Decision.** Classic design books, distilled as agent rules, act as lenses. A project profile picks a small coherent set, at most two active per step.

**Why.** These books encode decades of hard-won judgment, which is exactly what agents lack. But some of them disagree (rich domain models versus transaction scripts, for example), and loading all of them at once gives the agent conflicting pressure. A profile makes the choice once, per project, as an ADR.

**Cost.** Picking a profile is a real decision. Triage proposes one; you confirm.

## 9. APoSD as the spine of Interface Design

**Decision.** *A Philosophy of Software Design* arbitrates at interface level. You design the interfaces; agents implement behind them.

**Why.** Interfaces are the decisions that are cheap to change before code and expensive after. Owning them is the highest-leverage use of human attention, and deep modules with small interfaces are what keep a codebase changeable after many agent-written slices. Inside a module, smaller-scale code rules still apply; they just never override module depth.

**Cost.** You spend real time at this gate. That is the point.

## 10. A fair challenge panel with calibration

**Decision.** Lenses challenge your interface using a fixed card: quoted signature, the case for your current design, the objection, an anchor (a constraint ID or a cost-card number), an alternative signature, and its cost. Only anchored challenges can block. Three per lens at most. Reviewers never see the drafting chat. Your accept and overrule answers are counted, and rules adapt to your taste over time, except money and security rules.

**Why.** A reviewer that nags gets ignored; a reviewer that flatters is useless. Requiring a steelman, an anchor and a costed alternative makes every challenge worth reading, and calibration stops the same argument from coming back every week.

**Cost.** Slightly longer review cards. Worth it.

## 11. No design-it-twice step

**Decision.** There is no step that drafts a second, radically different interface before review.

**Why.** Challenge cards already bring alternative signatures, aimed at exactly the weak spots, at a fraction of the cost of a full second design.

**Cost.** Occasionally a wholly different approach goes unexplored. You can always ask for one.

## 12. Review built on `/polish`

**Decision.** Review extends an existing `/polish` skill: parallel read-only agents, validation of every finding against real code, a report grouped by category, and no fixes until you approve by number. Its PR review mode, which treats the diff as untrusted data, stays as is.

**Why.** It already does the hard parts well, it is cheap enough to run on every slice, and its untrusted-input handling is what makes server-side review safe.

**Cost.** None beyond the extensions below.

## 13. A converging multi-round reviewer (rejected)

**Considered.** A heavier variant of the same skill that keeps a run ledger, adds skeptic and deep-dive agents, and reviews its own fixes until a round warrants no edits.

**Why rejected.** It eats a lot of tokens for the extra confidence it buys. Two of its ideas were cheap and kept: findings written to a file, and regression tests that must fail when their fix is reverted.

## 14. Mechanical checks replace two review agents

**Decision.** Clean Architecture's dependency rule runs as an import-graph script. Interface conformance runs as a signature diff against the frozen stubs. Refactoring.Guru becomes rubric inside the existing design agent. Only APoSD (when an interface changed) and Money (in money repositories) get their own agents.

**Why.** Dependency direction is a graph property, not a judgment call. Spending model tokens on it would be waste. A typical slice stays at four review agents.

**Cost.** Refactoring.Guru shares context with another reviewer. If smells start slipping through, the profile can split it back out.

## 15. Money pack only where money moves

**Decision.** The financial-engineering skills load only when triage finds money signals (payment, exchange or chain SDKs, columns like amount or balance) and you confirm. They follow the pack's own routing: one domain skill per slice. Corrections in the pack's changelog trigger a re-review of features that relied on the old rule.

**Why.** In a payout worker, a reviewer that knows ambiguous timeouts can charge twice is the most valuable one in the room. In a CRUD admin panel it is noise.

**Cost.** Detection can miss. Confirming at triage keeps a human in that call.

## 16. BDD discovery everywhere, Gherkin only where it exists

**Decision.** Every Product gate works out rules and concrete examples, using Example Mapping. Open questions block the gate. Gherkin feature files and a BDD runner are used only in modules that already have them. Adopting BDD in a new module is an explicit choice, never automatic.

**Why this is good.** Concrete examples are the cheapest way to discover that two people mean different things by the same requirement, and they turn directly into the failing tests that every slice starts from. They also give the product, the glossary and the code one shared vocabulary, which is what keeps domain names consistent across agent-written slices. In repositories already running Cucumber, scenarios become the approved test plan, and the red-first check comes for free, because a new scenario fails until its behavior exists.

**Why not enforced.** Adding a test framework to a repository is a decision with maintenance cost. The thinking is free; the tooling is opt-in.

## 17. Language packs per module

**Decision.** Each module gets one language pack, picked from its manifest. Linter-catchable rules move into the linter config. The executor sees only the pack's rule index and reads the one or two rules relevant to the decision in hand. Review uses the pack's high-impact categories as rubric. Rules newer than the module's language version are skipped.

**Why.** Design books decide where boundaries go; a language pack decides how to express things well in that language. Agents write noticeably better idiomatic code with a ranked rule set close at hand.

**Cost.** Each pack must be read and pinned before use. Popularity is not correctness.

## 18. Python pack chosen for maintenance and adoption

**Decision.** Python uses Trail of Bits' `modern-python` for tooling (it feeds the linter and type checker config) and two or three skills from `wshobson/agents`' Python plugin as review rubric.

**Why.** The single Python pack shaped most like Vercel's had almost no adoption. Two well-maintained sources, one for tooling and one for idioms, cover the same ground with more confidence.

**Cost.** Two sources instead of one.

## 19. Prune as a scheduled, approved job

**Decision.** Ponytail's simplification ladder applies at three points: in the packet while writing, as review rubric, and in a prune job that audits a whole repository, ranks what to delete or simplify, and runs each approved item as a small behavior-preserving slice. Dead-code finding is done by each stack's own tool.

**Why.** Agents are biased toward adding code. Without a counterweight a codebase grows by accretion. A prune pass you approve keeps the counterweight under control.

**Never simplified away:** frozen interfaces, code enforcing a constraint ID, money invariants, and BDD steps still used by a scenario. The most aggressive mode never runs on money paths.

## 20. Third-party packs vendored and pinned

**Decision.** Every external pack lives in `~/.software-factory/` at a pinned commit. Bumps are deliberate and reviewed.

**Why.** Several of these packs move weekly and some are pre-1.0. An upstream change should never land in the middle of a feature.

**Cost.** Bumps are manual. That is intended.

## 21. factory-security: Cloudflare method, five scanners, routed knowledge

**Decision.** `factory-security` uses Cloudflare's `security-audit` as its method and evidence bar, five pinned scanners (Trivy, Opengrep, Gitleaks, zizmor, govulncheck) run before any judgment, and a routing index that loads at most one knowledge source per agent, chosen by the repository's threat model. Of the 817-skill mukul975 catalog it pins 15; of the Masriyan catalog none, keeping five ideas.

**Why.** The catalogs are mostly offensive, forensic and operational, and many relevant-looking skills fail a full read. The method that already matches the factory's evidence standard is the right core; specific knowledge earns its place only where the method leaves a gap. The full record, with the research: [research/security-selection.md](research/security-selection.md).

**Cost.** Without a sandbox, candidates whose exploitability needs a running system stay `needs_validation`. Several knowledge packs (OpenAI, Trail of Bits, Sentry) work only once installed and pinned.

## 22. factory-ui-ux: an enforced DESIGN.md, mechanical de-slop, anchored critique

**Decision.** Every repository with a UI keeps a `DESIGN.md` in Google Labs' format, extended with the product's principles, positions and words; a change that touches UI cannot proceed without it (gate rules, hook, runner). The skill drafts it from code and evidence and the user decides every position. Reviews run impeccable's detector, the factory's slop catalog, a computed-style script and axe in a real browser before any opinion, and every opinion is a challenge card anchored to the design file with a check. No installed style skill is loaded.

**Why.** Installed design skills polish surfaces, contradict each other and get accessibility wrong; none grounds a judgment in the product. The user's recorded standard is restraint, and "AI doesn't make design calls". Models judge design quality near chance, so they answer closed questions instead of scoring. The full record: [research/ui-ux-selection.md](research/ui-ux-selection.md).

**Cost.** Writing the design file takes a short interview. The slop thresholds are guesses until calibrated on the user's own screens. The tools need a local install.

## 23. factory-ci: its own measurement, a catalog with guards, savings that must beat the noise

**Decision.** `factory-ci` measures with a small script over `gh api`: 30 days of runs of every outcome, split into comparable groups, with the critical path, per-job queue, minutes, dollars and a measured noise floor. It applies a catalog of fixes with pinned actions and guards, reports CI posture through factory-security's zizmor line, and hands each approved fix to triage with a frozen baseline that `verify` checks after the merge. The installed `ci-speedup` is not loaded; its method is borrowed.

**Why.** On the user's own repositories, ci-speedup's success-only, unbounded sample described pipelines that were red at the time, and its verifier rejected its own report. The measurement needs about one API call per run and a few hundred lines. Run-to-run noise of 9 to 31% means a saving is claimed only when it beats the noise measured on the same repository. The full record: [research/ci-selection.md](research/ci-selection.md).

**Cost.** GitHub Actions only. Merge-queue time and checks from other apps are not measured yet. A fix's saving can take weeks of runs to confirm.

## 24. factory-retro: measured friction, environment fixes first, an evidence-gated playbook per repository

**Decision.** Reconcile ends every change with `factory-retro`. Retro measures the change's friction against the repository's earlier changes, then turns each lesson into a check where it can, a pointer where it cannot, and only then a line in the repository's `.factory/system/playbook.md`, which every factory skill reads. Entries need an outside signal seen in two changes, cite the code they apply to, carry counters, and retire when they stop earning their place. The user approves every change. To make this countable, the factory keeps an append-only `history` in `status.yaml`, tags every review finding by rule, and names lens rules exactly.

**Why.** Memory that admits every experience does worse than a fixed memory, and agent-written context files rarely help; outside evidence, itemized entries, pruning and caps are what worked. Before this, `status.yaml` overwrote the history retro needs. The full record: [research/retro-selection.md](research/retro-selection.md).

**Cost.** A few lines per step to append events. The thresholds are judgment until retro's own counters confirm them. Retro needs Pond for session numbers.

## 25. The first retro's two fixes: at most three interface panel rounds, and a factory version per change

**Decision.** The interface challenge panel runs at most three rounds: the full panel, then the full panel on the changed signatures only, then the APoSD reviewer alone; a fourth only when the user asks. Each change records the `factory_commit` it started on; when the factory has moved, the next step lists the factory's changes and brings `status.yaml` up to the current template, with the user's answers, before going on.

**Why.** The first change measured by hand spent 49% of its wall clock in six panel rounds, and the user had to stop the seventh. The skills changed during that change and a new `status.yaml` field never reached it, so UI review did not run on a UI slice. Details: [research/retro-selection.md](research/retro-selection.md), "What the first retro already shows".

**Cost.** Objections raised after round 3 reach the user only if they ask for another round. A factory update mid-change costs one confirmation.


## 26. From Factory's talk: acceptance on the running product, flaky tests at triage, tests that assert the example, a smaller model for checked work

**Decision.** Four changes, from Tereza Tížková's talk on Factory's missions ([research/talk-tizkova-factory.md](research/talk-tizkova-factory.md)):

- Reconcile starts with acceptance: a fresh agent, in an empty directory and told not to read the code, tries every FR example on the locally running product and reports pass, fail or not run with evidence. A defect the user confirms sends the change back to the slices gate, and the fix comes as a new slice; a wrong example the user corrects becomes the standing fit criterion. Triage records a run command for every module a user runs (`none` for a library), not only for packs with runtime checks. To make the send-back hold: the runner keeps a slice signed off under an earlier slices approval `done` when the commit the approver approved already showed it `done` at the same head commit, so an agent cannot revive a rewound slice by editing `status.yaml` (before, a send-back to the slices gate left every earlier slice `green` with no sign-off it could ever match), send-backs are committed, and the hook keeps gating source edits until a change is reconciled, not only until its last slice is done.
- Triage runs the test suite twice; a test that fails in either run joins `baseline_failures`, and those that failed once are named as flaky.
- The executor writes each red test to assert the outcome its Tests first line names, and review's cleanliness agent flags a test that only calls the code (`[factory/example-asserted]`).
- Research and retro's candidate reader run on a smaller model; every other agent keeps the session's model.

**Why.** Every check the factory ran was a test the executor wrote or a reviewer reading code; nothing confirmed the agreed examples in the running system, which is the failure the talk's user-testing validator caught. A red test can fail only because it calls a stub and then pass green with no assertion. One baseline run cannot tell a flaky test from a passing one, and a flaky old test fails red or green and costs a retry. Smaller models fit only where a later step checks the output against files; the scarce resource here is review time, not tokens.

**Cost.** One agent per change, and a run command to record per runnable module. The acceptance firewall is an instruction, not a sandbox. A second suite run per triage, which catches only tests that flake often. Research answers from a smaller model may need more follow-up questions. The runner proves who signed off which commit, not that signed-off code survives later commits: an agent can still undo it in a later commit, and the slices a re-approval keeps come from the `status.yaml` the agent wrote. The pull-request review before merge is the final control.

## 27. The tg-mini-app retro: milestone review, an autopilot build loop, fewer questions and commits

**Decision.** Six changes, measured on the first full change (`tg-mini-app`, standard track, 10 slices, about 9,500 lines with tests):

- **Milestones.** The slices gate groups slices into milestones: slice 01 alone, then two to four slices that end where the user can try something. Each slice keeps its red and green proof and its mechanical checks (`checks.md`); the review agents, the lens reviewers and the human sign-off run once per milestone. Headless mode keeps one slice per milestone, so the runner is unchanged. The hook opens a green slice's files only when no slice is being built, and a rewind resets every later slice whose code it removes.
- **Autopilot.** In interactive mode, build runs a milestone's slices back to back, goes straight on to its review, then to the next milestone and finally to reconcile, all in one session. It stops only to ask the user.
- **Files a frozen signature breaks.** The slices gate lists implementers, fakes and callers of the signatures a slice changes. When the executor still needs one, a file the adapter's typecheck shows broken by that signature is allowed and logged without asking.
- **Fixes applied.** Interactive reviews apply every validated finding that is not a note and stays inside the agreed files and contracts, and the sign-off question lists them so the user can undo any. This amends decision 12's approval by number, which headless mode keeps.
- **Commits.** Interactive build and review no longer commit `.factory/` per step; the planning state goes into each milestone's review commit. Triage checks that commit signing works, and a commit that fails to sign waits for the user, never goes unsigned.
- **Interface rounds after a send-back.** One round, the APoSD reviewer alone, on the changed signatures.

**Why.** Over about 13 active hours, the executor wrote code for 36 minutes. Build and review took about 7 hours, at 20 to 50 minutes per slice, mostly packets, session hand-offs, `/polish` and sign-off. Of the 49 questions to the user, 28 took the recommended option, all 8 file-allow questions were answered Allow (7 of them the same test fake breaking), and 3 of 9 sign-offs came within 15 seconds: the per-slice sign-off was not a real read. The change made 72 commits, 43 of them factory bookkeeping, and commit signing failed about five times, costing about an hour. Interface rounds 7 to 11 ran after a send-back, outside the cap.

**Cost.** A milestone's diff is larger to read than a slice's, and a review finding can now land after later slices were built on the code it fixes. Applied fixes reach the user after the fact, though each can be undone. A long autopilot session can run out of context; `status.yaml` resumes it. The expected saving, about 13 hours down to 5 or 6, is an estimate until the next change's retro measures it.

## 28. A Layout every gate holds: folder trees at architecture, frontend interfaces, exact Allowed files, a layout check; FSD only for a big frontend

**Decision.** The architecture gate gets a Layout section: a tree per module, one line per folder or file saying what lives there. An existing convention wins (`.factory/system/layout.md`, which reconcile keeps, or the folders the code already uses), and gates.md defines once what fits it: a named folder or file, or a file directly in a folder that already existed and that the Layout does not describe. A change only writes lines for new folders. A new frontend starts from the React config's default: a small tree (`pages/<page>/`, `components/`, `lib/`, `styles/`) up to five screens with no entity two screens use, and Feature-Sliced Design above that. FSD's layers go into `lenses.yaml`, so the existing dependency-rule check enforces them, and its own linter, steiger, runs in review. The interface gate designs frontends too: each page, and each export another folder imports (components with their props, hooks, the API client). Allowed files are exact paths, never wildcards, and must fit the Layout. Review check 9 flags every added file outside it.

**Why.** In `tg-mini-app` the Mini App came out as twelve flat files in `web/src`. The interface gate had designed every server module but not `web/`, the slice's Allowed files were `web/**`, and no lens covers folder structure: the design books judge interfaces and import direction, and the React pack is performance rules. The executor chose the layout alone. Layered server code passed because the architecture gate had chosen its layers.

**Cost.** A Layout section in every architecture document and one more review check. Designing a frontend raises the interface budget from 200 to 250 lines. FSD is a convention the user must want; the threshold of five screens is judgment until a retro shows otherwise. steiger needs a local install.

## 29. A catalog of reference layouts the architecture gate proposes from, with exemplars and pinned checkers

**Decision.** `kit/layouts/` holds ten reference layouts: layered, MVC, hexagonal (with Clean and Onion), DDD, CQRS, vertical slice, modular monolith, Feature-Sliced Design, a small frontend tree and feature folders. Each pattern file gives Layout lines to copy for TypeScript, Python, Go and Rust where the pattern is used there, its layers innermost first, the sibling rules a linear layer list cannot express, a checker, and exemplar repositories to look at. `index.yaml` maps the lens profile and observable signals to a proposal and an alternative: legacy keeps its tree, crud-service gets MVC, layered or vertical slice, domain-core gets hexagonal, a modular monolith of DDD contexts, and CQRS inside one context, and a frontend root gets the small tree or FSD. `tools.yaml` pins checkers per stack, with their config files; the Layout Decision picks one, writes its config from the pattern's layers and sibling rules, and the first slice proves it catches a planted violation. A Layout's lines sit under `Pattern: <id>, root: <path>, check: <tool>`, which reconcile keeps in `layout.md`, and review runs that checker on what the diff changed. A tree kept as it is records `existing`. Layers come per stack, and combined patterns come merged: a modular monolith already has DDD layers inside each module, and CQRS has lines for each host. The React config no longer carries layouts.

**Why.** The user wants proper layouts for the common patterns and real code to look up to, not one default per language. The research ([research/layouts-selection.md](research/layouts-selection.md)) read each pattern from its originator and verified every exemplar and tool version. It also corrected decision 28's FSD threshold: FSD's own test is reuse across pages and a growing team, and no source supports "more than five screens", so the small tree now lasts until an entity or user action is used by two screens.

**Cost.** Exemplar star counts and push dates age; the files carry their check date. Several of the best-known samples are stale, and Rust has no well-known, maintained hexagonal, DDD or modular-monolith exemplar. The checkers were checked against their registries and docs, not run on a real repository; the planted-violation step is what proves each config. The selection rows are judgment from the sources until a retro calibrates them.

## 30. A thin orchestrator for the autopilot, and token budgets per step

**Decision.** The autopilot of decision 27 no longer runs build, review and the next milestone in one session. `/factory-build` makes its session a thin orchestrator that holds only `status.yaml` and short reports. Each slice's build and each milestone's review runs as a fresh step agent in the foreground, which follows the skill for that one step, reads its inputs from files, and stops and reports wherever the skill would ask the user; the orchestrator asks and continues that agent with the answer. Reconcile, the last step, runs in the orchestrator. The orchestrator records each step agent's token total as a `step_tokens` event, and retro checks every step against a token budget in `metrics.md`.

**Why.** The `tg-mini-app` retro measured 351M tokens, of which 890k were output: the rest is the main session re-reading its own context on every turn, 8.8M per slice in build and 11.7M per slice in review. Skill text is a small share of that context; packets, diffs, test output and polish's reports are most of it. Decision 27's one-session autopilot would have made every later turn more expensive. A step agent's context dies with its step.

**Cost.** Each step agent re-reads its skill and inputs, which a long session would have cached. A question costs a round trip through the orchestrator. Step agents nest their own sub-agents (the executor, the review agents, and under factory-security's lens its hunters at a third level), which needs a harness that allows that depth: Claude Code does; Codex's default is one level and Cursor allows two (docs/research/harness-adapters.md), which the harness adapters must handle. A question's answer reaches a step agent by continuing it (Claude Code: SendMessage), or by a fresh agent that applies the answer where the skill asked it. The budgets are guesses until a repository has three changes of a track.

## 31. A framework on top of harnesses: evals first, one `.software-factory/` per project, harness adapters, a Slack channel

**Decision.** The factory becomes a framework for the software lifecycle that runs on the harnesses people already use, in four steps, in this order:

1. S13 evals, using Harbor: fixtures, script graders, a simulated user, a baseline.
2. S14 one `.software-factory/` per project. It holds the living documents and changes that `.factory/` holds today, plus a lockfile, config, principles and eval cases. A user layer carries taste across projects, and the project wins on conflict.
3. S15 adapters for Claude Code, Codex CLI and Cursor.
4. S16 a Slack channel for questions and replies, with approvals kept on the pull request.

This changes decisions 2 (the factory stays skills plus files, now behind adapters), 3 and 10 (calibration moves to the project and user layers), and 20 (packs are pinned per project).

**Why.** The kit was global, shared by every project, and updating it changed all of them at once. Nine skills, the hook and the runner were written for Claude Code only. Nothing measured whether a skill, model or harness change helped. Evals come first because S14 and S15 rewrite how every skill finds the kit and talks to the harness. In chat-native agents (Claude Tag, OpenClaw, OpenAI's dots, Grok Bot), no product binds an approval to a verified person and a commit, so the pull request stays the approval record. Research: [research/evals-selection.md](research/evals-selection.md), [research/harness-adapters.md](research/harness-adapters.md), [research/chat-channels.md](research/chat-channels.md).

**Cost.** Migrating `.factory/` to `.software-factory/` in repositories that already have one (bitxchange-tg). Docker for evals. Each harness is one more adapter to keep current, and Codex and Cursor need upgrades and trust steps before a first trial.

## 32. Review agents owned by factory-review, with a defect rubric and file coverage

**Decision.** factory-review carries its own review agents in `review-agents.md` instead of calling an installed review skill. This supersedes decision 12. Four agents: cleanliness, design and reuse, efficiency, and correctness. Correctness keeps side-effect gating and adds defect classes per language (`defects.md`: general, Go, Python, React and TypeScript, Rust), found with precision over recall. Every agent accounts for every reviewable file as reviewed or skipped with a reason, and the report and `review.md` carry that coverage line. Findings are numbered across the report and tagged `review/<category>`. The pull-request review mode is gone: the factory reviews only its own milestones.

**Why.** The installed skill was the one part of review outside the factory's pins: packs are pinned by hash, it was not, so an update to it changed review behavior unseen, and every machine and eval image had to install it. Its correctness agent left business-logic defects out of scope, so a defect no test pinned down had no reviewer. Agents on large diffs review some files and skip others without saying so; a coverage list makes a skipped file visible.

**Cost.** The factory now maintains the review rubric itself. The defect classes are judgment until REV-01 and REV-02 recall and precision measure them. The agent count is unchanged at four, but the correctness agent reads more.

## 33. S14 P1 to P3: `.software-factory/` per project, a framework cache per commit, three principle layers, init and upgrade

**Decision.** The first three phases of S14 (decision 31):

- **P1, the folder.** A project's state moves from `.factory/` to `.software-factory/`: `system/`, `changes/`, `runs/ci|ui|security|prune/` (the run folders that were `.factory/ci|ui|security|prune/`), `factory.lock`, `principles.md` and `evals/`. Skills, the hook, the runner, the stage evals and the docs use the new paths. Older decisions and dated research keep the old name, since they record what was true then.
- **P2, the layers.** The kit is no longer a symlink to this repository. `~/.software-factory/framework/<commit>/` holds `kit/` and `skills/` of one factory commit, unpacked once per machine and never edited by projects. A project's `factory.lock` names the commit and copies its pack pins, and `<kit>` is that commit's `kit/`. The user layer, `~/.software-factory/user/`, holds `principles.md` and `config.yaml` (`framework_repo`). Principles load in three layers: kit, user, project. A later layer wins on the same `<lens>/<rule>`, and a project Principle whose Source is a rule a lower layer quiets takes it out of Quiet rules. gates.md's Paths section defines all of this once.
- **Development path.** `framework: { dev_path: <absolute path to a factory checkout> }` may replace the commit, for developing the factory: `<kit>` is `<dev_path>/kit`, the skills are linked from `<dev_path>/skills`, and the version check uses that checkout's HEAD. Every skill first resolves `<kit>` and checks that the `realpath` of the gates.md it runs is inside the locked skills folder (the cache commit's or `dev_path`'s). Otherwise it names the commit or path actually running and stops. `step_start` records what ran.
- **Runner.** Before running the harness, the runner reads the change's `factory.lock` at the branch head and skips the change, with a message, when the lock is missing, names a `dev_path`, or names anything but a full 40-hex commit whose cache folder is installed. The branch is written by the harness, so it only selects among commits the operator installed with `bin/factory-install`; headless never runs a `dev_path`. A sign-off's "only planning state changed" no longer covers `factory.lock` or `principles.md`. A runner host links the skills user-level from the cache commit, because a project's links are untracked and absent from the throwaway clone, and `--setting-sources user` may skip project skills.
- **P3, init and upgrade.** `bin/factory-install <ref>` unpacks `kit/`, `skills/`, `hooks/` and `bin/` of one commit into the cache through a temporary folder and a rename, removes an old `~/.software-factory` link only when it points at a factory checkout's `kit/` (never its target), and writes `config.yaml`. `bin/factory-migrate` moves `.factory/` to `.software-factory/` (`ci`, `ui`, `security` and `prune` under `runs/`) with `git mv` for tracked folders and a rename otherwise, and rewrites `.git/info/exclude`. It refuses on tracked changes outside `.factory/`, deleted or unmerged files inside it, a rebase, merge, cherry-pick or revert in progress, a symlinked `.factory`, or an existing target, checks every `git mv` with `-n` first, commits nothing, and lists the other local and remote branches that still have `.factory/`. `/factory-init` detects the harness, stack and CI, locks a commit or `dev_path`, migrates, writes `factory.lock` and `principles.md`, links the skills, and offers the hard-gate hook in `.claude/settings.local.json` and the user layer's principles. `/factory-upgrade` shows the log and the decisions between two framework versions, installs, rewrites the lock's framework line and pins, and relinks. `kit/principles.md` now holds only framework defaults: the author's principles and quiet rules stay readable at `4820651b2eab869797f277d2d1d2f2c1b1ba2016:kit/principles.md`, which init offers for the user layer. The hook blocks source edits while an active change's lock is missing or names no framework, and whenever `.factory/changes/` holds a change that is not reconciled, whatever `.software-factory/` already holds, so an unmigrated branch is not left ungated; a `.factory/` whose changes are all reconciled blocks nothing. The runner reports a `factory/*` branch, local or remote, that still keeps its changes in `.factory/`.
- **Installation.** A project's skill links live in `.claude/skills/`, and the factory's links (`factory-*`, `ui-hard-gate`) go into `.git/info/exclude`, so review's committed-source check and rewind's `git clean` neither trip over them nor delete them. An old `~/.software-factory` symlink to `kit/` is removed first, or the cache and the user layer would write into this repository.

Where the design left a choice open:

- **D1.** A project without `factory.lock`, or whose locked commit is not in the cache, stops at Load (step 0), at triage's first step and at the top of ci, security and prune, pointing to `/factory-init`. No skill guesses a kit. A branch that still has `.factory/` and no `.software-factory/` stops the same way, pointing to `/factory-init` to migrate it.
- **D2.** `framework_repo` is used for the version log and also by `/factory-packs`, which bumps the framework's pins in that clone's `kit/packs.lock.yaml`. With the symlink gone, it is the only known path to the factory repository.
- **D3.** Reconcile counts accept and overrule answers in this repository's changes only. Counting across repositories would let one project's answers rewrite another project's file, which is the coupling decision 31 removes.
- **D4.** Pond finds the other projects. A rule that is a Principle in two or more of them, or quiet in two or more (never a money or security rule), and a playbook entry active in two repositories, are proposed for the user layer. The user decides each one.
- **D5.** A lesson that would add a linter rule to a language pack's `linter.propose` is now a proposal for the factory repository, since projects never edit the cache.
- **D6.** Packets copy the merged Principles of the three layers under Rules in scope. Review gives its review agents the merged Quiet rules (decision 32), rather than a link.
- **D7.** The rule that money and security rules never go quiet moves into gates.md's Paths, so it holds in every layer. It no longer depends on a sentence inside one `principles.md`.
- **D8.** Triage asks "committed or ignored" only while `.software-factory/changes/` holds no change, since the folder now exists from init on. Triage commits `factory.lock` and `principles.md` with the change when they exist.
- **D9.** Retro still never writes principles. Its lessons reach them through reconcile, which now writes the project's file.
- **D10.** The stage evals' setups write a `factory.lock` whose commit is the `factory_commit` they record (this repository's HEAD), with the kit's pins at that commit and `skills_linked: []`. The trial runner installs that commit as the cache.

**Why.** One global kit changed every project at once, and the user's taste, the framework's defaults and a project's own calibration lived in one file. A lockfile makes the framework version a project's own, reviewed choice. The layers keep taste that holds everywhere apart from what one repository taught. The runner and the skills refuse a framework they cannot prove is the locked one, instead of running whatever is linked.

**Calibration against decision 10.** Kept: the challenge card, counting accept and overrule answers per `<lens>/<rule>`, the threshold of three, and money and security rules never going quiet. Lost: answers no longer pool across repositories, so a new project needs three answers of its own before a rule is promoted or quieted, and it starts from the framework defaults plus the user layer. Cross-project taste reaches the user layer only through proposals the user approves. Since P3, `kit/principles.md` holds no one's taste; the author's moves to the user layer only when init's offer is accepted. Gained: a project's answers no longer change other projects, and a project can un-quiet a rule a lower layer quiets.

**Cost.** Every existing project needs `/factory-init` once, and every branch with `.factory/` a migration commit. Every machine and runner host keeps a cache folder per commit in use, and a runner host runs one linked framework at a time. Pins are per project, but packs are still installed once per machine: two projects pinned to different hashes of one pack cannot both load it until a cache per hash exists. A rule now takes longer to calibrate in a new repository.

**Merge.** Main's 4dfc306 (runtime.py, the runner's managed harness and recovery clone, the benchmark, the UI render checks) and 5d18ad5 (the review agents of decision 32) were brought into the S14 layout when main was merged into this branch: their paths moved under `.software-factory/` and `<kit>`.

## 34. Packs per project, in a cache per pinned hash

**Decision.** A pack loads from `~/.software-factory/packs/<name>@<hash>/`, the folder for the hash the project's `factory.lock` pins, and from nowhere else. `bin/factory-packs-fetch` fills it from a bare mirror of each source (`packs/.mirrors/<owner>__<repo>.git`, cloned without blobs), with `git archive` of the pinned tree into a temporary folder, a tree hash recomputed from the unpacked files, and a rename. The load is byte-exact: the mirror's `info/attributes` switches off every attribute that rewrites content (eol, filters, ident, export-ignore, export-subst), and archive and verification run without global or system git config. A symlink that is absolute or resolves outside the pack fails the pin, and clones and fetches check objects (`transfer.fsckObjects`). Sources are always `https://github.com/<source>.git`: there is no source override in production, and tests rewrite the URL through git's own `url.<base>.insteadOf`. `/factory-init` and `/factory-upgrade` run it after writing the lock, and a skill that finds a pack missing runs it once more, then continues without the pack; a headless runner host's operator fetches each change's lock instead. Each pin gains `path`, the pack's folder in its source, so `/factory-packs` reads upstream from the mirror (the tree at the default branch, its changelog and its log) instead of `~/.agents/.skill-lock.json` and `npx skills`.

**Why.** The framework is per project: like Angular in three apps that each pin their own version, two projects may pin different hashes of one pack. With one install per machine, only one of them could load it (decision 33, Cost). A content hash names exactly what a pin approved, so a shared folder per hash serves every project that pins it.

**Headless trust.** A branch's lock is harness-writable, so on a runner host the branch never chooses packs: the runner skips a change whose pins differ from its framework commit's `kit/packs.lock.yaml`, and the operator fetches only from that file.

**Cost.** The first fetch of each source needs the network, and a host without it runs without the packs it lacks. Disk grows by one folder per pack and hash in use, and the mirrors keep every commit and tree of their sources; nothing prunes either yet. A pin the skills CLI recorded for a pack at a repository's root names a commit, not a tree (`rust-skills`); the fetch accepts it and loads that commit's tree, and the next bump writes a tree hash.


## 35. FDA as the strong default for new frontend roots

**Decision.** New frontend roots propose Fractal Domain Architecture (`fda`) first, with colocated domains, explicit public entries and browser/server boundaries. Existing conventions win. Tiny prototypes/static sites/libraries and explicit team preferences may choose the small tree, FSD or feature folders with a recorded reason. The layout does not choose a framework or language. Only present responsibilities get files; no mandatory empty layers or repository wrappers.

**Why.** The user requested FDA as a strong default. [FDA research](research/layouts-selection.md) pins upstream and distinguishes its SvelteKit reference from Factory's React/Vite and Next adaptations. Actual framework route filenames and request-scoped SSR state prevail over inconsistent upstream skill examples.

**Cost.** One verified upstream example is not broad adoption evidence. Coarse layers alone do not enforce domain privacy or browser/server separation: the first implementation slice must prove its selected checker catches direct leaks, leaking re-exports and sibling-internal imports, and run the framework build. Decisions 28 and 29 remain valid except their frontend proposal order.

## 36. Approved development scope, direct execution and consolidated independent review

**Decision.** Preserve product, architecture, interface and slices approvals. Slice-plan approval explicitly authorizes bounded local implementation and repairs under unchanged promises. The conductor prepares packets and mechanical evidence and dispatches one executor per slice directly. One fresh independent general reviewer carries correctness, test assertions, design/reuse, cleanliness and hot-path efficiency; UI, security, money and APoSD specialists remain risk-triggered. Interactive milestones complete under the real approved execution scope after fresh review and checks; their Completion record is separate from final Human Sign-off. Headless PR-derived approvals/sign-offs are unchanged.

Correct executable-test mistakes locally when the approved criterion is unambiguous. Retain original history, record deviations, and replay corrected/regression tests against earlier source in an isolated clone before proving GREEN. Keep legitimate already-green negative tests with evidence and independent review. Resume local repairs without whole-source rewind, repeated generic panels or automatic permission questions after an arbitrary retry count. Real contract decisions, missing authority and destructive actions still stop.

**Why.** Repeated general reviews and an extra executor wrapper duplicate context and coordination. Direct execution with consolidated independent review simplifies development while preserving product and architecture discovery. It amends decisions 27, 30 and 32 for interactive development.

**Cost.** Consolidated review may miss issues; complete file coverage, risk specialists and final independent acceptance remain. Completed slices stay edit-protected: an acceptance defect needing a new corrective slice still requires the slices gate when no existing approved repair scope permits it. The 60–90 minute full-task target is unverified until another comparable run; policy edits alone prove no speedup.


## 37. Bundle pinned book rubrics with every framework and benchmark snapshot

**Decision.** `kit/packs/<name>@<hash>/` ships all ten currently configured `ciembor/agent-rules-books` packs with their skill entry and full/mini/nano rubrics, preserving exact upstream trees and MIT attribution. The common loader prefers a bundle only when source/path/hash match the project and framework pins. Existing framework archives already include `kit/`. The pack fetcher can verify and atomically copy matching bundles into the shared cache offline; other or older pins keep the existing cache/fetch path. Book-pin bumps ship the matching bundle with the lock.

Benchmark snapshots verify required book bundles before model execution, preserve their bytes during path adaptation, and record bundled provenance. Missing/corrupt required books are preparation errors rather than silent skips. Headless installed-framework/branch pin equality remains required. Profiles load the selected rubrics, not every available book.

**Why.** The user asked for books to be available for any Factory run. Cache-only preparation makes pinned book availability depend on host setup, even when unversioned global skills are installed.

**Cost.** About 303 KiB of pinned rule text plus license/manifest, and matching bundles must accompany book-pin updates. Older immutable framework versions are not rewritten; their cache/fetch behavior remains. This amends decision 34's cache-only lookup without using unversioned global skills or changing current pins. Historical benchmark snapshots/results stay unchanged.


## 38. An autonomous local implementation–review–repair–acceptance loop

**Decision.** New interactive slice plans include an explicitly approved local repair mandate. Reproducible acceptance defects against unchanged promises create ordinary corrective slices scoped to selected original slices' exact approved paths and criteria. Original documents, approval hashes and completed parent records stay unchanged. One shared read-only hook/CLI validates strict records, actual branch and commit provenance, evidence/input bytes, packet scope and every touched commit/pending source path, including edit-and-revert history. It does not manufacture authority, review or acceptance.

The conductor routes one validated finding batch to the existing executor and waits for actual native completion. Reviewers stay read-only. Isolated RED/GREEN, relevant mechanical checks, independent general/risk review, affected confirmation and complete independent FR/NFR acceptance determine technical success. Product/architecture/interface discovery remains. Real scope/contract/waiver/publication decisions remain. Older plans and headless PR authority keep their existing route.

**Why.** The user wants development to be an independent loop with the existing quality gates and less execution time. The remaining post-completion repair approval and conductor-written fixes interrupted that loop and repeated frontier work.

**Cost.** Corrective scope cannot grow through packet/deviation edits or use prior corrections as parents; missing planned paths require a real scope decision. Validators check bytes/scope, while actual review, environment applicability and independent acceptance remain conductor responsibilities. Time/price per accepted task is the metric; full-task speed improvement remains unmeasured. This extends decision 36's approved development scope and replaces its post-completion repair limit only for plans carrying the mandate.


## 39. Optional feature visual references, adapted to the approved brand

**Decision.** UI discovery offers once an optional 2–3 examples of the specific feature: screenshots, recordings, links or the product's good screens. Reuse supplied references; one useful example suffices. Capture only applicable observations in a change-local reference note, carried into UI design, branded mockups and executor packets. DESIGN.md owns brand/components/tokens/voice/density and approved FR/NFR/accessibility owns behavior. Review judges the actual branded result against approved criteria; external examples do not demand pixel identity or add features.

**Why.** The user finds feature examples much more useful than prompt-only design direction. Concrete visuals can clarify composition and interaction expectations and reduce visual rework. This is a workflow recommendation, not a measured model-quality result.

**Cost.** One small discovery invitation and concise reference capture; no reference quota, extra approval or development re-ask. Missing/declined/private references continue from the approved brief and design system. The previous UI hard gate's no-reference stop is removed; actual required browser, state, accessibility and visual-acceptance evidence remains. Late inspiration does not silently edit approved gate/brand criteria.


## 40. Named design principles, and a Gang of Four map loaded only by a smell

**Decision.** `kit/principles.md` names four framework principles, each with a one-line rule, a Test a reviewer applies to the diff without asking the author, and a tag: YAGNI (`factory/yagni`), KISS (`factory/kiss`), DRY (`factory/dry`) and SOLID (`factory/solid`). Their order when they conflict is written once. YAGNI and KISS win by default, so no interface with one implementation and no abstraction for a single caller, except a port that keeps an inner layer from importing an outer detail. DRY counts duplicated knowledge, not similar-looking code, and consolidates at the third copy (refactoring-guru's Rule of Three). SOLID applies at module boundaries, and open/closed adds an extension point only where a second variant exists. The same order decides between a lens rule and these principles. A user or project layer overrides or quiets one by its tag, as with any `<lens>/<rule>`. Review's Design and reuse rubric cites them by tag. KISS points at the existing simplification ladder instead of restating it.

No maintained, licensed Gang of Four rule set exists: `ciembor/agent-rules-books` has none, its refactoring-guru pack excludes design-pattern pages, and the MIT candidates on GitHub were single-author repositories under a month old. Factory writes its own `gang-of-four` pack, a smell-to-pattern table covering the 23 patterns with a Fits when and a smaller treatment per row, from general knowledge of the catalog and quoting no book or site. It is bundled at `kit/packs/gang-of-four@<tree>/` and pinned to this repository like any other pack. No profile loads it. Review reads it only when a design finding names one of the trigger smells listed in its Design and reuse rubric, and tags the result `[gang-of-four/<pattern>]`. A missing pattern is never a finding.

**Why.** The four principles conflict: without a written order, a DRY or SOLID finding can push an abstraction that YAGNI and KISS reject. A written order and a diff-level test make the findings repeatable. Mandatory patterns produce pattern-itis and contradict YAGNI and KISS, so the map treats patterns as a suggestion behind a smell.

**Cost.** The pack is Factory's to maintain: an edit renames its folder to the new tree hash and updates the lock and the `kit/packs/README.md` table in the same commit, and `/factory-packs` reports it as gone upstream until that commit reaches `main`. Removing the old Near-duplicates rubric line means a second copy of code is no longer a review finding.


## 41. Resume approved stages without rewriting or reapproval

**Decision.** Approved gate documents and a change's approved threat model keep their exact bytes. The editing hook blocks routine rewrites and accepts a full Write only when its result matches the recorded digest; pending drafts, status and separate evidence remain editable. Supplemental research, explanations and implementation findings do not reopen architecture or security decisions. A resume selects unfinished work, reuses applicable threat-model approval, and drafts/approves only pending gate documents. Proven agent-only incidental edits can be restored from the exact approved snapshot without changing approval records; user edits and uncertain provenance are preserved.

New standard interactive plan approvals authorize bounded implementation/review/acceptance repair rounds until required proof passes or a real blocker remains. Each round batches validated defects, retains RED/GREEN history, checks affected reviewers and reruns current acceptance. It does not repeat an unchanged whole panel or stop at an arbitrary repair count. Older explicit limits, manual pauses, headless approval provenance and final actual human sign-off remain. Material promise, contract, scope and security-outcome changes still require the concrete decision to be approved.

**Why.** Replaying completed planning and adding detail to approved architecture changed its hash and caused unnecessary downstream approvals; the threat-model step also always drafted and asked again. Standard review's one-repair limit turned repairable implementation failures into another human hand-off.

**Cost.** Hash checks stay exact, without semantic hashing or automatic reapproval. Hook enforcement covers editing tools, not shell writes or the truth of editable approval metadata. Skill-driven resume and security applicability still require judgment. This amends decisions 36 and 38 and the standard-track repair limit, without changing initial discovery or approval authority.


## 42. Reapprove changed decisions and explain the actual choice

**Decision.** Interactive revisions compare the exact before/after delta against existing product, architecture, interface, slice and security decisions. A compact impact note binds its compatibility reasons to the examined hashes/source; changed or contradicted gates reopen, while byte-identical compatible gates retain their approval records. Uncertain impact falls back to conservative invalidation. Supplementary interface fields do not get copied into approved architecture simply to make it match a later stage. Affected callers/tests/reviews/acceptance are reverified even when their governing architecture/security approvals remain valid. Completed parents stay locked; resolved send-back markers clear without another retained-gate approval. Headless PR snapshot authority is unchanged.

Question stages retain their existing scope and batching. Explain a meaningful choice with the user consequence, one concrete example, a recommendation and the alternatives' trade-offs. Use a small flow/state/sequence sketch or comparison table when it helps explain a relationship. Revisions show the actual changed decision, unchanged approvals and automatic checks; factual progress and explanatory follow-ups continue without another approval request. Ask for a user example only when missing context changes the decision.

**Why.** Pond session `15ba6cc4-cbac-42ed-a8b8-2e11185c0927` records the Glarity payment-widget flow saying architecture had nothing to change but needed reapproval because product reopened. The next step copied two response-field notes into architecture (`85df03db`, `2dd2159d` in Glarity). This was approval noise from stage-wide invalidation. The user values the questions and wants better explanations/visuals around meaningful decisions.

**Cost.** Compatibility is an evidence-backed workflow judgment, not semantic hashing or automatic approval of changed bytes. A model match alone does not prove unchanged security exposure. Existing closed-schema, money, storage, access and budget promises must still be examined, and actual contradictions require their decision to be revisited. This narrows decision 41's interactive chain reset; live agent behavior is not established by model-free regressions.


## 43. Cheap default review, explicit books and measured skill usage

**Decision.** Task-local `design_lenses: []` defaults all design-book rubrics off, including Refactoring.Guru, APoSD and Clean Architecture. Profiles advertise candidates rather than activate them. Task footprint is separate from risk: small/medium work gets no unsolicited lens question; large work may recommend one within the existing plan summary. Explicit selection loads one nano excerpt for small tasks, one mini for medium, at most two mini for large. The existing general reviewer carries selected review lenses, with at most one optional interface-design reviewer. Full books need an explicit deep-review request. Required tests, contract/import checks, independent correctness review and security/money coverage remain.

Every named skill invocation registers provider-backed token coverage per task. `kit/usage.py` records disjoint token classes, model, invocation, cumulative-resume high-water deltas and nested-attribution gaps. Headless Claude streaming evidence is retained outside the disposable harness clone on success, failure and interruption. Shared-session interactive measurements require actual entry baselines plus exit counters; otherwise attribution remains unknown. Reports expose per-skill invocation counts, measured classes and unknowns without additional model calls or mandatory retro. Actual dollars/call counts are not inferred from tokens. The former guessed multi-million-token budgets are retired.

**Why.** The user wants cheap, consistent steps instead of thorough stages skipped for cost. Automatic full APoSD panels and always-loaded book rubrics increased context and orchestration without per-task cost evidence. Measurement must show failed attempts and missing attribution, not reward skipping work.

**Cost.** Optional design critique can miss maintainability advice; the concise general review and executable checks remain the baseline. Token counters are observed provider telemetry, not a billing invoice or proof of correctness. Claude collection is implemented first; unsupported providers and nested skill splits stay explicit gaps. No matched live run or measured savings is claimed. This amends decisions 36/40's default rubric loads while retaining pinned availability and prior approval behavior.


## 44. ADRs declare enforcement like standing constraints

**Decision.** Every newly drafted or touched ADR carries `Enforced by`: a named architecture/lint rule, test, monitor or `human-verified`. Placement/import decisions use the chosen layout checker; behavioral decisions reuse their source constraint's enforcement and ID. Legacy missing lines read as human-verified until reconciliation drafts an explicit line. Named definitions must exist at source HEAD before reconciliation completes; missing execution is not green.

**Why.** A standing Decision without enforcement can silently outlive its implementation. This extends decision 5's constraint-to-check mapping to ADRs.

**Cost.** The conductor maps names to trusted existing commands; lexical definition checks do not prove that a test captures every implication of a Decision. No hook or workflow state is added.


## 45. Accepted ADRs anchor review and constrain pending plans

**Decision.** An accepted ADR whose Decision contradicts a changed line is an ordinary numbered review anchor, tagged `[adr/NNNN]`, with the existing severity ladder. Its named enforcement runs mechanically before model review. Draft Decisions and Frozen contracts are compared with accepted ADRs and SYS rows; a contradiction must name its proposed supersession or become an Open question, included in the approval summary. Only actual user answers enter pending drafts and their approval hashes. Approved documents stay unchanged.

**Why.** Conformance review cannot rescue a plan that silently contradicts standing intent.

**Cost.** Standard planning uses its existing conductor's bounded read rather than an extra fresh-agent call; the independent post-build reviewer remains. Critical planning can reuse a fresh panel. Small track checks only Covers/SYS references mechanically. None of these checks proves arbitrary semantic equivalence.


## 46. Pinned archgraph supplies cross-stack checks and review reading order

**Decision.** TypeScript, Python and Go may select archgraph on their Pattern line, pinned to published source commit `49464a7ec19fe8402b4258e751f7ba050c6eff19`. Native clean/planted fixtures prove import-rule enforcement. It supplements an already selected stack checker unless the Layout Decision chooses otherwise. Blast radius and ordered context seed the existing reviewer; every reviewable diff file remains covered and the full repository remains readable. Public-surface evidence helps only explicitly selected lenses.

**Why.** Importers and public boundaries are useful context that need not be rediscovered through a whole-repository read. This extends decision 29 without changing module ownership or review authority.

**Cost.** Native collection is experimental; incomplete surface coverage requires the existing search/manual fallback. Plain `check` fails forbidden edges, while cycle regressions require graph comparison. Missing tools are disclosed skips with the pinned install command, never clean results. No pack, MCP server or native parser is added to Factory.


## 47. Reconciliation reports ADR drift as a held decision

**Decision.** Reconcile runs named enforcement at HEAD and one bounded fresh read for human-verified accepted ADRs, only when such ADRs exist. `drift.md` records every accepted ADR, source/evidence and held gaps. Drift is decided at the existing consolidated final question: a new code change, ADR supersession, or explicit acceptance with a reason. The pass does not repair code or rewrite ADRs. Repeated evidenced drift across two changes supports a proposed mechanical enforcement.

**Why.** Shipping a new feature should expose standing decisions that no longer describe the code, rather than silently refreshing their prose.

**Cost.** The human-only read consumes the current reconcile allocation; it creates no new budget. Green tests establish tested outcomes, not the whole meaning of an ADR. Missing evidence remains unverified even if accepted by the user.


## 48. Retro attributes defects to the stage that produced them

**Decision.** M12 joins unique review/acceptance defects with their approved anchors and actual reconciliation decisions. It separates wrong gate documents, silent gate documents, changed interfaces and build nonconformance, reports unknown attribution, and normalizes by slices using the existing trend rule. The stage with the most evidenced wrong/silent defects becomes a review-budget proposal; only the user decides adoption.

**Why.** Finding tags describe what was noticed; they do not identify which stage needs better review. This extends decision 24.

**Cost.** Attribution requires evidence of the approved line and later decision, not a model's guess. Sparse history stays inconclusive. No new metric-classification agent or automatic budget change is introduced.


## 49. Authenticated events wake approved work

**Decision.** A local GitHub/Linear HMAC receiver durably deduplicates and coalesces wake-ups into SQLite before acknowledgment. Operator routes bind provider identities, dedicated clone, human approvers and a bounded continuation chain. The existing headless runner re-fetches actual PR authority and reports structured progress/wait/failure. Only verified changed-head progress continues automatically. Concurrent events cannot reset step limits or immediately retry preceding ambiguous failures. Interrupted running jobs remain parked for recovery.

**Why.** Already-approved projects should advance on events without an operator invoking each step. Authentication proves event origin, never approval of issue prose or new work.

**Cost.** Production ingress/subscriptions/secrets, canonical Linear dependency admission, common legacy/v2 locking and durable v2 resume remain separate integrations. Existing runner publication policy remains; no live service is configured here. Queue chain bounds are not token caps or exactly-once external effects.


## 50. Re-evaluate contracts after integration without silently changing them

**Decision.** V2 plans can opt into an approved `replan_budget` and trusted callback after each accepted local slice integration. It receives exact bindings, accepted commits and a bounded diff summary, records actual Opus native usage, and returns continue or at most three proposed slice deltas. A proposal pauses before later dispatch while retaining integrated commits and already-paid parallel outputs. It never rewrites frozen contracts, widens ownership, resets retries or grants approval. Compatible architecture/security decisions remain reusable.

**Why.** Missing work emerges during implementation; recording it before the next frontier is cheaper than reviewing a feature against an incomplete plan at the end.

**Cost.** Replan calls consume the existing feature and Opus-share limits; no automatic free call is added. The host must provide sandbox/timeout enforcement and native provider execution. Cross-run recovery needs a durable resume protocol before tickets can dispatch v2 slices independently.


## 51. Judge the factory by observed post-merge outcomes

**Decision.** M13 records confirmed escaped defects per fully observed merged feature; M14 records detection-to-recovery with unresolved incidents right-censored; M15 records adoption against an explicit successful event and eligible population. Stable incident IDs, merge attribution, declared windows and evidence support counts. Unmerged/unobserved features and missing analytics remain unknown. Compare quality separately from cost and time against the same-window control, including agent plus good CLAUDE.md.

**Why.** Gate failures show what checks caught; defects found after merge show what the factory missed. The historical sequential Factory result remains below its control and is not rewritten to justify the new design.

**Cost.** The helper validates supplied observations, not their external completeness. Production collection and a shipped observed pilot are still required. Adoption definitions belong to the product, not a generic automation default.


## 52. Retro may deprecate; shared context preserves provenance

**Decision.** Retro proposes improvement, creation, consolidation or deprecation using evidence, named consumers, replacement/migration and rollback. Human approval adopts the change; inactivity alone is insufficient, and historical framework pins remain intact. The proposed Pond-facing gateway reuses current retrieval tools and archgraph, gives workers/reviewers/a future Slack client the same bounded context schema, and separates authenticated read access from typed-entry proposals and external mutations.

**Why.** Skills and derived memory need a retirement path, while every consumer needs the same current decisions and navigation cues.

**Cost.** The gateway is a design, not an enabled MCP write endpoint or Slack bot. Project substring search is not tenant authorization; server-side scoped access and freshness/provenance are required. Raw transcripts remain historical evidence, never approval authority.


## 53. Reuse an Opus lead with bounded subagents; retain independent review

**Decision.** Replace the prescribed Sonnet slice-worker swarm with one Opus 5.5 lead, reused across dependency-ordered slices and repairs. The lead may use bounded native Opus helpers, including useful parallel subtasks. The v2 controller uses one isolated clone and an explicit native session ID, then resumes that session. The pinned helper inherits the model and current slice's ownership, read and frozen-file guards, with no background or nested agents. Helper usage counts toward budgets. A separate read-only Opus reviewer runs only after mechanical gates pass, before the next slice starts. Existing frozen contracts, scope guards, retries, actual-change approvals and final merge authority remain intact. A missing or changed implementation session stops execution rather than silently starting over.

**Why.** The user retained subagent delegation and chose an Opus lead instead of a Sonnet swarm. Context reuse and mechanical gates remain useful without prescribed parallel worktrees or a worker pool. The historical benchmark accepted 9/20 tasks for the prior sequential Factory versus 14/20 for each control; it does not evaluate this simplification.

**Cost.** The lead, helpers and review all use Opus, so new plans omit `opus_share_limit`. Explicit share ceilings in already-approved plans remain binding until the actual budget change is approved; historical pilot contracts are not rewritten. Incompatible explicit ceilings block admission before spending. Resumed native token and list-cost counters are accounted as deltas, and missing proof stays unknown. No native run or shipped pilot yet demonstrates savings, session reuse or improved quality. Durable event-driven v2 recovery remains separate work. This supersedes the prescribed slice-swarm execution defaults and the blanket 25% Opus target for new plans, not historical evidence or existing approvals.

## 54. One executable archgraph adapter for build and review

**Decision.** The existing build and review skills use `kit/archgraph.py` for pinned-tool discovery, bounded context and architecture regression evidence. Init detects availability. Build packets and reviewers receive ordered paths, explanations, source/base/policy/tool bindings and explicit omissions; helpers receive only their permitted context. A selected archgraph Layout check compares a verified Git base with current source under identical current rules and fails new forbidden edges, cycles and unplanned edges. Other selected stack checkers remain. The scoped v2 controller retains its existing sandboxed gates and filtered context; whole-root MCP is not silently granted to restricted helpers.

**Why.** Optional prose recipes left the everyday build without an executable context step. One shared adapter makes the same evidence reusable without another model call or a new skill.

**Cost.** Context defaults to an estimated 8k tokens; native graph coverage remains experimental and package-specific. Missing tools, changed source, invalid snapshots and uncovered changed source are explicit skipped/error proof gaps. Native TypeScript, Python and Go fixtures passed clean checks and rejected planted imports; this establishes integration behavior, not better feature quality. Existing approved documents and pilot contracts remain unchanged.

## 55. Recovery preserves authority, spending and verified work

**Decision.** V2 registers a plan to its original run directory and checkpoints execution with a hash-chained journal. A trusted host resumes only with the original approval source and exact plan/runtime/input bindings. Accepted commits, native session, elapsed time, usage, retries and review passes survive interruption. Recovery revalidates state under the execution lock, reuses verified boundaries and deduplicates receipts and events. Ambiguous native work, interrupted arbitrary callbacks and corrupt evidence hold rather than replay or reset budgets.

**Why.** Restarting the workflow must not repeat completed work, demand unchanged approvals or create a fresh spending allowance. This implements the recovery seam left open in decisions 49, 50 and 53.

**Cost.** Crash regressions and an independent review cover simulated interruption boundaries. Live provider restart recovery and automatic event-queue integration remain unvalidated. Recovery is not exactly-once execution of arbitrary external effects; it fails closed when the saved evidence cannot prove what happened.

## 56. Rename Software Factory to Plumb; migrate old projects, keep their file formats

**Decision.** The product, skills, scripts, modules, project state folder, lock, machine cache, branch prefix, environment variables and repository take the name Plumb (`plumb-*`, `.plumb/`, `plumb.lock`, `~/.plumb/`, `plumb/<slug>`, `PLUMB_*`). An old project migrates once: `/plumb-init` runs `bin/plumb-migrate`, which moves `.software-factory/` (and the older `.factory/`) into `.plumb/` with `git mv` and commits nothing. Until then the hook blocks source edits while either old folder holds an unreconciled change, and the runner still lists `factory/` branches and reports unmigrated ones. Markers stored inside project files keep their names: the `factory:design-schema` stamp, `factory/<name>` principle tags and the `factory_*` keys of `status.yaml`. Decisions 1 to 55, research, pilots and the benchmark's `factory` arm keep the old names as historical records.

**Why.** The user chose a shorter name that also works as a command prefix. Migrating once, as the earlier `.factory/` rename did, keeps one state path in every reader instead of two.

**Cost.** Each old project needs one migration commit. `/plumb-init` repoints a `factory_gate.py` hook entry before migrating, and `bin/plumb-migrate` refuses while any project or user settings file still runs it, while a git worktree lives under an old folder, or while two old folders' destinations are equal or nested. Until migration, the old folder's gate documents stay closed to edits. Runner state under `.git/` (`factory-usage`, `factory-recovery`, `factory-runner-heads.json`, `factory-v2-runs`) is not read after the rename: finish headless and v2 runs before upgrading. The old hook in an untracked `.claude/settings.local.json` cannot be repointed from the repository: after pulling a migration commit, each checkout runs `/plumb-init` once, and every Plumb skill stops until it does. Framework commits installed under `~/.software-factory/` stay there for projects not yet migrated; new installs go to `~/.plumb/`. Older documents link to `factory-*` paths that no longer exist.
