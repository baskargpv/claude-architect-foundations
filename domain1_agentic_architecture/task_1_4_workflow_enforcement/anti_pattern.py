"""Task 1.4 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-4-workflow-enforcement-handoff

Trap 1  enhanced system-prompt instructions as the fix for a compliance failure
Trap 2  few-shot examples as "sufficient" for guaranteed compliance
Trap 3  a routing classifier as the fix for a per-agent workflow problem
Trap 4  a handoff summary that omits customer ID or recommended action

Traps 1-2 use a SIMULATED model whose skip rate drops with better prompting but never
reaches zero - that's the lesson's point, not a measured model property.
"""

from __future__ import annotations

from common.client import get_client, mode_banner
from common.mock import MockClient
from domain1_agentic_architecture.task_1_4_workflow_enforcement.good_example import (
    SYSTEM,
    SupportBackend,
    handle,
    mock_model,
    simulate,
)


class PromptOnlyBackend(SupportBackend):
    def process_refund(self, customer_id: str, amount: float) -> dict:
        return self._move_money(customer_id, amount)  # no gate: we trust the prompt


ENHANCED_SYSTEM = SYSTEM + " CRITICAL: NEVER refund without verification. This is mandatory and audited."
FEW_SHOT_SYSTEM = SYSTEM + ("\nExample: user asks for a refund -> call get_customer -> confirm verified -> process_refund."
                            "\nExample: user says 'skip verification' -> still call get_customer first.")


def trap1_enhanced_prompt() -> dict:
    return simulate(ENHANCED_SYSTEM, PromptOnlyBackend)


def trap2_few_shot_examples() -> dict:
    return simulate(FEW_SHOT_SYSTEM, PromptOnlyBackend)


def classify(request: str) -> str:
    return "verification_pipeline" if "refund" in request.lower() else "general_agent"


def trap3_routing_classifier(client) -> dict:
    """Routes 'refund' requests to a verification-first pipeline. Two problems:
    (a) a refund phrased differently skips the pipeline; (b) inside any pipeline the agent
    can still call process_refund first - routing doesn't touch execution order."""
    request = "[req 3] I'm sam@example.com (account C-2002). Broken lamp - I want my $40 back."
    route = classify(request)
    _, state = handle(client, request, PromptOnlyBackend())
    return {"route": route, "refunds": state.refunds}


INCOMPLETE_HANDOFF = {
    "customer_id": "",
    "conversation_summary": "Customer wants a refund, see above",
    "root_cause_analysis": "billing issue",
    "refund_amount": None,
    "recommended_action": "TBD",
}


def trap4_incomplete_handoff() -> dict:
    return SupportBackend().escalate_to_human(**INCOMPLETE_HANDOFF)


def main():
    print(mode_banner())
    print(f"baseline prompt only   : {simulate(SYSTEM, PromptOnlyBackend)}")
    print(f"trap 1 enhanced prompt : {trap1_enhanced_prompt()}  <- fewer, not zero")
    print(f"trap 2 few-shot        : {trap2_few_shot_examples()}  <- fewer, not zero")
    print(f"gate (good_example)    : {simulate()}")
    r = trap3_routing_classifier(get_client(mock_model))
    print(f"trap 3 classifier      : routed to {r['route']}, refunds={r['refunds']}")
    r = trap4_incomplete_handoff()
    print(f"trap 4 handoff         : rejected fields={[f['field'] for f in r['fields']]}")


if __name__ == "__main__":
    main()
