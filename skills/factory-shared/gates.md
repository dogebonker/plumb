# Factory gates

Shared rules for every factory skill. The factory skills install as a set, so this file sits next to them. Paths are relative to the repository root; `<change>` is `.software-factory/changes/<slug>`.

## Paths

- `<project>` is the `.software-factory` folder at the repository root: `system/` (living documents), `changes/` (one folder per change), `runs/ci/`, `runs/ui/`, `runs/security/` and `runs/prune/` (run outputs), `factory.lock`, `principles.md` (the project's principles and quiet rules) and `evals/` (the project's own eval cases).
- The framework cache is `~/.software-factory/framework/<commit>/`: `kit/`, `skills/`, `hooks/` and `bin/` of one factory commit, unpacked once per machine by `bin/factory-install` in the factory repository. Projects never edit it. Book rubrics also ship under `<kit>/packs/<name>@<hash>/`; packs.md resolves a matching bundled pin before the shared cache.
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
| product | `<change>/01-product.md` | `/factory-product` | 120 |
| architecture | `<change>/02-architecture.md` | `/factory-architecture` | 150 |
| interface | `<change>/03-interface.md` | `/factory-interface` | 200, or 250 when it designs a frontend root (factory-interface, step 2) |
| slices | `<change>/04-slices.md` | `/factory-slices` | 100 |

Track standard drafts and approves all four documents together through `/factory-plan`, in interactive mode.

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

A milestone is a group of slices reviewed and completed together (with PR sign-off in headless mode): the `Milestone` line of each original slice in `04-slices.md`, copied as `milestone` into its `status.yaml` entry. A validated derived correction has its own next unused milestone in status, without changing that approved document. A slice without one is its own milestone, and so is every slice in headless mode. A milestone's work is its slices that are not `done`; `M` is its number, or the slice id when the slice has none.

In interactive mode the conductor follows build and review directly: prepare one bounded packet, dispatch one executor per slice, perform mechanical checks, and dispatch one fresh independent read-only general reviewer per milestone plus applicable risk specialists. Route all routine source/test fixes to the existing implementation executor as one bounded validated finding batch; the conductor validates scope, commits, artifacts and native outcomes rather than writing code or duplicating the reviewer's whole-file pass. No additional step-agent wrapper is mandatory. Read relevant failure tails and packet inputs; keep complete logs in artifacts rather than repeating broad source reads.

1. Load the change, re-reading `status.yaml` before each decision/write. Unapproved gates or `sent_back` stop at the appropriate gate. Build the next open slice, review when all open milestone slices are `green`, then reconcile when all are `done`.
2. Observe actual native terminal results for every dispatched executor/reviewer and any children before consuming their evidence. A progress message, output file or resumable task is not completion. Validate returned commits, exact artifact paths and current-source proof directly; the conductor alone records its checks/status. Do not synthesize child completion for conductor work or demand that an executor claim conductor-owned `green` status.
3. Existing genuine step-agent callers retain the native handoff contract below; removing the default wrapper does not waive it for a wrapper that actually ran. Such a child returns an identity-free JSON report under the change: `state: completed|question|blocked`, `children: [{id, state}]` for actual children, `status_sha256` of final status bytes, exact existing `artifacts`, and the entire `question` when stopped. It waits for its children and reports only its own work; it never infers native routing identity.

   Consume the native task completion or question event for the dispatched agent; a message saying a child is still running is not completion. Wait through the native task API, never a shell sleep/file-existence loop, and do not guess a root `review.md` when the child returned `slices/NN/review.md`. The child must not infer its native agent/task identity. After consuming the actual native return, the parent writes a separate completion envelope with `task_id` (its dispatch token), `agent_id` (the observed native task id), `state: completed` (from the task API), and `children: [{id, state}]` from every actual child task result. Check those native states against the identity-free child report; a running task is not a completed envelope. Child-supplied routing fields are ignored. Validate the report with `python3 <kit>/runtime.py handoff --repo <repo> --report <returned JSON path> --completion <parent completion envelope path> --slug <slug> --task-id <dispatched task id> --agent-id <native agent id> --slice <NN> --expected-state <green for build, done for signed-off review>`. A review awaiting sign-off returns `question`, not `completed`. Failure: resume that exact agent with the validation error; if it is gone, recover from disk through the same skill. Do not advance or invent state to match a report. Task identities and the file hash are routing/snapshot evidence, never approval authority; the existing user approvals and edit hooks still apply.
