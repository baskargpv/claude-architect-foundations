# Task 4.4 — Validation, Retry, and Feedback Loops

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- A retry needs the original document, the failed extraction AND the specific validation error.
- Retries fix format, structure, placement and arithmetic - never information absent from the source.
- Self-correcting schemas: `calculated_total` vs `stated_total`, `conflict_detected`, `detected_pattern`.
- Pydantic: parsing enforces structure, validators enforce cross-field semantics; one ValidationError feeds the retry.

## Exam trap

Assuming retries always work; retrying without the specific error; treating Pydantic as redundant once a schema is enforced.

## Exam answer vs current docs

Current docs: `strict: true` and `.parse()` enforce the schema server-side; they do not replace your semantic validators.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_4_4.py`.
