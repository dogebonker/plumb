# Walkthroughs

These are illustrative requests and outcomes, not extra project requirements.
Read only the case matching the current decision.

## Direct edit

Request: correct a misspelled settings label without changing behavior.

Read the owning module entry, component, and label consumers; check whether the
text is translated, used as an accessible name, or asserted in a UI test. Record
the scope and relevant check briefly, update the label and directly affected
fixtures, run the relevant check, and inspect the diff. A new change-spec folder
or full knowledge rewrite adds no value. If the bundle does not repeat the label
or state an affected contract, report that no knowledge edit was needed.

Expected result: finish the authorized edit with evidence and any unrun UI check
visible. A routine local edit needs no new approval.

## New behavior

Request: reject batches over five items before any item is stored.

Read the ingestion module's OKF entry, current validation, storage boundary,
callers, and applicable source requirements. For this bounded change, one brief
note can record R1, the ingress approach, and tasks tied to a rejection test and
existing valid-batch checks. Split requirements/design/tasks into separate files
when callers or changed contracts make the scope substantial. If an API client cannot
be inspected, record that coverage gap rather than implying all callers work.

Implement at the existing ingress, run the cases, inspect the diff, and update
the module contract with the new rule, request provenance, and actual results.
Keep unavailable integration checks `not run` with their impact on confidence.

Expected result: finish verified local work; claim only the compatibility checked.
Do not invoke another model CLI to write or review these documents.

## Conflicting sources

Request: implement the documented retention period. A captured Confluence policy
requires deletion after 30 days; a captured Linear ticket requires keeping the
same records for 90 days. Both apply to the same customer/data period, neither
supersedes the other, and project policy names no governing source.

Retain both passages and their available revisions. Show the concrete conflict:
on day 31, must those records exist? Ask which obligation governs this scope.
Hold the retention change and destructive checks while inspecting independent
code/tests. A newer capture timestamp alone does not settle authority. Record
the user's actual choice and any limits before implementing dependent tasks.

Expected result: a bounded decision question, then implementation when answered.
If a pre-existing decision already resolves applicability, cite it and continue
without asking again. Do not rewrite either external source as an implicit step.

## Stale source

Request: resume an unfinished change. Its captured repository spec said five
items, but the source now says eight. Read the changed passage and its context:
an accepted replacement changes the requested behavior; a draft proposal does
not automatically replace an existing commitment.

For a connected Plumb workspace, `status` can reveal selected local Git changes
and `refresh` can capture the new bytes. Neither action reconciles the knowledge
or settles the requirement. Compare revisions, update applicable spec/tasks,
rerun affected checks, then update knowledge from the resulting evidence. Keep
unaffected work. If using only an exported Notion page whose upstream version is
unavailable, record `version unknown` and the export capture date instead of
claiming it matches live Notion.

Expected result: continue when applicability is established; ask only if a real
governing choice remains. With no extra provider allocation, use host reasoning
instead of `check` or `propose`; a prior exhausted allocation does not reset.
