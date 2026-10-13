# Dashboard outputs: design and structure

The [later UI continuation and independent review](dashboard-final-comparison.md)
include accessible finished source, updated screenshots, and severity counts.

The pilot established completed behavior, not polished product design. Its fifteen
checks did not score visual composition, density, typography, or aesthetic quality.
The task requested a sensible hierarchy but explicitly prescribed no layout, colors,
or theme. All arms started with the same plain list and 20-line stylesheet.

Factory's simulated approvals accepted skipping design renders and mockup screenshots.
Its design documents largely preserved the starter's tokens and chose a plain queue.
The base captured arm left the stylesheet unchanged; the captured Context RED arm added three lines.
Superpowers used a 43-line stylesheet with badges and stronger hierarchy. None of
these observations demonstrates a polished design. Good design was feasible with
the same HTML/CSS constraints; the benchmark lacked a visual acceptance gate.

## Generated folders

These are unchanged copies of the retained workspaces **as captured at r4 timeout/completion**, not necessarily their latest committed GREEN code. In particular, the Context step agent was detached at RED `2acf68a` after its executor committed GREEN `03c6d91`; this exported Context folder is RED. Empty CLI configuration
directories and transient Git/temp data are omitted. Application code, tests,
planning documents, and recorded workflow state are retained.

| Output | Application files | Test files | Workflow/design files |
|---|---:|---:|---:|
| Factory | 5 | 3 | 16 |
| Factory + Context Mode | 5 | 3 | 15 |
| Superpowers | 4 | 2 | 1, plus one workflow `.gitignore` |

```text
dashboard-products/factory/
├── index.html
├── styles.css
├── tickets.js
├── app.js                 DOM, dialogs, event handling
├── store.js               storage and ticket rules
├── test_existing.cjs
├── test_dashboard.cjs
├── test_store.cjs          browser-independent storage/rules tests
├── DESIGN.md
└── .factory/
    ├── system/
    │   ├── constraints.md
    │   └── lenses.yaml
    └── changes/support-ticket-dashboard/
        ├── 01-product.md
        ├── 02-architecture.md
        ├── 03-interface.md
        ├── 04-slices.md
        ├── research.md
        ├── challenges.md
        ├── status.yaml
        └── slices/
            ├── 01/{packet.md,checks.md,review.md}
            ├── 02/{packet.md,checks.md}
            └── 03/packet.md
```

Context Mode's captured RED arm has the same file layout, without slice 01's `review.md`. Do not interpret its missing creation surface or duplicated Reset setup as the best implementation produced during the run.

```text
dashboard-products/superpowers/
├── index.html
├── styles.css
├── tickets.js
├── app.js                 ticket rules, storage, DOM, dialogs
├── test_existing.cjs
├── test_dashboard.cjs
├── docs/superpowers/plans/2026-10-13-support-ticket-dashboard.md
└── .superpowers/sdd/.gitignore
```

Neither arm produced a large application directory hierarchy. Factory's concrete
code boundary is its DOM-free `store.js`, accepting injected storage and seed data.
Its requirement IDs, packets, checks, hashes, and approvals make intended work and
unfinished stages easier to inspect. More files do not demonstrate better product
quality or lower maintenance cost.

Useful files to inspect:

- [Factory store](dashboard-products/factory/store.js) and [its tests](dashboard-products/factory/test_store.cjs).
- [Factory application](dashboard-products/factory/app.js) and [design document](dashboard-products/factory/DESIGN.md).
- [Factory requirement-to-slice mapping](dashboard-products/factory/.factory/changes/support-ticket-dashboard/04-slices.md).
- [Superpowers application](dashboard-products/superpowers/app.js) and [implementation plan](dashboard-products/superpowers/docs/superpowers/plans/2026-10-13-support-ticket-dashboard.md).
- [Context captured RED application](dashboard-products/factory-context/app.js) and [store](dashboard-products/factory-context/store.js).

## Context checkpoint recovery

The original Context timeout happened during detached RED proof, so its raw 11/15 score and exported files describe the checked-out RED state. The native executor had already committed GREEN `03c6d91`, including creation and removal of the duplicated Reset setup. Three recorded source actions were replayed into a fresh Git checkpoint because the original Git objects were not retained. [Recovery actions](/private/tmp/factory-dashboard-extension-20261013/recovery-actions.json) and [restoration provenance](/private/tmp/factory-dashboard-extension-20261013/restoration.json) map original RED/GREEN `2acf68a`/`03c6d91` to reconstructed `7f0211614c6f45727e5f41e87cbd05bf89bf83ca`/`4b66b4a52158905395ccf0f73888a22a90332448`.

Before any new model implementation, Main verified **17/17 store tests** and **15/15 frozen browser checks** on the recovered original GREEN. [GREEN unit evidence](/private/tmp/factory-dashboard-extension-20261013/recovered-green-unit.txt), [browser quality](/private/tmp/factory-dashboard-extension-20261013/recovered-green-quality.json), and [recovered screenshots](/private/tmp/factory-dashboard-extension-20261013/grade-recovered-green/) are separate from the historical captures above. Recovery does not retroactively make the 30-minute workflow complete: reviews and reconcile remained unfinished at timeout. A fresh same-model extension is running with an additional 15-minute/USD 5 cap; its final results and independent code-review comparison are not reported here yet.

## Additional two-tab check

A post-pilot browser check found a concrete Factory advantage outside the original
acceptance suite. For each unchanged product, two pages shared one browser context
and origin. These were the original retained versions, including Context's captured RED, not recovered GREEN or extension output. Both loaded the initial records. Page A saved T001 as `resolved`; page B
then saved T002 as `pending`. Page A reloaded and inspected both records.

| Output | T001 after both saves | T002 after both saves | Both edits preserved |
|---|---|---|---|
| Factory | resolved | pending | Yes |
| Factory + Context Mode | resolved | pending | Yes |
| Superpowers | open | pending | No |

Factory re-reads stored records before updating one ticket. Superpowers writes its
page's cached ticket array, so the second page overwrites the first page's edit.
This is an observed data-loss case, not a guarantee against every concurrent-write
race. The check used no model calls and changed no retained product files.

The original 15/15 result remains historical acceptance against its original suite;
it does not establish complete correctness. Superpowers completed the original workflow and delivery, while Factory demonstrated stronger behavior for this particular persistence case. The recovered original Context GREEN also passes the fifteen functional checks; its captured RED's missing creation must not be used to rank the best available code.
Neither implementation has established the polished product quality the user wants.

Not checked: repeated runs, simultaneous write races, or measured human maintenance
and follow-up time. The base Factory capture remains incomplete; the Context capture is RED while its recovered committed GREEN passes 15/15. Original workflow completion, polished visual quality, and extension results remain separate questions.
