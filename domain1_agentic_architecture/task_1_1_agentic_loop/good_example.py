"""Task 1.1 — Build a Multi-Tool Agent Loop (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-1-agentic-loops

The loop is deterministic control flow in code; stop_reason is the only signal that
decides whether it continues. Other tasks reuse run_agent() with their own tools.
"""

from __future__ import annotations

import ast
import json
import logging
import operator
from dataclasses import dataclass, field
from typing import Callable

from common import config
from common.client import get_client, mode_banner, response_text
from common.mock import last_tool_results, last_user_text, message, text, tool_use

log = logging.getLogger(__name__)

# ---- Step 1: two tools, each with a name, description and JSON Schema input_schema ----------

TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression (+ - * / ** and parentheses). "
                       "Use for any numeric calculation; returns the numeric result.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "e.g. '330 * 3.28084'"}},
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for facts. Returns a short list of result snippets with URLs. "
                       "Use it to look up a value before calculating with it.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

SEARCH_INDEX = {  # the web search is a stub, as the exercise specifies
    "eiffel tower height": [{"url": "https://example.org/eiffel", "snippet": "The Eiffel Tower is 330 metres tall."}],
    "great wall length": [{"url": "https://example.org/wall", "snippet": "The Great Wall is about 21196 km long."}],
}

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg}


def calculate(expression: str) -> float:
    """Safe arithmetic evaluator - never eval() model-supplied strings."""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError(f"unsupported expression: {expression}")
    return ev(ast.parse(expression, mode="eval").body)


def execute_tool(name: str, tool_input: dict) -> dict:
    try:
        if name == "calculator":
            return {"result": round(calculate(tool_input["expression"]), 4)}
        if name == "web_search":
            q = tool_input["query"].lower()
            hits = [r for key, results in SEARCH_INDEX.items() if key in q for r in results]
            return {"results": hits}
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        return {"is_error": True, "error": str(e)}
    return {"is_error": True, "error": f"unknown tool {name}"}


# ---- Steps 2-4 and 6: the loop --------------------------------------------------------------

MAX_ITERATIONS = 20  # Step 6: a safety bound, never the stop mechanism

# Current docs: values beyond the exam's tool_use / end_turn. All mean "not finished - find out why".
INCOMPLETE_STOP_REASONS = {"max_tokens", "stop_sequence", "refusal", "model_context_window_exceeded"}


@dataclass
class AgentResult:
    final_text: str
    stop_reason: str
    iterations: int
    messages: list
    tool_calls: list = field(default_factory=list)  # (tool_use_id, name, input)
    complete: bool = False
    hit_safety_cap: bool = False


def run_agent(
    client,
    user_message: str,
    tools: list = TOOLS,
    execute: Callable[[str, dict], dict] = execute_tool,
    system: str | None = None,
    history: list | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> AgentResult:
    # The API is stateless: every request carries the full history.
    messages: list = list(history or []) + [{"role": "user", "content": user_message}]
    tool_calls: list = []

    for iteration in range(1, max_iterations + 1):
        request = dict(model=config.model(), max_tokens=config.MAX_TOKENS, tools=tools, messages=messages)
        if system:
            request["system"] = system
        response = client.messages.create(**request)  # Step 2. No tool_choice -> "auto".
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":  # Step 4
            return AgentResult(response_text(response), "end_turn", iteration, messages, tool_calls, complete=True)

        if response.stop_reason == "tool_use":  # Step 3
            results = []
            for block in response.content:  # every block - text may precede the tool_use blocks
                if block.type != "tool_use":
                    continue
                tool_calls.append((block.id, block.name, block.input))
                output = execute(block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(output), "is_error": bool(output.get("is_error"))})
            messages.append({"role": "user", "content": results})  # one user message, all results
            continue

        if response.stop_reason == "pause_turn":  # server tool paused a long turn: resend to continue
            continue

        # max_tokens / stop_sequence / refusal / model_context_window_exceeded: surface, don't guess
        return AgentResult(response_text(response), response.stop_reason, iteration, messages, tool_calls)

    log.warning("agent hit MAX_ITERATIONS=%d without end_turn - investigate a runaway loop", max_iterations)
    return AgentResult("", "safety_cap", max_iterations, messages, tool_calls, hit_safety_cap=True)


# ---- Step 5: a prompt where one tool's output feeds the next --------------------------------

QUESTION = "How tall is the Eiffel Tower in feet? Look up its height first, then convert it."

PRACTICE = {
    "question": "An agent ends early when Claude returns text alongside a tool call; the loop checks "
                "response.content[0].type == 'text'. What should change?",
    "options": {
        "A": "Add an iteration cap of 15 loops",
        "B": "Check stop_reason: continue on tool_use, terminate on end_turn",
        "C": "Set tool_choice to any",
        "D": "Parse the assistant text for completion phrases",
    },
    "answer": "B",
    "why": "Only stop_reason reliably says whether Claude is finished; A is a safety net, C makes "
           "end_turn unreachable, D is ambiguous natural-language parsing.",
}


# ---- mock model -----------------------------------------------------------------------------

def mock_model(kwargs: dict):
    """Behaves like Claude here: text + tool_use in one response, then a dependent second call."""
    if (kwargs.get("tool_choice") or {}).get("type") == "any":  # forced: must call a tool every turn
        return message(tool_use("web_search", {"query": "Eiffel Tower height"}))
    results = last_tool_results(kwargs)
    if not results:
        if last_user_text(kwargs) == "Continue.":
            return message(text("The Eiffel Tower is about 1082.68 feet tall."))
        return message(text("Let me look that up."), tool_use("web_search", {"query": "Eiffel Tower height"}))
    last = json.loads(results[-1]["content"])
    if "results" in last:
        metres = last["results"][0]["snippet"].split(" is ")[1].split(" ")[0]
        return message(tool_use("calculator", {"expression": f"{metres} * 3.28084"}))
    return message(text(f"The Eiffel Tower is about {last['result']:.2f} feet tall (330 m)."))


def main():
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    print(mode_banner())
    result = run_agent(get_client(mock_model), QUESTION)
    print(f"stop_reason={result.stop_reason} iterations={result.iterations} complete={result.complete}")
    for tool_use_id, name, tool_input in result.tool_calls:
        print(f"  {name}({tool_input})  id={tool_use_id}")
    print(f"answer: {result.final_text}")


if __name__ == "__main__":
    main()
