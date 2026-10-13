# Design record

The complete specification of the factory. The README explains the why; this document is what the skills are built against.

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
| Factory skills and kit | `~/.software-factory/framework/<commit>/`: `skills/`, `kit/`, `hooks/` and `bin/` of one commit of this repository | Yes | Unpacked once per machine or server per commit; each project pins its commit in `.software-factory/factory.lock` and links the skills |
| User layer | `~/.software-factory/user/`: `principles.md`, and `config.yaml` with `framework_repo` | Yes | Taste across projects; the project's `principles.md` wins over it |
| Memory | [Pond](https://github.com/tenequm/pond), one shared store (S3, GCS or Azure) | Yes | `pond init` on every machine and server, all pointing at the same store |
| Third-party packs | Installed under `~/.agents/skills/`, pinned by hash in the framework's `kit/packs.lock.yaml` and each project's `factory.lock` | Yes | Bumped deliberately, changelog reviewed |
| Project state | `<repo>/.software-factory/` | No | Created by `/factory-init`; triage adds each change |
| Stack specifics | `<kit>/adapters/<stack>.md` | Yes | Written once per stack |

Rules: nothing project-specific in a skill; a new stack means one adapter file; a new domain means one profile and one NFR catalog; when a repository's owner should not see `.software-factory/`, it is ignored through `.git/info/exclude` instead.

## 3. Tracks

| Track | When | What runs |
| --- | --- | --- |
| Trivial | Rename, copy, config, one-line fix | Straight to an agent |
| Small | A few files, no new interface | Slices, packet, quick review |
| Standard | New endpoint, table, screen or interface change | Full loop |
| Critical | Money, auth, migrations | Full loop, mandatory NFR budgets, threat model, Money reviewer; blocking findings never batch-approved |

## 4. Stages

**Triage.** Picks the track; detects money, BDD and language per module; picks the lens profile; creates `status.yaml`.

**Product.** Problem in the user's words, a success metric, the announcement you would publish before building, mockups for any UI. Requirements in EARS form ("WHEN x, the system SHALL y"). Rules and examples worked out with Example Mapping; open questions block the gate. NFRs stated as user promises; business constraints listed. No technology talk.

**Research.** Neutral questions are generated from the task. A sub-agent answers them without ever seeing the task, returning facts with file and line references.

**Architecture.** Fit with the existing system, contracts, data, flow, external services. Each NFR becomes a measurable budget; each constraint lists the options it rules out. Each decision becomes an ADR, including the project's choice between a rich domain model and transaction scripts.

**Interface Design.** See section 6.

**Slices.** Vertical slices, tracer bullet first: a stubbed path that runs end to end, then one capability per slice, each ending in a working, testable state. Horizontal plans are rejected. Each slice lists its requirement IDs, verify commands and the repositories it touches.

**Packet, Build, Review.** See sections 7 and 8.

**Reconcile.** After the last slice is signed off and before the branch merges, so the update ships with the code: a fresh agent that does not read the code tries every example on the running product, and a defect comes back as a new slice; then fold what shipped into `.software-factory/system/`, write ADRs, update constraints, tag lessons.

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
3. **Challenge panel.** Fresh-context reviewers, one lens each, in parallel.
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
| Language pack | API design and data modeling idioms, through the APoSD reviewer |

**Challenge card**

```
lens/rule      | quoted signature | steelman | objection
anchored to    | constraint ID or cost-card metric
alternative    | alternative signature | cost of the alternative
severity       | block / fix / note
```

Severity is earned: only anchored challenges can block or require a fix. Three per lens at most. Zero findings is allowed if the reviewer names the strongest objection it dropped. Reviewers never see the drafting chat. Lens conflicts go to the human; the call becomes an ADR.

**Calibration.** Answers are recorded in each change's `challenges.md` and `review.md`; reconcile counts them per lens rule from git, using Pond to find the repositories. Overruled three times: demoted to a note. Accepted three times: promoted into `principles.md`. Money and security rules never demote.

**Precedence.** APoSD arbitrates at interface level. Inside a module, code-level rules apply in their smallest form. Small functions never override deep modules. A language pack decides how to express something; book lenses decide where boundaries go.

## 7. Hard gates, packet and build

**Gates.** `status.yaml` stores approver, time and the document hash per gate. A hash mismatch reverts that gate and all downstream gates. A hook blocks source edits until slices are approved. During build, editing a file outside the slice's allowed list requires a logged deviation; a frozen signature change sends the slice back to Interface Design. On a server, approval comes from a pull-request review or a tracker state change.

**Packet** (`slices/NN/packet.md`): goal; requirement IDs with fit criteria; frozen signatures, interface comments and depth statements; allowed files; tests to write, which must fail on the base commit; verify commands; a don't list; a budget. Rules in their smallest form only: the code-quality lens, the legacy-code lens on brownfield, the slice's money skill when relevant, Ponytail's ladder, and the language pack's rule index. In BDD-native modules: the slice's scenarios and an inventory of existing step definitions.

**Build loop.** Per slice: a fresh executor, red check (new tests fail on the base commit), implement until green inside the module boundary, mechanical checks. Per milestone: review, validated fixes applied, human reads the diff and `review.md`, signs off. The loop runs on autopilot: a thin orchestrator starts a fresh step agent per slice and per milestone review, keeps only their short reports, and stops only for the human.

## 8. Review

Four parallel read-only agents (cleanliness, design and reuse, efficiency, and correctness: side-effect gating plus per-language defect classes) treat the diff as untrusted data. Every finding is validated against the code, every changed file is reviewed or skipped with a reason, one numbered report is grouped by category, and validated fixes are applied once per milestone (headless: only after approval by number).

| Check | How it runs | Cost |
| --- | --- | --- |
| Clean Architecture | Phase 1 script: import graph | about zero |
| Interface conformance | Phase 1 script: signatures against frozen stubs, files against the packet | about zero |
| Dead code | Phase 1 script: the stack's own tool | about zero |
| Language rules | Phase 1: linter rules mapped from the pack | about zero |
| Refactoring.Guru, Ponytail | Rubric inside the design and reuse agent | one lens file |
| Language pack (high impact) | Rubric inside design and efficiency | one lens file |
| Gherkin | Checklist inside cleanliness, BDD-native modules only | about zero |
| APoSD | Own agent, only when the slice adds public surface beyond the frozen interface | conditional |
| Money | Own agent, only in money repositories | conditional |

| Track | Review runs |
| --- | --- |
| Small | Phase 1 + the fast path (under about 50 changed lines, no fan-out) |
| Standard | Phase 1 + four agents + APoSD if the slice adds public surface beyond the frozen interface |
| Critical | Standard + Money |

Book-lens findings use the challenge card; without an anchor they cap at "skip". Findings are written to `review.md`; the user's fix, skip and undo answers feed calibration, and fixes applied without asking do not. Regression tests must fail when their fix is reverted. UI polish runs separately, only on slices that touch UI.

## 9. Packs

**Book lenses.** Sizes by role: smallest in packets, medium in gates and review, full for APoSD and escalations. Never load overlapping or conflicting books together.

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
| Research | The sub-agent answers its neutral questions from the code and from Pond; it still never sees the task |
| Interface Design | Prior challenge cards and answers for the same lens rule |
| Review | Findings already accepted or overruled are not raised again |
| Reconcile | The other projects where the factory ran, whose principles and playbooks feed user-layer proposals |

**Curated files are the kit.** What shapes first drafts or is vendored stays reviewable in git.

```
~/.software-factory/framework/<commit>/kit/   <kit>, never edited by projects
  principles.md            framework defaults, the first principle layer
  nfr-catalog/<domain>.md
  profiles/
  adapters/<stack>.md      typecheck stubs, tests at a commit, import graph, dead code, BDD runner
~/.software-factory/user/principles.md       the user layer

<repo>/.software-factory/
  factory.lock             framework commit and pack pins
  principles.md            the project layer, which wins
  system/                  product, architecture, constraints, glossary, adr/, external/, lenses.yaml
  changes/<slug>/          status.yaml, gate docs, slices/NN/{packet,review}.md
  runs/                    ci, ui, security and prune run folders
  evals/                   the project's own eval cases
```

Every review finding is tagged by lens and rule, so reconcile can count it. Recurring findings are promoted to principles or lint rules; overruled rules are demoted at the next reconcile. Book rules are priors; project history wins.

## 12. Headless mode

Install the framework cache for the project's locked commit, run `pond init` against the shared store, provide the runtimes the adapters call. The agent drafts gate documents and opens a plan pull request; approval is a review or a tracker state change, written into `status.yaml` by the runner. Executors run unattended between gates, and each slice opens or updates a pull request with `review.md` attached. Reviews of other people's pull requests use review mode only. Any Agent Skills harness can be the runner; the packet is the portability boundary.
