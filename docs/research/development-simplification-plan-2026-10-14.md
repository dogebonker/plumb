# Development simplification: preserve discovery, remove repeated approvals

## Outcome and evidence

After the user approves the slice plan, complete routine local development, test correction, review repairs and acceptance without requesting the same authority again. Preserve the product, architecture, interface and design decisions and their existing human questions. Consolidate the interactive completion decision at the end. Headless pull-request approval authority stays unchanged.

The 2026-10-14 comparison reports Factory at 4h02m, 40 children, 1,748 responses, 18 operator questions and $36.07 estimated API cost. Conductor/direct work accounts for 39.8%, milestone review for 36%, and build for 15.5%. This supports reducing repeated review and coordination before buying cheaper coding. The numbers are observational: Factory child effort was not uniform, and the pair used a constrained Python scaffold. No promised speedup follows from this one run.

User target: development 2–3 times faster and total delivery 60–90 minutes. Measure both separately; retaining discovery means dividing total time by three is not a defensible forecast. No arbitrary deadline may convert incomplete work into accepted output.

Evidence: `docs/research/codex-fullstack-benchmark-2026-10-14.md`; `skills/factory-build/SKILL.md` sections 0–6; `skills/factory-review/SKILL.md` sections 1–6; `skills/factory-review/review-agents.md`; `skills/factory-shared/gates.md` Milestones, Send back, Headless mode.

## Scope and affected resources

Primary: `skills/factory-build/SKILL.md`, `skills/factory-build/packet.md`, `skills/factory-review/SKILL.md`, `skills/factory-review/review-agents.md`, `skills/factory-shared/gates.md`, `skills/factory-slices/SKILL.md`, `skills/factory-reconcile/SKILL.md`.

Conditional only where behavior requires it: `kit/runtime.py`, `hooks/factory_gate.py`, `runner/factory_run.py`, their tests, `evals/stages/RED-01`, `REV-01`, `REV-02`, `ACC-01` and `evals/stages/stagelib.py`. `README.md` and `evals/README.md` only for changed documented execution semantics. Do not edit FDA, benchmark accounting, transport isolation or unrelated current changes.

Complexity: MEDIUM. No new dependencies, generalized scheduler, model-routing experiment or new workflow state family.

## Acceptance and authority rules

- Existing approval of the slice plan authorizes implementation and repairs inside its frozen promises. For new plans, state this scope explicitly in the approval text. For existing plans, use actual session authorization; a state label or hash alone never supplies consent. Preserve explicit one-step/manual modes and user pause requests.
- Routine executable-test mistakes, relevant negative tests already green at the stub, and repairable failures are diagnosed and corrected locally with evidence. Do not erase/reduce required coverage or change an example to match defective code.
- Product examples, NFR budgets, public interface behavior and accepted architecture are unchanged. New requirements, relaxed promises, changed public APIs/architecture, credentials, destructive operations, Git/global configuration and security/money outcome decisions still require the appropriate authority. Batch independent questions only when a real decision is needed.
- Interactive `green -> done` is allowed only when actual initial execution approval covers the unchanged scope, fresh independent review covers the current source, and mechanical proof passes. The conductor records `Completion under approved scope` with the real approval reference and current proof; this is distinct from the final `Human Sign-off`, which remains empty until the user gives it. Missing authority or proof blocks `done`; status labels never supply either. One final interactive sign-off covers acceptance, held decisions and reconciliation drafts. Preserve headless runner APPROVED-review and sign-off derivation unchanged.
- At least one fresh independent general reviewer remains. Security/money critical checks, UI/accessibility checks when their risk changes, and final independent acceptance remain.
- User edits, dirty files, failed work and commit history survive retries and interruption. No whole-source restore/clean as routine recovery.
- Missing tools, missing proof, timeout, syntax/setup errors and unknown costs stay explicit; none become a green result.

## Ordered implementation

### 1. Lock behavior before changing prompts

Run the existing runtime, hook, runner, review-resume and stage self-checks below. Add only focused regressions needed for the changed boundary, before changing that boundary:

- Native completion provenance, exact paths, current source coverage and unresolved children remain enforced in `runner/test_runtime.py`.
- Interrupted RED verification retains live HEAD, branch, staged/dirty/untracked files; extend its existing timeout test to preservation during correction/recovery.
- Hooks retain gate document hash invalidation, allowed-file scope, UI design stamp and completed-slice protection in `hooks/test_factory_gate.py`.
- `runner/test_factory_run.py` keeps forged `done` and stale/absent PR sign-off rejected; `runner/test_review_resume.py` keeps review evidence invalidated on source changes.
- Existing RED/REV/ACC stage graders must still reject test deletion, no-assert tests, boundary violation, unauthorized extra fixes, missing review evidence, code-derived acceptance and missing independent failure evidence.

