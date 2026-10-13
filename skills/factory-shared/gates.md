# Factory gates

Shared rules for every factory skill. The factory skills install as a set, so this file sits next to them. Paths are relative to the repository root; `<change>` is `.software-factory/changes/<slug>`.

## Paths

- `<project>` is the `.software-factory` folder at the repository root: `system/` (living documents), `changes/` (one folder per change), `runs/ci/`, `runs/ui/`, `runs/security/` and `runs/prune/` (run outputs), `factory.lock`, `principles.md` (the project's principles and quiet rules) and `evals/` (the project's own eval cases).
- The framework cache is `~/.software-factory/framework/<commit>/`: `kit/`, `skills/`, `hooks/` and `bin/` of one factory commit, unpacked once per machine by `bin/factory-install` in the factory repository. Projects never edit it.
- The pack cache is `~/.software-factory/packs/<name>@<hash>/`: one folder per pinned pack and hash, shared by every project on the machine that pins that hash, filled by `bin/factory-packs-fetch` from bare mirrors in `~/.software-factory/packs/.mirrors/` ([packs.md](packs.md)). Projects never edit it.
- `<kit>` is `~/.software-factory/framework/<commit>/kit`, where `<commit>` is `framework.commit` in `<project>/factory.lock`, or `<dev_path>/kit` when the lock names a `dev_path` (Resolve `<kit>`, below).
- The user layer is `~/.software-factory/user/`: `principles.md`, the user's taste across projects, and `config.yaml`, whose `framework_repo:` is the local clone of the factory repository, used to show the log between two framework commits (Load a change) and by `/factory-packs` to bump the framework's pins.
- **Principle layers.** Principles and quiet rules load in three layers: `<kit>/principles.md` (framework defaults), then `~/.software-factory/user/principles.md`, then `<project>/principles.md`; a missing file is skipped. A later layer wins on the same `<lens>/<rule>`: a project Principle whose Source is a `<lens>/<rule>` that a lower layer lists under Quiet rules takes that rule out of Quiet rules. Money and security rules never go quiet in any layer: rules from a `fin-*` pack, and rules that guard authentication, authorization, secrets, injection, cross-site attacks or path traversal.

`<project>/factory.lock` pins what the project runs on. `/factory-init` and `/factory-upgrade` write it; every other skill only reads it.

```yaml
framework: { commit: <sha>, installed: <ISO date> }
packs:                                                                # copied from <kit>/packs.lock.yaml at init or upgrade
  <name>: { source: ..., path: ..., hash: ..., pinned_at: ... }       # one line per pack; `packs: {}` when there is none
skills_linked: [.claude/skills]                                       # where /factory-init linked the skills
```

To develop the factory itself, `framework` may instead be `{ dev_path: <absolute path to a factory checkout> }`.

**Resolve `<kit>`.** Every skill does this before it reads anything else from the lock or the kit:

1. `framework.commit: <sha>`: `<kit>` is `~/.software-factory/framework/<sha>/kit`, the skills folder is `~/.software-factory/framework/<sha>/skills/`, and `<running>` is `<sha>`.
2. `framework.dev_path: <path>`: `<kit>` is `<path>/kit`, the skills folder is `<path>/skills/`, and `<running>` is `git -C <path> rev-parse HEAD`.
3. A branch that still has `.factory/` and no `.software-factory/`: say "this branch still uses .factory/; run /factory-init to migrate it", and stop. No `factory.lock`, no cache folder for its commit, or no `dev_path` folder: say which, point to `/factory-init`, and stop.
4. The `realpath` of this gates.md, as you opened it, must be inside the `realpath` of that skills folder. Otherwise name the commit or path actually running (the folder that holds its `skills/`) and stop: the linked skills are not the locked framework.

## The chain

| Gate | Document | Skill | Line budget |
| --- | --- | --- | --- |
| product | `<change>/01-product.md` | `/factory-product` | 100 |
| architecture | `<change>/02-architecture.md` | `/factory-architecture` | 150 |
| interface | `<change>/03-interface.md` | `/factory-interface` | 200, or 250 when it designs a frontend root (factory-interface, step 2) |
| slices | `<change>/04-slices.md` | `/factory-slices` | 100 |

