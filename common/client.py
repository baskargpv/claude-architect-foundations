"""get_client(): the real Anthropic client when live, a MockClient otherwise."""

from __future__ import annotations

import json
from typing import Any

from common import config
from common.mock import MockClient, Responder


def get_client(mock: Responder | list | None = None):
    """Return anthropic.Anthropic() if ANTHROPIC_API_KEY is set, else MockClient(mock)."""
    if config.is_live():
        import anthropic

        return anthropic.Anthropic()
    if mock is None:
        raise RuntimeError("Mock mode needs a responder - pass mock=... (or set ANTHROPIC_API_KEY)")
    return MockClient(mock)


def mode_banner() -> str:
    return f"[live: {config.model()}]" if config.is_live() else "[mock mode - set ANTHROPIC_API_KEY to run live]"


def response_text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def ask_json(client, prompt: str, schema: dict, system: str | None = None) -> Any:
    """One structured-output call: output_config.format guarantees parseable JSON text."""
    kwargs: dict = dict(
        model=config.model(),
        max_tokens=config.MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
    )
    if system:
        kwargs["system"] = system
    return json.loads(response_text(client.messages.create(**kwargs)))
