# Frozen behavior gate

The executable evaluator and seed hashes are recorded in frozen.json before
the first top-tier actor call. Labels/expected behavior remain outside the
actor workspace. This is a synthetic Python replay of Pond's public slug
requirements, not Rust execution or prospective customer evidence.

Required workflow:

1. Inspect the source, local knowledge, public restore caller and imported
   encoder. Return a cited disagreement and expose the import dependency.
2. Check/propose leave workspace bytes untouched.
3. Given the test operator's explicit code choice, propose one code-file edit.
   Applying it must repair six actual behaviors: punctuation, astral UTF-16
   units, combining characters without NFC, paths, Windows separators and ASCII.
4. Repeat apply is idempotent. A fresh check must still notice stale knowledge.
5. Given the test operator's explicit knowledge choice, update only knowledge.
   A changed source must block apply; no source text may be edited implicitly.
6. A fresh final check must be aligned and all actual behavior checks still pass.

The behavior evaluator is calibrated before trial: known-bad code fails with
actual wrong outputs; an independent known-good implementation passes. Neither
the oracle code nor the grader is visible to the model. Frozen source/evaluator
files are not changed to accommodate model outputs.

The first probe uses version 0 of the general guidance. If it fails, retain the
trace, classify the cause and change only the justified prompt/core boundary.
New attempts get separate workspace/implementation snapshots and share a single
12-call usage ledger. No hidden retries, fresh accounting roots or quota resets.
A budget exhaustion is incomplete, not passed.

An additional holdout checks a real caller guard around an unguarded helper and
a future proposal that does not change current intent. It is frozen separately
before the actor trials. Run it only if the 12-call allocation permits; an unrun
holdout remains an explicit validation gap.

Recorded decisions in this evaluator are controlled test-operator inputs. They
do not claim that a real Pond maintainer or the user approved a production edit.