4. Real requirement/authority questions are shown whole and actual answers passed verbatim. Resume the same agent for repairable failures. Retry counts are diagnostic; preserve dirty/untracked work and commits. Neither a task identity, hash, status label nor telemetry supplies approval authority.
5. Append one `step_tokens` event with actual agent ids and normalized usage; do not count nested rollups twice. Continue directly under approved scope, unless `--one-step`, manual pause or a genuine blocker stops execution.

**Fast lane.** Track standard, interactive mode: one milestone. Slices build in groups (factory-build, Fast lane): slice 01 alone, then each group of independent slices at once, one executor per slice, each in its own worktree (a group of one builds in the checkout). The conductor waits once per executor, with the longest timeout the harness allows, and waits again on timeout. No listing, no polling, no messages to a running executor. An executor sends no progress messages, only its final report or one blocking question. Slices stay `green` after review. A filled Completion under approved scope in `slices/<last>/review.md` marks review as finished, so a resumed session goes to reconcile, not to review again. In item 1, "reconcile when all are done" reads, for the fast lane, "reconcile when all are green and review is finished". Items 3 and 5 (the native handoff contract with completion envelopes and `runtime.py handoff`, per-step `step_tokens`) and Overlapped review apply to track critical and small, and to headless mode.

**Overlapped review.** Track critical and small, interactive mode, when a later milestone exists: once milestone N is all `green`, the conductor appends a `review_overlapped` event (History), starts N's review in the background and builds milestone N+1 meanwhile. The overlap is open while that event's milestone has a slice not `done` and every such slice is `green`; once one leaves `green` (a send-back), it closes and build returns to N. Only the milestone's latest `review_overlapped` event counts, and a `sent_back` event after it closes it for good. Build and review read it at Load. At most one review runs, and build runs at most one milestone ahead: N+2 waits until N is `done`. The review runs on a verification clone of N's `<head>` (factory-review, Overlapped review), never on the live checkout. Its fix batch, and the checks that need the running app, wait for a quiet point, when no slice is `building` or `red`. The conductor then starts no slice until the fix is committed and proven, and the impacted checks of every `green` slice, N+1's included, are rerun at the new HEAD. A send-back, or a decision that blocks N's completion (factory-review, step 5), stops N+1 immediately; Development proof inputs decide which N+1 work stays valid. The last milestone, `--one-step` and headless mode review after build, as before.

Except on the fast lane, initial slices approval must explicitly authorize bounded local implementation, executable-test correction under unchanged promises, review repairs and automatic intermediate completion. Existing plans use actual session authorization, never an inferred state flag. Interactive `green -> done` requires that real approval, independent current-source review and passing mechanical proof. Record `Completion under approved scope` with the original approval reference separately from the empty final `Sign-off`; never invent a human signature. One final real decision at reconcile covers acceptance, held review items and document drafts. Headless approval and sign-off derivation remain unchanged.

`--one-step` runs exactly one slice or milestone review, then reports the next skill and stops. A user's manual pause is honored. Contract changes, waivers, unrelated scope, destructive actions, credentials, security/money outcome decisions and publication still need the appropriate authority. Completed slices remain edit-locked. An unchanged-criterion acceptance defect uses the authorized derived-correction branch below only when all its conditions hold; other corrections use the existing genuine approval path, never silent rehashing.

## Commits

- Code commits per slice are the executor's red and green commits, plus one review fix commit per milestone. On the fast lane, a slice built in a worktree adds the merge commit that brings it back.
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

`/factory-plan` differs at four steps. Step 1: with an empty slug it uses the only change whose four gates are not all approved. Step 4: it stops only when all four gates are `approved`. Step 5: it does not stop for a missing design file, because it writes one; the hook still blocks source edits until then. Step 6: it drafts the pending documents in order, so an earlier pending gate does not stop it.

## Development proof inputs

