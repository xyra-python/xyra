
import asyncio
import os
import signal
import sys
import time
from multiprocessing import Process

from xyra import App, Request, Response

def run_server():
    app = App()

    @app.get("/uaf")
    async def uaf_handler(req: Request, res: Response):
        # Trigger Use-After-Free
        res.send("This ends the response")

        # This should cause a crash because res is invalid after end()
        # calling get_data registers callbacks on the now-freed res object
        try:
            await res.get_data()
        except Exception as e:
            print(f"Caught exception: {e}")

    # Run on a different port to avoid conflicts
    try:
        app.listen(8081)
        print("Server started on 8081")
        # Keep running
        import time
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Server error: {e}")

def run_client():
    # Give server time to start
    time.sleep(2)
    import urllib.request
    try:
        print("Sending request...")
        with urllib.request.urlopen("http://localhost:8081/uaf") as response:
            print(f"Response code: {response.getcode()}")
            print(f"Response body: {response.read().decode()}")
    except Exception as e:
        print(f"Client error: {e}")

if __name__ == "__main__":
    # Start server in a separate process so we can detect if it crashes
    server_process = Process(target=run_server)
    server_process.start()

    try:
        run_client()
        # Wait a bit to see if server crashes
        time.sleep(1)

        if server_process.is_alive():
            print("Server is still alive (Fix needed? Or maybe UAF didn't crash immediately)")
            server_process.terminate()
        else:
            print("Server process died (UAF confirmed!)")
            sys.exit(0)

    except KeyboardInterrupt:
        server_process.terminate()
    finally:
        if server_process.is_alive():
            server_process.terminate()
