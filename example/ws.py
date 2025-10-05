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
    
    # Broadcast message ke semua clients
    for client in connected_clients:
        if client != ws:  # Jangan kirim ke sender sendiri
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