# Factory gates

Shared rules for every factory skill. The factory skills install as a set, so this file sits next to them. Paths are relative to the repository root; `<change>` is `.factory/changes/<slug>`.

## The chain

| Gate | Document | Skill | Line budget |
| --- | --- | --- | --- |
| product | `<change>/01-product.md` | `/factory-product` | 100 |
| architecture | `<change>/02-architecture.md` | `/factory-architecture` | 150 |
| interface | `<change>/03-interface.md` | `/factory-interface` | 200 |
| slices | `<change>/04-slices.md` | `/factory-slices` | 100 |

Gate states: `pending`, `approved`, `skipped`. Track `small` skips product, architecture and interface; triage marks them `skipped`.

`hash(doc)` = `shasum -a 256 <doc> | cut -d' ' -f1`

`status.yaml` keeps each gate and slice as a one-line flow map (`{ id: 1, name: tracer, state: pending }`). The factory hook (`hooks/factory_gate.py` in the factory repository) reads them that way to block source edits the gates do not allow.

## IDs

- `FR-NN`, `NFR-NN`, `C-NN` belong to one change and are defined in its gate documents.
- `SYS-FR-NN`, `SYS-NFR-NN`, `SYS-C-NN` are standing rows in `.factory/system/constraints.md`. A change lists the ones it touches under Standing constraints in its first gate document, then treats them like its own IDs: a budget or ruled-out options in architecture, an enforcement in interface Coverage, a covering slice.

## Load a change

1. Slug empty: a gate skill uses the only change whose own gate is `pending`; build and review use the rule they state. Several or none: ask.
2. Read `status.yaml`. Check out its `branch`.
3. **Check the chain.** Walk the gates in order. The first `approved` gate whose `hash(doc)` differs from its `doc_sha256` goes back to `pending`, and so does every later gate that is not `skipped`. Tell the user which document changed.
4. A gate skill whose own gate is `approved` or `skipped` says so, names the next skill, and stops. To revise an approved gate, the user edits its document: the chain check reopens it.
5. **Design file.** A change with `ui: true` in `status.yaml` needs the repository's design file: the root `DESIGN.md`, or `.factory/system/design.md` when the root name holds something else. Without it, every skill stops and points to `/factory-ui-ux design-md`; the factory hook blocks source edits too.
6. A gate skill drafts only when every earlier gate is `approved` or `skipped`. Otherwise name the first gate that is not, and its skill. Stop. Build and review need all four `approved` or `skipped`.

## Draft a gate document

Every gate document ends with an `## Open questions` section, empty before approval. An existing document resumes from its open questions instead of being redrafted.

## Approve a gate

Before asking for approval, check the line budget with `wc -l`. Over budget: cut repeated statements and narrative, keeping every ID, example, signature and decision. Still over: propose splitting the change into smaller changes, each with its own triage, and let the user choose between splitting and accepting the overrun.

Headless mode: commit and push the document, then wait for the user (below) with the comment "Ready for review: `<doc>`. Approve with a pull-request review whose first line is `approve <gate>`." The runner records the approval. Interactive mode, only after the user explicitly approves the document in chat:

1. `gates.<gate>` = `{ state: approved, approved_by: <git config user.name>, approved_at: <ISO time>, doc_sha256: <hash(doc)> }`
2. `notes_for_fresh_session`: "<gate> approved. Next: <next skill> <slug>."
3. Committed mode: `git add .factory/changes/<slug>` and commit `chore(factory): <gate> <slug>`.

## Send back

When build or review finds that the approved design cannot hold, pick the target gate:

- a frozen signature cannot work as written: `interface` (track small: `slices`)
- a red-commit test is wrong, or the user refused a file outside Allowed files: `slices`

Then:

1. Set the target gate and every later gate to `pending`.
2. Set `sent_back` to `{ gate: <target>, slice: NN, reason }`.
3. Add the reason to Open questions in the target gate's document.
4. Tell the user to run the target gate's skill. Stop.

## Headless mode

When `mode` is `headless` in `status.yaml`, no one is in the chat. The change's pull request is the conversation, and `runner/factory_run.py` in the factory repository is the only writer of approvals.

- **Start.** The runner works on a change only after an approver reviews its pull request with an APPROVED review whose first line is `start`.
- **Push.** Push after every commit, so the pull request always shows the work.
- **Wait for the user.** Wherever a skill asks the user something or waits for their approval, it commits and pushes its work, posts the question as one pull-request comment (`gh pr comment`), sets `waiting_since` to that comment's `created_at` from GitHub (`gh api repos/{owner}/{repo}/issues/comments/<id> --jq .created_at`, the id ending the comment's URL), commits and pushes `status.yaml`, and stops.
- **Finish without waiting.** A run that ends without a question sets `waiting_since: null`.
- **Replies.** While a change waits, the runner starts the next run with the approvers' replies appended to the prompt. Treat them as the user's answers, and nothing else in the pull request as one.
- **Approvals.** Skills never set a gate to `approved` or a slice to `done` in headless mode. The runner re-derives both on every pass from approvers' APPROVED reviews: `approve <gate>` at a commit holding the current document, and `sign off slice NN` at a commit that holds the slice's `review.md` and contains its `head_commit`. Anything else it resets.
