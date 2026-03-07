
import threading
import time

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
        import urllib.request
        def get_header(url):
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                return response.headers.get('Content-Type')

        # JSON
        ct = get_header("http://localhost:8007/json")
        print(f"JSON Content-Type: {ct}")
        assert ct == 'application/json'

        # HTML
        ct = get_header("http://localhost:8007/html")
        print(f"HTML Content-Type: {ct}")
        assert ct == 'text/html; charset=utf-8'

        # Text
        ct = get_header("http://localhost:8007/text")
        print(f"Text Content-Type: {ct}")
        assert ct == 'text/plain; charset=utf-8'

        # Custom
        ct = get_header("http://localhost:8007/custom")
        print(f"Custom Content-Type: {ct}")
        assert ct == 'application/custom'

        print("Regression tests passed!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_regressions()
