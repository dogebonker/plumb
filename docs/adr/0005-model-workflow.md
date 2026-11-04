# D05 — Bounded workflow before agents or retrieval infrastructure

Status: proposed, 2026-11-03.

## Options and choice

Compare a naive single model call over diff+docs, a fixed extract/assess/disprove workflow, and a tool-using autonomous reviewer with retrieval/indexing. Use the naive version as the mandatory baseline. The proposed target is the fixed workflow, conditional on measured benefit; no agent framework, arbitrary shell tools, vector database or multi-agent hierarchy is needed.

Force: FR2–FR4 need judgment over unstructured intent; NFR3–NFR6 demand evidence validity, measured quality and bounded cost/time.

Owner: `choose-architecture/references/ai-systems.md`, “Workflow or agent”:

> Use a fixed workflow with predefined code paths when the steps are known in advance.

The reference continues to distinguish open-ended agents; the known stages here do not require one. Primary guidance: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents).

## Proposed workflow

1. **Acquire:** deterministic snapshot/source inventory. No model, network fetch, tests or repo-authored commands.
2. **Extract:** structured normative claims referring to enumerated source passages. Validate quotes and context. Non-normative text and absent intent do not become requirements automatically.
3. **Assess:** compare the bounded evidence packet against applicable claims, preserving authority, exceptions and both document revisions. Candidate mismatches include a concrete behavior/scenario, exact references and uncertainty.
4. **Validate and disprove:** reject malformed evidence in code, then give one fresh bounded prompt the candidate batch and nearby counter-evidence. Retain, reject or mark unresolved per candidate; deduplicate by referenced claim/evidence and scenario. This is one batched call, not a call per finding. Candidates that do not fit the batch remain unresolved and make the report incomplete. A timeout cannot count as disproof passed.
5. **Render:** one validated report, including coverage and unresolved work.

The model sees selected read-only data; it has no tools, credentials, URL fetcher or mutation capabilities. Treat instructions inside docs/code/PR bodies as data. Source precedence and report validity are deterministic rules, not model decisions.

## Provider, budget and failure contract

Start with the official Anthropic SDK using schema-constrained output and strict Pydantic boundary models; retain plain core records. Support only that backend initially. The schema subset, refusal and truncation handling must pass the compatibility trial. SDK defaults do not own retries or deadlines: override them and have one invocation budget. [Official SDK](https://github.com/anthropics/anthropic-sdk-python), [structured-output documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).

Initial admission envelope: at most 3 generation calls, 60,000 total input tokens and 6,000 total output tokens, concurrency 1, 60-second generation deadlines and a 240-second invocation deadline. Token counting is separately bounded and included in the total time. At most one extra retry for an explicit retryable rejection, honoring `retry-after` within the deadline; no automatic retry after ambiguous accepted-request timeout. Refusal, truncation, unparseable JSON, stale evidence, missing usage and spend-cap errors have explicit outcomes. A token/cost reservation is consumed conservatively after ambiguous success. No cheaper model silently replaces the selected one.

These are assumed design ceilings, not benchmark results. Model choice and prices remain versioned run inputs. Strict output formats constrain structure, not truth. A failure to establish a worst-case price bound disables the priced-budget mode or prevents admission; do not invent a cost. Full details are in the [capacity appendix](../research/plumb-intent-forces-2026-11-03.md).

Advisory: DDIA and Release It favor explicit partial-failure handling; restarting a read-only check is simpler than durable orchestration. The AI reference suggests hybrid retrieval at scale; the initial corpus fits bounded full-context trials. Revisit that advice only after measuring actual packet sizes and missed-evidence errors.

Revisit when a controlled comparison improves the quality/cost target: select disproof only if its incremental gain beats its cost; introduce lexical retrieval when real supported packets overflow; add embeddings/reranking only if lexical recall fails a labeled retrieval set. Any added index needs source revision binding and a rebuild path.
