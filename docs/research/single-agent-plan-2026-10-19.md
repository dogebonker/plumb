# Single-agent execution change

User direction: remove the prescribed Sonnet swarm. One Opus 5.5 lead handles the
feature and uses bounded native Opus subagents when useful. The user's follow-up
explicitly retains subagent usage and independent review.

## Cleanup plan

1. Lock the current contract, scope, frozen-input, approval, gate, retry and usage
   behavior with the existing controller/contract tests before changing execution.
2. Add regressions for serial dependency order even with three ready slices,
   stopping before any later slice after a replan proposal, and the Opus 5.5 model
   on both the native command and provider receipts.
3. Delete prescribed parallel slice dispatch and its thread-pool/frontier machinery.
   The persistent lead handles ready slices and may delegate bounded independent
   subtasks within the active slice. Preserve source, accepted commits and failures.
4. Allow new plans to omit the old Opus-share ceiling. Keep an explicitly supplied
   legacy ceiling binding; never rewrite approved pilot plans or remove token/time
   budgets. Continue reporting model usage and cost independently of quality.
5. Give the ordinary skill path the same persistent Opus lead and useful native
   delegation, removing forced per-slice workers and parallel-oriented scaffolding.
   Keep recovery instructions for worktrees from existing interrupted runs.
6. Preserve mechanical gates, genuine human decisions and independent review.
   Helpers inherit the pinned Opus model and current scope/frozen guards; all must
   complete before the slice gate. Never label self-review independent.
7. Update current docs and append a superseding decision. Keep historical benchmark
   results, approval-bound pilot contracts and measured receipts unchanged.

## Verification

Run the targeted controller, contract, legacy-runner and hook checks; then the
relevant runner suite and Python static checks. No paid model run, application
deployment, benchmark rerun or approved-contract mutation is needed for this change.

## Native delegation boundary

The v2 lead can call the configured `factory-helper`. Its tools are limited to
Read, Grep, Glob, Edit and Write under the inherited hook. Native model forcing
pins helpers to `claude-opus-5-5`; background tasks and nested delegation are
disabled. Independent helper calls may run in parallel inside the active slice.
The legacy headless default pins the lead and helper model too. Root provider
usage includes its helpers and is charged once through cumulative snapshot deltas.

Claude Code 2.1.303's installed schema confirms cumulative resume counters.
The [subagent documentation](https://code.claude.com/docs/en/sub-agents) documents
model inheritance/forcing and tool allowlists; the [hook reference](https://code.claude.com/docs/en/hooks)
confirms children invoke the parent's configured PreToolUse hooks. Native execution
of the revised controller remains unvalidated; tests mock the provider boundary.

## Verification results

- Existing baseline: 34 controller and 11 contract tests passed before edits.
- Regressions first failed for the old fan-out, mandatory model mix, missing
  session reuse, denied helper delegation and inherited ambient Sonnet setting.
- Broad runner check: 152 tests passed. After the helper changes, all 41 controller,
  13 contract and 11 hook tests passed again; the legacy runner's assertion checks
  also passed with the forced helper-model regression.
- Ruff and whitespace checks passed. Independent review found no remaining defect.
- No paid model trial, deployment, benchmark rerun or publication was performed.
