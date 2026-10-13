"""Run: python3 runner/test_factory_run.py"""
import hashlib
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import factory_run
from factory_run import (
    approver_reviews,
    command,
    created_commits,
    home_problem,
    missing_framework,
    new_head_trusted,
    only_factory,
    next_skill,
    parse_status,
    triage_skips,
    unmigrated,
    verify,
)

STATUS = """feature: demo
branch: factory/demo
mode: headless
waiting_since: 2026-10-10T09:00:00Z
gates:
  product:      {p}
  architecture: {{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }}
  interface:    {{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }}
  slices:       {{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }}
slices: []
reconciled: false
"""
PENDING = "{ state: pending, approved_by: null, approved_at: null, doc_sha256: null }"

# Commands are the first line of an approver's review.
assert command("approve product\nlooks good") == ("approve", "product")
assert command("Sign off slice 01") == ("sign-off", "01")
assert command("please approve product") is None
assert command("") is None
assert command("Start") == ("start", None)

# A later CHANGES_REQUESTED review by the same approver revokes their earlier approvals.
ok = {"login": "Alice", "state": "APPROVED", "body": "approve product", "commit": "c1", "at": "2026-10-10T10:00:00Z"}
later_no = {**ok, "state": "CHANGES_REQUESTED", "body": "no", "at": "2026-10-10T11:00:00Z"}
assert approver_reviews([ok], {"alice"}) == [ok]
assert approver_reviews([ok, later_no], {"alice"}) == []
assert approver_reviews([ok], {"bob"}) == []

# The next skill follows the gates, then the slices, then reconcile.
assert next_skill(parse_status(STATUS.format(p=PENDING))) == "factory-product"
ui_status = parse_status(STATUS.format(p=PENDING).replace("mode: headless", "mode: headless\nui: true"))
assert next_skill(ui_status, has_design=False) == "factory-ui-ux"
assert next_skill(ui_status, has_design=True) == "factory-product"
approved_all = STATUS.format(p="{ state: approved }").replace("state: pending", "state: approved")
assert next_skill(parse_status(approved_all)) is None  # no slices yet: nothing to build
built = approved_all.replace("slices: []", "slices:\n  - { id: 1, name: t, state: green, head_commit: abc }")
assert next_skill(parse_status(built)) == "factory-review"
assert next_skill(parse_status(built.replace("state: green", "state: done"))) == "factory-reconcile"

