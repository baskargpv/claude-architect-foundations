# Task 1.1 — Agentic Loop Lifecycle

## Theory

Messages API agents run a four-step loop:

1. Send the request with the **full** conversation history.
2. Inspect `stop_reason`.
3. `"tool_use"`: run the requested tool(s), append the results, send again.
4. `"end_turn"`: Claude is finished.

`stop_reason` is the **only** authoritative signal. Don't parse natural language or use content-type heuristics to decide when to stop.

Each tool-use iteration appends **two** entries to history:

| Entry | Role | Contains |
|---|---|---|
| Claude's response | `assistant` | All of `response.content`: text **and** `tool_use` blocks |
| Tool results | `user` | One new message with a `tool_result` block per call, each tagged with its `tool_use_id` |

`tool_use_id` matters most when Claude requests several tools in one turn, because it ties each result back to its request.

## Exam trap

| Anti-pattern | Why it's wrong |
|---|---|
| `response.content[0].type == "text"` as the exit check | Claude can return text **and** a `tool_use` block in the same response |
| Iteration cap as the primary stop | Cuts off real work (cap too low) or wastes cost (cap too high) — safety net only |
| `tool_choice: {"type": "any"}` for the whole loop | Forces a tool call every turn → `end_turn` unreachable → self-inflicted infinite loop |

Correct default: leave `tool_choice` unset (`"auto"`).

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| `tool_choice: any` for the whole loop | Wrong because it makes `end_turn` unreachable | Still wrong, but on `claude-sonnet-5-5` (this repo's live model) forced `tool_choice` (`any`/`tool`) is **rejected with a 400**, so you get an error instead of a loop. The mock shows the exam's behaviour; live mode prints the API error. |
| Exit check on `content[0]` | Breaks when text comes before `tool_use` | Still breaks. On current models the text between tool calls can arrive as a `thinking` progress block instead, so `content[0]` might not even be text. Either way, only `stop_reason` is reliable. |
| `stop_reason` values | `tool_use`, `end_turn` | Also `max_tokens`, `pause_turn` (server tools), `refusal`. The good loop surfaces these instead of guessing. |

## Code walkthrough

**`good_example.py`**

- `run_agent()` is the loop. Each request sends `messages` (the full history) and no `tool_choice`.
- It appends `response.content` as the assistant turn, then branches **only** on `response.stop_reason`.
- On `tool_use` it walks **every** block. `content[0]` may be text, so it doesn't stop there. It runs each tool and appends **one** user message holding every `tool_result`, each keyed by `tool_use_id`.
- `max_iterations` raises `IterationCapReached`, so it's a loud safety net and never the normal exit.
- `mock_model()` replies with `"Let me check both orders."` **plus** two parallel `tool_use` blocks in one response, which is exactly the case that breaks naive loops.
- Later tasks (1.4, 1.5) reuse `run_agent(tools=..., execute=...)`.

**`anti_pattern.py`**

- `run_agent_text_check()` sees the leading text block and returns. No tool runs, and the "answer" is just a preamble.
- `run_agent_forced_tool()` sends `tool_choice: any` every turn. The mock (like the exam's model) must call a tool every time, so only the cap stops it.
- `run_agent_cap_only()` runs a fixed number of rounds. The tools ran, but Claude never saw the results.

**`test_task_1_1.py`** checks:

- The good loop runs both tools, finishes on `end_turn`, and has history `user → assistant → user → assistant`.
- `tool_use_id`s correlate, `tool_choice` is never sent, and the cap raises.
- Each anti-pattern fails exactly as described.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_1_agentic_loop
```
