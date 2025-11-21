import asyncio
import logging
import os
import socket
import time
import threading
import traceback
import inspect
from collections.abc import Callable
from typing import Any, Union, overload

import socketify

from .logger import get_logger, setup_logging
from .request import Request
from .response import Response
from .routing import Router
from .swagger import generate_swagger
from .templating import Templating
from .websockets import WebSocket


class App:
    """
    The main Xyra web application class.

    This class provides the core functionality for building web applications
    with routing, middleware support, WebSocket handling, and automatic API
    documentation generation.

    Attributes:
        _app: The underlying socketify application instance.
        _router: Router instance for managing HTTP routes.

        _middlewares: list of middleware functions.
        templates: Templating engine instance.
        swagger_options: Configuration for Swagger/OpenAPI documentation.
    """

    def __init__(
        self,
        options=None,
        templates_directory: str = "templates",
        swagger_options: dict[str, Any] | None = None,
    ):
        """
        Initialize the Xyra application.

        Args:
            options: Optional configuration for the underlying socketify app.
            templates_directory: Directory path for Jinja2 templates.
            swagger_options: dictionary with Swagger configuration options.
        """
        self._app = socketify.App(options)
        self._router = Router()

        self._middlewares: list[Callable] = []
        self.templates = Templating(templates_directory)
        self.swagger_options = swagger_options
        self._swagger_cache: dict[str, Any] | None = None
        self._swagger_lock = threading.Lock()
        self.log_requests = True  # Will be set in run_server

    def route(
        self, method: str, path: str, handler: Callable | None = None
    ) -> Union[Callable, "App"]:
        """
        Register a route with the specified HTTP method.

        This method can be used as a decorator or as a direct method call.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: URL path pattern (supports parameters like {id}).
            handler: Request handler function (optional if used as decorator).

        Returns:
            If handler is None, returns a decorator function.
            Otherwise, returns self for method chaining.

        Examples:
            # As decorator
            @app.route("GET", "/users")
            def get_users(req, res):
                pass

            # As method call
            app.route("POST", "/users", create_user)
        """
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

    @overload
    def get(self, path: str) -> Callable[[Callable], Callable]: ...

    @overload
    def get(self, path: str, handler: Callable) -> "App": ...

    def get(self, path: str, handler: Callable | None = None) -> Union[Callable, "App"]:
        """Register a GET route."""
        return self.route("GET", path, handler)

    def post(self, path: str, handler: Callable | None = None):
        """Register a POST route."""
        return self.route("POST", path, handler)

    def put(self, path: str, handler: Callable | None = None):
        """Register a PUT route."""
        return self.route("PUT", path, handler)

    def delete(self, path: str, handler: Callable | None = None):
        """Register a DELETE route."""
        return self.route("DELETE", path, handler)

    def patch(self, path: str, handler: Callable | None = None):
        """Register a PATCH route."""
        return self.route("PATCH", path, handler)

    def head(self, path: str, handler: Callable | None = None):
        """Register a HEAD route."""
        return self.route("HEAD", path, handler)

    def options(self, path: str, handler: Callable | None = None):
        """Register an OPTIONS route."""
        return self.route("OPTIONS", path, handler)

    def use(self, middleware: Callable):
        """Add a middleware to the application."""
        self._middlewares.append(middleware)
        return self

    @overload
    def websocket(self, path: str) -> Callable[[Callable], "App"]: ...

    @overload
    def websocket(self, path: str, handlers: dict[str, Callable]) -> "App": ...

    def websocket(
        self, path: str, handlers: dict[str, Callable] | None = None
    ) -> Union[Callable, "App"]:
        """
        Register a WebSocket route.

        This method can be used as a decorator or as a direct method call.

        Args:
            path: WebSocket path pattern.
            handlers: Dictionary with event handlers ('open', 'message', 'close', etc.).

        Returns:
            If handlers is None, returns a decorator function.
            Otherwise, returns self for method chaining.

        Examples:
            # As decorator
            @app.websocket("/ws")
            def handle_websocket(ws):
                ws.send("Connected!")

            # As method call
            app.websocket("/chat", {
                "open": on_open,
                "message": on_message,
                "close": on_close
            })
        """
        if handlers is None:
            # Used as decorator
            def decorator(func):
                self._register_websocket(path, {"open": func})
                return func

            return decorator
        else:
            # Used as method call
            self._register_websocket(path, handlers)
            return self

    def _register_websocket(self, path: str, handlers: dict[str, Callable]):
        """Register WebSocket route with socketify."""
        # Map Xyra event handlers to socketify callbacks
        ws_config = {}

        # Copy compression and other config if provided
        for key in [
            "compression",
            "max_payload_length",
            "idle_timeout",
            "max_backpressure",
            "max_lifetime",
        ]:
            if key in handlers:
                ws_config[key] = handlers[key]

        # Map event handlers
        if "open" in handlers:
            ws_config["open"] = lambda ws: handlers["open"](WebSocket(ws))

        if "message" in handlers:
            ws_config["message"] = lambda ws, message, opcode: handlers["message"](
                WebSocket(ws), message, opcode
            )

        if "close" in handlers:
            ws_config["close"] = lambda ws, code, message: handlers["close"](
                WebSocket(ws), code, message
            )

        if "drain" in handlers:
            ws_config["drain"] = lambda ws: handlers["drain"](WebSocket(ws))

        if "subscription" in handlers:
            ws_config["subscription"] = (
                lambda ws, topic, subscriptions, subscriptions_before: handlers[
                    "subscription"
                ](WebSocket(ws), topic, subscriptions, subscriptions_before)
            )

        # Register with socketify
        self._app.ws(path, ws_config)

    def static_files(self, path: str, directory: str):
        """Serve static files from a directory."""
        return self._app.static(path, directory)

    def _create_final_handler(
        self,
        route_handler: Callable,
        param_names: list[str],
        middlewares: list[Callable],
        parsed_path: str,
    ):
        # Determine if the handler is async
        is_async_handler = asyncio.iscoroutinefunction(route_handler)

        # Pre-compute middleware metadata to avoid runtime reflection (Optimization)
        middleware_chain = []
        for middleware in middlewares:
            handler_to_inspect = middleware
            if not inspect.isfunction(middleware) and hasattr(middleware, "__call__"):
                handler_to_inspect = middleware.__call__

            sig = inspect.signature(handler_to_inspect)
            params = list(sig.parameters.keys())
            is_coroutine = asyncio.iscoroutinefunction(handler_to_inspect)
            wants_call_next = "call_next" in params or "next" in params

            middleware_chain.append({
                "func": middleware,
                "is_coroutine": is_coroutine,
                "wants_call_next": wants_call_next
            })

        async def async_final_handler(res, req):
            start_time = time.time()
            try:
                # Optimized parameter extraction
                params = {
                    param_name: req.get_parameter(i)
                    for i, param_name in enumerate(param_names)
                    if req.get_parameter(i) is not None
                }
                request = Request(req, res, params)
                response = Response(res, self.templates)

                # Middleware Execution Chain
                async def execute_chain(index: int):
                    if index < len(middleware_chain):
                        mw_info = middleware_chain[index]
                        middleware = mw_info["func"]
                        is_coroutine = mw_info["is_coroutine"]
                        wants_call_next = mw_info["wants_call_next"]

                        # Helper to continue to next middleware
                        async def call_next(req_obj=None):
                            # Allow middleware to modify request object if passed
                            # though in this design request is mutable anyway
                            await execute_chain(index + 1)
                            return response

                        if wants_call_next:
                             # Supports onion architecture (FastAPI style or Express style with next)
                            if is_coroutine:
                                await middleware(request, call_next)
                            else:
                                # Wrap sync middleware
                                middleware(request, call_next)
                        else:
                            # Legacy/Simple pattern (req, res) -> None (Linear)
                            if is_coroutine:
                                await middleware(request, response)
                            else:
                                middleware(request, response)

                            # If response not ended, automatically call next
                            if not response._ended:
                                await execute_chain(index + 1)

                    else:
                        # End of middleware chain, call route handler
                        if is_async_handler:
                            await route_handler(request, response)
                        else:
                            route_handler(request, response)

                await execute_chain(0)

                # Log request if enabled (only for non-2xx status codes or slow requests)
                if self.log_requests:
                    duration = int((time.time() - start_time) * 1000)
                    # Only log errors, redirects, or slow requests (>100ms)
                    if response.status_code >= 400 or duration > 100:
                        req_logger = get_logger("xyra")
                        req_logger.info(
                            f"{request.method} {request.url} {response.status_code} {duration}ms"
                        )
            except Exception as e:
                # Log the full traceback for debugging
                req_logger = get_logger("xyra")
                req_logger.error(f"Error in async handler: {str(e)}")
                req_logger.error(traceback.format_exc())

                # Send proper error response
                try:
                    if not response._ended:
                        res.write_status("500")
                        res.end('{"error": "Internal Server Error"}')
                except Exception:
                    # If we can't even send the error response, just close
                    pass
                return

        return async_final_handler

    def _register_routes(self):
        """Register all routes with the underlying socketify app."""
        for route in self._router.routes:
            method = route["method"].lower()
            parsed_path = route["parsed_path"]

            final_handler = self._create_final_handler(
                route["handler"],
                route["param_names"],
                self._middlewares,
                route["parsed_path"],
            )

            # Use the app methods to register routes
            if method == "get":
                self._app.get(parsed_path, final_handler)
            elif method == "post":
                self._app.post(parsed_path, final_handler)
            elif method == "put":
                self._app.put(parsed_path, final_handler)
            elif method == "delete":
                self._app.delete(parsed_path, final_handler)
            elif method == "patch":
                self._app.patch(parsed_path, final_handler)
            elif method == "head":
                self._app.head(parsed_path, final_handler)
            elif method == "options":
                self._app.options(parsed_path, final_handler)

        # Add catch-all handler for unmatched routes (404)
        def not_found_handler(res, req):
            response = Response(res, self.templates)
            response.status(404).json({"error": "Not Found"})

        # Try different patterns for catch-all
        # self._app.any("*", not_found_handler)  # This might not work
        # Use a more specific pattern that catches all paths
        self._app.any("/*", not_found_handler)

    def enable_swagger(self, host: str = "localhost", port: int = 8000):
        """
        Enable Swagger UI documentation for the API.

        This method sets up routes for serving the Swagger UI interface
        and the OpenAPI JSON specification. It automatically generates
        documentation based on the registered routes.

        Args:
            host: Server host for API server URL in documentation.
            port: Server port for API server URL in documentation.
        """
        if not self.swagger_options:
            return

        # Set default paths if not provided
        if "swagger_json_path" not in self.swagger_options:
            self.swagger_options["swagger_json_path"] = "/docs/swagger.json"
        if "swagger_ui_path" not in self.swagger_options:
            self.swagger_options["swagger_ui_path"] = "/docs"

        swagger_json_path = self.swagger_options["swagger_json_path"]
        swagger_ui_path = self.swagger_options["swagger_ui_path"]

        # Ensure swagger_options has required fields for UI
        if "servers" not in self.swagger_options:
            self.swagger_options["servers"] = [
                {"url": f"http://{host}:{port}", "description": "Development server"}
            ]

        def get_swagger_json(req: Request, res: Response):
            if self.swagger_options is None:
                raise ValueError("Swagger options are not configured")
            try:
                if self._swagger_cache is None:
                    with self._swagger_lock:
                        if self._swagger_cache is None:
                            self._swagger_cache = generate_swagger(self, **self.swagger_options)
                res.json(self._swagger_cache)
            except Exception as e:
                res.status(500).json(
                    {"error": "Failed to generate Swagger spec", "message": str(e)}
                )

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

    def run_server(
        self,
        port: int = 8000,
        host: str = "localhost",
        reload: bool = False,
        log_enabled: bool = False,
    ):
        """Start the server."""
        if reload and os.environ.get("XYRA_RELOAD_CHILD") != "1":
            try:
                import subprocess  # nosec B404
                import sys
                import time

                import watchfiles

            except ImportError:
                print("watchfiles not installed, install with: pip install watchfiles")
                return

            print("🔄 Auto-reload enabled. Watching for file changes...")

            current_proc = None

            def start_server():
                nonlocal current_proc
                if current_proc:
                    current_proc.terminate()
                    current_proc.wait()
                env = os.environ.copy()
                env["XYRA_RELOAD_CHILD"] = "1"
                current_proc = subprocess.Popen([sys.executable] + sys.argv, env=env)  # nosec B603

            # Watch for file changes in current directory
            def watch_and_restart():
                for _changes in watchfiles.watch(
                    os.getcwd(), watch_filter=watchfiles.PythonFilter()
                ):
                    print("🔄 Files changed, restarting server...")
                    start_server()

            # Start watcher in background
            import threading

            watcher_thread = threading.Thread(target=watch_and_restart, daemon=True)
            watcher_thread.start()

            # Start initial server
            start_server()

            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                if current_proc:
                    current_proc.terminate()
                    current_proc.wait()

            return

        if self.swagger_options:
            self.enable_swagger(host, port)

        self._register_routes()

        # Always setup logging for startup messages
        setup_logging()
        logger = get_logger("xyra")
        self.log_requests = log_enabled

        logger.info(f"Started server process [{os.getpid()}]")
        logger.info("Waiting for application startup.")
        logger.info("Application startup complete.")
        logger.info(f"Xyra server running on http://{host}:{port}")
        if self.swagger_options:
            swagger_ui_path = self.swagger_options.get("swagger_ui_path", "/docs")
            logger.info(f"API docs available at http://{host}:{port}{swagger_ui_path}")

        self._app.listen(port, lambda config: logger.info(f"Listening on port {port}"))
        self._app.run()

    def listen(
        self,
        port: int = 8000,
        host: str = "localhost",
        reload: bool = False,
        logger: bool = False,
    ):
        """Alias for run_server method with default logger disabled."""
        # Check if port is already in use

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
            sock.close()
        except OSError as e:
            raise RuntimeError(
                f"Port {port} is already in use. Only one instance of Xyra can run per port."
            ) from e
        return self.run_server(port, host, reload, logger)

    @property
    def router(self):
        """Get the router instance."""
        return self._router

    @property
    def middlewares(self):
        """Get the middlewares list."""
        return self._middlewares