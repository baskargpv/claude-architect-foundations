# Task 5.3 — Error Propagation in Multi-Agent Systems

Lesson: <https://claudecertificationguide.com/learn/5-context-management/5-3-error-propagation>

## What you need to know

- **Structured error context has four parts:**
  1. **failure type** (transient / validation / business / permission)
  2. **attempted action** (query, parameters, target)
  3. **partial results** gathered before the failure
  4. **alternative approaches**
- **Two anti-patterns:** silent suppression (empty results marked as success) and workflow termination (killing the pipeline on one failure). Structured errors fix both.
- **Access failure vs valid empty result:** an access failure means the query never ran, so consider retrying. A valid empty result means it ran and found nothing, so don't retry.
- **Annotate coverage in the synthesis** (well-supported / limited / unavailable, with the reason) so a gap isn't mistaken for irrelevance.
- **Recover locally first:** subagents handle transient failures themselves (retry, fallback, degraded response) before propagating.

## Exam traps

| Trap | Demo |
|---|---|
| Catching a timeout and returning empty results as success | `trap1_silent_suppression` |
| Terminating the whole pipeline on one timeout | `trap2_terminate_pipeline`: solar and wind results discarded |
| A generic "search unavailable" after retries run out | `trap3_generic_status` |
| Retrying a valid empty result | `trap4_retry_valid_empty` |

## Exam answer vs current docs

No difference.

## Practice scenario

A web search subagent times out mid-research.

**C: return structured error context** (failure type, query, partial results, alternatives).

## Build exercise → code

| Step | Where |
|---|---|
| 1. An error schema: `failureType`, `attemptedAction`, `partialResults`, `alternativeApproaches` | `SubagentResult` (Pydantic) |
| 2. Access failure → `shouldRetry: true`; valid empty → success with `shouldRetry: false` | `search_with_recovery()` |
| 3. Exponential backoff (1s/2s/4s, scaled down for the demo), 3 attempts, keeping partial results | same. `fusion` recovers locally after 2 timeouts. |
| 4. A coordinator that handles each outcome without suppressing anything | `coordinate()` |
| 5. A coverage section in the synthesis | `coverage_section()` |

## Run

```bash
.venv/bin/python -m domain5_context_reliability.task_5_3_error_propagation.good_example
.venv/bin/python -m domain5_context_reliability.task_5_3_error_propagation.anti_pattern
.venv/bin/pytest domain5_context_reliability/task_5_3_error_propagation
```