Gate states: `pending`, `approved`, `skipped`. Track `small` skips product, architecture and interface; triage marks them `skipped`.

`hash(doc)` = `shasum -a 256 <doc> | cut -d' ' -f1`

`status.yaml` keeps each gate and slice as a one-line flow map (`{ id: 1, name: tracer, state: pending }`). The factory hook (`hooks/factory_gate.py` in the factory repository) reads them that way to block source edits the gates do not allow.

## IDs

- An FR's example is the `Example:` line indented under it. Older documents give it its own bullet (`- Example:`); read both.

- `FR-NN`, `NFR-NN`, `C-NN` belong to one change and are defined in its gate documents.
- `SYS-FR-NN`, `SYS-NFR-NN`, `SYS-C-NN` are standing rows in `.software-factory/system/constraints.md`. A change lists the ones it touches under Standing constraints in its first gate document, then treats them like its own IDs: a budget or ruled-out options in architecture, an enforcement in interface Coverage, a covering slice.

## Layout

A change's Layout is the Layout section of `02-architecture.md` together with the module's tree in `.software-factory/system/layout.md`. Under each module, lines come in one group per root, headed `Pattern: <id>, root: <path>, check: <tool or none>`: the reference layout from `<kit>/layouts/index.yaml` (or `<host>+cqrs`, or `existing` for a tree recorded as it is), the folder it was laid out for, and its checker from `<kit>/layouts/tools.yaml`. A line names a folder or a file, relative to the module path, and says what lives there; `<name>` matches one folder name, and `{a,b}` matches either. A file fits the Layout when any of these admits it:

- a line names the file, or names a folder the file is in or below
- the file sits directly in a folder that held tracked files at `change_base_commit`, and no line names that folder or a path directly inside it
- the file sits in a test tool's folder (`__snapshots__`, `__mocks__`) directly inside a folder the first two admit files in

## Milestones and autopilot

A milestone is a group of slices reviewed and signed off together: the `Milestone` line of each slice in `04-slices.md`, copied as `milestone` into its `status.yaml` entry. A slice without one is its own milestone, and so is every slice in headless mode. A milestone's work is its slices that are not `done`; `M` is its number, or the slice id when the slice has none.

In interactive mode `/factory-build` and `/factory-review` start the autopilot, and the session that runs them stays a thin orchestrator: it holds `status.yaml` and the step agents' reports, never code, diffs, packets or test output, so its context stays small however long the change runs.

1. Load the change (Load a change, steps 1 and 2). Re-read `status.yaml` from disk before every decision and every write. When a gate is not `approved` or `skipped`, or `sent_back` is set, name that gate's skill and stop. Otherwise the next step is: build the next slice of the milestone in progress ([../factory-build/SKILL.md](../factory-build/SKILL.md)), review a milestone whose open slices are all `green` ([../factory-review/SKILL.md](../factory-review/SKILL.md)), or, when every slice is `done`, reconcile ([../factory-reconcile/SKILL.md](../factory-reconcile/SKILL.md)), which the orchestrator follows itself, with its own `step_start`, before it stops.
2. For a build or review step, start one fresh step agent in the foreground (Models, below) and give it the absolute path of the step's skill. It receives only:

   > You are a factory step agent. Follow `<skill path>` for `<slug>`, for one step: one slice, or one milestone's review. Read what the skill says to read, from files. Your `step_start` detail is "session <the orchestrator's session id>, step agent, factory <sha>". Wait for every sub-agent you start before you report. A question the skill answers itself is not a question to report. Wherever the skill asks the user something, stop. Return a handoff JSON file under the change with `state: completed|question|blocked`, `children: [{id, state}]` for every child you used, `status_sha256` (SHA-256 of the final status.yaml bytes), `artifacts` (the exact existing paths you wrote, including slice-specific review paths), and `question` when stopped. Also report the outcome and the new state in at most five lines, then the question whole: every file list, output tail and numbered item the user needs to answer it. Save long output to a file under `.software-factory/changes/<slug>/` and name that file in the question.

