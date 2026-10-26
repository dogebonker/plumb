---
name: plumb-prune
description: Audit a repository for code to delete or simplify, protect what Plumb relies on, and run each approved item as a small behavior-preserving change.
disable-model-invocation: true
argument-hint: "[path to limit the audit]"
---

# Plumb prune

Usage: [per-skill accounting](../plumb-shared/gates.md#skill-token-accounting) applies to this invocation, including questions and interrupted work.

Scope: $ARGUMENTS (empty: the whole repository)

`<kit>` and `<project>`: [../plumb-shared/gates.md](../plumb-shared/gates.md), Paths; stop as it says.

Agents add code more readily than they remove it. Prune is the counterweight: you approve every item, and each one ships as its own small change. It runs on demand; to run it on a schedule, give `/plumb-prune` to your scheduler (for example `/schedule`).

Start on the default branch with no uncommitted changes outside `.plumb/`.

## 1. Audit

- For each module in `.plumb/system/lenses.yaml` (or each manifest, when there is none), the Dead code command from `<kit>/adapters/<language>.md`, over the scope.
- The `ponytail-audit` skill when it is installed; otherwise walk the scope yourself with the simplification ladder in [../plumb-shared/packs.md](../plumb-shared/packs.md).

Each item names its files and lines, what goes or what replaces it, and the lines it would remove.

## 2. Protect

Drop every item that touches:

- a signature in any `.plumb/changes/*/03-interface.md`
- code that a row of `.plumb/system/constraints.md` names under Enforced by
- a step-definition file (the adapter's BDD step search finds them): whether a scenario still uses a step cannot be decided by text search
- a public or exported symbol of a library module: other code may import it. In a module with a main entry point, a binary or a `dev_command` other than `none`, unused exports are candidates
- code behind a money signal, when `money` is `true` in `.plumb/system/lenses.yaml`, unless the item only deletes dead code

Done when every remaining item has been checked against all five, and each dropped item is listed with the reason.

## 3. Rank and approve

Rank the remaining items by lines removed against risk, where risk is the callers affected and whether tests cover the code. Show the list to the user; they approve items by number. Write the approved list to `.plumb/runs/prune/<YYYY-MM-DD>.md`; in committed mode, commit it on a new branch `plumb/prune-<YYYY-MM-DD>`.

## 4. Hand off

Each approved item runs as its own small change, in a fresh session: `/plumb-triage prune: <item>`. The item text says the change must preserve behavior and, when the code has no tests, that its first slice adds characterization tests that pass before anything is removed.
