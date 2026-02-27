
import threading
import time
import requests
from xyra import App, Request, Response

def run_server():
    app = App()

    @app.get("/json")
    def json_handler(req: Request, res: Response):
        res.json({"key": "value"})

    @app.get("/html")
    def html_handler(req: Request, res: Response):
        res.html("<h1>Header</h1>")

    @app.get("/text")
    def text_handler(req: Request, res: Response):
        res.text("plain text")

    @app.get("/custom")
    def custom_handler(req: Request, res: Response):
        res.header("Content-Type", "application/custom")
        res.send("custom data")

    app.listen(8007)

def test_regressions():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1)

    try:
        # JSON
        r = requests.get("http://localhost:8007/json")
        print(f"JSON Content-Type: {r.headers.get('Content-Type')}")
        assert r.headers.get('Content-Type') == 'application/json'

        # HTML
        r = requests.get("http://localhost:8007/html")
        print(f"HTML Content-Type: {r.headers.get('Content-Type')}")
        assert r.headers.get('Content-Type') == 'text/html; charset=utf-8'

        # Text
        r = requests.get("http://localhost:8007/text")
        print(f"Text Content-Type: {r.headers.get('Content-Type')}")
        assert r.headers.get('Content-Type') == 'text/plain; charset=utf-8'

        # Custom
        r = requests.get("http://localhost:8007/custom")
        print(f"Custom Content-Type: {r.headers.get('Content-Type')}")
        assert r.headers.get('Content-Type') == 'application/custom'

        print("Regression tests passed!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_regressions()