with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)

    def git(*args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false", "-C", str(repo), *args],
                              capture_output=True, text=True, check=True).stdout.strip()

    def check(text, approvals, may_skip=frozenset()):
        return verify(repo, "HEAD", change, text, approvals, may_skip)

    git("init", "-q", "-b", "factory/demo")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    change = ".software-factory/changes/demo"
    (repo / change).mkdir(parents=True)
    (repo / change / "01-product.md").write_bytes(b"# product v1\r\n")  # CRLF hashes as bytes
    git("add", ".")
    git("commit", "-qm", "v1")
    v1 = git("rev-parse", "HEAD")
    digest = hashlib.sha256(b"# product v1\r\n").hexdigest()
    review = {"login": "alice", "body": "approve product", "commit": v1, "at": "2026-10-10T10:00:00Z"}

    # An approval of the current document is recorded, and clears the wait.
    text, notes = check(STATUS.format(p=PENDING), [review])
    assert notes == ["product approved by alice"], notes
    assert f"doc_sha256: {digest}" in text and "waiting_since: null" in text

    # An approval the agent wrote itself, with no review behind it, is undone.
    forged = STATUS.format(p=f"{{ state: approved, approved_by: bot, approved_at: x, doc_sha256: {digest} }}")
    text, notes = check(forged, [])
    assert notes == ["product reset to pending: no matching approval"], notes
    assert parse_status(text)["gates"]["product"]["state"] == "pending"

    # An approval of an older version of the document does not count.
    (repo / change / "01-product.md").write_bytes(b"# product v2\n")
    git("commit", "-qam", "v2")
    _, notes = check(STATUS.format(p=PENDING), [review])
    assert notes == [], notes

    # Approving a later gate before an earlier one does nothing.
    v2 = git("rev-parse", "HEAD")
    _, notes = check(STATUS.format(p=PENDING),
                      [{**review, "body": "approve slices", "commit": v2}])
    assert notes == [], notes

    # A sign-off counts only at a commit that holds review.md and contains the slice's head commit.
    head_status = approved_all.replace("slices: []", f"slices:\n  - {{ id: 1, name: t, state: green, head_commit: {v2} }}")
    gates_ok = []
    for gate, doc in [("product", "01-product.md"), ("architecture", "02-architecture.md"),
                      ("interface", "03-interface.md"), ("slices", "04-slices.md")]:
        if gate != "product":
            (repo / change / doc).write_text(f"# {gate}\n")
    git("add", ".")
    git("commit", "-qm", "docs")
    docs = git("rev-parse", "HEAD")
    for gate, doc in [("product", "01-product.md"), ("architecture", "02-architecture.md"),
                      ("interface", "03-interface.md"), ("slices", "04-slices.md")]:
        h = hashlib.sha256((repo / change / doc).read_bytes()).hexdigest()
        head_status = head_status.replace(f"  {gate}:", f"  {gate}: {{ state: approved, approved_by: alice, "
                                          f"approved_at: 2026-10-10T09:30:00Z, doc_sha256: {h} }} #", 1)
        gates_ok.append({**review, "body": f"approve {gate}", "commit": docs})
    sign = {**review, "body": "sign off slice 01", "commit": docs, "at": "2026-10-10T11:00:00Z"}
    _, notes = check(head_status, [*gates_ok, sign])
    assert notes == [], notes  # no review.md at that commit yet
    (repo / change / "slices" / "01").mkdir(parents=True)
    (repo / change / "slices" / "01" / "review.md").write_text("# Review\n")
    git("add", ".")
    git("commit", "-qm", "review")
    reviewed = git("rev-parse", "HEAD")
    text, notes = check(head_status, [*gates_ok, {**sign, "commit": reviewed}])
    assert notes == ["slice 01 signed off by alice"], notes
    assert parse_status(text)["slices"][0]["state"] == "done"

    # The sign-off must sit on the branch head, after the slices approval, over a full head_commit with
    # only .software-factory/ changes since it.
    assert check(head_status.replace(v2, v2[:12]), [*gates_ok, {**sign, "commit": reviewed}])[1] == []
    early = {**sign, "commit": reviewed, "at": "2026-10-10T09:00:00Z"}
    assert check(head_status, [*gates_ok, early])[1] == []
    (repo / "src.txt").write_text("new code after the reviewed commit\n")
    git("add", ".")
    git("commit", "-qm", "code after review")
    assert check(head_status, [*gates_ok, {**sign, "commit": reviewed}])[1] == []  # not at head: not recorded
    code_head = head_status.replace(v2, git("rev-parse", "HEAD~2"))
    assert check(code_head, [*gates_ok, {**sign, "commit": git("rev-parse", "HEAD")}])[1] == []  # code since head_commit

    # A gate the agent marked skipped is reset unless triage skipped it.
    skipped = STATUS.format(p="{ state: skipped }")
    text, notes = check(skipped, [])
    assert notes == ["product reset to pending: triage did not skip it"], notes
    assert check(skipped, [], {"product"})[1] == []

    # Only the commit that created status.yaml on the branch's own line decides which gates triage skipped.
    status_path = f"{change}/status.yaml"
    (repo / status_path).write_text(STATUS.format(p="{ state: skipped }"))
    git("add", ".")
    git("commit", "-qm", "triage")
    (repo / status_path).write_text(STATUS.format(p="{ state: skipped }").replace(
        "architecture: { state: pending", "architecture: { state: skipped"))
    git("commit", "-qam", "agent skips architecture")
    start = {"login": "alice", "state": "APPROVED", "body": "start", "commit": git("rev-parse", "HEAD"), "at": "t"}
    assert triage_skips(repo, "HEAD", status_path, [start]) == {"product"}
    assert triage_skips(repo, "HEAD", status_path, []) == set()  # no approver started it: no skips
    (repo / status_path).write_text(STATUS.format(p=PENDING))
    git("commit", "-qam", "unskip before the start review")
    laundered = {**start, "commit": git("rev-parse", "HEAD")}
    assert triage_skips(repo, "HEAD", status_path, [laundered]) == set()  # not skipped where the approver looked

    # The harness's own commits are read from its reflog; commits it only checked out are not its own.
    clone = repo / "clone"
    subprocess.run(["git", "clone", "-q", str(repo), str(clone)], check=True)
    cloned = git("rev-parse", "HEAD")
    (clone / "x.txt").write_text("x\n")
    subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(clone),
                    "commit", "-qam", "x", "--allow-empty"], check=True)
    made = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    assert made in created_commits(clone) and cloned not in created_commits(clone)

    # A new head counts as the harness's own only as a fast-forward made of commits it created.
    older = git("rev-parse", "HEAD~1")
    assert new_head_trusted(repo, cloned, cloned, set())
    assert new_head_trusted(clone, cloned, made, {made})
    assert not new_head_trusted(clone, cloned, made, set())
    assert not new_head_trusted(repo, cloned, older, set())  # a force-push back to an older commit

    # A duplicated gate line survives one rewrite, so a second check still finds work: the runner refuses it.
    dup = STATUS.format(p=PENDING).replace("gates:\n", f"gates:\n  product: {PENDING}\n").replace(
        f"  product:      {PENDING}", f"  product: {{ state: approved, approved_by: bot, approved_at: x, doc_sha256: {digest} }}")
    text, notes = check(dup, [])
    assert notes and check(text, [])[1], (notes, check(text, [])[1])

    # A quoted done state is reset too.
    quoted = head_status.replace("state: green", 'state: "done"')
    text, notes = check(quoted, gates_ok)
    assert notes == ["slice 01 reset to green: no matching sign-off"], notes
    assert parse_status(text)["slices"][0]["state"] == "green"

    # A send-back to the slices gate keeps a signed-off slice done, before and after the new approval,
    # so the next skill builds the fix slice instead of re-reviewing slice 01.
    done_status = head_status.replace("state: green", "state: done")
    signed_off = {**sign, "commit": reviewed}
    fix = done_status.replace(f"head_commit: {v2} }}", f"head_commit: {v2} }}\n  - {{ id: 2, name: fix, state: pending, head_commit: null }}")
    (repo / change / "04-slices.md").write_text("# slices v2: a fix slice\n")
    (repo / status_path).write_text(fix)
    git("commit", "-qam", "send back")
    text, notes = check(done_status, [*gates_ok, signed_off])
    assert notes == ["slices reset to pending: no matching approval"], notes
    assert parse_status(text)["slices"][0]["state"] == "done"
    again = {**review, "body": "approve slices", "commit": git("rev-parse", "HEAD"), "at": "2026-10-10T12:00:00Z"}
    text, notes = check(fix, [*gates_ok, signed_off, again])
    assert parse_status(text)["gates"]["slices"]["state"] == "approved", notes
    assert parse_status(text)["slices"][0]["state"] == "done", notes
    assert next_skill(parse_status(text)) == "factory-build"

    # An agent cannot revive a slice by writing done into status.yaml: an earlier sign-off counts only when
    # the approved commit already showed the slice done at the same head_commit.
    (repo / status_path).write_text(fix.replace("state: done", "state: rewind", 1))
    git("commit", "-qam", "slice 01 rewound")
    rewound = {**again, "commit": git("rev-parse", "HEAD"), "at": "2026-10-10T13:00:00Z"}
    text, notes = check(fix, [*gates_ok, signed_off, rewound])
    assert "slice 01 reset to green: no matching sign-off" in notes, notes
    assert parse_status(text)["slices"][0]["state"] == "green"

    # Reapproving changed product content must not revive downstream reviews of its old snapshot.
    (repo / change / "01-product.md").write_text("# product v3\n")
    git("commit", "-qam", "revise product")
    revised = git("rev-parse", "HEAD")
    product_again = {**review, "commit": revised, "at": "2026-10-10T15:00:00Z"}
    for prior in (head_status, approved_all.replace("state: approved", "state: pending")):
        text, notes = check(prior, [*gates_ok, product_again, rewound])
        states = parse_status(text)["gates"]
        assert states["product"]["state"] == "approved", notes
        assert all(states[g]["state"] == "pending" for g in ("architecture", "interface", "slices")), notes
        assert check(text, [*gates_ok, product_again, rewound])[1] == []  # correction is idempotent

    # Review submission order does not matter when every gate covers the same current chain snapshot.
    renewed = [{**review, "body": f"approve {gate}", "commit": revised}
               for gate in ("architecture", "interface", "slices")]
    text, notes = check(STATUS.format(p=PENDING), [product_again, *renewed])
    assert all(g["state"] == "approved" for g in parse_status(text)["gates"].values()), notes

    # A skipped upstream gate has no required document snapshot.
    text, notes = check(STATUS.format(p="{ state: skipped }"), [*gates_ok, rewound], {"product"})
    assert parse_status(text)["gates"]["architecture"]["state"] == "approved", notes

    # Matching document content on a disconnected commit is not an approval of this branch.
    detached = git("commit-tree", "HEAD^{tree}", "-m", "unrelated history")
    assert check(STATUS.format(p=PENDING), [{**product_again, "commit": detached}])[1] == []

    # Planning state is .software-factory/ minus the lock and the project's principles: a sign-off does not
    # cover a change to either.
    base = git("rev-parse", "HEAD")
    (repo / change / "notes.md").write_text("planning\n")
    git("add", change)
    git("commit", "-qm", "planning")
    assert only_factory(repo, base, git("rev-parse", "HEAD"))
    for path in (".software-factory/factory.lock", ".software-factory/principles.md"):
        before = git("rev-parse", "HEAD")
        (repo / path).write_text("changed\n")
        git("add", path)
        git("commit", "-qm", path)
        assert not only_factory(repo, before, git("rev-parse", "HEAD")), path

    # The harness runs only when the lock names a full commit installed on this host; the branch, which the
    # harness controls, never brings its own framework (dev_path) or a short or non-hex commit.
    installed = repo / "framework"
    for part in ("kit", "skills", "hooks"):
        (installed / ("a" * 40) / part).mkdir(parents=True)
    (installed / ("c" * 40) / "kit").mkdir(parents=True)  # incomplete: no skills/ or hooks/
    with patch.object(factory_run, "FRAMEWORK", installed):
        for lock, missing in [(None, "no .software-factory/factory.lock"),
                              ("framework: { commit: " + "c" * 40 + " }\n", "is not installed"),
                              ("framework: { commit: " + "a" * 40 + " }\nframework: { dev_path: /x }\n",
                               "has 2 framework lines"),
                              ("framework: { commit: " + "a" * 40 + ", installed: 2026-10-13 }\n", None),
                              ("framework: { commit: " + "b" * 40 + ", installed: 2026-10-13 }\n", "is not installed"),
                              ("framework: { commit: ../.., installed: 2026-10-13 }\n", "no full 40-hex"),
                              ("framework: { commit: aaaaaaa, installed: 2026-10-13 }\n", "no full 40-hex"),
                              ("framework: { commit: " + "g" * 40 + ", installed: 2026-10-13 }\n", "no full 40-hex"),
                              (f"framework: {{ dev_path: {repo} }}\n", "names a dev_path"),
                              (f"framework: {{ dev_path: {repo}/gone }}\n", "names a dev_path")]:
            if lock is None:
                git("rm", "-q", ".software-factory/factory.lock")
            else:
                (repo / ".software-factory/factory.lock").write_text(lock)
                git("add", ".software-factory/factory.lock")
            git("commit", "-qm", "lock", "--allow-empty")
            reason = missing_framework(repo, "HEAD", change)
            assert (reason is None) if missing is None else (missing in (reason or "")), (lock, reason)

    # A branch whose changes are still in .factory/ is reported, not skipped silently.
    assert not unmigrated(repo, "HEAD")
    (repo / ".factory/changes/old").mkdir(parents=True)
    (repo / ".factory/changes/old/status.yaml").write_text("branch: factory/old\n")
    git("add", ".factory")
    git("rm", "-rq", "--cached", ".software-factory/changes")
    git("commit", "-qm", "legacy")
    assert unmigrated(repo, "HEAD")