3. Consume the native task completion or question event for the dispatched agent; a message saying a child is still running is not completion. Wait through the native task API, never a shell sleep/file-existence loop, and do not guess a root `review.md` when the child returned `slices/NN/review.md`. The child must not infer its native agent/task identity. After consuming the actual native return, the parent writes a separate completion envelope with `task_id` (its dispatch token), `agent_id` (the observed native task id), `state: completed` (from the task API), and `children: [{id, state}]` from every actual child task result. Check those native states against the identity-free child report; a running task is not a completed envelope. Child-supplied routing fields are ignored. Validate the report with `python3 <kit>/runtime.py handoff --repo <repo> --report <returned JSON path> --completion <parent completion envelope path> --slug <slug> --task-id <dispatched task id> --agent-id <native agent id> --slice <NN> --expected-state <green for build, done for signed-off review>`. A review awaiting sign-off returns `question`, not `completed`. Failure: resume that exact agent with the validation error; if it is gone, recover from disk through the same skill. Do not advance or invent state to match a report. Task identities and the file hash are routing/snapshot evidence, never approval authority; the existing user approvals and edit hooks still apply.
4. A reported question: show it to the user as reported, without shortening it. Continue the same step agent with the user's answer, word for word and labelled as the user's; the step agent treats it as the user's answer in chat, and the orchestrator never answers for the user. Where the agent cannot be continued, start a fresh one with the question and the answer; it applies the answer where its skill asked it.
5. When the validated step ends, append one `step_tokens` event (History) with the ids of every step agent the step used and normalized usage from Execution cost and evidence below. Never sum cumulative returns or nested rollups twice. Then go to 1.

`--one-step` after the slug (the slug is the arguments without it) runs build or review for exactly one step in this session, with no orchestrator: the skill asks the user directly and stops when the step ends. An eval trial or a user who wants one slice uses it.

The autopilot asks and continues for a rewind, a file a step may not allow on its own, a retry that failed twice, a signing failure, held review items and each milestone's sign-off. It ends at a send-back, at a gate that is not approved, and after reconcile.

## Commits

- Code commits per slice are the executor's red and green commits, plus one review fix commit per milestone.
- Interactive committed mode: build and review do not commit `.software-factory/` as separate steps. The planning state goes into the milestone review's first commit, and reconcile commits the rest. Gate approvals, send-backs and reconcile still commit.
- Headless mode commits and pushes after every step, since each run starts from a fresh clone. When `FACTORY_RUNNER_MANAGED=1`, commit locally and omit every skill push: the runner disables the clone's normal origin push URL (a publication policy, not network isolation) and publishes only a clean, successful, trusted step. Timeout, setup failure, nonzero exit or invalid head retains the full clone under the runner's `.git/factory-recovery/`; its checkpoint identifies the trusted starting head. Recover locally from that clone, preserving dirty/untracked files and commit history; do not publish or reset failed work merely to resume.
- A commit that fails to sign: ask the user to unlock their signing agent, then retry. Never commit unsigned.

## Load a change

0. Resolve `<kit>` (Paths). On failure, stop as it says, before the version check reads the lock.
1. Slug empty: a gate skill uses the only change whose own gate is `pending`; build and review use the rule they state. Several or none: ask.
2. Read `status.yaml`. Check out its `branch`. Append a `step_start` event to `history` (History, below).
   **Factory version.** A change runs on the framework commit it started on. When `factory_commit` is missing or differs from `<running>` (Paths, Resolve `<kit>`), the framework changed under this change: show `git -C <repo> log --oneline <factory_commit>..<running> -- :/skills :/kit`, where `<repo>` is the `dev_path` checkout, or else `framework_repo` from the user layer's `config.yaml` (when neither is set, or that clone lacks either commit, say so and skip the log), add every field of the triage template's `status.yaml` that this file lacks, with the value triage would set now (asking the user where triage would ask), then set `factory_commit` to `<running>` and append a `factory_updated` event. When no field is missing, the check asks nothing. A start state built for a test or an eval writes a `factory.lock` whose framework commit is its `factory_commit`, so the check stays silent. A headless runner runs this check like any session; a question it needs waits on the pull request like any other.
