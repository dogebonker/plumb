"""Grade a REV-02 workspace: python3 grade.py <workspace>. Prints one JSON line."""

import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import active_block_or_fix, change_dir, commit_by_subject, git_ok, read_status, report, \
    review_md_ok, review_range, same_commit, slice_field, workspace_arg  # noqa: E402

if __name__ == "__main__":
    workspace = workspace_arg()
    review = change_dir(workspace, "rev02") / "slices/01/review.md"
    status = read_status(workspace, "rev02")
    feat = commit_by_subject(workspace, r"^feat\(rev02\): slice 01$")
    subjects = (git_ok(workspace, "log", "--format=%s", f"{feat}..HEAD") or "").splitlines() if feat else []
    unchanged = feat and git_ok(workspace, "diff", "--quiet", feat, "HEAD", "--", ".", ":!.plumb") is not None
    start, end = review_range(review)
    report({
        "review_md": review_md_ok(review),
        "no_block_or_fix": review.exists() and not active_block_or_fix(review.read_text()),
        "no_fix_commit": bool(unchanged) and not any(subject.startswith("fix(") for subject in subjects),
        "head_unchanged": bool(feat) and slice_field(status, "head_commit") == feat,
        "slice_done": slice_field(status, "state") == "done",
        "review_commit": "chore(plumb): milestone 1 review" in subjects,
        "range": same_commit(slice_field(status, "base_commit"), start) and same_commit(feat, end),
    }, ["review_md", "no_block_or_fix", "no_fix_commit", "head_unchanged", "slice_done", "review_commit", "range"])
