# Task 4.2 — Few-Shot Prompting

Lesson: <https://claudecertificationguide.com/learn/4-prompt-engineering/4-2-few-shot-prompting>

## What you need to know

- **Few-shot examples are the first tool for inconsistent output.** Reach for them when:
  - formatting is inconsistent despite detailed instructions
  - judgement on ambiguous cases is inconsistent
  - fields come back empty even though the data is there
- **Use 2–4 targeted examples, each with reasoning.** The reasoning should say why this choice over the plausible alternatives, so the model learns the principle and generalises.
- **Cover the cases that actually fail**, e.g. narrative text if that's where extraction breaks.
- **Match the problem to the fix:**

| Problem | Fix |
|---|---|
| Inconsistent formatting | Few-shot |
| Malformed JSON | tool_use with a schema (4.3) |
| Made-up values for missing fields | Nullable schema fields (4.3) |
| Wrong tool picked | Descriptions first (2.1), then few-shot |
| Sum doesn't match total | Validation-retry loop (4.4) |

## Exam traps

| Trap | Demo |
|---|---|
| "Add more detailed instructions" when output is inconsistent | `trap1_more_instructions`: still 27% empty |
| Thinking few-shot only teaches literal pattern-matching | `trap2_examples_without_reasoning`: the same examples without reasoning don't generalise |
| Confidence thresholds to fix inconsistent judgement | `trap3_confidence_threshold` |

## Exam answer vs current docs

No difference.

## Practice scenario

Values are read from tables but missed in narrative paragraphs, with detailed instructions already in place.

**C: add few-shot examples covering both tables and narrative.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A detailed-instructions baseline on 10 varied documents | `INSTRUCTIONS`, `DOCS` (3 table, 4 narrative, 3 mixed) |
| 2. Record which fields fail on which structure | `run()` → `empty_by_structure`: all the failures are in narrative documents |
| 3. Three examples (table, narrative, mixed), each with reasoning | `FEW_SHOT` |
| 4. Re-run and compare | The empty rate drops from 27% to 3% |
| 5. Note what few-shot didn't fix | `remaining_issues()`: `n4` truly has no sample size, which needs a nullable schema field, not more examples |

**About the mock.** Missing values in prose without a narrative example (plus its reasoning) is **simulated**, to reproduce the lesson's scenario.

## Run

```bash
.venv/bin/python -m domain4_prompt_engineering.task_4_2_few_shot.good_example
.venv/bin/python -m domain4_prompt_engineering.task_4_2_few_shot.anti_pattern
.venv/bin/pytest domain4_prompt_engineering/task_4_2_few_shot
```
