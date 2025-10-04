class Router:
    def __init__(self):
        self.routes = []

    def add_route(self, method: str, path: str, handler):
        self.routes.append({"method": method, "path": path, "handler": handler})

    def get(self, path: str):
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