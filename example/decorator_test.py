"""
Decorator Test Example for Xyra Framework

This file tests if the decorator pattern works correctly with the Xyra framework.
"""

from xyra import App, Request, Response

# Create the application
app = App()


# Test decorator pattern
def home(req: Request, res: Response):
    """Home endpoint using method call pattern."""
    res.json({"message": "Hello from method call!", "route": "/"})


app.get("/", home)


def about(req: Request, res: Response):
    """About endpoint using method call pattern."""
    res.json({"message": "About page", "framework": "Xyra", "pattern": "method call"})


app.get("/about", about)


async def test_post(req: Request, res: Response):
    """Test POST endpoint using method call pattern."""
    try:
        data = await req.json()
        res.json({"received": data, "method": "POST", "pattern": "method call"})
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})


app.post("/test", test_post)


def get_user(req: Request, res: Response):
    """Get user by ID using method call pattern."""
    user_id = req.params.get("user_id")
    res.json({"user_id": user_id, "name": f"User {user_id}", "pattern": "method call"})


app.get("/user/{user_id}", get_user)


async def update_user(req: Request, res: Response):
    """Update user using method call pattern."""
    user_id = req.params.get("user_id")
    try:
        data = await req.json()
        res.json(
            {
                "user_id": user_id,
                "updated_data": data,
                "status": "updated",
                "pattern": "method call",
            }
        )
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})


app.put("/user/{user_id}", update_user)


def delete_user(req: Request, res: Response):
    """Delete user using method call pattern."""
    user_id = req.params.get("user_id")
    res.json({"user_id": user_id, "status": "deleted", "pattern": "method call"})


app.delete("/user/{user_id}", delete_user)


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
