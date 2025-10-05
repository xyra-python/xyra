class CorsMiddleware:
    def __init__(self, allowed_origins=None, allowed_methods=None, allowed_headers=None):
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["*"]
        self.allowed_headers = allowed_headers or ["*"]

    async def __call__(self, request, response, next_handler):
        origin = request.headers.get("origin")
        if origin:
            response.set_header("Access-Control-Allow-Origin", ", ".join(self.allowed_origins))
            response.set_header("Access-Control-Allow-Methods", ", ".join(self.allowed_methods))
            response.set_header("Access-Control-Allow-Headers", ", ".join(self.allowed_headers))

        if request.method == "OPTIONS":
            response.status_code = 204
            response.send("")
            return

        await next_handler()