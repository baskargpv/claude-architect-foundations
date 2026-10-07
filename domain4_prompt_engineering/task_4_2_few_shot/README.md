# Task 4.2 — Few-Shot Prompting

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- First tool for inconsistent output - not more instructions, thresholds or temperature.
- 2-4 targeted examples that cover the actual failing cases, each showing REASONING, not just input -> output.
- Route each failure to its fix: malformed JSON -> tool_use schema; fabricated fields -> nullable schema; wrong tool -> descriptions first; sum mismatch -> validation retry.

## Exam trap

Few-shot examples without reasoning (the model learns the literal pattern only); adding more prose instructions.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_4_2.py`.
