# Task 1.6 — Task Decomposition Strategies

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-6-task-decomposition>

## What you need to know

| Pattern | Good for | Trade-off |
|---|---|---|
| **Fixed sequential pipeline** (prompt chaining) | Steps known in advance: code review, document processing, extraction, compliance checks | Consistent and easy to debug, but can't adapt mid-run |
| **Dynamic adaptive decomposition** | Open-ended work: legacy exploration, security audits, research, debugging unfamiliar systems | More thorough, but less predictable in time and cost, and harder to debug |

- **A code review pipeline is fixed:**
  1. a per-file local pass (style, bugs, complexity)
  2. a cross-file integration pass (data flow, API consistency, import chains)
  3. a unified report
- **Attention dilution:** too many items in one pass gives uneven depth.
  - Early files get detail, later ones get skimmed.
  - The same pattern is flagged in one file and approved in another.
  - Obvious bugs are missed while minor style issues are caught.
- **The fix is structural:** per-item passes plus one integration pass. It's not about model size or prompt wording.
- **The lesson's 14-file example:**
  - Files 1–5 got detailed feedback, 6–9 moderate, 10–14 superficial (the null-pointer and SQL-injection bugs were missed).
  - A `forEach` was flagged in file 3 and ignored in identical file 11.

## Exam traps

| Trap | Demo |
|---|---|
| Picking the pattern that sounds more sophisticated instead of matching the task | `trap1_pattern_by_sophistication` vs `choose_pattern()` |
| A more powerful model or larger context window as the dilution fix | `trap2_bigger_model`: 4 issues vs multi-pass's 8 |
| A single pass with better prompts as "equivalent" to multi-pass | `trap3_better_prompt`: same drop-off |
| Fixed pipelines for open-ended investigation | `trap4_fixed_pipeline_for_exploration`: tests written on top of untested dependencies |
| Batching files without a cross-file integration pass | `trap5_batching_without_integration`: all 8 local issues found, the cross-batch contract bug missed |

## Exam answer vs current docs

No difference.

## Practice scenario

The 14-file review problem. Root cause and fix?

**D: per-file local passes plus a separate cross-file integration pass.**

- A (batches of 5) still misses issues that span batches.
- B (a bigger window) and C (a stronger prompt) don't change how attention is spread.

## Build exercise → code

The exercise is "Build a Multi-Pass Code Review Pipeline" (60 min).

| Step | Where |
|---|---|
| 1. A review agent over a directory of 10+ JS files | `load_repo()` reads `sample_repo/` (12 files) and refuses fewer than 10 |
| 2. A single-pass baseline | `single_pass_review()` |
| 3. Per-file passes with bug count, severity and line references | `local_review()`, one call per file (each prompt holds exactly one file). It also reports exports, what the file uses from other files, and its query style. |
| 4. A cross-file integration pass over the per-file summaries | `integration_review()`. It finds `10_profile.js` reading `user.id` when `getUser()` returns `userId`, and SQL that's parameterized in two files but concatenated in two others. |
| 5. Compare the two | `compare()`: single pass 4 issues (misses files 8, 11, 12) vs multi-pass 8, with cross-file issues found only by the integration pass |
| 6. Record dilution artefacts | `dilution_artefacts()`. Single pass: `forEach` and SQL injection flagged in file 3 but approved in file 11, null-deref flagged in file 5 but not 12. Multi-pass: none. |

**The lesson's dynamic example.** `adaptive_test_plan()` maps the import graph and plans tests by impact. When it discovers that `09_invoice.js` depends on untested `06_orders.js` → `04_db.js`, it re-plans so those are tested first.

**About the mock reviewer.** It's a deterministic static analyser (regex rules), so it can only see what's in the prompt. That keeps the per-file and integration results honest.

Its single-pass behaviour (full depth on files 1–5, critical issues only on 6–9, nothing after that) is **simulated** dilution, reproducing the lesson's symptom. It's labelled as such in the code.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_6_task_decomposition.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_6_task_decomposition.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_6_task_decomposition
```
