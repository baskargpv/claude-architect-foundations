"""Task 4.6 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-6-multi-pass-review

Trap 1  self-review in the same session as generation
Trap 2  a single pass for a large multi-file review
Trap 3  a larger context window to fix attention dilution
Trap 4  uncalibrated confidence scores for automated routing
"""

from __future__ import annotations

from common.client import get_client
from domain1_agentic_architecture.task_1_6_task_decomposition.good_example import dilution_artefacts, single_pass_review
from domain4_prompt_engineering.task_4_6_multi_pass_review.good_example import (
    FILES,
    is_noise,
    review_mock,
    review_with_confidence,
    route,
)


def trap1_same_session_self_review() -> dict:
    """SIMULATED: the session that wrote the code still holds its reasons, so it confirms them."""
    return {"verdict": "The eval() call is intentional for flexibility - approved.", "issues_found": 0}


def trap2_single_pass(client) -> dict:
    r = single_pass_review(client, FILES)
    return {"findings": len(r["issues"]), "artefacts": len(dilution_artefacts(r, FILES))}


def trap3_bigger_context(client) -> dict:
    r = single_pass_review(client, FILES, "You have a 1M-token window; review all files at once.")
    return {"findings": len(r["issues"]), "artefacts": len(dilution_artefacts(r, FILES))}  # same architecture, same result


def trap4_raw_confidence_routing(client, raw_threshold: float = 0.8) -> dict:
    routed = route(review_with_confidence(client), raw_threshold)
    return {"false_positives_to_developers": sum(1 for f in routed["developers"] if is_noise(f))}


def main():
    print(f"trap 1 same-session review : {trap1_same_session_self_review()}")
    print(f"trap 2 single pass         : {trap2_single_pass(get_client(review_mock))}")
    print(f"trap 3 bigger context      : {trap3_bigger_context(get_client(review_mock))}")
    print(f"trap 4 raw 0.8 threshold   : {trap4_raw_confidence_routing(get_client(review_mock))}")


if __name__ == "__main__":
    main()
