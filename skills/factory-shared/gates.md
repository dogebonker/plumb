# Factory gates

Shared rules for every factory skill. The factory skills install as a set, so this file sits next to them. Paths are relative to the repository root; `<change>` is `.factory/changes/<slug>`.

## The chain

| Gate | Document | Skill | Line budget |
| --- | --- | --- | --- |
| product | `<change>/01-product.md` | `/factory-product` | 100 |
| architecture | `<change>/02-architecture.md` | `/factory-architecture` | 150 |
| interface | `<change>/03-interface.md` | `/factory-interface` | 150 |
| slices | `<change>/04-slices.md` | `/factory-slices` | 100 |

Gate states: `pending`, `approved`, `skipped`. Track `small` skips product, architecture and interface; triage marks them `skipped`.

`hash(doc)` = `shasum -a 256 <doc> | cut -d' ' -f1`

## Load a change

1. Slug empty: a gate skill uses the only change whose own gate is `pending`; build and review use the rule they state. Several or none: ask.
2. Read `status.yaml`. Check out its `branch`.
3. **Check the chain.** Walk the gates in order. The first `approved` gate whose `hash(doc)` differs from its `doc_sha256` goes back to `pending`, and so does every later gate that is not `skipped`. Tell the user which document changed.
4. A gate skill whose own gate is `approved` or `skipped` says so, names the next skill, and stops. To revise an approved gate, the user edits its document: the chain check reopens it.
5. A gate skill drafts only when every earlier gate is `approved` or `skipped`. Otherwise name the first gate that is not, and its skill. Stop. Build and review need all four `approved` or `skipped`.

## Draft a gate document

Every gate document ends with an `## Open questions` section, empty before approval. An existing document resumes from its open questions instead of being redrafted.

A document fits its line budget (`wc -l`) before approval. Over budget, cut repetition and prose first. Still over, the change is too big for one pass: propose splitting it into smaller changes, each with its own triage.

## Approve a gate

Only after the user explicitly approves the document in chat:

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
