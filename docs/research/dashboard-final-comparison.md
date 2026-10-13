# Factory + Context continuation versus Superpowers

**Factory + Context has fewer critical findings in the independent review: 0 versus
Superpowers' 1. Both receive REQUEST CHANGES.** Factory has more high/medium findings,
and the extension does not demonstrate a modest token premium or less human follow-up.

[Open the new desktop/mobile comparison](dashboard-images/finished.html).

## Extension result

The user authorized an extra 10–15 minutes for Factory + Context. It received a
15-minute measured Claude session, the same `claude-sonnet-5-5` model, frozen Factory
and Context plugins, and a separate additional USD 5 cap. The session had no terminal
root usage result before its 900.08-second timeout, so exact additional tokens and
USD are unknown. Review time is separate from this model-execution window.

The UI is implemented and passes **15/15 frozen browser checks**. It now has compact
ticket rows, aligned desktop columns, clearer typography, a primary New ticket action,
status/priority badges, and a structured details dialog. At the time cap, the workflow
was awaiting milestone sign-off/reconcile; `reconciled` remains false. This is a working
UI snapshot, not a claim that the complete Factory workflow finished.

| Measure | Factory + Context after extension | Original Superpowers |
|---|---|---|
| Tested UI behavior | 15/15 | 15/15 |
| Experiment time | About 45.1 minutes including original run and recovery setup; workflow pending | 25.8 minutes to accepted delivery |
| Token usage, including cache/subagents | At least 16,705,961 combined observed tokens; exact total unknown | 8,272,040 |
| Independent code review | 0 critical, 3 high, 1 medium | 1 critical, 2 high |
| Architect status | BLOCK | BLOCK |
| Combined review recommendation | REQUEST CHANGES | REQUEST CHANGES |

The token lower bound is over twice Superpowers' completed total. Original Context's
last cumulative result gave 9,238,053 tokens; additional unique messages in its interrupted
final turn contribute at least 3,350,071, giving 12,588,124 for the original run. The fresh
extension contributes at least 4,117,837 more. Raw output counters undercount; these are
lower bounds, not exact totals. The raw input/cache methodology was calibrated against
Superpowers' complete result, where those three categories match exactly.

This is an unequal-time continuation responding to visual feedback, not another matched
30-minute trial. It cannot isolate Context Mode's effect or establish a global winner.

## Important recovery correction

The original timeout snapshot was captured after `git checkout --detach 2acf68a` to
prove RED. The executor had already committed GREEN as `03c6d91`. Its recorded source
transformations were replayed into an explicitly labelled recovery repository because
the original temporary Git repository had been deleted. No original commit identities
were fabricated.

Before any new model implementation, recovered GREEN passed **17/17 store tests and
15/15 frozen browser checks**. Thus the old 11/15 screenshot/source score described a
captured RED checkout, not the best implementation the executor had produced. The
missing creation surface and duplicated Reset setup belonged to that RED snapshot.
The original 30-minute workflow still did not complete its delivery protocol.

The extension preserves its actual Git repository for later inspection. Its additional
work primarily completes the visual slice and internal review, rather than first
implementing ticket creation.

## Independent review

Two clean-context native lanes reviewed anonymous, frozen candidates against the same
brief: a code-reviewer and an architect. Neither received the identity key, prior winner
claims or previous findings. Candidate A was subsequently revealed as finished Factory with Context Mode; B as Superpowers. Candidate hashes remained unchanged throughout review.

[Code review and reproductions](dashboard-review/code-review.md) ·
[Architecture review](dashboard-review/architecture-review.md).

Severity counts come from the code-reviewer, with repeated symptoms deduplicated by
root cause. Architecture findings inform the final recommendation and are not added
again as duplicate issues.

| Severity | Factory + Context | Superpowers |
|---|---:|---:|
| CRITICAL | 0 | 1 |
| HIGH | 3 | 2 |
| MEDIUM | 1 | 0 |
| LOW | 0 | 0 |

**Superpowers' critical blocker:** two ordinary tabs with healthy storage can delete
previously saved tickets. Create a ticket in one tab, then save an unrelated ticket
from the other. The second tab writes its stale whole collection and reduces the
persisted count from 13 to 12. Two tabs also allocate T013 independently, retaining
only the second creation. Factory preserves those sequential cross-ticket operations.

**Shared high issues:** both close dialogs despite failed storage writes, and both
can overwrite recoverable records with seeds after an invalid saved record is loaded.
Write-failure and corrupt-record conditions were deliberately injected in those probes.

**Factory's additional high issue:** an already-open stale details dialog can overwrite
another tab's change to an untouched field of the same ticket. Its store refresh protects
other records but the UI still submits both old field values. Superpowers has this symptom
too, counted under its single broader stale-snapshot critical finding.

**Factory's medium UI issue:** at 601px, the fixed desktop columns leave the title only
15px wide, making the first title about 493px tall. The 360px and wide-desktop checks
missed this breakpoint-transition failure.

The architect additionally reproduced Factory discarding an earlier unsaved creation
when a later creation also encounters write failure: old persisted state displaces newer
memory. This strengthens its persistence blocker, rather than adding another severity
count. Both architecture statuses are BLOCK.

Fresh reviewer verification: Factory **44/44** application/repository tests; Superpowers
**47/47**; each public smoke **2/2**, all with zero skips; JavaScript syntax checks pass.
Those passing suites do not cover the demonstrated failure paths. No review fixes were
applied to either candidate, preserving the comparison.

## Reading the result

Factory has an evidenced advantage against the most severe ordinary-use collection
overwrite in this review. Its extra module and repository tests did not eliminate
persistence and stale-dialog problems. Superpowers completed the workflow more efficiently,
but its 15/15 acceptance score did not establish safe persistence.

The current evidence supports fixing data integrity and Factory's handoff overhead
before declaring either workflow the default winner. No measured human follow-up savings
establish that Factory's much larger observed token cost is worthwhile.

## Accessible artifacts

- [Finished Factory application](dashboard-products/factory-context-finished/app.js), [store](dashboard-products/factory-context-finished/store.js), and [stylesheet](dashboard-products/factory-context-finished/styles.css).
- [Superpowers application](dashboard-products/superpowers/app.js).
- [Extension record](dashboard-review/evidence/result.json) and [recovery provenance](dashboard-review/evidence/restoration.json).
- [Final frozen browser grade](dashboard-review/evidence/final-quality.json) and [recovered original GREEN grade](dashboard-review/evidence/recovered-green-quality.json).
- [Independent reproduction script](dashboard-review/evidence/code-review-probes.cjs) and [raw results](dashboard-review/evidence/code-review-results.json).

Not checked: repeated trials, Safari/Firefox, assistive-technology speech, physical mobile
keyboards, or simultaneous-write stress. Both candidates still have data-integrity blockers;
the Factory workflow remains unfinished despite the working UI snapshot.