Do not replace these checks with assertions that a policy sentence exists. Test any new executable logic through its real caller. Prompt behavior requires a bounded actor exercise in step 5.

### 2. Remove redundant build orchestration and routine stops

`gates.md`, `factory-build/SKILL.md`, `packet.md`: let the conductor prepare the bounded packet and dispatch one implementation executor per slice directly. Remove the mandatory additional build step-agent wrapper. The conductor owns packets, mechanical checks and status transitions, reading packet inputs and relevant failure tails while full logs stay in artifacts. It observes the executor native terminal result, verifies the returned commit/output evidence and runs the required checks before recording `green`. The executor reports its own work and terminal result; it does not fabricate conductor-owned `green` state or wrapper handoff proof. Retain native completion checks for actual dispatched work, using existing runtime APIs only where their contracts fit, without inventing a child report for work performed directly.

Resume the same executor for local failures while its context is valid. Use a fresh executor only on unavailability or a concrete context/problem reason. Retry counts are diagnostics, not automatic requests for human permission; repeated identical failure triggers a bounded diagnosis and an explicit blocker if no recovery path exists.

Classify RED problems before remediation:

1. Existing behavior already covered: map its existing test; do not manufacture RED.
2. New negative test passes a stub because its required behavior is already present: retain it, record `red_exempt` with actual output and the unchanged fit criterion, and require independent review of that exemption.
3. Executable test is wrong but the approved promise is unambiguous: correct the test without changing its semantic expectation; preserve old test/commit, reason and before/after proof in a deviation. For corrected-test RED proof, overlay the corrected test files in an isolated pre-implementation checkout and run them there; retain original and corrected test hashes, checkout commit, command and assertion-failure output. Running the existing runtime RED helper against the original commit alone does not prove corrected tests. Run those exact corrected tests against current implementation for GREEN and retain that output. Keep original RED history and record supplementary proof rather than rewriting history; preserve the live checkout and all user changes.
4. Requirement/example or frozen contract is wrong/ambiguous: use the existing real decision/send-back path.
5. Environment/setup/timeout: evidence is inconclusive; repair setup within existing authority or record a blocker.

Remove default rewind of the entire repository on interruption or bad RED. Inspect and retain current work. A destructive restoration remains a separate authorized action. Logging a deviation never authorizes weakening tests. Retain specific allowed-file expansion for mechanically demonstrated callers/test helpers under unchanged contract and layout; unrelated files remain a scope question.

### 3. Consolidate independent review and preserve risk coverage

`factory-review/SKILL.md`, `review-agents.md`: replace four generic reviewer dispatches with one fresh read-only reviewer carrying the existing correctness, tests, design/reuse, cleanliness and hot-path efficiency rubrics. Keep prior-version comparison, concrete reproduction, complete file coverage, trusted findings validation, deduplication and independent writer/reviewer separation. Incorporate the existing bounded missing-outcome pass into that review packet rather than an extra broad source read by the conductor.

Retain specialized UI review when rendered behavior/accessibility changed; security review when trust-boundary behavior changed; money review for affected financial arithmetic/idempotency/outcomes. Decide from actual diffs and known entry points, not only file-name lists. Uncertain risk triggers the specialist; an empty or stale threat model does not prove no risk. Small non-security edits in a boundary file need not rerun a full unrelated threat analysis. Preserve existing APoSD trigger for new public symbols; keep its full scan bounded to the changed interface.

Apply demonstrated in-scope fixes, then rerun impacted checks and one scoped independent confirmation. Do not rerun unrelated full reviewer panels solely because a fix commit exists. New risk or broader edits expand review coverage. Final mechanical suite remains required at the final source revision. Use the existing isolated verification pattern for regression proof instead of temporarily restoring live production files and risking concurrent/dirty work.

### 4. Consolidate approvals and acceptance repairs

`gates.md`, slices/build/review/reconcile skills: initial slice approval describes automatic within-contract development completion. Intermediate interactive milestones transition `green -> done` only under the real initial execution approval plus fresh independent review and current mechanical proof described above. Record `Completion under approved scope` separately from final `Human Sign-Off`; proceed without repetitive sign-off and never describe autonomous completion as a new human approval. Keep headless PR behavior exactly as it is; no state-based substitute.

