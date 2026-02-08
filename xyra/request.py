import socket
import sys
from typing import Any
from urllib.parse import parse_qs, parse_qsl

if sys.implementation.name == "pypy":
    import ujson as json_lib
else:
    import orjson as json_lib

from .logger import get_logger


class Request:
    """
    HTTP request wrapper for Xyra applications.
    This class provides a convenient interface for accessing HTTP request data,
    including headers, query parameters, URL, body parsing, and route parameters.
    Attributes:
        _req: The underlying native request object.
        _res: The underlying native response object.
        params: Dictionary of route parameters (e.g., {id: "123"}).
        _headers_cache: Cached headers dictionary.
        _query_params_cache: Cached query parameters dictionary.
        _url_cache: Cached full URL string.
        _query_cache: Cached query string.
    """

    __slots__ = (
        "_req",
        "_res",
        "params",
        "_headers_cache",
        "_query_params_cache",
        "_url_cache",
        "_query_cache",
        "__dict__",
        "_remote_addr_cache",
    )

    def __init__(
        self,
        req: Any,
        res: Any,
        params: dict[str, str] | None = None,
    ):
        self._req = req
        self._res = res
        self.params = params or {}
        # Lazy loading caches
        self._headers_cache: dict[str, str] | None = None
        self._query_params_cache: dict[str, list] | None = None
        self._url_cache: str | None = None
        self._query_cache: str | None = None
        self._remote_addr_cache: str | None = None

    @property
    def method(self) -> str:
        """
        Get the HTTP method of the request.

        Returns:
            HTTP method (GET, POST, PUT, DELETE, etc.).

        usage:
            @app.route("*", "/api/*")
            def api_handler(req: Request, res: Response):
                if req.method == "GET":
                    res.json({"method": "GET"})
                elif req.method == "POST":
                    res.json({"method": "POST"})
        """
        method = self._req.get_method()
        if method is None:
            raise ValueError("Request method is None")
        return method

    @property
    def url(self) -> str:
        """
        Get the URL of the request (cached).

        Returns:
            Full request URL including query string.

        usage:
            @app.get("/debug")
            def debug(req: Request, res: Response):
                res.json({"url": req.url, "method": req.method})
        """
        if self._url_cache is None:
            url = self._req.get_url()
            if url is None:
                raise ValueError("Request URL is None")
            self._url_cache = url
        return self._url_cache

    @property
    def remote_addr(self) -> str:
        """
        Get the remote address (IP) of the client.

        Returns:
            IP address as a string (e.g., "127.0.0.1" or "::1").
        """
        if self._remote_addr_cache is None:
            try:
                addr_bytes = self._res.get_remote_address_bytes()
                if not addr_bytes:
                    self._remote_addr_cache = "unknown"
                elif len(addr_bytes) == 4:
                    self._remote_addr_cache = socket.inet_ntop(
                        socket.AF_INET, addr_bytes
                    )
                elif len(addr_bytes) == 16:
                    self._remote_addr_cache = socket.inet_ntop(
                        socket.AF_INET6, addr_bytes
                    )
                else:
                    self._remote_addr_cache = "unknown"
            except Exception:
                self._remote_addr_cache = "unknown"
        return self._remote_addr_cache

    @property
    def headers(self) -> dict[str, str]:
        """
        Get all headers as a dictionary (cached).

        Returns:
            Dictionary mapping lowercase header names to values.

        usage:
            @app.get("/headers")
            def show_headers(req: Request, res: Response):
                res.json(req.headers)
        """
        if self._headers_cache is None:
            # PERF: use native's direct accessor if available (faster C++ implementation)
            # This returns a dict with lowercase keys, matching our requirement.
            if hasattr(self._req, "get_headers"):
                self._headers_cache = self._req.get_headers()
            else:
                headers = {}
                # PERF: avoid creating intermediate dicts and lambda overhead
                self._req.for_each_header(
                    lambda key, value: headers.__setitem__(key.lower(), value)
                )
                self._headers_cache = headers
        return self._headers_cache

    @property
    def query(self) -> str:
        """
        Get the raw query string (cached).

        Returns:
            Query string without the leading '?' or empty string.

        usage:
            # GET /search?q=python&page=1
            @app.get("/search")
            def search(req: Request, res: Response):
                raw_query = req.query  # "q=python&page=1"
                res.json({"raw_query": raw_query})
        """
        if self._query_cache is None:
            # PERF: use native's direct accessor instead of parsing URL
            self._query_cache = self._req.get_query()
        return self._query_cache

    @property
    def query_params(self) -> dict[str, list]:
        """
        Parse and return query parameters as a dictionary (cached).

        Returns:
            Dictionary mapping parameter names to lists of values.

        usage:
            # GET /search?q=python&page=1
            @app.get("/search")
            def search(req: Request, res: Response):
                query = req.query_params.get("q", [""])[0]
                page = int(req.query_params.get("page", ["1"])[0])
                res.json({"query": query, "page": page})
        """
        if self._query_params_cache is None:
            # PERF: use native's direct accessor if available (faster C++ implementation)
            # This returns a dict with lists of values, matching parse_qs behavior.
            if hasattr(self._req, "get_queries"):
                self._query_params_cache = self._req.get_queries()
            else:
                query_string = self.query
                if not query_string:
                    self._query_params_cache = {}
                else:
                    self._query_params_cache = parse_qs(query_string)
        return self._query_params_cache

    def get_parameter(self, index: int) -> str | None:
        """
        Get a URL parameter by index.

        usage:
            @app.get("/users/{id}")
            def get_user(req: Request, res: Response):
                user_id = req.get_parameter(0)  # Gets {id} value
                res.json({"user_id": user_id})
        """
        return self._req.get_parameter(index)

    def get_header(self, name: str, default: str | None = None) -> str | None:
        """
        Get a specific header value.

        usage:
            @app.get("/auth")
            def check_auth(req: Request, res: Response):
                token = req.get_header("authorization")
                if not token:
                    res.unauthorized().json({"error": "No token"})
                else:
                    res.ok().json({"token": token})
        """
        # PERF: if headers are already cached, use the dictionary lookup
        if self._headers_cache is not None:
            return self._headers_cache.get(name.lower(), default)

        # PERF: otherwise use direct native access to avoid building the whole dict
        value = self._req.get_header(name.lower())
        return value if value else default

    async def text(self) -> str:
        """
        Get the request body as text.

        usage:
            @app.post("/echo")
            async def echo(req: Request, res: Response):
                text = await req.text()
                res.text(text)
        """
        body = await self._res.get_data()
        if isinstance(body, bytes):
            return body.decode("utf-8")
        elif isinstance(body, str):
            return body
        else:
            return str(body)

    async def json(self) -> Any:  # type: ignore
        """
        Parse the request body as JSON.

        usage:
            @app.post("/api/data")
            async def create_data(req: Request, res: Response):
                data = await req.json()
                # Process data...
                res.json({"received": data})
        """
        # PERF: Get raw data (bytes) to avoid unnecessary decoding to string
        body = await self._res.get_data()
        if not body:
            return {}

        if isinstance(body, bytes):
            return self.parse_json(body)

        if isinstance(body, str):
            return self.parse_json(body)

        # Fallback for other types
        return self.parse_json(str(body))

    def parse_json(self, json_string: str | bytes) -> Any:
        """
        Parse a JSON string or bytes synchronously.

        usage:
            json_str = '{"name": "John"}'
            data = req.parse_json(json_str)
            print(data["name"])  # "John"
        """
        try:
            return json_lib.loads(json_string)
        except Exception as e:
            raise ValueError(f"Invalid JSON: {e}") from e

    async def form(self) -> dict[str, str]:
        """
        Parse form data from the request body.

        usage:
            @app.post("/submit")
            async def submit_form(req: Request, res: Response):
                form_data = await req.form()
                name = form_data.get("name")
                res.json({"submitted": True, "name": name})
        """
        try:
            text_content = await self.text()
        except UnicodeDecodeError:
            logger = get_logger("xyra")
            logger.warning(
                "Failed to decode form data: Invalid UTF-8. Returning empty dict."
            )
            return {}

        if not text_content:
            return {}

        # Optimized form parsing using urllib.parse.parse_qsl for proper URL decoding
        try:
            # SECURITY: Limit max_num_fields to 1000 to prevent DoS via Hash Collision / CPU Exhaustion
            parsed_pairs = parse_qsl(
                text_content, keep_blank_values=True, max_num_fields=1000
            )
            form_data = dict(parsed_pairs)
            return form_data
        except ValueError as e:
            # SECURITY: Handle DoS attempt
            logger = get_logger("xyra")
            logger.warning(
                f"Form data exceeded max fields limit: {e}. Returning empty dict."
            )
            return {}
        except Exception as e:
            # Secure handling: If parse_qsl fails, return empty dict and log error.
            # Do NOT fallback to simple split which bypasses URL decoding.
            logger = get_logger("xyra")
            logger.warning(f"Failed to parse form data: {e}. Returning empty dict.")
            return {}

    @property
    def content_type(self) -> str | None:
        """
        Get the content type of the request.

        usage:
            if req.content_type == "application/json":
                data = await req.json()
        """
        return self.get_header("content-type")

    @property
    def content_length(self) -> int | None:
        """
        Get the content length of the request.

        Returns:
            Content-Length as integer or None.

        Example:
            length = req.content_length
            if length and length > 1024:
                res.bad_request().json({"error": "Too large"})
        """
        length = self.get_header("content-length")
        return int(length) if length else None

    def is_json(self) -> bool:
        """
        Check if the request content type is JSON.

        usage:
            if req.is_json():
                data = await req.json()
            else:
                res.bad_request().json({"error": "Expected JSON"})
        """
        content_type = self.content_type
        return content_type is not None and "application/json" in content_type.lower()

    def is_form(self) -> bool:
        """
        Check if the request content type is form data.

        usage:
            if req.is_form():
                form_data = await req.form()
            else:
                res.bad_request().json({"error": "Expected form data"})
        """
        content_type = self.content_type
        return (
            content_type is not None
            and "application/x-www-form-urlencoded" in content_type.lower()
        )
