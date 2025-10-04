from socketify import OpCode, WebSocket as SocketifyWebSocket

class WebSocket:
    def __init__(self, ws: SocketifyWebSocket):
        self._ws = ws

    def send(self, message, opcode=OpCode.TEXT):
        self._ws.send(message, opcode)

    def publish(self, topic, message, opcode=OpCode.TEXT, compress=False):
        self._ws.publish(topic, message, opcode, compress)

    def close(self):
        self._ws.close()

    @property
    def closed(self):
        return self._ws.is_closed()