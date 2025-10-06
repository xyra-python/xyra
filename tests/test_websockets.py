from unittest.mock import Mock

import pytest
from socketify import OpCode

from xyra.websockets import WebSocket


@pytest.fixture
def mock_socketify_ws():
    ws = Mock()
    ws.send = Mock()
    ws.publish = Mock()
    ws.subscribe = Mock()
    ws.unsubscribe = Mock()
    ws.close = Mock()
    ws.get_remote_address = Mock(return_value="127.0.0.1:12345")
    return ws


def test_websocket_init(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    assert ws._ws == mock_socketify_ws


def test_websocket_send_text(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.send("Hello", OpCode.TEXT)
    mock_socketify_ws.send.assert_called_once_with("Hello", OpCode.TEXT)


def test_websocket_send_text_method(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.send_text("Hello")
    mock_socketify_ws.send.assert_called_once_with("Hello", OpCode.TEXT)


def test_websocket_send_binary(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    data = b"binary data"
    ws.send_binary(data)
    mock_socketify_ws.send.assert_called_once_with(data, OpCode.BINARY)


def test_websocket_publish(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.publish("topic", "message", OpCode.TEXT, compress=True)
    mock_socketify_ws.publish.assert_called_once_with(
        "topic", "message", OpCode.TEXT, True
    )


def test_websocket_subscribe(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.subscribe("chat")
    mock_socketify_ws.subscribe.assert_called_once_with("chat")


def test_websocket_unsubscribe(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.unsubscribe("chat")
    mock_socketify_ws.unsubscribe.assert_called_once_with("chat")


def test_websocket_close(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.close(1000, "Normal closure")
    mock_socketify_ws.close.assert_called_once()


def test_websocket_closed(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    # Mock as connected
    assert ws.closed is False

    # Mock as disconnected
    mock_socketify_ws.get_remote_address.return_value = None
    assert ws.closed is True


def test_websocket_get_remote_address(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    address = ws.get_remote_address()
    assert address == "127.0.0.1:12345"
    mock_socketify_ws.get_remote_address.assert_called_once()
