# Task 5.5 — Human Review & Confidence Calibration

Lesson: <https://claudecertificationguide.com/learn/5-context-management/5-5-human-review-calibration>

## What you need to know

- **Aggregate accuracy hides failures.** 97% overall can sit alongside 45–60% on specific document types. **Validate by document type and field** before automating.
- **Stratified random sampling** (by type, confidence band and field) must include **high-confidence** automated items. That's the only way to catch a new error pattern the model is confident about.
- **Raw confidence is uncalibrated.** 0.90 on dates and 0.90 on amounts mean different real accuracy. Build calibration curves **per field per document type** from labelled validation sets.
- **Prioritise reviewer time by uncertainty:** low confidence, contradictory sources, weak document types. Use a dynamic queue, not chronological order or an even split.
- **Order of work:** measure by segment → calibrate → set thresholds → stratified sampling → only then reduce human review.

## Exam traps

| Trap | Demo |
|---|---|
| Automating high-confidence extractions on aggregate accuracy | `trap1_automate_on_aggregate`: 118 wrong international amounts automated |
| Sampling only low-confidence extractions | `trap2_sample_low_confidence_only`: 0 of the confident errors ever seen |
| Raw confidence without calibration | `trap3_raw_confidence`: the same raw band gives different accuracy per field |
| Spreading reviewer capacity evenly | `trap4_even_split`: 13 errors caught vs 300 when prioritised |

## Exam answer vs current docs

No difference.

## Practice scenario

97% accurate; the proposal is to auto-approve above 95% confidence.

**D: the aggregate can hide poor per-type and per-field accuracy, and confidence needs calibrating first.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A mock extraction system: 4 doc types, per-field values and confidence | `generate()`, built from the lesson's accuracy table. International amounts have a **simulated** confidently-wrong error pattern. |
| 2. Accuracy by type and field next to the strong-looking aggregate | `accuracy_by_segment()`: 95.8% aggregate vs 48.8% international dates |
| 3. Calibration curves and thresholds per field per type | `calibration()`, `thresholds()`: standard dates automate above 0.8; international amounts never |
| 4. Stratified sampling that includes high confidence | `stratified_sample()` |
| 5. A dynamic priority queue, lowest confidence first | `ReviewQueue` (heap) |

No model calls are involved, so this runs identically offline and live.

## Run

```bash
.venv/bin/python -m domain5_context_reliability.task_5_5_human_review_calibration.good_example
.venv/bin/python -m domain5_context_reliability.task_5_5_human_review_calibration.anti_pattern
.venv/bin/pytest domain5_context_reliability/task_5_5_human_review_calibration
```
