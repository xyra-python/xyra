import asyncio
import inspect
import json
import os
import socket
import threading
import time
import traceback
from collections.abc import Callable
from typing import Any, Union, overload

from . import libxyra
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
        _app: The underlying native application instance.
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
            options: Optional configuration for the underlying native app.
            templates_directory: Directory path for Jinja2 templates.
            swagger_options: dictionary with Swagger configuration options.
        """
        self._app = libxyra.App()
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
        """Register WebSocket route with native App."""
        # Map Xyra event handlers to native callbacks
        ws_config = {}

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

        # Register with native App
        self._app.ws(path, ws_config)

    def static_files(self, path: str, directory: str):
        """Serve static files from a directory."""
        if not path.endswith("/"):
            path += "/"
        if not path.startswith("/"):
            path = "/" + path

        import os

        async def static_handler(req: Request, res: Response):
            file_path = req.params.get("filename")
            if not file_path:
                res.status(404).text("Not Found")
                return

            # SECURITY: Prevent Path Traversal
            try:
                # Resolve absolute paths and resolve symlinks to prevent traversal
                abs_directory = os.path.realpath(directory)
                abs_path = os.path.realpath(os.path.join(abs_directory, file_path))

                # Verify the resolved path is within the static directory
                if os.path.commonpath([abs_directory, abs_path]) != abs_directory:
                    res.status(403).text("Forbidden")
                    return
            except Exception:
                res.status(400).text("Bad Request")
                return

            full_path = abs_path
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    content = f.read()
                # Simple extension to content-type mapping
                ext = os.path.splitext(full_path)[1].lower()
                content_types = {
                    ".html": "text/html",
                    ".js": "application/javascript",
                    ".css": "text/css",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".gif": "image/gif",
                    ".svg": "image/svg+xml",
                }
                res.header(
                    "Content-Type", content_types.get(ext, "application/octet-stream")
                )
                res.send(content)
            else:
                res.status(404).text("Not Found")

        self.get(path + "{filename}", static_handler)

    def _build_middleware_stack(
        self,
        middleware_chain: list[dict[str, Any]],
        route_handler: Callable,
        is_async_handler: bool,
    ) -> Callable:
        # Base handler
        async def run_route_handler(req, res):
            if is_async_handler:
                await route_handler(req, res)
            else:
                route_handler(req, res)
            return res

        next_call = run_route_handler

        for mw_info in reversed(middleware_chain):
            middleware = mw_info["func"]
            is_coroutine = mw_info["is_coroutine"]
            wants_call_next = mw_info["wants_call_next"]

            # Capture for closure
            current_next = next_call

            if wants_call_next:
                if is_coroutine:

                    async def layer(req, res, _mw=middleware, _next=current_next):
                        async def call_next(req_obj=None):
                            return await _next(req, res)

                        await _mw(req, call_next)
                        return res

                else:

                    async def layer(req, res, _mw=middleware, _next=current_next):
                        async def call_next(req_obj=None):
                            return await _next(req, res)

                        _mw(req, call_next)
                        return res

            else:
                # Legacy
                if is_coroutine:

                    async def layer(req, res, _mw=middleware, _next=current_next):
                        await _mw(req, res)
                        if not res._ended:
                            await _next(req, res)
                        return res

                else:

                    async def layer(req, res, _mw=middleware, _next=current_next):
                        _mw(req, res)
                        if not res._ended:
                            await _next(req, res)
                        return res

            next_call = layer

        return next_call

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
            # FIX RUFF B004: Use callable() instead of hasattr(..., "__call__")
            if not inspect.isfunction(middleware) and callable(middleware):
                handler_to_inspect = middleware.__call__

            sig = inspect.signature(handler_to_inspect)
            params = list(sig.parameters.keys())
            is_coroutine = asyncio.iscoroutinefunction(handler_to_inspect)
            wants_call_next = "call_next" in params or "next" in params

            middleware_chain.append(
                {
                    "func": middleware,
                    "is_coroutine": is_coroutine,
                    "wants_call_next": wants_call_next,
                }
            )

        # Build the middleware stack once
        middleware_stack_entry = self._build_middleware_stack(
            middleware_chain, route_handler, is_async_handler
        )

        async def async_final_handler(res, req):
            start_time = time.time()
            try:
                # Optimized parameter extraction
                params = {}
                for i, param_name in enumerate(param_names):
                    val = req.get_parameter(i)
                    if val != "":
                        params[param_name] = val

                request = Request(req, res, params)
                response = Response(res, self.templates)

                # Execute middleware stack
                await middleware_stack_entry(request, response)

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
                    # FIX BANDIT B110: Avoid silent pass. Log the failure to debug.
                    # If we can't even send the error response, just close.
                    req_logger.debug(
                        "Failed to send 500 error response (connection likely closed)"
                    )
                return

        return async_final_handler

    def _register_routes(self):
        """Register all routes with the underlying native app."""
        if not hasattr(self, "_loop"):
            self._loop = asyncio.new_event_loop()

            def run_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()

            import threading

            threading.Thread(target=run_loop, args=(self._loop,), daemon=True).start()

        def wrap_async(handler):
            def sync_handler(res, req):
                asyncio.run_coroutine_threadsafe(handler(res, req), self._loop)

            return sync_handler

        for route in self._router.routes:
            method = route["method"].lower()
            if method == "delete":
                method = "del"
            parsed_path = route["parsed_path"]

            final_handler = self._create_final_handler(
                route["handler"],
                route["param_names"],
                self._middlewares,
                route["parsed_path"],
            )

            # Use the app methods to register routes
            if hasattr(self._app, method):
                getattr(self._app, method)(parsed_path, wrap_async(final_handler))

        # Add catch-all handler for unmatched routes (404)
        async def not_found_handler(res, req):
            response = Response(res, self.templates)
            response.status(404).json({"error": "Not Found"})

        self._app.any("/*", wrap_async(not_found_handler))

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
                            self._swagger_cache = generate_swagger(
                                self, **self.swagger_options
                            )
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
                    url: {json.dumps(swagger_json_path)},
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
