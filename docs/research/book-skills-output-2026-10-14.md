# Book skills and output

The completed full-stack pair does not establish that book skills improve output. The globally installed book skills existed under `~/.agents/skills/`; they were not missing from the user's machine. Factory's benchmark copied only its separately pinned `~/.software-factory/packs/<name>@<hash>/` cache. The frozen r2 provenance records **0 installed and 35 skipped pinned packs**, including APoSD, refactoring and Clean Code. Generic correctness, design, efficiency, UI and security reviews still ran, so this benchmark cannot assess the advertised book-rubric contribution. Preparing the pinned cache before freezing the snapshot was a benchmark setup omission.

Useful principles can shape an implementation contract: hide volatile decisions behind a small interface; keep domain policy independent of HTTP/UI; commit state and history atomically; preserve drafts and observed versions; name code around the domain. This is a reasoned recommendation, not an experimental finding that adding book text improves an LLM. Ousterhout's primary teaching emphasizes functionality behind simpler interfaces and information hiding; Fowler warns against speculative complexity. [Managing complexity](https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=complexity), [YAGNI](https://martinfowler.com/bliki/Yagni.html).

Recommended usage:

- Select at most the profile's relevant short rules; preserve task/runtime constraints over stylistic doctrine.
- Give one reviewer a coherent rubric and require file/line evidence for consequential findings.
- Treat Clean Code naming/small-function guidance as heuristics; do not split working code solely to meet a line count.
- Require architecture layers when they reduce coupling or protect an actual boundary. A small CRUD service does not need a rich domain model by default.
- Keep correctness/security/data-loss and executable acceptance checks even when a stylistic rubric is skipped.

A convincing claim about output would require a matched ablation: the same tasks, model/effort, tools and budget, rubric off versus on, blind quality review and total cost including repairs. No such ablation was run here, so there is no claimed quality uplift or token saving.


Availability checked again on 2026-10-14: all 35 current pinned cache directories exist, as do the global book skill files. The r2 provenance file was created at 2026-10-13 21:02:40 UTC; the current pinned APoSD cache directory was created at 2026-10-14 00:43:36 UTC, while its global skill directory dates to 2026-09-10. These timestamps support the late cache preparation explanation; they do not identify who populated it. The immutable benchmark snapshot did not receive later host-cache contents. Historical provenance/results remain unchanged.

The historical r2 loading rules required the project-pinned cache and forbade substituting a same-name global skill. The current [packs.md](../../skills/factory-shared/packs.md) also accepts matching framework-bundled book trees. Snapshot preparation: [benchmark.py](../../evals/benchmark.py) copies only existing pinned cache directories and records missing ones as skips. Before another benchmark claiming book-enabled Factory behavior, prepare and verify the selected pinned rubric files in the snapshot; silently skipping all packs is insufficient.


Fix completed: all ten currently pinned book packs now ship in `kit/packs/`, 40 full/mini/nano/skill files totaling 310,183 bytes, with the upstream license outside the exact trees. Each tree was verified against its Git pin. A real isolated snapshot prepared with an empty host cache included all ten books and all tiers, launching no models. Fetch/install checks, 51 benchmark tests and independent code/architecture reviews passed. Required book absence/corruption now stops preparation. Ordinary loading stays offline; upstream pin maintenance explicitly bootstraps its source mirror. Older immutable framework versions and historical benchmark artifacts remain unchanged. No book-enabled full comparison has been rerun.
