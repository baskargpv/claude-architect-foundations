"""Task 2.1 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-1-tool-schema-design

Trap 1  few-shot examples to fix misrouting caused by minimal descriptions
Trap 2  a routing classifier as the first fix
Trap 3  consolidating the tools as the first fix
Trap 4  ignoring the system prompt after fixing the descriptions
"""

from __future__ import annotations

import re

from mcp.server.mcpserver import MCPServer

from common.client import get_client, mode_banner
from common.mcp_util import tool_defs
from domain2_tool_design_mcp.task_2_1_tool_interface_design.good_example import (
    CLEAR,
    QUERIES,
    VAGUE,
    build_server,
    evaluate,
    mock_model,
)

FEW_SHOT_SYSTEM = ("Example: 'check my order #12345' -> lookup_order\n"
                   "Example: 'update jane@example.com' -> get_customer")


def trap1_few_shot(client) -> dict:
    """Extra tokens on every request; only the cases the examples happen to cover get fixed."""
    result = evaluate(client, tool_defs(build_server(VAGUE)), system=FEW_SHOT_SYSTEM)
    return {**result, "extra_prompt_chars": len(FEW_SHOT_SYSTEM)}


def classify(query: str) -> str:
    return "lookup_order" if re.search(r"#\d+", query) else "get_customer"  # hand-written rules, no model


def trap2_routing_classifier() -> dict:
    """More infrastructure, and it misses phrasings nobody wrote a rule for (tracking IDs, 'delivery')."""
    picks = [(q, classify(q), want) for q, want in QUERIES]
    return {"accuracy": sum(g == w for _, g, w in picks) / len(picks),
            "misses": [q for q, g, w in picks if g != w]}


def trap3_consolidate_first(client) -> dict:
    """One `lookup(kind, identifier)` tool with the same vague wording: the choice just moves into a parameter."""
    srv = MCPServer("support")

    def lookup(kind: str, identifier: str) -> dict:
        return {}
    srv.add_tool(lookup, description="Retrieves customer information and order history.")
    tools = tool_defs(srv)
    kinds = []
    for q, want in QUERIES:
        # with no description telling them apart, the model has no basis for `kind` either
        resp = mock_model({"messages": [{"role": "user", "content": q}],
                           "tools": [{"name": "get_customer", "description": VAGUE["get_customer"]},
                                     {"name": "lookup_order", "description": VAGUE["lookup_order"]}]})
        kinds.append((resp.content[0].name, want))
    return {"tools_after_merge": len(tools), "accuracy": sum(g == w for g, w in kinds) / len(kinds)}


def trap4_ignore_system_prompt(client) -> dict:
    """Clear descriptions - but the system prompt still says 'always check customer details'."""
    return evaluate(client, tool_defs(build_server(CLEAR)),
                    system="You are a support agent. Always check customer details before proceeding.")


def main():
    print(mode_banner())
    r = trap1_few_shot(get_client(mock_model))
    print(f"trap 1 few-shot        : accuracy {r['accuracy']:.0%}, +{r['extra_prompt_chars']} chars on every call")
    r = trap2_routing_classifier()
    print(f"trap 2 classifier      : accuracy {r['accuracy']:.0%}, misses {r['misses'][:2]}...")
    r = trap3_consolidate_first(get_client(mock_model))
    print(f"trap 3 consolidate     : {r['tools_after_merge']} tool, still {r['accuracy']:.0%} correct")
    r = trap4_ignore_system_prompt(get_client(mock_model))
    print(f"trap 4 system prompt   : accuracy {r['accuracy']:.0%} despite clear descriptions")


if __name__ == "__main__":
    main()
