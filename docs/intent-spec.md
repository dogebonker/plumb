# Proposed public contract: intent checking

Status: historical design v0.1, 2026-11-03. These shapes are not implemented APIs.
See the [current reconciliation prototype](../plumb/README.md) for its implemented
module-workspace commands and contract. This proposed diff-review API remains unshipped.
The [skill-first replan](ARCHITECTURE.md) is the current target direction.

## Command surface

```text
plumb check [base..head | base...head] [--json] [--pr-body FILE]
plumb skill
```

Default output is Markdown. JSON replaces the human rendering on stdout; progress and diagnostics go to stderr. Without a range, use the unique merge-base of `origin/main` and `HEAD` through `HEAD`, and print the resolved object IDs. If that ref/history/common ancestor is missing or ambiguous, require an explicit range; do not guess another branch or fetch. Two dots compare the two named trees; three dots explicitly select merge-base semantics. Only committed changes are reviewed in v0.1. Always disclose that staged, unstaged and untracked changes are excluded; do not require a clean worktree or modify it.

An empty diff returns `complete/no_change` with zero model calls. Unsupported files in a nonempty declared review scope prevent a complete result; unchanged irrelevant binary assets need not prevent a supported text review. Explicit scoping can come later without changing these coverage semantics.

Provider/model credentials are operator configuration outside the reviewed source, not a PR-authored command or tool definition. First implementation supports Anthropic only. Provider/model selection and data egress must be apparent before the request. `plumb skill` tells agents these limitations and does not start a server or install a hook.

## Source policy

Discover tracked `README.md` and Markdown under `docs/`, excluding generated/vendor paths. Print/store the discovered and selected paths, not just a count. Compare base/head versions when those sources change. Tests and implementation comments are useful corroboration, not automatically independent normative authority.

Optional `.plumb/sources.json` in the **base** snapshot can set explicit include/exclude paths and precedence. An operator can instead supply a trusted policy file. No YAML parser is necessary for this first config format. Config contains paths and ranks, never executable commands, URLs to fetch, provider credentials or model instructions. Exact precedence is a user policy, not a global hardcoded ordering. A first-time head-only policy is displayed as proposed and cannot grant itself authority. Validate conflicts/unknown fields and record the policy digest.

Without a policy, all discovered sources have equal, unspecified authority. A file being named ADR or saying “Accepted” does not alone grant it precedence. The explicitly supplied PR body is an asserted request with captured bytes and origin; supplying it does not prove agreement. File timestamps are not approval dates. Record unknown dates as null. Never resolve contradictory rules solely by recency or inferred authority.

Sources also carry temporal roles: **baseline commitment**, **proposed head revision**, or **supplied request**. An unchanged baseline promise remains applicable. A replacement at head does not automatically supersede its baseline commitment. Trusted operator/base policy may explicitly permit head replacement of named sources/commitments; only those commitments retire, with the old passage retained as history. A model or head-authored policy cannot invent that permission. Before/after versions alone are not a source conflict: conflicting claims must apply concurrently to the same scenario.

| Case | Outcome |
| --- | --- |
| Unchanged promise; code drifts | Cited code/intent mismatch, with a proposed origin or unresolved origin |
| Spec and code change consistently; replacement authority is unknown | `intent_change` diagnostic and resolution question; incomplete, not an asserted defect/source conflict |
| Operator policy permits the specific replacement; code matches the new promise | No finding for the retired promise; retain the revision diagnostic and assess other active promises |
| Two concurrently applicable promises disagree | Source conflict with both passages |

No new approval service is implied: policy permission or its absence is enough. Non-normative wording changes do not automatically create an intent change. When the model cannot establish whether a substantive revision changes applicability, preserve that ambiguity as incomplete.

## Records and invariants

### Source

`Source` has `id`, `kind` (`repo_document` or `pr_body`), `locator`, `revision`, `content_sha256`, `authority`, `temporal_role`, `declared_date`, and captured UTF-8 bytes. Repo sources retain path, blob ID and tree-entry mode as well as commit. Supplied sources identify their local origin and content hash; a user-supplied URL is metadata, not fetched content.

Only supported text files become source passages. Symlinks, submodules, malformed encoding and size violations become named gaps if required for the declared scope. No silent lossy decoding, URL retrieval, submodule traversal or checkout filters. Source/claim IDs are derived from bound content and spans, not invented by the model.

### Claim

`Claim` has `id`, `source_id`, exact `quote`, byte span, 1-based line span, parent heading/context references, `statement`, and applicability metadata/uncertainty. The statement is a model-produced interpretation; the quoted passage is the evidence. Preserve the surrounding exception/negation, not just a convenient fragment. Claim extraction records examined passages and rejected/ambiguous passages for coverage.

