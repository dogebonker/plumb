"""Grade an FW-01 workspace: python3 grade.py <workspace>. Prints one JSON line.

Questions and answers are read as numbered items: factory-architecture's form, an answer indented under each
numbered question, or a numbered list of questions followed by a second list numbered from 1 again.
"""

import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE.parent))

from stagelib import change_dir, git_ok, report, workspace_arg  # noqa: E402

FORBIDDEN = [re.compile(line, re.I) for line in (CASE / "grading/forbidden_words.txt").read_text().splitlines() if line]
CITATION = re.compile(r"([\w./-]+\.\w+):(\d+)")
POND_ID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
CODE_ENTITY = re.compile(r"\b(delete|Notebook)\b", re.I)


def numbered_items(text):
    """[number, first line, following lines] for each item numbered at the start of a line; a heading ends one."""
    items, current = [], None
    for line in text.splitlines():
        match = re.match(r"^(\d+)[.)]\s+(.*)", line)
        if match:
            current = [int(match.group(1)), match.group(2), []]
            items.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None and line.strip():
            current[2].append(line.strip())
    return items


def questions_and_answers(text):
    items = numbered_items(text)
    runs = []
    for item in items:
        if not runs or item[0] <= runs[-1][-1][0]:
            runs.append([])
        runs[-1].append(item)
    if len(runs) >= 2:
        return [" ".join([q[1], *q[2]]) for q in runs[0]], [" ".join([a[1], *a[2]]) for a in runs[1]]
    return [item[1] for item in items], [" ".join(item[2]) for item in items]


if __name__ == "__main__":
    workspace = workspace_arg()
    research = change_dir(workspace, "fw01") / "research.md"
    questions, answers = questions_and_answers(research.read_text()) if research.exists() else ([], [])
    tracked = set((git_ok(workspace, "ls-files") or "").splitlines())
    cited = [re.sub(r"^.*?/repo/", "", path).removeprefix("./") for answer in answers
             for path, _ in CITATION.findall(answer)]
    report({
        "research_md": research.exists(),
        "questions_clean": bool(questions) and not any(word.search(q) for q in questions for word in FORBIDDEN),
        "questions_on_code": any(CODE_ENTITY.search(q) for q in questions),
        "answers_complete": bool(questions) and len(answers) == len(questions) and all(
            CITATION.search(a) or POND_ID.search(a) or re.search(r"not found", a, re.I) for a in answers),
        "answers_cite": bool(cited) and all(path in tracked for path in cited),
    }, ["research_md", "questions_clean", "questions_on_code", "answers_complete", "answers_cite"])
