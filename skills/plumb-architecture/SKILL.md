---
name: plumb-architecture
description: Architecture gate of a Plumb change - research facts, fit with the system, NFR budgets, constraints, ADRs.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Plumb architecture

Usage: [per-skill accounting](../plumb-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../plumb-shared/gates.md](../plumb-shared/gates.md). This gate decides how the change fits the existing system. Interfaces come next, in `/plumb-interface`.

Track standard, interactive mode: `/plumb-plan` drafts this document.

## 1. Load

Load the change as gates.md describes, for the `architecture` gate. An approved matching document is complete: skip steps 2 to 5 and continue to the next unfinished stage, reusing applicable security approval. Read `01-product.md` only when architecture is pending. A later research, implementation or review detail belongs in its evidence file, not in approved architecture.

## 2. Research

The Opus lead gathers bounded, cited facts about the baseline before choosing a solution. It may delegate independent read-only questions to Opus subagents when useful and integrates their actual results. Do not claim a task-blind research pass unless a helper actually had that isolation. `research.md` is evidence; the gate hashes `02-architecture.md`, which carries the facts it relies on.

1. Write a `## Questions` list: how the code in scope works today, what calls it, what data it touches, what Pond records about it. Each question names only code, data and records that exist at `change_base_commit`. Compare the list with `01-product.md` and reword any question that names a proposed rule or outcome from it.
2. Keep the questions and answers in `<change>/research.md`. Inspect baseline files with `git show <change_base_commit>:<path>` when the live checkout differs; do not create a worker or worktree for a read-only fact lookup.
3. Use the Opus 5.5 planning lead or explicitly assigned read-only Opus helpers (gates.md, Models) for the bounded research below. Reuse known evidence, wait for actual helper completion and keep unanswered research separate from approved decisions:

   > Answer each question from the repository's code at `change_base_commit` and, through Pond's tools, from sessions dated before `<date of change_base_commit>`. Write answers numbered like the questions. Facts only, each with baseline `path:line` or a Pond session id; write "not found" where the code and Pond are silent.

4. Record questions and answers in `<change>/research.md` in this form:

   ```markdown
   # Research: <slug>

   1. <question>
      Answer: <facts, each with path:line or a Pond session id>, or "not found"

   ## Experiments
   E1. <NFR or C ID it settles>: <what it checks>
       Command: <exact command>
       Output: <the result that settles it>
   ```

   One numbered item per question, its answer indented under it. Gaps become new questions, answered the same way. A resumed run keeps the questions already answered.
5. Read the files the answers point to, and `.plumb/system/`: earlier ADRs bind this change unless it supersedes them, and the rows of the SYS IDs listed in `01-product.md` give their current fit criteria.
6. Apply the project's concise Principles and existing architecture. Only when `design_lenses` explicitly selects an applicable architecture book, load its task-sized excerpt through [../plumb-shared/packs.md](../plumb-shared/packs.md). The profile alone loads no books; do not research design alternatives the task does not need.

Done when every question is answered or marked "not found", and every claim in the Research section of `02-architecture.md` cites an answer or experiment in `research.md`, or a documentation URL.

## 3. Draft `02-architecture.md`

```markdown
# Architecture: <slug>

## Research
Facts from `research.md`, each with its `path:line` or Pond session id.

## Fit
Where the change lives in the existing system, and what it reuses.

## Layout
### <module path>
Pattern: <id>, root: <path>, check: <tool or none>
- `<folder>/` or `<file>`, relative to the module path: <what lives there, and what may not>

Pattern: <id of a frontend root's layout>, root: <its path>, check: <tool or none>
- <its lines, when the module has one>

## Contracts and data
External contracts, data shapes, storage, migrations.

## Flow
The path of one request or event through the system, step by step.

## Budgets
- NFR-01: <promise from product> -> <measurable budget, e.g. p95 under 200 ms on <path>>

## Constraints
- C-01: <constraint> -> rules out <options>

## Threats
Components: <tags from <kit>/security/index.yaml>
Entry points: <each one, with the code that serves it>
Trust boundaries: <each one, with what enforces it>
- T-01: <abuse path against a who-may-see-or-do rule of the product> -> mitigated by <FR, NFR or named test>

## Decisions
### <title>
Supersedes: <earlier ADR, or none>
Context: <forces at play, with references>
Decision: <what was decided>
Enforced by: <archgraph rule `<name>` | lint: `<rule>` | test: `<file> :: <name>` | monitor: `<name>` | human-verified>
Consequences: <what gets easier, what gets harder>

## Open questions
```