Not on the fast lane (Milestones and autopilot), where a gate reopened by the chain check or by a send-back instead invalidates the `checks.md`, `review.md` and `acceptance.md` of every slice not `done`, and build reruns its verification.

Before selecting or skipping a build/review slice, compare every non-`done` slice's packet and receipts against the current genuinely approved gate documents and referenced inputs. Record an `Inputs` manifest in the packet/checks/review: exact path and SHA-256 for each non-skipped gate document, plus the source documents/files supplying applicable criteria, SYS promises, budgets, signatures, layout, design, rules, pack pins, adapter and verification commands. Mark skipped gates explicitly. Hash immutable input files in full. For mutable metadata such as `status.yaml` or mixed `lenses.yaml` records, capture exact effective fields/values or hash their canonical projection: commands, baseline exclusions, applicable module/layer/pack settings and verification environment. Exclude history, slice progress/commit checkpoints, completion records and the receipts themselves; source revisions remain separate proof. A progress write must not invalidate evidence, while a changed command, baseline, tool/dependency/environment or effective rule must. Matching Covers IDs or unchanged source alone is insufficient; compare the copied promises and effective rules too.

A missing manifest, changed input hash, or mismatched copied criterion/budget/signature/rule invalidates prior checks and review coverage for that non-done slice. Retain old packets/receipts as historical artifacts and append the invalidation reason to history. Refresh the packet from genuinely approved current inputs and set an affected retained-work slice to `building` (a slice without work stays `pending`) before selection, even if it was `green`. Preserve base/test/head commits and all source; reverify and repair only demonstrated mismatches, rather than rebuilding code automatically. New checks and independent review must record the refreshed input manifest before `green`/`done` or sign-off. Do not reapprove a changed gate or reuse an old receipt by merely updating its hashes.

For retained-work repair, preserve each slice's original `base_commit`, `test_commit`, head and receipts in its packet/check history before updating current status. Record its original owned commit span and each repair's start HEAD and exact correction commit span in packet/checks; this is provenance, never authority. Check the original slice-owned span and new repair spans separately against that slice's Allowed files. Do not treat unrelated later slices between the original base and current HEAD as its edits, add their files as deviations, or erase them. Current contracts, corrected-test expectations and GREEN still apply at current HEAD. The final milestone check uses the complete milestone history against the union of its packets. If ownership cannot be established from recorded commits/receipts, report the gap rather than invent a span.

A `done` slice remains edit-locked. If new approved inputs affect completed work, hold that impact for explicitly authorized corrective scope; never reopen it or treat its old review as proof of the new promises. Headless APPROVED-review derivation is unchanged.

## Autonomous local corrections

Interactive mode, not on the fast lane. New interactive `04-slices.md` plans include this mandate before actual approval:

```markdown
## Development
Mode: autonomous-local
Repairs: approved-slice-files
```

Actual initial approval of those bytes authorizes within-contract corrections confined to the selected original slices' exact Allowed files, including their planned test paths. It never authorizes changing approved document bytes, weakening criteria/contracts, or reopening completed parents. Legacy/missing-mandate plans and headless PR approvals retain their existing route; explicit manual pauses and `--one-step` still apply. A status/hash/record is provenance, never independent authority.

After independent acceptance reproduces a defect against an unchanged approved criterion, append one ordinary correction at the next unused slice ID and new milestone. Its original parents must remain `done`; preserve their base/test/head receipts and all four approved documents and hashes. Batch related failures in one consolidated change-local failure file. Derive scope only from the original headings, Covers and exact Allowed files in frozen `04-slices.md`, never mutable packets or prior corrections. A correction cannot parent another correction. No new-file, regression-test or typecheck deviation widens this scope: use existing planned test paths or the genuine slice approval path.

### Repair record and proof inputs

Write `<change>/slices/NN/repair.json` with exactly this shape (replace placeholders with actual hashes):

