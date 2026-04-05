from typing import Any

try:

    from ._libxyra import ffi, lib
except ImportError:
    pass

class WebSocket:
    def __init__(self, ws: Any):
        self._ws = ws

    def send(self, message: str | bytes, is_binary: bool = False) -> None:
        """Send a message to the WebSocket client."""
        if hasattr(self._ws, "send"):
            self._ws.send(message, is_binary)
        else:
            if isinstance(message, str):
                c_msg = message.encode('utf-8')
            else:
                c_msg = message
            lib.xyra_ws_send(self._ws, c_msg, len(c_msg), is_binary)

    def send_text(self, message: str) -> None:
        """Send a text message to the WebSocket client."""
        self.send(message, False)

    def send_binary(self, message: bytes) -> None:
        """Send binary data to the WebSocket client."""
        self.send(message, True)

    def close(self, code: int = 1000, message: str | None = None) -> None:
        """Close the WebSocket connection."""
        if hasattr(self._ws, "close"):
            self._ws.close()
        else:
            lib.xyra_ws_close(self._ws)

    def publish(
        self,
        topic: str,
        message: str,
        is_binary: bool = False,
        compress: bool = False,
    ) -> None:
        """Publish a message to a topic."""
        if hasattr(self._ws, "publish"):
            self._ws.publish(topic, message, is_binary, compress)
        else:
            c_topic = topic.encode('utf-8')
            c_msg = message.encode('utf-8') if isinstance(message, str) else message
            lib.xyra_ws_publish(self._ws, c_topic, len(c_topic), c_msg, len(c_msg), is_binary, compress)

    def subscribe(self, topic: str) -> None:
        """Subscribe to a topic."""
        if hasattr(self._ws, "subscribe"):
            self._ws.subscribe(topic)
        else:
            c_topic = topic.encode('utf-8')
            lib.xyra_ws_subscribe(self._ws, c_topic, len(c_topic))

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        if hasattr(self._ws, "unsubscribe"):
            self._ws.unsubscribe(topic)
        else:
            c_topic = topic.encode('utf-8')
            lib.xyra_ws_unsubscribe(self._ws, c_topic, len(c_topic))

    @property
    def closed(self) -> bool:
        """Check if the WebSocket is closed."""
        try:
            if hasattr(self._ws, "get_remote_address_bytes"):
                return self._ws.get_remote_address_bytes() is None

            out_ptr = ffi.new("char**")
            length = lib.xyra_ws_get_remote_address_bytes(self._ws, out_ptr)
            return length == 0
        except Exception:
            return True

    def get_remote_address(self) -> str | None:
        """Get the remote address of the WebSocket connection."""
        try:
            if hasattr(self._ws, "get_remote_address_bytes"):
                addr = self._ws.get_remote_address_bytes()
                if isinstance(addr, bytes):
                    return addr.decode()
                return str(addr) if addr else None

            out_ptr = ffi.new("char**")
            length = lib.xyra_ws_get_remote_address_bytes(self._ws, out_ptr)
            if length > 0:
                return ffi.string(out_ptr[0], length).decode('utf-8')
            return None
        except Exception:
            return None