# The cache lives under HOME, so HOME must be absolute and not /.
for home, ok in [("/", False), ("relative", False), ("", False), ("/Users/someone", True)]:
    with patch.dict("os.environ", {"HOME": home}):
        assert (home_problem() is None) == ok, home

# Recording approvals must pass the pushed head to the harness and use that head for trust checks.
with tempfile.TemporaryDirectory() as tmp:
    remote = Path(tmp) / "remote.git"
    repo = Path(tmp) / "runner"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(repo)], check=True)

    def git(*args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false", "-C", str(repo), *args],
                              capture_output=True, text=True, check=True).stdout.strip()

    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    git("checkout", "-b", "factory/demo")
    git("config", "commit.gpgsign", "false")
    change = ".software-factory/changes/demo"
    status_path = f"{change}/status.yaml"
    (repo / change).mkdir(parents=True)
    (repo / status_path).write_text(STATUS.format(p=PENDING))
    (repo / change / "01-product.md").write_text("# product\n")
    (repo / ".software-factory/factory.lock").write_text("framework: { commit: " + "a" * 40 + ", installed: 2026-10-13 }\n")
    git("add", ".")
    git("commit", "-qm", "triage")
    git("push", "-u", "origin", "factory/demo")
    for part in ("kit", "skills", "hooks"):
        (Path(tmp) / "framework" / ("a" * 40) / part).mkdir(parents=True)
    before = git("rev-parse", "HEAD")
    start = {"login": "alice", "state": "APPROVED", "body": "start", "commit": before,
             "at": "2026-10-10T10:00:00Z"}
    approve = {**start, "body": "approve product"}
    heads = {}
    harness_heads = []

    def harness(repo, branch, head, cmd, setup, timeout):
        harness_heads.append(head)
        assert head != before and head == git("rev-parse", "HEAD"), head
        assert heads[branch] == head
        (repo / "code.txt").write_text("harness output\n")
        git("add", ".")
        git("commit", "-qm", "harness code")
        git("push", "origin", f"HEAD:{branch}")
        return 0, {git("rev-parse", "HEAD")}

    with patch.object(factory_run, "pull_request", return_value=([start, approve], [])), \
            patch.object(factory_run, "harness_pass", side_effect=harness), \
            patch.object(factory_run, "FRAMEWORK", Path(tmp) / "framework"):
        factory_run.pass_change(repo, "factory/demo", status_path, {"alice"}, "unused", "/{skill} {slug}", 30, heads)
    assert len(harness_heads) == 1
    assert heads["factory/demo"] == git("rev-parse", "HEAD")

    # Without the locked framework on this host, the runner records approvals but never runs the harness.
    git("rm", "-q", ".software-factory/factory.lock")
    git("commit", "-qm", "drop the lock")
    git("push", "origin", "HEAD:factory/demo")
    heads["factory/demo"] = git("rev-parse", "HEAD")
    with patch.object(factory_run, "pull_request", return_value=([start, approve], [])), \
            patch.object(factory_run, "harness_pass", side_effect=harness), \
            patch.object(factory_run, "FRAMEWORK", Path(tmp) / "framework"):
        factory_run.pass_change(repo, "factory/demo", status_path, {"alice"}, "unused", "/{skill} {slug}", 30, heads)
    assert len(harness_heads) == 1
