# Decisions

Every decision that shaped the factory, in the order it was made. Each one says what was decided, why, and what it costs. Superseded decisions stay in the log, marked as such.

| # | Decision | Status |
| --- | --- | --- |
| 1 | Four gates from Dex Horthy's talk, plus a research step | Accepted |
| 2 | Skills plus files, not a platform | Accepted |
| 3 | Decisions in files, recall in Pond | Accepted |
| 4 | Hard gates tied to a document hash | Accepted |
| 5 | A constraints registry that must map to enforcement | Accepted |
| 6 | Tracks that scale process to risk | Accepted |
| 7 | One handoff packet per slice | Accepted |
| 8 | Design-book lenses, chosen by profile | Accepted |
| 9 | APoSD as the spine of Interface Design | Accepted |
| 10 | A fair challenge panel with calibration | Accepted |
| 11 | No design-it-twice step | Accepted |
| 12 | Review built on `/polish` | Accepted |
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

