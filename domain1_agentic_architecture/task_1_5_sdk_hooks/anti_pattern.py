"""Task 1.5 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-5-agent-sdk-hooks

Trap 1  PostToolUse hooks used to block policy-violating actions  -> the money already moved
Trap 2  enhanced prompt instructions for a 100% requirement        -> still probabilistic (SIMULATED)
Trap 3  model-side data normalisation instead of a PostToolUse hook -> inconsistent reads (SIMULATED)
Trap 4  confusing hook direction (normaliser registered as Pre)     -> nothing to normalise yet
"""

from __future__ import annotations

from common.client import mode_banner
from domain1_agentic_architecture.task_1_5_sdk_hooks.good_example import (
    REFUND_LIMIT,
    HookedMCPDispatcher,
    mcp_name,
    normalise,
)


def trap1_post_tool_use_block() -> HookedMCPDispatcher:
    def hooks(state):
        async def refund_limit_too_late(input_data, tool_use_id, context):
            if input_data["tool_input"]["amount"] > REFUND_LIMIT:
                return {"decision": "block", "reason": f"refund exceeds ${REFUND_LIMIT}"}  # WRONG event
            return {}
        return {"PostToolUse": [(f"^{mcp_name('process_refund')}$", [refund_limit_too_late])]}

    d = HookedMCPDispatcher(hooks)
    d.execute(mcp_name("process_refund"), {"order_id": "O-77", "amount": 750})
    return d


# Simulated: 1 in 20 transfers skips AML even with a strongly worded prompt (the lesson's ~95%).
PROMPT_ONLY_SKIPS = {7}


def trap2_prompt_only_compliance(n: int = 20) -> dict:
    d = HookedMCPDispatcher(lambda state: {})  # no hooks, just "ALWAYS run aml_check first" in the prompt
    for i in range(1, n + 1):
        account = "ACC-FLAGGED-1" if i == 7 else "ACC-CLEAN-1"
        if i not in PROMPT_ONLY_SKIPS:
            if d.execute(mcp_name("aml_check"), {"account": account})["result"] != "pass":
                continue
        d.execute(mcp_name("transfer_funds"), {"account": account, "amount": 1000})
    return {"transfers": len(d.ledger.transfers),
            "unscreened_flagged_transfers": sum(1 for a, _ in d.ledger.transfers if "FLAGGED" in a)}


def simulated_model_normaliser(tool: str, raw: dict, run: int) -> dict:
    """What 'ask the model to convert the formats' looks like over several runs (SIMULATED drift)."""
    out = dict(raw)
    if "shipped_on" in raw:
        out["shipped_on"] = "2024-04-03T00:00:00Z" if run % 2 else "2024-03-04T00:00:00Z"  # day/month swapped on odd runs
    if raw.get("status") == "P":
        out["status"] = "processed" if run % 3 == 0 else "pending"  # 'P' misread
    return out


def trap3_model_side_normalisation(runs: int = 4) -> list[dict]:
    raw = {"order_id": "O-77", "shipped_on": "04/03/2024", "status": "P"}
    return [simulated_model_normaliser("check_shipping", raw, r) for r in range(runs)]


def trap4_wrong_hook_direction() -> dict:
    def hooks(state):
        async def normaliser_in_pre(input_data, tool_use_id, context):
            raw = input_data.get("tool_response")  # PreToolUse: the tool hasn't run - there is no response
            if raw is None:
                return {}
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedToolOutput": normalise("check_shipping", raw)}}
        return {"PreToolUse": [(f"^{mcp_name('check_shipping')}$", [normaliser_in_pre])]}

    return HookedMCPDispatcher(hooks).execute(mcp_name("check_shipping"), {"order_id": "O-77"})


def main():
    print(mode_banner())
    d = trap1_post_tool_use_block()
    print(f"trap 1 PostToolUse block : ledger={d.ledger.refunds} events={[e for e, _ in d.events]}  <- money already moved")
    print(f"trap 2 prompt only       : {trap2_prompt_only_compliance()}")
    reads = trap3_model_side_normalisation()
    print(f"trap 3 model normalising : {[(r['shipped_on'][:10], r['status']) for r in reads]}  <- same input, different reads")
    print(f"trap 4 wrong direction   : {trap4_wrong_hook_direction()}  <- raw formats reach the model")


if __name__ == "__main__":
    main()
