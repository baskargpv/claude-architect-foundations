"""Model selection and mock/live switch shared by every demo."""

import os

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 16000


def model() -> str:
    """Model ID for live runs. Override with ANTHROPIC_MODEL."""
    return os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)


def is_live() -> bool:
    """Live when an API key is present, unless CCA_FORCE_MOCK=1 (tests set this)."""
    if os.environ.get("CCA_FORCE_MOCK") == "1":
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
