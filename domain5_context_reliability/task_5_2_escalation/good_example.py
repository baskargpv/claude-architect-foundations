"""Task 5.2 — Escalation & Ambiguity Resolution (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-2-escalation-ambiguity

Escalate on: an explicit request for a human (immediately), a policy GAP, or no progress after a
real attempt. Never on sentiment or self-reported confidence. Ambiguous customer matches ->
ask for another identifier, never pick one.
"""

from __future__ import annotations

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

# ---- Steps 1-2: explicit criteria + few-shot examples in the system prompt -------------------------

SYSTEM_PROMPT = """You are a support agent. Decide: resolve, escalate, or ask_identifier.
Escalate ONLY when:
1. The customer explicitly asks for a human -> escalate in your FIRST response, without investigating.
2. Policy is SILENT on the situation (a gap). A violation has a documented answer: give it, don't escalate.
3. You made a genuine attempt and cannot progress. "I might not manage" is not enough.
Never escalate because the customer sounds upset, and never because you feel unsure.
If several customer records match, ask for email, phone or order number - never pick one.

Example: "This is the THIRD time my parcel is late, I'm furious!" (late delivery, refund policy exists)
-> resolve: acknowledge the frustration and issue the late-delivery credit in the same reply.
Example: "Can I speak to a person, please?" -> escalate immediately; no lookups first.
Example: "Can I return a gift bought abroad in another currency?" (policy says nothing) -> escalate: policy gap.
"""

DECISION = {"type": "object", "additionalProperties": False, "required": ["action", "reason"],
            "properties": {"action": {"type": "string", "enum": ["resolve", "escalate", "ask_identifier"]},
                           "reason": {"type": "string"}}}


def decide(client, message_: str, context: str = "") -> dict:
    return ask_json(client, f"Customer: {message_}\nContext: {context}", DECISION, system=SYSTEM_PROMPT)


# ---- Step 3: matching that never guesses ------------------------------------------------------------

CUSTOMERS = [{"id": "C-1", "name": "John Smith", "email": "john.s@example.com", "last_order": "2026-09-30"},
             {"id": "C-2", "name": "John Smith", "email": "jsmith@example.net", "last_order": "2026-10-05"},
             {"id": "C-3", "name": "John Smith", "email": "john@smith.example", "last_order": "2026-06-11"},
             {"id": "C-4", "name": "Ana Lima", "email": "ana@example.com", "last_order": "2026-10-01"}]


def match_customer(name: str, email: str | None = None) -> dict:
    hits = [c for c in CUSTOMERS if c["name"] == name and (email is None or c["email"] == email)]
    if len(hits) == 1:
        return {"customer": hits[0]}
    if not hits:
        return {"customer": None, "ask": "I couldn't find that account - what email is on it?"}
    return {"customer": None, "ask": f"I found {len(hits)} accounts named {name}. What's the email or order number?"}


SCENARIOS = {  # Step 4
    "frustrated_simple": ("This is the third time my parcel is late and I'm furious!", "late delivery; credit policy exists"),
    "calm_policy_gap": ("Could I return a gift bought abroad in another currency?", "policy does not cover foreign-currency gifts"),
    "explicit_human": ("I want to talk to a human, please.", ""),
    "ambiguous_match": ("I'm John Smith, where's my order?", "3 records named John Smith"),
}

PRACTICE = {
    "question": "First-contact resolution is 55% (target 80%): the agent escalates simple damage replacements but tries "
                "complex policy exceptions itself. Most effective change?",
    "options": {"A": "Explicit escalation criteria with few-shot examples in the system prompt",
                "B": "Train a classifier", "C": "Sentiment-triggered escalation", "D": "Route on self-reported confidence"},
    "answer": "A",
    "why": "Prompt-level criteria and examples come before infrastructure; sentiment and confidence measure the wrong thing.",
}


# ---- mock model: follows the system prompt's rules -------------------------------------------------

def mock_model(kwargs: dict):
    msg = last_user_text(kwargs).lower()
    if "human" in msg or "person" in msg:
        return json_message({"action": "escalate", "reason": "explicit request for a human"})
    if "records named" in msg:
        return json_message({"action": "ask_identifier", "reason": "multiple matching customers"})
    if "does not cover" in msg or "says nothing" in msg:
        return json_message({"action": "escalate", "reason": "policy gap"})
    return json_message({"action": "resolve", "reason": "covered by policy; acknowledge frustration and resolve now"})


def main():
    print(mode_banner())
    for name, (msg, ctx) in SCENARIOS.items():
        print(f"step 4 {name:18s} -> {decide(get_client(mock_model), msg, ctx)}")
    print(f"step 3 match 'John Smith'        -> {match_customer('John Smith')}")
    print(f"       with email jsmith@...     -> {match_customer('John Smith', 'jsmith@example.net')['customer']['id']}")


if __name__ == "__main__":
    main()
