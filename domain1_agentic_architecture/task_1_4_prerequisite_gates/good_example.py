"""Task 1.4 — deterministic prerequisite gate in the tool dispatcher.

A prompt ("always verify before refunding") is right ~92% of the time. Money needs 100%.
SessionState records whether get_customer actually returned verification_status
"verified"; process_refund checks that state BEFORE doing anything and returns a
blocked error otherwise, whatever the model decided.

input_schema can't do this: JSON Schema shapes one call's fields and has no idea what
earlier calls returned. The gate lives in code.

Escalations go through a validated structured handoff. The human has no transcript,
so an empty or placeholder field is information lost for good.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError, field_validator

from common.client import get_client, mode_banner
from common.mock import last_tool_results, message, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

CUSTOMERS = {
    "C-42": {"name": "Ada Park", "verification_status": "verified"},
    "C-99": {"name": "Sam Doe", "verification_status": "unverified"},
}

TOOLS = [
    {"name": "get_customer", "description": "Fetch a customer record including verification_status. Required before any refund.",
     "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}},
    {"name": "process_refund", "description": "Issue a refund to a VERIFIED customer. Moves money.",
     "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}, "amount": {"type": "number"},
                                                       "reason": {"type": "string"}}, "required": ["customer_id", "amount", "reason"]}},
    {"name": "escalate_to_human", "description": "Hand the case to a human agent who has NO access to this conversation.",
     "input_schema": {"type": "object", "properties": {
         "customer_id": {"type": "string"}, "conversation_summary": {"type": "string"}, "root_cause": {"type": "string"},
         "refund_amount": {"type": ["number", "null"]}, "recommended_action": {"type": "string"}},
         "required": ["customer_id", "conversation_summary", "root_cause", "refund_amount", "recommended_action"]}},
]

SYSTEM = "You are a support agent. Always verify the customer with get_customer before refunding."

PLACEHOLDERS = {"", "n/a", "na", "tbd", "unknown", "none", "see above", "-"}


class HandoffPayload(BaseModel):
    customer_id: str
    conversation_summary: str  # what happened - the human has no transcript
    root_cause: str  # why it happened
    refund_amount: float | None  # the specific number, if applicable
    recommended_action: str  # what the human should do next

    @field_validator("customer_id", "conversation_summary", "root_cause", "recommended_action")
    @classmethod
    def no_placeholders(cls, v: str) -> str:
        if v.strip().lower() in PLACEHOLDERS:
            raise ValueError("empty/placeholder value - this information would be lost to the human")
        return v


@dataclass
class SessionState:
    verified_customers: set = field(default_factory=set)
    refunds: list = field(default_factory=list)  # the ledger: money that actually moved
    handoffs: list = field(default_factory=list)
    blocked: list = field(default_factory=list)


class SupportDesk:
    """Tool dispatcher. Every tool call goes through execute()."""

    def __init__(self):
        self.state = SessionState()

    def execute(self, name: str, tool_input: dict) -> dict:
        return getattr(self, f"_{name}")(**tool_input)

    def _get_customer(self, customer_id: str) -> dict:
        record = CUSTOMERS.get(customer_id)
        if record is None:
            return {"is_error": True, "error": f"customer {customer_id} not found"}
        if record["verification_status"] == "verified":
            self.state.verified_customers.add(customer_id)  # record the prerequisite as it actually happened
        return {"customer_id": customer_id, **record}

    def _process_refund(self, customer_id: str, amount: float, reason: str) -> dict:
        # THE GATE: a plain if-statement on session state. It can't be talked past.
        if customer_id not in self.state.verified_customers:
            self.state.blocked.append(("process_refund", customer_id))
            return {"is_error": True, "blocked": True,
                    "error": f"process_refund blocked: prerequisite not met - get_customer has not returned "
                             f"verification_status 'verified' for {customer_id} in this session"}
        return self._move_money(customer_id, amount, reason)

    def _move_money(self, customer_id: str, amount: float, reason: str) -> dict:
        refund_id = f"R-{len(self.state.refunds) + 1:03d}"
        self.state.refunds.append({"refund_id": refund_id, "customer_id": customer_id, "amount": amount})
        return {"refund_id": refund_id, "customer_id": customer_id, "amount": amount, "status": "refunded"}

    def _escalate_to_human(self, **payload) -> dict:
        try:
            handoff = HandoffPayload(**payload)
        except ValidationError as e:
            return {"is_error": True, "error": "handoff rejected", "fields": [
                {"field": err["loc"][0], "problem": err["msg"]} for err in e.errors()]}
        self.state.handoffs.append(handoff)
        return {"handoff_id": f"H-{len(self.state.handoffs):03d}", "status": "queued"}


def handle(client, request: str, desk: SupportDesk | None = None):
    desk = desk or SupportDesk()
    result = run_agent(client, request, tools=TOOLS, execute=desk.execute, system=SYSTEM)
    return result, desk.state


# ---- mock model ------------------------------------------------------------------------------

def mock_model(kwargs: dict):
    """A model that USUALLY verifies first - but this time jumps straight to the refund."""
    customer_id = re.search(r"C-\d+", kwargs["messages"][0]["content"]).group(0)
    results = last_tool_results(kwargs)
    if not results:
        return message(text("I'll refund that right away."),
                       tool_use("process_refund", {"customer_id": customer_id, "amount": 40.0, "reason": "damaged item"}))
    last = json.loads(results[-1]["content"])
    if last.get("blocked"):
        return message(tool_use("get_customer", {"customer_id": customer_id}))
    if "verification_status" in last:
        if last["verification_status"] == "verified":
            return message(tool_use("process_refund", {"customer_id": customer_id, "amount": 40.0, "reason": "damaged item"}))
        return message(tool_use("escalate_to_human", {
            "customer_id": customer_id,
            "conversation_summary": "Customer reports a damaged item and requests a $40 refund; identity could not be verified.",
            "root_cause": "Account verification_status is 'unverified', so refunds are not permitted automatically.",
            "refund_amount": 40.0,
            "recommended_action": "Verify identity by phone, then issue the $40 refund if the claim checks out."}))
    if last.get("status") == "refunded":
        return message(text(f"Your refund of ${last['amount']:.2f} has been processed ({last['refund_id']})."))
    if last.get("status") == "queued":
        return message(text("I've passed this to a colleague who will verify your account and follow up."))
    return message(text("Sorry, something went wrong."))


def main():
    print(mode_banner())
    for cid in ("C-42", "C-99"):
        result, state = handle(get_client(mock_model), f"I'm customer {cid}. My order arrived damaged, please refund $40.")
        print(f"\n{cid}: calls={[c[1] for c in result.tool_calls]}")
        print(f"  blocked={state.blocked} ledger={state.refunds} handoffs={len(state.handoffs)}")
        print(f"  reply: {result.final_text}")


if __name__ == "__main__":
    main()
