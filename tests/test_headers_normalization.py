
import threading
import time
import urllib.error
import urllib.request

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
        req = urllib.request.Request("http://localhost:8004/api/headers", headers=headers)
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            body = resp.read().decode('utf-8')

        import json
        received = json.loads(body)
        print(f"Status: {status_code}")
        print(f"Body: {received}")

        # Verify keys are lowercased
        if "x-custom-header" in received and "content-type" in received:
            print("Headers are correctly lowercased.")
        else:
            print("Headers are NOT strictly lowercased.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_headers_case()
