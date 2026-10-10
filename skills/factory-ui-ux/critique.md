# Critique protocol

How factory-ui-ux forms, anchors and ranks opinions. Sources: NN/g heuristic evaluation and severity ratings, the cognitive walkthrough, Shape Up, GOV.UK's design principles, the Linear method, and the standards in the user's `ui-hard-gate`; evidence in `docs/research/ui-ux/C-opinions.md` of the factory repository.

## Order

1. **Anchors.** The design file (principles, positions, words), the product gate's user, job and success metric, the constraints.
2. **Mechanical facts.** The pass in SKILL.md step 2. Never re-judge them.
3. **Walk the primary job** on each rendered screen and viewport. At each step ask: will the user try to do this; will they see the control; will they recognize it as the way; will they know it worked. A "no" is a finding, labeled `predicted`: it is a model's prediction, not a user test.
4. **Cut test** on every element: a candidate to cut when it has no action or explanation, duplicates another path, shows a status nobody defined, serves no job, has no evidence of demand, sits at a third level of disclosure, or is a screen with no new action.
5. **Heuristics and WCAG** only for problems steps 3 and 4 did not explain.

## Writing a finding

A challenge card, argued fairly: the current design's case first, then the objection, the alternative and what it costs. Two rules on top:

- **Anchored:** to a principle (P#), a position, a word, the success metric, or a WCAG criterion. Unanchored is taste: it caps at `note`.
- **Prediction / check:** what you would observe if the objection is right, and how to check it (a walkthrough step, a measurement, a usage number). No check caps at `note`.

The fix is the cheapest that works, in this order: delete, merge, make it a default, collapse it, restyle it. A cut names exactly what stays.

## Severity and volume

- `block`: the primary job fails a walkthrough step, a screen misstates the state of the work, a refusal of the design file is broken, or a WCAG A or AA criterion fails.
- `fix`: anchored, costs time or errors on the main path, and has a check.
- `note`: everything else.

Within a level, rank by frequency, then impact, then persistence. At most 3 `block` or `fix` findings per screen and 7 per review, plus one cut proposal per screen and one line on what works.

## Disagreement

An overruled finding is recorded and not raised again for that change. A rule overruled three times drops to `note` through calibration. When the user overrules a position of the design file itself, propose amending the design file instead of repeating the objection.

## The user's standing preferences

From `ui-hard-gate`, the PM's recorded feedback on the user's product; general enough to apply everywhere, while product-specific rules belong in that product's design file:

- show the headline, put detail on demand; "too much" is the most frequent complaint
- density both ways: neither cramped nor needlessly large
- honest states: "Something went wrong" is never enough; one loading style; fail closed
- name the work, never the machinery
- one filled primary button per surface; at most one secondary link per dialog
- copy matches what the backend actually does, and states each fact once
- look at every state in a real browser before handing anything over
