# Historical feature PR benchmark

Measure Factory before adding another skill. Target: 20 real merged feature PRs,
each replayed from its first-parent base in three arms:

The [published 20-PR results](../docs/research/real-pr-benchmark-2026-10-19.md)
include all 60 trials, costs, frozen reviews and grading-recovery evidence.
Its availability note records the subsequent user deletion of the private raw
artifacts; the published measurements survive, with that audit limitation.

| Arm | Instructions |
| --- | --- |
| `bare` | Shared task and provided acceptance tests |
| `claude-md` | Shared task plus a frozen, task-independent repository guide |
| `factory` | Exactly the same guide plus the pinned Factory skills |

The [frozen repository guides](REAL_PR_BASELINES.md) are available for inspection.

Quality decides the comparison. Tokens and wall time are separate columns, with
no cost or time ceiling in the acceptance rule. The provisional quality margin is
10 percentage points over `claude-md`: at least two more accepted tasks out of
20. The initial calibration target was 24; the experiment was reduced to the
user's lower bound of 20 before any feature-model outcomes, to limit first-run
cost. This is one descriptive experiment, not evidence of statistical superiority.

## Corpus and calibration

Candidate PRs come from local Limitless API, Goldengate API and Bitxchange Telegram
repositories. Initial candidates are explored round-robin across repositories.
The final 20 candidates are selected from that calibration pool before seeing
model outcomes, then revalidated after correcting test-support copying. Native
admission evidence is reused only when source, commands, environments and oracle
inputs match; changed test-support bytes require another calibration run.
This is a curated sample, not a random sample of all PRs. A task is admitted only when its PR acceptance tests
fail against BASE for a demonstrated feature reason and pass against the actual
PR implementation. Missing dependencies and broken reference tests are excluded,
with diagnostics retained. New APIs may produce verified missing-symbol/module
failures on BASE; unrelated import and toolchain failures do not qualify.

Every task retains the PR URL, full base/reference SHAs, literal title/body as
requirements, test command, instruction hash and admission logs. Sources are
exported without future Git history or inherited agent instructions. Every arm
receives the same actual PR acceptance tests and strict test-only support files
before implementation. Together with the PR description, these are the disclosed
executable contract, including new API names. Reference production code stays
private. BASE business source plus the provided contract forms each clean starting
commit. Actors may add their own tests but cannot change the provided contract;
grading reinjects its original bytes and checks actor test integrity. Blind review
also checks for test overfitting. Conclusions apply to the disclosed contracts.

The measured scope is offline unit behavior. Integration/e2e checks are explicitly
excluded. Goldengate PR 1002 uses its email-domain matching unit contract; its
Docker-backed auth/workspace tests are excluded and the full feature is assessed
by blind review. The private scope audit preserves every excluded test path.
Node tests use immutable installed dependencies and generate existing
ABI types from the candidate's own inputs. Go uses cached modules but starts with
an empty build cache per actor and grader. Shared caches contain no reference
build outputs. Calibration and grading run inside native macOS sandboxes; file
read and external-network canaries must fail before tests run. Loopback mock
servers are permitted. Same-process deliberate test-runner tampering remains a
review limitation; immutable acceptance files and expected test counts catch simpler
test deletion and skipped-test shortcuts.

## Execution and scoring

Pin `claude-opus-5-5`, high effort, CLI/tool hashes, Factory snapshot and every
input before execution. Force the same model and effort for subagents, and verify
native usage records. Arm order rotates through all six permutations. At most
three cases run concurrently on the same host; each case
retains its assigned arm order. Wall times include that shared-host contention.
No global skills, memory or additional MCP tools are part of the treatment. Factory uses
the existing skills-only execution adapter and a fixed synthetic operator policy;
this does not measure a live human discovery session or the complete hook-based
installation. Unanswerable questions, blocked delivery, timeouts and failed runs
remain in the table.

Each invocation has a 30-minute execution guard and each task allows at most 20
question/resume turns. These limits apply to every arm. Timed-out delivery stays
in the results; incomplete native usage remains unknown. There is no additional
relative token-cost or time ceiling in the quality-margin rule.

All arms receive a clean disposable Git baseline with local Benchmark identity and
signing disabled. The guide and Factory-only lock/pins are installed before that
baseline commit. Factory starts initialized against the pinned snapshot, with no
business profile, gate approval or change plan supplied. Test commands run in their
own disposable source copies using immutable dependencies, so sandbox protection
of the repository's dependency directory does not obstruct the declared command.

