from socketify import HttpResponse
import json

class Response:
    def __init__(self, res: HttpResponse, templating=None):
        self._res = res
        self.headers = {}
        self.status_code = 200
        self.templating = templating

    def render(self, template_name: str, **kwargs):
        if not self.templating:
            raise RuntimeError("Templating is not configured.")

        html = self.templating.render(template_name, **kwargs)
        self.header("Content-Type", "text/html; charset=utf-8")
        self.send(html)

    def status(self, code: int):
        self.status_code = code
        return self

    def header(self, key: str, value: str):
        self.headers[key] = value
        return self

    def _write_headers(self):
        for key, value in self.headers.items():
            self._res.write_header(key, value)

    def send(self, data):
        self._res.write_status(self.status_code)
        self._write_headers()
        self._res.end(data)

    def json(self, data):
        self.header("Content-Type", "application/json")
        self.send(json.dumps(data))