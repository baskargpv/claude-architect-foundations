"""Offline stand-in for anthropic.Anthropic.

Responses are real ``anthropic.types.Message`` objects, so code under test
reads exactly the same shape (``stop_reason``, ``content[i].type`` ...) in
mock and live mode.
"""

from __future__ import annotations

import copy
import itertools
import json
from typing import Any, Callable

from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

_ids = itertools.count(1)


def text(t: str) -> TextBlock:
    return TextBlock(type="text", text=t, citations=None)


def tool_use(name: str, input: dict, id: str | None = None) -> ToolUseBlock:
    return ToolUseBlock(type="tool_use", id=id or f"toolu_mock_{next(_ids)}", name=name, input=input)


def message(*blocks, stop_reason: str | None = None) -> Message:
    """Build a Message; stop_reason defaults to tool_use if any tool_use block is present."""
    if stop_reason is None:
        stop_reason = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return Message(
        id=f"msg_mock_{next(_ids)}",
        type="message",
        role="assistant",
        model="mock",
        content=list(blocks),
        stop_reason=stop_reason,
        stop_sequence=None,
        usage=Usage(input_tokens=0, output_tokens=0),
    )


def json_message(data: Any) -> Message:
    """A text reply containing JSON, as structured output (output_config.format) returns."""
    return message(text(json.dumps(data)))


# ---- helpers for writing responders -------------------------------------------------

def prompt_text(kwargs: dict) -> str:
    """Every string the request carries (system + all text/tool_result content), joined."""
    parts: list[str] = []
    system = kwargs.get("system")
    if isinstance(system, str):
        parts.append(system)
    for m in kwargs.get("messages", []):
        parts.append(_content_text(m["content"]))
    return "\n".join(parts)


def last_user_text(kwargs: dict) -> str:
    return _content_text(kwargs["messages"][-1]["content"])


def last_tool_results(kwargs: dict) -> list[dict]:
    """tool_result blocks in the latest user message (empty if none)."""
    content = kwargs["messages"][-1]["content"]
    if isinstance(content, str):
        return []
    return [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for b in content:
        if isinstance(b, dict):
            c = b.get("text") or b.get("content") or ""
            out.append(c if isinstance(c, str) else json.dumps(c))
        elif getattr(b, "type", None) == "text":
            out.append(b.text)
        elif getattr(b, "type", None) == "tool_use":
            out.append(json.dumps(b.input))
    return "\n".join(out)


# ---- the client ------------------------------------------------------------------------

Responder = Callable[[dict], Message]


class _Messages:
    def __init__(self, parent: "MockClient"):
        self._parent = parent

    def create(self, **kwargs) -> Message:
        self._parent.calls.append(copy.deepcopy(kwargs))
        return self._parent._next(kwargs)


class MockClient:
    """Replays a scripted list of Messages, or calls a responder(kwargs) -> Message.

    ``calls`` records a deep copy of every request so tests can assert on
    exactly what was sent (prompts, tool_choice, history ...).
    """

    def __init__(self, script: list[Message] | Responder):
        self.calls: list[dict] = []
        self._script = script if callable(script) else iter(script)
        self.messages = _Messages(self)

    def _next(self, kwargs: dict) -> Message:
        if callable(self._script):
            return self._script(kwargs)
        try:
            return next(self._script)
        except StopIteration:
            raise RuntimeError("MockClient script exhausted - the code made more calls than scripted") from None
