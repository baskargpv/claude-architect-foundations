"""Task 1.1 — the correct agentic loop: stop_reason decides, nothing else.

    (a) send full history  (b) inspect stop_reason
    (c) "tool_use"  -> run tools, append assistant turn + tool_result turn, send again
    (d) "end_turn"  -> done

tool_choice is left unset (defaults to "auto") so end_turn stays reachable.
The iteration cap is a safety net that raises; it is never the normal exit.

Other modules reuse run_agent() with their own tools/executor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from common import config
from common.client import get_client, mode_banner, response_text
from common.mock import last_tool_results, message, text, tool_use

ORDERS = {
    "A-100": {"status": "shipped", "carrier": "UPS", "eta": "2026-10-10"},
    "B-200": {"status": "processing", "eta": "2026-10-14"},
}

TOOLS = [
    {
        "name": "get_order_status",
        "description": (
            "Look up the current fulfilment status of ONE order by its order ID (e.g. 'A-100'). "
            "Returns status, carrier and ETA. Call once per order; calls for different orders can run in parallel."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID such as 'A-100'"}},
            "required": ["order_id"],
        },
    }
]


def execute_tool(name: str, tool_input: dict) -> dict:
    if name == "get_order_status":
        order = ORDERS.get(tool_input["order_id"])
        if order is None:
            return {"is_error": True, "error": f"order {tool_input['order_id']} not found"}
        return {"order_id": tool_input["order_id"], **order}
    return {"is_error": True, "error": f"unknown tool {name}"}


class IterationCapReached(RuntimeError):
    """Safety net tripped. In a healthy loop this never happens."""


@dataclass
class AgentResult:
    final_text: str
    stop_reason: str
    iterations: int
    messages: list
    tool_calls: list = field(default_factory=list)  # (tool_use_id, name, input)


def run_agent(
    client,
    user_message: str,
    tools: list = TOOLS,
    execute: Callable[[str, dict], dict] = execute_tool,
    system: str | None = None,
    max_iterations: int = 10,
    history: list | None = None,
) -> AgentResult:
    # history = prior turns to resend (the API is stateless: full history every request)
    messages: list = list(history or []) + [{"role": "user", "content": user_message}]
    tool_calls: list = []

    for iteration in range(1, max_iterations + 1):
        request = dict(model=config.model(), max_tokens=config.MAX_TOKENS, tools=tools, messages=messages)
        if system:
            request["system"] = system
        # NOTE: no tool_choice -> "auto". Forcing "any" would make end_turn unreachable.
        response = client.messages.create(**request)

        # Entry 1 of 2: Claude's own turn (text AND tool_use blocks), role "assistant".
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return AgentResult(response_text(response), "end_turn", iteration, messages, tool_calls)

        if response.stop_reason == "tool_use":
            results = []
            # Look at EVERY block, not content[0] - text can precede the tool_use blocks.
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_calls.append((block.id, block.name, block.input))
                output = execute(block.name, block.input)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,  # correlates each result with its request
                        "content": json.dumps(output),
                        "is_error": bool(output.get("is_error")),
                    }
                )
            # Entry 2 of 2: ONE new user message holding every tool_result.
            messages.append({"role": "user", "content": results})
            continue

        # max_tokens, refusal, pause_turn ...: surface it rather than guessing.
        return AgentResult(response_text(response), response.stop_reason, iteration, messages, tool_calls)

    raise IterationCapReached(f"no end_turn after {max_iterations} iterations")


# ---- mock model ------------------------------------------------------------------------

def mock_model(kwargs: dict):
    """Behaves like Claude on this task.

    Turn 1: text AND two parallel tool_use blocks in the SAME response (the case
    that breaks a content[0].type == "text" check). After tool results: end_turn.
    If forced with tool_choice "any" it must call a tool every time, so it never finishes.
    """
    if (kwargs.get("tool_choice") or {}).get("type") == "any":
        return message(tool_use("get_order_status", {"order_id": "A-100"}))
    results = last_tool_results(kwargs)
    if not results:
        return message(
            text("Let me check both orders."),
            tool_use("get_order_status", {"order_id": "A-100"}),
            tool_use("get_order_status", {"order_id": "B-200"}),
        )
    statuses = [json.loads(r["content"]) for r in results]
    summary = "; ".join(f"{s['order_id']} is {s['status']} (ETA {s['eta']})" for s in statuses)
    return message(text(f"Here's where things stand: {summary}."))


QUESTION = "Where are my orders A-100 and B-200?"


def main():
    print(mode_banner())
    result = run_agent(get_client(mock_model), QUESTION)
    print(f"stop_reason={result.stop_reason} iterations={result.iterations}")
    for tool_use_id, name, tool_input in result.tool_calls:
        print(f"  ran {name}({tool_input}) id={tool_use_id}")
    print(f"answer: {result.final_text}")


if __name__ == "__main__":
    main()
