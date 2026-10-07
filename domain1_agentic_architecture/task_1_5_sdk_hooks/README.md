# Task 1.5 — Agent SDK Hooks

## Theory

Both hook types run *your* check logic. The SDK only guarantees **when** it runs relative to the tool call.

| Hook | Runs / sees | Correct use |
|---|---|---|
| `PreToolUse` | **Before** the handler. Sees only the proposed call (tool name + input); no result exists yet. | Policy and security enforcement: deny before the action happens |
| `PostToolUse` | **After** the handler has already run. Sees the real output (dates, statuses, amounts). | Data normalisation, or recording state for a later `PreToolUse` check |

**Normalisation (PostToolUse):** when tools return mixed formats (Unix vs ISO 8601 vs DD/MM/YYYY; numeric vs string vs single-char status codes), rewrite every result into one schema **before the model sees it**. That removes misreadings like day/month swaps, or `"P"` read as "processed" instead of "pending".

**Threshold and prerequisite gates via PreToolUse:**

- Deny `process_refund` above $500, with a `permissionDecisionReason`.
- Deny `transfer_funds` until session state shows `aml_check` returned a pass.

This is the same deterministic enforcement as Task 1.4, formalised as an SDK hook.

**Decision framework:**

- **Hooks** for 100% requirements: compliance, financial thresholds, prerequisite ordering.
- **Prompts** for preferences: style, tone, non-critical guidance.

## Exam trap

**Using PostToolUse to block an action.** By the time PostToolUse runs, the handler has already executed. For `process_refund`, the money has already moved. PostToolUse can only inspect or rewrite the result; it can't undo the action. Blocking must happen in PreToolUse.

## Exam answer vs current docs

| | Exam answer | Current docs (Agent SDK hooks page) |
|---|---|---|
| Rewriting tool output in PostToolUse | "PostToolUse rewrites every result into one consistent schema" | Done with `hookSpecificOutput.updatedToolOutput`, which works for any tool. The older `updatedMCPToolOutput` covers MCP tools only. `additionalContext` appends instead of replacing. |
| Blocking from PostToolUse | Too late, the handler already ran | Same. A PostToolUse `decision: "block"` only feeds a reason back to Claude; the side effect stands. |
| PreToolUse decisions | deny / allow | `permissionDecision` is `"allow"`, `"deny"`, `"ask"` or `"defer"`. When hooks disagree, `deny` > `defer` > `ask` > `allow`, and one deny blocks the call. |
| Callback signature | — | `async def hook(input_data, tool_use_id, context) -> dict`, registered via `ClaudeAgentOptions(hooks={"PreToolUse": [HookMatcher(matcher=..., hooks=[...])]})` |

## Code walkthrough

**`good_example.py`**

- **Backend:** has real side effects (a `Ledger`), and three order sources with three date formats and three status vocabularies.
- **`build_hooks(state)`** returns callbacks in the exact Agent SDK shape:
  - `refund_limit` (Pre) denies above $500 with a reason telling the model to escalate.
  - `aml_gate` (Pre) denies `transfer_funds` unless `state.aml_passed` contains the account.
  - `normalize_order` (Post) returns `updatedToolOutput` with ISO dates and canonical statuses. `eu` dates are parsed as DD/MM explicitly.
  - `record_aml` (Post) writes the AML pass into session state for `aml_gate` to read later.
- **`HookedDispatcher`** honours the SDK contract so the demo runs offline on the Messages API:
  - Pre hooks run (in parallel), and any deny short-circuits before the handler.
  - The handler runs, then Post hooks may replace the output.
  - `events` records the order things happened.
- **End-to-end:** the Task 1.1 loop drives a mock model that looks up O-3 ($900) and tries a full refund. It gets the denial reason and tells the customer the refund needs approval. The ledger stays empty.

**`anti_pattern.py`**

- Puts the $500 check in a **PostToolUse** hook returning `{"decision": "block"}`. The event log shows `PreToolUse → handler → PostToolUse`, and the ledger holds the $750 refund.
- Has no normaliser, so the model sees `1717200000`, `"03/06/2024"` and `"P"`.

**`test_task_1_5.py`** proves:

- The handler never runs on a deny, and refunds under the limit go through.
- The AML gate reads state that a PostToolUse hook recorded.
- All three formats normalise correctly.
- The callbacks return the SDK output shape.
- The agent run moves no money.
- The anti-pattern's block arrives after the handler, with the money gone.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_5_sdk_hooks.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_5_sdk_hooks.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_5_sdk_hooks
```
