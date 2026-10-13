"""Run: python3 bin/test_factory_packs_fetch.py (a temporary HOME and local sources; never the real ones or GitHub)."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FETCH = Path(__file__).with_name("factory-packs-fetch")
OFF = "* -text -eol -crlf -filter -ident -export-ignore -export-subst -working-tree-encoding\n"
FIXTURE_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}  # never the tester's config


def sh(cwd, *cmd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True, env=FIXTURE_ENV).stdout.strip()


def commit(work, message, folder="packs/demo"):
    sh(work, "git", "add", "-A", "-f")
    sh(work, "git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-qm", message)
    sh(work, "git", "push", "-q", "origin", "HEAD:main")
    return sh(work, "git", "rev-parse", f"HEAD:{folder}"), sh(work, "git", "rev-parse", "HEAD")


def write(path, text, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())
    if mode:
        path.chmod(mode)


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp).resolve()
    home, base = tmp / "home", tmp / "sources"
    packs = home / ".software-factory" / "packs"
    marker = tmp / "filter-ran"
    # A hostile global config in the fetch's HOME: autocrlf and a required filter driver that leaves a marker.
    write(home / ".gitconfig", f"[core]\n\tautocrlf = true\n[filter \"evil\"]\n\tclean = touch {marker}; cat\n"
                               f"\tsmudge = touch {marker}; cat\n\trequired = true\n")

    # A source owner/repo served over file:// with partial clone allowed, a pack in packs/demo at two versions.
    source = base / "owner" / "repo.git"
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", str(source))
    sh(source, "git", "config", "uploadpack.allowFilter", "true")
    sh(source, "git", "config", "uploadpack.allowAnySHA1InWant", "true")
    work = tmp / "work"
    sh(tmp, "git", "clone", "-q", str(source), str(work))
    write(work / ".git" / "info" / "attributes", OFF)  # the fixture's files go in byte for byte
    write(work / "packs" / "demo" / "SKILL.md", "v1\n")
    write(work / "packs" / "demo" / "rules" / "a.md", "rule a\n")
    write(work / "packs" / "demo" / "run.sh", "#!/bin/sh\n", 0o755)
    write(work / "packs" / "demo" / ".gitignore", "*.md\n")  # the pack's own ignores never drop its files
    write(work / "README.md", "root\n")
    tree1, commit1 = commit(work, "one")
    blob = sh(work, "git", "rev-parse", "HEAD:README.md")

    def project(label, entries, path="packs/demo"):
        repo = tmp / label
        (repo / ".software-factory").mkdir(parents=True)
        lines = [f"  {e[0]}: {{ source: {e[1]}, path: {e[3] if len(e) > 3 else path}, hash: {e[2]}, pinned_at: 2026-10-13 }}"
                 for e in entries]
        (repo / ".software-factory" / "factory.lock").write_text(
            "framework: { commit: " + "0" * 40 + ", installed: 2026-10-13 }\npacks:\n" + "\n".join(lines)
            + "\nskills_linked: [.claude/skills]\n")
        return repo

    def fetch(repo, home=home):
        # GitHub URLs are rewritten to the local sources the way any git config can rewrite them.
        return subprocess.run([sys.executable, FETCH, str(repo)], capture_output=True, text=True, check=False,
                              env={**os.environ, "HOME": str(home), "GIT_CONFIG_COUNT": "1",
                                   "GIT_CONFIG_KEY_0": f"url.file://{base}/.insteadOf",
                                   "GIT_CONFIG_VALUE_0": "https://github.com/"})

    def leftovers():
        return list(packs.glob(".tmp-*"))

    # HOME must be absolute and not /, and a linked ~/.software-factory is refused.
    a = project("a", [("demo", "owner/repo", tree1)])
    for bad in ("/", "relative"):
        r = fetch(a, home=bad)
        assert r.returncode != 0 and "must be an absolute path other than /" in r.stderr, r.stderr
    linked = tmp / "linked"
    linked.mkdir()
    (linked / ".software-factory").symlink_to(tmp)
    r = fetch(a, home=linked)
    assert r.returncode != 0 and "is a link to" in r.stderr, r.stderr

    # Fetch: the pin's tree, files and modes as the source holds them; a killed run's temp folder is swept.
    packs.mkdir(parents=True)
    (packs / ".tmp-killed" / "tree").mkdir(parents=True)
    r = fetch(a)
    assert r.returncode == 0 and f"fetched demo@{tree1}" in r.stdout, r.stdout + r.stderr
    demo1 = packs / f"demo@{tree1}"
    assert (demo1 / "SKILL.md").read_text() == "v1\n" and (demo1 / "rules" / "a.md").read_text() == "rule a\n"
    assert os.access(demo1 / "run.sh", os.X_OK) and not (demo1 / "README.md").exists()
    mirror = packs / ".mirrors" / "owner__repo.git"
    assert sh(tmp, "git", "--git-dir", str(mirror), "config", "remote.origin.url") == "https://github.com/owner/repo.git"
    assert not leftovers(), list(packs.iterdir())

    # The mirror is a real partial clone: blobs outside the fetched pack stay on the source.
    missing = sh(tmp, "git", "--git-dir", str(mirror), "rev-list", "--objects", "--missing=print", "--all")
    assert f"?{blob}" in missing.splitlines(), missing

    # A re-run leaves a complete folder alone; a lock file can be named directly.
    inode = (demo1 / "SKILL.md").stat().st_ino
    r = fetch(a / ".software-factory" / "factory.lock")
    assert r.returncode == 0 and f"present demo@{tree1}" in r.stdout, r.stdout + r.stderr
    assert (demo1 / "SKILL.md").stat().st_ino == inode

    # Two projects pin one pack at different hashes: the mirror fetches the new one, both sit side by side.
    # The mirror's origin is reset to GitHub on every use, whatever was written there since.
    write(work / "packs" / "demo" / "SKILL.md", "v2\n")
    tree2, _ = commit(work, "two")
    sh(tmp, "git", "--git-dir", str(mirror), "config", "remote.origin.url", f"file://{tmp}/nowhere.git")
    r = fetch(project("b", [("demo", "owner/repo", tree2)]))
    assert r.returncode == 0 and f"fetched demo@{tree2}" in r.stdout, r.stdout + r.stderr
    assert sh(tmp, "git", "--git-dir", str(mirror), "config", "remote.origin.url") == "https://github.com/owner/repo.git"
    assert (packs / f"demo@{tree2}" / "SKILL.md").read_text() == "v2\n" and (demo1 / "SKILL.md").read_text() == "v1\n"

    # A pin naming a commit loads that commit's root tree (the skills CLI's hash for a pack at a repository's root),
    # and only with path `.`.
    r = fetch(project("c", [("rooted", "owner/repo", commit1, ".")]))
    assert r.returncode == 0 and (packs / f"rooted@{commit1}" / "README.md").read_text() == "root\n", r.stdout + r.stderr
    r = fetch(project("c2", [("subdir", "owner/repo", commit1, "packs/demo")]))
    assert r.returncode == 1 and f"failed subdir: refused: {commit1} is a commit" in r.stdout, r.stdout
    assert not (packs / f"subdir@{commit1}").exists()

    # An unknown hash and a blob fail, and the run exits non-zero after trying every pin.
    unknown = "1" * 40
    r = fetch(project("d", [("ghost", "owner/repo", unknown), ("blobby", "owner/repo", blob), ("demo", "owner/repo", tree1)]))
    assert r.returncode == 1, r.stdout + r.stderr
    assert f"failed ghost: {unknown} not found in owner/repo" in r.stdout, r.stdout
    assert f"failed blobby: {blob} names a blob in owner/repo, not a tree" in r.stdout, r.stdout
    assert f"present demo@{tree1}" in r.stdout and "2 of 3 packs failed" in r.stderr, r.stdout + r.stderr
    assert not (packs / f"ghost@{unknown}").exists() and not (packs / f"blobby@{blob}").exists()

    # Names, hashes and sources that could leave the cache are refused before any git or file work.
    r = fetch(project("e", [("../escape", "owner/repo", tree1), ("ok", "owner/..", tree1), ("ok2", "../x", tree1),
                            ("ok3", "owner/repo", "../" + tree1[3:]), ("Upper", "owner/repo", tree1)]))
    assert r.returncode == 1 and r.stdout.count("failed ") == 5 and r.stdout.count("refused") == 5, r.stdout
    assert not (home / ".software-factory" / "escape").exists() and not (packs / ".mirrors" / "owner__...git").exists()
    assert sorted(p.name for p in packs.iterdir()) == sorted(
        [".lock", ".mirrors", f"demo@{tree1}", f"demo@{tree2}", f"rooted@{commit1}"]), list(packs.iterdir())

    # Attributes and config never rewrite content: export-ignore, export-subst, ident, eol, a filter driver and the
    # global autocrlf all leave the files byte for byte as the source holds them, and the filter never runs.
    odd_files = {"SKILL.md": "odd\n", "lf.txt": "a\nb\n", "crlf.txt": "a\r\nb\r\n", "id.txt": "$Id$\n",
                 "subst.txt": "$Format:%H$\n",
                 ".gitattributes": "SKILL.md export-ignore\n* filter=evil\n*.txt text eol=crlf\nid.txt ident\n"
                                   "subst.txt export-subst\n"}
    for name, text in odd_files.items():
        write(work / "packs" / "odd" / name, text)
    odd, _ = commit(work, "odd", "packs/odd")
    r = fetch(project("g", [("odd", "owner/repo", odd)]))
    assert r.returncode == 0 and f"fetched odd@{odd}" in r.stdout, r.stdout + r.stderr
    for name, text in odd_files.items():
        assert (packs / f"odd@{odd}" / name).read_bytes() == text.encode(), name
    assert not marker.exists() and not leftovers()

    # Symlinks stay inside the pack: a link within it loads, an absolute or escaping one fails the pin.
    write(work / "packs" / "links" / "SKILL.md", "linked\n")
    (work / "packs" / "links" / "AGENTS.md").symlink_to("SKILL.md")
    (work / "packs" / "links" / "sub").mkdir()
    (work / "packs" / "links" / "sub" / "up.md").symlink_to("../SKILL.md")
    write(work / "packs" / "abs" / "SKILL.md", "abs\n")
    (work / "packs" / "abs" / "hosts").symlink_to("/etc/hosts")
    write(work / "packs" / "out" / "SKILL.md", "out\n")
    (work / "packs" / "out" / "sibling.md").symlink_to("../demo/SKILL.md")
    commit(work, "links")
    trees = {p: sh(work, "git", "rev-parse", f"HEAD:packs/{p}") for p in ("links", "abs", "out")}
    r = fetch(project("h", [(p, "owner/repo", t) for p, t in trees.items()]))
    assert r.returncode == 1 and f"fetched links@{trees['links']}" in r.stdout, r.stdout + r.stderr
    assert (packs / f"links@{trees['links']}" / "sub" / "up.md").read_text() == "linked\n"
    assert "failed abs: refused: symlinks leave the pack: hosts -> /etc/hosts" in r.stdout, r.stdout
    assert "failed out: refused: symlinks leave the pack: sibling.md -> ../demo/SKILL.md" in r.stdout, r.stdout
    assert not (packs / f"abs@{trees['abs']}").exists() and not (packs / f"out@{trees['out']}").exists()
    assert not leftovers()

    # Offline: pins already in the mirror still load after the source fails for another pin.
    shutil.rmtree(demo1)
    source.rename(tmp / "away.git")
    r = fetch(project("i", [("ghost", "owner/repo", unknown), ("demo", "owner/repo", tree1)]))
    assert r.returncode == 1 and "failed ghost: git fetch" in r.stdout and f"fetched demo@{tree1}" in r.stdout, r.stdout
    assert (demo1 / "SKILL.md").read_text() == "v1\n"
    (tmp / "away.git").rename(source)

    # An unreachable source fails each of its pins, naming why.
    r = fetch(project("f", [("demo", "nobody/missing", "2" * 40), ("demo2", "nobody/missing", "3" * 40)]))
    assert r.returncode == 1 and r.stdout.count("failed ") == 2 and "git clone" in r.stdout, r.stdout

    # transfer.fsckObjects: a source holding a malformed object is never mirrored.
    evil = base / "owner" / "evil.git"
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", str(evil))
    one = bytes.fromhex(subprocess.run(["git", "--git-dir", str(evil), "hash-object", "-w", "--stdin"], input=b"x\n",
                                       capture_output=True, check=True, env=FIXTURE_ENV).stdout.decode().strip())
    bad_tree = subprocess.run(["git", "--git-dir", str(evil), "hash-object", "-w", "-t", "tree", "--literally", "--stdin"],
                              input=b"100644 SKILL.md\0" + one + b"100644 SKILL.md\0" + one,  # a duplicate entry
                              capture_output=True, check=True, env=FIXTURE_ENV).stdout.decode().strip()
    bad_commit = sh(evil, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit-tree", bad_tree, "-m", "bad")
    sh(evil, "git", "update-ref", "refs/heads/main", bad_commit)
    sh(tmp, "git", "clone", "-q", "--bare", str(evil), str(tmp / "plain.git"))  # git accepts it without fsck
    r = fetch(project("j", [("evil", "owner/evil", bad_tree)]))
    assert r.returncode == 1 and "failed evil: git clone" in r.stdout, r.stdout + r.stderr
    assert not (packs / ".mirrors" / "owner__evil.git").exists() and not leftovers()

    # The lock's packs are a block of one-line entries; anything else stops the run instead of loading nothing.
    def lock_with(label, text):
        repo = tmp / label
        (repo / ".software-factory").mkdir(parents=True)
        (repo / ".software-factory" / "factory.lock").write_text(text)
        return repo
    r = fetch(lock_with("k", "packs: { demo: { source: owner/repo, hash: " + tree1 + " } }\n"))
    assert r.returncode != 0 and "write packs as a block" in r.stderr, r.stdout + r.stderr
    r = fetch(lock_with("l", "packs:\n  demo:\n    source: owner/repo\n"))
    assert r.returncode != 0 and "not a pack entry: demo:" in r.stderr, r.stdout + r.stderr
    r = fetch(lock_with("m", "packs: {}   # none yet\nskills_linked: []\n"))
    assert r.returncode == 0 and "no packs pinned" in r.stdout, r.stdout + r.stderr
    entry = "  demo: { source: owner/repo, hash: " + tree1 + " }\n"
    r = fetch(lock_with("n", "packs:\n" + entry + "skills_linked: []\npacks:\n" + entry))
    assert r.returncode != 0 and "a second packs: block" in r.stderr, r.stdout + r.stderr
    r = fetch(lock_with("o", "packs:\n" + entry + entry))
    assert r.returncode != 0 and "pinned twice" in r.stderr, r.stdout + r.stderr

print("factory-packs-fetch: all checks passed")
