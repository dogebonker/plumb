# Packet: slice <NN>, <name>

Fast lane: Goal, Covers, Allowed files, Tests first and Verify only (factory-build, Fast lane).

Written from: <each current approved gate document and doc_sha256; skipped gates explicitly marked>
Inputs: <immutable input path/SHA-256 and mutable metadata effective field/value projections for criteria/SYS promises, budgets, signatures, layout/design/rules, pins, adapters and verification commands; exclude progress/history/receipts; gates.md, Development proof inputs>

Correction provenance (derived corrections only): <validated slices/NN/repair.json and immutable input snapshot; original completed parents; fixed start_commit; exact paths; reproduced failure evidence. Goal comes from unchanged criterion/defect, not a nonexistent 04-slices heading. Own base/test/head receipts never replace parent records.>

Owned spans: <original slice commit span; retained-work repairs also record original head, repair-start HEAD and exact correction spans, never later slices as this slice's edits>

## Goal
<one sentence>

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-01 | <the FR's Example line> |
| SYS-NFR-01 | <fit criterion from the registry> |

## Frozen contract
<signatures, interface comments and depth statements, copied from `03-interface.md`. They do not change.>

Stub form: <the Stubs section of the language's adapter>

## Context
<Research facts this slice needs, each with path:line>

## Allowed files
One path per bullet.
- <path>

## Layout
Where each Allowed file belongs and what may not go there, copied.
- `<folder>/`: <what lives there, and what may not>

## Visual direction (UI slices only)
<DESIGN.md path and relevant brand/component/state rules; approved branded mockup paths when present; the affected feature's optional visual-references.md/artifacts and concise borrow/adapt/leave-out notes. With none, use the approved brief and design system. External examples never override brand, behavior or accessibility.>

## Tests first
Map existing coverage first. New tests fail before implementation except evidence-backed `red_exempt` cases, independently reviewed. Executable corrections retain their expectation and original history, with a deviation and isolated supplementary RED/GREEN proof.
- `<test file>` :: <test name>: <what it asserts>

## Scenarios (bdd: native modules only)
<the slice's scenarios, verbatim>

Existing step definitions, to reuse before writing new ones:
- `<path:line>` <step text>

## Verify
Commands run from the repository root and must also work in an isolated checkout; do not hardcode the live checkout path. RED proof uses `<kit>/runtime.py red` and retains its checkpoint/log under the slice. For fixed browser capabilities copy `red_test_command` from status verbatim, write `.software-factory/browser-red.json` via `runtime.py browser-red-request` (full recorded test commit SHA and safe checkpoint token), and run it directly once for all tests; the live browser wrapper cannot prove RED.
- `<command>`

## Rules in scope
Read these before writing code, and apply them inside the frozen contract.
- `<resolved pack>/<lens>.nano.md` (matching bundled book or exact cache; packs.md)
- Principles: <copied from the principle layers, merged (gates.md, Paths)>
- Simplification ladder: <copied from packs.md>
- Language pack: `~/.software-factory/packs/<index pack>@<hash>/SKILL.md`, plus `~/.software-factory/packs/<rules pack>@<hash>/SKILL.md` for each rules pack. Read only the one or two rules this slice needs, apply them to the code this slice writes, leave what the linter enforces to the linter, and skip rules that need a newer <language> than <language_version>.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- an approved promise is ambiguous or a frozen contract must change

A derived correction uses only its validated exact paths, including original planned tests. No new regression-file or typecheck deviation widens it; report for the genuine scope gate. Validate edit scope before every edit/resume/dispatch; complete validation is structural proof only, never independent approval or quality.

Correct an executable test mistake under an unchanged promise locally with recorded deviation and isolated proof. Resume repairable failures without repeated approval; preserve unrelated dirty work.
