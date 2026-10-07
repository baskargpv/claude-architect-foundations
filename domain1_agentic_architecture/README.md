# Domain 1 — Agentic Architecture & Orchestration (27%)

This is the most heavily weighted domain on the exam blueprint. It covers Task Statements 1.1–1.7.

| Task | One-line summary |
|---|---|
| [1.1 Agentic Loop](task_1_1_agentic_loop/) | `stop_reason` is authoritative; nothing else decides the loop |
| [1.2 Hub-and-Spoke](task_1_2_hub_and_spoke/) | Breadth-first decomposition + strict subagent isolation, all through one hub |
| [1.3 Context Passing](task_1_3_context_passing/) | Never let structured metadata become plain text before it reaches synthesis |
| [1.4 Prerequisite Gates](task_1_4_prerequisite_gates/) | Code enforces what prompts can only request |
| [1.5 SDK Hooks](task_1_5_sdk_hooks/) | Same rule as 1.4, formalised as hooks; block in Pre, normalise in Post |
| [1.6 Task Decomposition](task_1_6_task_decomposition/) | Match the pattern to whether the plan is knowable up front; fix dilution with multi-pass, not a bigger model |
| [1.7 Session State](task_1_7_session_state/) | Stale history beats good intentions; start fresh and inject only what's still true |

## Cross-cutting exam traps

| Trap | Why it's wrong | Task |
|---|---|---|
| `response.content[0].type == "text"` as the exit check | A `tool_use` block can follow text in the same response | 1.1 |
| Iteration cap as the primary stop condition | Cuts off real work or wastes cost; safety net only | 1.1 |
| `tool_choice: "any"` for the whole loop | `end_turn` becomes unreachable | 1.1 |
| Rigid "exactly N subtopics" prompt | Forces merging or dropping categories | 1.2 |
| Stripping metadata before synthesis (`.map(f => f.claim)`) | The single root cause of unattributed claims | 1.3 |
| Prompt-only enforcement for financial/compliance actions | ~92% reliable isn't 100% | 1.4 / 1.5 |
| PostToolUse used to block an action | The handler already ran | 1.5 |
| Fixed pipeline for open-ended investigation | Can't adapt to unexpected findings | 1.6 |
| Batching without an integration pass | Solves only within-batch dilution | 1.6 |
| Bigger model / larger context as the dilution fix | Dilution is architectural | 1.6 |
| `--resume` after files changed | Stale tool results remain in history | 1.7 |
| `fork_session` to fix stale context | The fork copies the same stale history | 1.7 |
| Full re-exploration when only a few files changed | Targeted re-analysis is the right move | 1.7 |

## Shared building block

The Task 1.1 `run_agent()` loop is reused by Tasks 1.4, 1.5 and 1.7. Each passes its own `tools`, an `execute` dispatcher (where gates and hooks live) and, for 1.7, prior `history`.

```bash
.venv/bin/pytest domain1_agentic_architecture
```
