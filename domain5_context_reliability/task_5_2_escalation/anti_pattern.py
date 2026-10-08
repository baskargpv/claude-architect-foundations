"""Task 5.2 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-2-escalation-ambiguity

Trap 1  sentiment-based escalation
Trap 2  self-reported confidence as the escalation signal
Trap 3  trying to resolve before honouring an explicit request for a human
Trap 4  picking the most recent / most active record from ambiguous matches
"""

from __future__ import annotations

from domain5_context_reliability.task_5_2_escalation.good_example import CUSTOMERS, SCENARIOS

ANGRY = ("furious", "third time", "ridiculous", "!")


def sentiment_router(message_: str) -> str:
    return "escalate" if any(w in message_.lower() for w in ANGRY) else "resolve"


def trap1_sentiment() -> dict:
    return {name: sentiment_router(msg) for name, (msg, _) in SCENARIOS.items() if name != "ambiguous_match"}


# SIMULATED self-reported confidence: sure about the hard case, unsure about the easy one
SELF_CONFIDENCE = {"frustrated_simple": 0.55, "calm_policy_gap": 0.9}


def trap2_confidence_router(threshold: float = 0.7) -> dict:
    return {k: ("escalate" if c < threshold else "resolve") for k, c in SELF_CONFIDENCE.items()}


def trap3_investigate_first() -> dict:
    steps = ["lookup_customer", "lookup_orders", "check_policy", "offer_resolution", "escalate"]
    return {"steps_before_escalating": steps.index("escalate"), "first_response_escalates": steps[0] == "escalate"}


def trap4_pick_most_recent(name: str = "John Smith") -> dict:
    hits = [c for c in CUSTOMERS if c["name"] == name]
    chosen = max(hits, key=lambda c: c["last_order"])
    return {"matches": len(hits), "picked": chosen["id"], "risk": "may expose another customer's data or refund the wrong account"}


def main():
    print(f"trap 1 sentiment     : {trap1_sentiment()}  <- escalates the easy one")
    print(f"trap 2 confidence    : {trap2_confidence_router()}  <- escalates easy, attempts the policy gap")
    print(f"trap 3 investigate   : {trap3_investigate_first()}")
    print(f"trap 4 most recent   : {trap4_pick_most_recent()}")


if __name__ == "__main__":
    main()