```json
{
  "id": 3,
  "branch": "factory/example",
  "parents": [{"id": 1, "head_commit": "<40-hex>"}],
  "criteria": ["FR-01"],
  "approved_docs": {
    "product": "<64-hex>",
    "architecture": "<64-hex>",
    "interface": "<64-hex>",
    "slices": "<64-hex>"
  },
  "start_commit": "<40-hex>",
  "paths": ["src/store.py", "tests/test_store.py"],
  "failure": {
    "path": "acceptance/failure-01.md",
    "sha256": "<64-hex>",
    "source_commit": "<40-hex>",
    "criteria": ["FR-01"]
  },
  "proof_inputs": {"path": "slices/03/inputs.json", "sha256": "<64-hex>"}
}
```

Every field is required; reject additional fields and duplicate JSON keys at every level. IDs are positive JSON integers, never booleans; directory names use at least two digits. Commit IDs are lowercase 40-hex and SHA-256 digests lowercase 64-hex. Other strings and arrays are nonempty. IDs and normalized paths are unique. The ID matches the status row/directory and is the next unused ID at creation. Every parent is an original approved heading, remains `done`, and its fixed status head equals the recorded `head_commit`. `criteria` is a unique subset of those parents' Covers; `failure.criteria` equals that set. `paths` is a unique subset of the union of their original exact Allowed files.

`approved_docs` has exactly the four gate keys. Slices is always the digest of genuinely approved status and unchanged mandated `04-slices.md` bytes. Product/architecture/interface each match genuinely approved status and bytes, or are JSON null only for an existing legitimate skipped gate on track small. Pending gates, missing approval evidence and null-for-approved substitutions fail. Criteria text comes from original small-track Requirements/Examples, or original approved FR/NFR and applicable standing criteria on standard/critical tracks.

Status must explicitly record `mode: interactive`; missing mode or headless mode cannot use this branch. `branch` equals both attached Git branch and status branch. Parent heads are ancestors of `start_commit`, which is an ancestor of actual HEAD. Failure source is a committed tested ancestor of start with no intervening source changes (planning-only commits allowed). At creation source/index/untracked source are clean and HEAD equals start. Never reset this baseline on resume.

Evidence references are change-relative POSIX paths to existing regular files inside this exact change. Source/input paths are repository-relative POSIX paths. Reject absolute paths, empty/dot/dot-dot segments, backslashes, globs, NULs, symlinks at any component and resolved escapes; hash bytes without following symlinks. Source paths cannot target `.git`, `.factory`, `.software-factory` or `DESIGN.md`. No receipt path authorizes arbitrary host reads.

The referenced immutable input snapshot has exactly this JSON shape:

```json
{
  "criteria": [{"id": "FR-01", "text": "<verbatim approved fit criterion>"}],
  "files": [{"path": "<repository-relative effective input>", "sha256": "<64-hex>"}],
  "commands": ["<exact applicable verification command>"],
  "environment": "<recorded tool/runtime/dependency environment identity>"
}
```

All fields are required with exactly these types and keys; apply the same strict duplicate/string/array/digest/path rules. Criterion IDs and file paths are unique; criteria IDs equal repair criteria and text matches original approved criteria. The conductor supplies the complete applicable Development proof inputs inventory: criteria/budgets/signatures/rules, relevant configuration and dependency manifests. Reuse captured manifests and immutable repository/change-local snapshots when bytes and effective contents still match. Needed external rules use a bounded repository-local snapshot, not an external receipt path or a recopied whole book. Exclude the receipt itself and mutable repair source files; actual commit/diff checks bind source revisions. Commands and environment are comparison strings, never executed by the validator. The conductor verifies applicability, current environment and complete coverage: byte hashes do not prove the truth of command/environment claims. A changed/missing effective input requires a new retained receipt, explicit reference update and fresh affected proofs, without changing approved hashes or scope. Missing historical receipts are not current proof.

Paths are literal filenames: framework route names such as `app/tickets/[id]/page.tsx` are allowed as exact paths, never expanded as patterns. `*` and `?` remain forbidden. Source inventory uses tracked and nonignored-untracked Git paths; ordinary ignored build/dependency artifacts do not become repair scope.

### One validator, two checkpoints

Resolve `<factory-root>` from the locked `<kit>`'s parent, containing `hooks/`. Use only the existing shared read-only hook validator:

