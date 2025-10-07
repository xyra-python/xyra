#!/usr/bin/env python3
"""
Benchmark server for Xyra framework performance testing.
"""

import os
import sys
import time

# Add parent directory to path to import xyra
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xyra import App, Request, Response


def create_simple_app() -> App:
    """Create a simple app for benchmarking."""
    app = App()

    # Simple hello world
    def hello(req: Request, res: Response):
        res.json({"message": "Hello, World!", "timestamp": time.time()})

    app.get("/", hello)

    # JSON response
    def json_response(req: Request, res: Response):
        res.json(
            {
                "id": 123,
                "name": "benchmark",
                "data": [1, 2, 3, 4, 5],
                "nested": {"key": "value"},
            }
        )

    app.get("/json", json_response)

    # JSON POST
    async def json_post(req: Request, res: Response):
        data = await req.json()
        res.json({"received": data, "processed": True})

    app.post("/json", json_post)

    # Headers test
    def headers_test(req: Request, res: Response):
        # Access headers to test header parsing performance
        user_agent = req.get_header("User-Agent")
        accept = req.get_header("Accept")
        res.json(
            {
                "user_agent": user_agent,
                "accept": accept,
                "all_headers_count": len(req.headers),
            }
        )

    app.get("/headers", headers_test)

    # Query params test
    def query_test(req: Request, res: Response):
        # Access query params to test query parsing performance
        page = req.query_params.get("page", ["1"])[0]
        limit = req.query_params.get("limit", ["10"])[0]
        search = req.query_params.get("search", [""])[0]
        res.json(
            {
                "page": int(page),
                "limit": int(limit),
                "search": search,
                "query_count": len(req.query_params),
            }
        )

    app.get("/query", query_test)

    # Route parameters test
    def user_detail(req: Request, res: Response):
        user_id = req.params.get("user_id")
        res.json(
            {
                "user_id": user_id,
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com",
            }
        )

    app.get("/user/{user_id}", user_detail)

    return app


def create_app_with_middleware() -> App:
    """Create app with middleware for testing middleware performance."""
    app = App()

    def logging_middleware(req: Request, res: Response):
        # Simulate logging middleware
        pass

    def auth_middleware(req: Request, res: Response):
        # Simulate auth check
        auth = req.get_header("Authorization")
        if not auth:
            res.status(401)
            res.json({"error": "Unauthorized"})
            return

    def cors_middleware(req: Request, res: Response):
        res.header("Access-Control-Allow-Origin", "*")
        res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")

    # Add middleware
    app.use(logging_middleware)
    app.use(cors_middleware)
    app.use(auth_middleware)

    @app.get("/middleware")
    def middleware_test(req: Request, res: Response):
        res.json({"middleware": "passed", "auth": "checked"})

    return app


def create_app_with_templates() -> App:
    """Create app with templating for testing template performance."""
    import tempfile
    import os

    # Create temporary directory for templates to avoid cluttering benchmark folder
    temp_dir = tempfile.mkdtemp(prefix="xyra_templates_")
    templates_dir = os.path.join(temp_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    # Copy test template to temp directory
    import shutil

    if os.path.exists("benchmark/templates/test.html"):
        shutil.copy(
            "benchmark/templates/test.html", os.path.join(templates_dir, "test.html")
        )

    app = App(templates_directory=templates_dir)

    @app.get("/template")
    def template_test(req: Request, res: Response):
        res.render("test.html", title="Benchmark", items=[1, 2, 3, 4, 5])

    return app


def main():
    """Main benchmark server."""
    import argparse

    parser = argparse.ArgumentParser(description="Xyra Benchmark Server")
    parser.add_argument(
        "--type",
        choices=["simple", "middleware", "template"],
        default="simple",
        help="Type of benchmark server",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    if args.type == "simple":
        app = create_simple_app()
        print("🚀 Starting simple benchmark server")
    elif args.type == "middleware":
        app = create_app_with_middleware()
        print("🚀 Starting middleware benchmark server")
    elif args.type == "template":
        app = create_app_with_templates()
        print("🚀 Starting template benchmark server")
    else:
        print("❌ Invalid server type")
        return

    print(f"📍 Listening on http://{args.host}:{args.port}")
    print("🎯 Ready for benchmarking")

    app.listen(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