The quote must equal the captured byte span after strict UTF-8 encoding, and its line span must agree with those bytes. Authority is inherited from the bound source/policy; the model cannot assign it. Conflicting claims may both be valid source evidence. Claims not examined by assessment remain visible in coverage.

### Evidence

`Evidence` references a known source passage or a code blob at `base` or `head`, with path, revision, blob/content identity, exact quote and spans. The requested snapshot defines the only permissible repo object IDs. Model responses use enumerated evidence handles; they cannot introduce arbitrary paths, revisions, links or commands.

Code supporting a deletion can exist only at base. A head path/line is required only for evidence that claims to describe head. For a deleted guard or file, include the base guard and the head caller/replacement when available. Pure source conflicts do not require a fictitious code location. Valid source links point to the exact revision when a remote URL is known; local `path:line@revision` is a sufficient fallback.

### Finding

`Finding` has `id`, `kind` (`code_intent_mismatch` or `source_conflict`), `claim_ids`, `evidence`, a concrete `scenario`, `observed_vs_stated`, `proposed_origin` (nullable `code_wrong`, `spec_stale`, `sources_conflict`), a short `reason`, `question`, and `disproof_outcome`.

- A code mismatch requires at least one quoted intent claim and at least one code evidence span. It explains which input/path reaches the alleged difference and what could invalidate that explanation.
- A source conflict requires two incompatible quoted claims and an explicit applicability overlap. They may be passages in separate sources or contradictory passages in one source. Its proposed origin is `sources_conflict`.
- Proposed origin is a hypothesis; null means unresolved. Authority/recency helps formulate a question but does not establish which source is correct. Code/spec origins require a stated reason beyond their mere disagreement.
- A reportable finding has passed syntax/provenance checks and completed the configured semantic assessment/disproof phase. A failed phase can preserve it as a **candidate**, never silently promote it to a retained finding.
- Each finding asks one concrete resolution question. It does not apply code/doc changes, accept waivers, post a review or declare an approval.

Deduplicate on the bound claims, evidence and behavior scenario; do not merge independent consequences just because they quote the same ADR. Fingerprints are deterministic for identical validated inputs; cross-edit identity stability is not promised in schema v1.

### RunReport

`RunReport` has `schema_version`, `run_id`, input identities (resolved base/head/merge-base when used, source and policy digests), tool/prompt/model identities, `status`, `outcome`, `findings`, `candidates`, `coverage`, `diagnostics`, `usage`, and elapsed time. Store the bounded packet manifest/digest; reproducibility means knowing what was read, not reproducing stochastic model output bit for bit.

`coverage` includes declared scope, examined/unread code paths and passages, assessed/unassessed claims, exclusions, unsupported inputs, gaps and per-phase completion. “Examined” requires the content to have been present in a successful request, not merely enumerated by Git; it is still not proof of comprehension. Missing applicable intent is explicit even if the model speculates about expected behavior.

Statuses and shell mapping:

| Status / condition | Exit | Meaning |
| --- | ---:| --- |
| `complete`, `no_change` | 0 | Nothing changed; no model needed |
| `complete`, no findings | 0 | No retained mismatch found within the complete declared scope |
| `complete`, findings | 1 | Human resolution questions remain |
| `error` | 2 | Input/config/preflight failure (including missing credentials/unsupported model) or Git acquisition failure |
| `incomplete` | 3 | After admitted analysis begins: refusal, timeout, quota, malformed/failed response, unresolved authority/applicability, or omitted coverage; valid partial findings may exist |

Incomplete takes precedence over findings. Once model analysis begins, dependency failure is incomplete rather than a preflight error; this keeps API-failure mapping deterministic. Acquisition errors can retain already-produced diagnostics but never masquerade as zero findings. Refusal/truncation/budget exhaustion, invalid evidence on a substantive candidate or unanswered applicability questions must prevent an unqualified complete/no-findings result. A validly disproven candidate is different from invalid evidence or a failed check.

`usage` separates request attempts, provider-reported token classes, known prices, estimated reservation and observed cost. Missing usage/cost is null, never zero. Keep provider request IDs; default logs contain identities/counts/errors, not source text or credentials. Persist raw packets/responses only through explicit operator diagnostics outside the reviewed tree.

## Mandatory boundary cases

The contract tests reject fabricated quotes, out-of-range lines, mismatched blob IDs, unknown references, code evidence taken from the dirty tree, fabricated approvals and silently skipped scope. Cover deleted/renamed files, unusual/newline paths, fenced pseudo-metadata, conflicting dates/ranks, prompt injection, unavailable API, malformed/refused/truncated responses and late/ambiguous timeouts. Markdown and JSON must expose the same retained findings and coverage state.

These tests prove contract behavior. They cannot measure whether semantic mismatch detection is useful; the separate evaluation gate does that.
