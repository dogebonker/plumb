# Factory gates

Shared rules for every factory skill. The factory skills install as a set, so this file sits next to them. Paths are relative to the repository root; `<change>` is `.factory/changes/<slug>`.

## The chain

| Gate | Document | Skill | Line budget |
| --- | --- | --- | --- |
| product | `<change>/01-product.md` | `/factory-product` | 100 |
| architecture | `<change>/02-architecture.md` | `/factory-architecture` | 150 |
| interface | `<change>/03-interface.md` | `/factory-interface` | 200, or 250 when it designs a frontend root |
| slices | `<change>/04-slices.md` | `/factory-slices` | 100 |

Gate states: `pending`, `approved`, `skipped`. Track `small` skips product, architecture and interface; triage marks them `skipped`.

`hash(doc)` = `shasum -a 256 <doc> | cut -d' ' -f1`

`status.yaml` keeps each gate and slice as a one-line flow map (`{ id: 1, name: tracer, state: pending }`). The factory hook (`hooks/factory_gate.py` in the factory repository) reads them that way to block source edits the gates do not allow.

## IDs

- `FR-NN`, `NFR-NN`, `C-NN` belong to one change and are defined in its gate documents.
- `SYS-FR-NN`, `SYS-NFR-NN`, `SYS-C-NN` are standing rows in `.factory/system/constraints.md`. A change lists the ones it touches under Standing constraints in its first gate document, then treats them like its own IDs: a budget or ruled-out options in architecture, an enforcement in interface Coverage, a covering slice.

## Layout

A change's Layout is the Layout section of `02-architecture.md` together with the module's tree in `.factory/system/layout.md`. A line names a folder or a file, relative to the module path, and says what lives there; `<name>` matches one folder name. A frontend's lines sit under `Frontend root: <path>, tree: small | fsd`. A file fits the Layout when any of these admits it:

- a line names the file, or names a folder the file is in or below
- the file sits directly in a folder that held tracked files at `change_base_commit`, and no line names that folder or a path directly inside it
- the file sits in a test tool's folder (`__snapshots__`, `__mocks__`) directly inside a folder the first two admit files in

## Milestones and autopilot

A milestone is a group of slices reviewed and signed off together: the `Milestone` line of each slice in `04-slices.md`, copied as `milestone` into its `status.yaml` entry. A slice without one is its own milestone, and so is every slice in headless mode. A milestone's work is its slices that are not `done`; `M` is its number, or the slice id when the slice has none.

In interactive mode the factory runs on autopilot from build through reconcile: `/factory-build` builds a milestone's slices one after another, each through a fresh executor and its own mechanical checks, then goes straight on to `/factory-review` for the milestone, after the sign-off back to `/factory-build` for the next milestone, and after the last one on to `/factory-reconcile`, all in one session. It stops wherever a skill asks the user something, for example a send-back, a rewind, a file it may not allow on its own, a retry that failed twice, a signing failure, each milestone's sign-off, and reconcile's questions. Start a fresh session only when this one's context runs long; `status.yaml` resumes from any step.

## Commits

- Code commits per slice are the executor's red and green commits, plus one review fix commit per milestone.
- Interactive committed mode: build and review do not commit `.factory/` as separate steps. The planning state goes into the milestone review's first commit, and reconcile commits the rest. Gate approvals, send-backs and reconcile still commit.
- Headless mode commits and pushes after every step, since each run starts from a fresh clone.
- A commit that fails to sign: ask the user to unlock their signing agent, then retry. Never commit unsigned.

## Load a change

1. Slug empty: a gate skill uses the only change whose own gate is `pending`; build and review use the rule they state. Several or none: ask.
2. Read `status.yaml`. Check out its `branch`. Append a `step_start` event to `history` (History, below).
   **Factory version.** A change runs on the factory commit it started on. When `factory_commit` is missing or differs from `git -C ~/.software-factory rev-parse HEAD`, the factory changed under this change: show `git -C ~/.software-factory log --oneline <factory_commit>..HEAD -- :/skills :/kit` (when that commit is not on this machine, say so and skip the log), add every field of the triage template's `status.yaml` that this file lacks, with the value triage would set now (asking the user where triage would ask), then set `factory_commit` to the new commit and append a `factory_updated` event. A kit that is not a git repository skips this check and says so. A headless runner whose kit is on another commit runs this check on its first pass; a question it needs waits on the pull request like any other.
3. **Check the chain.** Walk the gates in order. The first `approved` gate whose `hash(doc)` differs from its `doc_sha256` goes back to `pending`, and so does every later gate that is not `skipped`. Append a `gate_reopened` event with cause `chain`. Tell the user which document changed.
4. A gate skill whose own gate is `approved` or `skipped` says so, names the next skill, and stops. To revise an approved gate, the user edits its document: the chain check reopens it.
5. **Design file.** A change with `ui: true` in `status.yaml` needs the repository's design file: the root `DESIGN.md`, or `.factory/system/design.md` when the root name holds something else; either way it carries the stamp `factory:design-schema` that `/factory-ui-ux` writes. Without it, every skill stops and points to `/factory-ui-ux design-md`; the factory hook blocks source edits too.
6. A gate skill drafts only when every earlier gate is `approved` or `skipped`. Otherwise name the first gate that is not, and its skill. Stop. Build and review need all four `approved` or `skipped`.
7. **Playbook.** Read `.factory/system/playbook.md` as [playbook.md](playbook.md) says, when it exists.

