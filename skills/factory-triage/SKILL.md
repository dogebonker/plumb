---
name: factory-triage
description: Start a factory change - pick the track, create .factory/changes/<slug>/status.yaml and the working branch.
disable-model-invocation: true
argument-hint: "<task description>"
---

# Factory triage

Task: $ARGUMENTS

Triage turns a task into a tracked change. It writes no plan and no code.

## 1. Read the task and the repository

- If the task is empty, ask for it and stop.
- Read `CLAUDE.md` / `AGENTS.md`, the manifest (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, ...) and the test setup. Find three exact commands: the full test suite, a single test file, and lint plus type check.
- Read the code the task names, enough to judge how many modules it touches and whether it adds or changes an interface.
- Search Pond for prior work on the same area (`pond_search`, project filter set to this repository). Note session ids worth reading in the plan. If Pond tools are not available, note that and continue.

Done when you can name the modules in scope and all three commands.

## 2. Pick the track

| Track | When | What runs |
| --- | --- | --- |
| trivial | rename, copy, config, one-line fix | no factory: tell the user to hand it straight to an agent, then stop |
| small | a few files, no new or changed interface | short plan (goal, requirements, slices), then build and review |
| standard | new endpoint, table, screen, or any interface change | full plan, build and review |
| critical | money, auth, migrations | S1 runs it as standard. The Money reviewer and threat model are not built yet: say so |

Pick the track from what the code shows, not from how the task is worded.

## 3. Confirm with the user

Ask in one message:

- the track, with a one-line reason
- the slug (kebab-case, at most four words)
- the three commands, so the user can correct them
- whether `.factory/` is committed in this repository or ignored (only when `.factory/` does not exist yet; otherwise reuse the mode of an existing `status.yaml`)

Done when the user has answered all of them.

## 4. Create the change

1. The working tree must be clean apart from `.factory/`. If it is not, list the changes and ask the user to commit or stash them.
2. Record `change_base_commit` = `git rev-parse HEAD`. On the default branch, create `factory/<slug>`. On any other branch, ask whether to work there or create `factory/<slug>`.
3. Ignored mode: append `.factory/` to `.git/info/exclude`, so the repository's own files stay untouched.
4. Write `.factory/changes/<slug>/status.yaml`:

```yaml
feature: <slug>
task: "<the task in one line>"
track: standard             # small | standard | critical
factory_dir: committed      # committed | ignored
branch: <branch from 4.2>
change_base_commit: <sha>
test_command: "<full suite>"
test_file_command: "<single file, with a {file} placeholder>"
check_command: "<lint and type check>"
baseline_failures: []       # tests already failing at change_base_commit
gates:
  plan: { state: pending, approved_by: null, approved_at: null, doc_sha256: null }
slices: []                  # filled by factory-plan
sent_back: null             # { slice, reason } while the plan must be revisited
deviations: []              # { slice, file, reason }
pond_sessions: []           # prior sessions worth reading, from step 1
notes_for_fresh_session: "Triage done. Next: /factory-plan <slug>."
```

5. Run `test_command` once. Record every failing test by name in `baseline_failures`. Red and green are judged against this list, so a repository with failing or flaky tests can still build.
6. Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): triage <slug>`.

## 5. Hand off

Tell the user: run `/factory-plan <slug>`.
