# Task 1.4 — Deterministic Enforcement (Prerequisite Gates)

## Theory

Prompt instructions ("always verify before refunding") work most of the time. The exam's reference figure is **~92% reliable**, about an 8% failure rate. A financial operation needs 100%, so it needs deterministic enforcement: a plain `if` on session state. Code can't be talked past the way a model's instructions can.

**Mechanism:**

1. A session-level state tracker records whether the prerequisite actually happened (`get_customer` returned `verification_status: "verified"`).
2. The dependent tool (`process_refund`) checks that state **before executing anything**.
3. If the prerequisite isn't met, it returns a blocked error, whatever the model "decided".

**Why `input_schema` can't do this:** JSON Schema only shapes one call's fields (types, which are required). It has no concept of sequencing across calls. The gate belongs in your dispatcher.

**Structured handoff protocol.** These fields are required:

| Field | Purpose |
|---|---|
| `customer_id` | Who this concerns |
| `conversation_summary` | What happened. The human has **no** transcript access. |
| `root_cause` | Why it happened |
| `refund_amount` | The specific number, if applicable |
| `recommended_action` | What the human should do next |

An empty or placeholder field is information permanently lost to the human.

**Multi-concern requests:** a bundle like return + billing dispute + account update gets split into distinct items, each investigated, and the handoff covers **all** of them. Free-text summary/action fields let one handoff carry several concerns.

## Exam trap

Prompt-only enforcement for financial or compliance actions. "~92% reliable" is not 100%. The gate must be code.

## Exam answer vs current docs

No difference. The 92% figure is the exam's illustrative number, not a measured property of any model.

## Code walkthrough

**`good_example.py`**

- `SupportDesk.execute()` is the single dispatcher every tool call goes through. It's plugged into the Task 1.1 loop via `run_agent(tools=..., execute=desk.execute)`.
- `_get_customer()` adds the customer to `state.verified_customers` **only** when the record really is verified.
- `_process_refund()` holds the gate: if the customer isn't in `verified_customers`, it returns `{"is_error": true, "blocked": true, ...}` and the ledger is untouched.
- `HandoffPayload` (Pydantic) rejects empty or placeholder values (`N/A`, `TBD`, `see above` …). Rejections come back as per-field errors the model can act on.
- **Mock model:** it simulates the ~8% failure by calling `process_refund` first.
  - For **C-42** (verified): the gate blocks, the model verifies, and the refund succeeds on the retry.
  - For **C-99** (unverified): the gate blocks, verification fails, and the model escalates with a complete handoff.

**`anti_pattern.py`**

- `PromptOnlySupportDesk` removes the state check and relies on the system prompt alone. The same mock model refunds **unverified C-99** on the first call.
- `PLACEHOLDER_HANDOFF` shows what a lazy handoff looks like, and the good desk rejects it.

**`test_task_1_4.py`** checks:

- The call order is `process_refund` (blocked) → `get_customer` → `process_refund`.
- An unverified customer is never refunded.
- The gate works with no model involved.
- Placeholder fields are rejected by name.
- A multi-concern handoff is accepted.
- The prompt-only desk moves money for C-99.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_4_prerequisite_gates.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_4_prerequisite_gates.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_4_prerequisite_gates
```
