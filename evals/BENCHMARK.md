# Factory versus Superpowers

This comparison decides whether to keep Factory or switch. A modest token increase
(around 15%, as the user's example) is acceptable if the product requires substantially
less follow-up. That example is not an automatic cutoff or a weighted score.

## Measures

- **Product quality:** first-pass and final independent acceptance/regression tests,
  including edge cases. Agent-written tests and completion claims do not establish quality.
- **Completion time:** first delivery and acceptance after repairs, including workflow
  overhead. Blocked, failed and timed-out trials remain visible.
- **Tokens:** uncached input, cache reads, cache writes and output, including subagents.
  Estimated dollars are separate. A runtime probe confirmed resumed `modelUsage` and
  cost totals are cumulative; use the final total, not the sum of resumed results.
- **Follow-up:** failed first-pass tests and repair rounds are proxies. Actual human
  review/follow-up time is a manual measurement, initially unknown. Scripted approvals
  do not measure real review effort or establish production approval integrity.

The user's decision benchmark is a complete support-ticket dashboard: search and
filters, ticket details and editing, creation, saved state, keyboard use and mobile
layout. Browser tests grade behavior; anonymous desktop/mobile screenshots support
visual review. The three small Python cases remain diagnostic coverage. Neither
set establishes superiority for large brownfield changes, migrations, money or
multi-repository work.

## Running

No new Python dependency is required. Check fixtures and the controller first:

```sh
python3 evals/cases/check_cases.py
python3 evals/test_benchmark.py
python3 runner/test_review_resume.py
```

Browser cases require an already installed Playwright module and Chromium. Set
`PLAYWRIGHT_MODULE` to its absolute module directory before fixture checks or runs.
The runner records its exact version and browser path; it installs nothing.

Use a pinned Superpowers checkout and a full Claude model ID:

```sh
PLAYWRIGHT_MODULE=/path/to/installed/playwright \
python3 evals/benchmark.py run --superpowers /path/to/pinned/superpowers \
  --model <full-model-id> --cases support-dashboard --repeats 3 \
  --comparison-mode discovery --operator-policy /path/to/operator-policy.json \
  --out /tmp/factory-comparison
```

Choose the comparison before launching:

- `--comparison-mode execution --approved-spec /path/to/approved.md` gives every
  arm the same frozen, agreed implementation specification. Its content hash and
  text are retained. Approval identity is the synthetic benchmark operator only.
- `--comparison-mode discovery --operator-policy /path/to/policy.json` uses an
  independent fixed persona and preference policy. For example:
  `{"persona":"Offline dashboard owner","answers":[{"match":"storage|persist","answer":"Use local browser storage; no service"}],"default_answer":"Keep the agreed scope; explain any unresolved choice instead of adding features"}`.
  Answers match the question, never the agent's recommendation. An unmatched question
  stops until a real answer is recorded. `--operator human` asks the actual operator
  instead; identical preferences still need to be applied across arms.
- `--comparison-mode legacy-recommended` retains the earlier auto-recommendation
  simulation for diagnostics only. It is never a valid decision comparison.

The controller freezes input text/hashes and the initial per-arm prompt in the output.
Question and decision logs identify fixed policy, legacy simulation and human answers.

For a smoke test add `--cases csv-targets --repeats 1`. Defaults cap each trial at
1800 seconds, $5 estimated cost, 12 scripted questions and one acceptance repair.
Budget estimates may overshoot. The controller terminates process groups on timeout.
Every browser arm may receive one fixed reminder to invoke the shared checker exactly
as supplied. Reports count this separately from product repairs and approval questions.
Never enable broad permission or sandbox bypass to make a failed trial look successful.

Outputs include raw JSONL, questions, provenance, original skill hashes, product
snapshots, harness grading results, separate token categories and a report. Anonymous
source submissions and their separate key support blind product review. Keep raw
outputs outside git; they can contain environment details.

`regrade --out /tmp/factory-comparison` grades unfinished product snapshots without
another model run. The raw workspace includes full `.git`, dirty files and temporary
outputs. Each snapshot records the actual HEAD and branch, refs, RED/GREEN/test
commits and slice checkpoint fields. If execution stops detached at a RED commit,
a descendant committed change branch is exported and graded separately. Raw files
are never replaced by that branch; neither checkpoint is presumed latest or complete.
Historical snapshots lacking Git cannot recover this proof and stay labeled unknown.
Interrupted usage remains a last-observed lower bound.

Live trial/runtime directories and `progress.json` are retained for interruptions.
`resume --out /tmp/factory-comparison --trial <trial-id> --timeout 1800` resumes the
same session and dirty repository, preserving prior workspace evidence. Increase
`--budget-usd` explicitly if the cumulative budget was exhausted. A retained unanswered
question may be answered with `--answer 'actual human answer'`. Resume requires the
original runtime directory and unchanged pinned inputs; it does not reconstruct
missing state. Elapsed execution and per-turn observed usage remain recorded.

Record measured review effort with `followup --out /tmp/factory-comparison --trial
<trial-id> --seconds 120 --rounds 2`. Either field may stay null; scripted answers and
repair counts do not become human measurements. No automatic quality ranking is produced.

## Comparison contract

Both arms get identical requirements, fresh git fixtures, model, effort, tools and
sandbox. Arm order alternates by repetition. Superpowers retains its startup hook;
Factory follows its applicable stages through reconcile, using copied kit and pack
content: the copy is a one-commit git snapshot, and each Factory workspace's
`.software-factory/factory.lock` names it as `dev_path`, with an empty user layer. Missing optional packs remain visible. Pond and automatic recall are absent
from this cold-start comparison. The Factory arm currently compares skills without
the editing gate hook; it does not evaluate enforcement strength.

The controller consumes the root terminal JSONL result rather than waiting indefinitely
for CLI exit; forwarded subagent results cannot finish the root turn. Remaining process
handles are cleaned up before resuming. `CLAUDE_CODE_TMPDIR` points to a short, private,
git-ignored trial directory so agent scratch files are permitted without access to
a shared `/tmp/claude-UID` directory.

Each agent must stop at a choice or approval. The controller uses the selected
shared approved specification or independent operator policy, or an actual human
answer; it records the decision and resumes the same session. Recommended answers
are adopted only in explicitly labeled legacy diagnostics. Local unsigned fixture commits are allowed. There
are no remotes or installs. Read-only local research worktrees may live under workspace `.tmp`, which is within the runtime writable root; remove them after research. These are shared benchmark adaptations.

The copied Factory skills enable automated model invocation, and their copied gate
instructions explicitly accept a recorded simulated answer forwarded to a fresh
step agent. Original skills and production approval rules are unchanged. The root
prompt requests JSON directly; native JSON-schema enforcement is omitted because
it interrupted agents waiting for their reviewers. These adaptations are recorded
in provenance and limit this to an automated skills comparison. Required book rubrics now come from verified `kit/packs/<name>@<hash>/` bundles; missing or corrupt books stop preparation before model execution. Their exact bytes are excluded from path rewrites. Optional nonbook cache misses remain recorded as skips.

Graders and oracles stay outside agent workspaces. After execution, trusted tests
run in a fresh product copy. Agent-generated tests cannot replace them. Python
cases combine original public and hidden tests; the dashboard uses a trusted browser
grader with a fixed check count and screenshots. Starting fixtures must fail hidden
tests; reference implementations must pass. Browser cases allow localhost serving
and browser traffic; external requests and assets remain forbidden.

Grading also applies a native macOS sandbox and a fresh allowlisted environment; it fails closed on other platforms or without `sandbox-exec`. Python grading denies networking; browser grading permits localhost only. Product/runtime writes stay in the disposable grading copy and browser artifact directory. Host home files and regular files outside the explicitly allowed runtime/system roots are denied. Installed Playwright and Chromium are reused; nothing is installed.

Python counts come from a completion receipt written after the supplied suite finishes, rather than product stdout, and must exactly equal the expected count. This rejects stdout spoofing and ordinary early exits. **It is not tamper-proof against malicious Python imports:** tests and product share an interpreter, so deliberately hostile code can manipulate test objects or forge the receipt. Independent source review is required before treating scores from intentionally adversarial submissions as meaningful; separating fixture APIs into a privileged supervisor would require a different harness. Browser product JavaScript executes in Chromium, separately from the Node grading process.

Claude's Bash sandbox blocks Chromium's macOS startup. Every UI arm therefore gets
the same exact browser-check command and isolated RED checker, excluded from that Bash sandbox and permitted
only as an argument-free command. It immediately applies a separate native policy
and runs `node --test` over workspace `test*.cjs` files. Native checks block external
networking, protected reads, and writes outside work; the wrapper and policy are
outside work, explicitly write-denied, and hash-checked. CLI probes confirmed browser
execution in both base and Context configurations and blocked compound-command writes.
With Context Mode, call the shared checker directly through Bash; macOS cannot apply
its profile again inside the already confined MCP executor.

Ordinary Bash permission remains enabled so native executors can run their checks;
the normal Bash sandbox still confines those commands. A native-child probe verified
workspace writing and syntax checks, and CLI probes verified compound commands stay
inside the ordinary sandbox rather than gaining the browser wrapper's exemption.
Scratch and panel files belong under workspace `.tmp`, not a shared global temp path. The prompt supplies `red_test_command`: write `.software-factory/browser-red.json` with exactly `commit` (40 lowercase hexadecimal characters naming an ancestor commit) and `checkpoint` (1–64 letters, digits, `_` or `-`), then invoke the immutable argument-free RED checker through Bash. This request schema is shared by every arm and requires no access to Factory’s kit. It clones locally and retains the live GREEN checkout; both wrapper hashes are checked at finalization.

Technical `measurement_valid` and workflow `comparative_valid` are separate. Inspect
trajectories for actual workflow adherence before treating measurements as a full
workflow comparison. Superpowers completion remains unverified until that review;
Factory state files alone do not establish approval provenance. Unknown or partial
usage never becomes zero, and failed trials must not disappear from the comparison.

## Decision and integrations

Compare quality and follow-up first, then completion time and tokens at comparable
quality. Use three repeats and show individual results. Review anonymous products
before assigning human follow-up time. A tiny smoke test cannot justify a switch.
Add representative changes from the user's real repositories before the final call.

If Superpowers leaves comparable or less follow-up with less time and tokens, switch.
If Factory substantially reduces follow-up at a modest token premium, keep it. Mixed
results support choosing by change type rather than forcing an overall winner.

The completed one-repeat dashboard pilot and independent review are in
[dashboard-benchmark.md](../docs/research/dashboard-benchmark.md); excluded setup
attempts are retained in [pilot notes](../docs/research/benchmark-pilot-notes.md).

Baseline first. `--context-mode /path/to/prepared/plugin` adds a separate arm on macOS.
Dependencies and SQLite/FTS5 must already work: trials never install them. Every MCP
and hook process uses a shadow configuration and a native sandbox that denies external network,
protected reads and writes outside trial/data directories. Main Claude authentication
retains its normal configuration. Neither the policy nor plugin code is writable by
those processes.

The pinned 1.0.169 adapter redirects the executor's OS-temp bypass and readiness
sentinels into private storage; changed bundle anchors fail closed. This is a benchmark
adapter, not a global install. Native tests proved blocked external writes, protected
reads, networking and policy rewriting. A model-free RPC smoke test also proved startup,
SQLite/FTS5, Python execution and unchanged personal Claude settings. Context execution
tools remain outside Factory's Edit/Write gate-hook matcher; this pilot does not prove
production gate enforcement for them.

Browser mode additionally permits the installed browser runtime/cache and localhost
traffic. Native tests proved browser loading with external network and home reads
still denied. An actual MCP browser call passed using `ctx_execute(language="shell")`
to run Node. Importing Playwright inside Context Mode's Bun JavaScript executor
failed under this adapter, so browser checks use the shared Node checker described above.

ECC content can later enter the existing pinned pack mechanism when a measured gap
justifies a check; it must not add another planner or learned-rule authority. Beads
remains conditional on observed scheduling/ownership problems in parallel real work.

References: [CLI](https://code.claude.com/docs/en/cli-reference),
[sandbox](https://code.claude.com/docs/en/sandboxing),
[usage](https://code.claude.com/docs/en/agent-sdk/cost-tracking),
[temporary directories](https://code.claude.com/docs/en/env-vars),
[larger eval research](../docs/research/evals-selection.md).

Context observability records whether the plugin was enabled, whether actual
`ctx_` tools were used, deduplicated tool-call IDs and raw hook responses. Hooks are
not attributed to Context Mode without evidence. Large non-browser outputs are
routed to Context execution/index/search when available; browser checks retain the
shared direct Bash command. Summaries do not replace raw verification evidence,
and usage alone establishes no token savings without matched reruns.

## Codex-only full-stack comparison

Use `--harness codex --codex /absolute/path/to/codex --model gpt-6.1-sol --effort high --cases support-fullstack --repeats 1 --until-complete` with the same fixed operator policy, pinned Superpowers source and installed `PLAYWRIGHT_MODULE`. Both arms choose their stack within the case's launch/API contract. Project-scoped pinned Node/Python dependencies are permitted through the recorded registry allowlist; runtime services stay local. Context is intentionally unsupported in this adapter.

`--until-complete` removes time, price, question and repair caps, as requested. Process errors, policy admission failures and unanswered operator decisions still stop with retained resumable work; Ctrl-C preserves the owned trial. An accepted product must pass independent acceptance after the workflow reports completion. Factory reconciliation and Superpowers finish evidence still require trajectory review before declaring the comparison valid.

Codex starts with project-scoped prepared CLI policy and real local capability probes, rather than Claude plugin initialization. Pinned skills are read as files; tool mappings use actual Codex native interfaces. Browser checks use the declared zero-argument `benchmark_browser.check` and `red_check` MCP capabilities: the immutable bridge invokes the native Seatbelt wrappers outside the actor sandbox. Shell execution of those wrappers is unsupported; the execution-surface mapping preserves command identity and RED/GREEN evidence. Raw root JSONL is preserved. Actual `thread.started` IDs resume each session. Observer-side per-response usage includes discovered child threads, deduplicates response identities, and records unknown coverage. Completion requires each thread's latest owned start/completion evidence; an open child edge means resumable, not necessarily running. Collect final usage after root-process exit and check persistence/shutdown warnings. Shell policy probes and fixed browser capabilities do not establish universal isolation of every possible tool surface; see retained admission limitations.

Requested model/effort is audited in every recorded turn. Installed role TOMLs can override inherited defaults. Future preparation snapshots the inspected installed role preset, preserves instructions and other fields, pins model/effort in immutable copies, and checks hashes before initial commands and resumes. Python 3.11's `tomllib` or an already installed `tomli` parses these files; the adapter installs neither. Metadata records exact coverage and keeps `complete_effective_inventory_verified=false` and `uniform_effort_enforced=false`: higher-priority managed configuration, undiscovered role roots and full forks remain outside this bounded preset. Observed drift makes the uniform-effort comparison invalid; a prompt or root CLI flag is not proof of child effort.

`DECISIONS.md` captures stack rationale and FR/NFR agreements. The grader records verified requirement IDs and predefined user journeys separately from those claims. Cost per accepted application and per predefined accepted journey uses estimated API rates, not self-reported task counts. Actual invoice price remains null; missing usage/model/effort or unresolved child usage makes the measurement invalid, never free. Input includes cached subsets: additive token totals count input plus output once. No cost comparison is valid until both products and accounting are reviewed.