- Give each decision an `Enforced by` line using [standing ADR rules](../plumb-shared/adr.md). Code placement/import decisions name an archgraph rule or the stack checker chosen by the Layout Decision; behavioral decisions reuse the named test or monitor of their source constraint, cited by ID. Use `human-verified` only for a decision requiring human judgment. Existing ADRs without the line remain human-verified until reconcile touches them; never backfill an approved document.
- Each decision is an ADR kept inside this document, so the gate hash covers it. Reconcile moves them into `.plumb/system/adr/` once the change's slices are done, before it merges.
- When `.plumb/system/` records no domain-model decision, add one, starting from `domain_model` in `lenses.yaml`: rich domain model or transaction scripts. `keep` means record the model the code already uses. The decision writes its outcome back to `lenses.yaml`.
- Layout gives every module the change creates or adds folders to its lines, one group per root: the backend, and each frontend root (gates.md, Layout). Choose each root's layout as the procedure at the top of `<kit>/layouts/index.yaml` says: an existing convention wins and is recorded as `existing`; otherwise propose rows with their reasons and two exemplars from the pattern file, in the root's stack when it has them. FDA currently has one upstream example and two reference views: disclose that limitation rather than invent independent adoption. Choosing is a Decision. Copy the pattern's Layout lines for the root's stack, each path prefixed with the root's path relative to the module path (no prefix when they are the same); a `cqrs` addition goes under its host as `<host>+cqrs`. The Decision also appends the pattern's layers for that stack, prefixed the same way, after the module's existing `layers` (approval writes them to `lenses.yaml`), names its sibling rules, and picks a checker from `<kit>/layouts/tools.yaml` for that stack with its config written in full from those layers and sibling rules, or `check: none`. For `existing`, the rules come from the module's current `layers` in `lenses.yaml` and any rule the user names, with a baseline of today's violations in the config; with neither, `check: none`.
- For saved user data, Budgets turns each agreed persistence promise into an observable fit criterion and named failure boundary: a failed write, unreadable or invalid existing data, and interleaved writers including an editor opened before another save. Contracts and data identifies the actual persistence dependency and recovery/conflict strategy. Explain the guarantees the chosen storage can provide; do not call browser-local state a durable backup or assume a successful write alone prevents stale overwrite. Any promise the strategy cannot meet is an open question, resolved through the existing gate approval.
- Cite storage, runtime and platform guarantees from their documentation (its URL) or `research.md`. Run an experiment only when a Budget or failure boundary depends on behavior the documentation leaves unclear: at most three per change, each in a temp directory outside the repository. Record each in `research.md` under `## Experiments` with its command, output and the NFR or C it settles; Research cites those entries like any answer. Every other guarantee becomes a test the slices write.
- Track critical: Budgets holds at least one NFR budget.
- Threats: one abuse path per who-may-see-or-do rule of the product, each mitigated by an FR, an NFR or a named test, at most 15 lines. The Security lens routes by the Components line. Track critical writes "see `.plumb/system/threat-model.md`" instead, since `/plumb-security threat-model` runs there.
- When the profile is `domain-core` and a module in scope has no `layers` in `lenses.yaml`, and the Layout Decision does not supply them, decide them: path globs ordered from the innermost layer (the domain) outward. Approval writes them to `lenses.yaml`; review then checks that no file imports from a layer further out than its own.

Before the approval summary, run the [draft conformance pass](../plumb-shared/adr.md) against every accepted standing ADR and SYS row: scripted inventory, then a bounded read of the drafted Decisions and Frozen contracts, at most three evidence-backed conflict cards. Standard planning uses its conductor without an extra model call, as `/plumb-plan` describes. On track critical, reuse an existing fresh reviewer where available; otherwise use one fresh read-only agent. A contradiction without an explicit `Supersedes: NNNN` is an Open question quoting both decisions, answered by the user as `supersedes NNNN` or `withdraw`. Apply the answer only to pending drafts; keep the standing ADR and all approved documents unchanged. Include unresolved conflicts with Assumptions in the summary; record the resolved answer in the draft so its approval hash covers it. A changed draft refreshes this evidence, not compatible upstream approvals.

## 4. Walk the human through it

Follow gates.md **Explain questions and decisions**: recap the goal and relevant answers, then explain each actual architecture choice through what a user will notice. Show the changed behavior or failure in a small flow or before/after table, with a concrete example, recommendation and drawback. Keep internal module names and budgets as supporting detail; ask about outcomes such as "Will your notes still be there on another device?" When Change impact retains this architecture, skip this stage entirely; do not copy new interface fields into it to manufacture a decision.

Present the Decisions first, each with the main alternative it rejects. Then the Budgets, then the open questions. Fold every answer into the document.

Done when Open questions is empty and every NFR and C, its own and the listed SYS ones, has a budget or the options it rules out.

## 5. Approve

Approve the `architecture` gate as gates.md describes. Next skill: `/plumb-interface`; on track critical, `/plumb-security threat-model` first (headless runs skip it until an approver runs it).
