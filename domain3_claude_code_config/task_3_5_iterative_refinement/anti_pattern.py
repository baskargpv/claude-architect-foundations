"""Task 3.5 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-5-iterative-refinement

Trap 1  refining the prose when the model interprets it inconsistently
Trap 2  not batching feedback for issues that interact
Trap 3  confusing the interview pattern with the examples technique
"""

from __future__ import annotations

import json

from common.client import get_client
from domain3_claude_code_config.task_3_5_iterative_refinement.good_example import TASK, mock_model, runs

PRECISE_PROSE = (TASK + " Use a consistent, standard, internationally recognised format with the country code, "
                 "separating groups clearly and unambiguously.")


def trap1_more_precise_prose(client) -> int:
    return len({json.dumps(r) for r in runs(client, PRECISE_PROSE)})  # still more than one reading


def trap2_sequential_for_interacting_issues() -> dict:
    """Fix the error shape, then the SDK types, then logging - each later fix changes what the earlier one
    should have been, so earlier work is redone."""
    order = ["error response shape", "client SDK types", "logging format"]
    reworked = ["error response shape", "client SDK types"]  # revisited after the later fixes landed
    return {"messages": len(order), "fixes_redone": len(reworked)}


def trap3_wrong_technique() -> dict:
    return {
        "interview_when_target_known": "an extra round of questions whose answers you already had - just show examples",
        "examples_when_target_unknown": "examples encode a guess at the format, so Claude reliably hits the wrong target",
    }


def main():
    print(f"trap 1 precise prose : {trap1_more_precise_prose(get_client(mock_model))} different outputs over 3 runs")
    print(f"trap 2 sequential    : {trap2_sequential_for_interacting_issues()}")
    print(f"trap 3 wrong technique: {trap3_wrong_technique()}")


if __name__ == "__main__":
    main()
