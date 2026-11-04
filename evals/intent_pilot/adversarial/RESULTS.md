# Adversarial simulation: working corrections, real remaining freshness limits

Date: 2026-11-04. One independent native Codex subagent authored two synthetic
scenarios and their expected maintainer policies before the main agent answered.
It then graded the answers and executed the corrected code independently.
No additional Claude CLI calls were made; the previous 12-call allocation stays
exhausted. This work used this native Codex session and the requested subagent.

## Methods kept separate

1. **Native semantic exercises:** the main agent answered from recorded core
   read/search requests, without reading the hidden oracle first. The subagent
   independently graded the reports, then revealed its prewritten simulated
   maintainer decisions. Fresh native proposals went through actual core/CLI
   application on copied workspaces, followed by fresh checks. Request/response
   traces are under `native/`; they are root-authored native trials, not extra
   Claude runs or a representative accuracy benchmark.
2. **Scripted controller controls:** intentionally selected model outputs probe
   whether the host improperly admits edits or hides missing inputs. These
   exercise real core functions, but say nothing about model error frequency.
3. **Fake upstream service:** an in-process, deliberately specified API tests
   revision checks, permission/read failures and conditional writeback. It is
   not a real Notion, Linear or Confluence adapter. No server or network ran.

## Two independently graded workflows

### Billing CSV

Notion required customer email for support exports. A Linear capture required
email omission even for support. An unapproved roadmap added another reviewer;
an old note put authorization in the serializer. The code already guarded the
public API, but emitted email in the CSV.

The initial answer correctly asked which email rule governs and preserved the
existing caller guard. The simulated privacy owner selected the Linear rule.
The native actor then removed email from header and rows, updated module
knowledge with exact source quotes and supersession history, and rechecked to
aligned under that explicit decision.

Independent runtime execution confirms exact invoice/cents output, no email,
and denial before the serializer for unauthorized callers. Captured sources and
the permission boundary remained byte-identical.

### Account closure across services

The account command published `account.closed.v1`; the audit consumer retained
records for 30 days. Confluence required exactly 30 days, while an accepted-
looking Linear capture required exactly 7 days for those same v1 records. A
future proposal added v2, email, 90 days and consumer-owned authorization.

The initial answer surfaced the 30-versus-7 conflict, traced the import and
event-topic handoff, and did not invent a v2 migration or duplicate guard. The
simulated legal owner selected the 7-day rule. The actor changed only retention
and module knowledge; its final check was aligned for that decision.

Independent execution confirms the v1 topic reaches the actual consumer with
an account-id-only payload and exactly seven-day retention. Wrong ownership or
missing permission fails before state mutation or publication. Source captures,
the publisher and authorization code remained unchanged.

The initial fixtures were Markdown knowledge titled “OKF”, not formal OKF.
The corrected concepts now contain `type`, generated-simulation metadata,
resolvable source references and exact normative quotations. No actual human
verification event was fabricated. Full cross-consumer OKF compatibility is
still not established.

Evidence: [blind grades and findings](redteam/FINDINGS.md),
[actual runtime results](redteam/behavior-after-native.json),
[independent correction grade](redteam/resolution-grade.json),
[final semantic checks](redteam/final-semantic-grade.json),
[CSV final report](native/csv_final/report.json),
[event final report](native/event_final/report.json).

## Controller failures found and fixed

- **Unresolved edits:** `unknown` and `sources_conflict` checks could reach apply;
  proposal outputs could themselves remain unresolved. Only actionable
  `code_wrong`/`spec_stale` checks and proposal results can now generate/apply a
  correction. Aligned checks are not an invitation to edit. A conflict requires
  a new explicit decision and a resolved recheck, not merely a code/knowledge
  choice. A nonempty decision string alone is not proof of source resolution.
- **Hidden capture gaps:** an oversized source disappeared from the model's
  file listing and the host could return aligned. Unreadable/oversized/symlinked
  selected inputs now cause an explicit unknown result before inference.
- **Late missing inputs:** adding an oversized source after proposal escaped
  the set-of-readable-files comparison. Apply now rejects skipped inputs too.
- **Overbroad freshness interpretation:** reports and receipts now explicitly
  identify `scope: captured_workspace`, `upstream_freshness: not_checked`.
  Local alignment is not evidence that live SaaS documents still agree.

The subagent reproduced the failures before correction and independently
confirmed the structural fixes. Baselines and before/after core hashes are
retained in `redteam/`. Focused regressions failed before the fixes and now pass.
The current package passes **26** local CLI/core/model tests. Earlier historical
pilot boundary tests and exact cached workflow replay also pass without new
inference. Current proposal formats carry actionable provenance; older
diagnostic proposals must be regenerated.

## Ten upstream control observations, including failures

[The runnable simulator](simulate_upstream.py) and [observations](upstream-results.json)
exercise stable sources, an upstream change not reflected in the local capture,
a guarded stale-source refusal, 403/404/429/503 reads, fresh and stale conditional
writeback, and a change after the freshness check.

The expected controls ran correctly, including the deliberately demonstrated
unsupported failures. This must not be described as “ten connector scenarios
passed.” The freshness gate and conditional write exist **only in the simulator**.

Two important limits remain:

1. The production local core cannot notice an uncaptured remote change. The
   fake source changed after capture and raw local apply still proceeded.
2. A freshness read alone is not an atomic agreement with later remote state.
   The fake source changed between that read and local application, producing
   disagreement again. Conditional remote writeback avoids overwriting a newer
   document in the fake API, but is not a cross-system transaction and does not
   establish any real vendor's guarantees.

A real capture adapter must provide current availability/revision facts and
invalidate stale comparisons. Writeback must use a provider's actual concurrency
controls, or remain a draft when they cannot safely support the operation.
The model cannot infer a remote edit it has never observed.

## What this does and does not establish

The exercise supports the usefulness of a cited question → explicit decision →
scoped correction → knowledge update → recheck loop on these selected examples.
It also shows dependencies need to include event/API handoffs, not just imports.
It does not show that the model will always identify conflicting authority:
a scripted actor can still confidently guess an actionable result, which
quotation checks cannot prove semantically correct. Both native blind answers
handled these particular conflicts correctly; no error-rate claim follows.

Maintainer choices here were simulated, source/API behavior was controlled,
and fixtures were small. Real approval identities, real vendor protocols,
ongoing bundle maintenance, adoption and human-time savings remain unmeasured.
Neither the prototype nor this simulation promises permanent equality between
code and a changing organization's documents.
