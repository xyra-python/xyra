from socketify import OpCode
from socketify import WebSocket as SocketifyWebSocket


class WebSocket:
    def __init__(self, ws: SocketifyWebSocket):
        self._ws = ws

    def send(self, message: str | bytes, opcode: OpCode = OpCode.TEXT) -> None:
        """Send a message to the WebSocket client."""
        self._ws.send(message, opcode)

    def send_text(self, message: str) -> None:
        """Send a text message to the WebSocket client."""
        self.send(message, OpCode.TEXT)

    def send_binary(self, message: bytes) -> None:
        """Send binary data to the WebSocket client."""
        self.send(message, OpCode.BINARY)

    def publish(
        self,
        topic: str,
        message: str | bytes,
        opcode: OpCode = OpCode.TEXT,
        compress: bool = False,
    ) -> None:
        """Publish a message to a topic."""
        self._ws.publish(topic, message, opcode, compress)

    def subscribe(self, topic: str) -> None:
        """Subscribe to a topic."""
        self._ws.subscribe(topic)

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        self._ws.unsubscribe(topic)

    def close(self, code: int = 1000, message: str | None = None) -> None:
        """Close the WebSocket connection."""
        self._ws.close()

    @property
    def closed(self) -> bool:
        """Check if the WebSocket is closed."""
        return self._ws.get_remote_address() is None

    def get_remote_address(self) -> str | None:
        """Get the remote address of the WebSocket connection."""
        addr = self._ws.get_remote_address()
        return str(addr) if addr else None
