# Task 5.4 — Codebase Exploration & Context Degradation

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Degradation is depth-over-time (not breadth-in-one-pass like 1.6 dilution) and not a token-limit problem.
- Scratchpad files keep findings outside the context; subagent delegation keeps verbose output out entirely.
- Inject a phase-1 summary into phase-2 subagents; use `/compact` proactively.
- Crash recovery via a structured state manifest each agent exports.

## Exam trap

A bigger context window as the fix; delegation viewed only as parallelisation; restarting without saving state.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_5_4.py`.
