"""Shared by the REV oracles: commit the planning state, apply source fixes, write review.md and sign off."""

import re

from stagelib import NAME, change_dir, commit, write


def review(workspace, slug, fixes, findings, planning_commit=True):
    """fixes maps a path to (old, new) replacements; findings is review.md's Review agents lines."""
    status = change_dir(workspace, slug) / "status.yaml"
    text = status.read_text()
    base = re.search(r"\bbase_commit: (\w+)", text).group(1)
    head = re.search(r"\bhead_commit: (\w+)", text).group(1)
    if planning_commit:
        commit(workspace, "chore(plumb): milestone 1 review", ".plumb")
    for path, pairs in fixes.items():
        source = (workspace / path).read_text()
        for old, new in pairs:
            assert old in source, (path, old)
            source = source.replace(old, new)
        write(workspace / path, source)
    if fixes:
        fixed = commit(workspace, f"fix({slug}): milestone 1 review", *fixes)
        text, head = text.replace(f"head_commit: {head}", f"head_commit: {fixed}"), fixed
    write(status, text.replace("state: green", "state: done").replace(
        "Milestone 1 green. Next: /plumb-review", "All slices done. Next: /plumb-reconcile"))
    write(change_dir(workspace, slug) / "slices/01/review.md", f"""# Review: milestone 1, slices 01 to 01

Range: {base}..{head}

## Phase 1
- Per slice: `slices/01/checks.md`, each pass
- Milestone checks 5 to 9: pass
- After review fixes: {"pass" if fixes else "no fixes"}
- Red: each slice's test_commit failed on its new tests. Green: {head} passes test_command.

## Review agents
{findings}

## Lens reviewers
not run: track small

## Follow-ups
none

## Sign-off
{NAME}, 2026-10-01T12:00:00Z
""")