3. **Check the chain.** Walk the gates in order. The first `approved` gate whose `hash(doc)` differs from its `doc_sha256` goes back to `pending`, and so does every later gate that is not `skipped`, each as `{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }`. Append a `gate_reopened` event with cause `chain`. Tell the user which document changed.
4. A gate skill whose own gate is `approved` or `skipped` says so, names the next skill, and stops. To revise an approved gate, the user edits its document: the chain check reopens it.
5. **Design file.** A change with `ui: true` in `status.yaml` needs the repository's design file: the root `DESIGN.md`, or `.software-factory/system/design.md` when the root name holds something else; either way it carries the stamp `factory:design-schema` that `/factory-ui-ux` writes. Without it, every skill stops and points to `/factory-ui-ux design-md`; the factory hook blocks source edits too.
6. A gate skill drafts only when every earlier gate is `approved` or `skipped`. Otherwise name the first gate that is not, and its skill. Stop. Build and review need all four `approved` or `skipped`.
7. **Playbook.** Read `.software-factory/system/playbook.md` as [playbook.md](playbook.md) says, when it exists.

## Draft a gate document

Every gate document ends with an `## Open questions` section, empty before approval. An existing document resumes from its open questions instead of being redrafted.

## Approve a gate

Before asking for approval, check the line budget with `wc -l`. Over budget: cut repeated statements and narrative, keeping every ID, example, signature and decision. Still over: propose splitting the change into smaller changes, each with its own triage, and let the user choose between splitting and accepting the overrun.

Headless mode: commit and push the document, then wait for the user (below) with the comment "Ready for review: `<doc>`. Approve with a pull-request review whose first line is `approve <gate>`." The runner records the approval. Interactive mode, only after the user explicitly approves the document in chat:

1. `gates.<gate>` = `{ state: approved, approved_by: <git config user.name>, approved_at: <ISO time>, doc_sha256: <hash(doc)> }`
2. `notes_for_fresh_session`: "<gate> approved. Next: <next skill> <slug>."
3. Committed mode: `git add .software-factory/changes/<slug>` and commit `chore(factory): <gate> <slug>`.

## Send back

When build, review or reconcile's acceptance step finds that the approved design cannot hold, pick the target gate:

- an omitted or incorrect promised user outcome: `product` (track small: `slices`); hold the change for the appropriate human gate approval
- an approved budget is infeasible, or its storage/durability strategy cannot preserve acknowledged work: `architecture` (track small: `slices`); hold for the appropriate human gate approval
- a frozen signature cannot work as written: `interface` (track small: `slices`)
- a red-commit test is wrong, or the user refused a file outside Allowed files: `slices`
- an example failed in the running product at reconcile's acceptance step: `slices`, with no slice (`slice: null`); the fix comes as a new slice

Then:

1. Set the target gate and every later gate to `{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }`.
2. Set `sent_back` to `{ gate: <target>, slice: <NN or null>, reason }`, and append a `sent_back` event (ref: the slice, or `-`; detail: the target gate and reason).
3. Add the reason to Open questions in the target gate's document.
4. Committed mode: `git add .software-factory/changes/<slug> .software-factory/system` and commit `chore(factory): send back <slug> to <gate>`.
5. Tell the user to run the target gate's skill. Stop.

## Models

