import asyncio
import os
import socket
import time
from collections.abc import Callable
from typing import Any, Union, overload

import socketify

from .logger import get_logger, setup_logging
from .request import Request
from .response import Response
from .routing import Router
from .swagger import generate_swagger
from .templating import Templating


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
        if asyncio.iscoroutinefunction(route_handler):

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

                    await route_handler(request, response)

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
                    print(f"Error in async handler: {e}")
                    res.end('{"error": "Internal Server Error"}')
                    return

            return async_final_handler
        else:

            def sync_final_handler(res, req):
                try:
                    start_time = time.time()
                    # Optimized parameter extraction
                    params = {
                        param_name: req.get_parameter(i)
                        for i, param_name in enumerate(param_names)
                        if req.get_parameter(i) is not None
                    }
                    request = Request(req, res, params)
                    response = Response(res, self.templates)

                    route_handler(request, response)

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
                    print(f"Error in sync handler: {e}")
                    res.end('{"error": "Internal Server Error"}')

            return sync_final_handler

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
            assert self.swagger_options is not None
            try:
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
                import subprocess
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
                current_proc = subprocess.Popen([sys.executable] + sys.argv, env=env)

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
