"""Task 1.5 — using PostToolUse to block, and skipping normalisation.

1. The refund limit lives in a PostToolUse hook that returns {"decision": "block"}.
   By then the handler has ALREADY run: the $750 is gone. PostToolUse can only
   inspect or rewrite the result; it can't undo the action.
2. No normalisation: the model gets a Unix timestamp, "03/06/2024" (3 June or
   March 6?) and status "P" (pending? processed?), and has to guess.
"""

from __future__ import annotations

from common.client import mode_banner
from domain1_agentic_architecture.task_1_5_sdk_hooks.good_example import ORDERS, REFUND_LIMIT, build


def build_post_blocking_hooks(state) -> dict:
    async def refund_limit_too_late(input_data, tool_use_id, context):
        if input_data["tool_input"]["amount"] > REFUND_LIMIT:
            return {"decision": "block", "reason": f"Refund exceeds ${REFUND_LIMIT:.0f}"}  # WRONG event
        return {}

    return {"PostToolUse": [("^process_refund$", [refund_limit_too_late])]}  # and no normaliser


def main():
    print(mode_banner())
    d = build(build_post_blocking_hooks)
    out = d.execute("process_refund", {"order_id": "O-3", "amount": 750.0})
    print(f"refund $750 -> {out}")
    print(f"ledger: {d.backend.ledger.refunds}  <- 'blocked', but the money already moved")
    print(f"event order: {d.events}")
    for oid in ORDERS:
        print(f"lookup {oid}: model sees {d.execute('lookup_order', {'order_id': oid})}")


if __name__ == "__main__":
    main()
