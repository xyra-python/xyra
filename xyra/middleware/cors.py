from ..request import Request
from ..response import Response


class CorsMiddleware:
    """CORS (Cross-Origin Resource Sharing) middleware for Xyra applications."""

    def __init__(
        self,
        allowed_origins: str | list[str] | None = None,
        allowed_methods: str | list[str] | None = None,
        allowed_headers: str | list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 3600,
    ):
        # Handle string or list inputs
        if isinstance(allowed_origins, str):
            self.allowed_origins = [allowed_origins]
        else:
            self.allowed_origins = allowed_origins or ["*"]

        if isinstance(allowed_methods, str):
            self.allowed_methods = [allowed_methods]
        else:
            self.allowed_methods = allowed_methods or [
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "OPTIONS",
                "HEAD",
                "PATCH",
            ]

        if isinstance(allowed_headers, str):
            self.allowed_headers = [allowed_headers]
        else:
            self.allowed_headers = allowed_headers or [
                "Content-Type",
                "Authorization",
                "X-Requested-With",
            ]

        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if the origin is allowed."""
        if "*" in self.allowed_origins:
            return True
        return origin in self.allowed_origins

    def __call__(self, request: Request, response: Response):
        """Handle CORS for the request."""
        origin = request.get_header("origin")

        # Set CORS headers if origin is provided and allowed
        if origin and self._is_origin_allowed(origin):
            response.header("Access-Control-Allow-Origin", origin)
        elif "*" in self.allowed_origins and not self.allow_credentials:
            response.header("Access-Control-Allow-Origin", "*")

        # Set other CORS headers
        response.header("Access-Control-Allow-Methods", ", ".join(self.allowed_methods))
        response.header("Access-Control-Allow-Headers", ", ".join(self.allowed_headers))

        if self.allow_credentials:
            response.header("Access-Control-Allow-Credentials", "true")

        response.header("Access-Control-Max-Age", str(self.max_age))

        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            response.status(204)
            response.send("")
            response._ended = True
            return

        # For other requests, headers are set, continue to next middleware


def cors(
    allowed_origins: str | list[str] | None = None,
    allowed_methods: str | list[str] | None = None,
    allowed_headers: str | list[str] | None = None,
    allow_credentials: bool = False,
    max_age: int = 3600,
):
    """
    Create a CORS middleware function.

    This is a convenience function that creates and returns a CORS middleware instance.
    """
    return CorsMiddleware(
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
        allowed_headers=allowed_headers,
        allow_credentials=allow_credentials,
        max_age=max_age,
    )
