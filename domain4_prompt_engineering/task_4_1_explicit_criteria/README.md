# Task 4.1 — System Prompts with Explicit Criteria

Lesson: <https://claudecertificationguide.com/learn/4-prompt-engineering/4-1-system-prompts>

## What you need to know

- **Vague instructions give no decision boundary.** "Be conservative" or "only report high-confidence findings" don't tell the model what to do.
- **Use explicit categories instead:** report bugs and security issues; skip style and local patterns. Flag a comment only when its claimed behaviour contradicts the code.
- **One noisy category ruins trust in all of them.** A high false-positive rate in one category makes people distrust every category. Temporarily disable the noisy one while you refine its prompt.
- **Define severity with code examples, not prose.** Prose definitions give inconsistent classification.
- **Self-reported confidence is poorly calibrated.** Use explicit criteria first and confidence routing second (Task 4.6).

## Exam traps

| Trap | Demo |
|---|---|
| "Be conservative" / "high-confidence only" as the fix | `trap1_vague_instructions`: 40% false positives remain |
| Confidence thresholds as the fix for false positives | `trap2_confidence_threshold`: keeps 2 false positives and drops a real bug reported at 0.6 |
| Keeping a noisy category active while fixing it | `trap3_keep_noisy_category`: developers stop reading every finding |

## Exam answer vs current docs

No difference.

## Practice scenario

A 40% false-positive rate on documentation-mismatch findings, and developers now ignore everything.

**A: temporarily disable that category while refining it** with explicit criteria and code examples.

## Build exercise → code

| Step | Where |
|---|---|
| 1. A vague prompt over 5 snippets (bug, security, style, two comments) | `VAGUE_PROMPT`, `SNIPPETS`, `evaluate()`: 40% false positives, inconsistent severity |
| 2. Explicit report/skip categories and the comment trigger | `EXPLICIT_PROMPT` |
| 3. A code example per severity level | The `Critical example:` / `Minor example:` lines |
| 4. Compare false positives and consistency | Explicit prompt: 0% false positives, 3 true findings, stable severity |
| 5. Disable categories above 25% false positives | `active_categories()` |

**About the mock reviewer.** It's **simulated**: vague prompts over-flag and their severity drifts, explicit prompts don't. That reproduces the lesson's claims for the demo.

## Run

```bash
.venv/bin/python -m domain4_prompt_engineering.task_4_1_explicit_criteria.good_example
.venv/bin/python -m domain4_prompt_engineering.task_4_1_explicit_criteria.anti_pattern
.venv/bin/pytest domain4_prompt_engineering/task_4_1_explicit_criteria
```
