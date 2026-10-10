---
name: factory-triage
description: Start a factory change - pick the track, create .factory/changes/<slug>/status.yaml and the working branch.
disable-model-invocation: true
argument-hint: "<task description>"
---

# Factory triage

Task: $ARGUMENTS

Triage turns a task into a tracked change: a track, a branch, `status.yaml`, and the repository profile in `.factory/system/lenses.yaml`.

## 1. Read the task and the repository

- If the task is empty, ask for it and stop.
- Read `CLAUDE.md` / `AGENTS.md`, the manifest (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, ...) and the test setup. Find three exact commands: the full test suite, a single test file, and lint plus type check.
- Read the code the task names, enough to judge how many modules it touches and whether it adds or changes an interface.
- Search Pond for prior work on the same area (`pond_search`, project filter set to this repository). Note session ids worth reading in the gates. If Pond tools are not available, note that and continue.

Done when you can name the modules in scope and all three commands.

## 2. Detect money and BDD

Skip this step when `.factory/system/lenses.yaml` exists and its modules still match the repository; reuse it.

- **Modules.** The repository root, plus every directory with its own manifest. For each: path, language, and language version from the manifest (`engines` / `typescript` in `package.json`, `rust-version` or `edition` in `Cargo.toml`, `go` in `go.mod`, `requires-python` in `pyproject.toml`).
- **BDD per module.** `native` when the module has any of: `*.feature` files, a BDD runner dependency (`@cucumber/cucumber`, `cucumber`, `behave`, `pytest-bdd`, `godog`), or runner config (`cucumber.js`, `cucumber.mjs`, `cucumber.yml`, `behave.ini`, `features/environment.py`). Otherwise `off`.
- **Money signals.** A payment, exchange or chain SDK in any manifest (`stripe`, `adyen`, `paypal`, `braintree`, `square`, `plaid`, `modern-treasury`, `ccxt`, `ethers`, `viem`, `web3`, `@solana/web3.js`, `bitcoinjs-lib`, `fireblocks`), or money in the schema and code (columns or fields named `amount`, `balance`, `price`, `currency`, `ledger`, `payout`, `refund`). List each signal with its `path:line`.

Done when every module has a language and a BDD state, and every money signal has a location.

## 3. Pick the track

| Track | When | What runs |
| --- | --- | --- |
| trivial | rename, copy, config, one-line fix | no factory: tell the user to hand it straight to an agent, then stop |
| small | a few files, no new or changed interface | slices gate only, then build and review |
| standard | new endpoint, table, screen, or any interface change | all four gates, then build and review |
| critical | money, auth, migrations, or any change touching a module with confirmed money | runs as standard. The Money reviewer and threat model are not built yet: say so |

Pick the track from what the code shows, not from how the task is worded.

## 4. Confirm with the user

Ask in one message:

- the track, with a one-line reason
- the slug (kebab-case, at most four words)
- the three commands, so the user can correct them
- the modules with language and BDD state, and the money signals found: money is `true` only when the user confirms it
- whether `.factory/` is committed in this repository or ignored (only when `.factory/` does not exist yet; otherwise reuse the mode of an existing `status.yaml`)

Done when the user has answered all of them.

## 5. Create the change

1. The working tree must be clean apart from `.factory/`. If it is not, list the changes and ask the user to commit or stash them.
2. Record `change_base_commit` = `git rev-parse HEAD`. On the default branch, create `factory/<slug>`. On any other branch, ask whether to work there or create `factory/<slug>`.
3. Ignored mode: append `.factory/` to `.git/info/exclude`, so the repository's own files stay untouched.
4. Write `.factory/system/lenses.yaml` when step 2 did not reuse it:

```yaml
money: false                # true only after the user confirms
modules:
  - path: .
    language: go
    language_version: "1.22"
    bdd: off                # native | off. Triage never sets adopt
```

5. Write `.factory/changes/<slug>/status.yaml`:

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
deviations: []              # { slice, file, reason }
pond_sessions: []           # prior sessions worth reading, from step 1
notes_for_fresh_session: "Triage done. Next: <first gate skill> <slug>."
```

6. Track small: set `product`, `architecture` and `interface` to `{ state: skipped }`.
7. Run `test_command` once. Record every failing test by name in `baseline_failures`. Red and green are judged against this list, so a repository with failing or flaky tests can still build.
8. Committed mode: `git add .factory/changes/<slug> .factory/system/lenses.yaml` and commit `chore(factory): triage <slug>`.

## 6. Hand off

Tell the user the next skill: `/factory-product <slug>`, or `/factory-slices <slug>` on track small.