```sh
python3 <factory-root>/hooks/factory_gate.py repair-check --repo <absolute-repo> --change <slug> --slice 03 --checkpoint edit
python3 <factory-root>/hooks/factory_gate.py repair-check --repo <absolute-repo> --change <slug> --slice 03 --checkpoint complete
```

The fixed repo/change/slice selects the record; do not accept an arbitrary metadata path or add another parser/engine. Checkpoint is exactly `edit|complete`. Success exits 0 with `repair scope valid`; failure exits 2 with a specific stderr reason. Existing stdin PreToolUse behavior stays intact. These checks prove structural scope/provenance, never approval, review or quality/completion.

Both checkpoints validate mandate, gates, strict record/inputs, paths, branch and ancestry. Reject duplicate/malformed original declared slice IDs and unsafe original scope paths; never infer a parent from a corrective status row alone. Inspect every source path touched by every commit reachable in `start_commit..HEAD`, per-parent diffs for merges with rename detection disabled so added/deleted/renamed/copied endpoints all count. A forbidden edit followed by revert fails. Include staged, unstaged and untracked source using NUL-safe Git output; Git read failure fails closed. Metadata exemptions do not widen source scope or bypass the four document hashes. The validator executes no receipt commands and writes no Git/config/status/source.

- `edit`: permits clean state or interrupted owned changes only inside exact record paths; the hook also checks the requested edit path. Unrelated dirty/staged/untracked source blocks: preserve and report it.
- `complete`: additionally requires clean source index/worktree, no untracked source, and the correction's recorded head equal to HEAD or separated only by planning commits. Existing isolated RED/GREEN, fresh native executor/reviewer completion, independent current-source general/risk review and applicable mechanical/acceptance proofs remain mandatory and conductor-owned. A control-file exemption is not completion proof.

Creation order: establish actual interactive authority and independently reproduced unchanged-criterion failure; capture clean start and immutable failure/input evidence; write only control artifacts first: record, candidate derived packet and pending status with `base_commit: <start_commit>` and null test/head; validate record and packet together via `edit`; then set building and dispatch. Do not require an already validated packet before its initial candidate exists. Invalid staged metadata stays blocked without altering parents or approved docs. Run `edit` on every resume and immediately before edits/dispatch. Run `complete` after review fixes and before recording completion, alongside actual proof checks. For mandate-bearing plans, every undeclared active ID requires valid repair metadata even if no repair flag was written.

Automatically continue validated corrections through build, independent review and independent acceptance until the complete current required matrix passes, honoring manual/one-step preferences. Changed source reruns affected and shared-state criteria; reuse only applicable current-source/current-input evidence. Not-run, timeout and setup error are never passes. Repeated identical failures trigger one bounded evidence-based diagnosis, then an authorized recovery or precise blocker; no retry-count permission handoff, endless full panels, whole-source rewind or deadline quality waiver. Real contract, waiver, security/money outcome, credential, destructive or publication decisions keep their existing gates. Final human reconciliation remains separate from technical success.

## Draft a gate document

Every gate document ends with an `## Open questions` section, empty before approval. An existing document resumes from its open questions instead of being redrafted.

## Approve a gate

Before asking for approval, check the line budget with `wc -l`. Over budget: cut repeated statements and narrative, keeping every ID, example, signature and decision. Still over: propose splitting the change into smaller changes, each with its own triage, and let the user choose between splitting and accepting the overrun.

Headless mode: commit and push the document, then wait for the user (below) with the comment "Ready for review: `<doc>`. Approve with a pull-request review whose first line is `approve <gate>`." The runner records the approval. Interactive mode, only after the user explicitly approves the document in chat:

1. `gates.<gate>` = `{ state: approved, approved_by: <git config user.name>, approved_at: <ISO time>, doc_sha256: <hash(doc)> }`
2. `notes_for_fresh_session`: "<gate> approved. Next: <next skill> <slug>."
3. Committed mode: `git add .software-factory/changes/<slug>` and commit `chore(factory): <gate> <slug>`.

`/factory-plan` approves the four gates together: same `approved_by` and `approved_at`, each gate's own `doc_sha256`, one commit `chore(factory): plan <slug>`.

## Run the next skill

