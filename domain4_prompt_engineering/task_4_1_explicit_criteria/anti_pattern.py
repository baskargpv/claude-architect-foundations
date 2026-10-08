"""Task 4.1 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-1-system-prompts

Trap 1  "be conservative" / "only high-confidence findings" as the prompt fix
Trap 2  confidence thresholds as the fix for false positives
Trap 3  keeping every category active while a noisy one is being fixed
"""

from __future__ import annotations

from common.client import get_client
from domain4_prompt_engineering.task_4_1_explicit_criteria.good_example import (
    REPORTABLE,
    SNIPPETS,
    evaluate,
    mock_model,
    review,
)


def trap1_vague_instructions(client) -> dict:
    return evaluate(client, "You are a code reviewer. Be very conservative. Use your best judgement.")


def trap2_confidence_threshold(client, threshold: float = 0.8) -> dict:
    kept = [(s, f) for s in SNIPPETS for f in review(client, "Be conservative.", s) if f["confidence"] >= threshold]
    return {"kept_false_positives": sum(s["truth"] not in REPORTABLE for s, _ in kept),
            "dropped_real_bug": not any(s["truth"] == "bug" for s, _ in kept)}  # the bug came back at 0.6


def trap3_keep_noisy_category(category_fp: dict[str, float]) -> dict:
    """Developers stop reading ALL findings once any category is noisy (> 25% false positives)."""
    noisy = any(fp > 0.25 for fp in category_fp.values())
    return {"developers_read_findings": not noisy, "accurate_security_findings_acted_on": 0 if noisy else "all"}


def main():
    print(f"trap 1 vague        : {trap1_vague_instructions(get_client(mock_model))}")
    print(f"trap 2 confidence   : {trap2_confidence_threshold(get_client(mock_model))}")
    print(f"trap 3 noisy active : {trap3_keep_noisy_category({'security': 0.0, 'comment_mismatch': 0.5})}")


if __name__ == "__main__":
    main()
