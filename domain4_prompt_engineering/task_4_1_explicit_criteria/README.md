# Task 4.1 — System Prompts with Explicit Criteria

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- "Be conservative" / "high-confidence only" give no decision boundary - define report-X / skip-Y categories with concrete triggers.
- One noisy category destroys trust in all categories: temporarily disable it while you fix its prompt.
- Calibrate severity with code examples per level, not prose definitions.
- Self-reported confidence is poorly calibrated: use it for routing (4.6), never in place of criteria.

## Exam trap

Vague confidence-based instructions as the fix; keeping a high false-positive category running while reworking it.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_4_1.py`.
