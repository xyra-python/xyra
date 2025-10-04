import socketify
from .routing import Router
from .request import Request
from .response import Response
from .websockets import WebSocket
from .templating import Templating

import inspect

class App(socketify.App):
    def __init__(self, options=None, templates_directory="templates"):
        super().__init__(options)
        self.router = Router()
        self.ws_routes = []
        self.middlewares = []
        self.templates = Templating(templates_directory)
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

    def _create_handler_wrapper(self, user_function):
        is_async = inspect.iscoroutinefunction(user_function)
        sig = inspect.signature(user_function)
        num_params = len(sig.parameters)

        async def async_wrapper(res, req, data=None):
            request = Request(req)
            response = Response(res, self.templates)
            if num_params == 3:
                result = await user_function(request, response, data)
            else:
                result = await user_function(request, response)
            return result if result is not None else True

        def sync_wrapper(res, req, data=None):
            request = Request(req)
            response = Response(res, self.templates)
            if num_params == 3:
                result = user_function(request, response, data)
            else:
                result = user_function(request, response)
            return result if result is not None else True

        return async_wrapper if is_async else sync_wrapper

    def _register_routes(self):
        for route in self.router.routes:
            method = route["method"].lower()
            path = route["path"]

            handlers_chain = self.middlewares + [route["handler"]]
            wrapped_handlers = [self._create_handler_wrapper(h) for h in handlers_chain]

            final_handler = socketify.middleware(wrapped_handlers)

            getattr(super(), method)(path, final_handler)

    def _register_ws_routes(self):
        for route in self.ws_routes:
            path = route["path"]
            ws_handler = route["handler"]

            open_handler = None
            if "open" in ws_handler:
                open_handler = self._create_ws_handler(ws_handler["open"])

            message_handler = None
            if "message" in ws_handler:
                message_handler = self._create_ws_message_handler(ws_handler["message"])

            close_handler = None
            if "close" in ws_handler:
                close_handler = self._create_ws_close_handler(ws_handler["close"])

            super().ws(path, {
                "open": open_handler,
                "message": message_handler,
                "close": close_handler
            })

    def listen(self, port, host='0.0.0.0', handler=None):
        self._register_routes()
        self._register_ws_routes()
        return self.run(port=port, host=host, handler=handler)