# Stage cases

Five cases that each put one factory skill in a known start state and score what it leaves behind: review recall and precision (REV-01, REV-02), a real red (RED-01), acceptance on the running product (ACC-01) and the research firewall (FW-01). Python 3.10 or later, standard library only.

Each `<ID>/` holds:

- `case.json`: the entry command (build and review use `--one-step`, so no orchestrator continues to the next step), mode, planted faults with their lines, scores, `stop_when`, `timeout_s` and `max_turns`. `stop_when` is a list of `{path, regex}`, relative to the workspace: the trial stops once every file exists and its regex matches (an empty regex only needs the file).
- `fixture/` and `setup.py <target>`: the git history plus `.software-factory/` state (`factory.lock`, `system/`, the change), with real SHAs and gate hashes.
- `answers.json`: the scripted user, as `{kind: {match, reply}}`. The first `match` regex that fits a question gives the reply, and `default` matches anything. `recommended` means "your recommendation".
- `grade.py <workspace>`: prints one JSON line of scores between 0 and 1, plus `pass`. Hidden tests and mutants in `grading/` are copied into an export of the workspace only when grading.
- `oracle/apply.py <workspace>`: the ideal end state. Each `oracle/wrong_*.py` is a plausible wrong end state that must fail.

Check the cases without a model:

```sh
python3 evals/stages/check_stages.py
```

For each case it builds the start state and checks that the factory hook and the chain check accept it and that its public tests pass. Grading the untouched setup must fail, grading the oracle must pass, every wrong end state must fail, and `stop_when` must hold for the oracle but not for the untouched setup.

## Trial runner requirements

No runner drives these cases yet: wiring them into the trial runner (setup, an agent run with `answers.json` as the scripted user, then grade) comes next. The runner must:

- Install only a `git archive` of `kit/` and `skills/` as the trial's framework cache, `~/.software-factory/framework/<commit>/`, never this repository: a link to it would expose `grading/` and `oracle/` to the agent.
- Install it at the commit `setup.py` wrote as `factory_commit` and as the framework commit in `.software-factory/factory.lock` (this repository's HEAD), or Load's version check asks questions no answer covers.
- Kill the trial's process group when the trial ends, so a dev server the agent started does not outlive it.
- For ACC-01, read the answers with the port resolved from `<workspace>/.git/acc01-answers.json`. `setup.py` picks a free port for the dev server, writes it into `lenses.yaml` and resolves `{port}` there.

Pond and the `modern-python` language pack are not available in trials: research answers that would come from Pond are "not found", and packets name the pack without it being installed.

## Findings for the factory

Numbered as reported; all nine are fixed in the skills. By impact: B1, B4, B2, B3, B9, B6, B5, B7, B8.

| ID | Finding | Status |
| --- | --- | --- |
| B1 | Track small had no source for frozen signatures: build copied them only from `03-interface.md`. | Fixed: the small-track `## Interface` section of `04-slices.md` (factory-slices, factory-build step 2). |
| B2 | A review fix could not add a regression test: Tests first files are held for the user and a new file is outside Allowed files. | Fixed: factory-review step 6 lets a fix add a test file, logged as a deviation. |
| B3 | No mode ran exactly one step: interactive build and review start the autopilot, and headless needs a pull request and a remote. | Fixed: `--one-step` (gates.md, Milestones and autopilot). |
| B4 | `research.md` had no template, so a grader could only guess where questions and answers are. | Fixed: factory-architecture step 2.4 gives its form, one numbered question with its answer indented under it. FW-01's grader also reads two numbered lists. |
| B5 | A start state depends on the kit version through `factory_commit`; a different kit makes Load ask questions. | Fixed: the version check asks nothing when no field is missing, and a start state pins its kit to `factory_commit` (gates.md, Load a change). |
| B6 | A pending slice's packet is always rewritten by build step 2, so "pending with a packet" is not a separate state. | Fixed: a packet records the gate hashes it was written from, and build reuses a pending slice's packet when they still match. |
| B7 | Send back does not say whether `approved_by`, `approved_at` and `doc_sha256` are cleared when a gate goes back to `pending`. | Fixed: a gate sent back or reopened becomes `{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }`. |
| B8 | The Example line has two formats: its own bullet in `01-product.md`, indented under the FR in small-track `04-slices.md`. | Fixed: the Example line sits indented under its FR in every template; older bullets are still read (gates.md, IDs). |
| B9 | `review.md`'s Polish line has a `<severity>`, but polish's severities are not defined, so `block` and `fix` cannot be counted reliably. | Fixed: factory-review's Polish line maps polish's recommendation (fix is `fix`, skip is `note`; `block` only from lens cards). |
