"""Run: python3 bin/test_factory_install.py (a temporary HOME and repository; never the real ones)."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

INSTALL = Path(__file__).with_name("factory-install")


def sh(cwd, *cmd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    home, repo = tmp / "home", tmp / "factory"
    home.mkdir()
    env = {**os.environ, "HOME": str(home)}

    def install(*args, home=home):
        return subprocess.run([sys.executable, INSTALL, *args], capture_output=True, text=True,
                              env={**env, "HOME": str(home)}, check=False)

    for part in ("kit", "skills/factory-triage", "hooks", "bin", "runner"):
        (repo / part).mkdir(parents=True)
        (repo / part / "f.txt").write_text(part + "\n")
    bundled_book = repo / "kit" / "packs" / ("book@" + "a" * 40)
    bundled_book.mkdir(parents=True)
    (bundled_book / "SKILL.md").write_text("pinned book\n")
    (bundled_book / "run.sh").write_text("#!/bin/sh\n")
    (bundled_book / "run.sh").chmod(0o755)
    sh(tmp, "git", "init", "-q", "-b", "main", str(repo))
    sh(repo, "git", "add", ".")
    sh(repo, "git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-qm", "one")
    sha = sh(repo, "git", "rev-parse", "HEAD")
    dest = home / ".software-factory" / "framework" / sha

    # HOME must be absolute and not /.
    for bad in ("/", "relative"):
        r = install("HEAD", "--repo", str(repo), home=bad)
        assert r.returncode != 0 and "must be an absolute path other than /" in r.stderr, r.stderr

    # A link to anything but a checkout's kit/ is left alone, and the install stops naming its target.
    other = tmp / "other"
    other.mkdir()
    (home / ".software-factory").symlink_to(other)
    r = install("HEAD", "--repo", str(repo))
    assert r.returncode != 0 and f"is a link to {other.resolve()}" in r.stderr, r.stderr
    assert (home / ".software-factory").is_symlink() and not any(other.iterdir())
    (home / ".software-factory").unlink()

    # An old link to a checkout's kit/ is removed, never its target.
    old_kit = tmp / "old-checkout" / "kit"
    old_kit.mkdir(parents=True)
    (old_kit / "principles.md").write_text("taste\n")
    (old_kit / "packs.lock.yaml").write_text("packs:\n")
    (home / ".software-factory").symlink_to(old_kit)

    r = install("HEAD", "--repo", str(repo))
    assert r.returncode == 0, r.stderr
    assert "removed the old link" in r.stdout and (old_kit / "principles.md").read_text() == "taste\n", r.stdout
    assert not (home / ".software-factory").is_symlink()
    assert r.stdout.splitlines()[-1] == str(dest), r.stdout
    assert sorted(p.name for p in dest.iterdir()) == ["bin", "hooks", "kit", "skills"]  # runner/ is not part of it
    assert (dest / "skills" / "factory-triage" / "f.txt").read_text() == "skills/factory-triage\n"
    installed_book = dest / "kit" / "packs" / bundled_book.name
    assert (installed_book / "SKILL.md").read_bytes() == b"pinned book\n"
    assert os.access(installed_book / "run.sh", os.X_OK)
    config = home / ".software-factory" / "user" / "config.yaml"
    assert config.read_text() == f'framework_repo: "{repo.resolve()}"\n', config.read_text()
    assert [p.name for p in dest.parent.iterdir()] == [sha], "no temporary folder is left behind"

    # A re-run reports the install and changes nothing; without --repo, framework_repo names the checkout.
    (dest / "kit" / "f.txt").write_text("unchanged\n")
    r = install(sha[:7])
    assert r.returncode == 0 and "already installed" in r.stdout, r.stdout + r.stderr
    assert (dest / "kit" / "f.txt").read_text() == "unchanged\n"

    # An incomplete install (a hand install without hooks/) is redone.
    shutil.rmtree(dest / "hooks")
    r = install("HEAD")
    assert r.returncode == 0 and "installed framework" in r.stdout, r.stdout + r.stderr
    assert (dest / "hooks" / "f.txt").exists() and (dest / "kit" / "f.txt").read_text() == "kit\n"

    # framework_repo may start with ~; a config.yaml without a readable framework_repo stops the install.
    config.write_text("framework_repo: ~/../factory\n")
    assert install("HEAD").returncode == 0
    config.write_text("framework_rep: oops\n")
    r = install("HEAD")
    assert r.returncode != 0 and "has no readable framework_repo" in r.stderr, r.stderr
    config.write_text(f'framework_repo: "{repo}"\n')

    # An unknown ref fails before anything is written.
    r = install("no-such-ref")
    assert r.returncode != 0 and "no-such-ref" in r.stderr, r.stderr

print("factory-install: all checks passed")
