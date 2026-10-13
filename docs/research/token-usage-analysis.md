# Dashboard token-usage profile

**Factory + Context's observed input/cache traffic was 2.04 times Superpowers', mainly because it made 277 model calls versus 145.** Its average input/cache traffic per call was only 6.7% higher. This points to reducing unnecessary turns, failed retries and duplicated orchestration before removing quality gates or blaming Context Mode.

This is descriptive evidence from one unequal-time comparison: the original Factory + Context run timed out at 30 minutes and received a separate 15-minute visual continuation; Superpowers completed in 25.8 minutes. Factory's final presentation differed, and neither product passed the later independent persistence review. Context's isolated contribution and human follow-up savings are unmeasured.

## Accounting

Read only `turn-00..09.jsonl` from `/private/tmp/factory-comparison-dashboard-20261012-r4/trials/support-dashboard-factory-context-1`, `turn-00.jsonl` from `/private/tmp/factory-dashboard-extension-20261013`, and `turn-00..03.jsonl` from the matching `support-dashboard-superpowers-1` folder. Deduplicate assistant messages by `message.id` across files; retain the maximum raw count per usage field, rather than summing streamed message fragments. Every unique message is one observed model call. Agent counts are unique Agent/Task dispatch IDs, including nested dispatches, not unique people/processes.

| Run | Model calls | Agent dispatches | Uncached input | Cache creation | Cache reads | Input/cache total |
|---|---:|---:|---:|---:|---:|---:|
| Context original | 190 | 11 | 380 | 677,578 | 11,794,072 | 12,472,030 |
| Context extension | 87 | 6 | 174 | 348,564 | 3,764,492 | 4,113,230 |
| Context combined | **277** | **17** | **554** | **1,026,142** | **15,558,564** | **16,585,260** |
| Superpowers | **145** | **11** | **296** | **490,410** | **7,649,574** | **8,140,280** |

The three Superpowers input classes reconcile exactly to its terminal `model_usage`; its full total is 8,272,040 including 131,760 output tokens. Raw assistant-event output only exposes 5,601 there, so it is demonstrably incomplete. Context's raw output sums (10,961 original; 4,607 extension) are lower bounds, not comparable complete output. Its final output total and cost are unknown. Do not convert this input-only profile into a billed cost estimate: cached tokens and uncached tokens have different prices.

## Original Context run: stage and turn

The stage labels come from the corresponding questions, prompts and agent descriptions. Input/cache totals include root and child messages.

| Turn / stage | Calls | Agents with observed messages | Cache reads | Input/cache total |
|---|---:|---:|---:|---:|
| 00 Triage question | 5 | 0 | 155,729 | 177,596 |
| 01 Triage write / browser-capability block | 6 | 0 | 272,771 | 281,711 |
| 02 Capability reminder / design draft | 7 | 0 | 387,346 | 400,967 |
| 03 Design approval / product draft | 5 | 0 | 353,326 | 369,464 |
| 04 Product approval / architecture research and draft | 17 | 1 | 1,169,313 | 1,218,564 |
| 05 Architecture approval / interface challenge panel | 19 | 2 | 1,567,706 | 1,644,278 |
| 06 Interface approval / slices draft | 5 | 0 | 703,651 | 717,823 |
| 07 Tracer build: invalid test and send-back | 29 | 2 | 1,687,782 | 1,809,499 |
| 08 Tracer rebuild and repeated RED/GREEN proof | 33 | 2 | 2,395,206 | 2,504,305 |
| 09 Details and creation builds; interrupted RED verification | 64 | 4 | 3,101,242 | 3,347,823 |

Intake/gates (00–06) account for **4,810,403** input/cache tokens, or 38.6% of the original run. The failed/retried tracer (07–08) accounts for **4,313,804**, or 34.6%; this includes useful implementation, not exclusively waste. Details/creation account for the remaining **3,347,823**. Turns 08–09 alone contain 46.6% of original cache reads.

