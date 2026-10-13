"""Build the ACC-01 start state in an empty target directory: python3 setup.py <target>."""

import json
import socket
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import NAME, TEST_COMMAND, approve, build_slice, change_dir, commit, event, git, new_repo, pending_gate, \
    save, triage, write  # noqa: E402

SLUG = "acc01"
TASK = "Serve notes over HTTP: create, archive and list them"
RULES = [
    ("A user creates a note", "FR-01", "WHEN a user posts a note with a title, the system SHALL store it and return it "
     "with its id, not archived", 'POST /notes {"title": "milk"} on an empty server -> 201 '
     '{"id": 1, "title": "milk", "archived": false}'),
    ("A user lists archived notes", "FR-02", "WHEN a user lists notes with archived=true, the system SHALL return "
     "only the archived notes", "notes milk (archived) and eggs (not archived) -> GET /notes?archived=true returns "
     "milk only"),
    ("A user archives a note", "FR-03", "WHEN a user archives a note, the system SHALL mark it archived and return it",
     'note 1 milk -> POST /notes/1/archive returns 200 {"id": 1, "title": "milk", "archived": true}'),
]
SIGNATURE = "def make_server(store: Store, port: int) -> ThreadingHTTPServer:"
COMMENT = ("Serves the store on 127.0.0.1:port: POST /notes with a JSON title creates a note (201, 400 without a "
           "title), POST /notes/<id>/archive archives it (200, 404 when unknown), GET /notes lists notes, and "
           "GET /notes?archived=true|false lists only those with that archived flag.")
TESTS = [("test_post_creates_note", "FR-01"), ("test_list_archived_returns_notes", "FR-02"),
         ("test_archive_marks_note", "FR-03")]
STUB = f'''"""HTTP API for notes."""

from http.server import ThreadingHTTPServer

from store import Store


{SIGNATURE}
    raise NotImplementedError
'''
FACT = ("`Store.list(archived=None)` returns every note, or only those whose archived flag equals `archived` "
        "(store.py:21-23); `Store.archive` returns None for an unknown id (store.py:13-19)")


def product():
    rules = "\n".join(f"### {title}\n- {fr}: {rule}\n- Example: {example}\n" for title, fr, rule, example in RULES)
    return f"""# Product: {SLUG}

## Problem
Notes live only inside the process. Users want to create, archive and list them over HTTP.

## Success metric
A user can keep a list of notes and see only the archived ones, with no other tool.

## Announcement
Notes now have an HTTP API: create, archive, and list all or only archived notes.

## Mockups
none

## Rules and examples
{rules}
## Promises
none

## Constraints
none

## Standing constraints
none

## Non-goals
Persistence across restarts.

## Open questions
"""


ARCHITECTURE = f"""# Architecture: {SLUG}

## Research
- {FACT}. research.md, answer 1.

## Fit
A new app.py serves the existing Store with the standard library's http.server.

## Layout
### .
Pattern: existing, root: ., check: none
- `app.py`: the HTTP entry point
- `store.py`: the in-memory store
- `test_*.py`: unittest tests

## Contracts and data
JSON over HTTP. A note is `{{"id": int, "title": str, "archived": bool}}`.

## Flow
A request reaches the handler in app.py, which calls Store and replies with JSON.

## Budgets
none

## Constraints
none

## Decisions
### Standard library HTTP server
Supersedes: none
Context: the project has no dependencies (research.md, answer 1).
Decision: http.server's ThreadingHTTPServer.
Consequences: no install; routing is written by hand.

## Open questions
"""
INTERFACE = f"""# Interface: {SLUG}

## .
Depth: hides routing, JSON encoding and status codes behind one constructor
Cost: 1 public methods, 2 parameters, 0 error variants exposed, 0 configuration options exposed, 0 pass-through methods

```python
{SIGNATURE}
```
{COMMENT}

## Test plan
### . (bdd: off)
""" + "".join(f"- {fr}: `test_app.py` :: {name}\n" for name, fr in TESTS) + """
## Decisions

## Coverage
| ID | Enforced by |
| --- | --- |
""" + "".join(f"| {fr} | test: test_app.py :: {name} |\n" for name, fr in TESTS) + """
## Open questions
"""
CHALLENGES = f"""# Challenges: {SLUG}

## Round 1
### APoSD

| Field | Value |
| --- | --- |
| Lens / rule | a-philosophy-of-software-design / deep modules |
| Where | `{SIGNATURE}` |
| Steelman | One constructor hides every route. |
| Objection | none: the module is deep. |
| Anchored to | none |
| Alternative | `{SIGNATURE}` |
| Cost of alternative | none |
| Severity | note |
| Response | accept: keep it. |
"""
SLICES = f"""# Slices: {SLUG}

## Slices
### 01 notes over HTTP
Milestone: 1
Covers: FR-01, FR-02, FR-03
Modules: .
""" + "".join(f"Tests first: test_app.py :: {name} - {fr}'s example\n" for name, fr in TESTS) + f"""Allowed files: app.py, test_app.py
Verify: {TEST_COMMAND}

## Open questions
"""


