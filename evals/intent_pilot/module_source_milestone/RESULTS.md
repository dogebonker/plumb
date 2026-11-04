# Module initialization and connected Git source milestone

Completed 2026-11-04. This delivers the next usable step: initialize one real
module's draft knowledge, detect changes to one versioned source, and prevent
old corrections from proceeding after that source changes.

## Real public module

[`examples/pond-claude-code`](../../../examples/pond-claude-code/knowledge/index.md)
contains three committed Pond adapter files, a complete committed spec capture,
and a draft OKF 0.2 root/module/contract. The contract imports **6.6 Ingest order
and integrity** verbatim. It makes no claim that a human approved the import or
that the adapter satisfies it.

- Repository: `https://github.com/tenequm/pond`.
- Commit: `b049b2e8ba3a418ad54eebe738c9d8fbe8a8d1c3`.
- Source: `docs/spec.md`, Git blob `9ff4dca9355d75b338737d8150b077dadb58e163`.
- All three code files and the 115,498 source bytes match committed blobs.
- The selected 2,464-byte heading subtree is unchanged in the draft contract.
- Status is `current`; repeated refresh is `unchanged`, preserving all bytes,
  capture inode and modification time. The original dirty Pond checkout remains
  unchanged. [Verification record](verification.json), [verifier](verify_example.py).

Reproduce against this checkout (or initialize a new workspace for another clone):

```sh
python3 evals/intent_pilot/module_source_milestone/verify_example.py /Users/dan/Work/pond
```

## Source-change exercise

[`plumb.test_connected`](../../../plumb/test_connected.py) uses real temporary
Git commits through the actual CLI, with scripted model responses solely to
exercise the source/version guards:

1. Initialize a module with `value = 1` and a source requiring two.
2. Check and propose a code correction bound to that source version.
3. Commit a source change requiring three. Status becomes `changed`.
4. Old apply is rejected; check/propose fail before model construction.
5. Refresh captures the new committed source, preserving code, knowledge and
   connection configuration. The old correction remains invalid.
6. A fresh check and proposal can apply `value = 3` to the isolated workspace;
   repeat application is idempotent. Original repository code remains untouched.

These are boundary/control tests, not evidence of semantic model accuracy.

## Validation

- [44 prototype tests pass](tests.txt), including real Git initialization/refresh,
  unavailable/tampered sources, credential-free origin metadata, literal Markdown
  headings, excluded-path rejection, nonregular file rejection, and source
  changes during inference/apply/refresh.
- [14 earlier pilot tests pass](pilot-tests.txt).
- [Ruff passes](lint.txt).
- [Prior model workflow replay passes](replay.txt): ten original saved requests
  matched exactly, and the existing six-behavior repair/recheck sequence passed.
  Replay creates iteration `0006`; it does not make new inference calls.
- Independent native review reproduced three defects; all three were fixed and
  independently rechecked with no remaining finding in that scope.
- **Zero new Claude calls**. The prior authorization ledger remains at 12 calls.
  No network access, Rust build, local model, GPU work or dependency installation
  was needed for this milestone.

## Implemented surface and limits

[`plumb/workspace.py`](../../../plumb/workspace.py) implements `init`, `status`
and atomic source-only `refresh`. The existing core takes a source-verification
callback; the CLI wires it to the explicitly supplied `--source-repo`. A connected
workspace cannot silently run through the unconnected core path. New reports,
proposals and application receipts bind the connection and source/capture bytes.
The [usage guide](../../../plumb/README.md) documents the full flow.

Freshness means the selected **local Git ref** at verification time. Nothing
fetches origin or reads Notion/Confluence/Jira/Linear. Refresh does not resync
code, rewrite reviewed knowledge or push corrections upstream. Apply/refresh
assume an isolated, serial workspace; a concurrent editor or ref movement can
still race the final verification/write boundary. No new semantic verdict was
made on the real Pond module, and this does not establish product demand or
general accuracy.
