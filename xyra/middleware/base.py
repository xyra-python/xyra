from collections.abc import Awaitable, Callable

from ..request import Request
from ..response import Response


class BaseHTTPMiddleware:
    """
    Base class for ASGI-style middleware (like FastAPI/Starlette).

    Subclasses should override `dispatch`.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Implement this method to define middleware logic.

        Args:
            request: The Request object.
            call_next: A function that receives the request and returns a Response.

        Returns:
            A Response object.
        """
        raise NotImplementedError()

    async def __call__(self, request: Request, call_next: Callable):
        """
        Entry point for the middleware execution engine.
        """
        await self.dispatch(request, call_next)
