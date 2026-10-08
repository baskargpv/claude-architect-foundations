"""Task 2.1 — Tool Interface Design (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-1-tool-schema-design

Tool descriptions are the main thing the model uses to pick a tool. Vague descriptions
cause misrouting; the first fix is to expand them, not to add few-shot examples,
a routing classifier, or to merge tools.
"""

from __future__ import annotations

import re

from mcp.server.mcpserver import MCPServer

from common import config
from common.client import get_client, mode_banner
from common.mcp_util import tool_defs
from common.mock import message, tool_use

# ---- Step 1: two MCP tools with deliberately ambiguous one-line descriptions ----------------

VAGUE = {
    "get_customer": "Retrieves customer information and order history.",
    "lookup_order": "Retrieves details.",
}

# ---- Step 3: rewritten - purpose, input formats, examples, edge cases, boundary -------------

CLEAR = {
    "get_customer": (
        "Look up a customer's account profile: name, email, phone, loyalty tier, account status. "
        "Input: an email address, a phone number, or a customer ID like C-1042. "
        "Examples: 'update the email on my account', 'what loyalty tier am I'. "
        "Does not return shipping or delivery status. "
        "For a specific order number or tracking ID, use lookup_order instead."
    ),
    "lookup_order": (
        "Look up one order's status, delivery date and shipping progress. "
        "Input: an order number like #12345, or a carrier tracking ID like 1Z999AA10123456784. "
        "Examples: 'check my order #12345', 'track 1Z12345E0205271688', 'is my delivery late'. "
        "Returns nothing about the customer's account or profile. "
        "For account details (email, phone, tier) use get_customer instead."
    ),
}


def build_server(descriptions: dict[str, str]) -> MCPServer:
    srv = MCPServer("support")

    def get_customer(identifier: str) -> dict:
        return {"customer_id": "C-1042", "email": "jane@example.com", "tier": "gold"}

    def lookup_order(identifier: str) -> dict:
        return {"order": identifier, "status": "shipped", "eta": "2026-10-12"}

    srv.add_tool(get_customer, description=descriptions["get_customer"])
    srv.add_tool(lookup_order, description=descriptions["lookup_order"])
    return srv


# ---- Step 2: run 10 varied queries and log which tool gets picked -----------------------------

QUERIES = [  # (query, correct tool)
    ("Check my order #12345", "lookup_order"),
    ("Where is package 1Z999AA10123456784?", "lookup_order"),
    ("Update the email on my account jane@example.com", "get_customer"),
    ("What's the status of order #55821?", "lookup_order"),
    ("Find the customer with phone 555-0142", "get_customer"),
    ("Has #77310 shipped yet?", "lookup_order"),
    ("Show account details for C-1042", "get_customer"),
    ("Track 1Z12345E0205271688", "lookup_order"),
    ("What loyalty tier is jane@example.com?", "get_customer"),
    ("Is my delivery for #10001 late?", "lookup_order"),
]


def pick_tool(client, query: str, tools: list[dict], system: str | None = None) -> str:
    kwargs = dict(model=config.model(), max_tokens=1024, tools=tools,
                  messages=[{"role": "user", "content": query}])
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return next((b.name for b in response.content if b.type == "tool_use"), "none")


def evaluate(client, tools: list[dict], system: str | None = None) -> dict:
    picks = [(q, pick_tool(client, q, tools, system), want) for q, want in QUERIES]
    return {"accuracy": sum(got == want for _, got, want in picks) / len(picks), "picks": picks}


# ---- Step 5: look for keyword-sensitive system prompt instructions -----------------------------

def find_keyword_conflicts(system_prompt: str) -> list[str]:
    """Absolute instructions ('always', 'first', 'before') that name a tool's subject."""
    sentences = re.split(r"(?<=[.!?])\s+", system_prompt)
    return [s for s in sentences if re.search(r"\b(always|never|first|before)\b", s, re.I)
            and re.search(r"\b(customer|account|order)\b", s, re.I)]


PRACTICE = {
    "question": "The agent calls get_customer for 'check my order #12345' because both tools have minimal "
                "descriptions. Best first step?",
    "options": {"A": "Add few-shot examples of correct routing", "B": "Build a routing classifier",
                "C": "Expand each description with inputs, examples, edge cases and boundaries",
                "D": "Merge both tools into one"},
    "answer": "C",
    "why": "Descriptions are the root cause and the cheapest fix; the others are heavier or don't address why the model is confused.",
}


# ---- mock model: picks a tool by reading the descriptions, like Claude does ---------------------

ID_PATTERNS = {  # identifier in the query -> words a description must mention to claim it
    r"#\d{5}": "order number", r"\b1Z\w{10,}": "tracking id", r"[\w.]+@\w+\.\w+": "email",
    r"\b\d{3}-\d{4}\b": "phone", r"\bC-\d{4}\b": "customer id",
}
STOP = {"the", "my", "is", "for", "what", "with", "has", "yet", "on", "of", "a", "an", "s"}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower())) - STOP


def mock_model(kwargs: dict):
    query, tools = kwargs["messages"][0]["content"], kwargs["tools"]
    system = kwargs.get("system", "")
    if re.search(r"always check customer", system, re.I):  # keyword instruction overrides descriptions
        return message(tool_use("get_customer", {"identifier": query}))
    for name, example_tool in re.findall(r"Example: '([^']+)' -> (\w+)", system):  # few-shot examples
        if any(re.search(p, name) and re.search(p, query) for p in ID_PATTERNS):
            return message(tool_use(example_tool, {"identifier": query}))
    for pattern, cue in ID_PATTERNS.items():  # 1) a description whose Input: section claims this format
        if re.search(pattern, query):
            for t in tools:
                inputs = t["description"].split("Input:")[1].split("Examples:")[0] if "Input:" in t["description"] else ""
                if cue in inputs.lower():
                    return message(tool_use(t["name"], {"identifier": query}))
    scores = [(len(_words(query) & _words(t["description"])), -i, t["name"]) for i, t in enumerate(tools)]
    return message(tool_use(max(scores)[2], {"identifier": query}))  # 2) otherwise: best word overlap


def main():
    print(mode_banner())
    before = evaluate(get_client(mock_model), tool_defs(build_server(VAGUE)))
    after = evaluate(get_client(mock_model), tool_defs(build_server(CLEAR)))
    print(f"step 2 vague descriptions : accuracy {before['accuracy']:.0%}")
    for q, got, want in before["picks"]:
        if got != want:
            print(f"    misrouted: {q!r} -> {got}")
    print(f"step 4 clear descriptions : accuracy {after['accuracy']:.0%}")
    system = "You are a support agent. Always check customer details before proceeding."
    print(f"step 5 system prompt conflicts: {find_keyword_conflicts(system)}")


if __name__ == "__main__":
    main()
