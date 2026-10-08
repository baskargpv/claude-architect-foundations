# Task 1.5 — Agent SDK Hooks

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-5-agent-sdk-hooks>

## What you need to know

Hooks add deterministic behaviour at the boundary between the model's decisions and real tool side effects.

| Hook | When | Can |
|---|---|---|
| **PreToolUse** | Before the tool runs | Allow, deny, ask or defer (`permissionDecision`); rewrite arguments (`updatedInput`). A denied tool **never runs**. |
| **PostToolUse** | After the tool runs, before the model sees the result | Replace what the model sees (`updatedToolOutput`); record state for a later PreToolUse check |

- Neither hook reverses side effects. Blocking in PostToolUse stops the loop, but the action has already happened.
- **Normalisation targets:**
  - Unix and DD/MM/YYYY dates → ISO 8601
  - numeric or one-letter status codes → words
  - currency → a decimal amount plus a currency code
- **Policy examples:**
  - refunds over $500 → human escalation
  - `transfer_funds` gated on a passing AML check
  - `approve_discount` above 20% → manager approval queue
- **Decision rule:** if one failure means financial loss or legal risk, use a hook. Use prompts for formatting and style.

## Exam traps

| Trap | Demo |
|---|---|
| Using PostToolUse hooks to block policy violations | `trap1_post_tool_use_block`: event order is Pre → handler → Post, and the $750 is already in the ledger |
| Stronger prompts for a 100% requirement | `trap2_prompt_only_compliance`: one flagged transfer gets through (**simulated** skip rate) |
| Asking the model to normalise data instead of using PostToolUse | `trap3_model_side_normalisation`: the same input gives day/month swaps and `"P"` read as "processed" (**simulated** drift) |
| Confusing hook direction | `trap4_wrong_hook_direction`: a normaliser registered as PreToolUse has no result to work on, so raw formats reach the model |

## Exam answer vs current docs

| | Exam answer | Current docs (Agent SDK hooks page) |
|---|---|---|
| Scope | Task 1.5 tests PreToolUse and PostToolUse only | The SDK has many more events (SubagentStart/Stop, PreCompact …), which aren't tested here |
| Replacing tool output | "PostToolUse normalises results" | Done with `hookSpecificOutput.updatedToolOutput`, for any tool. The older `updatedMCPToolOutput` (MCP tools only) is **deprecated**. |
| PreToolUse decisions | allow / deny | `allow`, `deny`, `ask`, `defer`. When hooks disagree, `deny` beats `defer`, which beats `ask`, which beats `allow`. |
| Registration | — | `ClaudeAgentOptions(hooks={"PreToolUse": [HookMatcher(matcher="mcp__support__process_refund", hooks=[cb])]})`, with callback signature `async def cb(input_data, tool_use_id, context)` |

## Practice scenario

Transfers occasionally skip AML, compliance needs 100%, and prompting gets ~95%. The fix?

**A: a PreToolUse hook that blocks `transfer_funds` until `aml_check` passes.**

- B (a longer prompt) and D (few-shot) are still probabilistic.
- C (a PostToolUse flag) runs after the money has moved.

## Build exercise → code

The exercise is "Implement Agent SDK Hooks for Normalisation and Policy Enforcement" (60 min).

| Step | Where |
|---|---|
| 1. Three MCP tools with mismatched formats | `build_server()`: a **real** `mcp` server (in-process). Each tool's formats are listed below the table. |
| 2. PostToolUse normaliser returning `updatedToolOutput` | `normalise_output` → `normalise()` |
| 3. Check consistency across all three tools | The agent run in `main()` and `test_step3_...`. The model only ever sees ISO dates and English statuses. |
| 4. PreToolUse refund threshold (> $500 → deny + escalation reason) | `refund_threshold` |
| 5. AML gate: Pre on `transfer_funds`, Post on `aml_check` writes session state | `aml_gate` + `record_aml` |
| 6. Test both policies | Denied calls never reach the MCP handler (`events` proves it). After AML passes, or with a lower amount, they go through. |

The three MCP tools' raw formats:

| Tool | Dates | Status | Money |
|---|---|---|---|
| `get_customer` | Unix epoch | numeric codes | bare balance string |
| `lookup_order` | ISO 8601 | English words | integer cents |
| `check_shipping` | DD/MM/YYYY | one letter (S / P / D) | `"€12,50"` |

There's also `discount_approval`, the lesson's manager-approval example: a deny that adds the request to `approval_queue`, then succeeds after `manager_approves()`.

**How it runs.** `HookedMCPDispatcher` gives the SDK's guarantees on top of real MCP calls:

- PreToolUse hooks run in parallel, and any deny wins.
- Then the MCP call (`mcp.Client(server).call_tool`).
- Then PostToolUse hooks, which may replace the output.

Tools are exposed to the model as `mcp__support__<tool>`, and hook matchers are regexes on those names, the same as SDK matchers.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_5_sdk_hooks.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_5_sdk_hooks.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_5_sdk_hooks
```
