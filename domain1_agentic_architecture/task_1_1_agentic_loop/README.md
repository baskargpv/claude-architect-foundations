# Task 1.1 — Agentic Loops

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-1-agentic-loops>

## What you need to know

- An agentic loop is control flow written **in code**, not in a prompt. It repeats four steps:
  1. Send the full conversation history, including last round's tool results.
  2. Read `stop_reason`.
  3. On `"tool_use"`: run the tool(s), append the results as a new message, and send again.
  4. On `"end_turn"`: return the final answer.
- `stop_reason` is the **only** reliable loop-control signal.
- If tool results aren't appended to history, Claude never sees them.
- Claude picks tools from context, which is more adaptable than a hard-coded sequence. Where compliance must be guaranteed (money, security, regulation), enforce it in code instead (Task 1.4).

## Exam traps

| Trap | Why it fails | Demo |
|---|---|---|
| `response.content[0].type == "text"` means done | Claude often sends text **and** a `tool_use` block in one response | `trap1_content_type_check` |
| An iteration cap as the primary stop | Cuts off real work, or allows wasted iterations. Use it only as a safety net. | `trap2_cap_as_primary_stop` |
| Parsing phrases like "task complete" | Natural language is ambiguous. `stop_reason` isn't. | `trap3_parse_completion_phrase` |
| Forcing `tool_choice: "any"` | Forces a tool call even after Claude has finished, so the loop never ends | `trap4_force_tool_choice_any` |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Stop reasons | Only `tool_use` and `end_turn` | Also `pause_turn` (resend to continue a server-tool turn), `max_tokens`, `stop_sequence`, `refusal` and `model_context_window_exceeded`. Treat anything other than `end_turn` as "not finished, find out why". `run_agent()` handles every one of them. |
| Forcing `tool_choice: "any"` | Wrong because the loop never ends | Still wrong. On `claude-sonnet-5-5` (this repo's live model) forced `tool_choice` is **rejected with a 400**. Trap 4 shows the exam's behaviour in mock mode and prints the API error live. |

## Practice scenario

An agent ends early because its loop checks `content[0].type == "text"`. What should change?

**B: check `stop_reason`.** Continue on `tool_use` and stop on `end_turn`.

- A (a cap of 15) is only a safety net.
- C (`tool_choice: any`) makes finishing impossible.
- D (phrase parsing) is ambiguous.

Encoded as `PRACTICE` in `good_example.py`.

## Build exercise → code

The exercise is "Build a Multi-Tool Agent Loop" (45 min).

| Step | Where |
|---|---|
| 1. Two tools with JSON Schema inputs | `TOOLS`: `calculator` (safe AST evaluator, never `eval`) and a `web_search` stub |
| 2. A `while` loop that branches on `stop_reason` | `run_agent()` |
| 3. Handle `tool_use`: append the assistant turn, then **one** user message with every `tool_result` keyed by `tool_use_id` | `run_agent()`, `tool_use` branch |
| 4. Handle `end_turn`: return the final text | `run_agent()`, `end_turn` branch |
| 5. A prompt that chains tools | `QUESTION`: search the Eiffel Tower's height, then convert metres to feet. That takes 2 tool rounds, then `end_turn`. |
| 6. `MAX_ITERATIONS = 20` that only logs a warning | It sets `hit_safety_cap` and never triggers in normal runs |

`run_agent(tools=..., execute=..., system=..., history=...)` is reused by Tasks 1.4, 1.5 and 1.7.

**The mock model** reproduces the lesson's practical example. Its first reply is `"Let me look that up."` **plus** a `web_search` call, which is exactly what breaks the `content[0]` check.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_1_agentic_loop
```
