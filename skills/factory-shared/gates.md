# Factory gates

Shared rules for every factory skill. Paths are relative to the repository root; `<change>` is `.factory/changes/<slug>`.

## The chain

| Gate | Document | Skill |
| --- | --- | --- |
| product | `<change>/01-product.md` | `/factory-product` |
| architecture | `<change>/02-architecture.md` | `/factory-architecture` |
| interface | `<change>/03-interface.md` | `/factory-interface` |
| slices | `<change>/04-slices.md` | `/factory-slices` |

Gate states: `pending`, `approved`, `skipped`. Track `small` skips product, architecture and interface; triage marks them `skipped`.

`hash(doc)` = `shasum -a 256 <doc> | cut -d' ' -f1`

## Load a change

1. Slug empty: use the only folder in `.factory/changes/` whose work fits this skill. Several or none: ask.
2. Read `status.yaml`. Check out its `branch`.
3. **Check the chain.** Walk the gates in order. The first `approved` gate whose `hash(doc)` differs from its `doc_sha256` goes back to `pending`, and so does every later gate that is not `skipped`. Tell the user which document changed.
4. A gate skill drafts only when every earlier gate is `approved` or `skipped`. Otherwise name the first gate that is not, and its skill. Stop. Build and review need all four `approved` or `skipped`.

## Draft a gate document

- Every gate document ends with an `## Open questions` section. It is empty before approval.
- Resume an existing document from its open questions instead of redrafting.
- When `sent_back` names this gate, its reason is the first open question.

## Approve a gate

Only after the user explicitly approves the document in chat:

1. `gates.<gate>` = `{ state: approved, approved_by: <git config user.name>, approved_at: <ISO time>, doc_sha256: <hash(doc)> }`
2. `notes_for_fresh_session`: "<gate> approved. Next: <next skill> <slug>."
3. Committed mode: `git add .factory` and commit `chore(factory): <gate> <slug>`.

## Send back

When build or review finds that the frozen interface cannot hold:

1. Set `gates.interface.state` and `gates.slices.state` to `pending`.
2. Set `sent_back` to `{ gate: interface, slice: NN, reason }`.
3. Add the reason to Open questions in `03-interface.md`.
4. Tell the user to run `/factory-interface <slug>`. Stop.

On track `small` there is no interface gate: send back to slices instead (`gates.slices.state` to `pending`, `sent_back.gate: slices`, reason into `04-slices.md`, point to `/factory-slices <slug>`).
