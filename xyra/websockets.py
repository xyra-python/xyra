from typing import Any


class WebSocket:
    def __init__(self, ws: Any):
        self._ws = ws

    def send(self, message: str | bytes, is_binary: bool = False) -> None:
        """Send a message to the WebSocket client."""
        self._ws.send(message, is_binary)

    def send_text(self, message: str) -> None:
        """Send a text message to the WebSocket client."""
        self.send(message, False)

    def send_binary(self, message: bytes) -> None:
        """Send binary data to the WebSocket client."""
        self.send(message, True)

    def close(self, code: int = 1000, message: str | None = None) -> None:
        """Close the WebSocket connection."""
        self._ws.close()

    def publish(
        self,
        topic: str,
        message: str,
        is_binary: bool = False,
        compress: bool = False,
    ) -> None:
        """Publish a message to a topic."""
        self._ws.publish(topic, message, is_binary, compress)

    def subscribe(self, topic: str) -> None:
        """Subscribe to a topic."""
        self._ws.subscribe(topic)

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        self._ws.unsubscribe(topic)

    @property
    def closed(self) -> bool:
        """Check if the WebSocket is closed."""
        try:
            return self._ws.get_remote_address_bytes() is None
        except Exception:
            return True

    def get_remote_address(self) -> str | None:
        """Get the remote address of the WebSocket connection."""
        try:
            addr = self._ws.get_remote_address_bytes()
            if isinstance(addr, bytes):
                return addr.decode()
            return str(addr) if addr else None
        except Exception:
            return None
