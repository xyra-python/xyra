import inspect
from typing import Any, Callable, Dict, List, Optional, Union

import socketify

from .request import Request
from .response import Response
from .routing import Router
from .swagger import generate_swagger
from .templating import Templating
from .websockets import WebSocket


class App:
    def __init__(
        self,
        options=None,
        templates_directory: str = "templates",
        swagger_options: Optional[Dict[str, Any]] = None,
    ):
        self._app = socketify.App(options)
        self._router = Router()
        self._ws_routes: List[Dict[str, Any]] = []
        self._middlewares: List[Callable] = []
        self.templates = Templating(templates_directory)
        self.swagger_options = swagger_options

    def route(self, method: str, path: str, handler: Callable = None):
        """Register a route with the specified method."""
        if handler is None:
            # Used as decorator
            def decorator(func):
                self._router.add_route(method.upper(), path, func)
                return func

            return decorator
        else:
            # Used as method call
            self._router.add_route(method.upper(), path, handler)
            return self

    def get(self, path: str, handler: Callable = None):
        """Register a GET route."""
        return self.route("GET", path, handler)

    def post(self, path: str, handler: Callable = None):
        """Register a POST route."""
        return self.route("POST", path, handler)

    def put(self, path: str, handler: Callable = None):
        """Register a PUT route."""
        return self.route("PUT", path, handler)

    def delete(self, path: str, handler: Callable = None):
        """Register a DELETE route."""
        return self.route("DELETE", path, handler)

    def patch(self, path: str, handler: Callable = None):
        """Register a PATCH route."""
        return self.route("PATCH", path, handler)

    def head(self, path: str, handler: Callable = None):
        """Register a HEAD route."""
        return self.route("HEAD", path, handler)

    def options(self, path: str, handler: Callable = None):
        """Register an OPTIONS route."""
        return self.route("OPTIONS", path, handler)

    def use(self, middleware: Callable):
        """Add a middleware to the application."""
        self._middlewares.append(middleware)
        return self

    def static_files(self, path: str, directory: str):
        """Serve static files from a directory."""
        return self._app.static(path, directory)

    def websocket(self, path: str, handler: Union[Callable, Dict[str, Callable]]):
        """Register a WebSocket route."""
        self._ws_routes.append({"path": path, "handler": handler})
        return self

    def _create_ws_handler(self, handler: Callable):
        def ws_handler(ws):
            websocket = WebSocket(ws)
            handler(websocket)

        return ws_handler

    def _create_ws_message_handler(self, handler: Callable):
        def ws_message_handler(ws, message, opcode):
            websocket = WebSocket(ws)
            handler(websocket, message, opcode)

        return ws_message_handler

    def _create_ws_close_handler(self, handler: Callable):
        def ws_close_handler(ws, code, message):
            websocket = WebSocket(ws)
            handler(websocket, code, message)

        return ws_close_handler

    def _create_final_handler(
        self, route_handler: Callable, middlewares: List[Callable]
    ):
        def final_handler(res, req):
            request = Request(req)
            response = Response(res, self.templates)
            route_handler(request, response)

        return final_handler

    def _register_routes(self):
        """Register all routes with the underlying socketify app."""
        try:
            for route in self._router.routes:
                method = route["method"].lower()
                path = route["path"]

                final_handler = self._create_final_handler(
                    route["handler"], self._middlewares
                )

                # Use the app methods to register routes
                if method == "get":
                    self._app.get(path, final_handler)
                elif method == "post":
                    self._app.post(path, final_handler)
                elif method == "put":
                    self._app.put(path, final_handler)
                elif method == "delete":
                    self._app.delete(path, final_handler)
                elif method == "patch":
                    self._app.patch(path, final_handler)
                elif method == "head":
                    self._app.head(path, final_handler)
                elif method == "options":
                    self._app.options(path, final_handler)
        except Exception as e:
            print(f"Error registering routes: {e}")
            raise

    def _register_ws_routes(self):
        """Register all WebSocket routes."""
        for route in self._ws_routes:
            path = route["path"]
            ws_handler = route["handler"]

            # Handle both dict-style and single function handlers
            if isinstance(ws_handler, dict):
                open_handler = ws_handler.get("open")
                if open_handler:
                    open_handler = self._create_ws_handler(open_handler)

                message_handler = ws_handler.get("message")
                if message_handler:
                    message_handler = self._create_ws_message_handler(message_handler)

                close_handler = ws_handler.get("close")
                if close_handler:
                    close_handler = self._create_ws_close_handler(close_handler)

                self._app.ws(
                    path,
                    {
                        "open": open_handler,
                        "message": message_handler,
                        "close": close_handler,
                    },
                )
            else:
                # Single function handler - treat as open handler
                open_handler = self._create_ws_handler(ws_handler)
                self._app.ws(path, {"open": open_handler})

    def enable_swagger(self):
        """Enable Swagger UI documentation."""
        if not self.swagger_options:
            return

        swagger_json_path = self.swagger_options.get(
            "swagger_json_path", "/docs/swagger.json"
        )
        swagger_ui_path = self.swagger_options.get("swagger_ui_path", "/docs")

        def get_swagger_json(req: Request, res: Response):
            swagger_spec = generate_swagger(self, **self.swagger_options)
            res.json(swagger_spec)

        self.get(swagger_json_path, get_swagger_json)

        swagger_ui_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Swagger UI</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
            <style>
                html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
                *, *:before, *:after {{ box-sizing: inherit; }}
                body {{ margin: 0; background: #fafafa; }}
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"> </script>
            <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js"> </script>
            <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: "{swagger_json_path}",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                }})
                window.ui = ui
            }}
            </script>
        </body>
        </html>
        """

        def get_swagger_ui(req: Request, res: Response):
            res.html(swagger_ui_html)

        self.get(swagger_ui_path, get_swagger_ui)

    def run_server(self, port: int = 8000, host: str = "0.0.0.0"):
        """Start the server."""
        if self.swagger_options:
            self.enable_swagger()

        self._register_routes()
        self._register_ws_routes()

        print(f"🚀 Xyra server running on http://{host}:{port}")
        if self.swagger_options:
            swagger_ui_path = self.swagger_options.get("swagger_ui_path", "/docs")
            print(f"📚 API docs available at http://{host}:{port}{swagger_ui_path}")

        self._app.listen(port, lambda config: print(f"Listening on port {port}"))
        self._app.run()

    def listen(self, port: int = 8000, host: str = "0.0.0.0"):
        """Alias for run_server method."""
        return self.run_server(port, host)

    @property
    def router(self):
        """Get the router instance."""
        return self._router

    @property
    def middlewares(self):
        """Get the middlewares list."""
        return self._middlewares

    @property
    def ws_routes(self):
        """Get the WebSocket routes list."""
        return self._ws_routes
