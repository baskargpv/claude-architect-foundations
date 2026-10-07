# Task 2.3 — Tool Distribution & Tool Choice

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- 18 tools on one agent degrades selection; aim for 4-5 tools per agent, scoped to its role.
- Fix by situation: two tools read alike -> sharpen descriptions; different jobs -> split by role; variations on one job -> consolidate into one parameterised tool; too much reach -> constrain (least privilege).
- Splitting tools across two MCP servers fixes nothing - clients flatten all servers into one list.
- `tool_choice`: `auto` (default), `any` (must call some tool), `{type: tool, name}` (must call that tool).
- Give a synthesis agent a scoped `verify_fact` for the ~85% simple case instead of 2-3 coordinator round trips.

## Exam trap

Using `tool_choice: auto` when structured output is required; giving one agent 18 tools; a generic `fetch_url` instead of a constrained `load_document`.

## Exam answer vs current docs

Current docs: `claude-sonnet-5-5` and other newest models return a 400 for forced `tool_choice` (`any` / `tool`). Use `auto` + `strict: true` + a prompt instruction, or `output_config.format`. On the exam, answer with the three modes.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_2_3.py`.
