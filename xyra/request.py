import socket
import sys
from typing import Any
from urllib.parse import parse_qs

try:
    if sys.implementation.name == "pypy":
        import ujson as json_lib
    else:
        import orjson as json_lib
except ImportError:
    import json as json_lib

try:
    from ._libxyra import ffi, lib
except ImportError:
    ffi = None
    lib = None

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
        "_scheme_cache",
        "_host_cache",
        "_port_cache",
        "_body_cache",
        "_json_cache",
        "_form_cache",
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
        self._scheme_cache: str | None = None
        self._host_cache: str | None = None
        self._port_cache: int | None = None
        self._body_cache: str | bytes | None = None
        self._json_cache: Any = None
        self._form_cache: dict[str, str] | None = None

    @property
    def scheme(self) -> str:
        """
        Get the request scheme (http or https).
        Defaults to 'http' unless updated by middleware (e.g. ProxyHeadersMiddleware).

        Returns:
            Scheme string ('http' or 'https').
        """
        if self._scheme_cache is None:
            self._scheme_cache = "http"
        return self._scheme_cache

    @property
    def host(self) -> str:
        """
        Get the request host (domain or IP).
        Defaults to Host header (without port).

        Returns:
            Host string (e.g., "example.com" or "127.0.0.1").
        """
        if self._host_cache is None:
            host_header = self.get_header("host", "")
            if not host_header:
                self._host_cache = ""
                return self._host_cache

            # Handle IPv6 literals (e.g., [::1]:8080)
            if host_header.startswith("["):
                end = host_header.find("]")
                if end != -1:
                    self._host_cache = host_header[: end + 1]
                else:
                    self._host_cache = host_header
            # Handle IPv4 or Domain with port (e.g., example.com:8080)
            elif ":" in host_header:
                self._host_cache = host_header.split(":")[0]
            else:
                self._host_cache = host_header

        return self._host_cache

    @property
    def port(self) -> int:
        """
        Get the request port.
        Defaults to Host header port or 80/443 based on scheme.

        Returns:
            Port number as integer.
        """
        if self._port_cache is None:
            host_header = self.get_header("host", "")

            # Default based on scheme
            default_port = 443 if self.scheme == "https" else 80

            if not host_header:
                self._port_cache = default_port
                return self._port_cache

            if host_header.startswith("["):
                # IPv6 literal with port [::1]:8080
                end = host_header.find("]")
                if (
                    end != -1
                    and len(host_header) > end + 1
                    and host_header[end + 1] == ":"
                ):
                    try:
                        self._port_cache = int(host_header[end + 2 :])
                    except ValueError:
                        self._port_cache = default_port
                else:
                    self._port_cache = default_port
            elif ":" in host_header:
                # IPv4 or Domain with port
                try:
                    self._port_cache = int(host_header.split(":")[1])
                except ValueError:
                    self._port_cache = default_port
            else:
                self._port_cache = default_port

        return self._port_cache

    @property
    def method(self) -> str:
        """
        Get the HTTP method of the request.

        Returns:
            HTTP method (GET, POST, PUT, DELETE, etc.).
        """
        if hasattr(self._req, "get_method"):
            method = self._req.get_method()
        elif ffi:
            # CFFI fallback
            out_ptr = ffi.new("char**")
            length = lib.xyra_req_get_method(self._req, out_ptr)
            method = ffi.string(out_ptr[0], length).decode('utf-8')
        else:
            method = "GET"

        if method is None:
            raise ValueError("Request method is None")
        return method

    @property
    def url(self) -> str:
        """
        Get the request URL path (cached).
        """
        if self._url_cache is None:
            if hasattr(self._req, "get_url"):
                url = self._req.get_url()
            elif ffi:
                out_ptr = ffi.new("char**")
                length = lib.xyra_req_get_url(self._req, out_ptr)
                url = ffi.string(out_ptr[0], length).decode('utf-8')
            else:
                url = "/"
            if url is None:
                raise ValueError("Request URL is None")
            self._url_cache = url
        return self._url_cache

    @property
    def full_path(self) -> str:
        """
        Get the full request path including query string.

        Returns:
            Path + query string (e.g., "/api/users?id=1").
        """
        path = self.url
        query = self.query
        if query:
            return f"{path}?{query}"
        return path

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
            except Exception:  # nosec B110
                self._remote_addr_cache = "unknown"
        return self._remote_addr_cache

    @property
    def headers(self) -> dict[str, str]:
        """
        Get all headers as a dictionary (cached).
        """
        if self._headers_cache is None:
            if hasattr(self._req, "get_headers"):
                self._headers_cache = self._req.get_headers()
            elif hasattr(self._req, "for_each_header"):
                headers = {}
                def cb(k, v):
                    headers[k.lower()] = v
                self._req.for_each_header(cb)
                self._headers_cache = headers
            elif ffi:
                headers = {}
                @ffi.callback("void(void*, const char*, size_t, const char*, size_t)")
                def _cb(user_data, key_ptr, key_len, val_ptr, val_len):
                    k = ffi.string(key_ptr, key_len).decode('utf-8').lower()
                    v = ffi.string(val_ptr, val_len).decode('utf-8')
                    headers[k] = v

                lib.xyra_req_get_headers(self._req, ffi.NULL, _cb)
                self._headers_cache = headers
            else:
                self._headers_cache = {}
        return self._headers_cache

    @property
    def query(self) -> str:
        """
        Get the raw query string (cached).
        """
        if self._query_cache is None:
            if hasattr(self._req, "get_query"):
                # uWS / pybind get_query() with no args returns the whole query string.
                # In CFFI, we pass empty string to get the whole thing?
                # Actually lib.xyra_req_get_query expects a key, returning specific value.
                # Oh wait, uWebSockets HttpRequest::getQuery() without args returns full query.
                pass # need to fix

            if hasattr(self._req, "get_query"):
                try:
                    self._query_cache = self._req.get_query()
                except TypeError:
                    self._query_cache = self._req.get_query("")
            elif ffi:
                out_ptr = ffi.new("char**")
                # Need an empty string for key to get full query?
                # C API xyra_req_get_query(req, "") ?
                # If key is empty, let's assume it gets full query.
                c_key = b""
                length = lib.xyra_req_get_query(self._req, c_key, out_ptr)
                if length > 0:
                    self._query_cache = ffi.string(out_ptr[0], length).decode('utf-8')
                else:
                    self._query_cache = ""
            else:
                self._query_cache = ""

        return self._query_cache

    def get_queries(self) -> dict[str, list]:
        """
        Return query parameters as dictionary.
        This provides compatibility with the pybind11 native interface which
        some internal modules might still check for.
        """
        return self.query_params

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
            try:
                if hasattr(self._req, "get_queries"):
                    self._query_params_cache = self._req.get_queries()
                elif ffi and getattr(lib, "xyra_req_get_queries", None) is not None:
                    queries = {}
                    @ffi.callback("void(void*, const char*, size_t, const char*, size_t)")
                    def _cb(user_data, key_ptr, key_len, val_ptr, val_len):
                        k = ffi.string(key_ptr, key_len).decode('utf-8')
                        v = ffi.string(val_ptr, val_len).decode('utf-8')
                        if k not in queries:
                            queries[k] = []
                        queries[k].append(v)

                    lib.xyra_req_get_queries(self._req, ffi.NULL, _cb)
                    self._query_params_cache = queries
                else:
                    query_string = self.query
                    if not query_string:
                        self._query_params_cache = {}
                    else:
                        # SECURITY: Limit max_num_fields to 1000 to prevent DoS via Hash Collision / CPU Exhaustion
                        self._query_params_cache = parse_qs(
                            query_string, keep_blank_values=True, max_num_fields=1000
                        )
            except ValueError as e:
                # SECURITY: Handle DoS attempt
                logger = get_logger("xyra")
                logger.warning(
                    f"Query params exceeded max fields limit or failed to parse: {e}. Returning empty dict."
                )
                self._query_params_cache = {}
        return self._query_params_cache

    def get_parameter(self, index: int) -> str | None:
        """
        Get a URL parameter by index.
        """
        if hasattr(self._req, "get_parameter"):
            return self._req.get_parameter(index)

        out_ptr = ffi.new("char**")
        length = lib.xyra_req_get_parameter(self._req, index, out_ptr)
        if length > 0:
            return ffi.string(out_ptr[0], length).decode('utf-8')
        return None

    def get_header(self, name: str, default: str | None = None) -> str | None:
        """
        Get a specific header value.
        """
        if self._headers_cache is not None:
            return self._headers_cache.get(name.lower(), default)

        if hasattr(self._req, "get_header"):
            value = self._req.get_header(name.lower())
            return value if value else default

        out_ptr = ffi.new("char**")
        c_name = name.lower().encode('utf-8')
        length = lib.xyra_req_get_header(self._req, c_name, out_ptr)
        if length > 0:
            return ffi.string(out_ptr[0], length).decode('utf-8')
        return default

    async def text(self) -> str:
        """
        Get the request body as text.

        usage:
            @app.post("/echo")
            async def echo(req: Request, res: Response):
                text = await req.text()
                res.text(text)
        """
        # Cache body to allow multiple reads (e.g. CSRF middleware + handler)
        if self._body_cache is None:
            self._body_cache = await self._res.get_data()

        body = self._body_cache
        if isinstance(body, bytes):
            # SECURITY: Use errors="replace" to prevent UnicodeDecodeError DoS
            # when handling malformed UTF-8 payloads.
            return body.decode("utf-8", errors="replace")
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
        # Return cached JSON if available
        if self._json_cache is not None:
            return self._json_cache

        # SECURITY: Strictly validate Content-Type before parsing JSON
        content_type = self.get_header("content-type", "")
        if not isinstance(content_type, str):
            content_type = ""
        media_type = content_type.split(";")[0].strip().lower()
        if not media_type or not (
            media_type == "application/json" or
            media_type.endswith("+json")
        ):
            from .exceptions import bad_request
            raise bad_request(
                f"Invalid Content-Type for JSON parsing: '{content_type}'. "
                f"Expected 'application/json' or similar '+json' media type. "
            )

        # Cache body to allow multiple reads
        if self._body_cache is None:
            self._body_cache = await self._res.get_data()

        # PERF: Get raw data (bytes) to avoid unnecessary decoding to string
        body = self._body_cache
        if not body:
            return {}

        parsed = None
        if isinstance(body, bytes):
            parsed = self.parse_json(body)
        elif isinstance(body, str):
            parsed = self.parse_json(body)
        else:
            # Fallback for other types
            parsed = self.parse_json(str(body))

        # Cache parsed JSON
        self._json_cache = parsed
        return parsed

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
            from .exceptions import bad_request
            logger = get_logger("xyra")
            logger.warning(f"Failed to parse JSON: {e}")
            # SECURITY: Raise HTTP 400 Bad Request instead of ValueError to prevent 500 error logs DoS
            # SECURITY: Do not leak exception details to the client
            raise bad_request("Invalid JSON format") from None

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
        # Return cached form if available
        if self._form_cache is not None:
            return self._form_cache

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
            parsed_pairs = []
            parsed = False

            if lib and hasattr(lib, "xyra_parse_qsl"):
                try:
                    @ffi.callback("void(void*, const char*, size_t, const char*, size_t)")
                    def _cb(user_data, key_ptr, key_len, val_ptr, val_len):
                        k = ffi.string(key_ptr, key_len).decode('utf-8')
                        v = ffi.string(val_ptr, val_len).decode('utf-8')
                        parsed_pairs.append((k, v))
                    content_b = text_content.encode('utf-8')
                    lib.xyra_parse_qsl(content_b, len(content_b), True, 1000, ffi.NULL, _cb)
                    parsed = True
                except Exception:  # nosec B110
                    pass

            if not parsed:
                # The tests mock parse_qsl in xyra.request, so we need to fallback correctly
                # if we hit a mocked exception
                try:
                    from .libxyra import parse_qsl as cpp_parse_qsl
                    parsed_pairs = cpp_parse_qsl(
                        text_content, keep_blank_values=True, max_num_fields=1000
                    )
                    parsed = True
                except Exception:  # nosec B110
                    pass

            if not parsed:
                from urllib.parse import parse_qs
                parsed_qs = parse_qs(
                    text_content, keep_blank_values=True, max_num_fields=1000
                )
                parsed_pairs = []
                for k, v in parsed_qs.items():
                    parsed_pairs.append((k, v[-1] if isinstance(v, list) and v else v))

            # Convert list of tuples to dict, handling multiple values appropriately if needed.
            # parse_qs returns a dict of lists, parse_qsl returns list of tuples.
            # Our interface expects dict[str, str], so we take the last value.
            form_data = dict(parsed_pairs)
            self._form_cache = form_data
            return form_data
        except ValueError as e:
            # SECURITY: Handle DoS attempt
            logger = get_logger("xyra")
            logger.warning(
                f"Form data exceeded max fields limit: {e}. Returning empty dict."
            )
            self._form_cache = {}
            return {}
        except Exception as e:
            # Secure handling: If parse_qsl fails, return empty dict and log error.
            # Do NOT fallback to simple split which bypasses URL decoding.
            logger = get_logger("xyra")
            logger.warning(f"Failed to parse form data: {e}. Returning empty dict.")
            self._form_cache = {}
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