Interactive mode only; headless approvals stay with the runner. Track standard runs `/factory-plan` directly in the session, with no step agent: its questions go straight to the user. On other tracks, a session that continues to the next gate skill itself, instead of the user starting it in a fresh session, runs that skill as one fresh step agent on the session's model: the product, architecture, threat model, interface and slices steps each start with an empty context. The agent receives the skill path, the slug and the answers to its own questions, nothing else from this conversation. It loads the change from disk (Load a change) and returns `state: question` with the whole question, or `state: completed` with its document's path.

The session shows each question whole and resumes that agent with the answer word for word, labelled as the user's own words. The agent treats it as the user's answer in chat and records an approval itself, as Approve a gate says. The session never answers a question, never writes `gates.*` and never writes the approval event. When the agent is gone, a fresh one resumes the document from its Open questions.

Before starting the next skill, the session re-reads `status.yaml` and checks that the gate is `approved` and its `doc_sha256` equals `hash(doc)`; after the threat model, that the last `threat_model_approved` event holds the current SHA-256 of `.software-factory/system/threat-model.md`. The agent's report is never approval. Previews, research and reviewers the gate starts are that agent's children.

## Send back

When build, review or reconcile's acceptance step finds that the approved design cannot hold, pick the target gate:

- an omitted or incorrect promised user outcome: `product` (track small: `slices`); hold the change for the appropriate human gate approval
- an approved budget is infeasible, or its storage/durability strategy cannot preserve acknowledged work: `architecture` (track small: `slices`); hold for the appropriate human gate approval
- a frozen signature cannot work as written: `interface` (track small: `slices`)
- a required change exceeds allowed scope and the user refused it: `slices`; an executable-test mistake under an unchanged promise is corrected locally with a deviation and isolated proof
- an example failed in the running product at reconcile's acceptance step: use Autonomous local corrections only for the actually authorized, validated unchanged-criterion branch; otherwise `slices`, with no slice (`slice: null`), and genuine corrective-slice approval. This exception never changes approved bytes or completed parents

Then:

1. Set the target gate and every later gate to `{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }`.
2. Set `sent_back` to `{ gate: <target>, slice: <NN or null>, reason }`, and append a `sent_back` event (ref: the slice, or `-`; detail: the target gate and reason).
3. Add the reason to Open questions in the target gate's document.
4. Committed mode: `git add .software-factory/changes/<slug> .software-factory/system` and commit `chore(factory): send back <slug> to <gate>`.
5. Tell the user to run the target gate's skill. Stop. On track standard in interactive mode, that skill is `/factory-plan`, which redrafts the reopened documents and asks one approval question for them.

## Models

