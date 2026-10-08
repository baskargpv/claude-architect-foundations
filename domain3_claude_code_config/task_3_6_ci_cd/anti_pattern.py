"""Task 3.6 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-6-cicd-integration

Trap 1  the CI job hangs waiting for input (CLAUDE_HEADLESS / --batch / </dev/null aren't the fix)
Trap 2  self-review in the same session as generation
Trap 3  the Batch API for blocking pre-merge checks
Trap 4  not passing prior findings into the next review run
"""

from __future__ import annotations

from common.client import get_client
from domain3_claude_code_config.task_3_6_ci_cd.good_example import ISSUES, generate, mock_model, post_inline_comments, review


def runs_non_interactively(argv: list[str], env: dict | None = None) -> bool:
    return "-p" in argv or "--print" in argv  # nothing else switches the mode


def trap1_ci_hang_fixes() -> dict:
    attempts = {
        "plain claude": (["claude", "Review this PR"], {}),
        "CLAUDE_HEADLESS=true": (["claude", "Review this PR"], {"CLAUDE_HEADLESS": "true"}),  # doesn't exist
        "--batch": (["claude", "--batch", "Review this PR"], {}),  # doesn't exist
        "< /dev/null": (["claude", "Review this PR", "<", "/dev/null"], {}),  # still interactive mode
        "-p": (["claude", "-p", "Review this PR"], {}),
    }
    return {name: ("finishes" if runs_non_interactively(argv, env) else "hangs") for name, (argv, env) in attempts.items()}


def trap2_same_session_self_review(client) -> dict:
    """SIMULATED: the generating session still holds its own justification ('eval for flexibility'),
    so it confirms rather than challenges. An independent review session finds the bugs."""
    code = generate(client, "Write a login handler")
    same_session_verdict = "Looks good - eval keeps the config flexible, as intended."
    independent = post_inline_comments(review(client, code))
    return {"same_session": same_session_verdict, "independent_review_findings": len(independent)}


def trap3_batch_for_pre_merge() -> dict:
    return {"developer_waits_up_to_hours": 24, "latency_sla": None, "verdict": "blocking work stays synchronous"}


def trap4_no_prior_findings(client, pushes: int = 3) -> list[int]:
    code = generate(client, "Write a login handler")
    return [len(post_inline_comments(review(client, code, prior=None))) for _ in range(pushes)]  # same comments every push


def main():
    print(f"trap 1 CI hang fixes   : {trap1_ci_hang_fixes()}")
    print(f"trap 2 self-review     : {trap2_same_session_self_review(get_client(mock_model))}")
    print(f"trap 3 batch pre-merge : {trap3_batch_for_pre_merge()}")
    print(f"trap 4 no prior context: comments per push {trap4_no_prior_findings(get_client(mock_model))}  "
          f"(the same {len(ISSUES)} findings, every push)")


if __name__ == "__main__":
    main()
