import json
from typing import Any
from urllib.parse import parse_qs

from socketify import Request as SocketifyRequest


class Request:
    def __init__(self, req: SocketifyRequest, params: dict[str, str] | None = None):
        self._req = req
        self.params = params or {}

    @property
    def method(self) -> str:
        """Get the HTTP method of the request."""
        method = self._req.get_method()
        assert method is not None
        return method

    @property
    def url(self) -> str:
        """Get the URL of the request."""
        url = self._req.get_url()
        assert url is not None
        return url

    @property
    def headers(self) -> dict[str, str]:
        """Get all headers as a dictionary."""
        headers = {}
        self._req.for_each_header(lambda key, value: headers.update({key: value}))
        return headers

    @property
    def query(self) -> str:
        """Get the raw query string."""
        url = self._req.get_url()
        if url and "?" in url:
            return url.split("?", 1)[1]
        return ""

    @property
    def query_params(self) -> dict[str, list]:
        """Parse and return query parameters as a dictionary."""
        query_string = self.query
        if not query_string:
            return {}
        return parse_qs(query_string)

    def get_parameter(self, index: int) -> str | None:
        """Get a URL parameter by index."""
        return self._req.get_parameter(index)

    def get_header(self, name: str, default: str | None = None) -> str | None:
        """Get a specific header value."""
        return self.headers.get(name.lower(), default)

    async def text(self) -> str:
        """Get the request body as text."""
        return await self._req.text()  # type: ignore

    async def json(self) -> Any:
        """Parse the request body as JSON."""
        try:
            text_content = await self.text()
            if not text_content:
                return {}
            return json.loads(text_content)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in request body") from None

    async def form(self) -> dict[str, str]:
        """Parse form data from the request body."""
        text_content = await self.text()
        if not text_content:
            return {}

        # Simple form parsing - in production you might want to use a proper form parser
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
