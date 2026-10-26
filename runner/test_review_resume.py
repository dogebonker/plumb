"""Prove the source-tree precondition in plumb-review's resume shortcut."""
import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as temporary:
    repo = Path(temporary)

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def current(head):
        tracked = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", head, "--", ".", ":!.plumb"],
                                 check=False).returncode == 0
        indexed = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--quiet", head,
                                  "--", ".", ":!.plumb"], check=False).returncode == 0
        return tracked and indexed and not git("ls-files", "--others", "--exclude-standard", "--", ".", ":!.plumb")

    git("init", "-q")
    git("config", "user.name", "Benchmark")
    git("config", "user.email", "benchmark@example.invalid")
    git("config", "commit.gpgsign", "false")
    (repo / "source.py").write_text("value = 1\n")
    git("add", ".")
    git("commit", "-qm", "reviewed source")
    head = git("rev-parse", "HEAD")
    assert current(head)
    (repo / ".plumb").mkdir()
    (repo / ".plumb" / "review.md").write_text("awaiting sign-off\n")
    assert current(head)  # untracked planning artifacts do not change reviewed source
    git("add", ".plumb")
    git("commit", "-qm", "planning only")
    assert current(head)
    (repo / "source.py").write_text("value = 2\n")
    assert not current(head)  # unstaged source edit
    git("add", "source.py")
    assert not current(head)  # staged source edit
    (repo / "source.py").write_text("value = 1\n")
    assert not current(head)  # restored worktree must not hide a staged source change
    (repo / "source.py").write_text("value = 2\n")
    git("commit", "-qm", "source changed while waiting")
    assert not current(head)  # an intervening source commit
    refreshed = git("rev-parse", "HEAD")
    assert current(refreshed)
    assert "+value = 2" in git("diff", f"{head}..{refreshed}", "--", "source.py")
    (repo / "source.py").write_text("value = 1\n")
    assert not current(refreshed)  # dirty source must first enter the refreshed commit Range
    git("add", "source.py")
    git("commit", "-qm", "restore reviewed source")
    assert current(head)  # identical committed source is safe despite a different commit identity
    (repo / "new_source.py").write_text("value = 3\n")
    assert not current(head)  # untracked source must not silently evade review

print("review resume: all checks passed")
