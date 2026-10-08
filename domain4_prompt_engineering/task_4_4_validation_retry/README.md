# Task 4.4 — Validation, Retry, and Feedback Loops

Lesson: <https://claudecertificationguide.com/learn/4-prompt-engineering/4-4-validation-retry-loops>

## What you need to know

- **A retry needs three things:** the **original document**, the **failed extraction**, and the **specific validation error**. A bare retry repeats the mistake.
- **What retries can and can't fix:**
  - **Can fix:** format mismatches, structure errors, misplaced values, missed line items.
  - **Can't fix:** information absent from the source, or held in a document you never provided. Flag those for human review, or return null.
- **Self-checking schemas:**
  - `calculated_total` alongside `stated_total`
  - a `conflict_detected` boolean
  - `detected_pattern`, so dismissal rates can show which prompts need work
- **Schema vs semantics:** `tool_use` removes syntax errors. Semantic errors (sums, date order) need validators and a retry loop.
- **Pydantic does both jobs.** Parsing enforces structure and validators enforce cross-field rules, and both report through one `ValidationError` with per-field messages.

## Exam traps

| Trap | Demo |
|---|---|
| Assuming retries always work | `trap1_retry_absent_information`: 3 retries, still no department |
| Retrying without the specific error | `trap2_retry_without_error`: the same mistake every time |
| Schema validation alone | `trap3_schema_only`: schema-valid with a £50 gap |
| Treating Pydantic as redundant once tool_use has a schema | `trap4_pydantic_redundant`: swapped dates pass the schema |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Server-side enforcement | — | `strict: true` on tools and `client.messages.parse(...)` (returning validated Pydantic objects) enforce the schema server-side. **Neither replaces your semantic validators.** The site's lesson shows `parse(..., output_format=...)`; current SDK docs use `output_config.format`, the form this repo uses. |

## Practice scenario

Document A's sum is off by £50; Document B's department isn't in the source.

**C: retry A with the discrepancy error; flag B for human review.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. An extraction tool with calculated/stated totals, a conflict flag and `detected_pattern` | `SCHEMA`, `Invoice` |
| 2. Validation for completeness, sums, enums and date order, with specific messages | `Invoice.semantics()`, `validate()` |
| 3. A retry loop sending the document, the failed extraction and the error | `process()` |
| 4. 5 documents: 2 fixable, 3 with absent information | A (missed page-2 line) and B (swapped dates) are fixed on retry. C, D and E go to `human_review` with **no** retry. |
| 5. `detected_pattern` dismissal rates | `dismissal_rates()` |

## Run

```bash
.venv/bin/python -m domain4_prompt_engineering.task_4_4_validation_retry.good_example
.venv/bin/python -m domain4_prompt_engineering.task_4_4_validation_retry.anti_pattern
.venv/bin/pytest domain4_prompt_engineering/task_4_4_validation_retry
```
