# Task 5.2 — Escalation & Ambiguity Resolution

Lesson: <https://claudecertificationguide.com/learn/5-context-management/5-2-escalation-ambiguity>

## What you need to know

- **Three valid escalation triggers:**
  1. An **explicit request for a human**: escalate immediately, with no attempt to resolve first.
  2. A **policy gap**: the policy is silent. A violation has a documented answer, so it isn't a gap.
  3. **No progress after a genuine attempt.** Speculating "I might fail" isn't enough.
- **Two unreliable triggers:** sentiment (frustration doesn't track complexity) and self-reported confidence scores (poorly calibrated).
- **Frustrated customer, simple issue:** acknowledge and resolve. If they repeat that they want a human after you offer help, escalate.
- **Ambiguous matches** (three "John Smith"s): ask for email, phone or order number. Never pick by recency or activity.
- **Fix it in the prompt before adding infrastructure:** explicit criteria plus few-shot examples come before classifiers or sentiment tooling.

## Exam traps

| Trap | Demo |
|---|---|
| Sentiment-based escalation | `trap1_sentiment`: escalates the easy late parcel and misses the polite "talk to a human" |
| Self-reported confidence as the signal | `trap2_confidence_router` (**simulated** confidences): escalates the easy case, attempts the gap |
| Resolving before honouring an explicit human request | `trap3_investigate_first`: 4 steps before escalating |
| Picking the most recent or most active record | `trap4_pick_most_recent` |

## Exam answer vs current docs

No difference.

## Practice scenario

55% first-contact resolution: simple cases escalated, complex exceptions attempted.

**A: explicit escalation criteria with few-shot examples in the system prompt.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A system prompt with the three triggers and the two anti-patterns | `SYSTEM_PROMPT` |
| 2. Three few-shot examples | The `Example:` lines: frustrated but simple → resolve; explicit request → escalate; policy gap → escalate |
| 3. Matching that detects multiple records and asks without picking | `match_customer()` |
| 4. Four scenarios | `SCENARIOS`, `decide()` |
| 5. Explicit requests escalate in the first response, and ambiguous matches never resolve | `test_step5_...` (one call, no tools) and `test_step3_...` |

`decide()` sends `SYSTEM_PROMPT` to the model. The mock follows the same rules, so the tests check the intended behaviour offline.

## Run

```bash
.venv/bin/python -m domain5_context_reliability.task_5_2_escalation.good_example
.venv/bin/python -m domain5_context_reliability.task_5_2_escalation.anti_pattern
.venv/bin/pytest domain5_context_reliability/task_5_2_escalation
```
