"""Task 3.4 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-4-plan-mode-execution

Trap 1  direct execution for a multi-file architectural change
Trap 2  plan mode for a single-file bug with a clear stack trace
Trap 3  not recognising the plan-then-execute hybrid
Trap 4  starting in direct execution and switching to plan mode once complexity "emerges"
"""

from __future__ import annotations


def trap1_direct_for_architecture(files: int = 12) -> dict:
    """Edits start immediately; a better boundary is found at file 8 -> 7 real edits to unwind."""
    better_approach_found_at = 8
    return {"files_edited_before_rethink": better_approach_found_at - 1, "edits_to_unwind": better_approach_found_at - 1}


def trap2_plan_for_clear_bug() -> dict:
    return {"steps_needed": ["fix the null check"], "steps_taken": ["explore", "write plan", "wait for approval", "fix"],
            "overhead_steps": 3}


def trap3_plan_or_direct_only(files: int = 30) -> dict:
    """Either plan forever (nothing changes) or edit 30 files with no shared strategy (inconsistent)."""
    return {"plan_only_files_changed": 0, "direct_only_distinct_migration_styles": 3}


def trap4_switch_late(stated_in_task: str = "restructure the monolith into microservices") -> dict:
    complexity_was_stated_upfront = "restructure" in stated_in_task or "migrate" in stated_in_task
    return {"complexity_stated_upfront": complexity_was_stated_upfront,
            "files_already_modified_when_switching": 5, "should_have_started_in": "plan"}


def main():
    print(f"trap 1 direct for architecture : {trap1_direct_for_architecture()}")
    print(f"trap 2 plan for a clear bug    : {trap2_plan_for_clear_bug()}")
    print(f"trap 3 no hybrid               : {trap3_plan_or_direct_only()}")
    print(f"trap 4 switching late          : {trap4_switch_late()}")


if __name__ == "__main__":
    main()
