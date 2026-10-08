"""Task 1.1 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-1-agentic-loops

Trap 1  content[0].type == "text" means done         -> quits before running the tools
Trap 2  an iteration cap as the primary stop           -> cuts off legitimate work
Trap 3  parsing phrases like "task complete"            -> wasted iterations (or false stops)
Trap 4  forcing tool_choice "any"                      -> end_turn unreachable
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


def _create(client, messages, **extra):
    return client.messages.create(model=config.model(), max_tokens=config.MAX_TOKENS, tools=TOOLS,
                                  messages=messages, **extra)


def _run_tools(response) -> tuple[list, list]:
    calls, results = [], []
    for b in response.content:
        if b.type == "tool_use":
            calls.append((b.id, b.name, b.input))
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(execute_tool(b.name, b.input))})
    return calls, results


def trap1_content_type_check(client, question: str = QUESTION) -> AgentResult:
    messages, calls = [{"role": "user", "content": question}], []
    for i in range(1, 21):
        response = _create(client, messages)
        messages.append({"role": "assistant", "content": response.content})
        if response.content[0].type == "text":  # WRONG: "Let me look that up." + a tool_use block
            return AgentResult(response_text(response), response.stop_reason, i, messages, calls)
        new, results = _run_tools(response)
        calls += new
        messages.append({"role": "user", "content": results})
    return AgentResult("", "cap", 20, messages, calls)


def trap2_cap_as_primary_stop(client, question: str = QUESTION, cap: int = 2) -> AgentResult:
    messages, calls, response = [{"role": "user", "content": question}], [], None
    for _ in range(cap):  # WRONG: the cap IS the exit condition; stop_reason is ignored
        response = _create(client, messages)
        messages.append({"role": "assistant", "content": response.content})
        new, results = _run_tools(response)
        calls += new
        if results:
            messages.append({"role": "user", "content": results})
    return AgentResult(response_text(response), response.stop_reason, cap, messages, calls)


def trap3_parse_completion_phrase(client, question: str = QUESTION, safety_cap: int = 6) -> AgentResult:
    messages, calls = [{"role": "user", "content": question}], []
    for i in range(1, safety_cap + 1):
        response = _create(client, messages)
        messages.append({"role": "assistant", "content": response.content})
        if "task complete" in response_text(response).lower():  # WRONG: natural language is ambiguous
            return AgentResult(response_text(response), response.stop_reason, i, messages, calls, complete=True)
        new, results = _run_tools(response)
        calls += new
        # Claude already said end_turn, but the phrase never appeared - so we nag it to continue.
        messages.append({"role": "user", "content": results or "Continue."})
    return AgentResult(response_text(response), "cap", safety_cap, messages, calls)


def trap4_force_tool_choice_any(client, question: str = QUESTION, safety_cap: int = 5) -> AgentResult:
    messages, calls = [{"role": "user", "content": question}], []
    for i in range(1, safety_cap + 1):
        response = _create(client, messages, tool_choice={"type": "any"})  # WRONG for a whole loop
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "end_turn":
            return AgentResult(response_text(response), "end_turn", i, messages, calls, complete=True)
        new, results = _run_tools(response)
        calls += new
        messages.append({"role": "user", "content": results})
    return AgentResult("", "cap", safety_cap, messages, calls)


def main():
    import anthropic

    print(mode_banner())
    r = trap1_content_type_check(get_client(mock_model))
    print(f"trap 1 content[0] check : tools={len(r.tool_calls)} answer={r.final_text!r}  <- quit before looking anything up")
    r = trap2_cap_as_primary_stop(get_client(mock_model))
    print(f"trap 2 cap as exit      : tools={len(r.tool_calls)} stop_reason={r.stop_reason} answer={r.final_text!r}  <- cut off")
    r = trap3_parse_completion_phrase(get_client(mock_model))
    print(f"trap 3 phrase parsing   : {r.iterations} requests for a 3-request job, stopped by {r.stop_reason!r}")
    try:
        r = trap4_force_tool_choice_any(get_client(mock_model))
        print(f"trap 4 tool_choice any  : stopped by {r.stop_reason!r} after {len(r.tool_calls)} forced tool calls, no answer")
    except anthropic.BadRequestError as e:  # current docs: newest models reject forced tool_choice
        print(f"trap 4 tool_choice any  : rejected by the API on {config.model()}: {e.message}")


if __name__ == "__main__":
    main()
