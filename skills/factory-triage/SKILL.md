---
name: factory-triage
description: Start a factory change - detect modules, BDD and money, pick the track, create status.yaml, lenses.yaml and the working branch.
disable-model-invocation: true
argument-hint: "<task description>"
---

# Factory triage

Task: $ARGUMENTS

Triage turns a task into a tracked change: a track, a branch, `status.yaml`, and the repository profile in `.factory/system/lenses.yaml`.

## 1. Read the task and the repository

- If the task is empty, ask for it and stop.
- Read `CLAUDE.md` / `AGENTS.md`, the manifest (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, ...) and the test setup. Find three exact commands: the full test suite, a single test file, and lint plus type check (default: `linter.check` of the module's language pack).
- Read the code the task names, enough to judge how many modules it touches and whether it adds or changes an interface.
- Search Pond for prior work on the same area (`pond_search`, project filter set to this repository). Note session ids worth reading in the gates. If Pond tools are not available, note that and continue.

Done when you can name the modules in scope and all three commands.

## 2. Detect the repository profile

- **Modules.** The repository root, plus every directory with its own manifest, outside dependency and build directories (`node_modules`, `vendor`, `target`, `dist`, `.venv`). For each: path, language, and language version from the manifest (`engines` / `typescript` in `package.json`, `rust-version` or `edition` in `Cargo.toml`, `go` in `go.mod`, `requires-python` in `pyproject.toml`), or `unknown`.
- **BDD per module.** `native` when the module has any of: `*.feature` files, a BDD runner dependency (`@cucumber/cucumber`, `cucumber`, `behave`, `pytest-bdd`, `godog`), or runner config (`cucumber.js`, `cucumber.mjs`, `cucumber.yml`, `behave.ini`, `features/environment.py`). Otherwise `off`.
- **Money signals.** A payment, exchange or chain SDK in any manifest (`stripe`, `adyen`, `paypal`, `braintree`, `square`, `plaid`, `modern-treasury`, `ccxt`, `ethers`, `viem`, `web3`, `@solana/web3.js`, `bitcoinjs-lib`, `fireblocks`), or money in the schema and code (columns or fields named `amount`, `balance`, `price`, `currency`, `ledger`, `payout`, `refund`). List each signal with its `path:line`.

- **Language pack.** `react` for a module whose `package.json` depends on `react` or `next`, `rust`, `go` or `python` by manifest, otherwise `none`. Compare the module's linter config with `linter.propose` in `~/.software-factory/languages/<pack>.yaml` and list what is missing, and each `checks.install` tool the module lacks. For a pack with a `checks.runtime`, find the module's command that starts the app locally and the URL it serves.
- **Lens profile.** One of `~/.software-factory/profiles/`: `domain-core` for core business logic with invariants, `crud-service` for thin create-read-update-delete over storage, `legacy` for code without tests that is risky to change. Pick from what the code shows.

Done when every module has a language, a language pack and a BDD state, every money signal has a location, and a profile is proposed. When `.factory/system/lenses.yaml` exists, note where your findings differ from it.

## 3. Pick the track

| Track | When | What runs |
| --- | --- | --- |
| trivial | rename, copy, config, one-line fix | no factory: tell the user to hand it straight to an agent, then stop |
| small | a few files, no new or changed interface | slices gate only, then build and review |
| standard | new endpoint, table, screen, or any interface change | all four gates, then build and review |
| critical | money, auth, migrations. Code behind a money signal counts as money | all four gates; review adds the Money reviewer in money repositories. The threat model is not built yet: say so |

Pick the track from what the code shows, not from how the task is worded.

## 4. Confirm with the user

Ask in one message:

- the track, with a one-line reason
- the slug (kebab-case, at most four words)
- the three commands, so the user can correct them
- the lens profile with a one-line reason, the modules with language, language pack, BDD state and any dev command and URL, linter rules and check tools the user may adopt in a change of their own, the money signals found, and any difference from an existing `lenses.yaml`. `money` becomes `true` only when the user confirms it
- only when `.factory/system/constraints.md` does not exist: the closest domain in `~/.software-factory/nfr-catalog/` and its rows, for the user to keep, drop or tune. Without the kit, say so and point to `kit/README.md` in the factory repository
- whether `.factory/` is committed in this repository or ignored (only when `.factory/` does not exist yet; otherwise reuse the mode of an existing `status.yaml`)

- the mode: `interactive` (this chat) or `headless` (the runner drives it through a pull request), and for headless the GitHub logins whose reviews count as approvals

Done when the user has answered all of them.

## 5. Create the change

1. The working tree must be clean apart from `.factory/`. If it is not, list the changes and ask the user to commit or stash them.
2. Record `change_base_commit` = `git rev-parse HEAD`. On the default branch, create `factory/<slug>`. On any other branch, ask whether to work there or create `factory/<slug>`.
3. Ignored mode: append `.factory/` to `.git/info/exclude`, so the repository's own files stay untouched.
4. Write `.factory/system/lenses.yaml` with the confirmed values:

```yaml
profile: domain-core          # domain-core | crud-service | legacy
domain_model: rich            # rich | transaction-scripts | keep, from the profile; the architecture gate decides
money: false
domain: web-api              # NFR catalog that seeded the registry, or none
modules:
  - path: .
    language: go
    language_version: "1.22"
    pack: go                # react | rust | go | python | none
    dev_command: ""         # packs with runtime checks: starts the app locally
    dev_url: ""             # where dev_command serves the app
    layers: []              # path globs, innermost first; set by the architecture gate
    bdd: off                # native | off; adopt is set only by the user
```

5. When `.factory/system/constraints.md` is missing, create it from [constraints.md](../factory-shared/constraints.md) with the example rows removed. Add each catalog row the user kept as `SYS-NFR-NN`: Kind is the catalog key, Statement the promise, Fit criterion the tuned budget, Source `nfr-catalog/<domain>`, Enforced by `unmapped (<catalog Enforced by>)` until a change names the exact test, monitor or check.
6. Write `.factory/changes/<slug>/status.yaml`:

```yaml
feature: <slug>
task: "<the task in one line>"
track: standard             # small | standard | critical
factory_dir: committed      # committed | ignored
branch: <branch from 5.2>
change_base_commit: <sha>
test_command: "<full suite>"
test_file_command: "<single file, with a {file} placeholder>"
check_command: "<lint and type check>"
baseline_failures: []       # tests already failing at change_base_commit
gates:
  product:      { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
  architecture: { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
  interface:    { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
  slices:       { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
slices: []                  # filled by factory-slices
sent_back: null             # { gate, slice, reason } while a gate must be revisited
stubbing: false             # true only while the interface gate compiles its stubs
reconciled: false           # set by factory-reconcile
mode: interactive           # interactive | headless
approvers: []               # headless: GitHub logins whose reviews approve
waiting_since: null         # headless: when the change last stopped for its approvers
deviations: []              # { slice, file, reason }
pond_sessions: []           # prior sessions worth reading, from step 1
notes_for_fresh_session: "Triage done. Next: <first gate skill> <slug>."
```

7. Track small: set `product`, `architecture` and `interface` to `{ state: skipped }`.
8. Run `test_command` once. Record every failing test by name in `baseline_failures`. Red and green are judged against this list, so a repository with failing or flaky tests can still build.
9. Headless mode needs committed mode: the pull request carries the documents. Push the branch and open a draft pull request (`gh pr create --draft`) titled `factory: <slug>`.
10. Committed mode: `git add .factory/changes/<slug> .factory/system` and commit `chore(factory): triage <slug>`.

## 6. Hand off

Tell the user the next skill: `/factory-product <slug>`, or `/factory-slices <slug>` on track small.
