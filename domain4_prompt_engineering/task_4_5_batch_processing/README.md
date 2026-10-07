# Task 4.5 — Batch Processing Strategies

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Message Batches: 50% cheaper, up to 24h, no latency SLA, `custom_id` correlates results.
- Synchronous for blocking work (pre-merge); batch for latency-tolerant work (nightly, weekly).
- SLA math: 30h SLA - 24h window = 6h buffer; the submission cadence must be SHORTER than the buffer (e.g. 4h).
- Resubmit only failed/expired `custom_id`s with modifications; tune prompts on 5-10 samples first.

## Exam trap

Switching everything to batch for the savings; resubmitting the whole batch.

## Exam answer vs current docs

Exam answer: no multi-turn tool calling inside a batch request. Current docs: server tools (web search) can loop inside a batch item and return `pause_turn`; client tools still cannot.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_4_5.py`.
