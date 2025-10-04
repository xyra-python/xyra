import asyncio
import websockets
from urllib.parse import urlparse

class App:
    def __init__(self):
        self.routes = {}
        self.middlewares = []
        self.ws_routes = {}

    def use(self, middleware):
        self.middlewares.append(middleware)

    def get(self, path, handler):
        self.routes[('GET', path)] = handler

    def post(self, path, handler):
        self.routes[('POST', path)] = handler

    def ws(self, path, handler):
        self.ws_routes[path] = handler

    async def _apply_middlewares(self, req, res):
        for middleware in self.middlewares:
            await middleware(req, res)

    async def _handle_http(self, path, method, request):
        key = (method, path)
        if key in self.routes:
            handler = self.routes[key]
            # Mock req, res for simplicity
            req = {'method': method, 'path': path}
            res = {'status': 200, 'body': ''}
            await self._apply_middlewares(req, res)
            await handler(req, res)
            return res
        return {'status': 404, 'body': 'Not Found'}

    async def _handle_ws(self, websocket, path):
        if path in self.ws_routes:
            handler = self.ws_routes[path]
            # Apply middlewares
            for middleware in self.middlewares:
                await middleware(websocket, path)
            await handler(websocket)
        else:
            await websocket.close()

    async def _http_handler(self, request):
        parsed = urlparse(request.url)
        path = parsed.path
        method = request.method
        return await self._handle_http(path, method, request)

    def listen(self, port, host='localhost'):
        async def ws_handler(websocket):
            path = websocket.path
            await self._handle_ws(websocket, path)

        start_server = websockets.serve(ws_handler, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()