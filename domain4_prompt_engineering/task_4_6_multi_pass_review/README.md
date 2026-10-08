# Task 4.6 — Multi-Instance and Multi-Pass Review

Lesson: <https://claudecertificationguide.com/learn/4-prompt-engineering/4-6-multi-pass-review>

## What you need to know

- **Use an independent instance to review.** Same-session self-review keeps the generation reasoning and confirms rather than challenges. A separate instance, with no prior reasoning context, catches more.
- **Large multi-file reviews suffer attention dilution.** Fix it with per-file passes plus a cross-file integration pass that receives every per-file finding. A bigger context window doesn't help.
- **Confidence can route findings:** high confidence goes to developers, low confidence to human review. But raw self-reported confidence is uncalibrated, so calibrate thresholds against labelled verdicts first.
- **Production shape:** generation → per-file review → integration review → confidence routing → calibration loop. It costs more, so use it where the stakes justify it.

## Exam traps

| Trap | Demo |
|---|---|
| Same-session self-review | `trap1_same_session_self_review` (**simulated**: approves its own `eval()`) |
| A single pass for a large multi-file review | `trap2_single_pass`: 3 dilution artefacts |
| A larger context window to fix dilution | `trap3_bigger_context`: identical result |
| Uncalibrated confidence for automated routing | `trap4_raw_confidence_routing`: 2 confidently wrong findings reach developers |

## Exam answer vs current docs

No difference.

## Practice scenario

A 14-file PR gets uneven, contradictory review.

**B: per-file passes plus a cross-file integration pass.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A single pass over a 10+ file PR, documenting the problems | `single_pass_review()` over Task 1.6's 12-file `sample_repo` |
| 2. Per-file review prompts | `multi_pass_review()` (reused from Task 1.6) |
| 3. A separate integration prompt over the per-file findings | same |
| 4. A 0.0–1.0 confidence per finding, with high/low routing | `review_with_confidence()`, `route()` |
| 5. A fresh instance verifies a subset; calibrate the threshold | `verify()` runs as a separate single-message request. `calibrate()` picks the lowest confidence at which ≥ 90% of findings are right. |

**About the mock.** `NOISE` adds three plausible but wrong findings. Two of them come with **simulated** high raw confidence (0.85), the "confidently wrong" case. Calibration from the verifier's verdicts sets the threshold at 0.92, so those two go to humans instead of developers.

## Run

```bash
.venv/bin/python -m domain4_prompt_engineering.task_4_6_multi_pass_review.good_example
.venv/bin/python -m domain4_prompt_engineering.task_4_6_multi_pass_review.anti_pattern
.venv/bin/pytest domain4_prompt_engineering/task_4_6_multi_pass_review
```
