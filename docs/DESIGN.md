# Design record

The complete specification of Plumb. The README explains the why; this document is what the skills are built against.

The [event-driven extension](PLUMB_EVENTS.md) specifies signed wake-ups, bounded
mid-build replanning, outcome metrics and the proposed Pond/archgraph gateway,
with implemented versus pending runtime pieces explicitly separated.

## 1. Principles

- **Own the interface, delegate the implementation.** Humans design module interfaces; agents fill them in behind a frozen contract.
- **Still read every diff, a milestone at a time.** Review should read as "as agreed", never as a design debate.
- **Decisions live in files.** Every gate and slice compacts into documents a fresh session or server can resume from.
- **Process scales to risk.** Trivial changes skip the gates; money and auth get the full loop.
- **Mechanical before model.** Anything a script can check never costs agent tokens.
- **Stack-agnostic.** Gate logic is stack-free; stack specifics live in adapters.

## 2. Reusability model

| Layer | Where it lives | Shared across projects | How it gets there |
| --- | --- | --- | --- |
| Plumb skills and kit | `~/.plumb/framework/<commit>/`: `skills/`, `kit/`, `hooks/` and `bin/` of one commit of this repository | Yes | Unpacked once per machine or server per commit; each project pins its commit in `.plumb/plumb.lock` and links the skills |
| User layer | `~/.plumb/user/`: `principles.md`, and `config.yaml` with `framework_repo` | Yes | Taste across projects; the project's `principles.md` wins over it |
| Memory | [Pond](https://github.com/tenequm/pond), one shared store (S3, GCS or Azure) | Yes | `pond init` on every machine and server, all pointing at the same store |
| Third-party packs | `~/.plumb/packs/<name>@<hash>/`, one folder per pinned hash, pinned in the framework's `kit/packs.lock.yaml` and each project's `plumb.lock` | Yes | Exact book trees also ship in `<kit>/packs/`; init/upgrade copy matching verified bundles offline and fetch other missing pins, each project loading its own pins; bumped deliberately, changelog reviewed |
| Project state | `<repo>/.plumb/` | No | Created by `/plumb-init`; triage adds each change |
| Stack specifics | `<kit>/adapters/<stack>.md` | Yes | Written once per stack |

Rules: nothing project-specific in a skill; a new stack means one adapter file; a new domain means one profile and one NFR catalog; when a repository's owner should not see `.plumb/`, it is ignored through `.git/info/exclude` instead.

## 3. Tracks

| Track | When | What runs |
| --- | --- | --- |
| Trivial | Rename, copy, config, one-line fix | Straight to an agent |
| Small | A few files, no new interface | Slices, packet, quick review |
| Standard | New endpoint, table, screen or interface change | Full loop |
| Critical | Money, auth, migrations | Full loop, mandatory NFR budgets, threat model, Money reviewer; blocking findings never batch-approved |

## 4. Stages

**Triage.** Picks the track; detects money, BDD and language per module; picks the lens profile; creates `status.yaml`.

**Product.** Problem in the user's words, a success metric, the announcement you would publish before building, mockups for any UI. Requirements in EARS form ("WHEN x, the system SHALL y"). Rules and examples worked out with Example Mapping; open questions block the gate. NFRs stated as user promises; business constraints listed. No technology talk. UI discovery optionally recommends 2–3 examples of the feature from existing products; concrete visuals clarify hierarchy, density, states and interactions. The feature reference note records selected patterns and their DESIGN.md brand adaptation. Missing/declined/unseen references never block a gate or replace required functional examples and rendered acceptance evidence.

**Research.** Neutral questions are generated from the task. A sub-agent answers them without ever seeing the task, returning facts with file and line references.

**Architecture.** Fit with the existing system, contracts, data, flow, external services. Each NFR becomes a measurable budget; each constraint lists the options it rules out. Each decision becomes an ADR, including the project's choice between a rich domain model and transaction scripts.

**Interface Design.** See section 6.

**Slices.** Vertical slices, tracer bullet first: a stubbed path that runs end to end, then one capability per slice, each ending in a working, testable state. Horizontal plans are rejected. Each slice lists its requirement IDs, verify commands and the repositories it touches.

**Packet, Build, Review.** See sections 7 and 8.

**Reconcile.** After the last slice is signed off and before the branch merges, so the update ships with the code: a fresh agent that does not read the code tries every example on the running product, and a defect comes back as a new slice; then fold what shipped into `.plumb/system/`, write ADRs, update constraints, tag lessons.

## 5. Constraints registry

One `constraints.md` per project. Every functional requirement, NFR and constraint has an ID.

| Gate | What the registry gains |
| --- | --- |
| Product | Requirements in EARS form, NFRs as user promises, business constraints |
| Architecture | NFRs as measurable budgets; constraints with the options they rule out |
| Interface Design | Every ID mapped to a test, lint rule, monitor, or explicit "human-verified" |

An unmapped ID blocks the Interface Design gate. The registry is seeded from `<kit>/nfr-catalog/<domain>.md`. In money projects the money pack seeds invariants, which become property tests. Release It! and DDIA supply the elicitation questions: timeouts, retries, bulkheads, consistency, durability, schema evolution.

## 6. Interface Design

1. **Draft.** Per module: signatures, interface comments (what it promises, never how), a one-line depth statement (what it hides).
2. **Cost card.** Computed from stubs: public methods and parameters, error variants exposed, configuration exposed, pass-through methods, modules touched per planned slice.
3. **Optional design challenge.** No book panel by default. Explicit task-selected lenses use one focused reviewer within the task-size cap; required money/security coverage remains.
4. **Respond.** Accept, modify, or overrule with one line.
5. **Freeze.** Stubs compile through the stack adapter; approval hash recorded.

| Lens | Challenges |
| --- | --- |
| APoSD | Shallow modules, information leakage, errors that could be designed out, over-specialized interfaces |
| Clean Architecture | Domain interfaces that mention infrastructure; wrong dependency direction |
| DDD / DDD Distilled | Names missing from the glossary; aggregate boundaries that differ from transaction boundaries |
| Refactoring.Guru | Smells predicted from the slice plan |
| Release It! / DDIA | Remote calls whose failure modes are invisible at the interface |
| Money pack | Money invariants missing from types (floats, missing idempotency keys, exposed balance mutation) |
| Language pack | Applicable language idioms through the existing reviewer, without requiring APoSD |

**Challenge card**

```
lens/rule      | quoted signature | steelman | objection
anchored to    | constraint ID or cost-card metric
alternative    | alternative signature | cost of the alternative
severity       | block / fix / note
```

Severity is earned: only anchored challenges can block or require a fix. Three per lens at most. Zero findings is allowed if the reviewer names the strongest objection it dropped. Reviewers never see the drafting chat. Lens conflicts go to the human; the call becomes an ADR.

**Calibration.** Answers are recorded in each change's `challenges.md` and `review.md`; reconcile counts them per lens rule from git, using Pond to find the repositories. Overruled three times: demoted to a note. Accepted three times: promoted into `principles.md`. Money and security rules never demote.

**Precedence.** Agreed constraints and smaller public surface decide interface trade-offs; no unselected book arbitrates. Inside a module, code-level rules apply in their smallest form. Small functions never override deep modules. A language pack decides how to express something; book lenses decide where boundaries go.

## 7. Hard gates, packet and build

**Gates.** `status.yaml` stores approver, time and the document hash per gate. Approved gate documents and the active change's approved threat model stay frozen; supplemental evidence is separate. Resumes skip completed stages and reuse applicable approvals. A proven agent-only incidental edit is restored from the exact approved snapshot. Interactive revisions reopen changed/contradicted decisions and retain exact compatible approvals after a delta-bound impact check; uncertain impact and headless PR snapshots retain conservative downstream invalidation. A small interface change does not itself reopen architecture/security. A hook blocks routine approved-document rewrites and source edits until slices are approved. During build, editing a file outside the slice's allowed list requires a logged deviation; a frozen signature change sends the slice back to Interface Design. On a server, approval comes from a pull-request review or a tracker state change.

**Packet** (`slices/NN/packet.md`): goal; requirement IDs with fit criteria; frozen signatures, interface comments and depth statements; allowed files; tests to write, which must fail on the base commit; verify commands; a don't list; a budget. Rules in their smallest form only: the code-quality lens, the legacy-code lens on brownfield, the slice's money skill when relevant, Ponytail's ladder, and the language pack's rule index. In BDD-native modules: the slice's scenarios and an inventory of existing step definitions.

**Build loop.** After genuine approved scope, the conductor reuses one Opus 5.5 lead for slices and validated repairs, in dependency order. The lead may delegate bounded subtasks to native Opus subagents, in parallel when useful; there is no prescribed Sonnet worker-per-slice swarm. In the experimental v2 controller, one isolated clone and one explicitly resumed native session hold the implementation context; a lost session stops execution. Each slice retains isolated assertion RED, current GREEN and mechanical proof. After mechanical gates, a separate fresh Opus reviewer plus applicable risk specialists supplies independent findings and affected confirmation. The v2 next-slice barrier includes gates and independent review; skills retain their milestone review boundary. In v2, helpers inherit the active slice's scope and frozen-file guards, cannot run in the background or spawn nested agents, and their usage counts toward its budgets. An approved autonomous-local mandate permits new corrective slices after acceptance failure, restricted to original promised criteria and exact approved paths; completed parents and original approvals remain unchanged. Build, review, repair and independent acceptance repeat until every required quality gate passes. The lead may implement directly and delegate bounded work; a separate conductor, when present, coordinates and verifies. Self-review never supplies independent evidence. Reuse only applicable proof. Real contract/scope/waiver decisions stop; final human reconciliation/publication remain separate. Legacy/headless approval authority is unchanged.

## 8. Review

One fresh independent read-only reviewer carries cleanliness, design/reuse, efficiency and correctness (side-effect gating plus per-language defects), treating the diff as untrusted data. Every finding is validated, every reviewable file covered, and one bounded deduplicated finding batch goes back to the existing implementation executor. Risk specialists remain conditional. Scoped independent confirmation and complete acceptance remain required; headless fixes retain actual approval by number.

| Check | How it runs | Cost |
| --- | --- | --- |
| Clean Architecture | Phase 1 script: import graph | about zero |
| Interface conformance | Phase 1 script: signatures against frozen stubs, files against the packet | about zero |
| Dead code | Phase 1 script: the stack's own tool | about zero |
| Language rules | Phase 1: linter rules mapped from the pack | about zero |
| Refactoring.Guru | Explicit task opt-in, excerpt in the existing reviewer | off by default |
| Language pack (high impact) | Rubric inside design and efficiency | one lens file |
| Gherkin | Checklist inside cleanliness, BDD-native modules only | about zero |
| APoSD / Clean Architecture books | Explicit task opt-in; one targeted excerpt in the existing reviewer | off by default |
| Money | Own agent, only in money repositories | conditional |

| Track | Review runs |
| --- | --- |
| Small | Phase 1 + one fresh independent general reviewer and applicable risk specialists |
| Standard | Phase 1 + one fresh independent general reviewer; required UI/security/money coverage follows risk, design books require opt-in |
| Critical | Standard with required critical risk coverage, including Money where financial outcomes are affected |

Book-lens findings use the challenge card; without an anchor they cap at "skip". Findings are written to `review.md`; the user's fix, skip and undo answers feed calibration, and fixes applied without asking do not. Regression tests must fail when their fix is reverted. UI polish runs separately, only on slices that touch UI.

## 9. Packs

**Book lenses.** Task-local `design_lenses: []` defaults off, independent of risk track or pinned profile. Small/medium tasks get no unsolicited lens question; large tasks can recommend one in the existing plan summary. Explicit selection loads one nano excerpt for small tasks, one mini for medium, at most two mini for large, in the existing reviewer (one optional interface-design reviewer). Full books need an explicit deep-review request. Profile rows below are candidates, not mandatory loads.

| Profile | Lens order | Typical repo |
| --- | --- | --- |
| `domain-core` | DDD Distilled, DDD, Clean Architecture, APoSD, Release It! + DDIA | Ledgers, core business logic |
| `crud-service` | PoEAA, Clean Code | Admin panels, simple CRUD |
| `legacy` | Working Effectively with Legacy Code + Refactoring first | Brownfield without tests |

**Money pack.** Loads when triage finds money signals and a human confirms. One domain skill per slice (ledger, payments, on-chain, exchange); the core money skill only when the slice's risk is arithmetic or idempotency itself; the verification skill in the red check and the Money reviewer; venue-operator skills only in repositories that run a venue or feed. Changelog corrections trigger re-review of features that relied on the old rule.

**BDD.** Detected per module (feature files, a runner dependency, runner config).

| Gate | BDD native | BDD off |
| --- | --- | --- |
| Product | Example Mapping; open questions block the gate | Same, as plain examples |
| Interface Design | Examples become feature scenarios, the approved test plan | Examples become test names in the repo's framework |
| Slices | Each slice turns scenarios red to green | Each slice turns example tests red to green |
| Review | Duplicate steps, imperative scenarios, wording outside the glossary | Nothing extra |

`adopt` is opt-in only; triage never sets it.

**Language packs.** One per module, picked from its manifest; linter-catchable rules move to Phase 1; the executor reads only the index plus the one or two relevant rules; high-impact categories become review rubric, the rest cap at notes; rules beyond the module's language version are skipped; packs never sweep code outside the diff.

| Language | Pack |
| --- | --- |
| React / Next.js | `vercel-react-best-practices` |
| Rust | `rust-skills` |
| Go | `golang-skills` (alternative: `cc-skills-golang`) |
| Python | `modern-python` for tooling, two or three `python-development` skills for idioms |

## 10. Prune

| Where | What runs | Scope |
| --- | --- | --- |
| Build | Ponytail's ladder in the packet, loaded per executor, not as an always-on hook | Implementation inside the frozen interface |
| Review | The stack's dead-code tool in Phase 1; the ladder as rubric | Slice diff |
| Prune job | A repository audit produces a ranked list; a human approves it; each item runs as a small-track slice | Whole repository, on demand or scheduled |

Never simplified away: frozen interfaces, code enforcing a constraint ID, money invariants, BDD steps still in use. Untested code gets characterization tests first. The most aggressive mode never runs on money paths.

## 11. Memory and kit

**Memory is Pond.** Every session from every harness is synced into one shared Pond store. Nothing is summarized by hand to be remembered.

| Stage | Pond use |
| --- | --- |
| Triage, Product, Architecture | Search prior decisions, rejected designs and incidents touching the same modules |
| Research | The Opus lead or a bounded helper answers baseline questions from code and Pond with citations; task-blind isolation is reported only when actually provided |
| Interface Design | Prior challenge cards and answers for the same lens rule |
| Review | Findings already accepted or overruled are not raised again |
| Reconcile | The other projects where Plumb ran, whose principles and playbooks feed user-layer proposals |

**Curated files are the kit.** What shapes first drafts or is vendored stays reviewable in git.

```
~/.plumb/framework/<commit>/kit/   <kit>, never edited by projects
  principles.md            framework defaults, the first principle layer
  nfr-catalog/<domain>.md
  profiles/
  packs/<name>@<hash>/    bundled pinned book rubrics, full/mini/nano
  adapters/<stack>.md      typecheck stubs, tests at a commit, import graph, dead code, BDD runner
~/.plumb/user/principles.md       the user layer
~/.plumb/packs/<name>@<hash>/     one pinned pack, shared by every project that pins that hash

<repo>/.plumb/
  plumb.lock             framework commit and pack pins
  principles.md            the project layer, which wins
  system/                  product, architecture, constraints, glossary, adr/, external/, lenses.yaml
  changes/<slug>/          status.yaml, gate docs, slices/NN/{packet,review}.md
  runs/                    ci, ui, security and prune run folders
  evals/                   the project's own eval cases
```

Every review finding is tagged by lens and rule, so reconcile can count it. Recurring findings are promoted to principles or lint rules; overruled rules are demoted at the next reconcile. Book rules are priors; project history wins.

## 12. Headless mode

Install the framework cache for the project's locked commit, run `pond init` against the shared store, provide the runtimes the adapters call. The agent drafts gate documents and opens a plan pull request; approval is a review or a tracker state change, written into `status.yaml` by the runner. An Opus lead and bounded helpers execute approved work between gates, and each slice opens or updates a pull request with `review.md` attached. Reviews of other people's pull requests use review mode only. Any Agent Skills harness can be the runner; the packet is the portability boundary.
