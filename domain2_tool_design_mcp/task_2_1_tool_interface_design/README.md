# Task 2.1 — Tool Interface Design

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Tool descriptions are the PRIMARY selection mechanism, not supplementary metadata.
- A production description states: what it does, inputs (types/formats/constraints), example queries, edge cases/limits, and when to use THIS tool vs. similar ones.
- Misrouting fix ranking: expand descriptions (correct) > few-shot / routing classifier / consolidation (wrong as a first step).
- Split generic tools (`analyze_document`) into narrow ones (`extract_data_points`, `summarize_content`, `verify_claim_against_source`).
- Keyword-sensitive system-prompt instructions can silently override good descriptions - reread the system prompt after fixing them.

## Exam trap

Reaching for few-shot examples, a routing classifier, or consolidation before expanding descriptions. Descriptions are not the fix when the toolkit itself is too large (past ~4-5 tools per agent) - see 2.3.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_2_1.py`.
