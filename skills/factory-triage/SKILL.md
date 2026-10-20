---
name: factory-triage
description: Start a factory change - detect modules, BDD and money, pick the track, create status.yaml, lenses.yaml and the working branch.
disable-model-invocation: true
argument-hint: "<task description>"
---

# Factory triage

Usage: [per-skill accounting](../factory-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Task: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Triage turns a task into a tracked change: a track, a branch, `status.yaml`, and the repository profile in `.software-factory/system/lenses.yaml`.

## 1. Read the task and the repository

- Resolve `<kit>` ([../factory-shared/gates.md](../factory-shared/gates.md), Paths) first, and stop as it says on failure.
- If the task is empty, ask for it and stop.
- Read `CLAUDE.md` / `AGENTS.md`, the manifest (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, ...) and the test setup. Find three exact commands: the full test suite, a single test file, and lint plus type check (default: `linter.check` of the module's language pack).
- Read the code the task names, enough to judge how many modules it touches and whether it adds or changes an interface.
- Search Pond for prior work on the same area (`pond_search`, project filter set to this repository). Note session ids worth reading in the gates. If Pond tools are not available, note that and continue.

Done when you can name the modules in scope and all three commands.

## 2. Detect the repository profile

- **Modules.** The repository root, plus every directory with its own manifest, outside dependency and build directories (`node_modules`, `vendor`, `target`, `dist`, `.venv`). For each: path, language, and language version from the manifest (`engines` / `typescript` in `package.json`, `rust-version` or `edition` in `Cargo.toml`, `go` in `go.mod`, `requires-python` in `pyproject.toml`), or `unknown`.
- **BDD per module.** `native` when the module has any of: `*.feature` files, a BDD runner dependency (`@cucumber/cucumber`, `cucumber`, `behave`, `pytest-bdd`, `godog`), or runner config (`cucumber.js`, `cucumber.mjs`, `cucumber.yml`, `behave.ini`, `features/environment.py`). Otherwise `off`.
- **Money signals.** A payment, exchange or chain SDK in any manifest (`stripe`, `adyen`, `paypal`, `braintree`, `square`, `plaid`, `modern-treasury`, `ccxt`, `ethers`, `viem`, `web3`, `@solana/web3.js`, `bitcoinjs-lib`, `fireblocks`), or money in the schema and code (columns or fields named `amount`, `balance`, `price`, `currency`, `ledger`, `payout`, `refund`). List each signal with its `path:line`.

- **Language pack.** `react` for a module whose `package.json` depends on `react` or `next`, `rust`, `go` or `python` by manifest, otherwise `none`. Compare the module's linter config with `linter.propose` in `<kit>/languages/<pack>.yaml` and list what is missing, and each `checks.install` tool the module lacks.
- **Run command.** For each module a user runs (an app, a service, a CLI): the command that starts it locally, or for a CLI the command that invokes it, and for a server the local URL it serves. A library records `none`. Review's runtime checks and reconcile's acceptance step use them.
- **UI.** The change touches UI when it changes files of a module with front-end dependencies (react, next, vue, svelte, solid, angular), templates, or styles. Note whether a design file exists (gates.md, Load a change).
- **Lens profile.** One of `<kit>/profiles/`: `domain-core` for core business logic with invariants, `crud-service` for thin create-read-update-delete over storage, `legacy` for code without tests that is risky to change. Pick from what the code shows.
- **Task size and optional design books.** Apply packs.md Pick to the observed footprint. Default `design_lenses: []`; record only an actual user selection. Risk and size are separate: a tiny money change still gets required money/security checks without a book panel. Reassess size from the slice plan without reopening approved decisions.

Done when every module has a language, a language pack, a BDD state and a run command or `none`, every money signal has a location, and a profile is proposed. When `.software-factory/system/lenses.yaml` exists, note where your findings differ from it.

## 3. Pick the track

| Track | When | What runs |
| --- | --- | --- |
| trivial | rename, copy, config, one-line fix | no factory: tell the user to hand it straight to an agent, then stop |
| small | a few files, no new or changed interface | slices gate only, then build and review |
| standard | new endpoint, table, screen, a new product's first sign-in, or any interface change | `/factory-plan` (one discovery pass, one approval of all four documents), then one build session, one review, reconcile. Headless: all four gates, then build and review |
| critical | money, a change to an existing authentication or authorization system, or a migration of existing stored data. Code behind a money signal counts as money | all four gates, plus `/factory-security threat-model` after the architecture gate; review adds the Money reviewer in money repositories |

Pick the track from what the code shows, not from how the task is worded.

## 4. Confirm with the user

Follow gates.md **Explain questions and decisions**: start with the short recap and keep the existing intake in one message. Present the proposed track as "how much planning and checking this needs", the slug as "short project name", and the mode as "continue in this chat / run through a pull request". Group detected commands, modules, BDD and lens details in a compact "What I found" table, preserving exact values for corrections. Explain promises through user examples and visuals; do not paste catalog terminology into questions. Ask only real intake decisions; detected facts and unchanged approvals are not additional decisions.

Ask in one message:

- the track, with a one-line reason
- the slug (kebab-case, at most four words)
- the three commands, so the user can correct them
- whether the change touches UI, and whether the design file exists
- UI: only when no references were supplied and this invitation was not already offered or declined, offer once the optional 2–3 feature examples in [../factory-ui-ux/references.md](../factory-ui-ux/references.md), explaining that concrete visuals can improve layout/interaction quality while DESIGN.md keeps our brand. Reuse any already supplied, record usable examples or `none` in `<change>/visual-references.md` when the change folder exists, and continue without them; no separate approval or repeated development question.
- the lens profile with a one-line reason, the modules with language, language pack, BDD state and any dev command and URL, linter rules and check tools the user may adopt in a change of their own, the money signals found, and any difference from an existing `lenses.yaml`. `money` becomes `true` only when the user confirms it
- when `.software-factory/system/constraints.md` is missing, or this change introduces or changes a capability (for example saved user data, multiple writers, offline work, auth or money): the relevant promises from the closest domain in `<kit>/nfr-catalog/` and its rows, for the user to keep, drop or tune
- compare those promises with the existing registry instead of offering the entire catalog again. Reuse matching SYS IDs; carry missing or changed promises into the product gate for agreement, even when the registry already exists. For saved user data, use `<kit>/nfr-catalog/stateful-data.md` alongside the domain catalog; storage technology does not decide whether the promise applies
- whether `.software-factory/` is committed in this repository or ignored, only when nothing has settled it yet: reuse the mode of an existing `status.yaml`, else committed when `git ls-files .software-factory` lists files and ignored when `git check-ignore -q .software-factory/` succeeds, as `/factory-init` left it

- the mode: `interactive` (this chat) or `headless` (the runner drives it through a pull request; who approves is configured on the runner)

Done when the required intake decisions are answered. Unanswered optional visual references never delay triage; record `none` and proceed.

## 5. Create the change

1. The working tree must be clean apart from `.software-factory/`. If it is not, list the changes and ask the user to commit or stash them. When `git config commit.gpgsign` is `true`, check that signing works: `git commit-tree -S -m probe $(git hash-object -t tree /dev/null)`. On failure, ask the user to unlock their signing agent before going on: the executor and the gates commit throughout the change.
2. Record `change_base_commit` = `git rev-parse HEAD`. On the default branch, create `factory/<slug>`. On any other branch, ask whether to work there or create `factory/<slug>`; a headless change always uses `factory/<slug>`, where the runner finds it.
3. Ignored mode: append `.software-factory/` to `.git/info/exclude` when `git check-ignore -q .software-factory/` fails, so the repository's own files stay untouched.
4. Write `.software-factory/system/lenses.yaml` with the confirmed values:

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
    dev_command: ""         # starts the app locally, or invokes the CLI; none for a library
    dev_url: ""             # the local URL dev_command serves; empty for a CLI or a library
    layers: []              # path globs, innermost first; set by the architecture gate
    bdd: off                # native | off; adopt is set only by the user
```

5. When `.software-factory/system/constraints.md` is missing, create it from [constraints.md](../factory-shared/constraints.md) with the example rows removed. Add each catalog row the user kept as `SYS-NFR-NN`: Kind is the catalog key, Statement the promise, Fit criterion the tuned budget, Source `nfr-catalog/<domain>`, Enforced by `unmapped (<catalog Enforced by>)` until a change names the exact test, monitor or check.
6. Write `.software-factory/changes/<slug>/status.yaml`:

```yaml
feature: <slug>
task: "<the task in one line>"
track: standard             # small | standard | critical
track_proposed: standard    # the track triage recommended, kept when the user chose another
task_size: medium           # small | medium | large; footprint, independent of risk track
design_lenses: []           # explicit task-local opt-in pack names; absent also means none
factory_dir: committed      # committed | ignored
branch: <branch from 5.2>
change_base_commit: <sha>
factory_commit: <sha>       # <running> (gates.md, Paths): the factory version this change runs on (gates.md, Load a change)
test_command: "<full suite>"
red_test_command: null      # exact isolated RED capability when a fixed browser wrapper is supplied; otherwise omit/null
test_file_command: "<single file, with a {file} placeholder>"
check_command: "<lint and type check>"
baseline_failures: []       # tests failing or flaky at change_base_commit
gates:
  product:      { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
  architecture: { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
  interface:    { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
  slices:       { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
slices: []                  # filled by factory-slices
sent_back: null             # { gate, slice, reason } while a gate must be revisited
stubbing: false             # true only while the interface gate compiles its stubs
ui: false                   # true when the change touches UI: it then needs the design file
reconciled: false           # set by factory-reconcile
mode: interactive           # interactive | headless
waiting_since: null         # headless: GitHub time of the question the change waits on
deviations: []              # { slice, file, reason }
pond_sessions: []           # prior sessions worth reading, from step 1
notes_for_fresh_session: "Triage done. Next: <first gate skill> <slug>."
history:                    # append-only events (factory-shared/gates.md, History)
  - { at: <ISO time>, step: factory-triage, event: step_start, ref: "-", detail: "session <id>, factory <sha>" }
```

7. Track small: set `product`, `architecture` and `interface` to `{ state: skipped }`.
8. Run `test_command` twice. Record by name every test that failed in either run in `baseline_failures`. Red and green are judged against this list, so a repository with failing or flaky tests can still build. Tests that failed in only one run are flaky.
9. Committed mode: `git add .software-factory/changes/<slug> .software-factory/system`, plus `.software-factory/factory.lock` and `.software-factory/principles.md` when they exist, and commit `chore(factory): triage <slug>`.
10. Headless mode needs committed mode: the pull request carries the documents. Push the branch and open a draft pull request (`gh pr create --draft`) titled `factory: <slug>`. Tell the user the runner starts once an approver reviews it with an APPROVED review whose first line is `start`.

## 6. Hand off

Name the flaky tests from step 5.8, if any, as candidates for a fix of their own. Track standard in interactive mode: continue to `/factory-plan <slug>` in this session, also when `ui` is `true` and the design file is missing, since factory-plan writes it. Otherwise tell the user the next skill: `/factory-ui-ux design-md` when `ui` is `true` and the design file is missing; otherwise `/factory-product <slug>`, or `/factory-slices <slug>` on track small.
