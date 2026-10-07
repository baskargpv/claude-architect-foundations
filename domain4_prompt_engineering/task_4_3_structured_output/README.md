# Task 4.3 — Structured Output with Tool Use

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- `tool_use` + JSON schema eliminates syntax errors; prompt-asked JSON has no guarantee.
- `tool_choice` applies per request - reset to `auto` after a forced call or you loop.
- Schemas don't catch sum mismatches, misplaced fields or fabrication.
- Production schemas: nullable fields, an `unclear` enum value, `other` + detail string.

## Exam trap

Believing tool_use prevents all extraction errors; making every field required (pressures fabrication).

## Exam answer vs current docs

Exam answer: two-tier hierarchy (tool_use > prompt JSON) and three `tool_choice` modes. Current docs add `strict: true`, `output_config.format` and a fourth mode `{type: none}`; newest models (incl. `claude-sonnet-5-5`) reject forced `any`/`tool` with a 400.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_4_3.py`.
