import socketify
from .routing import Router
from .request import Request
from .response import Response
from .websockets import WebSocket
from .templating import Templating
from .swagger import generate_swagger
import inspect

class App(socketify.App):
    def __init__(self, options=None, templates_directory="templates", swagger_options=None):
        super().__init__(options)
        self.router = Router()
        self.ws_routes = []
        self.middlewares = []
        self.templates = Templating(templates_directory)
        self.swagger_options = swagger_options
        self.get = self.router.get
        self.post = self.router.post
        self.put = self.router.put
        self.delete = self.router.delete
        self.patch = self.router.patch
        self.head = self.router.head
        self.options = self.router.options

    def use(self, middleware):
        self.middlewares.append(middleware)

    def static(self, path, directory):
        return super().static(path, directory)

    def ws(self, path, handler):
        self.ws_routes.append({"path": path, "handler": handler})

    def _create_ws_handler(self, handler):
        def ws_handler(ws):
            websocket = WebSocket(ws)
            handler(websocket)
        return ws_handler

    def _create_ws_message_handler(self, handler):
        def ws_message_handler(ws, message, opcode):
            websocket = WebSocket(ws)
            handler(websocket, message, opcode)
        return ws_message_handler

    def _create_ws_close_handler(self, handler):
        def ws_close_handler(ws, code, message):
            websocket = WebSocket(ws)
            handler(websocket, code, message)
        return ws_close_handler

    def _create_final_handler(self, route_handler, middlewares):
        async def final_handler(res, req, data=None):
            request = Request(req, params=data)
            response = Response(res, self.templates)

            index = 0

            async def next_handler():
                nonlocal index
                if index < len(middlewares):
                    middleware = middlewares[index]
                    index += 1

                    if inspect.iscoroutinefunction(middleware):
                        await middleware(request, response, next_handler)
                    else:
                        middleware(request, response, next_handler)
                else:
                    if inspect.iscoroutinefunction(route_handler):
                        await route_handler(request, response)
                    else:
                        route_handler(request, response)

            await next_handler()

        return final_handler

    def _register_routes(self):
        for route in self.router.routes:
            method = route["method"].lower()
            path = route["path"]

            final_handler = self._create_final_handler(route['handler'], self.middlewares)
            getattr(super(), method)(path, final_handler)

    def _register_ws_routes(self):
        for route in self.ws_routes:
            path = route["path"]
            ws_handler = route["handler"]
            open_handler = ws_handler.get("open")
            if open_handler:
                open_handler = self._create_ws_handler(open_handler)

            message_handler = ws_handler.get("message")
            if message_handler:
                message_handler = self._create_ws_message_handler(message_handler)

            close_handler = ws_handler.get("close")
            if close_handler:
                close_handler = self._create_ws_close_handler(close_handler)

            super().ws(path, {
                "open": open_handler,
                "message": message_handler,
                "close": close_handler
            })

    def enable_swagger(self):
        if not self.swagger_options:
            return

        swagger_json_path = self.swagger_options.get("swagger_json_path", "/docs/swagger.json")
        swagger_ui_path = self.swagger_options.get("swagger_ui_path", "/docs")

        def get_swagger_json(req, res):
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

        def get_swagger_ui(req, res):
            res.html(swagger_ui_html)

        self.get(swagger_ui_path, get_swagger_ui)

    def listen(self, port, host='0.0.0.0', handler=None):
        if self.swagger_options:
            self.enable_swagger()
        self._register_routes()
        self._register_ws_routes()
        return self.run(port=port, host=host, handler=handler)