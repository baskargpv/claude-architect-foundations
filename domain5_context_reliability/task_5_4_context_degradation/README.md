# Task 5.4 — Codebase Exploration & Context Degradation

Lesson: <https://claudecertificationguide.com/learn/5-context-management/5-4-codebase-exploration>

## What you need to know

- **What degradation looks like:** the model loses track of specific earlier findings as verbose output piles up. The symptom: "the typical repository pattern" instead of "`OrderRepository` in `src/repos/order.ts` caches `findById`".
- **It isn't a token-limit problem**, so a bigger window doesn't fix it.
- **Scratchpad files:** write key findings (classes, paths, dependency chains) to a file and read it before later steps. Start one from the beginning of any long exploration.
- **Subagent delegation:** verbose exploration happens in isolated contexts, and only structured summaries come back. The main benefit is context isolation; parallelism is secondary.
- **Summary injection:** seed phase-2 subagent prompts with the phase-1 findings, so they don't start cold and repeat work.
- **Use `/compact` proactively** to protect context quality, not just when the limit is hit.
- **Crash recovery:** a JSON state manifest (`sessionId`, `phase`, `exploredPaths`, `keyFindings`, `nextSteps`) that the coordinator loads on resume.

## Exam traps

| Trap | Demo |
|---|---|
| A bigger context window to fix degradation | `trap1_bigger_window`: still "typical repository pattern" |
| Treating delegation as only about parallelism | `trap2_inline_exploration`: the main context fills with raw output |
| Restarting without saving state | `trap3_restart_without_saving` |
| `/compact` only at the limit | `trap4_compact_only_at_limit`: 25 turns spent degraded |

## Exam answer vs current docs

No difference.

## Practice scenario

The agent drifts into generic "typical patterns" after several modules.

**B: scratchpad files with key findings.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A coordinator delegating focused tasks to subagents that return summaries | `TASKS`, `run_subagent()`: 40 lines of raw reading stay in the subagent |
| 2. Write findings to a scratchpad and read it before each step | `Scratchpad` |
| 3. Inject the phase-1 summary into phase-2 prompts | `explore()` → `phase2_prompt` |
| 4. Export and load a JSON state manifest | `export_manifest()`, `load_manifest()` |
| 5. Compare with and without the scratchpad | `answer_later_question()`: specific class and path vs "typical repository pattern" |

**About the mock.** The degradation is **simulated**: without the scratchpad in context, the mock loses the specific names.

## Run

```bash
.venv/bin/python -m domain5_context_reliability.task_5_4_context_degradation.good_example
.venv/bin/python -m domain5_context_reliability.task_5_4_context_degradation.anti_pattern
.venv/bin/pytest domain5_context_reliability/task_5_4_context_degradation
```
