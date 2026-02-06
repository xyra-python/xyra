import sys
from http.cookies import SimpleCookie
from typing import Any

if sys.implementation.name == "pypy":
    import ujson as json_lib
else:
    import orjson as json_lib

import asyncio

# Security: Limit maximum request body size to 10MB to prevent DoS
MAX_BODY_SIZE = 10 * 1024 * 1024


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

    __slots__ = ("_res", "headers", "status_code", "templating", "_ended")

    def __init__(self, res: Any, templating=None):
        """
        Initialize the Response object.

        Args:
            res: The underlying native response instance.
            templating: Optional templating engine for rendering templates.
        """
        self._res = res
        self.headers: dict[str, str] = {}
        self.status_code: int = 200
        self.templating = templating
        self._ended = False

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
        # SECURITY: Prevent Header Injection (CRLF)
        if "\n" in key or "\r" in key or "\n" in value or "\r" in value:
            raise ValueError("Header injection detected")
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
        cookie: SimpleCookie = SimpleCookie()
        cookie[name] = value

        if max_age is not None:
            cookie[name]["max-age"] = max_age

        if expires:
            cookie[name]["expires"] = expires

        if path:
            cookie[name]["path"] = path

        if domain:
            cookie[name]["domain"] = domain

        if secure:
            cookie[name]["secure"] = True

        if http_only:
            cookie[name]["httponly"] = True

        if same_site:
            cookie[name]["samesite"] = same_site

        # Get the cookie string without the "Set-Cookie: " prefix
        # SECURITY: Validate path and domain to prevent attribute injection
        if path and (";" in path or "\r" in path or "\n" in path):
            raise ValueError("Invalid character in cookie path")
        if domain and (";" in domain or "\r" in domain or "\n" in domain):
            raise ValueError("Invalid character in cookie domain")

        cookie_string = cookie.output(header="").strip()
        self.header("Set-Cookie", cookie_string)
        return self

    def clear_cookie(
        self, name: str, path: str = "/", domain: str | None = None
    ) -> "Response":
        """Clear a cookie.
        usage:
            @app.get("/")
            def hello(req: Request, res: Response):
                res.json({"message": "hello world"})
                res.clear_cookie("session_id", path="/")
        """
        return self.set_cookie(
            name,
            "",
            path=path,
            domain=domain,
            expires="Thu, 01 Jan 1970 00:00:00 GMT",
            max_age=0,
            # Maintain defaults for security flags to be safe
            secure=False,
            http_only=True,
            same_site="Lax",
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

    async def get_data(self) -> bytes:
        """Get the request body data (async)."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        chunks = []
        current_size = [0]

        def on_data(chunk, is_last):
            def resolve():
                if future.done():
                    return

                chunk_len = len(chunk)
                # Check limit before appending
                if current_size[0] + chunk_len > MAX_BODY_SIZE:
                    future.set_exception(
                        ValueError(
                            f"Request body too large (max {MAX_BODY_SIZE} bytes)"
                        )
                    )
                    return

                current_size[0] += chunk_len
                chunks.append(chunk)

                if is_last:
                    future.set_result(b"".join(chunks))

            loop.call_soon_threadsafe(resolve)

        def on_abort():
            loop.call_soon_threadsafe(
                lambda: future.done()
                or future.set_exception(RuntimeError("Connection aborted"))
            )

        self._res.on_data(on_data)
        self._res.on_aborted(on_abort)

        return await future

    def get_remote_address_bytes(self) -> bytes:
        """Get the remote address as bytes."""
        return self._res.get_remote_address_bytes()