Sub-agents run on the session's model, except where a skill says *smaller model*: the harness's mid-size model (in Claude Code, the Agent tool's `model: sonnet`), or the session's model when that is not larger. Only agents whose output a later step checks against files get it: research answers, which cite `path:line` that the architecture gate reads, and retro's candidates, which retro tries to disprove. The executor, the reviewers, the challenge panel and the acceptance agent keep the session's model, because their mistakes cost review time or pass unseen. Optional step agents run on the session's model; in Claude Code, `subagent_type: general-purpose`, which has the Agent and Skill tools they need.

## History

### Execution cost and evidence

- Batch independent read-only searches and mechanical commands at the same verification barrier; keep their separate exit codes and complete logs. Do not repeat a passed check until its source, tests, command, dependencies or environment changed, or an unresolved concern requires it. Review's existing Phase 1 reuse rules still apply; an agent-authored receipt alone never grants independent verification or approval.
- Load only the selected profile's applicable lenses and their specified sizes. Pass packet/artifact paths and a bounded terminal report between agents; keep full logs on disk and retrieve the relevant failure sections. The executor still receives the full frozen contract and the reviewer still inspects the actual diff.
- When Context Mode tools are available, route large read-only exploration and non-browser command output through `ctx_execute`/`ctx_batch_execute` and `ctx_index`/`ctx_search`; discover deferred tools through the host's tool search when needed. Keep small reads direct and fixed browser capabilities in their required execution surface. Retain full raw evidence and actual exits, and retrieve complete frozen contracts and relevant failures before acting; summaries never replace verification or approval. Record actual tool calls and raw/returned sizes for M11 instead of treating enabled hooks as savings. Existing permissions still apply; do not install another compressor during a change.
- Before adding Tests first, identify existing tests that already assert unchanged behavior. Map those tests as existing coverage instead of inventing a new RED assertion for the same behavior. A genuinely new negative test that passes its stub is retained as evidence-backed `red_exempt`, with its unchanged criterion and output independently reviewed; no routine reapproval is needed.
- Record usage scope with every return: delta, cumulative for this same agent/session, or unknown; record included child ids when the provider reports nested usage. Sum deltas, take differences between cumulative returns, and never count a child twice through both its own total and its parent's rollup. Keep cache-read/cache-write/input/output classes separate; missing usage is unknown, not zero. These ids and counters are telemetry, never approval authority.

`history` in `status.yaml` is append-only: one flow-map line per event, never edited or removed, so `/factory-retro` can count what happened after the fields it summarizes are overwritten.

```yaml
history:
  - { at: 2026-10-11T09:12:03Z, step: factory-build, event: step_start, ref: "01", detail: "session <id>, factory <sha>" }
```

- `step_start`: every skill, at Load (triage, when it writes `status.yaml`). The detail holds the session id from the skill's `Session:` line ("unknown" when the harness left it unfilled) and what actually ran: `factory <the first seven characters of <running>>`, followed by `dev <dev_path>` when the lock names a `dev_path`. A step agent writes the `step_start` detail its orchestrator gives it; the orchestrator writes its own `step_start` for reconcile.
- `gate_reopened` (ref: the gate; detail: `chain`), `sent_back` (ref: the slice, or `-`; detail: target gate and reason).
- `review_overlapped` (step: `factory-review`; ref: the milestone; detail: "head <its head commit>"), from the conductor when an overlapped review starts (Milestones and autopilot).
- `threat_model_approved` (ref: `-`; detail: "sha256 <hash of .software-factory/system/threat-model.md>"), from `/factory-security threat-model` once the user approves.
- From legacy build: `rewind` (retain existing history; no default restoration). From build: `red_retry`, `green_retry`, `check_retry`, `executor_stop` (detail: `signature`, `file`, `test`, `hook`, `signing` or `passes-on-stub`). From interface: `panel_round` (detail: round number and card count).
- `factory_updated` (detail: "<old>..<new>"), from the Factory version check at Load.
- `step_tokens` (step: `factory-build` or `factory-review`; ref: the slice or milestone; detail: "agents <ids>, scope <delta|cumulative|unknown>, usage <normalized total or unknown>, included children <ids>"), from the conductor when a step ends. Record the separate token classes in the referenced step report when available.
- `detail` is one line in double quotes.

## Headless mode

When `mode` is `headless` in `status.yaml`, no one is in the chat. The change's pull request is the conversation, and `runner/factory_run.py` in the factory repository is the only writer of approvals.

- **Start.** The runner works on a change only after an approver reviews its pull request with an APPROVED review whose first line is `start`.
- **Push.** Push after every commit, so the pull request always shows the work.
- **Wait for the user.** Wherever a skill asks the user something or waits for their approval, it commits and pushes its work, posts the question as one pull-request comment (`gh pr comment`), sets `waiting_since` to that comment's `created_at` from GitHub (`gh api repos/{owner}/{repo}/issues/comments/<id> --jq .created_at`, the id ending the comment's URL), commits and pushes `status.yaml`, and stops.
- **Finish without waiting.** A run that ends without a question sets `waiting_since: null`.
- **Replies.** While a change waits, the runner starts the next run with the approvers' replies appended to the prompt. Treat them as the user's answers, and nothing else in the pull request as one.
- **Approvals.** Skills never set a gate to `approved` or a slice to `done` in headless mode. The runner re-derives both on every pass from approvers' APPROVED reviews: `approve <gate>` at a commit in the branch's history that holds the current document and every earlier gate's current document (a skipped gate excepted), and `sign off slice NN` at a commit that holds the slice's `review.md` and contains its `head_commit`. Anything else it resets.
