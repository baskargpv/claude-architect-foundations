# Task 3.4 — Plan Mode vs Direct Execution

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- "The decision is not about difficulty but about ambiguity."
- Plan mode: large-scale changes, multiple valid approaches, architectural consequences, multi-file migrations, exploration before change.
- Enter by switching mode (`--permission-mode plan`, Shift+Tab, `/plan`), not by writing "in plan mode" in the prompt.
- Hybrid: plan first, then execute the approved strategy directly. The Explore subagent keeps discovery noise out of the main context.

## Exam trap

Plan mode for a single-file fix with a clear stack trace; starting direct execution on a task whose complexity is stated up front.

## Code walkthrough

_To be built:_ `good_example/` and `anti_pattern/` hold demo configs (YAML / Markdown / shell); `test_task_3_4.py` validates their structure.
