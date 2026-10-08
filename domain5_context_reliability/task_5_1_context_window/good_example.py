"""Task 5.1 — Context Window Management (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-1-context-window-management

Summaries destroy amounts, dates and IDs -> keep them in a case-facts block sent with EVERY prompt.
Trim verbose tool results before they enter history. Put a key-findings summary at the top of
aggregated input (lost-in-the-middle is fixed by structure, not by asking for attention).
"""

from __future__ import annotations

import json
import re

from common import config
from common.client import get_client, mode_banner, response_text
from common.mock import message, text

# ---- the verbose tool result (40+ fields) ------------------------------------------------------

ORDER_LOOKUP = {"order_id": "8891", "customer_id": "C-5512", "order_date": "2026-03-03", "total_amount": 247.83,
                "return_eligible": True, "item_description": "Espresso machine, model EX-200", "status": "delivered",
                **{f"internal_field_{i}": f"value {i}" for i in range(40)}}

# ---- Steps 1-3: extract facts, trim results, always prepend the facts block -----------------------

def extract_case_facts(order: dict, requested_refund: float) -> dict:
    return {"customerId": order["customer_id"], "orderId": order["order_id"], "orderDate": order["order_date"],
            "refundAmount": requested_refund, "status": order["status"], "itemDescription": order["item_description"]}


KEEP = ("order_id", "order_date", "total_amount", "return_eligible", "item_description")


def trim(order: dict) -> dict:
    return {k: order[k] for k in KEEP}  # before it ever enters history


def build_system(case_facts: list[dict]) -> str:
    """One entry per issue, so summarisation can't blend them."""
    return "CASE FACTS (authoritative, never summarised):\n" + json.dumps(case_facts, indent=1)


def summarise(client, turns: list[dict]) -> str:
    convo = "\n".join(f"{t['role']}: {t['content']}" for t in turns)
    return response_text(client.messages.create(model=config.model(), max_tokens=512, messages=[
        {"role": "user", "content": f"[SUMMARISE] Summarise this conversation briefly:\n{convo}"}]))


def reply(client, system: str | None, history: list[dict], user_msg: str) -> str:
    kwargs = dict(model=config.model(), max_tokens=1024, messages=history + [{"role": "user", "content": user_msg}])
    if system:
        kwargs["system"] = system
    return response_text(client.messages.create(**kwargs))


CUSTOMER_TURNS = [
    "Hi, I'd like a refund of $247.83 for order #8891 placed on March 3rd.",
    "The espresso machine leaks from the bottom.",
    "I already tried descaling it.",
    "I'd prefer the money back rather than a replacement.",
    "How long will it take?",
    "Can you confirm the details of my refund?",
]


def run_conversation(client, use_facts_block: bool = True, summarise_after: int = 4) -> list[str]:
    """Step 4: 6 turns, history summarised after turn 4."""
    facts = [extract_case_facts(ORDER_LOOKUP, 247.83)]
    history, answers = [], []
    for i, msg in enumerate(CUSTOMER_TURNS, start=1):
        system = build_system(facts) if use_facts_block else None
        answer = reply(client, system, history, msg)
        history += [{"role": "user", "content": msg}, {"role": "assistant", "content": answer}]
        answers.append(answer)
        if i == summarise_after:
            history = [{"role": "user", "content": f"(Summary of earlier conversation: {summarise(client, history)})"},
                       {"role": "assistant", "content": "Understood."}]
    return answers


# ---- Step 5: aggregated input with a key-findings summary first --------------------------------------

def aggregate(sections: dict[str, str], key_findings: list[str]) -> str:
    out = "## Key Findings Summary\n" + "\n".join(f"- {k}" for k in key_findings) + "\n"
    return out + "\n".join(f"\n## {title}\n{body}" for title, body in sections.items())


PRACTICE = {
    "question": "After summarising history, the agent says 'your recent refund request' instead of the $247.83 refund "
                "for order #8891. Most effective fix?",
    "options": {"A": "Tell the summariser to keep numbers", "B": "A persistent case-facts block in every prompt",
                "C": "Retrieve the details from a database each turn", "D": "A larger context window"},
    "answer": "B",
    "why": "Facts kept outside the summarised history can't be compressed away.",
}


# ---- mock model (SIMULATED: summaries drop specifics; answers use whatever specifics are in context) -----

def mock_model(kwargs: dict):
    prompt = kwargs["messages"][-1]["content"]
    if prompt.startswith("[SUMMARISE]"):
        return message(text("The customer wants a refund for a recent order that is faulty."))
    context = kwargs.get("system", "") + json.dumps(kwargs["messages"])
    if "confirm the details" in prompt:
        amount = re.search(r"247\.83", context)
        order = re.search(r"8891", context)
        if amount and order:
            return message(text("Confirmed: refund of $247.83 for order #8891 placed 2026-03-03."))
        return message(text("Confirmed: your recent refund request is being processed."))
    return message(text("Thanks - noted."))


def main():
    print(mode_banner())
    print(f"step 3 trimmed {len(ORDER_LOOKUP)} fields -> {len(trim(ORDER_LOOKUP))}: {trim(ORDER_LOOKUP)}")
    print(f"step 4 with facts block   : {run_conversation(get_client(mock_model))[-1]}")
    print(f"       without facts block: {run_conversation(get_client(mock_model), use_facts_block=False)[-1]}")
    print("step 5 aggregated input:\n" + aggregate({"Web search": "...", "Document analysis": "...", "Interviews": "..."},
                                                   ["Refund policy allows 30 days", "Leak defect affects batch EX-200"]))


if __name__ == "__main__":
    main()
