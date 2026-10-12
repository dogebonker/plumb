"""Grade an ACC-01 workspace: python3 grade.py <workspace>. Prints one JSON line."""

import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import change_dir, flow_field, read_status, report, workspace_arg  # noqa: E402

VERDICT = re.compile(r"(did not pass|not run|pass(?:ed|es)?|fail(?:ed|s|ure)?)\b", re.I)
SURFACE = re.compile(r"://|localhost|127\.0\.0\.1|\[::1\]|^(via|on|at|http|api|surface)$", re.I)


def verdict(text):
    match = VERDICT.match(text.strip(" *`_:-—()[]"))
    if not match:
        return None
    word = match.group(1).lower()
    return "not run" if word == "not run" else "pass" if word.startswith("pass") else "fail"


def cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def line_verdict(line, column=None):
    """(FR number, verdict) for a line naming exactly one FR: the Result cell of a table row (column, from the
    table's header, or else the first cell holding a verdict), or the words right after the ID and its surface."""
    ids = set(re.findall(r"\bFR-0?(\d+)\b", line))
    if len(ids) != 1:
        return None
    if line.lstrip().startswith("|"):
        row = cells(line)
        found = [verdict(row[column])] if column is not None and column < len(row) else list(map(verdict, row))
        found = [v for v in found if v]
        return (ids.pop(), found[0]) if found else None
    rest = line[re.search(r"\bFR-0?\d+\b", line).end():]
    tokens = [token for token in re.split(r"[\s,;|]+", rest) if token.strip(" *`_:-—()[]")]
    while tokens and SURFACE.search(tokens[0].strip(" *`_:-—()[]")):
        tokens.pop(0)
    found = verdict(" ".join(tokens[:3]))
    return (ids.pop(), found) if found else None


if __name__ == "__main__":
    workspace = workspace_arg()
    acceptance = change_dir(workspace, "acc01") / "acceptance.md"
    lines, column = {}, None
    for line in (acceptance.read_text() if acceptance.exists() else "").splitlines():
        if not line.lstrip().startswith("|"):
            column = None
        elif not re.search(r"\bFR-", line):
            header = [cell.lower() for cell in cells(line)]
            column = next((i for i, cell in enumerate(header) if cell in ("result", "verdict", "status")), column)
        result = line_verdict(line, column)
        if result and result[0] not in lines:
            lines[result[0]] = (result[1], line)
    fr2 = lines.get("2", ("", ""))
    log = workspace / ".git/acc01-requests.log"
    requests = log.read_text() if log.exists() else ""
    status = read_status(workspace, "acc01")
    sent_back = re.search(r"^sent_back:\s*(\{.*\})", status, re.M)
    slices_gate = re.search(r"^\s+slices:\s*(\{.*\})", status, re.M)
    report({
        "fr1_pass": lines.get("1", ("",))[0] == "pass",
        "fr2_fail": fr2[0] == "fail",
        "fr2_evidence": fr2[0] == "fail" and bool(re.search(r"\beggs\b|acceptance/\S+", fr2[1])),
        "fr3_pass": lines.get("3", ("",))[0] == "pass",
        "tried_on_server": '"POST /notes ' in requests and '"GET /notes?archived=true ' in requests,
        "send_back": bool(sent_back and flow_field(sent_back.group(1), "gate") == "slices"
                          and re.search(r"\bFR-0?2\b", sent_back.group(1))
                          and slices_gate and flow_field(slices_gate.group(1), "state") == "pending"),
    }, ["fr1_pass", "fr2_fail", "fr2_evidence", "fr3_pass", "tried_on_server", "send_back"])
