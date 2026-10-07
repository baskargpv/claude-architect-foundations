# Task 2.5 — Built-in Tools

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Grep searches file CONTENTS; Glob matches file PATHS.
- Edit does unique-text replacement; a non-unique `old_string` fails by design.
- Explore incrementally: Grep for entry points -> Read only what that justifies -> Grep again for renamed wrappers/barrel re-exports.
- Deprecation sweep: Grep (direct refs) -> Glob (sibling test files) -> Grep (wrapper names). Never Glob first.

## Exam trap

Glob to find function callers; reading every file up front; defaulting to Read + Write for every change.

## Exam answer vs current docs

After Edit reports a non-unique match - exam guide v1.0: fall back to Read + Write. Current Claude Code: widen `old_string` or set `replace_all: true`. Both agree: try Edit first.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_2_5.py`.
