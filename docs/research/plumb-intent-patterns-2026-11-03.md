# Patterns evidence for the clean-slate intent checker

Reviewed 2026-11-03 at `2f79d58`. This is a read-only reference-code review under `use-patterns`, not a proposal to preserve the factory. The new checker does not exist yet, so the findings below describe existing code only. Proposed design guidance is separated at the end.

## Findings: ADR evidence and optional architecture adapter

Scope: **4 files, 1,147 lines** (Python: 4 files, 1,147 lines).

| File | Language | Lines |
|---|---|---:|
| `kit/adr.py` | Python | 396 |
| `kit/archgraph.py` | Python | 317 |
| `kit/test_adr.py` | Python | 205 |
| `kit/test_archgraph.py` | Python | 229 |

Excluded: every other repository file from pattern scanning, including generated/vendored `kit/packs/**`, `runner/**`, `hooks/**`, `skills/**`, `bin/**`, `assets/**`, `docs/**`, and `evals/**`. The document authorization/pagination fixtures are product examples, not checker implementation, and were not added to this scope. Within `kit/`, the Python exclusion glob was `{v2_contract.py,runtime.py,v2_gates.py,outcomes.py,usage.py,ci/ci_runs.py,ci/test_ci_runs.py}`. Repository-wide textual caller search was still enabled for PY24, as the skill requires; selected callers and Git policy declarations were also read to judge the findings.

History: **git history available**, not shallow. Each of the four files has two commits: its feature introduction (`a255c85` for ADR evidence; `2ed9925` for the architecture adapter) and the `5cfb977` rename. This is little history: it establishes existence and churn, not independently evolving teams or a maintenance incident.

Not triaged: **none**. Read ranks 1–29: **136/136 hits, 29/29 clusters**, plus every counted list. The triager attributed the second half of `execute` to its nested `native` function; both enclosing bodies were read in full, so that attribution did not reduce coverage. Type checks were manually recognized as parsing despite the triager reporting zero `[boundary]` clusters.

Scan artifacts: `/private/tmp/plumb-patterns-2026-11-03/scan-command.sh`, `scan.txt`, `triage.txt`, `exclusions.txt`. They are temporary audit artifacts, not new product dependencies.

| # | Family | Id | Where | Smell / signal | Evidence | Recommended fix | Confidence | Payoff vs cost |
|---|---|---|---|---|---|---|---|---|
| P1 | DRY | single-source-of-truth | `kit/archgraph.py:81`, `kit/archgraph.py:220` | Git read safety policy copied into two subprocess calls; PY15 plus wider read | Both calls independently spell `core.fsmonitor=false` and `core.hooksPath=/dev/null`, with the same 30-second timeout. `kit/test_archgraph.py:126` checks these options on the helper path only. Two copies of one safety policy, no observed disagreement. | In a new Git reader, define this policy once beside its subprocess invocation. If maintaining the old adapter, share a local argv prefix; preserve streaming stdout for archive. Do not import a factory runner solely to reuse a tuple. | medium: copy counts are factual; coordinated future change is a policy judgment | One place to harden Git execution; one tuple or one private function, no service/interface. |
| P2 | SOLID | srp | `kit/archgraph.py:123`, `kit/archgraph.py:194`, `kit/archgraph.py:215`, `kit/archgraph.py:281` | Long mixed workflow; PY25, PY17, PY16 | `execute` is 174 lines. It combines tool discovery, argument/path validation, current scan/context retrieval, base snapshot materialization and verification, structural comparison, report persistence and terminal output. Tests replace process execution but still need a temporary Git repo (`kit/test_archgraph.py:17`, `kit/test_archgraph.py:53`). Distinct blocks are visible; separate owner/churn evidence is absent. | For the new checker, keep snapshot reading, semantic assessment/evidence validation and rendering as plain functions with data returned between them. If this old adapter were retained, first extract the self-contained base-snapshot block and report formatting; do not split every conditional. | medium: blocks/count are factual, reason-to-change separation is a design judgment | Keeps evidence rules testable without terminal/file output; a few functions rather than an adapter framework. |

