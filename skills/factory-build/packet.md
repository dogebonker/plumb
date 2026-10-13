# Packet: slice <NN>, <name>

Written from: 04-slices.md <doc_sha256>, 03-interface.md <doc_sha256, or skipped>

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

## Tests first
Each fails in the red commit, before any implementation exists.
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
- `~/.agents/skills/<lens>/<lens>.nano.md`
- Principles: <copied from the principle layers, merged (gates.md, Paths)>
- Simplification ladder: <copied from packs.md>
- Language pack: `~/.agents/skills/<index pack>/SKILL.md`, plus `~/.agents/skills/<rules pack>/SKILL.md` for each rules pack. Read only the one or two rules this slice needs, apply them to the code this slice writes, leave what the linter enforces to the linter, and skip rules that need a newer <language> than <language_version>.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
