"""Task 1.4 — prompt-only enforcement of a financial prerequisite.

The system prompt says "always verify before refunding", and that's the only safeguard.
When the model skips verification (the ~8% case), the money moves, even for an
unverified account.

A placeholder handoff is the second failure: "N/A" fields mean the human starts from zero.
"""

from __future__ import annotations

from common.client import get_client, mode_banner
from domain1_agentic_architecture.task_1_4_prerequisite_gates.good_example import (
    SupportDesk,
    handle,
    mock_model,
)


class PromptOnlySupportDesk(SupportDesk):
    def _process_refund(self, customer_id: str, amount: float, reason: str) -> dict:
        # WRONG: no state check - we trust that the prompt told the model to verify first.
        return self._move_money(customer_id, amount, reason)


PLACEHOLDER_HANDOFF = {
    "customer_id": "C-99",
    "conversation_summary": "N/A",
    "root_cause": "TBD",
    "refund_amount": None,
    "recommended_action": "see above",  # the human can't "see above" - there is no transcript
}


def main():
    print(mode_banner())
    result, state = handle(get_client(mock_model),
                           "I'm customer C-99. My order arrived damaged, please refund $40.", PromptOnlySupportDesk())
    print(f"C-99 (UNVERIFIED): calls={[c[1] for c in result.tool_calls]} ledger={state.refunds}  <- money moved")

    desk = SupportDesk()
    print(f"placeholder handoff -> {desk.execute('escalate_to_human', PLACEHOLDER_HANDOFF)}")


if __name__ == "__main__":
    main()
