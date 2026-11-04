---
name: plumb
description: Develop changes from module knowledge and source requirements, using lightweight edits or requirements/design/tasks specs, then verify behavior and update lasting knowledge. Use for spec-driven development, source/code drift, or maintaining service and module contracts.
---

# Plumb

Use the existing coding agent to carry a requested change from source intent to
verified code and lasting module knowledge. Work in the project's language,
tools, and conventions. No Plumb CLI, MCP service, or OpenProse runtime is required.

## 1. Select context and scope

Read project instructions and the relevant service/module knowledge index first.
Follow links for the requested behavior, then inspect implementation, callers,
tests, fixtures, configuration, and public contracts. Load adjacent bundles only
when a dependency or changed contract reaches them.

State the requested outcome, affected modules, preserved behavior, and checks.
Map imports, public APIs, event producers/consumers, shared data, and external
services where relevant. List uninspected or unavailable dependencies explicitly;
an import scan or bundle link alone does not prove the dependency map complete.

Use existing OKF bundles where present. Create one when lasting module knowledge
helps the task; a direct copy edit need not bootstrap a knowledge base. Start
in the project's documentation location: an `index.md` with `okf_version: "0.2"`
YAML frontmatter linking typed Markdown entries. Give each service/module a
bounded entry with `type: Software Module`, its scope, code paths, contracts,
dependencies, source links, and unknowns. These headings are a local convention,
not a claim of additional required OKF fields. Mark unreviewed imports `draft`.
Keep durable knowledge separate from the proposed change; skip empty entries.

## 2. Establish intent and provenance

Read selected repository documents or source material through available,
authorized connectors or local exports. Notion, Confluence, Linear, and GitHub
issues are possible inputs, not built-in capture adapters. A URL alone is not
retrieved evidence; report unavailable material and continue independent work.

For each applicable claim retain the source locator, section or passage, available
revision, and capture date. Record `version unknown` when unavailable; a content
hash identifies captured bytes but proves neither upstream freshness nor authority.
Keep enough original wording to preserve MUST/SHOULD, exceptions, and applicability.
Label paraphrases and inference. Distinguish observed implementation, agreed
intent, imported/unreviewed claims, and proposed behavior.

Resolve apparent differences by checking scope, date, supersession, and existing
governing decisions. A before/after revision or implementation drift alone is not
a source conflict. For concurrently applicable incompatible commitments with no
governing choice, present the passages, concrete scenario, and smallest decision
needed; hold dependent changes while continuing independent work. Record the
actual answer and provenance. Do not request unchanged approvals or invent intent.

When a source changes, compare captured and available material, revisit affected
claims/specs/checks, and invalidate dependent conclusions. Keep unaffected work.
If freshness cannot be checked, report that limit instead of declaring current.

## 3. Choose the smallest change record

For a bounded direct edit, use a brief scope/check note in the conversation or
existing task. A small single-module behavior change with a clear acceptance
example can keep its requirement, approach, and checks in the same note.

For substantial behavior changes, cross-module contracts, or consequential uncertainty, read
[references/change-spec.md](references/change-spec.md) and write requirements,
design, and tasks in the project's change-spec location. Populate only relevant
sections; identify unknowns before executing tasks that depend on them. Reuse a
current spec rather than restarting. Specs record the delta, not current truth.

For a worked direct edit, new behavior, source conflict, or stale-source case,
read the matching case in [references/examples.md](references/examples.md).

## 4. Implement and verify

Use the host agent's normal editing tools and actual permissions; isolate work
where project practice or risk warrants it. Skill text grants no permissions,
sandbox, automatic approval, external write authority, or spending allowance.
Execute authorized reversible tasks without ceremonial approval handoffs.

Use native host reasoning for semantic comparison and implementation. Optional
Plumb `init`, `status`, and `refresh` help capture selected local Git inputs;
inspect the installed CLI help before use. `refresh` updates captures, not agreed
knowledge. These commands do not establish live SaaS freshness.

`check` and `propose` launch extra provider inference and consume allowance. Use
them only with an explicit available allocation; exhaustion stays exhausted across
retries/resume. Otherwise perform the comparison in the host. Inspect existing
receipts before retrying. `apply` is an optional guarded single-file correction,
not the normal multi-file implementation path; use it only within authorized scope.

Run targeted behavior and preservation checks, then applicable project diagnostics.
Inspect the actual diff against intent and affected dependencies. Record commands,
results, and evidence; distinguish pass, fail, and not run with reasons. Repair
in-scope defects and rerun affected checks. Missing proof remains a visible gap.

## 5. Reconcile and report

Update affected module knowledge with verified observations and actual governing
decisions, preserving source references and requirement strength. Keep intended
but unverified behavior labeled accordingly; planned behavior stays in the spec.
Preserve prior decisions or supersession links instead of rewriting history.
External source writeback requires its own applicable authorization.

Report changed code/spec/knowledge files, requirement-to-check evidence, unresolved
decisions, missing dependency coverage, and verification gaps. Report observable
resource use and any extra provider calls; mark unavailable usage unknown. Finish
when the scoped outcome and knowledge update are supported, or report the exact
remaining blocker and safe independent work completed.
