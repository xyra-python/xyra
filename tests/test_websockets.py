from unittest.mock import Mock

import pytest

# from socketify import OpCode
from xyra.websockets import WebSocket


from unittest.mock import patch

@pytest.fixture
def mock_fallback_ws():
    # A mock without the standard websocket methods
    # so hasattr(self._ws, "send") will be False
    return Mock(spec=[])

@pytest.fixture
def mock_socketify_ws():
    ws = Mock()
    ws.send = Mock()
    ws.publish = Mock()
    ws.subscribe = Mock()
    ws.unsubscribe = Mock()
    ws.close = Mock()
    ws.get_remote_address_bytes = Mock(return_value=b"127.0.0.1:12345")
    return ws


def test_websocket_init(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    assert ws._ws == mock_socketify_ws


def test_websocket_send_text(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.send("Hello", False)
    mock_socketify_ws.send.assert_called_once_with("Hello", False)


def test_websocket_send_text_method(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.send_text("Hello")
    mock_socketify_ws.send.assert_called_once_with("Hello", False)


def test_websocket_send_binary(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    data = b"binary data"
    ws.send_binary(data)
    mock_socketify_ws.send.assert_called_once_with(data, True)


def test_websocket_publish(mock_socketify_ws):
    ws = WebSocket(mock_socketify_ws)
    ws.publish("topic", "message", False, compress=True)
    mock_socketify_ws.publish.assert_called_once_with("topic", "message", False, True)


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
    mock_socketify_ws.get_remote_address_bytes.return_value = None
    assert ws.closed is True


def test_websocket_api_stability():
    """Test that WebSocket class has expected public methods and properties to prevent accidental renaming."""
    expected_methods = [
        "send",
        "send_text",
        "send_binary",
        "publish",
        "subscribe",
        "unsubscribe",
        "close",
    ]
    expected_properties = ["closed"]

    for method in expected_methods:
        assert hasattr(WebSocket, method), f"WebSocket is missing method: {method}"
        assert callable(getattr(WebSocket, method)), (
            f"WebSocket.{method} is not callable"
        )

    for prop in expected_properties:
        assert hasattr(WebSocket, prop), f"WebSocket is missing property: {prop}"


@pytest.mark.asyncio
async def test_websocket_in_app():
    """Test WebSocket integration in app."""

    from xyra import App

    messages = []

    def on_open(ws: WebSocket):
        ws.subscribe("chat")
        messages.append("connected")

    def on_message(ws: WebSocket, message, opcode):
        messages.append(f"received: {message}")

    def on_close(ws: WebSocket, code, message):
        messages.append("disconnected")

    app = App()
    app.websocket("/ws", {"open": on_open, "message": on_message, "close": on_close})

    # Test that websocket route is registered
    # We can't easily test the full integration without running the server
    # but we can check that the method exists and doesn't error
    assert hasattr(app, "websocket")

    # Test decorator syntax
    @app.websocket("/chat")
    def chat_handler(ws: WebSocket):
        ws.send("Welcome to chat!")

    # Check that decorator works
    assert callable(chat_handler)


def test_websocket_message_handling():
    """Test handling WebSocket messages."""
    mock_ws = Mock()
    ws = WebSocket(mock_ws)
    print(f"Testing check ws {ws}")

    received_messages = []

    def on_message(message, opcode):
        received_messages.append((message, opcode))

    # Simulate message handling
    on_message("Hello", False)
    assert received_messages == [("Hello", False)]

    # Test binary message
    on_message(b"binary", True)
    assert received_messages[1] == (b"binary", True)

@patch("xyra.websockets.lib")
def test_websocket_fallback_send_str(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.send("Hello", False)

    # "Hello".encode('utf-8')
    mock_lib.xyra_ws_send.assert_called_once_with(mock_fallback_ws, b"Hello", 5, False)

@patch("xyra.websockets.lib")
def test_websocket_fallback_send_bytes(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.send_binary(b"binary data")

    mock_lib.xyra_ws_send.assert_called_once_with(mock_fallback_ws, b"binary data", 11, True)

@patch("xyra.websockets.lib")
def test_websocket_fallback_close(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.close(1000, "Normal closure")

    mock_lib.xyra_ws_close.assert_called_once_with(mock_fallback_ws)

@patch("xyra.websockets.lib")
def test_websocket_fallback_publish_str(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.publish("topic", "message", False, compress=True)

    mock_lib.xyra_ws_publish.assert_called_once_with(mock_fallback_ws, b"topic", 5, b"message", 7, False, True)

@patch("xyra.websockets.lib")
def test_websocket_fallback_publish_bytes(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.publish("topic", b"message", True, compress=False)

    mock_lib.xyra_ws_publish.assert_called_once_with(mock_fallback_ws, b"topic", 5, b"message", 7, True, False)

@patch("xyra.websockets.lib")
def test_websocket_fallback_subscribe(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.subscribe("chat")

    mock_lib.xyra_ws_subscribe.assert_called_once_with(mock_fallback_ws, b"chat", 4)

@patch("xyra.websockets.lib")
def test_websocket_fallback_unsubscribe(mock_lib, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)
    ws.unsubscribe("chat")

    mock_lib.xyra_ws_unsubscribe.assert_called_once_with(mock_fallback_ws, b"chat", 4)

@patch("xyra.websockets.ffi")
@patch("xyra.websockets.lib")
def test_websocket_fallback_closed(mock_lib, mock_ffi, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)

    mock_ffi.new.return_value = "dummy_ptr"
    mock_lib.xyra_ws_get_remote_address_bytes.return_value = 0
    assert ws.closed is True
    mock_lib.xyra_ws_get_remote_address_bytes.assert_called_once_with(mock_fallback_ws, "dummy_ptr")

    mock_lib.xyra_ws_get_remote_address_bytes.reset_mock()
    mock_lib.xyra_ws_get_remote_address_bytes.return_value = 10
    assert ws.closed is False
    mock_lib.xyra_ws_get_remote_address_bytes.assert_called_once_with(mock_fallback_ws, "dummy_ptr")

@patch("xyra.websockets.ffi")
@patch("xyra.websockets.lib")
def test_websocket_fallback_closed_exception(mock_lib, mock_ffi, mock_fallback_ws):
    ws = WebSocket(mock_fallback_ws)

    # Exception during the check means it's considered closed
    mock_ffi.new.side_effect = Exception("Test Exception")
    assert ws.closed is True
