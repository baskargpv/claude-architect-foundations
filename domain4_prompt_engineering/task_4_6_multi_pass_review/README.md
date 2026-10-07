# Task 4.6 — Multi-Instance and Multi-Pass Review

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Same-session self-review confirms its own reasoning - use an independent instance.
- Pass 1: per-file local analysis. Pass 2: a separate cross-file integration pass.
- Confidence routing: low confidence -> human. Raw confidence must be calibrated per pipeline against labelled sets.

## Exam trap

Larger context window to fix dilution; same-session "review carefully"; uncalibrated confidence for automated decisions.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_4_6.py`.
