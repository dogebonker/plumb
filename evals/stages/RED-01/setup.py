"""Build the RED-01 start state in an empty target directory: python3 setup.py <target>."""

import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import LADDER, TEST_COMMAND, approve, change_dir, commit, event, new_repo, pending_gate, save, \
    triage, write  # noqa: E402

SLUG = "red01"
TASK = "Archive notes older than 30 days"
EXAMPLE = ("now 2026-10-12 12:00; a note created 2026-09-01 12:00 -> archived_at 2026-10-12 12:00; "
           "a note created 2026-09-12 12:00, exactly 30 days earlier -> not archived")
RULE = ("WHEN notes are archived at a time now, the system SHALL set archived_at to now on each note "
        "created more than 30 days before now")
SIGNATURE = "def archive_stale(notes: list[Note], now: datetime) -> list[Note]:"
COMMENT = ("Sets archived_at to now on every note created more than 30 days before now, and returns those notes "
           "in input order. A note created exactly 30 days before now is not archived.")
TESTS = [("test_archives_note_older_than_30_days",
          "a note created 2026-09-01 12:00 gets archived_at 2026-10-12 12:00 when archived at 2026-10-12 12:00"),
         ("test_keeps_note_exactly_30_days_old", "a note created 2026-09-12 12:00 keeps archived_at None")]
FACT = "`Note` is a dataclass with `title`, `created` and `archived_at: datetime | None = None` (notes.py:7-11)"

PRODUCT = f"""# Product: {SLUG}

## Problem
Old notes clutter the list. Notes nobody touched for a month should move out of the way.

## Success metric
After an archive run, no note older than 30 days is active.

## Announcement
Notes older than 30 days are now archived.

## Mockups
none

## Rules and examples
### A note older than 30 days is archived
- FR-01: {RULE}
- Example: {EXAMPLE}

## Promises
none

## Constraints
none

## Standing constraints
none

## Non-goals
Restoring archived notes.

## Open questions
"""
ARCHITECTURE = f"""# Architecture: {SLUG}

## Research
- {FACT}. research.md, answer 1.

## Fit
One function next to `Note` in notes.py. No storage.

## Layout
### .
Pattern: existing, root: ., check: none
- `notes.py`: the Note type and the functions on notes
- `test_*.py`: unittest tests

## Contracts and data
None changed: `archived_at` already exists.

## Flow
The caller passes its notes and the current time. `archive_stale` sets `archived_at` on the stale notes and returns them.

## Budgets
none

## Constraints
none

## Decisions
### Transaction scripts
Supersedes: none
Context: notes.py holds a plain dataclass and no services (research.md, answer 1).
Decision: a module-level function in notes.py.
Consequences: easy to call and test; the rule lives outside the Note type.

## Open questions
"""
INTERFACE = f"""# Interface: {SLUG}

## .
Depth: hides the 30-day rule and the date arithmetic behind one call
Cost: 1 public methods, 2 parameters, 0 error variants exposed, 0 configuration options exposed, 0 pass-through methods

```python
{SIGNATURE}
```
{COMMENT}

## Test plan
### . (bdd: off)
- FR-01: `test_archive.py` :: {TESTS[0][0]}, {TESTS[1][0]}

## Decisions

## Coverage
| ID | Enforced by |
| --- | --- |
| FR-01 | test: test_archive.py :: {TESTS[0][0]}, {TESTS[1][0]} |

## Open questions
"""
TESTS_FIRST = "\n".join(f"Tests first: test_archive.py :: {name} - {what}" for name, what in TESTS)
SLICES = f"""# Slices: {SLUG}

## Slices
### 01 archive stale notes
Milestone: 1
Covers: FR-01
Modules: .
{TESTS_FIRST}
Allowed files: notes.py, test_archive.py
Verify: {TEST_COMMAND}

## Open questions
"""
PACKET_TESTS = "\n".join(f"- `test_archive.py` :: {name}: {what}" for name, what in TESTS)
PACKET = f"""# Packet: slice 01, archive stale notes

## Goal
01 archive stale notes

## Covers
| ID | Fit criterion |
| --- | --- |
| FR-01 | {EXAMPLE} |

## Frozen contract
```python
{SIGNATURE}
```
{COMMENT}

Depth: hides the 30-day rule and the date arithmetic behind one call

Stub form: classes, protocols, dataclasses and type aliases exactly as written, with full type hints. Functions and methods: the frozen signature with the body `raise NotImplementedError`. Imports: whatever the signatures need.

## Context
- {FACT}

## Allowed files
One path per bullet.
- notes.py
- test_archive.py

## Layout
Where each Allowed file belongs and what may not go there, copied.
- `notes.py`: the Note type and the functions on notes
- `test_*.py`: unittest tests

## Tests first
Each fails in the red commit, before any implementation exists.
{PACKET_TESTS}

## Verify
- `{TEST_COMMAND}`

## Rules in scope
Read these before writing code, and apply them inside the frozen contract.
- `~/.agents/skills/clean-code/clean-code.nano.md`
- {LADDER}
- Language pack: `~/.agents/skills/modern-python/SKILL.md`. Read only the one or two rules this slice needs, apply them to the code this slice writes, leave what the linter enforces to the linter, and skip rules that need a newer Python than 3.10.

## Stop and report
- a frozen signature cannot work as written
- a file outside Allowed files must change
- a red-commit test is wrong
"""
RESEARCH = f"""# Research: {SLUG}

## Questions
1. What fields does `Note` in notes.py hold, and of which types?

## Answers
1. {FACT}.
"""


def main(target):
    repo = new_repo(target, CASE)
    base = commit(repo, "feat: notes", ".")
    s = {"slug": SLUG, "task": TASK, "track": "standard", "base": base, "sent_back": None, "slices": [],
         "gates": {gate: pending_gate() for gate in ("product", "architecture", "interface", "slices")},
         "history": [event(0, "factory-triage", "step_start")], "notes": f"Triage done. Next: /factory-product {SLUG}."}
    triage(repo, s, "crud-service")
    s["notes"] = f"product approved. Next: /factory-architecture {SLUG}."
    approve(repo, s, "product", "01-product.md", PRODUCT, 2)
    write(change_dir(repo, SLUG) / "research.md", RESEARCH)
    s["notes"] = f"architecture approved. Next: /factory-interface {SLUG}."
    approve(repo, s, "architecture", "02-architecture.md", ARCHITECTURE, 4)
    s["notes"] = f"interface approved. Next: /factory-slices {SLUG}."
    approve(repo, s, "interface", "03-interface.md", INTERFACE, 6)
    s["slices"] = [{"id": "01", "name": "archive stale notes", "milestone": 1, "state": "pending",
                    "base_commit": None, "test_commit": None, "head_commit": None}]
    s["notes"] = f"slices approved. Next: /factory-build {SLUG}."
    approve(repo, s, "slices", "04-slices.md", SLICES, 8)
    # Build step 2 wrote the packet; the executor is not dispatched yet, so the slice is still pending.
    s["history"].append(event(10, "factory-build", "step_start", "01"))
    save(repo, s)
    write(change_dir(repo, SLUG) / "slices/01/packet.md", PACKET)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: setup.py <target>")
    main(sys.argv[1])
