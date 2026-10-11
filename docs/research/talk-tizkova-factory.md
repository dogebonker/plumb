# Notes: "What It Actually Takes to Build a Software Factory"

Tereza Tížková, Factory (factory.ai), AI Engineer, published 2026-09-27, 22 minutes. [Video](https://www.youtube.com/watch?v=vGCJ7diEtrw). Notes taken 2026-10-11 from the auto-generated transcript.

Source weight: a vendor talk about Factory's own product (Droid, Missions). Its numbers are Factory's own benchmarks or unnamed (a "Stanford" chart, a Coinbase CEO tweet). Treat the claims as ideas to test, not evidence.

## What she said

1. **A factory is the whole loop**, not a coding agent or a swarm: collect signals (user feedback, logs), prioritize, orchestrate, execute, validate, test in production, iterate, and keep learning. Writing code is the easy part.
2. **Three properties:** agnostic, autonomous, always improving.
3. **Agnostic.** Work where people already work (Slack, GitHub), let them bring their own subscriptions, and do not bet on one model.
4. **Model routing.** Classify the task's difficulty (prompt, codebase, tools), pick the cheapest model predicted to clear the bar, switch up when it fails. Claimed: about 25% saving on their conservative benchmark, plus speed and provider failover. Related cost tricks: non-frontier default models, caching, no spend limits but results expected from big spenders.
5. **Loops need a verifiable "done".** Open-ended tasks make done hard to define. Long autonomous runs are growing but still not reliable. Agents cheat: they pass the test instead of meeting the intent.
6. **Missions.** An orchestrator writes a *validation contract* before any code. Workers run **in sequence, not as a swarm**, each with fresh context, each free to fan out sub-agents. Validators judge code they did not write and send feedback back to the start. In one 16-hour customer mission, validation took 40% of the time.
7. **Two validators.** *Scrutiny*: linters, types, tests, code shape. *User testing*: uses the product in a virtual machine, clicks through it, ignores how it was built. Her example: a migration that looked right in code but was not interactive; only the clicking validator caught it.
8. **Deferred context.** Tools load as short descriptions; the full schema loads only when used. Claimed 50%+ token saving at scale.
9. **Power law of adoption.** An unprepared codebase gets worse with agents, and the damage compounds. Their "agent readiness" check: reproducible dev environment, tests, docs, style, linters, with recommended fixes.
10. **Unwritten rules.** People keep repeating to agents how they want things done. Their answer: packaged skills and context, and documentation the agent updates itself.
11. **Humans move up a level:** decide what to build, not how. Agents absorb alignment work (status, syncs).

## Where the factory already stands

| Her point | Factory today | Verdict |
| --- | --- | --- |
| Validation contract before code (6) | Slices gate names each test and what it asserts; constraints registry maps every ID to enforcement; packet carries fit criteria | Covered, and stricter: a human approves the contract |
| Sequential workers, fresh context (6) | Fresh session per gate, fresh executor per slice, slices built one at a time | Covered |
| Validators judge code they did not write (6) | Review agents are fresh and separate from the executor | Covered for review. Not for tests: the executor writes both the red tests and the code (A2) |
| Scrutiny validator (7) | Review Phase 1 scripts plus `/polish` | Covered |
| User testing validator (7) | Only on UI: the UI/UX lens renders routes, React Doctor scans at runtime. Nothing runs the product's FR examples against the running app | **Gap** (A1) |
| Anti-cheating (5) | Red tests must fail on the stub commit and stay unchanged; fix-commit tests must fail when the fix is reverted | Mostly covered. Hole: a test that only calls a stub fails red on the stub error and passes green with no assertion (A2) |
| Agnostic (3) | Open skills format; runner hard-codes `claude -p` | Covered where it matters |
| Model routing (4) | No model choice anywhere: every sub-agent inherits the session model | Gap, low value (A3) |
| Deferred context (8) | Harness already defers tools; language packs load an index, then one rule | Covered |
| Agent readiness (9) | Triage finds the three commands, records `baseline_failures`, proposes missing linter rules, picks `legacy` for untested code | Mostly covered. Flaky tests are not detected (A4) |
| Unwritten rules (10) | Retro, evidence-gated playbook, calibrated principles | Covered, deliberately stricter than self-updating docs (X4) |

## Adopt

All four were accepted on 2026-10-11 and applied as decision 26 in [../DECISIONS.md](../DECISIONS.md).

**A1. Black-box acceptance run before reconcile. Priority: high.**
A fresh agent gets only the FR examples (`01-product.md`; track small: `04-slices.md`) and a way to run the product: `dev_command` and `dev_url` for a service or UI, the binary for a CLI. It never sees code, packets or reviews. It drives the running product (browser for UI, HTTP for an API, the shell for a CLI) and reports pass or fail per example, with the evidence it saw. A defect the user confirms sends the change back to the slices gate, and the fix comes as a new slice: rewinding an earlier signed-off slice would also undo every slice built after it.
Why: every check the factory runs today is code the executor wrote (tests) or code read by a reviewer. Nothing confirms the agreed examples hold in the running system. This is her strongest point, and the inputs already exist.
Cost: one agent per change. Triage must record a run command for every runnable module, not only for packs with runtime checks. Libraries skip it: their tests are the surface.

**A2. Tests must assert the example. Priority: low, cheap.**
One clause in the executor's red step and one rubric line for polish's cleanliness agent: each Tests-first test asserts the concrete outcome of the FR example it covers, not only that the call returns. A1 catches most of what weak tests let through, so a separate test-writing agent is not worth its cost yet. Revisit if retro shows slices passing review and failing A1.

**A4. Flaky tests at triage. Priority: medium.**
Run `test_command` twice at triage. A test that fails in either run joins `baseline_failures`, which red and green already exclude; those that failed once are named as flaky. One list, because red and green treat both the same. Today one run sets the baseline, so a flaky old test can fail red or green and cost a retry.
Cost: one extra suite run per change.

**A3. Model tiers by role, not a router. Priority: low, conditional.**
Only if token cost or rate limits are a real constraint. The scarce resource here is human review time, and a weaker executor costs more of it. Applied: a smaller model only for agents whose output a later step checks against files: research (answers cite `path:line` the architecture gate reads) and retro's candidate reader (retro tries to disprove each). The executor, reviewers, panel and the A1 acceptance agent keep the session's model: a missed failure there passes unseen. No escalation logic is needed while the executor runs on the top tier.

## Reject

- **X1. Autonomous intake and prioritization** of logs and feedback. Prioritization is a product decision, and the product gate is the human's.
- **X2. Weeks-long unattended runs.** The factory's premise is that the human reads every diff. Her own reliability chart says long runs are not dependable yet.
- **X3. A learned difficulty classifier.** One user's volume cannot train or measure one. Static tiers (A3) get most of it.
- **X4. Self-updating docs and skills.** The retro research found agent-written context rarely helps; the playbook stays evidence-gated with user approval.
- **X5. Caching and deferred tools** are the harness's job, not the factory's.

## Useful reference point

Her mission spent 40% of its time in validation. The first measured change here spent 49% of its wall clock at the interface gate before the round cap. Retro can report the review share per change against that number.
