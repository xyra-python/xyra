
import threading
import time
import requests
from xyra import App, Request, Response

def run_server():
    app = App()

    @app.get("/unsafe")
    def unsafe(req: Request, res: Response):
        # Vulnerable pattern: echoing input via res.send without Content-Type
        q = req.query_params.get("q", [""])[0]
        res.send(f"You said: {q}")

    app.listen(8006)

def test_xss():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1)

    try:
        # Payload
        payload = "<script>alert(1)</script>"
        url = f"http://localhost:8006/unsafe?q={payload}"

        print(f"Requesting {url}")
        resp = requests.get(url)

        print(f"Status: {resp.status_code}")
        print(f"Headers: {resp.headers}")
        print(f"Body: {resp.text}")

        ct = resp.headers.get("Content-Type")
        print(f"Content-Type: {ct}")

        if not ct:
            print("VULNERABLE: No Content-Type header. Browser will sniff.")
        elif "html" in ct:
            print("VULNERABLE: Content-Type is HTML.")
        else:
            print(f"Likely Safe: Content-Type is set to {ct}.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_xss()
