from typing import Any

import orjson
from socketify import Response as SocketifyResponse


class Response:
    """
    HTTP response wrapper for Xyra applications.

    This class provides a convenient interface for building HTTP responses,
    including setting status codes, headers, sending data, and rendering templates.

    Attributes:
        _res: The underlying socketify response object.
        headers: Dictionary of response headers.
        status_code: HTTP status code (default: 200).
        templating: Templating engine instance.
        _ended: Flag indicating if response has been sent.
    """

    def __init__(self, res: SocketifyResponse, templating=None):
        """
        Initialize the Response object.

        Args:
            res: The underlying socketify response instance.
            templating: Optional templating engine for rendering templates.
        """
        self._res = res
        self.headers: dict[str, str] = {}
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

    def send(self, data: str | bytes) -> None:
        """
        Send response data and finalize the response.

        This method writes the status code and headers to the response,
        then sends the data and marks the response as ended.

        Args:
            data: The response body data (string or bytes).
        """
        if self._ended:
            return

        # Write status code
        self._res.write_status(str(self.status_code))
        # Write headers
        self._write_headers()

        if isinstance(data, str):
            self._res.end(data)
        else:
            self._res.end(data)

        self._ended = True

    def json(self, data: Any) -> None:
        """Send JSON response."""
        self.header("Content-Type", "application/json")
        json_data = orjson.dumps(data).decode("utf-8")
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
        max_age: int | None = None,
        expires: str | None = None,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: str | None = None,
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
        self, name: str, path: str = "/", domain: str | None = None
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
