
import threading
import time
import urllib.error
import urllib.request

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
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req) as response:
                status = response.status
                headers = response.headers
                body = response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            status = e.code
            headers = e.headers
            body = e.read().decode('utf-8', errors='replace')

        print(f"Status: {status}")
        print(f"Headers: {headers}")
        print(f"Body: {body}")

        ct = headers.get("Content-Type")
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
