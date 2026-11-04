"""Behavior checks against prewritten synthetic maintainer policies; no inference.

Run: python3 .../verify_resolution.py --csv COPY --event COPY --output RESULT.json
Loads actual fixture source in a temporary Python module namespace. The event bus
and archive are test doubles, not live services or proof of distributed delivery.
"""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

BASE = Path(__file__).resolve().parent


@contextmanager
def modules(root, names):
    saved = {key: value for key, value in sys.modules.items() if key == "code" or key.startswith("code.")}
    for key in list(saved):
        del sys.modules[key]
    try:
        for name in names:
            parts = name.split(".")
            for i in range(1, len(parts)):
                package = ".".join(parts[:i])
                if package not in sys.modules:
                    module = ModuleType(package)
                    module.__path__ = [str(root.joinpath(*parts[:i]))]
                    sys.modules[package] = module
            spec = importlib.util.spec_from_file_location(name, root.joinpath(*parts).with_suffix(".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        yield [sys.modules[name] for name in names]
    finally:
        for key in list(sys.modules):
            if key == "code" or key.startswith("code."):
                del sys.modules[key]
        sys.modules.update(saved)


def sources_unchanged(case, root):
    original = BASE / case / "workspace"
    files = list((original / "sources").glob("*.md"))
    assert {p.name for p in files} == {p.name for p in (root / "sources").glob("*.md")}
    for source in files:
        assert source.read_bytes() == (root / "sources" / source.name).read_bytes(), source.name


def csv(root):
    with modules(root, ["code.billing.csv_writer", "code.api.export"]) as (_, api):
        invoice = SimpleNamespace(id="inv-7", customer_email="private@example.test", total_cents=1234)
        output = api.export_invoices(SimpleNamespace(can_export_billing=True), [invoice])
        assert output == "invoice_id,total_cents\ninv-7,1234", output
        assert "email" not in output and invoice.customer_email not in output
        try:
            # None raises if the serializer runs: permission must deny before iteration.
            api.export_invoices(SimpleNamespace(can_export_billing=False), None)
        except PermissionError:
            pass
        else:
            raise AssertionError("Unauthorized export was accepted")
    sources_unchanged("csv_boundary", root)
    text = (root / "knowledge/billing-export.md").read_text()
    assert "sources/linear-privacy.md" in text and "sources/notion-export.md" in text
    return ["authorized CSV contains only invoice id and exact cents", "unauthorized actor denied before serializer",
            "source captures unchanged", "OKF references governing and superseded decisions"]


def event(root):
    with modules(root, ["code.events.publisher", "code.accounts.close", "code.audit.consumer"]) as (_, accounts, consumer):
        class Bus:
            def __init__(self):
                self.events = []

            def publish(self, topic, payload):
                self.events.append((topic, payload))

        class Archive:
            def __init__(self):
                self.records = []

            def append(self, account_id, *, retention_days):
                self.records.append((account_id, retention_days))

        bus, archive = Bus(), Archive()
        account = SimpleNamespace(id="acct-4", closed=False)
        accounts.close_account(SimpleNamespace(account_id="acct-4", can_close_account=True), account, bus)
        assert account.closed
        assert bus.events == [("account.closed.v1", {"account_id": "acct-4"})], bus.events
        for topic, payload in bus.events:
            assert topic == consumer.TOPIC
            consumer.consume_closed(payload, archive)
        assert archive.records == [("acct-4", 7)], archive.records
        for actor in (SimpleNamespace(account_id="other", can_close_account=True),
                      SimpleNamespace(account_id="acct-4", can_close_account=False)):
            denied_bus = Bus()
            denied_account = SimpleNamespace(id="acct-4", closed=False)
            try:
                accounts.close_account(actor, denied_account, denied_bus)
            except PermissionError:
                pass
            else:
                raise AssertionError("Unauthorized closure was accepted")
            assert not denied_account.closed and not denied_bus.events
    sources_unchanged("event_boundary", root)
    text = (root / "knowledge/account-closure.md").read_text()
    assert "sources/linear-legal.md" in text and "sources/confluence-retention.md" in text
    return ["authorized close emits v1 account_id-only payload", "topic routes to actual audit consumer",
            "archive receives exactly seven-day retention", "wrong owner and missing permission deny before state/event",
            "source captures unchanged", "OKF references governing and superseded decisions"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--event", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    results = {"method": "actual synthetic source execution, prewritten maintainer policy; stdlib test doubles"}
    for name, path, verify in (("csv", args.csv, csv), ("event", args.event, event)):
        if path:
            try:
                results[name] = {"pass": True, "checks": verify(path.resolve())}
            except (AssertionError, OSError) as error:
                results[name] = {"pass": False, "error": str(error)}
    assert args.csv or args.event, "Select at least one resolved workspace"
    text = json.dumps(results, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if all(v["pass"] for v in results.values() if isinstance(v, dict)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
