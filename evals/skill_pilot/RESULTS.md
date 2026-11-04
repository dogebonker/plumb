# Skill-first implementation and controlled forward test

Date: 2026-11-04. The standalone [Plumb skill](../../skills/plumb/SKILL.md) is
implemented, with conditional substantial-change guidance and four walkthroughs.
The CLI exposes `skill` and `skill --path` without model inference. The root
[README](../../README.md) explains the skill-first product and uses new artwork.

## Independent native forward test

A separate native Codex subagent used the draft skill on an isolated, synthetic
Python ingestion module. It received the requested behavior and original source
material, not a proposed implementation. It wrote a change record, implementation,
tests, and a knowledge update. No additional Claude CLI calls were made. Native
host token usage was not available; this was not a zero-inference experiment.

- Baseline accepted batches and wrote every item. Existing cases passed.
- Added rejection checks failed before implementation in four list/iterator
  subcases, confirming that the checks exercise changed behavior.
- The correction rejects more than five items before any storage call.
- Three tests with 19 subcases verify preserved counts/order for zero through
  five and rejection for six/nine, including zero storage calls.
- Direct execution separately confirms existing store contents survive rejection.
- The module knowledge records observed behavior, the source, checks, and the
  finite-request memory limitation. It does not invent human verification.

The subagent also inspected two concurrently applicable retention sources: delete
at 30 days versus retain for 90. It asked which rule governs on day 31, holding
that change while preserving the source files. No destructive operation ran.

The [fixture and evidence](fixture/), including the original staged baseline,
are preserved with [content hashes](manifest.json). Recheck hashes and reproduce
the baseline/red/green behavior without any model calls:

```sh
python3 evals/skill_pilot/verify.py
```

This rechecks saved code behavior. It does not rerun the agent or prove skill
interpretation is repeatable across models.

## Refinement from observed overhead

The draft produced 55 lines across three spec files for a four-line behavior
change. The implemented skill now permits one brief requirement/approach/check
note for a bounded, clear single-module change. Separate requirements/design/tasks
remain appropriate when scope needs them. A follow-up read-only routing check
confirmed both the copy-edit and small behavior-change cases continue without a
new approval question. The original fixture is retained unchanged, including its
three-file change record; it reflects the earlier draft's execution.

## Release checks

- 46 prototype tests pass, including new skill output/path and missing-package
  behavior. The model constructor is not reached by documentation commands.
- 14 existing historical pilot tests pass.
- The controlled fixture's three tests pass, and its four before-fix failure
  subcases are independently reproduced by `verify.py`.
- Installed skill-creator validation passes. Local links, examples, and skill
  references resolve. CLI examples are parsed with `--help`, without execution.
- Independent read-only review found no material code/permission/spend defects.
  Its later documentation mismatch was corrected to match small-change routing.
- Ruff passes for production Python, the artwork generator, and the verifier.

## README artwork

A new procedural engineering plate replaces the old factory animation. A fixed
plumb line connects knowledge, a spec, implementation, checks, and knowledge
updates. The retention change is explicitly illustrative.

`assets/intent-loop.gif` is 960×480, 59 encoded frames, and 38,707 bytes. It plays
three 8.04-second cycles and ends on the finished plate. A matching static SVG is
selected for reduced-motion preferences and linked directly. Both formats use
matching geometry; the SVG supplies a title and description. The finished PNG
was visually inspected at full size and the producer checked a 700-pixel preview.
The generator validates frame variation, loop endpoints, dimensions, duration,
and file size. Regenerate with the already available Pillow dependency:

```sh
python3 assets/intent_art.py
```

One local generation took 1.69 seconds with a reported peak RSS of 144,261,120
bytes. This is an observed development run, not a portable performance claim.
Pillow is for regenerating artwork; the Plumb CLI has no new dependencies.

## Limits

No real cross-project reuse, customer adoption, live SaaS capture, OpenProse
execution, or browser/GitHub rendering test ran. The native forward test is
controlled and synthetic, not a general accuracy benchmark. The skill guides
host behavior and is not a sandbox. The prior 12-call Claude allocation remains
exhausted; there were no additional Claude CLI calls in this implementation.
