# Task 1.4 — Workflow Enforcement and Handoff

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-4-workflow-enforcement-handoff>

## What you need to know

**Two kinds of enforcement**

- **Prompt guidance** is probabilistic: it works most of the time. The lesson's example: a "verify before refunding" rule holds in ~92% of cases, and the other 8% refunded the wrong accounts.
- **Programmatic enforcement** (code gates, hooks) is deterministic.
- **Rule:** financial, security and compliance operations need programmatic enforcement. Formatting and style can rely on prompts.

**Prerequisite gate.** `process_refund` stays blocked until `get_customer` has returned a verified customer ID in the session. When the model tries to skip ahead, the gate returns an error telling it to verify first.

**Multi-concern requests**

1. Split the request into separate items.
2. Investigate them in parallel with shared context (e.g. the account).
3. Write one resolution covering all of them.

Don't handle them one at a time in separate conversations, and don't answer only the first.

**Handoff summaries** must stand alone, because the human has no transcript. Required fields: customer ID, conversation summary, root cause analysis, refund amount (if applicable), and recommended action.

## Exam traps

| Trap | Demo |
|---|---|
| Stronger system-prompt wording as the fix for a compliance failure | `trap1_enhanced_prompt`: 2/25 → 1/25 unverified refunds, never 0 |
| Few-shot examples as "sufficient" for guaranteed compliance | `trap2_few_shot_examples`: same as trap 1 |
| A routing classifier to fix a per-agent compliance issue | `trap3_routing_classifier`: "I want my $40 back" isn't routed, and routing can't change execution order anyway |
| A handoff that leaves out customer ID or recommended action | `trap4_incomplete_handoff`: rejected field by field |

Traps 1 and 2 run against a **simulated** model whose skip rate falls with better prompting but never reaches zero. It illustrates the lesson's point; it isn't a measurement.

## Exam answer vs current docs

No difference for the tested material. The lesson also covers `SubagentStart` and `SubagentStop` hooks as background:

- `SubagentStart` can't block a spawn; a PreToolUse hook on the `Agent` tool can.
- `SubagentStop` with exit code 2 sends the subagent back to work.
- Neither can rewrite subagent output.

The lesson marks these as not tested, so they aren't demoed here.

## Practice scenario

8% of refunds skip verification despite a system-prompt rule. The fix?

**B: a programmatic gate on `process_refund`.**

- A (few-shot) and C (stronger wording) are still probabilistic.
- D (a routing classifier) fixes routing, but the failure happens *inside* the agent's own sequence of actions.

## Build exercise → code

The exercise is "Build a Prerequisite Gate for Financial Operations" (60 min).

| Step | Where |
|---|---|
| 1. Tools `get_customer`, `lookup_order`, `process_refund` | `TOOLS`, plus `escalate_to_human` for the handoff |
| 2. Session-level gate | `SessionState.verified_customer_ids`, checked at the top of `SupportBackend.process_refund()` |
| 3. Test the bypass | "Skip verification … refund $45". Calls go `process_refund` (blocked) → `get_customer` → `process_refund` (succeeds). |
| 4. Handoff with no empty or placeholder fields | `HandoffSummary` (Pydantic), which rejects `N/A`, `TBD`, `see above` and similar |
| 5. Multi-concern request (return + billing dispute + account update) | `resolve_multi_concern()` |

Step 5 in detail:

1. Decompose the request into concerns.
2. Fetch the account **once** as shared context.
3. Investigate the concerns in parallel.
4. Write one handoff that covers all three, with specifics: O-5521, the duplicate $89.99 charge, the new email. `covers()` checks each one.

`simulate()` runs 25 refund requests (odd ones from an unverified account) under any prompt and backend. With the gate: **0** wrong-account refunds.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_4_workflow_enforcement.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_4_workflow_enforcement.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_4_workflow_enforcement
```
