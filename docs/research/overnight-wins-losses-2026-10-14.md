# Where Factory won and lost — 14 October 2026

For the observed neutral full-stack task, Superpowers is the efficiency winner. Factory's extra process delivered some stronger checks and one fewer HIGH review finding, but no demonstrated human-follow-up reduction that justifies its cost. Both products need repairs after external review.

| Observation | Factory | Superpowers |
| --- | ---: | ---: |
| Completion | 4h 02m 06s | 32m 46s |
| Recorded-usage API estimate | $36.07 | $1.90 |
| Questions | 18 | 3 |
| Model responses | 1,748 | 86 |
| Child threads | 40 | 2 |
| Trusted first-delivery checks | 19/19 | 19/19 |
| External CRITICAL / HIGH / MEDIUM findings | 0 / 0 / 2 | 0 / 1 / 1 |

**Factory's strengths:** stronger schema/data-audit checks and explicit persistence promises; independent internal acceptance caught Unicode and control-size defects before delivery; compact rows and short ticket IDs; complete decision/constraint records. The professional visual direction is a preference, not a measured architecture or usability win. Its two remaining MEDIUM issues were malformed/deep JSON returning HTML 500 instead of JSON 400, and focus returning to New Ticket after a details save.

**Superpowers' strengths:** 7.39× faster and 19.02× cheaper on the recorded API estimate; much less coordination; a clearer HTTP/domain separation; stronger draft/conflict recovery and details hierarchy. Its remaining HIGH issue was trusting a malformed 201 response as successful creation, closing the dialog without confirmed persistence; its MEDIUM issue was a UTF-16 title limit inconsistent with the server's code-point limit. Both architectural reviews were WATCH.

**Equal:** all 19 trusted checks and five predefined journeys passed at first workflow delivery. Both recorded the shared FR/NFR agreements, SQLite and vanilla JavaScript. Flask versus standard-library HTTP was a real different decision. No observed Superpowers read of Factory documentation was found in the contamination audit.

The biggest cost buckets were main orchestration/direct work (39.8%) and milestone review (36.0%); implementation was 15.5%. Cheaper implementation models alone cannot close this gap. The development simplification removes the executor wrapper and four-general-reviewer panel, reduces routine questions and repeated reads/checks, and preserves independent review plus actual final acceptance. None of those policy changes proves a 60–90-minute complete delivery yet.

This was one constrained task with a Python starter and unequal observed child effort (Factory had 68 medium responses despite requested high). It is not a valid uniform-effort or blank-slate architecture experiment. Prices are API-rate estimates, not verified invoices; human follow-up minutes were not measured. There is no general winner claim.

Evidence: [full comparison](codex-fullstack-benchmark-2026-10-14.md), [gallery](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/gallery.html), [code review](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/independent-code-review.md), [architecture review](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/independent-architecture-review.md), and [contamination audit](/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/contamination-audit.md).
