#!/usr/bin/env python3
"""GitHub Actions history for factory-ci, read-only.

  python3 ci_runs.py fetch <owner/repo> <out> [--days 30]
  python3 ci_runs.py analyze <out> [--since <date or ISO time>]

fetch writes <out>/data.json with gh api GET calls only. analyze writes <out>/summary.json.
Why this method: docs/research/ci-selection.md (CI-2) in the factory repository.
"""
import argparse
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

GH_ENV = {**os.environ, "GH_TELEMETRY": "false", "GH_NO_UPDATE_NOTIFIER": "1", "GH_PROMPT_DISABLED": "1"}
RUN = "{id, name, event, head_branch, head_sha, run_attempt, status, conclusion, created_at}"
JOB = ("{name, run_attempt, created_at, started_at, completed_at, conclusion, labels, runner_name,"
       " steps: [.steps[]? | {name, started_at, completed_at, conclusion}]}")
# USD per minute for GitHub's standard labels, https://docs.github.com/en/billing/reference/actions-runner-pricing,
# read 2026-10-11. Self-hosted is free. Any other label is unpriced: a larger runner's own name, or a standard
# label with no published price (windows-11-arm).
PRICES = [(r"ubuntu-slim", 0.002), (r"ubuntu-(latest|\d\d\.\d\d)-arm", 0.005), (r"ubuntu-(latest|\d\d\.\d\d)", 0.006),
          (r"windows-(latest|\d{4})", 0.010), (r"macos-(latest|\d+)-xlarge", 0.102), (r"macos-(latest|\d+)-large", 0.077),
          (r"macos-(latest|\d+)(-intel)?", 0.062)]
GREEN = {"success", "skipped", "neutral"}
RED = {"failure", "timed_out", "startup_failure"}
SLICE_CAP = 1000  # GitHub returns at most 1,000 runs per filtered query
WORKERS = 6  # well under GitHub's secondary limit of 900 GETs a minute


class GhError(Exception):
    pass


def gh(path, jq, paginate=True):
    cmd = ["gh", "api", *(["--paginate"] if paginate else []), path, "--jq", f"({jq}) | tojson"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=GH_ENV, check=False)
    if r.returncode:
        raise GhError(f"{path}: {r.stderr.strip()}")
    return [json.loads(line) for line in r.stdout.splitlines() if line.strip()]


def ts(s):  # Python 3.10 parses only whole seconds or exactly 6 fractional digits; the API sends 0 to 9
    return datetime.fromisoformat(re.sub(r"\.(\d+)", lambda m: "." + m[1][:6].ljust(6, "0"), s.replace("Z", "+00:00")))


def secs(a, b):
    return (ts(b) - ts(a)).total_seconds()


