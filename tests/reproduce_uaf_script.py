import threading
import time
import sys
import os
import urllib.request

# Ensure xyra is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xyra import App, Request, Response

# This script attempts to trigger UAF in Response object.

def run_server():
    app = App()

    @app.get("/uaf")
    async def uaf_handler(req: Request, res: Response):
        # Schedule response on main loop
        res.text("ok")
        # Return immediately.
        # res variable goes out of scope here.
        # In async_final_handler, response wrapper goes out of scope.
        # This runs on background thread.
        # Main loop (native) will execute the deferred callback later.
        # If lambda captures 'this', and 'this' is destroyed, it crashes.
        return

    # Run on port 9001
    print("Starting server on 9001")
    app.listen(9001)

def main():
    # Start server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(2) # Wait for server start

    try:
        # Send many requests to trigger race condition
        for i in range(100):
            try:
                with urllib.request.urlopen("http://localhost:9001/uaf", timeout=1) as response:
                    body = response.read().decode('utf-8')
                    assert response.status == 200
                    assert body == "ok"
            except Exception as e:
                print(f"Request failed: {e}")
                # If server crashed, this will fail
                sys.exit(1)

            if i % 10 == 0:
                print(f"Request {i} OK")
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

    print("Success: No crash")
    sys.exit(0)

if __name__ == "__main__":
    main()
