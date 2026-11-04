# Second pilot: source conflict and applicability

Status: prospective protocol for the next model run, 2026-11-03. The source
history is retrospective. Original first-pilot inputs, scripts and results stay
unchanged.

## Claim to test

Can the same model distinguish an implementation mismatch from contradictory,
superseded or merely proposed intent, and ask for missing evidence? Does a small
module bundle preserve the source meaning while reducing irrelevant material?

## Sources and cases

Use Pond's public Claude Code restore-path module around commit `a218ef3`.
The old Windows plan includes an NFC-normalization claim. The correction says
that claim is wrong. The updated plan contains both its correction and the old
bullet. Capture all three documents and the exact before/after code from Git.
No uncommitted files, Rust execution, external service connectors or source
modification are involved.

Six diagnostic cases are fixed before model execution:

1. Current correction + fixed implementation: aligned.
2. Current correction + old implementation: implementation mismatch.
3. Old claim and correction both binding under an explicit controlled operator
   policy that disputes the correction's retirement authority: conflict; ask a
   person, do not silently choose the newer one. This synthetic authority framing
   is identical in both arms; active roles alone would not erase a correction.
4. Updated plan explicitly supersedes its own old assertion: aligned, without
   treating the retained old bullet as an unresolved active promise.
5. Current correction plus an opposing future proposal: aligned with current
   intent; the proposal does not itself make current code defective.
6. Current correction plus only the restore caller, without the encoder/decoder:
   insufficient implementation evidence; do not invent the missing behavior.

Cases 3 and 5 are **controlled source-role presentations** of real historical
text, not claims that the real project had exactly those approval states. The
other cases are analyst-provisional interpretations of historical evidence.
There are six related scenarios about one behavior, not six independent bugs.
There is no maintainer-approved ground truth or actual prospective PR yet.

## Fair comparison and budget

Raw arm: complete captured source documents with their declared roles.
Bundle arm: module-relevant, **verbatim** passages from those same documents,
with identical source IDs/roles and original-source links. No paraphrased
replacement requirement is permitted. Both arms get the same code excerpts and
the same task. The bundle's selection is known-module curation, not automatic
retrieval or a tested dependency graph.

Use `claude-sonnet-5-5`, low effort, fresh independent CLI evaluation per arm/case,
one at a time. Alternate arm ordering. Twelve evaluations maximum, $2 aggregate
admission budget, at most $0.25 per invocation, 90 seconds per invocation. Retain
exact prompts, schema, code, labels, provider output and input/protocol hashes.
No retries or tuning after viewing results. Uncompleted cases stay unrun.

## Evaluation contract

Return code status (aligned/mismatch/unknown), source status
(compatible/conflict/unknown), whether human action is needed,
cited source/code evidence, a brief explanation and one question when needed.
For contradictory active rules without established precedence, code status is
unknown and source status is conflict. A characterized human question is a
finished analysis; missing required code remains unknown.

Locate source quotes against the **original captured document**, permitting
whitespace-only wrapping differences and restoring the exact original span.
Require unique source matches; ambiguous matches are errors. Code quotations
remain exact. A source conflict requires both source citations; a positive
code judgment requires a code citation. Report semantic label agreement and
evidence validity separately. No outcome must be inferred from citation
existence alone.

`needs_human` includes approving a corrective action for an established mismatch,
choosing between conflicting rules, or supplying required missing evidence.
It does not mean that a known mismatch is an unfinished analysis, and it grants
no permission to execute a correction.

Record preserved-versus-changed source wording, raw/bundle input sizes, observed
provider list cost, failures and pending questions. One run cannot establish a
repeatable latency/cost advantage. Human curation/review time remains null until
a person measures it. Do not turn this controlled probe into a claim of customer
adoption or general accuracy.
