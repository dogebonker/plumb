---
name: factory-plan
description: Plan a standard-track factory change in one pass - one discovery round, the four gate documents drafted together, one approval.
disable-model-invocation: true
argument-hint: "[slug]"
---

# Factory plan

Usage: [per-skill accounting](../factory-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Slug: $ARGUMENTS
Session: ${CLAUDE_SESSION_ID}

Gate rules: [../factory-shared/gates.md](../factory-shared/gates.md). On track standard this skill drafts the four gate documents together, from one discovery pass, and asks for one approval. Each document keeps its gate skill's template; track critical still runs those skills one at a time.

Track standard, interactive mode only. On another track, or in headless mode, name the gate skill that runs instead (`/factory-product`, or `/factory-slices` on track small; headless changes keep their pull-request approvals) and stop.

## 1. Load

Load the change as gates.md describes, for the `product` gate, with its `/factory-plan` exceptions: it runs while any of the four gates is `pending` and drafts only the pending documents. An existing document resumes from its Open questions and Assumptions. All four approved with matching hashes: continue directly to the next unfinished build/review/reconcile stage. Never reopen an earlier gate to add detail needed by a later one.

## 2. Research in the background

Only when pending architecture has unanswered research questions, start research before round 1: [../factory-architecture/SKILL.md](../factory-architecture/SKILL.md) step 2, items 1 to 4, in the background. Reuse recorded answers; ask only the missing questions. Its questions name only code, data and records that exist at `change_base_commit`, so none names a product rule. Run no experiment unless a Budget depends on behavior the documentation leaves unclear, and then at most one. Later implementation evidence goes into `research.md`, without rewriting approved architecture.

## 3. Discovery

Phrase every question in the brief's own nouns ("Can a player edit a post after someone replies?", not "Is data mutable?"), so a short reply suffices.

Follow gates.md **Explain questions and decisions**: keep the questions and one-round batching, but give concrete examples, recommended outcomes and trade-offs. Share a small diagram across related flow/access/persistence questions when it helps; simple choices stay brief. On revisions, show the impact table and ask only changed decisions, leaving compatible architecture/security approvals intact.

On resume, skip topics already answered or approved. If product is approved, read its decisions as fixed inputs and ask only a concrete unresolved decision in a pending gate; do not repeat discovery or regenerate the product/design documents.

**Round 1, one message.** Ask about each topic below that the brief, the repository and `.software-factory/system/` do not already settle. Number the questions. Give your proposed answer with each one.

1. **Users and roles.** Who will use it, in what roles, how many, on which devices. How people get in (accounts, invitations, sign-in) and how each person is shown to others (name, display name, alias).
2. **Who may see and do what between users.** For each thing a user creates: who can see it and who can act on it. Anything private between some users, and every place it must never leak: lists, search, counts, previews, notifications, history. Any tool people use to protect themselves or each other (safety, consent, blocking, reporting) and who learns that it was used.
3. **Data lifecycle.** Create, edit (by whom, until when), delete or withdraw, what happens when a person leaves or is removed, how things are closed, ended or archived, and what history is kept afterwards.
4. **Failure and durability.** What "saved" means. What the user sees and keeps when a save fails or the connection drops. Two people acting at the same time, and editing from a stale copy. What happens when stored data is damaged or unreadable.
5. **Vocabulary.** What the users call each role, thing and action, and the words that must never appear on screen. These become the Glossary.
6. **Brand voice.** How the product should sound, with two or three example lines for real moments (an empty state, a success, an error), and where the voice must be plain with no flavor (safety, errors, removals, money).
7. **Visual direction.** Look and feel, themes, the devices that matter most, any reference products, two or three named products it must never be mistaken for, the accessibility bar, and the quality bar for this release (a finished daily tool or a working prototype). Offer the optional 2 to 3 feature examples of [../factory-ui-ux/references.md](../factory-ui-ux/references.md) here, once, when triage has not.
8. **Non-goals.** Name the three to five features a user of this kind of product would expect (for example notifications, reactions, integrations, admin tools) and ask which ones this version must not build.

Omit topic 7 when `ui` is false. Do not use the words "approve" or "confirm" in a discovery message: approval is one separate question at the end.

Round 1 also carries what triage left for the product gate: the catalog promises to keep, drop or tune. When `ui` is `true`, a change that adds a screen gets the one representative mockup (step 4) without asking; otherwise ask once, as factory-product step 3 does. When capturing needs the one-time Playwright download (`mockup_capture` in `<kit>/ui/tools.yaml`), round 1 says so, and the reply to round 1 is the agreement.

**Round 2, only when needed, one message.** Ask only about: a rule whose concrete example you still cannot write, two answers that contradict each other, and a new rule an answer revealed. After round 2, every topic still open becomes an entry under `## Assumptions` in `01-product.md` with the alternative you rejected. Assumptions are listed in the approval summary, so the user can correct them there.

Done when every topic is answered, settled by the repository, or an Assumption.

## 4. Draft the set

In this order, draft only pending documents from their existing templates; retain resolved sections and approved documents exactly. Design/mockup work runs only when still missing or genuinely affected by a pending product decision. A newly added template field is not permission to backfill an approved document:

- `01-product.md`: the template of [../factory-product/SKILL.md](../factory-product/SKILL.md) step 3, with its Glossary from topic 5 and its Assumptions. Every rule gets at least one requirement and one concrete example, as that step's Example Mapping says.
- The design file, when `ui` is `true`. Missing: [../factory-ui-ux/design-md-guide.md](../factory-ui-ux/design-md-guide.md) steps 1 to 6 and 8, its step 5 rendering only the one representative screen at two widths, drafted to `<change>/design-draft.md`, with the discovery answers in place of its step 7 interview. Voice and Words come from topics 5 and 6, marked `confirmed`. Existing: propose only new Words, Voice lines and states.
- The mockup, when step 3 decided one: the Mockups section of [../factory-ui-ux/SKILL.md](../factory-ui-ux/SKILL.md) on track standard, built from the design draft. Its capture is also the design file's representative preview: one capture, not two.
- `02-architecture.md`: the template of [../factory-architecture/SKILL.md](../factory-architecture/SKILL.md) step 3 and its rules, Threats included, after that skill's step 2 items 5 and 6 (earlier ADRs and explicitly selected applicable lenses only). The Layout Decision names its rows and reasons without the two exemplars. The domain-model decision takes one line.
- `03-interface.md`: the template of [../factory-interface/SKILL.md](../factory-interface/SKILL.md) step 2 and its rules, with signatures only for modules another module or a later slice calls, no Cost lines and no Decisions. Test plan and Coverage stay complete: an unmapped ID blocks approval.
- `04-slices.md`: the template and Rules of [../factory-slices/SKILL.md](../factory-slices/SKILL.md) step 3, every slice `Milestone: 1` with its `Depends on` line, cut so independent slices build in parallel as those Rules say, without the Development section.

Before the approval summary, run the [draft conformance pass](../factory-shared/adr.md): one scripted inventory of every accepted standing ADR and SYS row, then the planning conductor’s bounded read of all pending Decisions and Frozen contracts against it. This adds no model call on the standard track; the existing post-build general review remains independent. The standard-track read deliberately reuses the planning context rather than adding the proposed fresh conformance agent. Keep at most three evidence-backed conflict cards. A contradiction without an explicit `Supersedes: NNNN` becomes an Open question in its pending gate document, quoting the standing Decision and the draft line, with answers `supersedes NNNN` or `withdraw`. Fold only the actual user answer into the pending draft so its approval hash covers it; never mutate approved documents or standing ADRs. The summary includes these conflicts beside Assumptions. Refresh the pass after a relevant draft change, reusing unchanged evidence; do not reopen compatible architecture/security approvals. Track small remains `/factory-slices`: its conformance check is scripted only, matching slices’ Covers against SYS rows, with no architecture document or semantic agent call.

## 5. Line budgets

Check each document as gates.md's Approve a gate says. More than eight slices: offer the split the same way.

## 6. Ask for approval

One message: the rules as one line each with their example, the Glossary, the Voice lines, the design file's principles, positions and quality bar, the mockup paths, each Decision with the alternative it rejects, the Threats, the slice list, the Assumptions and draft-conformance conflicts (including their recorded answers), and this sentence: "Approving this plan authorizes building all slices inside their Allowed files, executable-test corrections under unchanged promises, and bounded implementation, review and acceptance repairs until the required checks pass or a real blocker remains, before your final sign-off. Changed promises, waivers, unrelated scope, destructive actions, credentials and publication remain separate decisions." Then ask: "Approve this plan, or correct it?" On resume, summarize only the pending decisions and their concrete diff; do not request approval of unchanged earlier decisions.

A reply that approves counts as approval, even when it also carries answers already folded into the documents. A reply with a new correction is folded in, and the question is asked again. Only a reply that approves records approval (gates.md, Approve a gate).

## 7. Approve

1. Approve only the pending gates, as gates.md's Approve a gate says for `/factory-plan`; preserve every unchanged existing approval.
2. Update `slices` in `status.yaml` as [../factory-slices/SKILL.md](../factory-slices/SKILL.md) step 5 does: `sent_back: null`, and a new slice appended as `{ id, name, milestone: 1, state: pending, base_commit: null, test_commit: null, head_commit: null }`. Without these rows the factory hook blocks every source edit. After a send-back, every slice not `done` that has commits goes to `building` with its commits kept, and build's Fast lane reworks the slices whose Covers, Allowed files or frozen signatures changed and reverifies the rest.
3. When `ui` is `true` and the design file was missing, write it from the draft with its stamp, as design-md-guide.md step 9 says.
4. `notes_for_fresh_session`: "Plan approved. Next: /factory-build <slug>." Committed mode: `git add .software-factory/changes/<slug> .software-factory/system`, plus the design file, and commit once, `chore(factory): plan <slug>`.

Continue directly to `/factory-build <slug>` in this session.
