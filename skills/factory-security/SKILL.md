---
name: factory-security
description: Security audit of a repository - threat model from the code and .factory/system, pinned scanners, the security-audit method with routed knowledge, proven findings proposed as small factory changes.
disable-model-invocation: true
argument-hint: "[audit | threat-model | lens <slug>] [path to scope]"
---

# Factory security

Mode and scope: $ARGUMENTS (empty: `audit` of the whole repository)

Defensive review of this repository, never of systems it does not own. Why each source and tool is here: `docs/research/security-selection.md` in the factory repository. The kit's `security/index.yaml` and `security/tools.yaml` (under `~/.software-factory/`) hold the routing and the scanner commands.

| Mode | When | Runs |
| --- | --- | --- |
| `audit` | on demand | steps 1 to 6 |
| `threat-model` | track critical, after the architecture gate | steps 1 and 2 |
| `lens <slug>` | factory-review, for a slice whose diff touches a trust boundary in the threat model | step 5 on the slice diff only |

## 1. Prepare

- Load the `security-audit` skill (Cloudflare) in guidance mode; it is the method. The full six-phase workflow runs only when the user asked for a full or deep audit.
- Make the run folder `.factory/security/<YYYY-MM-DD-HHMM>/` and make sure `.factory/security/` is excluded from git (add it to `.git/info/exclude` if not).
- Check each tool in `tools.yaml` against its pinned version. A missing or older tool is skipped, with its install line in the report.

## 2. Threat model

Write or update `.factory/system/threat-model.md` from [threat-model.md](threat-model.md), reading `.factory/system/` (product, ADRs, constraints, lenses.yaml) and the code itself: entry points, data stores, outbound calls, secrets, deployment files, CI. Every entry point and every trust boundary gets at least one threat or an explicit "none, because". The Components line uses the tags in `index.yaml`; routing reads it.

Show the model to the user and fold in their corrections before anything else runs. Done when the user confirms it.

## 3. Route

Pick from `index.yaml`: the method file for each component, and the knowledge entries whose `when` tags match the threat model. Each pack passes the pin check in [../factory-shared/packs.md](../factory-shared/packs.md) or is skipped. Write `routing.md` in the run folder: every entry loaded and why, every entry skipped and why.

Rules for loaded knowledge: load only the part `read` names; ignore what `skip` lists and add what `add` lists; never run anything under a pack's `scripts/`; verdicts, severity and the evidence bar come only from `security-audit`.

## 4. Scan

Run each applicable tool exactly as `tools.yaml` says: from an empty working directory, with telemetry off, output into the run folder. Then list the repository's own suppressions (ignore files and inline markers) as data. Every scanner result is a candidate.

## 5. Hunt and verify

Follow `security-audit`'s hunting and verification in the chosen profile (quick unless asked otherwise), one agent per component. Each agent loads the method file for its component plus at most one routed knowledge entry. Scanner candidates and the threat model's abuse paths are its starting points; it hunts for more along the trust boundaries.

Each candidate ends `confirmed`, `needs_validation` (with the exact blocker and the plan that would settle it) or `rejected`, under `security-audit`'s evidence bar. Exploitability that needs a running system is proven only inside an isolated sandbox; without one the candidate stays `needs_validation`. Validate the findings file with `security-audit`'s validators.

## 6. Rank and propose

Rank confirmed findings: known exploited (CISA KEV) first, then EPSS, then reachability (govulncheck, call path in the trace), then severity. Report infrastructure findings as the misconfiguration, then what it reaches, then the blast radius.

Show the ranked list to the user. For each finding they approve:

- propose it as its own small change (`/factory-triage fix: <finding>`), whose first slice adds a regression test that fails before the fix
- a rule that should hold from now on becomes a draft `SYS-C` row for `.factory/system/constraints.md`, and, when the `variant-analysis` pack is pinned, a scanner rule for the pattern

Write `report.md` in the run folder: findings by rank, `needs_validation` items with their plans, what was routed and skipped, which tools ran or were skipped, and the suppressions found. Done when every candidate has a verdict and every confirmed finding has the user's answer.
