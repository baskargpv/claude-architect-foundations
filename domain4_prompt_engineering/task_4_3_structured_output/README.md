# Task 4.3 — Structured Output with Tool Use

Lesson: <https://claudecertificationguide.com/learn/4-prompt-engineering/4-3-structured-output>

## What you need to know

- **`tool_use` with a JSON schema is the most reliable approach.** It removes syntax errors (missing brackets, trailing commas). Prompt-based JSON can still break in production.
- **`tool_choice` options:**
  - `auto` (default): the model may answer in text.
  - `any`: the model must call some tool. Use it when the document type is unknown.
  - `{"type": "tool", "name": ...}`: the model must call that tool. Use it for mandatory steps.

  It applies **per request**: drop it after a forced call, or the model will repeat that call.
- **A schema guarantees shape, never correctness.** Sums that don't add up, values in the wrong field, and invented values all pass it.
- **Schema design:**
  - Make fields nullable when a source may lack them. This is the main defence against fabrication.
  - Keep `required` to fields that are always present.
  - Add an `unclear` enum value, and `other` plus a detail string.
  - Put formatting rules in the prompt.

## Exam traps

| Trap | Demo |
|---|---|
| Believing tool_use prevents all extraction errors | `trap1_schema_is_not_correctness`: 3 schema-valid but wrong records |
| Confusing `auto` with `any` | `trap2_auto_for_structured_output`: d4 comes back as prose |
| Making every field required | `trap3_all_required`: invented `due_date` and `po_number` |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Reliability hierarchy | tool_use + schema > prompt-based JSON | Also `strict: true` on tools and `output_config.format` for the response. **On the exam, answer with the two tiers.** |
| `tool_choice` modes | Three | A fourth, `{"type": "none"}`, which is the default when no tools are passed. Also, `claude-sonnet-5-5` **rejects** forced `any`/`tool` with a 400. `create()` falls back to `auto` plus an explicit instruction. |

## Practice scenario

Every field is required, and the model invents dates and amounts.

**A: make those fields optional or nullable.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A schema with 3 required fields, 3 nullable, and an enum with `unclear`/`other` plus a detail string | `EXTRACT_INVOICE` |
| 2. `auto`: find a text reply | `extract_all(client)` returns prose for `d4` |
| 3. `any`: every response is a tool call | `extract_all(client, {"type": "any"})` |
| 4. Force a named tool | `{"type": "tool", "name": "extract_receipt"}` runs even for an invoice |
| 5. 5 documents (3 complete, 2 missing fields) | `d4` and `d5` return `null`, not invented values; `d3` → `other` + `"map licence"` |

## Run

```bash
.venv/bin/python -m domain4_prompt_engineering.task_4_3_structured_output.good_example
.venv/bin/python -m domain4_prompt_engineering.task_4_3_structured_output.anti_pattern
.venv/bin/pytest domain4_prompt_engineering/task_4_3_structured_output
```
