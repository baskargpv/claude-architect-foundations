# Task 2.1 — Tool Interface Design

Lesson: <https://claudecertificationguide.com/learn/2-tool-design-mcp/2-1-tool-schema-design>

## What you need to know

- **Descriptions drive tool choice.** Tool descriptions are the main thing the model uses to pick a tool. One-liners cause misrouting.
- **A good description has five parts:**
  1. purpose
  2. expected inputs and formats
  3. example queries
  4. edge cases and limits
  5. an explicit boundary against similar tools
- **Fix order for misrouting:** expand the descriptions first. Few-shot examples, a routing classifier, or merging tools are worse first steps.
- **Split broad tools into narrow ones.** For example, `analyze_document` → `extract_data_points`, `summarize_content`, `verify_claim_against_source`.
- **Renaming fixes overlap too.** A tool can be renamed (`analyze_content` → `extract_web_results`) without changing its implementation.
- **Reread the system prompt.** Keyword instructions like "always check customer details" can override good descriptions.
- **Scope:** descriptions fix confusion between a handful of tools. Past ~4–5 tools per agent, the toolkit itself is the problem (Task 2.3).

## Exam traps

| Trap | Demo |
|---|---|
| Few-shot examples to fix misrouting from minimal descriptions | `trap1_few_shot`: 70%, with extra tokens on every call |
| A routing classifier as the first step | `trap2_routing_classifier`: misses tracking IDs nobody wrote a rule for |
| Merging the tools as the first step | `trap3_consolidate_first`: 1 tool, still 30% correct |
| Ignoring the system prompt after fixing descriptions | `trap4_ignore_system_prompt`: 40% despite good descriptions |

## Exam answer vs current docs

No difference.

## Practice scenario

The agent calls `get_customer` for "check my order #12345". Best first step?

**C: expand both descriptions** with inputs, examples, edge cases and boundaries.

## Build exercise → code

| Step | Where |
|---|---|
| 1. Two MCP tools with ambiguous one-line descriptions | `build_server(VAGUE)`, a real in-process `mcp` server |
| 2. Run 10 queries and log which tool gets picked | `QUERIES`, `evaluate()`. Vague descriptions: 30%. |
| 3. Rewrite the descriptions with all five parts | `CLEAR` |
| 4. Re-run and compare | 100% |
| 5. Review the system prompt for keyword instructions | `find_keyword_conflicts()` |

**About the mock model.** It reads the tool descriptions the same way the real model would:

- If a description's `Input:` section claims the query's identifier format, it picks that tool.
- Otherwise it falls back to word overlap between the query and the descriptions.

Live mode sends the same tool definitions to Claude.

## Run

```bash
.venv/bin/python -m domain2_tool_design_mcp.task_2_1_tool_interface_design.good_example
.venv/bin/python -m domain2_tool_design_mcp.task_2_1_tool_interface_design.anti_pattern
.venv/bin/pytest domain2_tool_design_mcp/task_2_1_tool_interface_design
```
