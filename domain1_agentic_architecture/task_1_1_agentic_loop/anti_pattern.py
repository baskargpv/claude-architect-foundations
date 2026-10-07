"""Task 1.1 — three broken loop-exit strategies the exam uses as distractors.

1. content[0].type == "text" means done   -> exits before running tools Claude asked for
2. tool_choice {"type": "any"} every turn -> end_turn unreachable; only the cap stops it
3. iteration cap as the real exit          -> cuts off genuine work mid-task
"""

from __future__ import annotations

import json

from common import config
from common.client import get_client, mode_banner, response_text
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import (
    QUESTION,
    TOOLS,
    AgentResult,
    execute_tool,
    mock_model,
)


def _run_tools(response) -> tuple[list, list]:
    calls, results = [], []
    for b in response.content:
        if b.type == "tool_use":
            calls.append((b.id, b.name, b.input))
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(execute_tool(b.name, b.input))})
    return calls, results


def run_agent_text_check(client, user_message: str, max_iterations: int = 10) -> AgentResult:
    """ANTI-PATTERN 1: treats a leading text block as 'finished'."""
    messages: list = [{"role": "user", "content": user_message}]
    calls: list = []
    for i in range(1, max_iterations + 1):
        response = client.messages.create(model=config.model(), max_tokens=config.MAX_TOKENS, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": response.content})
        if response.content[0].type == "text":  # WRONG: tool_use blocks may follow the text
            return AgentResult(response_text(response), response.stop_reason, i, messages, calls)
        new_calls, results = _run_tools(response)
        calls += new_calls
        messages.append({"role": "user", "content": results})
    return AgentResult("", "cap", max_iterations, messages, calls)


def run_agent_forced_tool(client, user_message: str, max_iterations: int = 5) -> AgentResult:
    """ANTI-PATTERN 2: tool_choice "any" for the whole loop - Claude can never end_turn."""
    messages: list = [{"role": "user", "content": user_message}]
    calls: list = []
    for i in range(1, max_iterations + 1):
        response = client.messages.create(
            model=config.model(),
            max_tokens=config.MAX_TOKENS,
            tools=TOOLS,
            tool_choice={"type": "any"},  # WRONG for a whole loop: forces a tool call every turn
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "end_turn":
            return AgentResult(response_text(response), "end_turn", i, messages, calls)
        new_calls, results = _run_tools(response)
        calls += new_calls
        messages.append({"role": "user", "content": results})
    # Only the cap stopped us - a self-inflicted infinite loop.
    return AgentResult("", "cap", max_iterations, messages, calls)


def run_agent_cap_only(client, user_message: str, iterations: int = 1) -> AgentResult:
    """ANTI-PATTERN 3: a fixed number of rounds IS the exit condition; stop_reason ignored."""
    messages: list = [{"role": "user", "content": user_message}]
    calls: list = []
    response = None
    for _ in range(iterations):
        response = client.messages.create(model=config.model(), max_tokens=config.MAX_TOKENS, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": response.content})
        new_calls, results = _run_tools(response)
        calls += new_calls
        if results:
            messages.append({"role": "user", "content": results})
    # Tools ran, but Claude never got to read their results and answer.
    return AgentResult(response_text(response), response.stop_reason, iterations, messages, calls)


def main():
    import anthropic

    print(mode_banner())

    r = run_agent_text_check(get_client(mock_model), QUESTION)
    print(f"1) content[0] check: tools run={len(r.tool_calls)} answer={r.final_text!r}  <- quit before looking anything up")

    try:
        r = run_agent_forced_tool(get_client(mock_model), QUESTION)
        print(f"2) tool_choice any: stopped by {r.stop_reason!r} after {r.iterations} iterations, {len(r.tool_calls)} tool calls, no answer")
    except anthropic.BadRequestError as e:
        # Current docs: claude-sonnet-5-5 rejects forced tool_choice outright.
        print(f"2) tool_choice any: API rejected it on {config.model()} -> {e.message}")

    r = run_agent_cap_only(get_client(mock_model), QUESTION, iterations=1)
    print(f"3) cap as exit: tools run={len(r.tool_calls)} stop_reason={r.stop_reason!r} answer={r.final_text!r}  <- cut off mid-task")


if __name__ == "__main__":
    main()
