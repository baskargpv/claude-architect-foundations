"""Task 3.1 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-1-claude-md-hierarchy

Trap 1  team conventions in one developer's user-level config -> new teammate never gets them
Trap 2  thinking /memory triggers configuration loading
Trap 3  directory-level CLAUDE.md for a convention that spans many directories
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from domain3_claude_code_config.task_3_1_claude_md_hierarchy.good_example import (
    build_project,
    context_text,
    loaded_memory,
    memory_command,
)

NAMING = "Use plural nouns for REST resources."


def trap1_conventions_in_user_config() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = build_project(Path(tmp) / "repo", {"README.md": "app"})
        home_a, home_b = Path(tmp) / "dev_a", Path(tmp) / "dev_b"
        (home_a / ".claude").mkdir(parents=True)
        (home_a / ".claude" / "CLAUDE.md").write_text(NAMING)  # WRONG place for a team rule
        return {"dev_a_has_rule": NAMING in context_text(loaded_memory(repo, home_a)),
                "dev_b_has_rule": NAMING in context_text(loaded_memory(repo, home_b))}


def trap2_memory_loads_nothing() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo, home = build_project(Path(tmp) / "repo"), Path(tmp) / "home"
        before = loaded_memory(repo, home)
        memory_command(repo, home)  # "B should run /memory to load the rules"
        return {"changed_what_loaded": loaded_memory(repo, home) != before}


def trap3_directory_level_for_cross_cutting(dirs: int = 50) -> dict:
    """One copy per directory -> 50 files to keep in sync; edit one and they drift."""
    with tempfile.TemporaryDirectory() as tmp:
        files = {f"src/module_{i:02d}/CLAUDE.md": "Tests: name them 'does X when Y'.\n" for i in range(dirs)}
        repo = build_project(Path(tmp) / "repo", files)
        (repo / "src/module_07/CLAUDE.md").write_text("Tests: name them 'should X'.\n")  # someone updates one copy
        versions = {p.read_text() for p in repo.glob("src/*/CLAUDE.md")}
        return {"copies": dirs, "distinct_versions": len(versions)}


def main():
    print(f"trap 1 user-level team rules : {trap1_conventions_in_user_config()}")
    print(f"trap 2 /memory loads config  : {trap2_memory_loads_nothing()}")
    print(f"trap 3 per-directory copies  : {trap3_directory_level_for_cross_cutting()}  <- use .claude/rules with paths:")


if __name__ == "__main__":
    main()
