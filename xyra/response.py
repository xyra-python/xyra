import json
from typing import Any, Dict, Optional, Union

from socketify import Response as SocketifyResponse


class Response:
    def __init__(self, res: SocketifyResponse, templating=None):
        self._res = res
        self.headers: Dict[str, str] = {}
        self.status_code: int = 200
        self.templating = templating
        self._ended = False

    def render(self, template_name: str, **kwargs) -> None:
        """Render a template with the given context."""
        if not self.templating:
            raise RuntimeError("Templating is not configured.")

        html = self.templating.render(template_name, **kwargs)
        self.header("Content-Type", "text/html; charset=utf-8")
        self.send(html)

    def status(self, code: int) -> "Response":
        """Set the HTTP status code."""
        self.status_code = code
        return self

    def header(self, key: str, value: str) -> "Response":
        """Set a response header."""
        self.headers[key] = value
        return self

    def _write_headers(self) -> None:
        """Write all headers to the response."""
        for key, value in self.headers.items():
            self._res.write_header(key, value)

    def send(self, data: Union[str, bytes]) -> None:
        """Send response data and end the response."""
        if self._ended:
            return

        if isinstance(data, str):
            self._res.end(data)
        else:
            self._res.end(data)

        self._ended = True

    def json(self, data: Any) -> None:
        """Send JSON response."""
        self.header("Content-Type", "application/json")
        json_data = json.dumps(data, ensure_ascii=False)
        self.send(json_data)

    def html(self, html: str) -> None:
        """Send HTML response."""
        self.header("Content-Type", "text/html; charset=utf-8")
        self.send(html)

    def text(self, text: str) -> None:
        """Send plain text response."""
        self.header("Content-Type", "text/plain; charset=utf-8")
        self.send(text)

    def redirect(self, url: str, status_code: int = 302) -> None:
        """Redirect to a different URL."""
        self.status(status_code)
        self.header("Location", url)
        self.send("")

    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: Optional[str] = None,
    ) -> "Response":
        """Set a cookie."""
        cookie_parts = [f"{name}={value}"]

        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")

        if expires:
            cookie_parts.append(f"Expires={expires}")

        if path:
            cookie_parts.append(f"Path={path}")

        if domain:
            cookie_parts.append(f"Domain={domain}")

        if secure:
            cookie_parts.append("Secure")

        if http_only:
            cookie_parts.append("HttpOnly")

        if same_site:
            cookie_parts.append(f"SameSite={same_site}")

        cookie_string = "; ".join(cookie_parts)
        self.header("Set-Cookie", cookie_string)
        return self

    def clear_cookie(
        self, name: str, path: str = "/", domain: Optional[str] = None
    ) -> "Response":
        """Clear a cookie."""
        cookie_parts = [f"{name}=", "Expires=Thu, 01 Jan 1970 00:00:00 GMT"]

        if path:
            cookie_parts.append(f"Path={path}")

        if domain:
            cookie_parts.append(f"Domain={domain}")

        cookie_string = "; ".join(cookie_parts)
        self.header("Set-Cookie", cookie_string)
        return self

    def cors(
        self,
        origin: str = "*",
        methods: str = "GET,POST,PUT,DELETE,OPTIONS",
        headers: str = "Content-Type,Authorization",
        credentials: bool = False,
    ) -> "Response":
        """Set CORS headers."""
        self.header("Access-Control-Allow-Origin", origin)
        self.header("Access-Control-Allow-Methods", methods)
        self.header("Access-Control-Allow-Headers", headers)

        if credentials:
            self.header("Access-Control-Allow-Credentials", "true")

        return self

    def cache(self, max_age: int = 3600) -> "Response":
        """Set cache headers."""
        self.header("Cache-Control", f"public, max-age={max_age}")
        return self

    def no_cache(self) -> "Response":
        """Disable caching."""
        self.header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.header("Pragma", "no-cache")
        self.header("Expires", "0")
        return self
