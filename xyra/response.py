import re
import sys
from typing import Any

from .datastructures import Headers
from .libxyra import format_cookie

if sys.implementation.name == "pypy":
    import ujson as json_lib
else:
    import orjson as json_lib

import asyncio

# Security: Limit maximum request body size to 10MB to prevent DoS
MAX_BODY_SIZE = 10 * 1024 * 1024

# SECURITY: Regex to match control characters except HTAB (\t)
# Matches 0x00-0x08, 0x0A-0x1F, 0x7F
_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")


class Response:
    """
    HTTP response wrapper for Xyra applications.

    This class provides a convenient interface for building HTTP responses,
    including setting status codes, headers, sending data, and rendering templates.

    Attributes:
        _res: The underlying native response object.
        headers: Dictionary of response headers.
        status_code: HTTP status code (default: 200).
        templating: Templating engine instance.
        _ended: Flag indicating if response has been sent.
    """

    __slots__ = (
        "_res",
        "headers",
        "status_code",
        "templating",
        "_ended",
        "_body_cache",
        "_body_future",
    )

    def __init__(self, res: Any, templating=None):
        """
        Initialize the Response object.

        Args:
            res: The underlying native response instance.
            templating: Optional templating engine for rendering templates.
        """
        self._res = res
        self.headers = Headers()
        self.status_code: int = 200
        self.templating = templating
        self._ended = False
        self._body_cache: bytes | None = None
        self._body_future: asyncio.Future[bytes] | None = None

    def render(self, template_name: str, **kwargs) -> None:
        """Render a template with the given context.
        usage:
            @app.get("/")
            async index(req: Request, res: Response):
                res.render("index.html", title="Home Page")
        """
        if not self.templating:
            raise RuntimeError("Templating is not configured.")

        html = self.templating.render(template_name, **kwargs)
        self._header_fast("Content-Type", "text/html; charset=utf-8")
        self.send(html)

    def status(self, code: int) -> "Response":
        """Set the HTTP status code.
        usage:
            @app.get("/")
            async def index(req: Request, res: Response):
                res.status(200).json({"message": "Hello World"})

            @app.get("/")
            async def index(req: Request, res: Response):
                res.status(201).json(users)
        """
        self.status_code = code
        return self

    def _header_fast(self, key: str, value: str) -> "Response":
        """Set a response header without validation (internal use only)."""
        self.headers[key] = value
        return self

    def header(self, key: str, value: str) -> "Response":
        """Set a response header."""
        # SECURITY:
        # Risk: Header injection (CRLF) and response splitting.
        # Attack: Attacker injects \r\n to start a new header or response body.
        # Mitigation: Reject all control characters (except HTAB) in keys and values.
        if _CONTROL_CHARS_PATTERN.search(key) or _CONTROL_CHARS_PATTERN.search(value):
            raise ValueError("Invalid characters in header (injection attempt)")

        self.headers[key] = value
        return self

    def _write_headers(self) -> None:
        """Write all headers to the response."""
        for key, value in self.headers.items():
            self._res.write_header(key, value)

    def send(self, data: str | bytes) -> None:
        """
        Send response data and finalize the response.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.send("Hello, Xyra!")
        """
        if self._ended:
            return

        # Write status code
        self._res.write_status(str(self.status_code))

        # SECURITY: Set default Content-Type if missing to prevent MIME sniffing/XSS.
        # Browsers may sniff "text/html" from response body if Content-Type is missing.
        # Default to safe types: text/plain for strings, application/octet-stream for bytes.
        if "content-type" not in self.headers:
            if isinstance(data, str):
                self._header_fast("Content-Type", "text/plain; charset=utf-8")
            else:
                self._header_fast("Content-Type", "application/octet-stream")

        # Write headers
        self._write_headers()

        if isinstance(data, str):
            self._res.end(data)
        else:
            self._res.end(data)

        self._ended = True

    def json(self, data: Any) -> None:
        """Send JSON response.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.json({"message": "Hello, Xyra!"})
        """
        # PERF: Use fast header setting as the key and value are trusted
        self._header_fast("Content-Type", "application/json")
        # PERF: json_lib (orjson) returns bytes, send them directly to avoid decode/encode overhead
        json_data = json_lib.dumps(data)
        self.send(json_data)

    def html(self, html: str) -> None:
        """Send HTML response.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.html("<h1>Hello Xyra!</h1>")
        """
        # PERF: Use fast header setting as the key and value are trusted
        self._header_fast("Content-Type", "text/html; charset=utf-8")
        self.send(html)

    def text(self, text: str) -> None:
        """Send plain text response.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.text("Hello Xyra!")
        """
        # PERF: Use fast header setting as the key and value are trusted
        self._header_fast("Content-Type", "text/plain; charset=utf-8")
        self.send(text)

    def redirect(self, url: str, status_code: int = 302) -> None:
        """Redirect to a different URL.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.redirect("/", 302)
        """
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
        same_site: str | None = "Lax",
    ) -> "Response":
        """Set a cookie.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.json({"message": "hello world"})
                res.set_cookie("session_id", "abc123", max_age=3600, secure=True)
        """
        # Optimized native implementation
        try:
            cookie_string = format_cookie(
                name,
                value,
                max_age,
                expires,
                path,
                domain,
                secure,
                http_only,
                same_site,
            )
            # SECURITY:
            # Risk: Multiple cookies being overwritten.
            # Attack: If a session/CSRF cookie is overwritten by a later cookie, security is bypassed.
            # Mitigation: Use CIMultiDict and .add() to ensure all Set-Cookie headers are sent.
            self.headers.add("Set-Cookie", cookie_string)
        except ValueError as e:
            # Re-raise as ValueError if it comes from C++ binding (mapped from std::invalid_argument)
            raise ValueError(str(e)) from e

        return self

    def clear_cookie(
        self,
        name: str,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: str | None = "Lax",
    ) -> "Response":
        """Clear a cookie.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.json({"message": "hello world"})
                res.clear_cookie("session_id", path="/", secure=True, http_only=True)
        """
        return self.set_cookie(
            name,
            "",
            expires="Thu, 01 Jan 1970 00:00:00 GMT",
            path=path,
            domain=domain,
            secure=secure,
            http_only=http_only,
            same_site=same_site,
        )

    def cors(
        self,
        origin: str = "*",
        methods: str = "GET,POST,PUT,DELETE,OPTIONS",
        headers: str = "Content-Type,Authorization",
        credentials: bool = False,
    ) -> "Response":
        """Set CORS headers.
        usage:
            async def mycors(req: Request, res: Response):
                res.cors(
                    origin = "google.com, 127.0.0.1:3000",
                    methods = "GET,POST,PUT,DELETE,OPTIONS",
                    headers = "Content-Type,Authorization",
                    credentials = False,
                )
            app.use(mycors)
        """
        self.header("Access-Control-Allow-Origin", origin)
        self.header("Access-Control-Allow-Methods", methods)
        self.header("Access-Control-Allow-Headers", headers)

        if credentials:
            # PERF: Use fast header setting as the key and value are trusted
            self._header_fast("Access-Control-Allow-Credentials", "true")

        return self

    def cache(self, max_age: int = 3600) -> "Response":
        """Set cache headers.
        usage:
            @app.get("/")
            async def cache(req: Request, res: Response):
                res.cache(max_age=86400)
        """
        # PERF: Use fast header setting as the key is trusted and value is numeric/safe
        self._header_fast("Cache-Control", f"public, max-age={int(max_age)}")
        return self

    def vary(self, name: str) -> "Response":
        """Add a header name to the Vary header.
        usage:
            @app.get("/")
            async def vary(req: Request, res: Response):
                res.vary("Origin")
        """
        self.headers.add("Vary", name)
        return self

    def no_cache(self) -> "Response":
        """Disable caching.
        usage:
            data_users = {"id":1, "name": "john"}
            @app.get("/")
            async def nocache(req: Request, res: Response):
                res.no_cache().json(data_users)
        """
        # PERF: Use fast header setting as keys and values are trusted
        self._header_fast("Cache-Control", "no-cache, no-store, must-revalidate")
        self._header_fast("Pragma", "no-cache")
        self._header_fast("Expires", "0")
        return self

    def close(self) -> None:
        """
        Close the connection immediately.

        usage:
            @app.get("/")
            def close(req: Request, res: Response):
                res.close()
        """
        self._res.close()
        self._ended = True

    async def get_data(self) -> bytes:
        """Get the request body data (async)."""
        if self._body_cache is not None:
            return self._body_cache

        if self._body_future is not None:
            return await self._body_future

        loop = asyncio.get_running_loop()
        self._body_future = loop.create_future()
        chunks = []
        # Track received bytes synchronously in on_data to fail fast
        received_bytes = [0]
        # Flag to prevent multiple close calls or scheduling unnecessary callbacks
        aborted = [False]

        def on_data(chunk, is_last):
            if aborted[0]:
                return

            # SECURITY: Track total size immediately to prevent DoS via buffering
            chunk_len = len(chunk)
            received_bytes[0] += chunk_len

            if received_bytes[0] > MAX_BODY_SIZE:
                aborted[0] = True
                # Abort immediately to stop memory growth
                if hasattr(self._res, "close"):
                    # This runs in uWebSockets thread, so it's safe/correct to call native close
                    self._res.close()

                # Signal error to the future (thread-safe)
                def fail():
                    if self._body_future and not self._body_future.done():
                        self._body_future.set_exception(
                            ValueError(
                                f"Request body too large (max {MAX_BODY_SIZE} bytes)"
                            )
                        )

                loop.call_soon_threadsafe(fail)
                return

            def resolve():
                if self._body_future is None or self._body_future.done():
                    return

                chunks.append(chunk)

                if is_last:
                    result = b"".join(chunks)
                    self._body_cache = result
                    self._body_future.set_result(result)

            loop.call_soon_threadsafe(resolve)

        def on_abort():
            loop.call_soon_threadsafe(
                lambda: (self._body_future and self._body_future.done())
                or (
                    self._body_future
                    and self._body_future.set_exception(
                        RuntimeError("Connection aborted")
                    )
                )
            )

        self._res.on_data(on_data)
        self._res.on_aborted(on_abort)

        return await self._body_future

    def get_remote_address_bytes(self) -> bytes:
        """Get the remote address as bytes."""
        return self._res.get_remote_address_bytes()
