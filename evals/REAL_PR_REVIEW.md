# Anonymous implementation review

Review each packet independently using its task, provided acceptance contract,
base, source and diff. Read only assigned packets and this rubric. Keep packet
files unchanged. Do not use network access, historical implementations, adjacent
trial records, score tables or mapping keys.

Accept when the implementation fulfills the task and disclosed API contract,
preserves relevant existing behavior, and has no identified material correctness,
security or maintainability defect. Check boundary conditions, authorization and
data handling, compatibility, error behavior, and whether the implementation
generalizes beyond fixture values. Assess architectural effects from the actual
dependencies and responsibilities. Provided tests belong to the starting input;
credit only additional tests authored in the diff.

A rejection requires a concrete missing requirement or defect, its file/symbol,
the triggering condition, and its consequence. Keep stylistic preferences and
unverified concerns as observations in the reason. The measured scope is local
implementation with offline unit verification; integration evidence may be
unavailable. Report meaningful uncertainty explicitly.

For each anonymous packet return exactly:

```json
{"verdict": "accept", "reason": "Specific assessment and any relevant limits."}
```

Use `reject` for a material issue and explain it. Freeze every verdict and reason
before learning identity or performance metrics. There is one review pass per
implementation; corrections after unblinding do not alter the measured verdict.
