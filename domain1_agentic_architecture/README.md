# Domain 1 — Agentic Architecture & Orchestration (27%)

Source: <https://claudecertificationguide.com/learn/1-agentic-architecture>

Each task follows the same layout:

- `good_example.py` implements the lesson's **Build Exercise** step by step.
- `anti_pattern.py` has one runnable function per **Exam Trap**.
- The tests check every step, every trap, and the practice scenario's answer.

| Task | Build exercise | Traps |
|---|---|---|
| [1.1 Agentic Loops](task_1_1_agentic_loop/) | Multi-tool agent loop (calculator + web search, `MAX_ITERATIONS = 20`) | 4 |
| [1.2 Multi-Agent Orchestration](task_1_2_orchestration/) | Hub-and-spoke research coordinator ("renewable energy technologies", 6 energy types) | 5 |
| [1.3 Subagent Invocation and Context Passing](task_1_3_subagent_context/) | `Agent` tool in `allowed_tools`, scoped subagents, structured findings, parallel spawns | 4 |
| [1.4 Workflow Enforcement and Handoff](task_1_4_workflow_enforcement/) | Prerequisite gate on `process_refund`, structured handoff, multi-concern request | 4 |
| [1.5 Agent SDK Hooks](task_1_5_sdk_hooks/) | Real MCP server; PostToolUse normalisation; PreToolUse refund, AML and discount policies | 4 |
| [1.6 Task Decomposition Strategies](task_1_6_task_decomposition/) | Multi-pass code review over a 12-file JS repo, plus an adaptive test plan | 5 |
| [1.7 Session State and Resumption](task_1_7_session_resumption/) | Named sessions on a 10-file codebase; resume vs fork vs fresh start | 4 |

## Shared building block

Task 1.1's `run_agent()` loop is reused by Tasks 1.3 (each subagent), 1.4, 1.5 and 1.7. Each passes in:

- its own `tools`
- an `execute` dispatcher (where gates and hooks live)
- a `system` prompt
- optionally, prior `history`

```bash
.venv/bin/pytest domain1_agentic_architecture
```
