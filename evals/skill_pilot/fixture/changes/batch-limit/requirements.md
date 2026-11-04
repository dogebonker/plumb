# Batch limit requirements

Source: `../../sources/selected-requirement.md`, selected requirement passage.
Revision: version unknown; captured 2026-11-04. Status: agreed requested delta,
established by the current user request; no separate approval or upstream freshness claim.

> Requests over five items must be rejected before storing anything; preserve accepted behavior for zero through five.

- R1: Requests MUST reject more than five items before any store operation. A six-item
  list or generator raises a limit-identifying error; the store receives zero append calls.
- R2: Zero through five items MUST preserve ordered appends, existing store entries,
  and return counts. Every size 0–5 succeeds for lists and generators.

The current implementation's missing limit is expected before/after drift, not
an unresolved source conflict. Error class is not specified; ValueError is the
local design choice for invalid argument size.
