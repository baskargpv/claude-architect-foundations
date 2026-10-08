"""Task 4.2 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-2-few-shot-prompting

Trap 1  adding more detailed instructions when the output is already inconsistent
Trap 2  thinking few-shot only teaches literal pattern matching (examples without reasoning)
Trap 3  confidence thresholds to fix inconsistent judgement calls
"""

from __future__ import annotations

import re

from common.client import get_client
from domain4_prompt_engineering.task_4_2_few_shot.good_example import FEW_SHOT, INSTRUCTIONS, mock_model, run

MORE_INSTRUCTIONS = INSTRUCTIONS + (" IMPORTANT: values may appear in narrative sentences, not only tables. Read every "
                                    "sentence carefully. Do not miss authors or sample sizes in prose. Be thorough.")


def trap1_more_instructions(client) -> dict:
    return run(client, MORE_INSTRUCTIONS)


def trap2_examples_without_reasoning(client) -> dict:
    """Same three examples with the reasoning stripped: only the literal pattern is shown, so the
    general principle (sample size = the count attached to a recruitment verb) isn't learned."""
    bare = re.sub(r"Reasoning:.*", "", FEW_SHOT)
    return run(client, INSTRUCTIONS + bare)


def trap3_confidence_threshold() -> dict:
    return {"fix": "only accept extractions with confidence > 0.9",
            "effect": "filters on a poorly calibrated number; never shows the model how to read narrative text",
            "root_cause_addressed": False}


def main():
    print(f"trap 1 more instructions : empty {trap1_more_instructions(get_client(mock_model))['empty_rate']:.0%}")
    print(f"trap 2 no reasoning      : empty {trap2_examples_without_reasoning(get_client(mock_model))['empty_rate']:.0%}")
    print(f"trap 3 confidence filter : {trap3_confidence_threshold()}")


if __name__ == "__main__":
    main()
