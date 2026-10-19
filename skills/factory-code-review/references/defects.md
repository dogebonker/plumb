# Defect checklist

Adapted from the user-supplied `bug-review` skill (CodeRabbit-derived checklist). Keep the FC/DI/SA/SP/PS/MQ/DD identifiers in findings. These are review prompts, not proof that a defect exists. Apply DD when documentation/configuration changed; Factory intent conformance still runs for code changes with unchanged docs.

### Functional Correctness

- **FC1 Stale async result.** An async request keyed on a changing input (id, filter, URL, auth scope) must drop its response if the key changed before it writes state (abort signal, request counter, key compare).
- **FC2 Failure shown as success.** A failed, partial, empty or non-2xx result must not render as success or collapse into a default (0, null, "none") through a blanket catch or fallback. Every new `await` or `.then` needs a failure path that resets loading state and tells the user. `finally` alone is not one.
- **FC3 Numeric edges.** For each division, percentage, clamp, float compare or parse, check zero, negative, NaN, Infinity, overflow and unit scale (percent vs fraction, bytes vs MiB).
- **FC4 Parser too loose or too narrow.** Test each new regex, split or substring match against quoting, comments, CRLF, prefix collisions, case, scheme-less or unicode input.
- **FC5 Validation drift.** A changed rule must apply on every path (UI, save, API, mocks). Off-range, duplicate, null, wrong-type and non-integer values must be rejected, and valid ones accepted.
- **FC6 Shared state read after a wait.** State read after an `await`, timer or event (selection, active tab, current record) must be re-read or compared with the captured value.
- **FC7 Incomplete reset.** When something is reset, switched, deleted or restarted, list every cache, storage key, timer, selection and child record tied to it and confirm each is cleared or rescoped. Prefix-based deletes must not hit unrelated keys.
- **FC8 Override not honored everywhere.** When a value can be overridden (env var, flag, option, config path), every consumer must read the override, not a hard-coded default.
- **FC9 Wrong name or reference.** Each new file path, route, key, host, enum value, model id, import or case-sensitive URL must exist and match exactly. Check for code that cannot compile or parse (conflict leftovers, duplicate definitions, missing imports).
- **FC10 Lifecycle and event order.** Timers fire late, effects re-run, responses arrive before mount fetches, reconnect and resume replay events. Verify ordering assumptions hold. When an instance (connection, session, worker) is replaced, callbacks and queued events from the old one must be rejected by identity or generation, not by a flag reset in the same call.
- **FC11 Advertised but not wired.** A route, menu item, option, tool or doc claim needs a working implementation in the same mode. Flag placeholder or hard-coded data presented as real.
- **FC12 Pagination and caps.** List and search reads must follow cursors to the end and must not apply a cap before filtering.
- **FC13 Business rule mismatch.** Compare the logic with the rule stated in the spec, comment or doc (pricing, scoping, retries, settlement).
- **FC14 UI accessibility and locale.** Icon-only controls need accessible names. Drawers need focus handling. Dates and numbers use the active locale.
- **FC15 Branch order for a new mode.** When a new mode or option joins an existing if-chain or switch, check that earlier branches do not shadow it, and compare the order with sibling chains that handle the same modes.

### Data Integrity & Integration

- **DI1 Multi-store write without rollback.** When one operation writes to two places, failure of step N must undo or retry earlier steps.
- **DI2 Non-atomic file writes.** State files are written to a unique temp path and renamed. No shared temp names across concurrent requests.
- **DI3 Duplicate side effects.** Paid, emailed or externally created resources need a stable idempotency key (not a random UUID or timestamp per call). An error after the provider accepted must not trigger a second send.
- **DI4 Key collisions.** Composite identities and cache keys must be unique and unambiguously encoded (`a:b` + `c` vs `a` + `b:c`).
- **DI5 Schema and migration gaps.** Check rollback with existing rows, nullable unique columns, missing foreign keys, and backfill before new constraints.
- **DI6 Cache key misses an input.** Every input that changes the result is in the key. Failures are not cached long.
- **DI7 External contract misread.** Status codes, error shapes, field names and semantics match the provider docs or the pinned SDK version.
- **DI8 Two sources of truth.** When a file, DB, UI list and memory all track one thing, add, remove, external edit and refresh update each of them.

### Stability & Availability

- **SA1 Teardown misses a path.** Every start has a stop on error, cancel, unmount and crash (timers, listeners, workers, PID and lock files, child process trees).
- **SA2 Lock ownership.** Lock or lease release checks ownership. Renewal starts well before expiry.
- **SA3 Retry classification.** Retry only errors known to be safe to repeat. Separate timeout, abort and network error. Stop loops whose cursor does not advance.
- **SA4 Missing timeout.** Every outbound call, probe and poll has a timeout shorter than its caller's.
- **SA5 Hard failure on optional dependency.** A missing optional service, corrupt cache file or absent env var degrades the feature, not the process.
- **SA6 Guard fails open.** Safety checks fail closed when their helper cannot run or returns an unexpected shape.
- **SA7 Deploy config.** Check image versions, rollout on config or secret change, upgrade jobs, hard-coded names and namespaces.
- **SA8 Unbounded growth.** Logs, buffers, temp files and in-memory lists have a bound.

### Security & Privacy

- **SP1 Missing authorization.** Each new route or action enforces auth, role, tenant and object ownership like its siblings. A new bypass (public route, cache, redirect) must not skip it.
- **SP2 Privileged credentials for any caller.** Server-side credentials act only on resources the caller may touch.
- **SP3 Secret or PII exposure.** No secrets in code, URLs or logs. Redaction handles edge input (`@` in usernames, query strings, fragments). TLS verification stays on.
- **SP4 Injection.** User, run or model-controlled values are not spliced into shell, SQL, HTML or prompts without escaping or delimiting.
- **SP5 Untrusted code.** Tools, actions and base images are pinned. Downloaded artifacts are verified before use.
- **SP6 Network exposure.** Local services bind to loopback. State-changing endpoints have CSRF protection. Credentialed redirects are restricted.
- **SP7 Destructive action without target check.** Deletes compare account, project or namespace with the expected one first.

### Performance & Scalability

- **PS1 Unstable dependencies.** Inline objects or arrays in effect deps or props cause refetch or remount on every render.
- **PS2 Heavy work on the hot path.** CPU-bound loops and unbounded reads in a request handler or event loop are bounded or moved off it.
- **PS3 Repeated work.** Full rescans per write, N+1 queries, and resources created per retry without release.

### Maintainability & Code Quality

- **MQ1 Tests that do not prove the claim.** Assertions check exact values, edge input and every documented cause. The test must fail without the fix. Mocks and spies are restored.
- **MQ2 Local quality.** Unused parameters, helpers in the wrong module, and broken project conventions. Report only when it affects correctness or the repo documents the rule.

### Doc and config drift (non-code files only)

- **DD1** Versions, counts and thresholds in docs match lockfiles and code.
- **DD2** Shown commands and snippets work as written.
- **DD3** Behavior claims (atomicity, status codes, supported options) match the code.
- **DD4** Checklists and status rows marked done are actually done.
- **DD5** Links resolve from the file's location. No machine-specific paths.
- **DD6** A fix in one implementation is ported to its siblings and the contract doc.
- **DD7** Manifests and lockfiles declare what the code uses.
- **DD8** Docs do not recommend unsafe steps (disabling TLS, `--insecure`).
