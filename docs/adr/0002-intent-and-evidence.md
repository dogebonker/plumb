# D02 — Explicit intent, evidence and human resolution

Status: proposed, 2026-11-03.

## Classification decision

Options: a general AI reviewer; a generic document-retrieval product; a focused intent checker. Select the checker. The Core is deciding what stated promises apply and producing auditable mismatch questions. Source acquisition and evaluations support it; SDK/CLI/rendering are Generic. Full tactical DDD does not fit a short-lived command.

Force: FR2–FR4 and NFR3/NFR4. A plausible but unsupported finding costs trust; authority errors can falsely accuse either code or specs.

Owner: `domain-driven-design-distilled/domain-driven-design-distilled.mini.md`:

> Put the most modeling effort into the Core Domain. Keep Supporting and Generic Subdomains simpler unless their own complexity proves otherwise.

Revisit when a genuinely new capability needs different language, authority rules or users; do not turn model/provider concerns into business contexts.

## Domain-logic decision

Options: unvalidated dictionaries throughout; a rich entity/aggregate system; a few immutable records with validated invariants plus a use-case function. Select the last. Source/Claim/Finding/RunReport are the shared vocabulary. The core validates evidence relationships; the use case sequences work. No transactional aggregates, repository abstractions or domain-event bus are required.

Force: NFR3's never-invent-citations contract and FR3's uncertainty. These are real invariants; no persistent entity lifecycle exists.

Owner: `patterns-of-enterprise-application-architecture/patterns-of-enterprise-application-architecture.mini.md`:

> Choose the business logic pattern by force: Transaction Script for short independent simple flows, Table Module for table-centered set logic, and Domain Model for significant rules, invariants, identity, lifecycle, or collaboration.

Advisory: Clean Architecture calls for independent rules; that is satisfied by plain records/functions, not by adding layers. KISS rejects full aggregates or factories without a second real variant.

Revisit when durable human resolutions introduce a lifecycle; only then consider entities and persistence.

## Semantics

The [contract](../intent-spec.md) treats `code_wrong`, `spec_stale`, and `sources_conflict` as **proposed origins**, not authoritative truth. Null is permitted when origin cannot be responsibly inferred. A human chooses what to change; this release applies nothing.

Authority is explicit metadata from operator-selected policy. Equal-rank, concurrently applicable incompatible claims remain a conflict; recency alone cannot authorize a policy change. A PR body is an asserted request, not proof of approval. Both base and head document changes remain visible with baseline/proposed temporal roles. Before/after versions alone are not a conflict. A matching code/spec revision with unknown replacement authority yields an intent-change diagnostic and incomplete question; trusted policy may allow a specific head replacement and retire only that baseline commitment. Do not promote a head-authored config or self-declared “accepted” passage into operator authority.

A missing applicable claim becomes a coverage gap. A source conflict needs two passages; a code mismatch needs at least one source passage and code evidence at a pinned revision. Citation validation establishes provenance, not applicability, reachability or correctness. No numeric “confidence probability” is emitted without calibration.