Acceptance requires completed delivery, passing acceptance tests, no new Archgraph
violations and blind acceptance. A genuine execution-guard timeout counts as
failure to deliver under the declared treatment when start inventory and isolation
are verified and no infrastructure failure is indicated. Missing final native
usage remains unknown accounting. The launcher applies the pinned root model,
forced subagent model and high effort on every turn; interrupted accounting
prevents exhaustive native verification of every executed model call.
Archgraph compares against each BASE: existing
cycles/debt are reported separately, and default graph analysis does not prove
compliance with an unstated architectural policy. No rules files are supplied:
the meaningful gate is new detected cycles; forbidden/unplanned edge gates are
inactive. Tool exit 2 is an infrastructure error, not a violation. Candidate compile/import errors
count as failed quality only if the reference control still passes; infrastructure
failures leave evidence incomplete.

After each trial finishes, generate anonymous task/source/diff packets. Reviews
may proceed while other trials run. Early review packets must match the final
controller packets and graded-result hashes exactly before verdicts are imported.
A fresh independent
reviewer sees no arm labels, usage, scores or reference implementation. Freeze
verdicts and reasons before unblinding. The coordinating agent already knows the
corpus, so it cannot honestly act as the blind reviewer. Publish the actual review
method with the table. The [review rubric](REAL_PR_REVIEW.md) is fixed before
review and requires concrete material issues for rejection.

Task tokens use the final cumulative native session usage, rather than summing
overlapping resumed totals. Task wall time sums execution turns. Isolation-probe
tokens/time are shown separately; failed probes remain in raw observations. USD
values are native CLI reports, not invoice totals or estimated call counts. Missing evidence is never zero or a
win. Report every task/arm and all exclusions.

CLI 2.1.302 preserves totals across normal process exits and resumes, a change
introduced in 2.1.277 ([official cost-tracking documentation](https://code.claude.com/docs/en/agent-sdk/cost-tracking#accumulate-costs-across-multiple-calls)).
Abnormal termination can leave accounting incomplete; retain that gap explicitly.
Calibration, harness repair and independent review are evaluation overhead,
excluded from implementation-turn metrics. Do not describe those metrics as the
total cost of building and evaluating the benchmark.

The initial diagnostic pilot is excluded from the quality comparison. Its hidden
tests required novel API names absent from the PR prose; Factory initialization
was not seeded; and the dependency overlay could not be created in place. It also
exposed a grading defect involving derived native-agent links under `.tmp`, now
excluded from hashing and test copies. Pilot configuration, grader, results,
inference logs and the grading-only amendment remain archived. The corrected
experiment keeps the same 20 tasks, model and guides, discloses the test contract,
fixes setup, and reruns every arm. No task was replaced based on a model outcome.
Pilot usage is reported separately, with interrupted accounting gaps preserved.

## Commands

Keep corpus references, raw trials and the blind key in a private directory that
actors cannot read. The current private working directory is
`.tmp/pr-benchmark-private/`; do not commit source copies or raw conversations.

```sh
python3 evals/pr_corpus.py --catalog PRIVATE/catalog.json --out PRIVATE/corpus --target 20 --timeout 240
python3 evals/pr_benchmark.py run --manifest PRIVATE/corpus/manifest.json --out PRIVATE/run --model claude-opus-5-5 --effort high --archgraph /absolute/path/to/archgraph
python3 evals/pr_benchmark.py blind-packets --out PRIVATE/run
python3 evals/pr_benchmark.py blind-verdict --out PRIVATE/run --input PRIVATE/verdicts.json
python3 evals/pr_benchmark.py report --out PRIVATE/run
```

`REPORT.md` contains the controller's measured table. Quality requires terminal
results for all three arms, valid treatment/isolation evidence, test and
architecture evidence and frozen blind verdicts. `accounting_complete` and
per-metric coverage are separate. Actual infrastructure or treatment gaps leave
the quality comparison inconclusive. The initial controller coupled accounting
gaps to quality completeness; a reporting-only amendment corrected that after
all 60 inference runs exited. It changed no inference inputs, acceptance scoring,
tasks or the 10pp margin. The original controller, result hashes and earlier
protocol text remain archived with the private run evidence.

Two bare-arm mechanical grading gaps received one supplemental check each after
inference and blind review ended: a candidate/reference test setup failure, and
an architecture-diff timeout. The unchanged candidates passed the pinned checks;
source, tests, tool and original-result hashes matched before and after. The
published recovered quality view is separate from the frozen first-pass table.
No agent attempt, candidate edit or blind-review retry occurred.