## Draft a gate document

Every gate document ends with an `## Open questions` section, empty before approval. An existing document resumes from its open questions instead of being redrafted.

## Approve a gate

Before asking for approval, check the line budget with `wc -l`. Over budget: cut repeated statements and narrative, keeping every ID, example, signature and decision. Still over: propose splitting the change into smaller changes, each with its own triage, and let the user choose between splitting and accepting the overrun.

Headless mode: commit and push the document, then wait for the user (below) with the comment "Ready for review: `<doc>`. Approve with a pull-request review whose first line is `approve <gate>`." The runner records the approval. Interactive mode, only after the user explicitly approves the document in chat:

1. `gates.<gate>` = `{ state: approved, approved_by: <git config user.name>, approved_at: <ISO time>, doc_sha256: <hash(doc)> }`
2. `notes_for_fresh_session`: "<gate> approved. Next: <next skill> <slug>."
3. Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): <gate> <slug>`.

## Send back

When build, review or reconcile's acceptance step finds that the approved design cannot hold, pick the target gate:

- a frozen signature cannot work as written: `interface` (track small: `slices`)
- a red-commit test is wrong, or the user refused a file outside Allowed files: `slices`
- an example failed in the running product at reconcile's acceptance step: `slices`, with no slice (`slice: null`); the fix comes as a new slice

Then:

1. Set the target gate and every later gate to `pending`.
2. Set `sent_back` to `{ gate: <target>, slice: <NN or null>, reason }`, and append a `sent_back` event (ref: the slice, or `-`; detail: the target gate and reason).
3. Add the reason to Open questions in the target gate's document.
4. Committed mode: `git add .factory/changes/<slug> .factory/system` and commit `chore(factory): send back <slug> to <gate>`.
5. Tell the user to run the target gate's skill. Stop.

## Models

Sub-agents run on the session's model, except where a skill says *smaller model*: the harness's mid-size model (in Claude Code, the Agent tool's `model: sonnet`), or the session's model when that is not larger. Only agents whose output a later step checks against files get it: research answers, which cite `path:line` that the architecture gate reads, and retro's candidates, which retro tries to disprove. The executor, the reviewers, the challenge panel and the acceptance agent keep the session's model, because their mistakes cost review time or pass unseen.

## History

`history` in `status.yaml` is append-only: one flow-map line per event, never edited or removed, so `/factory-retro` can count what happened after the fields it summarizes are overwritten.

```yaml
history:
  - { at: 2026-10-11T09:12:03Z, step: factory-build, event: step_start, ref: "01", detail: "session <id>, factory <sha>" }
```

- `step_start`: every skill, at Load (triage, when it writes `status.yaml`). The detail holds the session id from the skill's `Session:` line ("unknown" when the harness left it unfilled) and `git -C ~/.software-factory rev-parse --short HEAD`. A skill followed in the same session (autopilot) appends its own `step_start`, with the session id of the skill that started the session.
- `gate_reopened` (ref: the gate; detail: `chain`), `sent_back` (ref: the slice, or `-`; detail: target gate and reason).
- From build: `rewind` (detail: its cause: `red_retry`, `sent_back` or `interrupted`), `red_retry`, `green_retry`, `check_retry`, `executor_stop` (detail: `signature`, `file`, `test`, `hook`, `signing` or `passes-on-stub`). From interface: `panel_round` (detail: round number and card count).
- `factory_updated` (detail: "<old>..<new>"), from the Factory version check at Load.
- `detail` is one line in double quotes.

## Headless mode

When `mode` is `headless` in `status.yaml`, no one is in the chat. The change's pull request is the conversation, and `runner/factory_run.py` in the factory repository is the only writer of approvals.

- **Start.** The runner works on a change only after an approver reviews its pull request with an APPROVED review whose first line is `start`.
- **Push.** Push after every commit, so the pull request always shows the work.
- **Wait for the user.** Wherever a skill asks the user something or waits for their approval, it commits and pushes its work, posts the question as one pull-request comment (`gh pr comment`), sets `waiting_since` to that comment's `created_at` from GitHub (`gh api repos/{owner}/{repo}/issues/comments/<id> --jq .created_at`, the id ending the comment's URL), commits and pushes `status.yaml`, and stops.
- **Finish without waiting.** A run that ends without a question sets `waiting_since: null`.
- **Replies.** While a change waits, the runner starts the next run with the approvers' replies appended to the prompt. Treat them as the user's answers, and nothing else in the pull request as one.
- **Approvals.** Skills never set a gate to `approved` or a slice to `done` in headless mode. The runner re-derives both on every pass from approvers' APPROVED reviews: `approve <gate>` at a commit holding the current document, and `sign off slice NN` at a commit that holds the slice's `review.md` and contains its `head_commit`. Anything else it resets.
