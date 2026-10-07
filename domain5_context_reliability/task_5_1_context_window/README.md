# Task 5.1 — Context Window Management

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Progressive summarisation destroys amounts, dates and IDs - keep a persistent case-facts block outside the summarised history.
- Lost-in-the-middle: put a key-findings summary first and use section headers; instructions don't fix position effects.
- Trim verbose tool results BEFORE they enter history (PostToolUse or in the tool).
- The API is stateless - every request carries full history; prompt caching rewards a stable prefix.

## Exam trap

Trusting summarisation with transactional data; "pay attention to everything" as the fix; keeping 40-field tool results "just in case".

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_5_1.py`.
