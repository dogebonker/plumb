"""Run: python3 kit/ci/test_ci_runs.py"""
import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ci_runs import analyze, critical_path, dist, health, noise_floor, price, ran, secs


def t(sec):
    return f"2026-10-01T{sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}Z"


def job(name, created, started, completed, attempt=1, conclusion="success", labels=("ubuntu-latest",), runner="r1"):
    return {"name": name, "run_attempt": attempt, "created_at": t(created), "started_at": t(started),
            "completed_at": t(completed), "conclusion": conclusion, "labels": list(labels), "runner_name": runner,
            "steps": [{"name": "Test", "started_at": t(started), "completed_at": t(completed), "conclusion": "success"}]}


def run(rid, jobs, attempt=1, conclusion="success", event="pull_request", branch="feature", sha="abc", created=0,
        name="CI", wid=1):
    return {"id": rid, "name": name, "workflow_id": wid, "event": event, "head_branch": branch, "head_sha": sha, "run_attempt": attempt,
            "status": "completed", "conclusion": conclusion, "created_at": t(created), "jobs": jobs}


def summary(runs, required=("build", "test", "external/app"), cache_list=None):
    data = {"repo": {"full_name": "o/r", "private": True, "default_branch": "main"}, "fetched_at": "2026-10-03T00:00:00Z",
            "gh_invocations": 1, "required": list(required), "up_to_date_required_by_ruleset": None,
            "last_green": {"CI": t(0)}, "workflows": {"1": "CI", "7": "Dependabot Updates"}, "notes": [], "runs": runs, "caches": cache_list}
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "data.json").write_text(json.dumps(data))
        with redirect_stdout(StringIO()):
            analyze(tmp)
        return json.loads((Path(tmp) / "summary.json").read_text())


# The path walks back through the job that unblocked each one; with required checks it ends at the last of them.
build, test_, lint = job("build", 0, 3, 60), job("test", 61, 64, 180), job("lint", 0, 2, 200)
assert critical_path([build, test_, lint]) == ["lint"]
assert critical_path([build, test_, lint], {"build", "test"}) == ["build", "test"]

assert secs("2026-10-09T16:33:12.5Z", "2026-10-09T16:33:13.123456700Z") == 0.623456

# Jobs that never held a runner: skipped, cancelled before a runner took them, and a re-run's copy of a passed job.
assert not ran(job("docs", 0, 50, 10, conclusion="skipped"))
assert not ran(job("mac", 0, 0, 9, conclusion="cancelled", runner=""))
assert not ran(job("build", 900, 3, 60, attempt=2))

for labels, usd in {("ubuntu-latest",): 0.006, ("ubuntu-24.04-arm",): 0.005, ("windows-2025",): 0.010,
                    ("macos-15-xlarge",): 0.102, ("macos-latest",): 0.062, ("self-hosted", "linux"): 0.0,
                    ("ubuntu-latest-8-cores",): None, ("windows-11-arm",): None}.items():
    assert price(job("a", 0, 0, 1, labels=labels)) == usd, labels

assert dist([60.0] * 29)["p90"] is None and dist([60.0] * 30)["p90"] == 1.0
assert noise_floor([5.0] * 9) is None and noise_floor([5.0] * 40) == {"runs_per_side": 20, "pct": 0.0}

# Newest first: failure, cancelled, failure, a PR run (other branch), then success ends the streak at two.
main = [run(i, [], conclusion=c, event=e, branch=b, created=10 - i) for i, (c, e, b) in enumerate(
    [("failure", "push", "main"), ("cancelled", "push", "main"), ("failure", "push", "main"),
     ("success", "pull_request", "feature"), ("success", "push", "main"), ("failure", "push", "main")])]
h = health(main, "main", {"CI": t(4), "Deploy": None})
assert h["CI"]["default_branch_failure_streak"] == 2 and h["Deploy"] == {
    "outcomes": {}, "last_green_on_default_branch": None, "default_branch_failure_streak": 0}

# Run 1: "re-run failed jobs". Attempt 1 ran build (passed) and test (failed); attempt 2 copied build and re-ran test.
rerun = run(1, [job("build", 0, 3, 60), job("test", 61, 64, 94, conclusion="failure"),
                job("build", 900, 3, 60, attempt=2), job("test", 900, 903, 1020, attempt=2)], attempt=2)
clean = [run(i, [job("build", 0, 3, 60), job("test", 61, 64, 180)], sha=f"s{i}") for i in range(2, 6)]
later_red = run(6, [job("build", 0, 3, 60), job("test", 61, 64, 300, conclusion="failure")],
                conclusion="failure", sha="s2", created=1)
bump = run(7, [], event="dynamic", name="npm in /web - Update #123", wid=7)
s = summary([rerun, *clean, later_red, bump], cache_list=[
    {"ref": "refs/pull/1/merge", "size_in_bytes": 2e9, "created_at": t(0), "last_accessed_at": t(0)},
    {"ref": "refs/heads/main", "size_in_bytes": 1e9, "created_at": t(5), "last_accessed_at": t(65)},
    {"ref": "refs/heads/main", "size_in_bytes": 4e9, "created_at": "2026-10-02T12:00:00Z",
     "last_accessed_at": "2026-10-02T12:00:00Z"}])  # unread, but less than a day old

# Success: build 57 s once (its copy is not counted) + re-run test 117 s, and four clean runs of 173 s = 866 s.
# Failure: the red run, 57 + 236 s. Earlier attempts: the failed first test, 30 s.
assert s["runner_minutes_by_outcome"] == {"success": 14, "failure": 5, "earlier attempts": 0}, s["runner_minutes_by_outcome"]
assert s["usd_by_outcome"]["earlier attempts"] == 0.01  # 30 s bills as one minute, $0.006
assert s["queue_seconds_by_label"]["ubuntu-latest"]["n"] == 13  # 3 real jobs in the re-run, 2 in each of the other five
stratum = s["strata"][0]
assert stratum["wall"]["n"] == 4 and stratum["wall"]["median"] == 3.0  # re-run and red runs stay out
assert stratum["critical_path"] == {"jobs": ["build", "test"], "share": 1.0, "ends_at": "a required check"}
assert stratum["queue_share_of_wall"] == 0.03  # 3 s + 3 s of queue on the path over 180 s
assert stratum["jobs"]["test"]["queue_seconds"]["median"] == 3.0
assert stratum["jobs"]["test"]["duration"]["median"] == 1.93 and stratum["sample"].startswith("insufficient")
pr = s["per_pr_commit"]
assert pr["not_measured"] == ["external/app"]
assert pr["wait_to_green"]["n"] == 4  # s2 went red later, so only abc, s3, s4, s5 count
assert s["caches"] == {"count": 3, "gb": 7.0, "on_pull_refs": 1, "never_restored": 1, "never_restored_gb": 2.0}
assert s["health"]["CI"]["last_green_on_default_branch"] == t(0)
assert s["health"]["Dependabot Updates"]["outcomes"] == {"success": 1}  # one entry, not one per update title
print("ci_runs: all checks passed")