Sub-agents run on the session's model, except where a skill says *smaller model*: the harness's mid-size model (in Claude Code, the Agent tool's `model: sonnet`), or the session's model when that is not larger. Only agents whose output a later step checks against files get it: research answers, which cite `path:line` that the architecture gate reads, and retro's candidates, which retro tries to disprove. The executor, the reviewers, the challenge panel and the acceptance agent keep the session's model, because their mistakes cost review time or pass unseen. Step agents run on the session's model; in Claude Code, `subagent_type: general-purpose`, which has the Agent and Skill tools they need.

## History

### Execution cost and evidence

- Batch independent read-only searches and mechanical commands at the same verification barrier; keep their separate exit codes and complete logs. Do not repeat a passed check until its source, tests, command, dependencies or environment changed, or an unresolved concern requires it. Review's existing Phase 1 reuse rules still apply; an agent-authored receipt alone never grants independent verification or approval.
- Load only the selected profile's applicable lenses and their specified sizes. Pass packet/artifact paths and a bounded terminal report between agents; keep full logs on disk and retrieve the relevant failure sections. The executor still receives the full frozen contract and the reviewer still inspects the actual diff.
- When Context Mode tools are available, route large read-only exploration and non-browser command output through `ctx_execute`/`ctx_batch_execute` and `ctx_index`/`ctx_search`; discover deferred tools through the host's tool search when needed. Keep small reads direct and fixed browser capabilities in their required execution surface. Retain full raw evidence and actual exits, and retrieve complete frozen contracts and relevant failures before acting; summaries never replace verification or approval. Record actual tool calls and raw/returned sizes for M11 instead of treating enabled hooks as savings. Existing permissions still apply; do not install another compressor during a change.
- Before adding Tests first, identify existing tests that already assert unchanged behavior. Map those tests as existing coverage instead of inventing a new RED assertion for the same behavior. A genuinely new test that passes its stub still follows the explicit `red_exempt` decision.
- Record usage scope with every return: delta, cumulative for this same agent/session, or unknown; record included child ids when the provider reports nested usage. Sum deltas, take differences between cumulative returns, and never count a child twice through both its own total and its parent's rollup. Keep cache-read/cache-write/input/output classes separate; missing usage is unknown, not zero. These ids and counters are telemetry, never approval authority.

`history` in `status.yaml` is append-only: one flow-map line per event, never edited or removed, so `/factory-retro` can count what happened after the fields it summarizes are overwritten.

```yaml
history:
  - { at: 2026-10-11T09:12:03Z, step: factory-build, event: step_start, ref: "01", detail: "session <id>, factory <sha>" }
```

- `step_start`: every skill, at Load (triage, when it writes `status.yaml`). The detail holds the session id from the skill's `Session:` line ("unknown" when the harness left it unfilled) and what actually ran: `factory <the first seven characters of <running>>`, followed by `dev <dev_path>` when the lock names a `dev_path`. A step agent writes the `step_start` detail its orchestrator gives it; the orchestrator writes its own `step_start` for reconcile.
- `gate_reopened` (ref: the gate; detail: `chain`), `sent_back` (ref: the slice, or `-`; detail: target gate and reason).
- From build: `rewind` (detail: its cause: `red_retry`, `sent_back` or `interrupted`), `red_retry`, `green_retry`, `check_retry`, `executor_stop` (detail: `signature`, `file`, `test`, `hook`, `signing` or `passes-on-stub`). From interface: `panel_round` (detail: round number and card count).
- `factory_updated` (detail: "<old>..<new>"), from the Factory version check at Load.
- `step_tokens` (step: `factory-build` or `factory-review`; ref: the slice or milestone; detail: "agents <ids>, scope <delta|cumulative|unknown>, usage <normalized total or unknown>, included children <ids>"), from the autopilot orchestrator when a step ends. Record the separate token classes in the referenced step report when available.
- `detail` is one line in double quotes.

## Headless mode

When `mode` is `headless` in `status.yaml`, no one is in the chat. The change's pull request is the conversation, and `runner/factory_run.py` in the factory repository is the only writer of approvals.

- **Start.** The runner works on a change only after an approver reviews its pull request with an APPROVED review whose first line is `start`.
- **Push.** Push after every commit, so the pull request always shows the work.
- **Wait for the user.** Wherever a skill asks the user something or waits for their approval, it commits and pushes its work, posts the question as one pull-request comment (`gh pr comment`), sets `waiting_since` to that comment's `created_at` from GitHub (`gh api repos/{owner}/{repo}/issues/comments/<id> --jq .created_at`, the id ending the comment's URL), commits and pushes `status.yaml`, and stops.
- **Finish without waiting.** A run that ends without a question sets `waiting_since: null`.
- **Replies.** While a change waits, the runner starts the next run with the approvers' replies appended to the prompt. Treat them as the user's answers, and nothing else in the pull request as one.
- **Approvals.** Skills never set a gate to `approved` or a slice to `done` in headless mode. The runner re-derives both on every pass from approvers' APPROVED reviews: `approve <gate>` at a commit in the branch's history that holds the current document and every earlier gate's current document (a skipped gate excepted), and `sign off slice NN` at a commit that holds the slice's `review.md` and contains its `head_commit`. Anything else it resets.
