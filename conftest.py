"""Force every test into offline mock mode, even if ANTHROPIC_API_KEY is set."""

import pytest


@pytest.fixture(autouse=True)
def _force_mock_mode(monkeypatch):
    monkeypatch.setenv("CCA_FORCE_MOCK", "1")
