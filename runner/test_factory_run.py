"""Run: python3 runner/test_factory_run.py"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

from factory_run import command, next_skill, record, set_scalar

STATUS = """feature: demo
branch: factory/demo
mode: headless
approvers: [alice]
waiting_since: null
gates:
  product:      {{ state: {p}, approved_by: null, approved_at: null, doc_sha256: null }}
  architecture: {{ state: {a}, approved_by: null, approved_at: null, doc_sha256: null }}
  interface:    {{ state: {i}, approved_by: null, approved_at: null, doc_sha256: null }}
  slices:       {{ state: {s}, approved_by: null, approved_at: null, doc_sha256: null }}
slices:
{slices}
reconciled: {r}
"""


def status(p="pending", a="pending", i="pending", s="pending", slices="", r="false"):
    return STATUS.format(p=p, a=a, i=i, s=s, slices=slices, r=r)


# Commands are the first line of an approver's review.
assert command("approve product\nlooks good") == ("approve", "product")
assert command("Sign off slice 01") == ("sign-off", "01")
assert command("please approve product") is None

# The next skill follows the gates, then the slices, then reconcile.
assert next_skill(status()) == "factory-product"
assert next_skill(status(p="skipped", a="skipped", i="skipped")) == "factory-slices"
done = {"p": "approved", "a": "approved", "i": "approved", "s": "approved"}
assert next_skill(status(**done, slices="  - { id: 1, name: t, state: pending }")) == "factory-build"
assert next_skill(status(**done, slices="  - { id: 1, name: t, state: green, head_commit: abc }")) == "factory-review"
assert next_skill(status(**done, slices="  - { id: 1, name: t, state: done }")) == "factory-reconcile"
assert next_skill(status(**done, slices="  - { id: 1, name: t, state: done }", r="true")) is None
assert "waiting_since: 2026" in set_scalar(status(), "waiting_since", "2026-10-10T10:00:00Z")

with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)

    def git(*args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false", "-C", str(repo), *args],
                              capture_output=True, text=True, check=True).stdout.strip()

    git("init", "-q", "-b", "factory/demo")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    change = repo / ".factory" / "changes" / "demo"
    change.mkdir(parents=True)
    (change / "01-product.md").write_text("# product v1\n")
    git("add", ".")
    git("commit", "-qm", "v1")
    v1 = git("rev-parse", "HEAD")
    digest = hashlib.sha256(b"# product v1\n").hexdigest()

    # An approval at the commit holding the current document is recorded.
    text, recorded = record(repo, change, status(), [
        {"login": "alice", "body": "approve product", "commit_id": v1, "submitted_at": "2026-10-10T10:00:00Z"}])
    assert recorded == ["product approved by alice"], recorded
    assert f"doc_sha256: {digest}" in text and "approved_by: alice" in text

    # An approval of an older version of the document is not.
    (change / "01-product.md").write_text("# product v2\n")
    git("commit", "-qam", "v2")
    _, recorded = record(repo, change, status(), [
        {"login": "alice", "body": "approve product", "commit_id": v1, "submitted_at": "2026-10-10T10:00:00Z"}])
    assert recorded == [], recorded

    # Approving a later gate before an earlier one does nothing.
    _, recorded = record(repo, change, status(), [
        {"login": "alice", "body": "approve slices", "commit_id": v1, "submitted_at": "2026-10-10T10:00:00Z"}])
    assert recorded == []

    # A sign-off at or after the slice's head commit, with review.md written, finishes the slice.
    (change / "slices" / "01").mkdir(parents=True)
    (change / "slices" / "01" / "review.md").write_text("# Review\n\n## Sign-off\n<name>, <ISO time>\n")
    git("add", ".")
    git("commit", "-qm", "review")
    head = git("rev-parse", "HEAD")
    green = status(**done, slices=f"  - {{ id: 1, name: t, state: green, head_commit: {v1} }}")
    text, recorded = record(repo, change, green, [
        {"login": "alice", "body": "sign off slice 01", "commit_id": head, "submitted_at": "2026-10-10T11:00:00Z"}])
    assert recorded == ["slice 01 signed off by alice"], recorded
    assert "state: done" in text
    assert "alice, 2026-10-10T11:00:00Z" in (change / "slices" / "01" / "review.md").read_text()

print("factory_run: all checks passed")
