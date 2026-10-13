"""Setup shared by REV-01 and REV-02: track small, slices approved, slice 01 green and waiting for its review."""

from stagelib import LADDER, TEST_COMMAND, approve, build_slice, change_dir, commit, event, git, new_repo, save, \
    triage, write

TASK = "Show how many pages the notes fill, the latest note with a tag, and the archived share"
REQUIREMENTS = """- FR-01: WHEN notes are shown a given number per page (at least 1), the system SHALL report how many pages they fill, a partly filled last page included
  Example: 7 notes, 3 per page -> 3 pages; 6 notes, 3 per page -> 2 pages; no notes -> 0 pages
- FR-02: WHEN a user asks for the latest note with a tag, the system SHALL return the most recently added note with that tag, or none
  Example: notes added in the order a (work), b (home), c (work) -> the latest work note is c; the latest travel note is none
- FR-03: WHEN a user asks how much of the notes is archived, the system SHALL return the archived fraction
  Example: 1 of 4 notes archived -> 0.25; no notes -> 0.0"""
TESTS = """test_listing.py :: test_page_count - FR-01's example
test_listing.py :: test_latest - FR-02's example
test_listing.py :: test_archived_share - FR-03's example"""
SIGNATURES = [
    ("def page_count(total: int, size: int) -> int:",
     "Pages needed to show total notes, size per page; size is at least 1, and a partly filled last page counts."),
    ("def latest(notes: list[dict], tag: str) -> dict | None:",
     "The most recently added note with tag, or None; notes are stored oldest first."),
    ("def archived_share(notes: list[dict]) -> float:",
     "The fraction of notes that are archived; 0.0 when there are no notes."),
]
INTERFACE = "\n\n".join(f"```python\n{signature}\n```\n{comment}" for signature, comment in SIGNATURES)
STUB = '''"""Count the pages notes fill, find the latest note with a tag, and the archived share."""
''' + "".join(f"\n\n{signature}\n    raise NotImplementedError\n" for signature, _ in SIGNATURES)


def slices_doc(slug):
    tests = "\n".join(f"Tests first: {line}" for line in TESTS.splitlines())
    return f"""# Slices: {slug}

## Goal
{TASK}.

## Requirements
{REQUIREMENTS}

## Standing constraints
none

## Interface
{INTERFACE}

## Slices
### 01 listing summary
Milestone: 1
Covers: FR-01, FR-02, FR-03
Modules: .
{tests}
Allowed files: listing.py, test_listing.py
Verify: {TEST_COMMAND}

## Open questions
"""


def packet(slug):
    covers = "\n".join(f"| {line[2:7]} | {example.strip()[len('Example: '):]} |"
                       for line, example in zip(REQUIREMENTS.splitlines()[::2], REQUIREMENTS.splitlines()[1::2]))
    tests = "\n".join(f"- `{line.split(' :: ')[0]}` :: {line.split(' :: ')[1].replace(' - ', ': ', 1)}"
                      for line in TESTS.splitlines())
    return f"""# Packet: slice 01, listing summary

## Goal
01 listing summary

## Covers
| ID | Fit criterion |
| --- | --- |
{covers}

## Frozen contract
{INTERFACE}

Stub form: functions and methods: the frozen signature with the body `raise NotImplementedError`.

## Context
None: track small has no architecture document.

## Allowed files
One path per bullet.
- listing.py
- test_listing.py

## Layout
Where each Allowed file belongs and what may not go there, copied.
- `./`: existing; the module's Python files and their tests

## Tests first
Each fails in the red commit, before any implementation exists.
{tests}

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


def setup(case_dir, target, slug):
    repo = new_repo(target, case_dir)
    base = commit(repo, "feat: notes", ".", ":!listing.py", ":!test_listing.py")
    s = {"slug": slug, "task": TASK, "track": "small", "base": base, "sent_back": None, "slices": [],
         "gates": {gate: {"state": "skipped"} for gate in ("product", "architecture", "interface")},
         "history": [event(0, "factory-triage", "step_start")],
         "notes": f"Triage done. Next: /factory-slices {slug}."}
    s["gates"]["slices"] = {"state": "pending", "approved_by": None, "approved_at": None, "doc_sha256": None}
    triage(repo, s, "crud-service")
    s["slices"] = [{"id": "01", "name": "listing summary", "milestone": 1, "state": "pending",
                    "base_commit": None, "test_commit": None, "head_commit": None}]
    s["notes"] = f"slices approved. Next: /factory-build {slug}."
    approve(repo, s, "slices", "04-slices.md", slices_doc(slug), 5)
    start = git(repo, "rev-parse", "HEAD")
    test, head = build_slice(repo, slug, {"listing.py": STUB}, ["test_listing.py"])
    # Interactive mode: build does not commit .software-factory/; the milestone review's first commit carries it.
    s["slices"][0].update(state="green", base_commit=start, test_commit=test, head_commit=head)
    s["history"] += [event(10, "factory-build", "step_start", "01"), event(20, "factory-build", "step_tokens", "01",
                                                                           "agents 3b7d0f12, usage 182340")]
    s["notes"] = f"Milestone 1 green. Next: /factory-review {slug}."
    save(repo, s)
    slice_dir = change_dir(repo, slug) / "slices/01"
    write(slice_dir / "packet.md", packet(slug))
    write(slice_dir / "checks.md", f"""# Checks: slice 01, listing summary

Range: {start}..{head}
- Allowed files: pass
- Frozen contract: pass
- Red tests unchanged: pass
- Red: {test} failed on the new tests. Green: {head} passes test_command.
- Lint: pass
""")