**P1 confirmation.** Two copies today: yes. Must they change together: yes if the shared promise is that every Git read disables hooks/fsmonitor and is bounded. Already divergent: no in the two scoped calls. Counter-signals: these are not coincidentally equal values or separately owned published contracts. `git` returning bytes and archive streaming to disk are different operations; that difference rejects a forced unification of their complete subprocess implementations. History: two commits on `kit/archgraph.py`; no demonstrated copy-drift incident. Wider-read declarations at `kit/runtime.py:14` and `runner/plumb_run.py:63` reinforce that this is an existing policy, but they are outside the scanned maintenance scope.

**P1 steps, only if this legacy code were maintained:**

1. Pin both the buffered and streaming Git invocations with assertions about safety options and timeouts; the current test covers only the buffered helper.
2. Introduce a local immutable prefix representing the Git safety policy.
3. Derive the two argument lists from that prefix, retaining their distinct output handling and errors.
4. Run both scoped test modules and inspect the argument assertions.

**P1 target:** `~/.agents/skills/dry-patterns/patterns/single-source-of-truth.md` and `~/.agents/skills/dry-patterns/examples/single-source-of-truth.ts` (installed canonical paths; `~/.claude/skills` is the skill's compatibility spelling).

**P2 confirmation.** More than 80 lines: 174. At least two named result blocks: current context, verified base snapshot, structural diff, persisted report. Different reasons: snapshot safety, tool output compatibility and presentation can vary independently, but the two available commits do not establish separate historical changes. Testing requires I/O: current `execute` tests initialize a Git repo and write artifacts; process calls are patched. Counter-signals: the function is not generated, a mapping table, or just a flat list of calls. Extracting every branch would be worse; the base-snapshot block has a coherent result and relatively few inputs. No performance or defect claim is made.

**P2 steps, only if this legacy code were maintained:**

1. Preserve the integration cases for malformed output, snapshot mutation, missing coverage, links and archive attributes.
2. Extract verified base snapshot materialization behind one private function, preserving its temporary-directory lifetime and all exceptions.
3. Extract report serialization/printing, leaving the command orchestrator to return the result and exit classification.
4. Re-run the scoped tests after each extraction; leave unrelated adapter discovery unchanged.

**P2 target:** `~/.agents/skills/solid-patterns-python/patterns/srp.md` and `~/.agents/skills/solid-patterns-python/examples/srp.py`. Mechanics: Extract Method. No class, Protocol, repository abstraction or GoF pattern is needed.

## Considered and rejected

The following ledger accounts for every ranked cluster; individual hits are preserved in `scan.txt`. Grouping hits with the same counter-signal avoids treating each `mkdir(..., exist_ok=True)` or parsed-field check as a separate finding.

| Rank | Hits | Where / signals | Verdict and reason |
|---:|---:|---|---|
| 1 | 34 | `kit/archgraph.py:189`, PY1/2/3/4/5/11/16/17 | P2 covers the enclosing mixed workflow. Reject Strategy/Composite/Visitor/Builder: a nested command-output helper and snapshot parsing are not repeated interchangeable algorithms; path `parts` and tar `contents` are not a domain tree. Resource `with` nesting preserves lifetime and safety. |
| 2 | 16 | `kit/adr.py:109`, PY2/3/4/16/25 | Reject polymorphism/Builder/long-function split: these are untrusted-manifest checks and one cohesive named-enforcement evaluation. `require_lines` has a real strict caller/test at `kit/test_adr.py:133`; resource scopes explain part of the nesting. It is 85 lines, but length alone is not a finding. |
| 3 | 11 | `kit/adr.py:355`, PY1/3/4/17 | Reject Strategy/OCP: one CLI composition root owns a closed command set. Named arguments, validation and printing belong here. |
| 4 | 8 | `kit/archgraph.py:27`, PY17/20 | Reject DIP: binary/environment discovery is already the infrastructure edge. Tests deliberately patch environment at `kit/test_archgraph.py:221`. |
| 5 | 7 | `kit/adr.py:209`, PY2/4/5/16 | Reject Builder/Strategy: four explicit arguments and a real small-track path, tested at `kit/test_adr.py:109`; no placeholder-heavy construction. Reject Visitor: dict/string validation is a trust boundary. The new CLI should omit factory tracks because its brief omits them, not because this function proves they were invalid. |
| 6 | 7 | `kit/adr.py:276`, PY2/4/5/11 | Reject Composite/Builder: path parts and evidence validation are not tree algorithms; four meaningful required inputs. Preserve missing/unknown evidence distinctions. |
| 7 | 6 | `kit/archgraph.py:123`, PY1/3/4/17/25 | P2; reject command-class hierarchy: command selection is single-site and closed. |
| 8 | 6 | `kit/archgraph.py:57`, PY5/16/17/20 | Reject DIP/Builder: this is the bounded subprocess edge, with an actual test fake and four meaningful inputs. Monotonic clock and sleep implement its own runtime guard; injecting every stdlib call would add reader load. |
| 9 | 5 | `kit/test_archgraph.py:39`, PY3/5/17 | Reject Strategy/Builder/SRP: explicit test double translates the small command set into planted tool output; no production abstraction needs to be added. |
| 10 | 4 | `kit/archgraph.py:297`, PY4 | Reject Strategy: argparse `required=True` is API configuration, not a behavioral algorithm flag. |
| 11 | 4 | `kit/test_archgraph.py:17`, PY4 | Reject Builder: fixture setup uses named platform booleans (`check`, `create`); no ambiguous object construction. |
| 12 | 4 | `kit/test_archgraph.py:218`, PY17/20 | Reject DIP: environment manipulation is the subject of this infrastructure test, not a hidden business dependency. |
| 13 | 3 | `kit/adr.py:194`, PY4/11 | Reject Composite/Strategy: fixed path-shape checks enforce write scope; `existing=True` is named validation policy. |
| 14 | 2 | `kit/adr.py:58`, PY4/16 | Reject nested-conditional rewrite: a directory walk with immediate validation failures; flattening resource/data traversal adds no benefit. |
| 15 | 2 | `kit/adr.py:26`, PY3/4 | Reject State/Strategy: fence open/close is one small parser; its state is local, not replicated across methods. |
| 16 | 2 | `kit/test_archgraph.py:118`, PY4 | Reject Builder: named subprocess success checks are fixture setup. |
| 17 | 2 | `kit/test_archgraph.py:86`, PY5/17 | Reject Builder: test fake preserves the real function's call contract and plants a failure. |
| 18 | 2 | `kit/adr.py:22`, PY4/17 | Reject SRP: deterministic JSON serialization feeds a content digest; it performs no external I/O. PY17 mistakes `json.dumps` for persistence. |
| 19 | 1 | `kit/archgraph.py:94`, PY3 | Reject Strategy: symlink/file/deleted are local snapshot representation cases, not interchangeable business algorithms. |
| 20 | 1 | `kit/adr.py:338`, PY11 | Reject Composite: `Path.parts` checks report placement. |
| 21 | 1 | `kit/test_adr.py:127`, PY4 | Reject speculative generality: test exercises the non-default strict flag. |
| 22 | 1 | `kit/archgraph.py:84`, PY11 | Reject Composite: repository path containment is a boundary check. |
| 23 | 1 | `kit/archgraph.py:114`, PY2 | Reject Visitor: decoded JSON schema validation, not dispatch. |
| 24 | 1 | `kit/test_adr.py:109`, PY4 | Reject speculative generality: test exercises the small-track flag. |
| 25 | 1 | `kit/test_adr.py:185`, PY4 | Reject speculative generality: test verifies that small-track mode cannot bypass the architecture contract. |
| 26 | 1 | `kit/test_archgraph.py:95`, PY5 | Reject Builder: four arguments required by the test fake's replaced function. |
| 27 | 1 | `kit/test_archgraph.py:103`, PY5 | Reject Builder: same function contract; fake plants a source mutation. |
| 28 | 1 | `kit/test_adr.py:37`, PY4 | Reject Strategy: `mkdir` named platform flags, no algorithm variants. |
| 29 | 1 | `kit/test_archgraph.py:53`, PY21 | Reject speculative generality: callers pass different fakes at `kit/test_archgraph.py:92`, `kit/test_archgraph.py:100`, `kit/test_archgraph.py:107`; the override is used. |

Counted lists:

- **PY7:** only `Unavailable(Exception)` at `kit/archgraph.py:23`; this exception class distinguishes unavailable from failed evidence at `kit/archgraph.py:282`. It is not a one-implementation abstract hierarchy.
- **PY15:** reviewed every repeated-literal list. P1 owns repeated Git execution safety. Status/command strings (`check`, `pass`, `fail`, `missing`, `conforming`, `human-verified`) are closed protocol values or explicit test expectations, not a reason to share production constants with assertions. Fixture IDs, paths, code strings and native command flags repeat to set up or assert scenarios. Delimiters, byte modes, SHA widths and chunk sizes have different meanings or already visible units. `120` in the runtime guard and its error text at `kit/archgraph.py:64`, `kit/archgraph.py:67` could be one named duration if that policy becomes configurable; no separate finding is justified for an unrequested option. Current output-size constant is already named at `kit/archgraph.py:20`.
- **PY17:** counts are 28/19/12/9 definitions for `test_archgraph`/`test_adr`/`adr`/`archgraph`. Test count does not establish SRP. P2 covers the concrete mixed function; the module-level file totals are not additional findings.
- **PY23:** two `git` definitions: test fixture helper (`kit/test_adr.py:34`) versus production safe read (`kit/archgraph.py:80`), intentionally different contracts. Two `main` entry points (`kit/adr.py:355`, `kit/archgraph.py:297`) and two `setUp` fixtures (`kit/test_adr.py:12`, `kit/test_archgraph.py:17`) serve different workflows; names alone are not duplicate knowledge.
- **PY8/PY9/PY10/PY14:** no singleton, ABC/Protocol, forwarding-method or trivial-factory hits. Wider read also clears the private `native` wrapper at `kit/archgraph.py:189`: it adds `--no-daemon`, records each artifact and gives every caller bounded execution. It is not a pass-through.
- **PY24:** no dead-code candidates after repository-wide reference counting. No dead-code deletion is recommended.

Signals with no hits: **PY6, PY8, PY9, PY10, PY12, PY13, PY14, PY18, PY19, PY22, PY24**. All other signals are accounted for above. No WEAK candidate is retained: P1/P2 meet the relevant confirm counts, with confidence limited where history/ownership remains judgment.

## Guidance for the new core, not findings about unwritten code

1. **A fixed function pipeline before a workflow framework.** Inputs → claims → relevant code → proposed mismatch → validated evidence → report. `kit/adr.py:229` already demonstrates exact source-digest/quote checks; `kit/adr.py:304` checks source quotes at the pinned commit. Preserve these behavioral requirements through new tests, not by importing the old factory helpers.
2. **A small external-call seam is justified; a class family is not.** `kit/test_archgraph.py:39` and `kit/test_archgraph.py:53` demonstrate why a real process call and a recorded fake need the same call shape. For the new provider call, start with a passed function and validated data. Add a provider adapter only when a second actual provider or a fake makes differing transport behavior real. No registry, abstract factory, container or plugin loader up front.
3. **One authoritative evidence schema.** Define required source revisions, quotes, code ranges and finding categories once; derive validation and JSON output from it where practical. Markdown should render validated findings rather than rebuilding evidence semantics. This applies P1's lesson to the product's core rule, without claiming an existing Claim/Finding implementation was audited.
4. **Explicit absent/unknown results.** `kit/test_adr.py:127` and `kit/test_archgraph.py:57` demonstrate that missing human/tool evidence is not green. A no-op checker or Null Object that silently yields “pass” would violate that contract; absence should stay visible.
5. **Keep resource safety while removing machinery.** `kit/archgraph.py:57` bounds child execution/output; `kit/archgraph.py:223` rejects unsafe snapshots; `kit/test_adr.py:81` checks invented quotes and stale digests. Recreate whichever requirements the new read-only CLI actually needs. Do not port gate statuses, draft mutation, approval authority, slice tracks or archgraph installation provenance merely to inherit these tests.

## Verification

The prescribed Python scan and triage commands completed successfully. All four scoped files and their caller references were read; the report's scope/counts were checked against `wc -l`. `python3 -m unittest kit.test_adr kit.test_archgraph` passed **34 tests in 7.118 seconds** as a reference-behavior check. An assert-based report check validated 66 code references, the 29-row/136-hit ledger and unchanged source diffs for all four scoped files. No source code, fixtures or tests were edited.

This review did not audit the whole factory, model providers, retrieval accuracy or the future CLI implementation. P1/P2 are design lessons, not measured defects or instructions to refactor code that the clean-slate project will retire.
