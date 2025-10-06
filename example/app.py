"""
Simple Xyra Example Application

This is a minimal example showing how to use the Xyra framework
with both decorator and function call patterns.
"""

from xyra import App, Request, Response

# Create the application
app = App(swagger_options={
    "title": "Blog API",
    "version": "1.0.0",
    "description": "API for Blog Application",
})


# Example 1: Using decorator pattern (if working)
# @app.get("/")
# def home(req: Request, res: Response):
#     res.json({"message": "Hello from Xyra!"})


# Example 1: Using function call pattern
def home(req: Request, res: Response):
    """Home endpoint that returns a welcome message."""
    res.json({"message": "Hello from Xyra!", "framework": "Xyra", "version": "0.1.3"})


app.get("/", home)


# Example 2: JSON API endpoint
def api_info(req: Request, res: Response):
    """API information endpoint."""
    res.json(
        {
            "api": "Xyra Simple Example",
            "endpoints": ["GET /", "GET /api/info", "GET /hello/{name}", "POST /echo"],
        }
    )


app.get("/api/info", api_info)


# Example 3: Path parameters
def hello_name(req: Request, res: Response):
    """Greet a specific person by name."""
    name = req.params.get("name", "World")
    res.json({"message": f"Hello, {name}!", "name": name})


app.get("/hello/{name}", hello_name)


# Example 4: POST endpoint with JSON body
async def echo(req: Request, res: Response):
    """Echo back the JSON data sent in the request."""
    try:
        data = await req.json()
        res.json({"echo": data, "received_at": "2024-01-01T00:00:00Z"})
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})


app.post("/echo", echo)


# Example 5: HTML response
def html_page(req: Request, res: Response):
    """Return a simple HTML page."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Xyra Simple Example</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Welcome to Xyra!</h1>
        <p>This is a simple example of the Xyra web framework.</p>

        <h2>Available Endpoints:</h2>
        <div class="endpoint">GET / - Home page (JSON)</div>
        <div class="endpoint">GET /api/info - API information</div>
        <div class="endpoint">GET /hello/{name} - Personalized greeting</div>
        <div class="endpoint">POST /echo - Echo JSON data</div>
        <div class="endpoint">GET /page - This HTML page</div>

        <h2>Try these:</h2>
        <ul>
            <li><a href="/">JSON Home</a></li>
            <li><a href="/api/info">API Info</a></li>
            <li><a href="/hello/Alice">Hello Alice</a></li>
            <li><a href="/page">This HTML Page</a></li>
        </ul>
    </body>
    </html>
    """
    res.html(html)


app.get("/page", html_page)


# Example 6: Error handling
def error_demo(req: Request, res: Response):
    """Demonstrate error handling."""
    error_type = req.query_params.get("type", ["none"])[0]

    if error_type == "400":
        res.status(400)
        res.json({"error": "Bad Request - This is a demo error"})
    elif error_type == "404":
        res.status(404)
        res.json({"error": "Not Found - This is a demo error"})
    elif error_type == "500":
        res.status(500)
        res.json({"error": "Internal Server Error - This is a demo error"})
    else:
        res.json(
            {
                "message": "No error triggered",
                "usage": "Add ?type=400, ?type=404, or ?type=500 to trigger errors",
            }
        )


app.get("/error", error_demo)


if __name__ == "__main__":

    # Start the server
    app.listen(8000, reload=True)