The tracer was sent back because `vm.runInNewContext` generated cross-realm seed arrays that `deepStrictEqual` rejected. The retry re-authored the store and performed a new RED/GREEN sequence. The outer step agent then checked out RED and ran the suite again after its executor had already proved RED/GREEN. Similar outer/executor repeated verification occurs later. These are trace-backed rework opportunities; this profile cannot attribute an exact number of removable tokens to each.

The logs also record the shared browser wrapper initially called with a pipe/compound command, followed by the common capability reminder. Superpowers had the same capability problem and received the same reminder. It is not a Factory-specific explanation for the entire gap.

## Extension: root versus task ancestry

Resolve each child message's `parent_tool_use_id` through Agent dispatches to its outermost task. This keeps executor/reviewer descendants inside their owning stage without counting their tokens twice.

| Group | Calls | Agents with observed messages | Cache reads | Input/cache total |
|---|---:|---:|---:|---:|
| Root orchestrator's own messages | 12 | 0 | 537,798 | 580,411 |
| Slice 03 recovered verification | 8 | 1 | 172,514 | 204,471 |
| Slice 04 hierarchy build, including executor | 36 | 2 | 1,703,795 | 1,844,712 |
| Milestone 2 review, including correctness and UI reviewers | 31 | 3 | 1,350,385 | 1,483,636 |

The build and review groups contain 81.1% of the extension's cache reads. Root-only work is 14.1% of input/cache traffic, so removing just the top-level orchestrator cannot close the whole gap. Review produced useful fixes: focus moves to the first invalid field and filter-control heights align. Preserve that independent review, while targeting repeated setup and repeated unchanged-source proofs.

A root Bash command polled `.factory/changes/support-ticket-dashboard/review.md`; the reviewer actually produced `slices/04/review.md` and reported completion. That wrong-path wait contributed to the workflow failing to reach sign-off/reconcile within the extension. A sleeping Bash command consumes wall time without new model tokens during the sleep; do not claim the wait itself explains millions of tokens.

Across the original and extension traces there are 40 distinct Bash command strings mentioning the browser checker, six detached-checkout commands, and ten commands containing `sleep`. These are command mentions, not 40 proven successful browser runs: some include documentation writes or invalid wrapper invocations. The relevant evidence is the duplicated RED/GREEN sequences and artifact polling, not the raw mention count.

## Superpowers comparison

| Turn / stage | Calls | Agents with observed messages | Cache reads | Input/cache total |
|---|---:|---:|---:|---:|
| 00 Plan / execution choice | 5 | 0 | 150,098 | 176,443 |
| 01 First implementer / browser-capability block | 22 | 1 | 811,738 | 867,023 |
| 02 Implementation, task reviews, fix re-reviews, whole-branch review | 114 | 11 | 6,187,956 | 6,590,540 |
| 03 Merge and final verification | 4 | 0 | 499,782 | 506,274 |

Superpowers used four implementers, four task reviewers, two fix re-review dispatches and a final whole-branch reviewer. It did not win by omitting all review or rework. Factory's nested step-agent/executor structure adds another layer around implementation; its architecture research and two interface challengers also precede the build. Those activities can be useful, but this small single-module task paid for them without demonstrating that they caught the later persistence blockers.

## Did Context Mode help, and should we add trimming tools?

The retained Context original and extension traces contain **zero `ctx_` tool calls** and 417 + 222 hook responses. The plugin was enabled and hooks ran, but those facts do not establish that large outputs were routed through its compression/index/search tools. We cannot attribute savings or the token premium to Context Mode. The benchmark now records enabled versus used, deduplicated tool calls and hook responses separately, and explicitly routes large non-browser outputs through Context tools while preserving raw verification logs. The pinned historical runs remain unchanged.

These tools address different costs; their published reduction claims are not measurements of Factory:

