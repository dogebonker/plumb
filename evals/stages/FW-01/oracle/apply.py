"""Turn a fresh FW-01 setup into the research and draft the architecture gate should produce.

Usage: python3 apply.py <workspace>.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stagelib import change_dir, workspace_arg, write  # noqa: E402

QUESTIONS = [
    "What does `Notebook.delete` in notes.py do today, and what happens for an unknown id?",
    "Which code calls `Notebook.delete`?",
    "What data does one note hold, and where is it kept?",
    "What do Pond sessions dated before the change base record about notes.py?",
]
ANSWERS = [
    "It removes the entry from the `notes` dict with `del` (notes.py:17). An unknown id raises KeyError "
    "(notes.py:16, test_notes.py:14-16).",
    "Only the tests: test_notes.py:11 and test_notes.py:16.",
    "A dict with `id` and `title` (notes.py:11), kept in the in-memory `notes` dict keyed by id (notes.py:6).",
    "not found",
]


def research(workspace, questions, answers):
    """Write research.md in plumb-architecture's form, one answer indented under each question, and a draft."""
    items = "".join(f"{number}. {question}\n" + (f"   Answer: {answers[number - 1]}\n" if number <= len(answers) else "")
                    for number, question in enumerate(questions, 1))
    write(change_dir(workspace, "fw01") / "research.md", f"# Research: fw01\n\n{items}")
    write(change_dir(workspace, "fw01") / "02-architecture.md", """# Architecture: fw01

## Research
- `Notebook.delete` removes a note from the in-memory dict (notes.py:17), research.md answer 1.

## Open questions
""")


if __name__ == "__main__":
    research(workspace_arg(), QUESTIONS, ANSWERS)
