# Task 3.4 — Plan Mode vs Direct Execution

Lesson: <https://claudecertificationguide.com/learn/3-claude-code-config/3-4-plan-mode-execution>

## What you need to know

- **"The decision is not about difficulty but about ambiguity."**
- **Use plan mode for:**
  - large restructures
  - several valid approaches
  - architectural decisions
  - multi-file changes
  - code that needs exploring first

  It reads and proposes, and writes **nothing** until the plan is approved.
- **Entering plan mode:** `claude --permission-mode plan`, Shift+Tab until the status bar shows plan mode, or a `/plan` prefix on the prompt. Writing "in plan mode" in the prompt body does nothing.
- **Use direct execution for a known fix:** a single-file bug with a clear stack trace, a validation check, a config value.
- **Hybrid:** plan first to investigate, then execute directly. For example, a 30-file logging migration.
- **The Explore subagent** runs discovery in isolation and returns a summary, keeping the main context clean.
- **If the task already states its complexity**, choose plan mode up front.

## Exam traps

| Trap | Demo |
|---|---|
| Direct execution for multi-file architectural changes | `trap1_direct_for_architecture`: real edits to unwind |
| Plan mode for a single-file bug with a clear stack trace | `trap2_plan_for_clear_bug`: 3 overhead steps |
| Not recognising the plan-then-execute hybrid | `trap3_plan_or_direct_only` |
| Starting direct and switching only when complexity "emerges" | `trap4_switch_late`: the complexity was stated up front |

## Exam answer vs current docs

No difference on the lesson.

## Practice scenario

Monolith → microservices, a null pointer with a clear stack trace, and a 30-file logging migration.

**A: plan mode for (1) and (3), direct execution for (2).**

## Build exercise → code

| Step | Where |
|---|---|
| 1. Plan a complex multi-file task without changing files | `PlanModeSession`: reads are allowed, and writes are blocked until `approved` |
| 2. Fix a simple bug directly | `choose_mode()` → `"direct"` |
| 3. Plan a migration, then execute file by file | `plan_then_execute()` |
| 4. Verbose discovery through an Explore subagent | `explore()`: the main history receives an 85-char summary, not the 30-line listing |
| 5. A decision framework: 4+ plan criteria and 3 direct, with examples | `PLAN_CRITERIA`, `DIRECT_CRITERIA`, `choose_mode()`, `entered_plan_mode()` |

## Run

```bash
.venv/bin/python -m domain3_claude_code_config.task_3_4_plan_mode.good_example
.venv/bin/python -m domain3_claude_code_config.task_3_4_plan_mode.anti_pattern
.venv/bin/pytest domain3_claude_code_config/task_3_4_plan_mode
```
