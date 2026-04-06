try:

    from ._libxyra import ffi, lib

    def parse_path(path_str):
        params = []
        @ffi.callback("void(void*, const char*, size_t, const char*, size_t)")
        def _parse_cb(user_data, name_ptr, name_len, type_ptr, type_len):
            name = ffi.string(name_ptr, name_len).decode('utf-8')
            type_str = ffi.string(type_ptr, type_len).decode('utf-8')
            params.append((name, type_str))

        path_b = path_str.encode('utf-8')
        lib.xyra_parse_path(path_b, len(path_b), ffi.NULL, _parse_cb)

        # Convert {param} style back to :param style for uWS matching
        native_path = path_str
        parsed_params = []
        import re

        for param_tuple in params:
            # param_tuple is (name, type)
            name = param_tuple[0]
            # simple replacement
            native_path = re.sub(r'\{' + name + r'(?:-[^}]+)?\}', f':{name}', native_path)
            parsed_params.append(name)

        return native_path, parsed_params

except ImportError:
    def parse_path(path_str):
        return path_str, []


class Router:
    """
    HTTP route manager for Xyra applications.

    The Router class handles registration and organization of HTTP routes
    with their corresponding handler functions. It supports both decorator
    and method-based route registration.

    Attributes:
        routes: List of route dictionaries containing method, path, and handler.
        _route_map: Dictionary for O(1) route lookup by method and parsed path.
    """

    def __init__(self) -> None:
        """Initialize an empty router with no routes."""
        self.routes = []
        self._route_map: dict[str, dict] = {}

    def add_route(self, method: str, path: str, handler) -> None:
        """
        Add a new route to the router.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: URL path pattern.
            handler: Function to handle requests for this route.
        """
        parsed_path, param_names = parse_path(path)
        route_dict = {
            "method": method,
            "path": path,
            "parsed_path": parsed_path,
            "param_names": param_names,
            "handler": handler,
        }
        self.routes.append(route_dict)

        # Add to route map for O(1) lookup if needed
        route_key = f"{method}:{parsed_path}"
        self._route_map[route_key] = route_dict

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