| Tool | What it reduces | Decision for Factory |
|---|---|---|
| [Context Mode](https://github.com/mksglu/context-mode) | Tool-output context through execution, indexing and retrieval | Measure actual routing in the existing arm before adding another layer. |
| [trim / llm-trim](https://github.com/deepresearcher08/trim) | Repository/file context selected with AST analysis and a token budget | A candidate for large-repository exploration; compare selected excerpts against full-source correctness. Our current evidence points mainly to call count. |
| [RTK](https://github.com/rtk-ai/rtk) | Output from common development commands | Consider a separate output-filter experiment only if raw output remains material. The browser wrapper already returns bounded summaries and retains full logs plus actual exit status. |
| [llmtrim](https://github.com/fkiene/llmtrim) | API request context through a local proxy, CLI or library | Defer proxy integration: it changes the request path and may affect cache behavior and auth configuration. Test it separately with pinned inputs and quality checks. |

No additional tool or dependency was installed. First compare the revised Factory and Superpowers with the same approved feature/design and stopping rule, then compare revised Factory with and without actual Context routing. Record stage calls, input/cache/output classes, time, independent defects and human follow-up. Only after that should a trimming arm be added, with raw evidence retained and quality failures treated as failures. A shorter returned output is not itself proof of a smaller bill or less follow-up work.

## A 30–50% premium target

At Superpowers' observed input/cache volume, that target is **10.58–12.21 million**, versus Factory + Context's observed 16.59 million. That requires approximately **26–36% less Factory input/cache traffic**, not a 50% reduction. At Factory's current average input per call it corresponds roughly to **177–204 calls**, versus 277. These are planning targets for comparable future runs, not promised savings or billed-cost forecasts.

Prioritize these changes while retaining acceptance and independent review:

1. Consume structured child completion/question and the returned artifact path. Remove open-ended file/state polling and stop extra executor nesting when one foreground performer can produce the same verified result.
2. Validate test harness assumptions cheaply before launching a full slice. The cross-realm equality failure should not trigger rebuilding a useful tracer from scratch.
3. Reuse a recorded proof keyed to the exact source and test revisions. The outer agent checks that identity and evidence, then independently verifies the final deliverable; it need not replay every unchanged RED/GREEN suite in the same mutable checkout.
4. Right-size intake/panels to the task's unresolved decisions. Preserve product/NFR acceptance, a genuine design reference and an independent challenge where there is a concrete risk; avoid paying for multiple broad panels that approve an incomplete persistence contract.
5. Give task agents bounded packets and exact failure evidence. Reduce repeated full-document reads and repeated workspace setup only after measuring which calls carry them; cache reads alone do not reveal whether the material was useful.
6. Keep stronger persistence/breakpoint checks, representative previews and final independent review. Their token cost should be offset by eliminating rework and duplicate orchestration, not by dropping correctness proof.

No before/after benchmark has yet established that these changes achieve the target. Use equal approved requirements/design and a separate decision-quality trial; measure actual follow-up work alongside final quality.

## Reproduce the input accounting

Run this standard-library snippet over the retained folders above. It does not invoke a model or modify products.

```python
import json
from pathlib import Path

fields = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")

def profile(folder):
    messages, agents = {}, {}
    for path in sorted(Path(folder).glob("turn-*.jsonl")):
        for line in path.open():
            event = json.loads(line)
            message = event.get("message", {})
            if event.get("type") != "assistant" or not message.get("id"):
                continue
            record = messages.setdefault(message["id"], {
                "turn": path.stem, "parent": event.get("parent_tool_use_id"),
                "usage": dict.fromkeys(fields, 0),
            })
            for field in fields:
                record["usage"][field] = max(record["usage"][field], message.get("usage", {}).get(field, 0))
            for block in message.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task"):
                    agents[block["id"]] = {
                        "description": block["input"].get("description"),
                        "parent": event.get("parent_tool_use_id"),
                    }
    totals = {field: sum(m["usage"][field] for m in messages.values()) for field in fields}
    print(len(messages), len(agents), totals)
    # Group original messages by record['turn']; group extension by outermost Agent.
    for record in messages.values():
        parent = record["parent"]
        while parent in agents and agents[parent]["parent"]:
            parent = agents[parent]["parent"]
        record["stage"] = agents.get(parent, {}).get("description", "Root orchestrator")
    return messages, agents
```

Not measured: complete interrupted output/cost, repeated-trial variance, or real human follow-up. Cached context volume is traffic evidence, not proof that Context Mode caused waste or that any particular quality gate can safely be removed.
