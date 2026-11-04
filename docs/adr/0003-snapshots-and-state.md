# D03 — Immutable inputs, ephemeral derivation, no database

Status: proposed, 2026-11-03.

## Options and choice

Choose Git objects plus captured source bytes and an invocation-local report. Reject mutable live filesystem reads mixed across model calls, a persistent claim database, and dual-writing JSON plus an index as primary state.

Force: NFR3 requires reproducible citation provenance, FR1 is a committed-range review, and no retained-history use case is required.

Owner: `designing-data-intensive-applications/designing-data-intensive-applications.mini.md`:

> Make core trade-offs explicit: source of truth, consistency expectation, retry behavior, duplicate and reordered work, partial failure, data evolution, and whether state is durable, cached, derived, or ephemeral.

## Ownership and consistency

| Data | Source of truth / writer | Lifetime and recovery |
| --- | --- | --- |
| Reviewed code and repo docs | Git commits authored outside Plumb | Read resolved object IDs; never modify |
| Supplied PR body / authority policy | Operator's exact supplied bytes | Capture once, digest, identify origin; no approval inference |
| Claims / evidence selections | This invocation | Derived; recompute on restart |
| Model candidates | Provider response, translated and validated locally | Untrusted derived data; never authority |
| RunReport | CLI; stdout or operator redirection | Versioned, content-bound; no resume database |

Pin base/head once. `A..B` means a direct tree comparison; `A...B` explicitly selects merge-base semantics. Default range selection, if offered, must be printed. A shallow/missing history error cannot silently become a different comparison. Git documents the distinction. [Git diff](https://git-scm.com/docs/git-diff).

Read blobs, not the mutable checkout. Discover paths with NUL-delimited output; bind path, blob ID, tree entry mode and revision. Reject unsupported symlinks/submodules, binary or oversized selected files as coverage gaps. Do not follow symlinks, apply textconv/checkout filters or run external diff drivers. Deleted-code evidence cites the base blob, and renamed files retain both identities. [Git object reading](https://git-scm.com/docs/git-cat-file), [diff helper controls](https://git-scm.com/docs/git-diff).

Git executes as an argv process under a controlled environment, with replacement objects/lazy network fetching disabled and no repository scripts. Git documents these controls; they prevent replacement refs and partial-clone fetches from changing an offline object read. [Git execution controls](https://git-scm.com/docs/git). Repo text cannot select commands. A generic hostile Git installation is outside Plumb's guarantees; supported Git and resource limits are prerequisites.

Read intent from both sides where changed; preserve before/after passages and status. Operator policy comes from explicit trusted input or the base snapshot. No cache exists initially. Any later cache must key on snapshot/source/policy/prompt/schema/model identities, be disposable and expose staleness/rebuild behavior.

Advisory: Release It favors durable recovery for long jobs. These bounded read-only checks can restart, so checkpoints buy little. A timed-out model request may still be billable; stop rather than claiming exactly-once spend.

Revisit when measured repeated derivation is costly enough to justify a rebuildable index, or durable user resolutions become a real requirement. A cache never becomes the authority for source intent.
