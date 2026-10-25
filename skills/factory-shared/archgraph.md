# Archgraph evidence for review

Use the Layout Decision's Pattern line. Archgraph supplements a previously selected stack checker; it replaces that checker only when the Decision explicitly chooses it. The pinned install and checker commands live in `kit/layouts/tools.yaml`: source commit `49464a7ec19fe8402b4258e751f7ba050c6eff19`, built with `--locked`. Version `0.1.0` alone does not identify this build. Record the binary SHA-256 alongside the source pin. Do not install skills or MCP to run these commands.

If absent, report **skipped** with the exact install line from the registry. Preserve the adapter's checks and ordinary reviewer reading order; absence is not a clean verdict. A command error, unresolved import, incomplete symbols or stale graph is a limitation to report, not evidence of conformance. The native engine is experimental.

## Shared adapter

Build, milestone review and standalone code review use `python3 <kit>/archgraph.py`.
It resolves the immutable Cargo installation and records its binary checksum;
`ARCHGRAPH_BIN` additionally requires `ARCHGRAPH_SHA256` and is labelled a
caller-verified artifact rather than independently proven source provenance.
`doctor` checks availability without scanning or calling a model:

```sh
python3 <kit>/archgraph.py doctor
```

Prepare context before building a slice, and again for the final review snapshot:

```sh
python3 <kit>/archgraph.py prepare \
  --repo <absolute-repository-root> --root web --language typescript \
  --base <recorded-base-sha> \
  --files web/src/orders.ts web/src/orders.test.ts \
  --task 'Implement the approved order behavior' --budget 8k \
  --rules web/layout.yaml --out <absolute-outside-repository>/context
```

`--root`, `--rules` and every `--files` value are repository-relative; root defaults
to `.`. Language is `typescript`, `python` or `go`. Omit `--rules` to detect the
module's `layout.yaml`; missing rules remain a disclosed policy gap. Output must
be a new or empty directory outside the repository. Reports retain source bytes'
fingerprint, commit, base when supplied, dirty status, tool identity, complete seed
list, missing/outside-module files, context omissions and native limitations.
Eight thousand estimated context tokens is the default, not a provider-token cap.
Pass the report path and relevant reading-order entries; do not paste complete
graphs or duplicate source into every helper's prompt. Filter helper context to
its permitted reads. The full reviewable-file list remains the coverage checklist.

For Python monorepos, select a package explicitly when detection is ambiguous
(`--root . --language python --package kit`, for example). Package selection is
recorded and identical at both gate endpoints. Preparation preserves unscanned
seeds without pretending their dependencies are known; a mechanical check rejects
changed source missing from its graph. It derives changed and untracked files from
the explicit base when `--files` is omitted. Use another module/package or the
selected stack checker to cover the remaining files, rather than narrowing a
scan until it passes.

Where the approved Pattern selects archgraph, run its regression gate:

```sh
python3 <kit>/archgraph.py check \
  --repo <absolute-repository-root> --root web --language typescript \
  --base <recorded-base-sha> --rules web/layout.yaml \
  --out <absolute-outside-repository>/architecture-check
```

This compares a verified Git-base snapshot with current working source, using the
same current rules and inclusion options. It fails new forbidden edges, cycles
and unplanned edges. It never rewrites rules, approved documents or source.
Existing baseline debt remains separate; an absolute-clean final gate still uses
the existing full check. Other selected stack checkers stay in place.

Exit `0` means `available`/`prepared` for discovery/context, or `pass` for a check;
exit `1` means architecture regressions; exit `2` means `skipped` or `error` with
the concrete reason. A prepared reading plan is not a passing architecture gate.
Reuse a report only when source, base, policy, tool and options still match;
otherwise collect fresh evidence. Commands and raw evidence stay outside source.
No extra model or book-review pass is introduced.

The scoped v2 controller retains its existing stronger sandboxed gates and
filtered context builder. Native archgraph MCP has whole-root context authority;
do not attach it to a restricted helper as though query seeds enforce `reads`.

## Gate evidence

From the module's source root, save output outside the scanned root (replace `<tmp>` with an absolute path):

```sh
archgraph scan . --engine native --symbols --include-tests --rules layout.yaml -o <tmp>/head.json
archgraph check <tmp>/head.json
```

`check` fails forbidden edges, including layer/entrypoint rules. It does **not** fail cycles or unplanned edges. For regression checks, scan the approved base and candidate with identical rules, roots, language and inclusion options, then:

```sh
archgraph diff <tmp>/base.json <tmp>/head.json --fail-on new-forbidden,new-cycles,new-unplanned
```

Use the module's explicit `--language typescript|python|go` if detection is ambiguous; Python package layouts may also need `--package` or `--python-path`. Do not remove source roots or tests to obtain a clean result. `evals/checkers/run.sh --only archgraph` proves clean/planted forbidden imports for all three languages without installing other checkers. A pinned Cargo installation is recognized from its installation receipt. A separately verified build requires `ARCHGRAPH_BIN` and `ARCHGRAPH_SHA256`; that hash verifies the supplied artifact, not its build provenance.

## Reading order and blast radius

The full diff's reviewable-file list remains the coverage checklist. From the same root, seed **every changed file**, passing paths as separate arguments (never interpolate an unquoted path string):

```sh
archgraph context --graph <tmp>/head.json --root . --task 'Review change against approved intent' --files <changed-file-1> <changed-file-2> --budget 40k --format json
```

Save the JSON in `<tmp>/review-context.json`. Its `entries` are ordered context (path, reason, tier and optional source text), including imports/importers; `mode: body` entries can have `content: null`, so the reviewer opens those paths. Hand that order to the existing reviewer with `omitted`, `limitations`, `used_tokens` and `budget`; do not silently drop omitted, deleted or unscanned changed files. The 40k is an estimated context budget, not a hard provider-token cap. The reviewer may open any repository file. The graph orders reading; it never limits read authority or replaces diff coverage.

For a **committed** candidate, the complete blast-radius report is:

```sh
archgraph impact <base>..<head> --root . --engine native --symbols --include-tests --rules layout.yaml --format json
```

Save as `<tmp>/review-impact.json`; give the reviewer `affected_files`, `affected_modules`, `unscanned_files` and `limitations`. This command scans Git endpoints, not uncommitted edits. To reuse clean endpoint graphs, replace the collection options with `--graph <tmp>/head.json --base-graph <tmp>/base.json`; the graph commits must exactly match the range and be clean. Keep a base graph for deleted files and their importers. For an uncommitted candidate use the fresh `context` import/importer expansion and disclose that committed `impact` does not cover pending edits. Never present `HEAD` impact as evidence for a dirty candidate.

## Added public symbols

With both endpoint graphs collected using `--symbols` and identical scope:

```sh
archgraph surface <tmp>/base.json --format json
archgraph surface <tmp>/head.json --format json
```

Save both reports in `<tmp>`. Each report has `complete`, `modules[].exported[]` and `limitations`; exported entries carry `file`, `name` and their resolved `target`. Compare the sets of `(file, name)` to trigger the APoSD reviewer on observed additions, even when coverage is incomplete. `surface` is a report, not a failing added-export check, and `diff` does not emit an added-export list. Only conclude there are no additions when both reports have `complete: true` and their limitations permit it; otherwise also run the existing export search/manual check and mark coverage incomplete. Native TypeScript reports incomplete coverage at this pin, even for simple ES modules. Renames may trigger an extra review. CommonJS export surfaces are not indexed at this pin. Graph evidence cannot prove semantic compatibility or the intent of a behavioral ADR.
