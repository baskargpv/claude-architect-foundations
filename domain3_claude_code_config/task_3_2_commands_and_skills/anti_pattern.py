"""Task 3.2 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-2-slash-commands-skills

Trap 1  a flat Markdown file directly inside .claude/skills/
Trap 2  a team-shared command in a user-scoped path
Trap 3  expecting a skill to act like CLAUDE.md (always-on)
Trap 4  not using context: fork for a verbose skill
Trap 5  putting task-specific workflows in CLAUDE.md
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from common.claude_config import parse_frontmatter
from common.client import get_client
from domain3_claude_code_config.task_3_2_commands_and_skills.good_example import (
    BRAINSTORM_SKILL,
    REVIEW_COMMAND,
    discover_commands,
    mock_model,
    run_skill,
)


def trap1_flat_file_in_skills() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        (repo / ".claude/skills").mkdir(parents=True)
        (repo / ".claude/skills/review.md").write_text(REVIEW_COMMAND)  # no folder, no SKILL.md
        return sorted(discover_commands(repo, Path(tmp) / "home"))


def trap2_team_command_in_user_path() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo, me, teammate = Path(tmp) / "repo", Path(tmp) / "me", Path(tmp) / "teammate"
        repo.mkdir()
        (me / ".claude/commands").mkdir(parents=True)
        (me / ".claude/commands/review.md").write_text(REVIEW_COMMAND)
        return {"me": sorted(discover_commands(repo, me)), "teammate": sorted(discover_commands(repo, teammate))}


def session_context(repo: Path) -> str:
    """What every session starts with: CLAUDE.md, not skill bodies."""
    p = repo / "CLAUDE.md"
    return p.read_text() if p.exists() else ""


def trap3_skill_as_always_on() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        (repo / ".claude/skills/typing").mkdir(parents=True)
        (repo / ".claude/skills/typing/SKILL.md").write_text("---\ndescription: typing rules\n---\nAlways add type hints.\n")
        return {"rule_in_every_session": "Always add type hints." in session_context(repo)}


def trap4_no_fork() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        skill_path = Path(tmp) / "SKILL.md"
        skill_path.write_text(BRAINSTORM_SKILL.replace("context: fork\n", ""))
        skill = {"path": skill_path, "meta": parse_frontmatter(skill_path.read_text())[0]}
        history = run_skill(get_client(mock_model), skill, "cache invalidation strategy", [])
        return {"chars_added_to_main_conversation": len(history[-1]["content"])}


def trap5_workflow_in_claude_md(sessions: int = 20) -> dict:
    workflow = "Release procedure: bump version, update CHANGELOG, tag, build, publish, announce.\n" * 10
    return {"chars_loaded_over_sessions": len(workflow) * sessions,  # in CLAUDE.md: paid every session
            "as_a_skill_used_twice": len(workflow) * 2}  # as a skill: paid only when /release runs


def main():
    print(f"trap 1 flat file in skills/ : commands found = {trap1_flat_file_in_skills()}")
    print(f"trap 2 team cmd in ~/.claude: {trap2_team_command_in_user_path()}")
    print(f"trap 3 skill as always-on   : {trap3_skill_as_always_on()}")
    print(f"trap 4 no context: fork     : {trap4_no_fork()}")
    print(f"trap 5 workflow in CLAUDE.md: {trap5_workflow_in_claude_md()}")


if __name__ == "__main__":
    main()
