# Twelve-call checkpoint: the bounded end-to-end workflow works

The current prototype passed its executable workflow gate and the separate
caller-guard holdout. This demonstrates local source/code/knowledge
reconciliation, explicit correction choices, actual file application and fresh
rechecking on controlled fixtures. It does not establish the whole product on
arbitrary repositories, live SaaS sources or real maintainer workflows.

## What the strong model did

Claude Fable 5.1 at high effort chose which files to read, followed the public
restore function's import to the encoder, and compared implementation with the
operator-selected source and a stale OKF document. It produced the source/code
citations, human question, dependency links and exact proposed edits.

The frozen replay started with a real kind of Pond bug: encoding only slashes
and dots when native session paths require one dash per non-alphanumeric UTF-16
unit, with no NFC normalization. The local knowledge also described the wrong
rule and pointed to an unapproved proposal.

The workflow then:

1. Diagnosed the code mismatch without changing files.
2. Given a controlled test-operator choice to fix code, proposed one encoder edit.
3. Applied that proposal; six actual Python behavior checks passed, including
   astral characters, combining characters, Windows separators and plain ASCII.
4. Rechecked and still identified stale module knowledge.
5. Given a separate test-operator choice, corrected the knowledge and its source
   reference while preserving the governing decision's wording.
6. Rejected application when a captured source changed; repeated application was
   idempotent. A fresh final check was aligned and the behavior checks still passed.

The holdout used a different domain: document deletion. A public entry point
checks ownership before calling a helper that has no authorization check of its
own. The model traced that dependency and correctly returned aligned. It also
kept a future proposal separate from the current agreement.

These are synthetic Python fixtures inspired by a public Pond requirement.
The authority/choice inputs are test-operator fixtures, not actual user or Pond
maintainer approvals. No Pond source or live external documents were edited.

## What changed during improvement

The initial candidate completed the code repair and detected stale knowledge,
but the host rejected the already-chosen knowledge correction because the model
did not ask another human question. The model was right to leave it empty at
that stage. The controller now distinguishes check-time questions from an
explicitly chosen correction. A regression test preserves that distinction.

Saved actor responses were reused only after exact equality checks of each
original system prompt and payload. Their outputs were unchanged. No additional
inference was spent repeating accepted work. Calls 9–10 performed the final
fresh check; calls 11–12 exercised the holdout.

Measurement review found a grader default argument still pointing at the seed
workspace. The original evaluator and binding remain archived; the corrected
gate checks the actual iteration workspace. All ten saved actor inputs were
then replayed through the strengthened gate with inference disabled. Expected
outcomes and runtime checks were not weakened. See [the improvement log](DECISIONS.md).

Independent offline review also reproduced CLI artifact writes bypassing the
separate-apply boundary, including hardlinked output files. Those paths now
reject in-workspace destinations, and all CLI/model artifacts use atomic
replacement rather than truncating existing entries. The reproductions were
captured as failing tests before the fixes and now pass.

## Usage and evidence

- Exactly **12 serial Claude Fable 5.1 CLI calls**, each a separate provider
  session; no model-side tools, subagents, hidden retries or model fallbacks.
- Provider-reported disjoint token classes total **61,919 tokens**, including
  cached input. This is not a reliable percentage of Claude Max allowance.
- The ledger reports **$1.346071 in API-equivalent list cost**. The CLI was
  authenticated through Claude Max; this number is not a confirmed charge.
- No local model/GPU execution, repository build, indexing or browser process
  was started for this hill-climb. Runtime tests are small isolated Python tests.

The latest [workflow evaluation](evaluation.json) passes all five compound
stages. The [holdout evaluation](holdout-evaluation.json) passes. The latest
candidate is [iteration 0004](iterations/0004/evaluation.json); its model outputs
were exactly replayed, not regenerated. [Replay evidence](candidate-replay.json)
records the unchanged inputs. [Independent review](FINAL_REVIEW.md) reports PASS
within the bounded scope and retains the failures and their fixes.

The final package passes **21** focused CLI/core/model tests. The earlier
pilot's **14** evidence-boundary tests still pass. Ruff and whitespace checks pass.
Receipt verification preserves the original historical pilots separately.

## Runnable result and next reassessment

[The prototype guide](../../../plumb/README.md) documents:

```sh
python3 -m plumb check MODULE_WORKSPACE --decision 'CURRENT SOURCE SELECTION' \
  --output REVIEW/report.json --receipts REVIEW/receipts
python3 -m plumb propose REVIEW/report.json --choice code \
  --output REVIEW/proposal.json --receipts REVIEW/receipts
python3 -m plumb apply REVIEW/proposal.json
```

Reports and receipts must be outside the reviewed workspace. `knowledge` is
the other correction choice. Recheck after each application; resolving one
side does not imply every disagreement disappeared.

The current limit is deliberate: selected text workspaces, existing module
knowledge and local source captures, one file per proposal, isolated application.
Automatic initial module/bundle discovery, live Notion/Confluence/Jira/Linear
connectors and upstream document writes are not implemented. Neither are a
complete cross-service dependency graph, production concurrent-writer guarantees
or human curation/adoption measurements. Those require separate evidence.

The next useful validation is one real module with untouched source exports
and actual maintainer choices. The controlled gate proves the machinery can
perform the loop; it cannot supply the team's intended behavior or prove that
maintaining the knowledge is worth the effort. The approved 12-call allocation
has been used, so further model trials stop here for reassessment.
