---
name: factory-security
description: Security audit of a repository - threat model from the code and .software-factory/system, pinned scanners, the security-audit method with routed knowledge, proven findings proposed as small factory changes.
disable-model-invocation: true
argument-hint: "[audit [quick|standard|deep] | threat-model | lens <slug>] [path to scope]"
---

# Factory security

Usage: [per-skill accounting](../factory-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Mode and scope: $ARGUMENTS (empty: `audit quick` of the whole repository)

`<kit>` and `<project>`: [../factory-shared/gates.md](../factory-shared/gates.md), Paths; stop as it says.

Defensive review of this repository, never of systems it does not own. Why each source and tool is here: `docs/research/security-selection.md` in the factory repository. Routing and scanner commands: `<kit>/security/index.yaml` and `tools.yaml`.

| Mode | When | Runs |
| --- | --- | --- |
| `audit` | on demand | steps 1 to 6, `security-audit` in full audit mode with the chosen profile (default `quick`) |
| `threat-model` | track critical, after the architecture gate | step 2 only |
| `lens <slug>` | factory-review, on a slice whose diff touches a trust boundary or entry point of the threat model (track standard without `threat-model.md`: of the `## Threats` section of `02-architecture.md`; an absent threat model never skips the lens) | steps 3 and 5 for that diff: one agent, `security-audit` in guidance mode, no run folder |

Never copy a secret value into any file, report or message: cite file:line, rule and fingerprint.

## 1. Prepare (audit)

- Read `security-audit` (Cloudflare) from its cache folder after the pin check in [../factory-shared/packs.md](../factory-shared/packs.md), in full audit mode with the profile. Invoking `/factory-security audit` is the user's choice of `.software-factory/runs/security/<YYYY-MM-DD-HHMM>/` as its output folder.
- That folder must be ignored by git: `git check-ignore -q .software-factory/runs/security/x` must succeed; otherwise append `.software-factory/runs/security/` to the file `git rev-parse --git-path info/exclude` names.
- Check each tool in `tools.yaml` against its pinned version. A missing or older tool is skipped, with its install line in the report.

## 2. Threat model

**Resume first.** For the current change, compare the model's bytes with its latest genuine `threat_model_approved` event and the approved product/architecture security decisions. A matching model whose assets, trust boundaries, access rules, assumptions and accepted risks remain applicable is complete: leave its bytes and approval event unchanged, skip drafting and approval, and continue to the next unfinished stage. Resuming, a new code commit, additional citations or an implementation finding within the agreed security decisions do not require security reapproval. Record fresh findings and mitigation evidence in a change-local `security-notes.md` or review instead. A hash mismatch first uses gates.md's exact-byte recovery rule for your own proven incidental edits; preserve user changes and uncertain provenance. A file's existence alone is not approval; missing/unproven approval retains the initial approval step. Headless authority is unchanged.

If a material security decision must change, preserve the approved model and write the proposed diff separately. Ask only about changed assets, boundaries, access rules, assumptions or accepted risks; show why the existing decision cannot hold. Do not redraft the entire model or architecture to add observations. An in-scope fix preserving those decisions proceeds through build/review without a new approval.

Apply gates.md **Change impact** and **Explain questions and decisions**. An interface/product amendment alone does not invalidate the model. For a real security choice, describe who can now see or do what, one concrete abuse/failure example, the recommended protection and its usability/cost trade-off; use a small actor → boundary → data diagram when useful. Extra explanation or a newly cited mitigation is not another approval question.

Only for an initial model or material decision revision, draft separately from the approved `.software-factory/system/threat-model.md` using [threat-model.md](threat-model.md), reading `.software-factory/system/` (product, ADRs, constraints, lenses.yaml) and the code itself: entry points, data stores, outbound calls, secrets, deployment files, CI. Every entry point and every trust boundary gets at least one threat or an explicit "none, because". The Components line uses the tags of `index.yaml`; routing reads it.

Show the initial draft or material decision diff to the user and ask: "Approve this threat model, or correct it?" Only after actual approval, finalize the approved bytes with their corrections and, when run for a change, append a `threat_model_approved` event to its `history` with those bytes' SHA-256 ([../factory-shared/gates.md](../factory-shared/gates.md), History), then write exactly those bytes to the model. The editing hook permits that full Write against the recorded digest. Verify the on-disk hash before continuing. Ask once per changed decision set: answering an explanatory question does not change the draft or require approval again; a new material requirement does. Done when the file is written and approved; continue automatically in interactive mode unless manually paused.

## 3. Route

Pick from `index.yaml`, for each component of the threat model (lens mode: only the components the diff touches; on track standard without `threat-model.md`, the components of the `Components:` line in the `## Threats` section of `02-architecture.md`):

- the method: `security-audit`'s parent instructions for the orchestrator; for each hunter, its hunting method and the one attack-class block and component file `index.yaml` names
- knowledge: the matching `own` checklist, plus the first pack entry in index order whose `when` tags match and whose pack passes the pin check in [../factory-shared/packs.md](../factory-shared/packs.md)
- verifiers also load the `role: verifier` entries; `role: after-confirmed` entries run in step 6

Load only the part `read` names, from the pack's cache folder (packs.md, Load), ignore what `skip` lists, apply what `add` lists, never run anything under a pack's `scripts/`. Verdicts, severity and the evidence bar come only from `security-audit`. Write `routing.md` in the run folder (lens mode: a routing line in the reply): every entry loaded and why, every entry skipped and why.

## 4. Scan (audit)

Run each applicable tool exactly as `tools.yaml` says, including its `before` checks, from a fresh empty working directory, output into the run folder. List what the repository can still do to its own scan (`tools.yaml` header): inline suppressions, `.gitleaksignore` entries (each one a candidate), the Opengrep ignore patterns in effect.

## 5. Hunt and verify

Follow `security-audit`'s hunting and verification for the profile, one hunter per component, each with its method block plus its routed knowledge. Scanner candidates and the threat model's abuse paths are the starting points; hunters search along the trust boundaries for more.

Each candidate ends `confirmed`, `needs_validation` (with the exact blocker and the plan that would settle it) or `rejected`, under `security-audit`'s evidence bar. Exploitability that needs a running system is proven only inside an isolated sandbox; without one the candidate stays `needs_validation`.

Audit mode: write `findings.json` and the coverage ledger in the run folder as `security-audit` specifies, and run its validators on them (`node <pack>/validate-findings.cjs <run>/findings.json`, where `<pack>` is `security-audit`'s cache folder ([../factory-shared/packs.md](../factory-shared/packs.md)), and `validate-coverage-ledger.cjs` on the ledger). Lens mode: return confirmed findings as cards anchored to a threat ID of the threat model, or on track standard without `threat-model.md`, of the `## Threats` section of `02-architecture.md`.

## 6. Rank and propose (audit)

Rank confirmed findings: known exploited first (the CISA KEV list), then EPSS, then reachability (govulncheck, or the call path in the trace), then severity; `tools.yaml` says where the KEV and EPSS data come from. Report infrastructure findings as the misconfiguration, then what it reaches, then the blast radius.

Show the ranked list to the user. For each finding they approve, propose its own small change: `/factory-triage fix: <finding>`, whose first slice adds a regression test that fails before the fix. A rule that should hold from then on goes into that task text as a constraint, so reconcile writes its `SYS-C` row; with a pinned `variant-analysis` pack, also propose a scanner rule for the pattern.

Write `report.md` in the run folder: findings by rank, `needs_validation` items with their plans, what was routed and skipped, which tools ran or were skipped, and what the repository could still suppress. Done when every candidate has a verdict and every confirmed finding has the user's answer.
