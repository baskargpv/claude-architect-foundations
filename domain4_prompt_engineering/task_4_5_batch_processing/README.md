# Task 4.5 — Batch Processing Strategies

Lesson: <https://claudecertificationguide.com/learn/4-prompt-engineering/4-5-batch-processing>

## What you need to know

- **Message Batches API facts:** 50% cheaper, up to **24h** processing, **no latency SLA**, and `custom_id` correlates each request with its result.
- **Match the API to the wait:**
  - **Synchronous** for blocking work: pre-merge checks, real-time review.
  - **Batch** for latency-tolerant work: overnight reports, weekly audits, nightly test generation.
- **SLA math:** a 30h SLA minus the 24h worst case leaves a 6h buffer. The submission cadence must be **shorter** than the buffer, so every 4h.
- **Handling failures:**
  - Find failed `custom_id`s (`errored` **or** `expired`).
  - Resubmit **only** those, with changes: chunking, simpler prompts, more `max_tokens`.
  - Poll `processing_status` until `ended`. Results arrive in any order.
- **Tune on 5–10 sample documents first.** At 90% first-pass success, 1,000 docs need 100 retries; at 60%, 400.

## Exam traps

| Trap | Demo |
|---|---|
| Switching every workflow to batch for the savings | `trap1_everything_to_batch` |
| Assuming results arrive quickly because they usually do | `trap2_design_for_typical_time`: fine typically, but breaches the 30h SLA in the worst case |
| The Batch API for multi-turn tool calling | `trap3_multi_turn_tools_in_batch`: the item stops at `tool_use` |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Tool calling in a batch | Not supported; use the synchronous API | **Server** tools (e.g. web search) can run their loop inside a batch item and return `pause_turn`. **Client** tools still stop at `tool_use` and need a follow-up request. **On the exam, answer per the guide.** |

## Practice scenario

The manager wants both workflows on batch.

**A: batch the overnight report only; keep the pre-merge check real-time.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. Classify 5 workflows | `WORKFLOWS`, `classify()` |
| 2. A 20-document batch with unique `custom_id`s | `build_requests()` |
| 3. Filter failures by `custom_id` and retry with changes | `process_all()`: 3 failures (2 errored, 1 expired), resubmitted with doubled `max_tokens`, giving 20/20 |
| 4. Submission frequency for a 30h SLA | `cadence_ok()`, `recommended_cadence()` → 4h |
| 5. Tune on a sample before the full batch | `expected_retries()` |

**How it runs.** Offline, `FakeBatches` implements the same `create` / `retrieve` / `results` calls as `client.messages.batches`. Live, `batch_client()` returns the real client, and `run_batch()` polls every 30s, which really can take hours.

## Run

```bash
.venv/bin/python -m domain4_prompt_engineering.task_4_5_batch_processing.good_example
.venv/bin/python -m domain4_prompt_engineering.task_4_5_batch_processing.anti_pattern
.venv/bin/pytest domain4_prompt_engineering/task_4_5_batch_processing
```
