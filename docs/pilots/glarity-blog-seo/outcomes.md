# Glarity pilot: outcomes after merge

The pilot has not merged. Its merge SHA/time, post-merge incident observation,
time to recovery and adoption are **unknown / pending**, not zero. Pre-merge gate
failures and reviewer rejections are not escaped defects. The existing trial report
retains its original measurements; this page adds no inferred production results.

The current [input record](outcomes.json) generates the [pending report](outcomes-report.json).
Its seven-day window is provisional before merge; no outcome has been observed or
window selected after seeing a result.

| Measure | Current result | Evidence needed |
| --- | --- | --- |
| M13: escaped defects per feature | Pending; merged denominator 0, observed denominator 0, rate unknown | Final approved merge SHA/time, stable incident IDs with attribution, and a completed continuously observed window |
| M14: detection-to-recovery | Unknown; no post-merge incident cohort observed | Confirmed incident detection/recovery evidence; unresolved incidents stay right-censored |
| M15: adoption | Unknown; event and eligible population not yet defined | A user-defined successful event, eligible population, observation cutoff and deduplicated adopted/eligible counts |

At final merge, record one feature ID and full merge SHA plus timestamp. Declare
the first incident window before examining outcomes (proposed: the first 7 days,
`[merge, merge + 7 days)`) and the actual monitoring source. A completed calendar
window alone does not prove observation: retain evidence that incidents were
observed continuously from merge through the end. Capture suspected incidents
separately until attribution is confirmed. A repeated report of the same incident
keeps its stable ID; a correction cannot create a second count. Record recovery
when verified, including recovery after the initial 7-day window. Before that,
recovery duration is unknown and elapsed ongoing time is right-censored at as-of.

Keep explicit records in `outcomes.json` and print the report with:

```sh
python3 kit/outcomes.py report --input <change>/outcomes.json
```

The [retro metric definitions](../../../skills/factory-retro/metrics.md)
define the JSON fields and evidence requirements. The helper validates records; it
does not connect analytics, open incidents or supply missing observations. No
adoption event or population is chosen by this page: an educational blog/guide
read, a route click and a completed product action mean different things.

The [published real-PR benchmark](../../research/real-pr-benchmark-2026-10-19.md)
remains the honest delivery-quality baseline: accepted tasks were 14/20 for bare
agent, 14/20 for agent + a good CLAUDE.md, and 9/20 for sequential Factory. It does
not measure this swarm's production defects, recovery or adoption. Retain the
good-CLAUDE.md control and show cost, tokens and wall time separately. A production
comparison requires comparable features, incident definitions, surveillance and
windows; none exists yet. No new benchmark calls are implied.

Raw evidence from the original benchmark and first pilot trial was deleted by the
user; the published reports describe the resulting audit limitation. Outcome
records collected after an eventual merge must retain their own evidence and must
not pretend to replace those missing raw logs.
