"""Task 5.4 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-4-codebase-exploration

Trap 1  a bigger context window to fix context degradation
Trap 2  treating subagent delegation as only about parallelisation
Trap 3  restarting a session without saving state first
Trap 4  using /compact only when the context limit is hit
"""

from __future__ import annotations

from common import config
from common.client import get_client, response_text
from domain5_context_reliability.task_5_4_context_degradation.good_example import TASKS, answer_later_question, mock_model


def trap1_bigger_window(client) -> str:
    """A 1M window still fills with verbose output; the specific finding is still buried."""
    return answer_later_question(client, "(1M-token window, 20 turns of verbose output, nothing written down)")


def trap2_inline_exploration(client) -> dict:
    """Doing the exploration in the MAIN context: every verbose read lands there."""
    main_context = ""
    for task in TASKS.values():
        main_context += response_text(client.messages.create(model=config.model(), max_tokens=4096,
                                                             messages=[{"role": "user", "content": f"[EXPLORE] {task}"}]))
    return {"main_context_chars": len(main_context)}


def trap3_restart_without_saving() -> dict:
    findings_before_restart = ["OrderRepository.findById is cached (src/repos/order.ts)"]
    new_session_context = []  # nothing was saved to a scratchpad or manifest
    return {"findings_lost": len(findings_before_restart) - len(new_session_context)}


def trap4_compact_only_at_limit(turns_until_limit: int = 40, degraded_from_turn: int = 15) -> dict:
    return {"turns_spent_degraded_before_compacting": turns_until_limit - degraded_from_turn}


def main():
    print(f"trap 1 bigger window   : {trap1_bigger_window(get_client(mock_model))}")
    print(f"trap 2 no delegation   : {trap2_inline_exploration(get_client(mock_model))}  (subagents return a few hundred)")
    print(f"trap 3 restart unsaved : {trap3_restart_without_saving()}")
    print(f"trap 4 late /compact   : {trap4_compact_only_at_limit()}")


if __name__ == "__main__":
    main()
