from .params import parse_path


class Router:
    """
    HTTP route manager for Xyra applications.

    The Router class handles registration and organization of HTTP routes
    with their corresponding handler functions. It supports both decorator
    and method-based route registration.

    Attributes:
        routes: List of route dictionaries containing method, path, and handler.
    """

    def __init__(self) -> None:
        """Initialize an empty router with no routes."""
        self.routes = []

    def add_route(self, method: str, path: str, handler) -> None:
        """
        Add a new route to the router.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: URL path pattern.
            handler: Function to handle requests for this route.
        """
        parsed_path, param_names = parse_path(path)
        self.routes.append(
            {
                "method": method,
                "path": path,
                "parsed_path": parsed_path,
                "param_names": param_names,
                "handler": handler,
            }
        )

    def get(self, path: str):
        """
        Register a GET route.

        Args:
            path: URL path pattern for the route.

        Returns:
            Decorator function that registers the handler.
        """

        def decorator(handler):
            self.add_route("GET", path, handler)
            return handler

        return decorator

    def post(self, path: str):
        def decorator(handler):
            self.add_route("POST", path, handler)
            return handler

        return decorator

    def put(self, path: str):
        def decorator(handler):
            self.add_route("PUT", path, handler)
            return handler

        return decorator

    def delete(self, path: str):
        def decorator(handler):
            self.add_route("DELETE", path, handler)
            return handler

        return decorator

    def patch(self, path: str):
        def decorator(handler):
            self.add_route("PATCH", path, handler)
            return handler

        return decorator

    def head(self, path: str):
        def decorator(handler):
            self.add_route("HEAD", path, handler)
            return handler

        return decorator

    def options(self, path: str):
        def decorator(handler):
            self.add_route("OPTIONS", path, handler)
            return handler

        return decorator
