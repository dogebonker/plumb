# Landscape

What the existing spec-driven and agent-workflow projects already do well, where they stop, and what this Plumb takes from each. Surveyed in October 2026; these projects move fast, so check each repository before relying on a detail.

## The projects

| Project | Center of gravity | Taken from it | Where it stops |
| --- | --- | --- | --- |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | A project constitution plus a fixed specify, plan, tasks, implement sequence, with a converge step that compares what was built against the plan | The constitution idea (here: the kit's principles and the constraints registry) and convergence (here: interface conformance) | Phase order is enforced, approval is not; small changes produce a lot of generated prose; no program-design layer |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Living specs plus one folder per proposed change, archived back into the specs after shipping; multi-repo planning in beta | Living specs and archive-on-merge (here: reconcile); one plan spanning several repositories | No phase gates by design; verification is non-blocking; spec drift is managed by hand |
| [Superpowers](https://github.com/obra/superpowers) | A full methodology as auto-triggered skills: brainstorming, small planned tasks, a fresh sub-agent per task with review, strict TDD | Fresh executor per unit of work, review between units, test-first discipline | Designs serve the feature in flight and are not folded into a long-lived spec; sign-off happens in chat |
| [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) | A simulated agile team: product, architecture, UX, development and QA roles, with planning sized to the change | Scale-adaptive planning (here: tracks); roles as review perspectives | Heavy to learn and to run; role personas cost tokens without adding judgment |
| [Get Shit Done](https://github.com/gsd-build/get-shit-done) | Context engineering: small orchestrators, work in fresh sub-agent contexts, state on disk, size budgets per file | State on disk, fresh context per task, line budgets for documents | Phases rather than vertical slices; no program-design step |
| QRSPI implementations (several community repositories) | Dex Horthy's newer workflow: questions, research, design discussion, structure outline, plan, implement | The research firewall, the structure outline as a header-file-like contract, and a cap on instructions per step | Fragmented across many forks and versions |
| [plumb gist](https://gist.github.com/Maciejdziuba/88890d7e0eeefa5a8738bbe9fd5e20b8) | A direct port of the talk's four gates as one skill, with a status file and a resume rule | Status file, "least confident decisions" list, tests that must fail on the old code | One monolithic skill; no constraints registry; chat approval; per-repo memory |
| [pi-sdd-kit](https://github.com/felipefontoura/pi-sdd-kit) | Strict spec-then-approve with a hard per-phase approval token, EARS requirements, steering documents with reasons | Hard approval tokens; EARS; recording the reason behind each standing rule | Tied to one agent harness |

## Gaps none of them close

1. **Constraints are second-class.** Non-functional requirements and hard constraints appear as prose, if at all, and nothing checks that they are enforced.
2. **Program design is nearly absent.** Most go from architecture or tasks straight to code, so interface decisions are made silently mid-implementation.
3. **Approval is soft.** A plan existing is treated as a plan being approved.
4. **Specs drift after shipping.** Only one project folds what shipped back into its specs.
5. **Memory stops at the repository.** Nothing carries lessons and taste across projects.
6. **Maintainability is unchecked.** Tests prove behavior, not design; that is the failure mode the talk describes.
7. **One weight fits all.** Either everything gets the full ceremony or nothing does.
8. **Laptop-bound.** Running the same loop headless on a server is an afterthought.

Plumb's answers to each are in [DECISIONS.md](DECISIONS.md): the constraints registry (5), Interface Design (9, 10), hard gates (4), reconcile (in DESIGN.md), Pond as shared memory (3), mechanical checks and lenses (8, 14), tracks (6), and skills plus files (2).

## Packs Plumb builds on

| Pack | What it contributes |
| --- | --- |
| [ciembor/agent-rules-books](https://github.com/ciembor/agent-rules-books) | Classic design and engineering books distilled into agent rules in three sizes, with a compatibility matrix showing which books conflict |
| [nbailo/financial-engineering-skills](https://github.com/nbailo/financial-engineering-skills) | Correctness rules for code that moves money: payments, ledgers, on-chain, exchanges, verification |
| [Cucumber BDD](https://cucumber.io/docs/bdd/) | Discovery, formulation and automation practices; Example Mapping |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | The impact-ranked rule-index shape all language packs follow |
| [leonardomso/rust-skills](https://github.com/leonardomso/rust-skills), [cxuu/golang-skills](https://github.com/cxuu/golang-skills), [trailofbits/skills](https://github.com/trailofbits/skills), [wshobson/agents](https://github.com/wshobson/agents) | Language packs for Rust, Go and Python |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | A ladder that makes agents check the simplest option first, plus a repository audit |
| [tenequm/pond](https://github.com/tenequm/pond) | Lossless storage, semantic search and SQL over every agent session, across clients and machines; Plumb's memory layer |
