import socket
import threading
import time
import os
import sys

# Ensure xyra is importable
# sys.path.insert(0, os.getcwd())

from xyra import App

stored_ws = None
close_event = threading.Event()

def run_server(port):
    print(f"Starting server on port {port}")
    app = App()

    def on_open(ws):
        global stored_ws
        print("WebSocket opened")
        stored_ws = ws

    def on_close(ws, code, msg):
        print("WebSocket closed")
        close_event.set()

    app.websocket("/ws", {
        "open": on_open,
        "close": on_close
    })

    try:
        # Enable logging to see what happens
        app.listen(port=port, logger=True)
    except Exception as e:
        print(f"Server exception: {e}")

def test_websocket_uaf():
    port = 9007
    t = threading.Thread(target=run_server, args=(port,))
    t.daemon = True
    t.start()

    print("Waiting for server...")
    connected = False
    for i in range(20):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", port))
            s.close()
            connected = True
            print("Server is listening")
            break
        except ConnectionRefusedError:
            time.sleep(0.1)

    if not connected:
        print("Failed to connect to server")
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("Connecting client...")
        s.connect(("127.0.0.1", port))

        req = (
            "GET /ws HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(1024)
        print(f"Handshake response: {resp[:50]}...")

        if b"101 Switching Protocols" not in resp:
            print("Handshake failed")
            return

        time.sleep(0.5)
        if stored_ws is None:
            print("stored_ws is None")
            return

        print("Closing client socket...")
        s.close()

        if not close_event.wait(timeout=5):
            print("Close callback timed out")
            return

        print("Testing get_remote_address...")
        try:
            addr = stored_ws.get_remote_address()
            print(f"Address: {addr}")
            if addr is None:
                print("SUCCESS: Address is None (safe)")
            else:
                print("WARNING: Address is not None (unexpected but maybe ok if empty)")
        except Exception as e:
            print(f"Exception: {e}")

        print("Testing send...")
        try:
            stored_ws.send("test")
            print("Send returned (safe)")
        except Exception as e:
            print(f"Exception: {e}")

        print("Testing closed property...")
        if stored_ws.closed:
             print("SUCCESS: closed property is True")
        else:
             print("FAILURE: closed property is False")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    test_websocket_uaf()
