# Archgraph evidence for review

Use the Layout Decision's Pattern line. Archgraph supplements a previously selected stack checker; it replaces that checker only when the Decision explicitly chooses it. The pinned install and checker commands live in `kit/layouts/tools.yaml`: source commit `49464a7ec19fe8402b4258e751f7ba050c6eff19`, built with `--locked`. Version `0.1.0` alone does not identify this build. Record the binary SHA-256 alongside the source pin. Do not install skills or MCP to run these commands.

If absent, report **skipped** with the exact install line from the registry. Preserve the adapter's checks and ordinary reviewer reading order; absence is not a clean verdict. A command error, unresolved import, incomplete symbols or stale graph is a limitation to report, not evidence of conformance. The native engine is experimental.

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
