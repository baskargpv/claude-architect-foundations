# Task 3.5 — Iterative Refinement Techniques

Lesson: <https://claudecertificationguide.com/learn/3-claude-code-config/3-5-iterative-refinement>

## What you need to know

| Situation | Technique |
|---|---|
| Known target, but prose is read inconsistently | **2–3 concrete input/output examples** |
| A complex transformation with many edge cases | **Test-driven iteration**: write tests first and share failures as "Expected X, got Y" |
| An unfamiliar domain where you don't know the target | **Interview pattern**: Claude asks questions before implementing |
| Issues that interact (fixing A changes B) | **Batch** them in one message |
| Independent issues | Send them **sequentially** |

More precise prose is never the fix for inconsistent interpretation, because it still relies on interpretation.

## Exam traps

| Trap | Demo |
|---|---|
| Refining the prose when interpretation is inconsistent | `trap1_more_precise_prose`: still varies across runs |
| Not batching interacting issues | `trap2_sequential_for_interacting_issues`: fixes get redone |
| Confusing the interview pattern with examples | `trap3_wrong_technique` |

## Exam answer vs current docs

No difference.

## Practice scenario

A prose-described transformation is interpreted differently each run. Try first?

**A: 2–3 concrete input/output examples.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. Prose only, run 3 times, note the variation | `runs(client, TASK)`: 3 different formats |
| 2. Add 2–3 examples, run 3 times | `with_examples()`: 1 consistent output |
| 3. Tests (happy path, edge, error) and iterate on failures | `TESTS`, `tdd_loop()`: 2 failures, then 0 once the failure text is fed back |
| 4. The interview pattern | `interview()` returns Claude's clarifying questions |
| 5. Three interdependent issues in one message | `plan_feedback()` batches the interacting issues and sends independent ones separately |

**About the mock.** Its drift for prose-only prompts is **simulated**: each run picks a different reasonable format. It shows what the technique fixes; it isn't a measurement.

## Run

```bash
.venv/bin/python -m domain3_claude_code_config.task_3_5_iterative_refinement.good_example
.venv/bin/python -m domain3_claude_code_config.task_3_5_iterative_refinement.anti_pattern
.venv/bin/pytest domain3_claude_code_config/task_3_5_iterative_refinement
```
