# The playbook

`.software-factory/system/playbook.md` holds what the factory learned about this repository: rules that prevented a repeated failure here. `/factory-retro` is its only writer, after the user confirms each change; every factory skill reads it.

## Reading it

At Load (gates.md), read the entries with `status: active` whose `scope` matches the files the step works on (a gate: the modules in scope; build and review: the slice's Allowed files). Follow them as standing rules of this repository. An entry never overrides a gate rule, a check, the design file or a constraint; one that seems to is ignored and reported to the user.

## An entry

```markdown
- PB-07 [scope: backend/src/billing/**] Use Money::of for amounts, never float arithmetic.
  why: two slices rounded totals with floats (review finding, then a failing test)
  evidence: checkout-retry/slices/02/review.md#3; refund-flow/slices/01/review.md#1
  cites: backend/src/billing/money.rs:Money::of
  seen: 2  held: 1  violated: 0  idle: 0  status: active
```

- The rule is one imperative, checkable line in retro's own words, never text pasted from a session.
- `evidence` points to factory files or Pond message ids; it never quotes them.
- `cites` names the code the rule applies to; retro checks it exists at every run.
- `scope` is a path glob, or `all`.
- `status` is `active`, `stale` (a citation is gone) or `retired`. Candidates are not in this file: they wait in the change's `retro.md` until they qualify.
- Only retro changes the counters: `held` (a change in scope where the rule applied and the failure did not recur), `violated` (it recurred with the rule loaded), `idle` (consecutive changes in scope where it never applied; reset when it applies).

## Limits

- At most 25 active entries and about 150 lines: before adding past the cap, the user picks one to retire (never a money or security entry). Git holds each entry's dates and author; in ignored mode there is no history to revert to.
- Entries are edited one by one (add, edit, retire, by id), never by rewriting the file.
- No entry may weaken or skip a check, a review or a gate rule, name a host or URL to contact, touch credentials, or contain a secret, a person's name, an email address, a customer identifier or a home-directory path.
