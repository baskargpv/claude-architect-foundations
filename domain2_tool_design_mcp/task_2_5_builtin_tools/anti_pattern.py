"""Task 2.5 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-5-built-in-tools

Trap 1  Glob to find function callers (it matches paths, not contents)
Trap 2  Grep to find files by name pattern (Glob is the purpose-built tool)
Trap 3  reading every source file up front
Trap 4  Read + Write for every change instead of trying Edit first
Trap 5  answering "widen old_string / replace_all" on the exam's non-unique-match question
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from domain2_tool_design_mcp.task_2_5_builtin_tools.good_example import Tools, migrate, workspace


def trap1_glob_for_callers(root: Path) -> list[str]:
    return Tools(root).glob("**/*processLegacyOrder*")  # no FILE is named after the function


def trap2_grep_for_test_files(root: Path) -> list:
    return Tools(root).grep(r"\.test\.ts")  # file NAMES aren't in file CONTENTS


def trap3_read_everything(root: Path) -> int:
    t = Tools(root)
    for p in sorted(root.rglob("*")):
        if p.is_file():
            t.read(str(p.relative_to(root)))
    return t.context_chars


def trap4_read_write_every_change(root: Path) -> int:
    t = Tools(root)
    for f in ("src/checkout.ts", "src/admin.ts"):
        content = t.read(f)
        t.write(f, content.replace("processLegacyOrder(", "processOrder("))  # whole file in, whole file out
    return t.context_chars


def trap5_exam_answer_after_non_unique() -> dict:
    return {"exam_guide_v1_answer": "Read + Write the whole file",
            "current_docs / real work": "widen old_string or set replace_all: true",
            "trap": "answering the current-docs version on the exam"}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = workspace(Path(tmp) / "ws")
        print(f"trap 1 Glob for callers : {trap1_glob_for_callers(root)}  <- Grep finds 4 files")
        print(f"trap 2 Grep for tests   : {trap2_grep_for_test_files(root)}  <- Glob finds 2 files")
        good_chars = migrate(workspace(Path(tmp) / "ws2"))["context_chars"]
        print(f"trap 3 read everything  : {trap3_read_everything(root)} chars vs the whole incremental migration's {good_chars}")
        edit = Tools(workspace(Path(tmp) / "ws3"))
        edit.edit("src/admin.ts", "processLegacyOrder(order)", "processOrder(order)")
        edit.edit("src/checkout.ts", "processLegacyOrder(", "processOrder(", replace_all=True)
        print(f"trap 4 Read+Write       : {trap4_read_write_every_change(root)} chars vs Edit's {edit.context_chars}")
    print(f"trap 5 exam vs docs     : {trap5_exam_answer_after_non_unique()}")


if __name__ == "__main__":
    main()
