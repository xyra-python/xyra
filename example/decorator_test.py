"""
Decorator Test Example for Xyra Framework

This file tests if the decorator pattern works correctly with the Xyra framework.
"""

from xyra import App, Request, Response

# Create the application
app = App()


# Test decorator pattern
@app.get("/")
def home(req: Request, res: Response):
    """Home endpoint using decorator pattern."""
    res.json({"message": "Hello from decorator!", "route": "/"})


@app.get("/about")
def about(req: Request, res: Response):
    """About endpoint using decorator pattern."""
    res.json({"message": "About page", "framework": "Xyra", "pattern": "decorator"})


@app.post("/test")
async def test_post(req: Request, res: Response):
    """Test POST endpoint using decorator pattern."""
    try:
        data = await req.json()
        res.json({"received": data, "method": "POST", "pattern": "decorator"})
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})


@app.get("/user/{user_id}")
def get_user(req: Request, res: Response):
    """Get user by ID using decorator pattern."""
    user_id = req.params.get("user_id")
    res.json({"user_id": user_id, "name": f"User {user_id}", "pattern": "decorator"})


@app.put("/user/{user_id}")
async def update_user(req: Request, res: Response):
    """Update user using decorator pattern."""
    user_id = req.params.get("user_id")
    try:
        data = await req.json()
        res.json(
            {
                "user_id": user_id,
                "updated_data": data,
                "status": "updated",
                "pattern": "decorator",
            }
        )
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})


@app.delete("/user/{user_id}")
def delete_user(req: Request, res: Response):
    """Delete user using decorator pattern."""
    user_id = req.params.get("user_id")
    res.json({"user_id": user_id, "status": "deleted", "pattern": "decorator"})


if __name__ == "__main__":
    print("🧪 Testing Xyra Decorator Pattern")
    print(f"📊 Routes registered: {len(app.router.routes)}")

    for route in app.router.routes:
        print(f"   {route['method']} {route['path']}")

    print()
    print("🚀 Starting server on http://localhost:8000")
    print("🌐 Test endpoints:")
    print("  • GET    /")
    print("  • GET    /about")
    print("  • POST   /test")
    print("  • GET    /user/{user_id}")
    print("  • PUT    /user/{user_id}")
    print("  • DELETE /user/{user_id}")
    print()

    app.listen(8000)