def fetch(repo, out, days):
    calls, notes = 0, []

    def call(path, jq, paginate=True):  # main thread only; pooled pulls are counted where they run
        nonlocal calls
        calls += 1
        return gh(path, jq, paginate)

    def pooled(fn, items):
        with ThreadPoolExecutor(WORKERS) as pool:
            return list(pool.map(fn, items))

    try:
        meta = call(f"repos/{repo}", "{full_name, private, default_branch}")[0]
    except GhError as e:
        sys.exit(f"cannot read {repo} with the active gh account ({e}). "
                 "Ask the user to make an account with access active; never switch accounts yourself.")
    branch = meta["default_branch"]
    required, strict = set(), None
    try:
        required.update(*call(f"repos/{repo}/branches/{quote(branch, safe='')}",
                              "(.protection.required_status_checks // {}) | [.checks[]?.context] + (.contexts // [])"))
    except GhError as e:
        notes.append(f"branch protection unreadable: {e}")
    try:
        for page in call(f"repos/{repo}/rules/branches/{quote(branch, safe='')}",
                         '[.[] | select(.type == "required_status_checks") | .parameters]'
                         " | {contexts: [.[].required_status_checks[].context],"
                         " strict: any(.[]; .strict_required_status_checks_policy == true)}"):
            required.update(page["contexts"])
            strict = bool(strict) or page["strict"]
    except GhError as e:
        notes.append(f"rulesets unreadable: {e}")

    workflows = call(f"repos/{repo}/actions/workflows?per_page=100", '.workflows[] | select(.state == "active") | {id, name}')

    def last_green(w):
        try:
            # a fork's pull request from its own default branch also matches branch=, so check event and repository
            got = gh(f"repos/{repo}/actions/workflows/{w['id']}/runs?branch={quote(branch, safe='')}"
                     "&status=success&per_page=30", "[.workflow_runs[] | select(.head_repository.full_name == "
                     f'{json.dumps(repo)} and (.event | IN("push", "schedule", "workflow_dispatch")))][0].created_at'
                     " // empty", paginate=False)
        except GhError:
            return "unreadable"
        return got[0] if got else None

    greens = dict(zip((w["name"] for w in workflows), pooled(last_green, workflows), strict=True))
    calls += len(workflows)

    today = datetime.now(timezone.utc).date()
    runs = {}
    for d in range(days):
        day = (today - timedelta(days=d)).isoformat()
        got = call(f"repos/{repo}/actions/runs?per_page=100&created={day}", f".workflow_runs[] | {RUN}")
        if len(got) >= SLICE_CAP:  # ponytail: day slices only; split by hour if a repository ever hits this
            notes.append(f"{day}: {len(got)} runs, capped by GitHub at {SLICE_CAP}; that day is incomplete")
        runs.update((r["id"], r) for r in got)  # a run can appear on two pages while new runs arrive
    runs = [r for r in runs.values() if r["status"] == "completed"]
    need_jobs = [r for r in runs if r["conclusion"] not in ("action_required", "skipped")]

    def jobs(r):
        try:
            return gh(f"repos/{repo}/actions/runs/{r['id']}/jobs?filter=all&per_page=100", f".jobs[] | {JOB}")
        except GhError as e:
            return str(e)

    for r, js in zip(need_jobs, pooled(jobs, need_jobs), strict=True):
        r["jobs"] = js if isinstance(js, list) else []
        if not isinstance(js, list):
            notes.append(f"run {r['id']}: jobs unreadable: {js}")
    calls += len(need_jobs)
    try:
        caches = call(f"repos/{repo}/actions/caches?per_page=100",
                      ".actions_caches[] | {ref, size_in_bytes, created_at, last_accessed_at}")
    except GhError as e:
        caches = None
        notes.append(f"caches unreadable: {e}")
    data = {"repo": meta, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "gh_invocations": calls, "required": sorted(required), "up_to_date_required_by_ruleset": strict,
            "last_green": greens, "notes": notes, "runs": runs, "caches": caches}
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "data.json"), "w") as f:
        json.dump(data, f)
    print(f"{repo}: {len(runs)} completed runs, {calls} gh invocations, {len(notes)} notes")


def quantile(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, math.ceil(q * len(xs)) - 1)] if xs else None


def dist(xs, unit=60):
    if not xs:
        return {"n": 0}
    out = {"n": len(xs), "median": round(statistics.median(xs) / unit, 2),
           "mean": round(statistics.fmean(xs) / unit, 2), "max": round(max(xs) / unit, 2)}
    out["p90"] = round(quantile(xs, 0.9) / unit, 2) if len(xs) >= 30 else None  # unstable below 30 runs
    return out