def main(target):
    repo = new_repo(target, CASE)
    base = commit(repo, "feat: notes store", ".", ":!app.py", ":!test_app.py")
    s = {"slug": SLUG, "task": TASK, "track": "standard", "base": base, "sent_back": None, "slices": [],
         "gates": {gate: pending_gate() for gate in ("product", "architecture", "interface", "slices")},
         "history": [event(0, "factory-triage", "step_start")], "notes": f"Triage done. Next: /factory-product {SLUG}."}
    with socket.socket() as probe:  # a free port, so parallel trials do not collide
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    triage(repo, s, "crud-service", f"python3 app.py {port}", f"http://127.0.0.1:{port}")
    answers = (CASE / "answers.json").read_text().replace("{port}", str(port))
    write(repo / ".git/acc01-answers.json", json.dumps(json.loads(answers), indent=2) + "\n")
    s["notes"] = f"product approved. Next: /factory-architecture {SLUG}."
    approve(repo, s, "product", "01-product.md", product(), 2)
    write(change_dir(repo, SLUG) / "research.md", f"""# Research: {SLUG}

## Questions
1. How does store.py list and archive notes, and what does it depend on?

## Answers
1. {FACT}. It imports nothing.
""")
    s["notes"] = f"architecture approved. Next: /factory-interface {SLUG}."
    approve(repo, s, "architecture", "02-architecture.md", ARCHITECTURE, 4)
    write(change_dir(repo, SLUG) / "challenges.md", CHALLENGES)
    s["notes"] = f"interface approved. Next: /factory-slices {SLUG}."
    approve(repo, s, "interface", "03-interface.md", INTERFACE, 6)
    s["slices"] = [{"id": "01", "name": "notes over HTTP", "milestone": 1, "state": "pending",
                    "base_commit": None, "test_commit": None, "head_commit": None}]
    s["notes"] = f"slices approved. Next: /factory-build {SLUG}."
    approve(repo, s, "slices", "04-slices.md", SLICES, 8)
    start = git(repo, "rev-parse", "HEAD")
    test, head = build_slice(repo, SLUG, {"app.py": STUB}, ["test_app.py"])
    write(change_dir(repo, SLUG) / "slices/01/checks.md", f"""# Checks: slice 01, notes over HTTP

Range: {start}..{head}
- Allowed files: pass
- Frozen contract: pass
- Red tests unchanged: pass
- Red: {test} failed on the new tests. Green: {head} passes test_command.
- Lint: pass
""")
    s["slices"][0].update(state="green", base_commit=start, test_commit=test, head_commit=head)
    s["history"] += [event(10, "factory-build", "step_start", "01"), event(20, "factory-review", "step_start", "1")]
    s["notes"] = f"Milestone 1 green. Next: /factory-review {SLUG}."
    save(repo, s)
    commit(repo, "chore(factory): milestone 1 review", ".factory")
    # Signed off in chat: review.md and the done state stay uncommitted until reconcile commits them.
    s["slices"][0]["state"] = "done"
    s["notes"] = f"All slices done. Next: /factory-reconcile {SLUG}."
    save(repo, s)
    write(change_dir(repo, SLUG) / "slices/01/review.md", f"""# Review: milestone 1, slices 01 to 01

Range: {start}..{head}

## Phase 1
- Per slice: `slices/01/checks.md`, each pass
- Milestone checks 5 to 9: pass
- After review fixes: no fixes
- Red: each slice's test_commit failed on its new tests. Green: {head} passes test_command.

## Review agents
No findings.

## Lens reviewers
- APoSD: not run: the diff adds no public symbol outside the frozen contract

## Follow-ups
none

## Sign-off
{NAME}, 2026-10-01T11:00:00Z
""")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: setup.py <target>")
    main(sys.argv[1])
