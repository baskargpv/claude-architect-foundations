# Task 2.3 — Tool Distribution & Tool Choice

Lesson: <https://claudecertificationguide.com/learn/2-tool-design-mcp/2-3-tool-distribution-choice>

## What you need to know

- **Keep each agent to 4–5 tools, scoped to its role.** More tools means less reliable selection. Relevance matters too: an agent given tools outside its role tends to misuse them.
- **Pick the fix that matches the problem:**

  | Problem | Fix |
  |---|---|
  | Near-duplicate tools (same shape) | **Consolidate** into one parameterised tool (e.g. 22 tools → 4) |
  | A tool that reaches too far | **Constrain** it (`fetch_url` → `load_document`) |

  Consolidating doesn't replace least privilege; they solve different things.
- **A second MCP server doesn't help.** The client flattens every server's tools into one list.
- **`tool_choice` modes:**
  - `auto`: the model may answer in text.
  - `any`: the model must call some tool.
  - `{"type": "tool", "name": ...}`: the model must call that tool. Use it for a mandatory first step, then switch back to `auto`.
- **Scoped cross-role tool:** give an agent a narrow version of another role's ability (`verify_fact` on synthesis) so the common simple case skips coordinator round trips.

## Exam traps

| Trap | Demo |
|---|---|
| Routing every simple verification through the coordinator | `trap1_route_everything_via_coordinator`: 80 vs 12 round trips |
| `tool_choice: "auto"` when structured output is required | `trap2_auto_when_structure_required`: prose instead of a tool call |
| 18 tools on one agent | `trap3_one_agent_18_tools` |
| A generic `fetch_url` | `trap4_generic_fetch_url`: happily fetches the cloud metadata endpoint |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Forced `tool_choice` for a mandatory first step | `{"type": "tool", "name": "extract_metadata"}` | `claude-sonnet-5-5` **rejects** forced `tool_choice` (`any` / `tool`) with a 400. `first_turn_tool_choice()` tries the forced call, and on a 400 falls back to `auto` plus an explicit instruction, then checks the first call. The same applies on the exam: answer with forced selection. |

## Practice scenario

85% of the synthesis agent's fact checks are simple, but they all go through the coordinator. Fix?

**A: a scoped local `verify_fact` tool**, with complex checks still routed through the coordinator.

## Build exercise → code

| Step | Where |
|---|---|
| 1. Three roles with 4–5 tools each | `AGENT_TOOLS`, checked by `audit_toolsets()` |
| 2. A scoped `verify_fact` for simple single-source lookups | `verify_fact()` rejects multi-source or judgement checks with "route to the coordinator" |
| 3. Force `extract_metadata` first, then `auto` | `run_document_agent()` + `first_turn_tool_choice()` |
| 4. `load_document` that validates URLs | Only `https://docs.example.com/*.pdf` or `.md` is accepted |
| 5. End-to-end check that no agent goes outside its set | `end_to_end()`. Each agent's tools run through `ToolGuard`, which records any violation. |

## Run

```bash
.venv/bin/python -m domain2_tool_design_mcp.task_2_3_tool_distribution.good_example
.venv/bin/python -m domain2_tool_design_mcp.task_2_3_tool_distribution.anti_pattern
.venv/bin/pytest domain2_tool_design_mcp/task_2_3_tool_distribution
```