Within-contract failure discovered by independent acceptance is an implementation defect, not automatically a new product decision. For an active green milestone, repair in the existing authorized packet and retest. For already completed slices, retain edit protection and represent a bounded repair slice under the unchanged approved scope; record affected IDs, allowed paths, original authority and mechanical proof. If this requires changing the approved slices document, distinguish authorized implementation refinement from promise changes explicitly and retain both document versions; do not silently rehash/reapprove a changed gate. Choose the smallest consistent representation supported by existing gate checks before implementing; if no representation preserves authority, defer automatic post-completion repair and report that limit rather than weaken hooks.

Acceptance remains a fresh non-authoring agent checking every current FR/NFR/SYS criterion through actual public surfaces. Reuse only same-source, same-criterion evidence per the existing rule; changed code requires affected criteria plus shared-state regressions, and a final complete acceptance matrix. Missing/failed evidence stays visible. Incorrect requirements or unavailable proof needing waiver are held for the final real decision; actual defects are repaired before presenting completion.

Reconcile can prepare mechanical ADR/registry/product drafts while work proceeds. Ask once for the final review/acceptance/held decisions and substantive document changes. Global user-layer promotions, credentials, deployed systems and Git publication remain separate scope; no unattended global writes inferred from local build authorization.

### 5. Verify policy coherence and measure a bounded exercise

Run the existing checks again, plus narrowly added tests. Exercise a small pre-approved two-slice local task with (a) one wrong executable test under an unchanged criterion, (b) one negative test that legitimately passes the stub, (c) one review repair, and (d) one intentional frozen-interface conflict. The first three complete without user reapproval; the fourth stops with the exact decision and preserves work. Use the same task/model/effort for old/new development policies, record actual child count, response count, elapsed development time, price estimate and independent acceptance. Count setup cost separately. This exercise tests changed workflow behavior, not production-scale speed.

Acceptance for the implementation: all behavioral boundaries pass, one executor layer per slice, one general independent review per milestone, zero routine reapproval questions, no user-work loss, no unchecked or falsely passed requirement, and truthful cost/completion evidence. Report measured changes from the small exercise without promising the 60–90 minute whole-app target. The next comparable full-stack benchmark is the proper evidence for that target; do not launch another four-hour pair for this cleanup alone.

## Verification commands

From repository root, sequential where prerequisites require it:

```sh
python3 runner/test_runtime.py
python3 hooks/test_factory_gate.py
python3 runner/test_factory_run.py
python3 runner/test_review_resume.py
python3 evals/stages/check_stages.py
git diff --check
```

Read command results and preserve existing failures separately. This plan itself does not claim those checks were executed. No package-wide lint/typecheck command was established in this inspection; use the repository's actual check surface when implementation starts, and mark non-applicable checks explicitly.

## Fallback inventory and risk handling

- Full-source rewind after interrupted executor or first RED failure: masking recovery path with data-loss risk. Replace with evidence-based local continuation; preserve explicit destructive authority.
- Second failure -> ask user: avoidable delegation of diagnosis. Replace with bounded diagnosis; retain real blocker/contract decision.
- Four reviewers plus step-agent wrapper: duplicate reading/coordination. Collapse structure, retain independent review rubrics.
- Legitimate negative tests need user `red_exempt`: narrow compatibility case. Permit evidence-backed exemption, independently reviewed; never accept environment failure as RED.
- Existing exact-source review-resume, isolated RED clone, fixed-browser RED capability and headless approval rederivation: grounded fail-safe paths. Keep and test both normal and rejected cases.
- Marking `done` without real approved execution scope, fresh independent review and current mechanical proof; auto-approving modified gates; skipping unavailable security/browser checks; deleting assertions; or lowering NFRs to finish faster: forbidden masking fallbacks. Supported interactive completion under prior real authority is allowed; headless approval derivation remains unchanged.

Primary risks: consolidated review can miss issues; constrain the task and retain risk specialists/independent acceptance. Broad repair authorization can become scope creep; require unchanged frozen criteria and exact file/evidence records. Execution-time target may be unattainable while discovery remains long; report phase timing instead of concealing it.

## Handoff and stop condition

Executor owns only the resources above, accommodates concurrent FDA/benchmark work, and obtains a fresh independent review of this cleanup's authority/state boundaries. First implement prompt-only removal of redundant dispatch/approval loops; touch runtime/hook/runner logic only when a demonstrated caller mismatch requires it. Preserve headless protocol and all product/architecture questions.

Stop when changed behavior has fresh passing evidence and the bounded exercise is reported, or when an actual unresolved contract/authority decision prevents safe progress. Do not claim the large-task speed target achieved from policy edits or a tiny exercise. No commit, push, benchmark product repair or production deployment is part of this handoff.
