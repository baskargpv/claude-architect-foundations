# Task 1.3 — Subagent Invocation and Context Passing

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-3-subagent-invocation-context>

## What you need to know

**Spawning**

- The coordinator spawns subagents with the **`Task`** tool, renamed **`Agent`** in Claude Code v2.1.63; `Task` still works as an alias.
- It must be listed in the coordinator's `allowedTools`. Defining subagents under `agents` isn't enough on its own.
- Each **AgentDefinition** has three parts:
  - a description, used to decide when to invoke it
  - a system prompt
  - a toolset restricted to its role

**Context-passing rules.** Subagents see only what the coordinator writes into their prompt. So:

1. Pass complete findings from earlier agents.
2. Keep content (`claim`) separate from metadata (`source_url`, `document_name`, `page_number`, `confidence`, `retrieved_by`). Content without metadata can't be attributed.
3. State goals and quality criteria, not step-by-step procedures.

**Running subagents**

- **Parallel spawning:** put several Agent calls in **one** coordinator response for independent work.
- **`fork_session`** branches from a shared baseline (forks don't see each other).
- **`--resume`** continues the same line of work.

## Exam traps

| Trap | Demo |
|---|---|
| Assuming subagents can see the coordinator's history or other subagents' output | `trap1_assume_inherited_context`: "the document we found earlier" returns 0 findings |
| Blaming the synthesis agent for missing citations | `trap2_blame_synthesis`: metadata stripped at the handoff. A stronger synthesis prompt still leaves 4 of 4 claims unsourced. |
| Running independent subagents one after another | `trap3_sequential_invocation`: peak concurrency is 1 |
| Confusing `fork_session` with `--resume` | `trap4_confuse_fork_with_resume`: two "resumes" put approach B on top of approach A |

## Exam answer vs current docs

| | Exam answer | Current docs (Agent SDK subagents page) |
|---|---|---|
| `allowedTools` must include `Task` / `Agent` | Hard gate: no entry, no spawning | `allowed_tools` is an **auto-approve** list. Leaving `Agent` out doesn't remove the tool. The spawn goes to the permission check instead, which denies it in an unattended run. Claude can also always spawn the built-in `general-purpose` subagent. `spawn_decision()` returns `deny` when unattended and `ask` otherwise. The exam outcome is the same. |
| Tool name | `Task` | `Agent` in `tool_use` blocks. Still `Task` in the `system:init` tools list. Match both. |
| `fork_session` | A separate session control | A modifier on resume: `resume=<id>` + `fork_session=True` branches, and leaving out the flag appends. The CLI `--fork-session` works only with `--resume` / `--continue`. |

## Practice scenario

Synthesis output has unsourced claims, but both research subagents return correct URLs and pages. Root cause?

**B: the coordinator passes content without structured metadata.** A (give synthesis web access) and C (citation instructions) can't restore data that never arrived. D contradicts the setup.

## Build exercise → code

The exercise is "Implement Context Passing with Structured Metadata" (50 min).

| Step | Where |
|---|---|
| 1. Coordinator with `Agent` in `allowed_tools` and subagents under `agents` | `COORDINATOR_OPTIONS = AgentOptions(allowed_tools=["Agent"], agents=SUBAGENTS)`, checked by `spawn_decision()` |
| 2. Web search + document analysis `AgentDefinition`s with restricted tools | `SUBAGENTS`: web agent gets `web_search` only; doc agent gets `read_document` only (`scope_violations()` checks this) |
| 3. Structured findings | `Finding` (Pydantic). Its validator requires `source_url` for web findings, and `document_name` + `page_number` for document findings. |
| 4. Complete structured results to synthesis | `build_synthesis_prompt()` embeds the full findings JSON. The handoff happens **in code**, so metadata can't be dropped by a model paraphrasing it. |
| 5. Verify attribution and trace gaps | `verify_attribution()` checks each claim's line for its citation. `trace_attribution_gap()` diagnoses from what *reached* synthesis. |
| 6. Spawn both in one response | The coordinator is a tool-using agent with an `Agent` tool. Its first response contains **two** `Agent` calls. `Spawner.execute_parallel()` runs them concurrently and waits for both. |

Each subagent runs its own loop: Task 1.1's `run_agent`, with only its permitted tools.

`test_step6_research_subagents_run_in_parallel` uses a `threading.Barrier` that only passes if both subagents are running at the same time.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_3_subagent_context.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_3_subagent_context.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_3_subagent_context
```
