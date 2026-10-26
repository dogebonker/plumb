"""Turn a fresh ACC-01 setup into the ideal end of /plumb-reconcile when the user calls FR-02 a defect.

It starts the product, tries the three examples over HTTP, writes acceptance.md from the responses and sends the
change back. Usage: python3 apply.py <workspace>.
"""

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stagelib import change_dir, commit, event, flow, git, pending_gate, workspace_arg, write  # noqa: E402

REASON = "acceptance: FR-02"


def call(url, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    with urlopen(Request(url + path, data=data, method=method), timeout=5) as response:
        return f"{method} {path} -> {response.status} {response.read().decode()}"


def try_examples(workspace):
    """Run dev_command, try each example, and return the three evidence lines."""
    lenses = (workspace / ".plumb/system/lenses.yaml").read_text()
    command = re.search(r'dev_command: "(.*)"', lenses).group(1)
    url = re.search(r'dev_url: "(.*)"', lenses).group(1)
    server = subprocess.Popen(command.split(), cwd=workspace, start_new_session=True,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                urlopen(url + "/notes", timeout=1).close()
                break
            except OSError:
                time.sleep(0.1)
        fr1 = call(url, "POST", "/notes", {"title": "milk"})
        call(url, "POST", "/notes", {"title": "eggs"})
        fr3 = call(url, "POST", "/notes/1/archive")
        fr2 = call(url, "GET", "/notes?archived=true")
    finally:
        os.killpg(server.pid, signal.SIGTERM)
        server.wait()
    return url, fr1, fr2 + "; eggs is not archived but is listed", fr3


def record(workspace, url, fr1, fr2, fr3):
    change = change_dir(workspace, "acc01")
    write(change / "acceptance.md", f"""Tried at: {git(workspace, "rev-parse", "HEAD")}

| ID | Surface | Result | Evidence | Answer |
| --- | --- | --- | --- | --- |
| FR-01 | {url} | pass | {fr1} | |
| FR-02 | {url} | fail | {fr2} | defect |
| FR-03 | {url} | pass | {fr3} | |
""")
    slices_doc = change / "04-slices.md"
    write(slices_doc, slices_doc.read_text().rstrip("\n") + f"\n- {REASON}: GET /notes?archived=true returns every note.\n")
    status = change / "status.yaml"
    text = re.sub(r"^(  slices:\s+)\{.*\}$", lambda m: m.group(1) + flow(pending_gate()), status.read_text(), flags=re.M)
    text = text.replace("sent_back: null", "sent_back: " + flow({"gate": "slices", "slice": None, "reason": REASON}))
    text = text.replace("All slices done. Next: /plumb-reconcile", "Sent back to slices. Next: /plumb-slices")
    text += f"  - {flow(event(40, 'plumb-reconcile', 'step_start'))}\n"
    text += f"  - {flow(event(41, 'plumb-reconcile', 'sent_back', '-', 'slices: ' + REASON))}\n"
    write(status, text)
    commit(workspace, "chore(plumb): send back acc01 to slices", ".plumb")


if __name__ == "__main__":
    workspace = workspace_arg()
    record(workspace, *try_examples(workspace))
