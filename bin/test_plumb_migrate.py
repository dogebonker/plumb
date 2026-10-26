"""Run: python3 bin/test_plumb_migrate.py (temporary repositories only)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MIGRATE = Path(__file__).with_name("plumb-migrate")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, check=True).stdout


def migrate(repo, *args, home=None):
    env = {**os.environ, "HOME": str(home or Path(repo).parent / "home")}  # never the real ~/.claude
    return subprocess.run([sys.executable, MIGRATE, *args, str(repo)], capture_output=True, text=True, check=False, env=env)


def write(path, text="x\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def snapshot(repo):
    files = sorted(str(p.relative_to(repo)) for p in repo.rglob("*") if ".git" not in p.relative_to(repo).parts)
    return files, (repo / ".git/info/exclude").read_text(), git(repo, "status", "--porcelain", "--ignored")


def new_repo(tmp, name):
    repo = Path(tmp) / name
    git(tmp, "init", "-q", "-b", "main", str(repo))
    write(repo / "src/app.py")
    write(repo / ".factory/system/layout.md")
    write(repo / ".factory/changes/demo/status.yaml", "branch: plumb/demo\n")
    write(repo / ".factory/ui/shot.png")
    return repo


with tempfile.TemporaryDirectory() as tmp:
    # Committed mode: tracked folders move with git mv (their untracked files along), an ignored run folder
    # moves with a plain rename, and its exclude line follows it to runs/.
    repo = new_repo(tmp, "committed")
    write(repo / ".git/info/exclude", "# git ls-files --others --exclude-from=.git/info/exclude\n.factory/ui/\n.factoryx\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    git(repo, "branch", "old")  # still has .factory/
    git(repo, "checkout", "-q", "-b", "clean")
    git(repo, "rm", "-rq", ".factory")
    git(repo, "commit", "-qm", "no Plumb")
    git(repo, "checkout", "-q", "main")
    blob = subprocess.run(["git", "-C", str(repo), "hash-object", "-w", "--stdin"], input="x\n",
                          capture_output=True, text=True, check=True).stdout.strip()
    tree = subprocess.run(["git", "-C", str(repo), "mktree"], input=f"100644 blob {blob}\t.factory\n",
                          capture_output=True, text=True, check=True).stdout.strip()
    git(repo, "branch", "file-named-factory", git(repo, "commit-tree", tree, "-m", "a file").strip())  # not listed
    git(repo, "branch", "in-worktree")  # has .factory/, but another worktree has it checked out
    git(repo, "worktree", "add", "-q", str(Path(tmp) / "wt"), "in-worktree")
    git(tmp, "init", "-q", "--bare", str(Path(tmp) / "remote.git"))
    git(repo, "remote", "add", "origin", str(Path(tmp) / "remote.git"))
    git(repo, "push", "-q", "origin", "old", "clean")
    git(repo, "remote", "set-head", "origin", "old")  # origin/HEAD is a symref: listed once, as origin/old
    write(repo / ".factory/changes/demo/status.yaml", "branch: plumb/demo\nedited: true\n")
    write(repo / ".factory/changes/demo/slices/01/packet.md")  # untracked inside a tracked folder

    before = snapshot(repo)
    r = migrate(repo, "--dry-run")
    assert r.returncode == 0, r.stderr
    assert snapshot(repo) == before, "a dry run changes nothing"
    assert "would git mv .factory/system .plumb/system" in r.stdout, r.stdout
    assert "would mv .factory/ui .plumb/runs/ui" in r.stdout, r.stdout
    assert ".factory/ui/ -> .plumb/runs/ui/" in r.stdout, r.stdout
    assert "other local branches with .software-factory/ or .factory/: old\n" in r.stdout, r.stdout  # not main, clean or the file
    assert "skipped, checked out in another worktree: in-worktree\n" in r.stdout, r.stdout
    assert "remote branches with .software-factory/ or .factory/: origin/old\n" in r.stdout, r.stdout

    r = migrate(repo)
    assert r.returncode == 0, r.stderr
    assert not (repo / ".factory").exists()
    assert (repo / ".plumb/changes/demo/status.yaml").read_text().endswith("edited: true\n")
    assert (repo / ".plumb/changes/demo/slices/01/packet.md").exists()
    assert (repo / ".plumb/runs/ui/shot.png").exists()
    staged = git(repo, "diff", "--cached", "--name-status", "-M").splitlines()
    assert "R100\t.factory/system/layout.md\t.plumb/system/layout.md" in staged, staged
    assert git(repo, "log", "--oneline").count("\n") == 1, "nothing is committed"
    exclude = (repo / ".git/info/exclude").read_text()
    assert ".plumb/runs/ui/\n.factoryx\n" in exclude and exclude.startswith("# git ls-files"), exclude
    assert git(repo, "check-ignore", ".plumb/runs/ui/shot.png").strip()

    # Ignored mode: nothing is tracked, so every folder moves with a plain rename. Exclude lines keep their
    # anchor, glob and negation prefixes and lose a carriage return; a symlink inside is moved as a link, with a warning.
    repo = new_repo(tmp, "ignored")
    write(repo / ".git/info/exclude", "/.factory/\n**/.factory/\r\n!.factory/x\n.factory\n.factoryx\n")
    (repo / ".factory/system/latest").symlink_to("layout.md")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    r = migrate(repo)
    assert r.returncode == 0, r.stderr
    assert "mv .factory/changes .plumb/changes" in r.stdout and "git mv" not in r.stdout, r.stdout
    assert "warning: .factory/system/latest is a symlink" in r.stdout, r.stdout
    assert (repo / ".plumb/system/layout.md").exists() and not (repo / ".factory").exists()
    assert (repo / ".plumb/system/latest").is_symlink()
    assert (repo / ".git/info/exclude").read_text() == \
        "/.plumb/\n**/.plumb/\n!.plumb/x\n.plumb\n.factoryx\n"
    assert git(repo, "status", "--porcelain") == "", "the move stays ignored"

    # Refusals, each before anything changes: a dirty tracked file outside .factory/, and an existing target.
    repo = new_repo(tmp, "refuse")
    write(repo / ".git/info/exclude", "")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    write(repo / "src/app.py", "edited\n")
    before = snapshot(repo)
    r = migrate(repo)
    assert r.returncode == 1 and "tracked changes outside .software-factory/ or .factory/: src/app.py" in r.stderr, r.stderr
    assert snapshot(repo) == before
    git(repo, "checkout", "-q", "--", "src/app.py")
    for target in ("system", "changes"):
        write(repo / ".plumb" / target / "keep.md")
        before = snapshot(repo)
        r = migrate(repo)
        assert r.returncode == 1 and f".plumb/{target} already exists" in r.stderr, r.stderr
        assert snapshot(repo) == before
        (repo / ".plumb" / target / "keep.md").unlink()
        (repo / ".plumb" / target).rmdir()

    # A deleted tracked file under .factory/ would stop git mv half-way: refused.
    (repo / ".factory/system/layout.md").unlink()
    before = snapshot(repo)
    r = migrate(repo)
    assert r.returncode == 1 and "deleted or unmerged files under .software-factory/ or .factory/: .factory/system/layout.md" in r.stderr, r.stderr
    assert snapshot(repo) == before
    git(repo, "checkout", "-q", "--", ".factory")

    # Mid-rebase (or merge, cherry-pick, revert): refused.
    rebase = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "rebase-merge").strip())
    rebase.mkdir()
    r = migrate(repo)
    assert r.returncode == 1 and "rebase-merge is in progress" in r.stderr, r.stderr
    rebase.rmdir()

    # .factory itself a symlink: refused.
    link_repo = new_repo(tmp, "linked")
    (link_repo / ".factory").rename(Path(tmp) / "elsewhere")
    (link_repo / ".factory").symlink_to(Path(tmp) / "elsewhere")
    r = migrate(link_repo, "--dry-run")
    assert r.returncode != 0 and ".factory is a symlink" in r.stderr, r.stderr
    assert (Path(tmp) / "elsewhere/system/layout.md").exists()

    # A branch already migrated: nothing to move, the other branches are still listed.
    git(repo, "branch", "legacy")
    git(repo, "mv", ".factory", ".plumb")
    git(repo, "commit", "-qm", "migrated")
    r = migrate(repo)
    assert r.returncode == 0 and "nothing to migrate" in r.stdout and "with .software-factory/ or .factory/: legacy" in r.stdout, r.stdout

    # .software-factory/ (the name before Plumb) moves whole; its lock becomes plumb.lock.
    named = Path(tmp) / "named"
    git(tmp, "init", "-q", "-b", "main", str(named))
    write(named / ".software-factory/factory.lock", "framework: { commit: abc }\n")
    write(named / ".software-factory/changes/demo/status.yaml", "branch: factory/demo\n")
    write(named / ".software-factory/principles.md")
    git(named, "add", "-A")
    git(named, "commit", "-qm", "before the rename")
    write(named / ".software-factory/scratch/run.log")  # untracked, ignored
    write(named / ".git/info/exclude", "/.software-factory/scratch/\n")
    r = migrate(named)
    assert r.returncode == 0, r.stderr
    staged = git(named, "diff", "--cached", "--name-status", "-M")
    assert "R100\t.software-factory/factory.lock\t.plumb/plumb.lock" in staged, staged
    assert "R100\t.software-factory/changes/demo/status.yaml\t.plumb/changes/demo/status.yaml" in staged, staged
    assert (named / ".plumb/scratch/run.log").exists() and not (named / ".software-factory").exists()
    assert (named / ".git/info/exclude").read_text() == "/.plumb/scratch/\n"

    # Both old folders with the same entry: refused before anything moves.
    both = Path(tmp) / "both"
    git(tmp, "init", "-q", "-b", "main", str(both))
    write(both / ".software-factory/changes/a/status.yaml")
    write(both / ".factory/changes/b/status.yaml")
    r = migrate(both)
    assert r.returncode == 1 and "more than one old folder" in r.stderr, r.stderr
    assert (both / ".factory/changes/b/status.yaml").exists() and (both / ".software-factory/changes/a/status.yaml").exists()

    # A slice worktree registered under the old folder: refused, since a plain move would orphan it.
    held = Path(tmp) / "held"
    git(tmp, "init", "-q", "-b", "main", str(held))
    write(held / "src/app.py")
    write(held / ".git/info/exclude", "/.software-factory/\n")
    git(held, "add", "-A")
    git(held, "commit", "-qm", "source")
    write(held / ".software-factory/changes/demo/status.yaml")
    git(held, "worktree", "add", "-q", "-b", "factory/demo-02", str(held / ".software-factory/worktrees/02"), "HEAD")
    r = migrate(held)
    assert r.returncode == 1 and "lives under an old folder" in r.stderr, r.stderr
    assert (held / ".software-factory/worktrees/02/src/app.py").exists() and not (held / ".plumb").exists()

    # The project still runs the old hook, which would stop gating after the move: refused.
    hooked = Path(tmp) / "hooked"
    git(tmp, "init", "-q", "-b", "main", str(hooked))
    write(hooked / ".software-factory/changes/demo/status.yaml")
    write(hooked / ".claude/settings.local.json", '{"hooks": {"PreToolUse": [{"hooks": [{"command": "python3 /x/hooks/factory_gate.py"}]}]}}')
    r = migrate(hooked)
    assert r.returncode == 1 and "still runs factory_gate.py" in r.stderr, r.stderr
    assert (hooked / ".software-factory/changes/demo/status.yaml").exists()

    # Once init has repointed a tracked .claude/settings.json, that uncommitted edit does not block the move,
    # and an ignored leftover in .factory/ that lands elsewhere moves alongside .software-factory/.
    write(hooked / ".claude/settings.json", '{"hooks": {"PreToolUse": [{"hooks": [{"command": "python3 /x/hooks/factory_gate.py"}]}]}}')
    (hooked / ".claude/settings.local.json").unlink()
    git(hooked, "add", ".claude/settings.json")
    git(hooked, "commit", "-qm", "team hook")
    write(hooked / ".claude/settings.json", '{"hooks": {"PreToolUse": [{"hooks": [{"command": "python3 /x/hooks/plumb_gate.py"}]}]}}')
    write(hooked / ".factory/ui/shot.png", "png")
    r = migrate(hooked)
    assert r.returncode == 0, r.stderr
    assert (hooked / ".plumb/changes/demo/status.yaml").exists() and (hooked / ".plumb/runs/ui/shot.png").exists()

print("plumb-migrate: all checks passed")
