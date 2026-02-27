
import threading
import time
import requests
from xyra import App, Request, Response

def run_server():
    app = App()

    @app.get("/api/headers")
    def headers(req: Request, res: Response):
        res.json(req.headers)

    app.listen(8004)

def test_headers_case():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1)

    try:
        # Send mixed case headers
        headers = {"X-Custom-Header": "Value", "CONTENT-TYPE": "application/json"}
        resp = requests.get("http://localhost:8004/api/headers", headers=headers)

        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.json()}")

        # Verify keys are lowercased
        received = resp.json()
        if "x-custom-header" in received and "content-type" in received:
            print("Headers are correctly lowercased.")
        else:
            print("Headers are NOT strictly lowercased.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_headers_case()
