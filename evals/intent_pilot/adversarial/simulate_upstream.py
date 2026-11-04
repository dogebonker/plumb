"""In-process external-source race controls; not a real vendor integration."""

import hashlib
import json
import runpy
import sys
import tempfile
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY))

from plumb import apply, propose, reconcile
from plumb.test_core import Script, response


class SourceError(Exception):
    pass


class FakeDocumentService:
    """A deliberately specified fake API, not Notion/Linear request semantics."""

    def __init__(self):
        self.version = 1
        self.body = "Retain audit records for exactly 7 days.\n"
        self.read_status = 200
        self.events = []

    def get(self):
        self.events.append({"method": "GET", "status": self.read_status})
        if self.read_status != 200:
            raise SourceError("Source unavailable: " + str(self.read_status))
        return {
            "id": "audit-policy",
            "revision": self.version,
            "body": self.body,
            "sha256": hashlib.sha256(self.body.encode()).hexdigest(),
        }

    def change(self, body):
        self.version += 1
        self.body = body

    def conditional_update(self, body, expected_revision):
        if self.version != expected_revision:
            self.events.append({"method": "PATCH", "status": 409})
            raise SourceError("Upstream changed after approval")
        self.change(body)
        self.events.append({"method": "PATCH", "status": 200})
        return self.get()


def current_source_gate(service, captured, action):
    current = service.get()
    if (current["revision"], current["sha256"]) != (
        captured["revision"],
        captured["sha256"],
    ):
        raise SourceError("Captured source is stale")
    return action()


def fixture(root, captured):
    files = {
        "code/policy.py": "retention_days = 30\n",
        "knowledge/module.md": "The selected current retention is exactly 7 days.\n",
        "sources/decision.md": captured["body"],
    }
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    inspect = response(
        "inspect", reads=[{"path": p, "start_line": 0, "end_line": 0} for p in files]
    )
    finding = response(
        outcome="code_wrong",
        explanation="Selected retention differs.",
        question="Change to the selected 7-day policy?",
        evidence=[
            {"path": "code/policy.py", "quote": "retention_days = 30"},
            {"path": "sources/decision.md", "quote": captured["body"].strip()},
        ],
    )
    report = reconcile(
        root,
        Script(inspect, finding),
        decision="Test operator selects captured audit-policy revision 1.",
    )
    edit = {
        "path": "code/policy.py",
        "old": "retention_days = 30",
        "new": "retention_days = 7",
        "reason": "Explicit controlled code correction.",
    }
    proposal = propose(
        report, "code", Script(inspect, {**finding, "question": "", "edits": [edit]})
    )
    return proposal


def actual_days(root):
    return runpy.run_path(str(root / "code/policy.py"))["retention_days"]


def main():
    results = {
        "method": "fake API + scripted model controls; no model inference/network",
        "production_connector_implemented": False,
        "cases": [],
    }
    with tempfile.TemporaryDirectory(prefix="plumb-upstream-") as temporary:
        base = Path(temporary).resolve()
        for name, guarded, changed in [
            ("stable_guarded_apply", True, False),
            ("local_core_cannot_see_remote_change", False, True),
            ("freshness_gate_rejects_remote_change", True, True),
        ]:
            service = FakeDocumentService()
            captured = service.get()
            root = base / name
            proposal = fixture(root, captured)
            if changed:
                service.change("Retain audit records for exactly 30 days.\n")
            try:
                receipt = (
                    current_source_gate(
                        service, captured, lambda proposal=proposal: apply(proposal)
                    )
                    if guarded
                    else apply(proposal)
                )
                observation = {"applied": True, "status": receipt["status"]}
            except SourceError as error:
                observation = {"applied": False, "reason": str(error)}
            assert observation["applied"] == (not guarded or not changed)
            assert actual_days(root) == (7 if observation["applied"] else 30)
            observation["outcome"] = (
                "remaining_gap"
                if changed and not guarded
                else "applied"
                if observation["applied"]
                else "blocked"
            )
            results["cases"].append(
                {
                    "name": name,
                    **observation,
                    "actual_code_days": actual_days(root),
                    "upstream_revision": service.version,
                    "events": service.events,
                }
            )

        for status in [403, 404, 429, 503]:
            service = FakeDocumentService()
            captured = service.get()
            service.read_status = status
            invoked = []
            try:
                current_source_gate(
                    service,
                    captured,
                    lambda invoked=invoked: invoked.append("apply-or-model"),
                )
            except SourceError as error:
                reason = str(error)
            else:
                raise AssertionError("Unavailable source was accepted")
            assert invoked == []
            results["cases"].append(
                {
                    "name": "read_failure_" + str(status),
                    "action_invocations": len(invoked),
                    "outcome": "blocked",
                    "reason": reason,
                    "events": service.events,
                }
            )

        service = FakeDocumentService()
        approved = service.get()
        service.change("Another maintainer's newer policy.\n")
        newer = service.body
        try:
            service.conditional_update(
                "Proposed document correction.\n", approved["revision"]
            )
        except SourceError:
            pass
        else:
            raise AssertionError("Stale writeback overwrote new upstream text")
        assert service.body == newer
        results["cases"].append(
            {
                "name": "writeback_after_approval_race",
                "outcome": "blocked",
                "newer_document_preserved": True,
                "events": service.events,
            }
        )

        service = FakeDocumentService()
        approved = service.get()
        receipt = service.conditional_update(
            "Explicitly revised current policy.\n", approved["revision"]
        )
        assert (
            receipt["revision"] == 2
            and service.body == "Explicitly revised current policy.\n"
        )
        results["cases"].append(
            {
                "name": "fresh_conditional_writeback",
                "outcome": "updated",
                "revision": receipt["revision"],
                "events": service.events,
            }
        )

        service = FakeDocumentService()
        captured = service.get()
        root = base / "check_then_change"
        proposal = fixture(root, captured)

        def change_after_check():
            service.change("Retain audit records for exactly 30 days.\n")
            return apply(proposal)

        current_source_gate(service, captured, change_after_check)
        assert actual_days(root) == 7 and "30 days" in service.body
        results["cases"].append(
            {
                "name": "check_then_remote_change_race",
                "outcome": "remaining_gap",
                "actual_code_days": actual_days(root),
                "current_remote_days": 30,
                "meaning": "A freshness read cannot make a later local edit atomic with remote policy changes.",
            }
        )
    output = Path(__file__).with_name("upstream-results.json")
    output.write_text(json.dumps(results, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(results["cases"]),
                "expected_controls_verified": True,
                "remaining_gaps": [
                    row["name"]
                    for row in results["cases"]
                    if row.get("outcome") == "remaining_gap"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
