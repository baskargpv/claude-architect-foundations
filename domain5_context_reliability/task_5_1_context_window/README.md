# Task 5.1 — Context Window Management

Lesson: <https://claudecertificationguide.com/learn/5-context-management/5-1-context-window-management>

## What you need to know

- **Summarisation destroys specifics.** "$247.83 for order #8891 placed March 3rd" becomes "a recent order". Keep a **persistent case-facts block** (customerId, orderId, orderDate, refundAmount, status, itemDescription) in every prompt, outside the summarised history, with one entry per issue.
- **Lost in the middle:** models use the start and end of long inputs reliably. The fix is structural: a key-findings summary at the top plus section headers.
- **Trim tool results before they enter history.** An order lookup may return 40+ fields when you need 5.
- **The API is stateless**, so every request carries the full history. Don't selectively truncate it; use case facts and summaries instead.
- **Upstream agents should return structured findings**, not their reasoning.
- **Prompt caching:** static content first, then a `cache_control` breakpoint, then dynamic content. The details are out of exam scope.

## Exam traps

| Trap | Demo |
|---|---|
| Treating summarisation as safe for transactional data | `trap1_summarisation_only`: "your recent refund request" |
| "Pay attention to everything" for lost-in-the-middle | `trap2_attention_instruction` (**simulated** position effect) |
| Keeping full tool results "in case they're needed later" | `trap3_untrimmed_results`: about 10× the characters |
| Selectively truncating history | `trap4_truncate_history`: leaves an orphaned `tool_result` |

## Exam answer vs current docs

No difference. The lesson marks prompt-caching mechanics (TTLs, breakpoint limits) as out of exam scope.

## Practice scenario

After summarisation the agent loses $247.83 and #8891.

**B: a persistent case-facts block.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. Extract transactional facts from tool output | `extract_case_facts()` |
| 2. Prepend the facts block to every prompt | `build_system()`, sent as `system` on every turn |
| 3. Trim the 40+ field lookup | `trim()` → 5 fields |
| 4. A 6-turn conversation, summarised after turn 4 | `run_conversation()`: the final answer still has $247.83, #8891 and the date |
| 5. Key-findings summary first, then labelled sections | `aggregate()` |

**About the mock summariser.** It **simulates** what summarisation does to specifics: it keeps the gist and drops the numbers.

## Run

```bash
.venv/bin/python -m domain5_context_reliability.task_5_1_context_window.good_example
.venv/bin/python -m domain5_context_reliability.task_5_1_context_window.anti_pattern
.venv/bin/pytest domain5_context_reliability/task_5_1_context_window
```
