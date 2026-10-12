"""Grade a REV-01 workspace: python3 grade.py <workspace>. Prints one JSON line."""

import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import active_block_or_fix, change_dir, commit_by_subject, git_ok, passed, read_status, report, \
    review_md_ok, slice_field, tests_at, workspace_arg  # noqa: E402

DECOY = "    for index in range(len(notes) - 1, -1, -1):"
BUGS = re.compile(r"page_count|archived_share|listing\.py:(6|1[7-9]|20)\b|ZeroDivision|divi\w* by zero", re.I)

if __name__ == "__main__":
    workspace = workspace_arg()
    hidden = tests_at(workspace, "HEAD", {"test_hidden_listing.py": CASE / "grading/test_hidden_listing.py"},
                      ["test_hidden_listing"])
    recall = (passed(hidden, "test_b1_partly_filled_last_page_counts")
              + passed(hidden, "test_b2_no_notes_share_is_zero")) / 2
    feat = commit_by_subject(workspace, r"^feat\(rev01\): slice 01$")
    before = tests_at(workspace, feat) if feat else {}
    now = tests_at(workspace, "HEAD")
    public = bool(before) and all(now.get(name, ("missing",))[0] == "ok" for name in before)
    listing = (git_ok(workspace, "show", "HEAD:listing.py") or "").splitlines()
    decoy_kept = passed(hidden, "test_d1_latest_scans_every_note_newest_first") and listing.count(DECOY) == 1
    review = change_dir(workspace, "rev01") / "slices/01/review.md"
    active = active_block_or_fix(review.read_text()) if review.exists() else []
    real = sum(bool(BUGS.search(line)) for line in active)
    precision = decoy_kept * (real / len(active) if active else 0)
    report({
        "recall": recall,
        "precision": precision,
        "public_tests": public,
        "review_md": review_md_ok(review),
        "fix_commit": commit_by_subject(workspace, r"^fix\(rev01\): milestone 1 review$") is not None,
        "slice_done": slice_field(read_status(workspace, "rev01"), "state") == "done",
    }, ["recall", "precision", "public_tests", "review_md", "fix_commit", "slice_done"])
