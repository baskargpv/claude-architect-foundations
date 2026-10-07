# Task 2.2 — Structured Error Responses

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Two layers: protocol errors (malformed call, JSON-RPC error, model never sees a result) vs. tool execution errors (`isError: true`, model reads and recovers).
- Four categories: transient (`isRetryable: true`), validation, business, permission (all `false`).
- `isRetryable` answers only: will resending this EXACT call work? `false` means "not this call again", not "stop".
- Access failure (`isError: true`) must look nothing like a valid empty result (`isError: false`, no retry).
- Subagents recover transient failures locally and propagate the rest with partial results and what was attempted.

## Exam trap

Retrying a successful empty result; treating business errors as retryable; marking validation `isRetryable: true` because the agent can fix the input.

## Exam answer vs current docs

Exam guide v1.0 assigns `retriable: false` to business errors and leaves validation unspecified. `false` for validation is the wider-ecosystem convention (gRPC INVALID_ARGUMENT, AWS retry metadata) - reason from "will this exact call work again".

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_2_2.py`.
