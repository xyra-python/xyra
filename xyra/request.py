from typing import Any
from urllib.parse import parse_qs, parse_qsl

from socketify import (
    Request as SocketifyRequest,
)
from socketify import (
    Response as SocketifyResponse,
)


class Request:
    def __init__(
        self,
        req: SocketifyRequest,
        res: "SocketifyResponse",
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

    @property
    def method(self) -> str:
        """Get the HTTP method of the request."""
        method = self._req.get_method()
        assert method is not None
        return method

    @property
    def url(self) -> str:
        """Get the URL of the request (cached)."""
        if self._url_cache is None:
            url = self._req.get_url()
            assert url is not None
            self._url_cache = url
        return self._url_cache

    @property
    def headers(self) -> dict[str, str]:
        """Get all headers as a dictionary (cached)."""
        if self._headers_cache is None:
            headers = {}
            self._req.for_each_header(
                lambda key, value: headers.update({key.lower(): value})
            )
            self._headers_cache = headers
        return self._headers_cache

    @property
    def query(self) -> str:
        """Get the raw query string (cached)."""
        if self._query_cache is None:
            url = self.url
            if "?" in url:
                self._query_cache = url.split("?", 1)[1]
            else:
                self._query_cache = ""
        return self._query_cache

    @property
    def query_params(self) -> dict[str, list]:
        """Parse and return query parameters as a dictionary (cached)."""
        if self._query_params_cache is None:
            query_string = self.query
            if not query_string:
                self._query_params_cache = {}
            else:
                self._query_params_cache = parse_qs(query_string)
        return self._query_params_cache

    def get_parameter(self, index: int) -> str | None:
        """Get a URL parameter by index."""
        return self._req.get_parameter(index)

    def get_header(self, name: str, default: str | None = None) -> str | None:
        """Get a specific header value."""
        return self.headers.get(name.lower(), default)

    async def text(self) -> str:
        """Get the request body as text."""
        body = await self._res.get_data()
        if isinstance(body, bytes):
            return body.decode("utf-8")
        elif isinstance(body, str):
            return body
        else:
            return str(body)

    async def json(self) -> Any:  # type: ignore
        """Parse the request body as JSON."""
        return await self._res.get_json()

    async def form(self) -> dict[str, str]:
        """Parse form data from the request body."""
        text_content = await self.text()
        if not text_content:
            return {}

        # Optimized form parsing using urllib.parse.parse_qsl for proper URL decoding
        try:
            parsed_pairs = parse_qsl(text_content, keep_blank_values=True)
            form_data = dict(parsed_pairs)
            return form_data
        except Exception:
            # Fallback to simple parsing if parse_qsl fails
            form_data = {}
            for pair in text_content.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    form_data[key] = value
            return form_data

    @property
    def content_type(self) -> str | None:
        """Get the content type of the request."""
        return self.get_header("content-type")

    @property
    def content_length(self) -> int | None:
        """Get the content length of the request."""
        length = self.get_header("content-length")
        return int(length) if length else None

    def is_json(self) -> bool:
        """Check if the request content type is JSON."""
        content_type = self.content_type
        return content_type is not None and "application/json" in content_type.lower()

    def is_form(self) -> bool:
        """Check if the request content type is form data."""
        content_type = self.content_type
        return (
            content_type is not None
            and "application/x-www-form-urlencoded" in content_type.lower()
        )
