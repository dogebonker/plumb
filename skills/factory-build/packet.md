# Packet: slice <NN>, <name>

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
- <path>

## Tests first
Each fails on its assertion in the red commit, before any implementation exists.
- `<test file>` :: <test name>: <what it asserts>

## Verify
- `<command>`

## Rules in scope
Read these before writing code, and apply them inside the frozen contract.
- `~/.agents/skills/<lens>/<lens>.nano.md`
- Language pack: `~/.agents/skills/<index pack>/SKILL.md`, plus `~/.agents/skills/<rules pack>/SKILL.md` for each rules pack. Read only the one or two rules this slice needs, apply them to the code this slice writes, leave what the linter enforces to the linter, and skip rules that need a newer <language> than <language_version>.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
