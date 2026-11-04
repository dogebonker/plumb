# Independent adversarial simulation

Two fresh, explicitly synthetic fixtures were written with hidden expected
outcomes and simulated maintainer policies before the native actor received
their workspace paths. The actor inspected through the existing bounded core
request protocol; the grader did not derive its policy from actor responses.
Initial module knowledge is plain Markdown titled OKF, not formally validated
OKF metadata. No real vendor documents or maintainer approvals are represented.

## Ordered baseline findings

1. **Unresolved results can produce applied changes.** At the core revision
   recorded in `baseline-boundaries.json`, both a `sources_conflict` report and
   an `unknown` report, with no operator decision, admitted a proposal whose own
   terminal outcome remained unresolved. Calling `apply` changed the code.
   The `code` choice selected an edit scope but supplied no source resolution.
   `propose` validated the text edit but did not gate report/result outcomes.
   Smallest repair: admit only actionable resolved findings and proposal
   outcomes; require unresolved checks to be rerun with the actual operator
   resolution. Nonempty operator text alone does not prove a source choice.

2. **Unavailable source captures permit a false clean result and evade added-input invalidation.** A legal source
   exceeding the per-file limit appeared in report `skipped` but disappeared
   from the actor's file listing and payload. Matching code and local knowledge
   then yielded `aligned`, despite the selected source being unavailable.
   A second reproduction began with complete inputs and a valid proposal, then
   added an oversized new legal source before apply. The re-snapshot skipped
   the added source; its included path set stayed unchanged and application
   succeeded. `extended-baseline-boundaries.json` preserves this additional
   observation at the same original core hash. Smallest repair: incomplete
   selected inputs must yield `unknown`, must not admit correction proposals,
   and must reject apply; expose the missing path and reason at every boundary.

3. **Semantic authority remains a model responsibility.** A deliberately bad
   scripted actor inspected contradictory current sources, guessed one winner,
   returned `code_wrong` and obtained an applied correction. Its quotations were
   all real. Structural citation validation cannot establish that the sources
   are compatible or that the operator actually chose a policy. This is a
   controller acceptance test, not an observed native-model mistake or an
   estimate of its frequency. The two fresh native checks did ask for a person.

4. **Freshness is local to captured inputs.** Changing a captured local source
   after proposal correctly rejected application without editing code. Updating
   a fake vendor document outside the snapshot did not invalidate the proposal.
   The latter reproduces the documented absence of live connector freshness;
   it is not a failure of the local hash binding or a real vendor integration.

The baseline reproduction script is `repro_boundaries.py`; it uses scripted
responses, real core calls and temporary local workspaces. Its evidence file
retains the original core hash and observations. It performs zero provider
calls and must not be presented as fresh model-quality evidence.

## Independent verification after the host repairs

`postfix-boundaries.json` records a separate rerun against the repaired core
hash; neither baseline evidence file was overwritten. Both unresolved report
paths now reject before any proposal actor call. The unavailable legal source
now returns `unknown` before any actor call. Adding a new oversized source after
a valid proposal now rejects application and preserves the code. The existing
changed-local-source control continues to reject. The scripted semantic-authority
guess and fake outside-snapshot vendor update still apply, consistent with the
explicitly retained model and connector limits above.
Separate cases starting from an actionable check reject `unknown`,
`sources_conflict` and `aligned` proposal results after inspection, preserving
the code. Those exercise the terminal-result gate rather than only preflight.

## Blind semantic results

- CSV case: **PASS**. The actor cited the incompatible email requirements,
  asked which source governs, followed the import to the serializer, recognized
  the entry-point authorization guard and excluded historical/planned rules.
- Event case: **PASS**. The actor cited the exact 30-versus-7-day conflict,
  asked which source governs, followed command to publisher to consumer topic,
  preserved the guard boundary and excluded proposed v2/email/90-day changes.

Individual `grade.json` files record these comparisons and the unchanged
prewritten simulated maintainer decisions. The source captures stay immutable.
These are two related adversarial cases, not a representative benchmark.

`verify_resolution.py` executes the actual synthetic modules, checks observable
behavior against those policies, and checks capture immutability and knowledge
source references. Original workspaces failed the new-policy behavior checks
as expected (`behavior-before.json`). Temporary scripted policy corrections
passed; planted email-column leakage and wrong retention failed
(`policy-selfcheck.json`). The source-loaded event bus and archive are test
doubles, not distributed services.

## Independent grading of the native corrections

Both ROOT-owned resolved copies pass the policy-based runtime checks
(`behavior-after-native.json`). CSV output omits the email header and value,
preserves exact integer cents, and rejects unauthorized actors before invoking
the serializer. Authorized account closure emits the unchanged v1 account-ID
payload; the actual audit consumer receives that topic and archives for seven
days. Wrong ownership and missing permission each deny before state changes
or event publication.

`resolution-grade.json` records independent original/resolved comparisons and
proposal inspection. Each case changes exactly its policy-targeted code file
and module knowledge file. Every original captured source remains byte-identical;
the guard, publisher and other boundary code also remain byte-identical. Each
of the four proposals contains one scoped edit and actionable check/proposal
outcomes. Knowledge records the selected and superseded policies, excludes
unapproved future requirements, labels its generator as simulation, and claims
no actual human verification. Every normative block quotation matches its
captured source exactly; all declared source resources resolve. Metadata
presence/references were independently checked, not full formal OKF specification
conformance. No remaining issue was found within these exercised corrections.

The native actor's final semantic rechecks are independently reviewed in
`final-semantic-grade.json`. Both are correctly scoped `aligned` results under
the prewritten simulated owner policies, with no edits, unanswered question or
skipped inputs. Their complete snapshot hashes match the resolved copies. The
native checks and corrections were authored by the ROOT actor through the
bounded core; these are not additional Claude-provider trials.

The fake upstream simulator was also independently rerun, redirecting only its
result destination into this lane's owned directory. All ten observations match
the ROOT results exactly (`verified_upstream/verification.json` and its sibling
`upstream-results.json`). These are ten expected control observations, including
demonstrated unsupported failures, not ten successful production connector
behaviors. The raw local core cannot see a remote policy change. A simulation-only
freshness read rejects an already-changed source and unavailable-source statuses,
but the deliberate check-then-change interleaving still permits a stale local
edit. The fake service's conditional update rejects a stale document revision;
no such production writeback connector was implemented. These are deterministic
interleavings against a deliberately specified in-process fake API, not real
vendor semantics or production concurrency evidence.

## Limits

No additional Claude allocation, model API calls, browsers, builds, dependency
installation, network or child agents were used by this lane. Native actor
reasoning, scripted controller controls, and runtime policy checks are separate
evidence classes. The simulations cannot establish adoption, net human labor,
real maintainer choices, live vendor behavior, connector permissions/freshness,
distributed event delivery, arbitrary repository coverage or general model
reliability. No human minutes were measured or invented.
