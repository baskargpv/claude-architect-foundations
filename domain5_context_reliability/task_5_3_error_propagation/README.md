# Task 5.3 — Error Propagation in Multi-Agent Systems

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Structured error context: failure type, what was attempted, partial results, alternative approaches.
- Silent suppression and workflow termination share one root cause: the coordinator only gets a bare exception or a bare empty success.
- Distinguish access failure from a valid empty result; recover transient failures locally first.
- Annotate coverage gaps in synthesis instead of silently omitting topics.

## Exam trap

Returning empty results as success; killing the pipeline on one subagent failure; retrying a valid empty result.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_5_3.py`.
