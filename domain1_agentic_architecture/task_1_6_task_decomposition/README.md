# Task 1.6 — Task Decomposition Strategies

## Theory

| Pattern | Best for | Limitation |
|---|---|---|
| **Fixed sequential pipeline** | Structured tasks whose steps are known in advance: code review, document extraction, compliance checks | Can't adapt to unexpected findings mid-execution |
| **Dynamic adaptive decomposition** | Open-ended investigation whose scope is unknown at the start: legacy-codebase exploration, security audits, debugging | Less predictable, harder to estimate and debug |

**Attention dilution.** A model spreads its attention across everything in a single pass. More items in one pass means less attention per item. The symptoms:

- Detailed feedback on early items, shallow or missing feedback on later ones.
- The same pattern flagged in one item and approved, unflagged, in another.

**The fix is structural, not a model or prompting fix:**

- **Per-item local passes:** each item gets its own call and the full attention budget.
- **A separate cross-item integration pass:** runs once, after all local passes, and looks only for cross-cutting concerns no single-item pass could see.

## Exam trap

**Matching the pattern to whatever sounds more sophisticated** instead of to the task. A multi-pass code review (N per-file passes + one integration pass) is a **fixed** pipeline, because the plan is knowable before any file is opened.

Reject these explicitly:

- **A bigger model or larger context window.** Dilution is architectural, not a capability problem.
- **A stronger "be equally thorough" prompt.** It doesn't change how attention is allocated.
- **Batching without an integration pass.** It solves dilution within a batch but never compares items in different batches.

## Exam answer vs current docs

No difference.

## Code walkthrough

**`good_example.py`**

- **A. Fixed pipeline.** `review_pipeline()` runs `local_review()` once per file (each prompt holds exactly one file), then `integration_review()` once. The integration pass gets every per-file finding ("don't repeat these") and a narrow brief: cross-file contracts, API consistency, inconsistent judgements. It catches `api/users.py` returning `user_id` while `web/client.py` reads `userId`.
- **B. Dynamic decomposition.** `investigate()` asks for one next step at a time, given the findings so far. The app logs reveal payments-service timeouts, a lead nobody planned for. That leads to the pool config, then the deploy history, then the root cause.
- **Mock model rules:**
  - A reviewer sees a cross-file bug **only if both files are in the same prompt**. That's honest, not a cheat.
  - The single-pass behaviour is **simulated** dilution (thorough on the first two files, skims the rest), labelled as such in the code. It reproduces the documented symptom; it doesn't measure it.

**`anti_pattern.py`**

- `single_pass_review()` returns 2 of 4 local issues and no cross-file bug.
- `batched_review()` (batches of 2, no integration) finds all 4 local issues but misses the cross-file bug, because `users.py` and `client.py` sit in different batches.
- `fixed_pipeline_investigation()` runs logs → DB → CDN as decided up front. It never follows the payments-service lead, so `root_cause=None`.

**`test_task_1_6.py`** proves:

- The pipeline makes exactly N + 1 calls, with the integration pass last, and each local pass sees one file.
- Everything is found.
- The dynamic run follows the unplanned lead.
- Each anti-pattern misses what the notes say it misses.
- Batching catches the bug only when the two files happen to share a batch. That's luck, not architecture.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_6_task_decomposition.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_6_task_decomposition.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_6_task_decomposition
```
