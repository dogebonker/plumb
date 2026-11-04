# D04 — Deep functions and inward dependencies

Status: proposed, 2026-11-03.

## Dependency decision

Options: SDK/CLI-shaped core; full ports-and-adapters framework; a few inward-facing functions over plain records. Select the last.

Force: FR1/FR5 use the same report, and NFR3 must be testable without network or a provider SDK. `intent.py` owns evidence invariants; `check.py` receives a snapshot and one model-call function. Git/model/config/rendering stay outside policy. The CLI constructs dependencies. The supplied function has a real deterministic test double; an abstract provider hierarchy does not.

Owner: `clean-architecture/clean-architecture.mini.md`:

> Pass plain request and response models across use-case boundaries. Do not pass web requests, framework contexts, ORM rows, database-bound structures, or framework response objects into or out of core policy.

Revisit when more real callers/providers require an expanded interface; concrete SDK types still remain at the edge. Enforce the chosen dependency direction with a small import-boundary check in CI, not merely this diagram.

## Interface-depth decision

Expose a small external operation: `check(snapshot, intent_sources, model_call, budget) -> RunReport`. This is a **proposed signature**, not an existing export. Construction and options belong at the CLI edge; callers do not manually order extraction, assessment, validation and disproof.

Owner: `a-philosophy-of-software-design/a-philosophy-of-software-design.mini.md`:

> Prefer deep modules: small, semantic interfaces that hide meaningful internal complexity. Reject pass-through services, thin library wrappers, helper modules, and tiny split-outs that add names without reducing reader burden.

Force: one person should be able to understand and test a check without holding provider protocol, Git path rules and prompt sequencing in mind.

| Seam | Rating and reason |
| --- | --- |
| CLI → check | Deep: one complete use case hides sequencing and honest partial outcomes |
| Snapshot reader → snapshot records | Deep: hides commit/path/mode/size and source binding complexity |
| Evidence validation → accepted finding or diagnostic | Deep: localizes quote/range/revision/relationship invariants |
| Provider → model-call function | Useful narrow seam: hides protocol, refusal and usage translation; real fake exists in tests |
| Renderer → Markdown/JSON | Intentionally humble presentation functions, not new service layers |
| Generic source/provider plugin registries | Shallow today: speculative setup/configuration without demonstrated variation |

Advisory: Clean Architecture names ports and interfaces; KISS prefers the smallest realization. Functions and concrete records satisfy the dependency rule without a container, abstract base class, generic repository or factories. The bounded [pattern report](../research/plumb-intent-patterns-2026-11-03.md) provides existing-code evidence, not an instruction to port old modules.

Revisit when changing one external mechanism forces policy edits or duplicates a rule across real callers. Extract at that pressure point; do not prebuild extension points.
