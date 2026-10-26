"""Build the FW-01 start state in an empty target directory: python3 setup.py <target>."""

import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import approve, commit, event, new_repo, pending_gate, triage  # noqa: E402

SLUG = "fw01"
TASK = "Deleted notes become tombstones that can be resurrected during a 14-day grace period, then are reaped"
PRODUCT = f"""# Product: {SLUG}

## Problem
A user who deletes a note by mistake loses it for good.

## Success metric
Users bring back notes they deleted by mistake, without asking for help.

## Announcement
A deleted note now waits 14 days as a tombstone. Resurrect it any time during that grace period.

## Mockups
none

## Rules and examples
### A deleted note becomes a tombstone
- FR-01: WHEN a user deletes a note, the system SHALL keep it as a tombstone, hidden from the note list, for a 14-day grace period
- Example: milk deleted on 2026-10-01 -> the list no longer shows milk; milk stays a tombstone until 2026-10-15

### A tombstone can be resurrected during its grace period
- FR-02: WHEN a user resurrects a tombstone within its grace period, the system SHALL put the note back in the list
- Example: milk resurrected on 2026-10-10 -> the list shows milk again

### Tombstones are reaped after the grace period
- FR-03: WHEN a tombstone's grace period ends, the system SHALL reap it, and it can no longer be resurrected
- Example: on 2026-10-16, resurrecting milk fails: milk was reaped

## Promises
none

## Constraints
none

## Standing constraints
none

## Non-goals
Keeping tombstones across restarts.

## Open questions
"""


def main(target):
    repo = new_repo(target, CASE)
    base = commit(repo, "feat: notebook", ".")
    s = {"slug": SLUG, "task": TASK, "track": "standard", "base": base, "sent_back": None, "slices": [],
         "gates": {gate: pending_gate() for gate in ("product", "architecture", "interface", "slices")},
         "history": [event(0, "plumb-triage", "step_start")], "notes": f"Triage done. Next: /plumb-product {SLUG}."}
    triage(repo, s, "domain-core")
    s["notes"] = f"product approved. Next: /plumb-architecture {SLUG}."
    approve(repo, s, "product", "01-product.md", PRODUCT, 2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: setup.py <target>")
    main(sys.argv[1])
