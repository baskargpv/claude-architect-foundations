import pytest

from common import config
from common.client import get_client
from common.mock import MockClient, message, text, tool_use


def test_tests_always_run_in_mock_mode():
    assert not config.is_live()


def test_message_infers_stop_reason():
    assert message(text("hi")).stop_reason == "end_turn"
    assert message(text("hi"), tool_use("t", {})).stop_reason == "tool_use"


def test_mock_client_records_calls_and_exhausts():
    client = get_client([message(text("one"))])
    assert isinstance(client, MockClient)
    client.messages.create(model="m", messages=[{"role": "user", "content": "x"}])
    assert client.calls[0]["messages"][0]["content"] == "x"
    with pytest.raises(RuntimeError, match="exhausted"):
        client.messages.create(model="m", messages=[])