# Failed setup never starts the harness; failed and timed-out work stays recoverable.
with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp) / "runner"
    remote = Path(tmp) / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(repo)], check=True)
    def git(*args):
        return subprocess.check_output(["git", "-c", "commit.gpgsign=false", "-C", str(repo), *args], text=True).strip()
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    git("checkout", "-b", "factory/demo")
    (repo / "code").write_text("GREEN")
    git("add", ".")
    git("commit", "-qm", "green")
    git("push", "origin", "factory/demo")
    head = git("rev-parse", "HEAD")
    calls = []
    def failing_setup(cmd, work, timeout):
        calls.append(cmd)
        (work / "code").write_text("dirty")
        (work / "untracked").write_text("recover")
        return 7
    with patch.object(factory_run, "run_harness", side_effect=failing_setup):
        code, _ = factory_run.harness_pass(repo, "factory/demo", head, ["must-not-run"], "setup", 1)
    assert code == 7 and calls == [["setup"]]
    recovery = list((repo / ".git/factory-recovery").glob("*/work"))
    assert len(recovery) == 1
    assert (recovery[0] / "code").read_text() == "dirty"
    assert (recovery[0] / "untracked").read_text() == "recover"
    assert (recovery[0] / ".git/objects").is_dir()
    with patch.object(factory_run, "run_harness", side_effect=subprocess.TimeoutExpired("harness", 1)):
        assert factory_run.harness_pass(repo, "factory/demo", head, ["timeout"], None, 1)[0] is None
    assert len(list((repo / ".git/factory-recovery").glob("*/work"))) == 2
    # Managed harness cannot publish; the runner publishes clean successful commits only.
    def successful_harness(cmd, work, timeout):
        def work_git(*args):
            return subprocess.check_output(["git", "-c", "commit.gpgsign=false", "-C", str(work), *args], text=True).strip()
        work_git("config", "user.email", "test@example.com")
        work_git("config", "user.name", "test")
        (work / "code").write_text((work / "code").read_text() + " completed")
        work_git("add", "code")
        work_git("commit", "-qm", "feat: completed step")
        attempted = subprocess.run(["git", "-C", str(work), "push", "origin", "HEAD"], capture_output=True, check=False)
        assert attempted.returncode != 0
        return 0
    with patch.object(factory_run, "run_harness", side_effect=successful_harness):
        assert factory_run.harness_pass(repo, "factory/demo", head, ["build"], None, 1)[0] == 0
    git("fetch", "origin", "factory/demo")
    assert git("show", "origin/factory/demo:code") == "GREEN completed"
    head = git("rev-parse", "origin/factory/demo")
    # A failed run retains its committed work and never publishes it.
    def failed_committed_harness(cmd, work, timeout):
        successful_harness(cmd, work, timeout)
        subprocess.run(["git", "-C", str(work), "checkout", "-q", "--detach", "HEAD"], check=True)
        (work / "pending").write_text("retain untracked after failure")
        return 3
    with patch.object(factory_run, "run_harness", side_effect=failed_committed_harness):
        assert factory_run.harness_pass(repo, "factory/demo", head, ["failed"], None, 1)[0] == 3
    git("fetch", "origin", "factory/demo")
    assert git("rev-parse", "origin/factory/demo") == head
    failed_work = [w for w in (repo / ".git/factory-recovery").glob("*/work") if (w / "pending").exists()]
    assert len(failed_work) == 1 and (failed_work[0] / ".git/HEAD").read_text().strip() != "ref: refs/heads/factory/demo"
    original_run = factory_run.run
    def clone_failure(cwd, *cmd, **kwargs):
        if cmd[:2] == ("git", "clone"):
            (cwd / "partial-clone").write_text("setup evidence")
            raise RuntimeError("clone failed")
        return original_run(cwd, *cmd, **kwargs)
    with patch.object(factory_run, "run", side_effect=clone_failure):
        try:
            factory_run.harness_pass(repo, "factory/demo", head, ["unused"], None, 1)
        except RuntimeError:
            pass
        else:
            raise AssertionError("clone failure was swallowed")
    recovery = list((repo / ".git/factory-recovery").glob("*/work"))
    assert len(recovery) == 4
    assert any((work / "partial-clone").exists() for work in recovery)

print("factory_run: all checks passed")
