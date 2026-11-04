# Substantial changes

Use the project's existing change folder and naming convention. If none exists,
use a local `changes/<slug>/` folder with `requirements.md`, `design.md`, and
`tasks.md`. These are change documents, not mandatory runtime state. For a small,
clear change, keep the relevant requirements, approach, and checks in one note.
Split the files when the scope needs it; omit irrelevant sections.

## Requirements

Record the requested delta and preserved behavior with stable requirement IDs.
Each requirement needs a concrete scenario and an observable expected result.
Attach the source locator, captured revision or `version unknown`, relevant
passage, applicability, and status: agreed, imported/unreviewed, or proposed.
An actual user request can establish the requested delta; identify it as such.

Preserve normative strength: a source SHOULD remains a SHOULD. Put strengthened
or changed obligations in an explicit proposal or actual decision. Record open
decisions only where the answer changes implementation; proceed on settled work.

Example after a user requests a five-item batch limit:

> R1 — New request: a batch MUST reject more than five items before storage.
> Source: current user request, captured in the change record; no source revision.
> Scenario: six valid items arrive; response identifies the limit and storage
> receives no writes. Preserve the accepted behavior for batches of zero to five.

The example obligation belongs to this example request, not to other projects.

## Design

Describe the smallest implementation that satisfies the requirements, citing
relevant code paths and existing conventions. Include changed interfaces, data,
events, errors, and migration/rollback consequences only when applicable.
Separate observed behavior from the proposed design.

List known consumers/producers and module owners where discoverable. Identify
dependency inspection gaps, including dynamic imports, external API callers,
event consumers, or shared-data writers. Explain whether each unknown blocks a
task, limits the claim of completion, or can be checked within the request.
Avoid declaring compatibility from a successful local test alone.

## Tasks and evidence

Make tasks executable in dependency order, each tied to a requirement and check.
Keep task state and verification state separate: an edited file does not pass a
test, and a failed test does not prove a requirement was satisfied.

| Task | Requirement | Work | Check / evidence | State |
| --- | --- | --- | --- | --- |
| T1 | R1 | Validate batch size at the existing ingress | Six-item request is rejected; storage spy sees zero writes | Pending |
| T2 | R1 / preservation | Keep supported batch behavior | Existing zero-to-five cases still pass | Pending |
| T3 | R1 | Update module contract with observed result and request source | Contract links implementation and T1/T2 evidence | Pending |

Replace descriptions with actual project commands/cases and results as work runs.
For example, record `fail — test_batch_limit: six items reached storage`, repair
the defect, and retain the later passing result. Record `not run — integration
service unavailable` with the affected requirement and remaining uncertainty;
do not mark it passed or silently waive it. A rejected weakening of a requirement
is not a test fix. Ask for a genuine changed governing choice only if needed.

On resume, read the current diff, task evidence, source revisions, and recorded
decisions. Continue incomplete tasks and invalidate only evidence affected by new
changes. Reconcile verified results into the module bundle; retain the change
record as the history of the delta.