def noise_floor(xs, rounds=2000, seed=1):
    """95th percentile of the relative gap between medians of two random groups of unchanged history."""
    k = min(20, len(xs) // 2)
    if k < 5:
        return None
    rng, base, gaps = random.Random(seed), statistics.median(xs), []
    for _ in range(rounds):
        s = rng.sample(xs, 2 * k)
        gaps.append(abs(statistics.median(s[:k]) - statistics.median(s[k:])) / base if base else 0.0)
    return {"runs_per_side": k, "pct": round(100 * quantile(gaps, 0.95), 1)}


def ran(job):
    """A job that held a runner. A re-run copies jobs that already passed with a new created_at and the old
    start: those copies, skipped jobs and jobs cancelled before a runner took them did not run."""
    return (job["conclusion"] != "skipped" and bool(job.get("runner_name")) and job["started_at"] is not None
            and job["completed_at"] is not None and secs(job["created_at"], job["started_at"]) >= 0
            and secs(job["started_at"], job["completed_at"]) >= 0)


def label(job):
    return ",".join(sorted(job["labels"])) or "unknown"


def price(job):
    labels = [x.lower() for x in job["labels"]]
    if "self-hosted" in labels:
        return 0.0
    return next((usd for pat, usd in PRICES for x in labels if re.fullmatch(pat, x)), None)


def critical_path(jobs, required=()):
    """From the last required job to finish (or the last job), back through the job that unblocked each one."""
    jobs = sorted(jobs, key=lambda j: j["completed_at"])
    gates = [j for j in jobs if j["name"] in required]
    cur = (gates or jobs)[-1]
    path = [cur]
    while True:
        before = [j for j in jobs if j["completed_at"] < cur["completed_at"]
                  and secs(j["completed_at"], cur["created_at"]) >= -2]
        if not before:
            return [j["name"] for j in reversed(path)]
        cur = before[-1]
        path.append(cur)


def analyze(out, since=None):
    with open(os.path.join(out, "data.json")) as f:
        data = json.load(f)
    runs = [r for r in data["runs"] if not since or r["created_at"] >= since]
    required = set(data["required"])
    minutes, dollars, unpriced = Counter(), Counter(), set()
    queue, strata = defaultdict(list), defaultdict(list)
    for r in runs:
        jobs = [j for j in r.get("jobs", []) if ran(j)]
        for j in jobs:
            d = secs(j["started_at"], j["completed_at"])
            redone = any(k["name"] == j["name"] and k["run_attempt"] > j["run_attempt"] for k in jobs)
            bucket = "earlier attempts" if redone else r["conclusion"]
            minutes[bucket] += d / 60
            usd = price(j)
            if usd is None:
                unpriced.add(label(j))
            else:
                dollars[bucket] += math.ceil(d / 60) * usd
            queue[label(j)].append(secs(j["created_at"], j["started_at"]))
        if jobs and r["conclusion"] == "success" and r["run_attempt"] == 1:
            key = (r["name"], r["event"], tuple(sorted({j["name"] for j in jobs})), tuple(sorted({label(j) for j in jobs})))
            strata[key].append(jobs)
    summary = {"repo": data["repo"]["full_name"], "private": data["repo"]["private"], "fetched_at": data["fetched_at"],
               "since": since, "window": [min((r["created_at"] for r in runs), default=None),
                                          max((r["created_at"] for r in runs), default=None)],
               "gh_invocations": data["gh_invocations"], "notes": data["notes"], "runs": len(runs),
               "health": health(runs, data["repo"]["default_branch"], data["last_green"]),
               "up_to_date_required_by_ruleset": data["up_to_date_required_by_ruleset"],
               "runner_minutes_by_outcome": {k: round(v) for k, v in minutes.most_common()},
               "usd_by_outcome": {k: round(v, 2) for k, v in dollars.most_common()},
               "usd_note": ("billed rates with per-job round-up" if data["repo"]["private"] else
                            "public repository: standard runners are free; amounts are what a private one would pay")
                           + "; self-hosted shown as 0 (GitHub's announced per-minute fee is postponed)",
               "unpriced_labels": sorted(unpriced),
               "queue_seconds_by_label": {k: dist(v, 1) for k, v in sorted(queue.items())},
               "strata": [stratum(k, v, required) for k, v in sorted(strata.items(), key=lambda kv: -len(kv[1]))
                          if len(v) >= 3],
               "per_pr_commit": per_pr_commit(runs, sorted(required)),
               "caches": caches(data["caches"], data["fetched_at"])}
    path = os.path.join(out, "summary.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=1)
    print(f"{path}: {len(runs)} runs, {len(summary['strata'])} strata of 3 or more runs")


def health(runs, branch, last_green):
    """Per workflow: outcomes in the window, the last green run on the default branch (any age), and the current
    failure streak there."""
    out = {}
    for name in sorted({r["name"] for r in runs} | set(last_green)):
        rs = sorted((r for r in runs if r["name"] == name), key=lambda r: r["created_at"], reverse=True)
        streak = 0
        for r in rs:  # newest first; cancelled and skipped runs neither break nor extend it
            if r["head_branch"] != branch or r["event"] not in ("push", "schedule", "workflow_dispatch"):
                continue
            if r["conclusion"] == "success":
                break
            streak += r["conclusion"] in RED
        out[name] = {"outcomes": dict(Counter(r["conclusion"] for r in rs)),
                     "last_green_on_default_branch": last_green.get(name), "default_branch_failure_streak": streak}
    return out


def stratum(key, items, required):
    name, event, jobs, labels = key
    walls = [secs(min(j["created_at"] for j in fs), max(j["completed_at"] for j in fs)) for fs in items]
    paths = Counter(tuple(critical_path(fs, required)) for fs in items)
    top = paths.most_common(1)[0][0]
    per_job = {}
    for jn in jobs:
        durs, steps = [], defaultdict(list)
        for fs in items:
            for j in fs:
                if j["name"] == jn:
                    durs.append(secs(j["started_at"], j["completed_at"]))
                    for s in j["steps"]:
                        if s["started_at"] and s["completed_at"] and s["conclusion"] != "skipped":
                            steps[s["name"]].append(secs(s["started_at"], s["completed_at"]))
        slow = sorted(steps.items(), key=lambda kv: -statistics.median(kv[1]))[:3]
        per_job[jn] = {"duration": dist(durs), "noise_floor": noise_floor(durs),
                       "slowest_steps": {s: dist(v) for s, v in slow}}
    return {"workflow": name, "event": event, "labels": list(labels),
            "first": min(min(j["created_at"] for j in fs) for fs in items),
            "last": max(min(j["created_at"] for j in fs) for fs in items),
            "wall": dist(walls), "noise_floor": noise_floor(walls),
            "runner_minutes_per_run": dist([sum(secs(j["started_at"], j["completed_at"]) for j in fs) for fs in items]),
            "sample": "ok" if len(items) >= 20 else "insufficient: report, do not rank",
            "critical_path": {"jobs": list(top), "share": round(paths[top] / len(items), 2),
                              "ends_at": "a required check" if required & set(top) else "the last job"},
            "jobs": per_job}


def per_pr_commit(runs, required):
    """Per pull-request head commit: wait from its first run to its last required check green (Actions jobs
    only), and the runner minutes it used."""
    names = {j["name"] for r in runs for j in r.get("jobs", [])}
    actions = [c for c in required if c in names]
    by_sha = defaultdict(list)
    for r in runs:
        if r["event"].startswith("pull_request"):
            by_sha[r["head_sha"]].append(r)
    waits, used = [], []
    for rs in by_sha.values():
        latest = {}
        for r in rs:
            for j in r.get("jobs", []):
                if j["run_attempt"] == r["run_attempt"] and j["completed_at"]:
                    latest[j["name"]] = max(latest.get(j["name"], ("", "")), (j["completed_at"], j["conclusion"]))
        want = actions or list(latest)
        if want and all(c in latest and latest[c][1] in GREEN for c in want):
            waits.append(secs(min(r["created_at"] for r in rs), max(latest[c][0] for c in want)))
        spent = sum(secs(j["started_at"], j["completed_at"]) for r in rs for j in r.get("jobs", []) if ran(j))
        if spent:
            used.append(spent)
    return {"basis": "required checks run by Actions" if actions else
            "no required check found among Actions jobs: until every PR job was green",
            "not_measured": [c for c in required if c not in names],
            "wait_to_green": {**dist(waits), "noise_floor": noise_floor(waits)},
            "runner_minutes": {**dist(used), "noise_floor": noise_floor(used)}}


def caches(entries, fetched_at):
    """never_restored: entries over a day old that were never read after they were written."""
    if entries is None:
        return None
    unused = [e for e in entries if e["created_at"] == e["last_accessed_at"] and secs(e["created_at"], fetched_at) > 86400]
    return {"count": len(entries), "gb": round(sum(e["size_in_bytes"] for e in entries) / 1e9, 2),
            "on_pull_refs": sum(e["ref"].startswith("refs/pull/") for e in entries),
            "never_restored": len(unused), "never_restored_gb": round(sum(e["size_in_bytes"] for e in unused) / 1e9, 2)}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("repo")
    f.add_argument("out")
    f.add_argument("--days", type=int, default=30)
    a = sub.add_parser("analyze")
    a.add_argument("out")
    a.add_argument("--since")
    args = p.parse_args()
    if args.cmd == "fetch":
        fetch(args.repo, args.out, args.days)
    else:
        analyze(args.out, args.since)


if __name__ == "__main__":
    main()
