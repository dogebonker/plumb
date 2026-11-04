# Final independent verification

## Verdict

**PASS — the bounded core workflow, holdout and repaired CLI artifact boundary are supported by independent local checks.** Verification used current code, original receipts and fresh temporary workspaces. No provider/model invocation occurred during this review.

## Proven behavior

- `python3 -m unittest plumb.test_cli plumb.test_core plumb.test_model -v`: all 21 tests pass, including the corrected distinction between a check requiring a question and an already-chosen proposal permitting an empty question.
- Independently replayed calls 1–10 through current `reconcile`, `propose` and `apply`. Every system prompt and payload matched the saved input exactly before returning its saved response. This was a fresh controller/behavior execution, not acceptance of `evaluation.json` or `candidate-replay.json` self-reports.
- On an independently populated temporary workspace: initial diagnosis was cited `code_wrong` with the restore→encoder dependency and question; check/propose preserved all captured bytes; explicit code choice changed only `code/slug.py`; all six public restore-path behavior checks passed; repeat apply returned `already_applied`; recheck identified `spec_stale`; explicit knowledge choice changed only `knowledge/module.md`; changing the governing source rejected apply without modifying knowledge; final fresh check was aligned and behavior still passed.
- Final workspace bytes and the initial/intermediate/final reports' traces, snapshots, hashes, evidence and links match `iterations/0003`. Core/prompt hashes match that iteration; subsequent CLI/model artifact-write changes were independently regression-tested below.
- Independently replayed calls 11–12 with exact inputs: holdout report was aligned, cited the caller's authorization guard and imported unguarded helper, treated the future proposal as unadopted, and left bytes untouched. Saved holdout report and workspace match the fresh replay. This confirms inspected scenario reasoning, not a general authorization audit.

## Accounting and measurement integrity

Exactly 12 sequential call receipts contain 12 distinct provider sessions, all successful `claude-fable-5-1`. Raw stdout, stored provider envelope and returned response agree. Independently summed provider usage is **61,919 tokens and $1.34607075 provider list cost**; this is not an invoice. Calls 1–8 belong to the failed initial controller attempt, 9–10 supply the final recheck, and 11–12 supply the holdout. Replay added zero inference calls.

The archived evaluator matches `frozen-v1.json`; the only current evaluator difference is changing `hashes(workspace=WORKSPACE)` to resolve the active workspace at call time. Current evaluator hash matches `frozen.json`; seed hashes and behavior-program hash are unchanged across versions. Fresh replay directly verifies the stronger gate. The failed first attempt remains recorded. These bindings establish retained content consistency; they do not independently authenticate historical freeze timing.

## CLI boundary verification

Initial review reproduced `check WORKSPACE --output WORKSPACE/code/main.py` overwriting captured code without apply. The containment fix now rejects it with exit 2 before model construction, preserving bytes. Regressions also cover propose/knowledge overwrite, receipt directories inside the workspace and symlink output into a reviewed file.

Review then reproduced an external hardlink alias bypassing path containment and overwriting captured code. The final fix routes every CLI report/proposal and model prompt/receipt write through `plumb/artifacts.py:write_json`: serialize into a private temporary file, flush/fsync, then `os.replace` the artifact entry. Re-running the original hardlink reproduction now preserves reviewed code and creates a valid report at a distinct inode. The model prompt-archive hardlink regression also passes. All 21 local tests pass with zero inference. No confirmed material blocker remains within this isolated-workspace scope.

## Limits

Operator choices are simulated fixture inputs, not actual user/maintainer approval. This is an isolated Python, Pond-inspired demonstration: no Rust/customer repository, SaaS connector writes, production concurrency guarantee, adoption evidence or measured human maintenance effort.

Skipped: new inference, network, browser and builds. Remaining risk: concurrent writers remain unsupported; the 12-call evidence cannot establish general model reliability.
