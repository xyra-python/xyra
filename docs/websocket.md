# WebSocket in Xyra

Xyra supports WebSocket for real-time communication between server and client. WebSocket enables persistent bidirectional connections, ideal for chat applications, real-time notifications, games, or live dashboards.

## Setup WebSocket

To use WebSocket in Xyra, you need to register a WebSocket route and specify a handler.

### Simple Handler

```python
from xyra import App

app = App()

@app.websocket("/ws")
def handle_websocket(websocket):
    websocket.send("Connected!")
```

### Handler with Separate Events

For better control, you can specify separate handlers for each event:

```python
def on_open(ws):
    print("Client connected")
    ws.send("Welcome!")

def on_message(ws, message, opcode):
    print(f"Received: {message}")
    ws.send(f"Echo: {message}")

def on_close(ws, code, message):
    print("Client disconnected")

app.websocket("/chat", {
    "open": on_open,
    "message": on_message,
    "close": on_close
})
```

## WebSocket Methods

The WebSocket object provides various methods for sending and receiving data.

### Sending Data

```python
def websocket_handler(websocket):
    # Send text message
    websocket.send("Hello World")
    websocket.send_text("Text message")
    
    # Send binary data
    websocket.send_binary(b"Binary data")
    
    # Send with specific opcode
    from socketify import OpCode
    websocket.send("Data", OpCode.TEXT)
```

### Publish to Topic

WebSocket supports a pub/sub pattern for broadcasting to multiple clients:

```python
def websocket_handler(websocket):
    # Subscribe to topic
    websocket.subscribe("room1")
    websocket.subscribe("notifications")
    
    # Unsubscribe from topic
    websocket.unsubscribe("room1")
    
    # Publish message to topic
    websocket.publish("room1", "Hello everyone in room1!")
    websocket.publish("notifications", "System update available", compress=True)
```

### Close Connection

```python
def websocket_handler(websocket):
    # Close with normal status
    websocket.close()
    
    # Close with code and message
    websocket.close(1000, "Normal closure")
    
    # Close with error code
    websocket.close(1001, "Going away")
```

### Check Connection Status

```python
def websocket_handler(websocket):
    if websocket.closed:
        print("Connection is closed")
        return
    
    # Connection is still active
    websocket.send("Connection is active")
```

## Complete Example

### Simple Chat Room

```python
from xyra import App

app = App()

# Store connected clients (in production, use proper storage)
connected_clients = set()

def on_open(ws):
    connected_clients.add(ws)
    print(f"Client connected. Total clients: {len(connected_clients)}")
    ws.send("Welcome to chat room!")

def on_message(ws, message, opcode):
    print(f"Received: {message}")
    
    # Broadcast message to all clients
    for client in connected_clients:
        if client != ws:  # Don't send to sender
            client.send(f"User: {message}")

def on_close(ws, code, message):
    connected_clients.discard(ws)
    print(f"Client disconnected. Total clients: {len(connected_clients)}")

app.websocket("/chat", {
    "open": on_open,
    "message": on_message,
    "close": on_close
})

if __name__ == "__main__":
    print("🚀 Chat server running on ws://localhost:8000/chat")
    app.listen(8000)
```

### Real-time Dashboard

```python
import json
import time
from xyra import App

app = App()

def on_open(ws):
    print("Dashboard client connected")
    ws.subscribe("metrics")
    ws.send(json.dumps({"type": "welcome", "message": "Connected to dashboard"}))

def on_message(ws, message, opcode):
    try:
        data = json.loads(message)
        if data.get("type") == "subscribe":
            ws.subscribe(data.get("topic", "metrics"))
        elif data.get("type") == "unsubscribe":
            ws.unsubscribe(data.get("topic", "metrics"))
    except json.JSONDecodeError:
        ws.send(json.dumps({"error": "Invalid JSON"}))

def on_close(ws, code, message):
    print("Dashboard client disconnected")

app.websocket("/dashboard", {
    "open": on_open,
    "message": on_message,
    "close": on_close
})

# Simulate metrics publishing
def publish_metrics():
    while True:
        time.sleep(5)  # Publish every 5 seconds
        metrics = {
            "type": "metrics",
            "cpu": 45.2,
            "memory": 67.8,
            "timestamp": time.time()
        }
        app.websocket("/dashboard", lambda ws: ws.publish("metrics", json.dumps(metrics)))

# Note: In production, run this in a separate thread or async task

if __name__ == "__main__":
    app.listen(8000)
```

### JavaScript Client

To connect from the browser, use JavaScript:

```html
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Chat</title>
</head>
<body>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type message...">
    <button onclick="sendMessage()">Send</button>

    <script>
        const ws = new WebSocket('ws://localhost:8000/chat');
        const messages = document.getElementById('messages');
        const input = document.getElementById('messageInput');

        ws.onopen = function(event) {
            console.log('Connected to WebSocket');
        };

        ws.onmessage = function(event) {
            const messageDiv = document.createElement('div');
            messageDiv.textContent = event.data;
            messages.appendChild(messageDiv);
        };

        ws.onclose = function(event) {
            console.log('Disconnected from WebSocket');
        };

        function sendMessage() {
            const message = input.value;
            if (message) {
                ws.send(message);
                input.value = '';
            }
        }

        // Send on Enter key
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

## Error Handling

Always handle errors in WebSocket connections:

```python
def on_open(ws):
    try:
        ws.send("Welcome!")
        # Setup initial state
    except Exception as e:
        print(f"Error in on_open: {e}")
        ws.close(1011, "Internal error")

def on_message(ws, message, opcode):
    try:
        # Process message
        if len(message) > 1000:
            ws.send("Message too long")
            return
        
        # Process message...
        ws.send(f"Processed: {message}")
    except Exception as e:
        print(f"Error processing message: {e}")
        ws.send("Error processing message")
```

## Security Considerations

1. **Input Validation**: Always validate and sanitize input from WebSocket
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Authentication**: Verify client identity before accepting connections
4. **Origin Checking**: Check the origin header to prevent cross-site WebSocket hijacking
5. **Message Size Limits**: Limit message size to prevent DoS attacks

## WebSocket Tips

1. **Connection Management**: Track connected clients for broadcasting
2. **Heartbeat**: Implement ping/pong to detect broken connections
3. **Reconnection**: Handle reconnection logic on the client side
4. **Binary Data**: Use binary messages for efficient data
5. **Compression**: Enable compression for large messages
6. **Topics**: Use pub/sub pattern for scalable broadcasting

---

[Back to Table of Contents](../README.md)