# Initial result: feasible, no demonstrated reasoning advantage from the bundle

Ran 2026-11-03 on Pond's Claude Code transcript adapter. Both input forms
identified all five known defects. This pilot does **not** demonstrate that OKF
improves mismatch detection or that maintaining bundles saves human effort.

One raw-source finding also challenged our expected-clean label. Static review
supports its reported code path, but the intended contract needs a maintainer's
decision. It must not be casually counted as a false alarm.

## What actually ran

- Ten committed historical snapshots: before and after five public corrections.
  They are five correlated pairs, not ten independent defects or real PR reviews.
- Twenty independent, serial Claude CLI evaluations: ten original-source inputs
  and ten curated OKF inputs, using the same code, pinned `claude-sonnet-5-5`, low
  effort and fixed output contract. Each CLI result records two assistant turns
  for structured output; twenty CLI evaluations does not mean twenty API calls.
- Production code only, including shared JSONL/adapter code where required;
  corrective diffs and provisional labels stayed out of reviewer packets.
- No Rust build/tests, local models, index, browser, external-doc connector,
  source mutation, tools, MCP access or child agents in the trial processes.
- Original source explanations, curated concepts, exact prompts, raw provider
  JSON, token/cost observations and hashes are retained. The source checkout's
  existing dirty files were not used or changed.

See [the frozen protocol](README.md), [source manifest](data/sources.json),
[actual OKF bundle](data/knowledge/index.md), [machine summary](runs/summary.json)
and [receipt diagnostics](runs/diagnostics.json).

## Results, keeping different questions separate

| Observation | Original source notes | Curated OKF |
| --- | ---: | ---: |
| Known-defect snapshots called mismatch | 5/5 | 5/5 |
| Agreement with provisional labels | 9/10 | 10/10 |
| Answers passing exact source/code quote validation | 5/10 | 10/10 |
| Source quote failures explained entirely by whitespace/line breaks | 5 | 0 |
| API/process failures or unrun cases | 0 | 0 |
| Provider-reported list cost | $1.121106 | $1.088207 |

The apparent 9/10 versus 10/10 semantic difference is entirely the disputed
control. On the other nine snapshots, both arms agree with the provisional
labels. The strict citation score's larger difference is entirely formatting:
the raw explanations are hard-wrapped; five answers flattened those line breaks.
The code quotations in those five responses are exact. The original strict
scores are preserved; whitespace folding is a separately labeled post-run
diagnostic, not a retroactive improvement of the benchmark.

Total provider-reported list cost for the twenty evaluations was **$2.209313**.
The separate authentication/model preflight reported **$0.002412**. These are
list-cost observations, not an invoice or measured subscription charge. Costs
were close in this run; no repeatable cost or latency advantage is established.
All calls completed within the declared per-call bounds. No speedup claim is
made from one pass over this small, varying-context sample.

## The useful disagreement

The disputed fixed snapshot is `638da979433c`, from correction
[`6a05cd1`](https://github.com/tenequm/pond/commit/6a05cd17f0869967d149df42f0b4b961b3d3c0ee).

The original explanation says timestamp-free Claude Code transcripts gate Empty.
Our curated concept said a full-file scan **may** classify them Empty. The raw
reviewer noticed that a nonempty file whose first row lacks `sessionId` does not
reach that full-file watermark check: the shared reader leaves it Opaque/pending.
The bundle reviewer accepted the implementation.

This is exactly the kind of question an intent tool should preserve:

> Should every wholly timestamp-free transcript be considered empty, or should
> malformed/id-less files deliberately remain pending and surface an error?

Those alternatives need different documentation or code. The source also says
undeterminable input remains Opaque, so the correct answer is not established by
this pilot. No code fix or external issue was created. The independent static
[adjudication](ADJUDICATION.md) records the code path and uncertainty.

It also exposes a risk in bundle curation: replacing categorical source wording
with “may” can weaken a requirement. Cleaner documents can make a model's answer
more consistent while concealing an unresolved source/implementation tension.

## What this means for Plumb

The basic reconciliation task is technically plausible: a model can compare
these real implementation snapshots with sourced behavior statements and return
auditable evidence. The raw-documents baseline is already strong on these easy,
retrospective cases. OKF has demonstrated a convenient representation here, not
an independently useful detection capability.

Do not build all the integrations or a complete dependency graph on the strength
of this result. The next test should target the missing value: whether a small,
gradually curated module bundle helps select and preserve the right intent from
noisy or conflicting sources, and whether that benefit exceeds curation effort.
Use documents available before the evaluated change; include at least one real
source disagreement and a maintainer-approved interpretation. Keep the raw-source
baseline. Track time spent preparing and resolving questions as well as findings.

## Limits and verification

This is a deliberately easy retrospective feasibility test. The source notes
describe the corrections and the curator knew the cases. Labels are
analyst-provisional. No prospective holdout, independent human labeling,
maintenance interval, willingness-to-adopt test or human-time measurement ran.
Human curation/review minutes are explicitly null. No product-grade general
precision/recall claim is justified.

Seven focused evidence-boundary tests pass. Ruff checks pass. YAML parsing and
basic OKF/source-reference checks pass; full cross-consumer OKF compatibility is
not claimed. `verify_results.py` re-read every raw receipt, checked the pinned
model, success state, input/protocol hashes, zero trial subagents and exact
evidence, then reproduced the observations. The independent static review
examined the disputed label. Original trial inputs and results were not tuned or
rerun after seeing outcomes.

Recheck without spending model tokens:

```sh
python3 -m unittest discover -s evals/intent_pilot -p 'test_*.py'
python3 evals/intent_pilot/verify_results.py
```
