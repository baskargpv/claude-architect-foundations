# Task 1.2 — Multi-Agent Orchestration

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-2-orchestration-patterns>

## What you need to know

- **Hub-and-spoke:** one coordinator at the centre, specialised subagents (web search, document analysis, synthesis …) around it.
- **The coordinator** does all the managing. It:
  - decomposes the task and picks which subagents to use (not always the whole pipeline)
  - splits research scope so subagents don't duplicate sources
  - passes context to each subagent
  - aggregates results, handles errors and routes information
  - runs refinement loops that re-delegate to fill gaps
- **All subagent-to-subagent traffic goes through the hub.** That gives you observability, consistent error handling and control over what each agent sees.
- **Subagents start with isolated context.** They don't get the coordinator's system prompt or history, other subagents' results, or shared memory, unless the coordinator writes it into their prompt.
- **Each call is independent.** A repeat call remembers nothing.
- **Narrow decomposition failure:** if whole categories are missing from the output, the cause is the coordinator's decomposition. Better queries, a stronger synthesis agent or more subagents don't fix it.
- **Diagnosis rule:** when output is wrong or incomplete, check what the coordinator gave the subagent first.

## Exam traps

| Trap | Demo |
|---|---|
| Blaming downstream subagents (e.g. "tune the queries") when decomposition was too narrow | `trap1_blame_downstream` |
| Assuming subagents share memory or inherit the coordinator's history | `trap2_assume_shared_memory` |
| Direct subagent-to-subagent communication "for efficiency" | `trap3_direct_subagent_communication`: the hub's log stays empty, and the failure goes unhandled |
| Adding more subagents to fix a decomposition problem | `trap4_add_more_subagents`: 4 subagents, still only solar and wind |
| Not tracing the failure back to the coordinator's input | `trap5_wrong_failure_trace` vs `trace_coverage_failure()` |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Subagent-to-subagent communication | Always wrong; everything goes through the hub | In current Claude Code a subagent can spawn its own subagents (nested delegation, 3 levels by default). "No direct communication" is an exam simplification, not a product limit. On the exam, treat direct communication as wrong. |

## Practice scenario

A "renewable energy technologies" report covers only solar and wind, though every subagent did strong work. Root cause?

**D: the coordinator only ever assigned solar and wind.** Options A–C blame subagents that never received the other categories.

## Build exercise → code

The exercise is "Build a Hub-and-Spoke Research Coordinator" (60 min).

| Step | Where |
|---|---|
| 1. A coordinator that owns decomposition, selection and aggregation | `Coordinator`, with `COORDINATOR_SYSTEM` |
| 2. At least 5 subtopics covering the full breadth | `decompose()` returns solar, wind, geothermal, tidal, biomass and nuclear fusion |
| 3. Web search + document analysis subagents with explicit context | `build_subagent_prompt()` restates goal, subtopic and earlier results on every call. The document agent receives the web agent's findings **through the coordinator**. |
| 4. Aggregate and label coverage | `assess_coverage()`: ≥3 sourced findings = well-covered, 1–2 = partial, 0 = missing |
| 5. A refinement loop | Only partial or missing subtopics get a targeted follow-up, sent to whichever subagent has contributed fewer findings. The loop exits when coverage meets the threshold. `max_iterations` is the safety net. |
| 6. Test with renewable energy | `test_step6_all_six_energy_types_well_covered`. `trace_coverage_failure()` names the origin of any gap. |

**Mock yields:**

- On the first pass, *tidal* comes back missing and *nuclear fusion* partial.
- Fusion is fixed in one follow-up round. Tidal needs two, so `iterations == 2`.
- `routing_log` records every hub-to-spoke and spoke-to-hub message.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_2_orchestration.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_2_orchestration.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_2_orchestration
```
