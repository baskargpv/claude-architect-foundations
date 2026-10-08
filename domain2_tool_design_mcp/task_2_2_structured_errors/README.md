# Task 2.2 — Structured Error Responses

Lesson: <https://claudecertificationguide.com/learn/2-tool-design-mcp/2-2-structured-error-responses>

## What you need to know

- **Two error layers:**
  - **Protocol errors** are JSON-RPC `error` responses (e.g. `-32602` for an unknown tool). The host handles them, and the model never sees them.
  - **Tool execution errors** are normal results with `isError: true`. The model reads them and decides how to recover.
- **`errorCategory`, `isRetryable` and `description`** are application conventions, not MCP envelope fields. They go in `structuredContent`.

| Category | `isRetryable` | Recovery |
|---|---|---|
| transient | `true` | Same call after a delay |
| validation | `false` | Fix the input and send a **new** call. The agent recovers on its own. |
| business | `false` | Don't retry. Take another path or escalate. |
| permission | `false` | Retry as a principal with the right access |

- **`isRetryable: false` means "don't resend this exact call"**, not "stop".
- **Access failure vs empty result:** an access failure (`isError: true`, transient) must look nothing like a valid empty result (`isError: false`, `resultCount: 0`, no retry).
- **In multi-agent systems:** recover transient failures locally, and only pass up what can't be resolved, along with partial results and what was attempted.

## Exam traps

| Trap | Demo |
|---|---|
| Retrying an empty result from a successful query | `trap1_retry_empty_result`: 4 calls, then a wrong escalation |
| Generic "Operation failed" errors | `trap2_generic_errors`: blind identical retries |
| Treating business errors as retryable | `trap3_business_as_retryable` |
| Marking validation `isRetryable: true` | `trap4_validation_marked_retryable`: the exact malformed call fails 3 times |
| Reading `isRetryable: false` as "abandon" | `trap5_false_means_abandon`: gives up on a fixable input |
| Silently returning empty results as success | `trap6_silent_suppression`: a timeout reads as "customer does not exist" |

## Exam answer vs current docs

| | Exam answer | Note |
|---|---|---|
| `isRetryable` for validation errors | Exam guide v1.0 sets `false` only for business errors and never assigns a value to validation | `false` for validation follows ecosystem convention (gRPC, AWS retry metadata). Ask whether resending the exact call would work; for validation it wouldn't, so `false`. |

## Practice scenario

An empty lookup is retried 3 times, then escalated, but the account doesn't exist. Root cause?

**D: the tool doesn't distinguish access failures from valid empty results.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. An MCP customer-lookup tool with a `failure_mode` switch | `build_server()` → `lookup_customer` |
| 2–3. All four categories with `isError: true`, `errorCategory`, `isRetryable` and `description` | `error()`, which returns a real MCP `CallToolResult` with `structured_content` |
| 4. A valid empty result that's structurally different | `ok({"resultCount": 0, "results": []})` with `is_error=False` |
| 5. A loop that branches on category | `lookup_with_recovery()` handles each category as described in the table above |

The recovery loop is plain Python, with no model call, so it runs identically offline and live.

## Run

```bash
.venv/bin/python -m domain2_tool_design_mcp.task_2_2_structured_errors.good_example
.venv/bin/python -m domain2_tool_design_mcp.task_2_2_structured_errors.anti_pattern
.venv/bin/pytest domain2_tool_design_mcp/task_2_2_structured_errors
```
