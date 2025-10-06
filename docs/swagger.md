# API Documentation with Swagger

Xyra integrates with Swagger (OpenAPI) to automatically generate API documentation. This documentation allows developers and API users to understand available endpoints, parameters, and responses.

## Enable Swagger

To enable Swagger in a Xyra application, provide the `swagger_options` option during app initialization:

```python
from xyra import App

app = App(swagger_options={
    "title": "My API",
    "version": "1.0.0",
    "description": "API documentation for My App"
})
```

## Access Documentation

Once enabled, Swagger documentation will be available at:

- **Swagger UI**: `http://localhost:8000/docs` (or custom path)
- **JSON Spec**: `http://localhost:8000/docs/swagger.json` (or custom path)

## Swagger Configuration

You can customize various aspects of the API documentation:

```python
app = App(swagger_options={
    "title": "Blog API",
    "version": "1.0.0",
    "description": "API for Blog Application",
    "contact": {
        "name": "Developer Team",
        "email": "dev@example.com",
        "url": "https://example.com/contact"
    },
    "license_info": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    "servers": [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.example.com",
            "description": "Production server"
        }
    ],
    "swagger_ui_path": "/api-docs",
    "swagger_json_path": "/api-docs/swagger.json"
})
```

### Configuration Options

- `title`: API title
- `version`: API version
- `description`: API description
- `contact`: Contact information (name, email, url)
- `license_info`: License information (name, url)
- `servers`: List of servers with URL and description
- `swagger_ui_path`: Path for Swagger UI (default: "/docs")
- `swagger_json_path`: Path for JSON spec (default: "/docs/swagger.json")

## Automatic Documentation

Xyra automatically generates documentation from:

- Route definitions
- Parameter types (from docstrings)
- Request/response schemas
- HTTP methods

### Example Route with Documentation

```python
@app.get("/users/{user_id}")
def get_user(req: Request, res: Response):
    """
    Get user by ID.

    Args:
        user_id (str): The ID of the user to retrieve.

    Returns:
        dict: User information including id, name, and email.
    """
    user_id = req.params.get("user_id")
    # Logic to get user
    user = {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
    res.json(user)

@app.post("/users")
async def create_user(req: Request, res: Response):
    """
    Create a new user.

    Body:
        name (str): User's full name
        email (str): User's email address

    Returns:
        dict: Created user information.
    """
    user_data = await req.json()
    # Logic to create user
    user_data["id"] = "123"  # Generated ID
    res.status(201)
    res.json(user_data)
```

## Custom Response Schemas

For better control over response schemas, you can use type hints and docstrings:

```python
from typing import List, Dict, Any

@app.get("/users")
def list_users(req: Request, res: Response) -> List[Dict[str, Any]]:
    """
    Get list of users.

    Query Parameters:
        page (int): Page number (default: 1)
        limit (int): Items per page (default: 10)

    Returns:
        List[Dict]: List of user objects.
    """
    users = [
        {"id": "1", "name": "Alice", "email": "alice@example.com"},
        {"id": "2", "name": "Bob", "email": "bob@example.com"}
    ]
    res.json(users)
```

## Security Schemes

You can add authentication information to the documentation:

```python
app = App(swagger_options={
    "title": "Secure API",
    "version": "1.0.0",
    "description": "API with authentication",
    "security": [
        {"bearerAuth": []}
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
})
```

## Complete Example

Here is a complete example application with Swagger:

```python
from xyra import App, Request, Response
from typing import List, Dict, Any

app = App(
    templates_directory="templates",
    swagger_options={
        "title": "Blog API",
        "version": "1.0.0",
        "description": "API for Blog Application",
        "contact": {
            "name": "Blog Team",
            "email": "api@blog.com"
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Development server"}
        ]
    }
)

@app.get("/posts")
def get_posts(req: Request, res: Response) -> List[Dict[str, Any]]:
    """
    Get all blog posts.

    Query Parameters:
        page (int): Page number
        limit (int): Posts per page

    Returns:
        List[Dict]: List of blog posts.
    """
    posts = [
        {"id": 1, "title": "First Post", "content": "Content here", "author": "Admin"},
        {"id": 2, "title": "Second Post", "content": "More content", "author": "Admin"}
    ]
    res.json(posts)

@app.get("/posts/{post_id}")
def get_post(req: Request, res: Response) -> Dict[str, Any]:
    """
    Get a specific blog post.

    Path Parameters:
        post_id (int): The ID of the post to retrieve.

    Returns:
        Dict: Blog post information.
    """
    post_id = req.params.get("post_id")
    post = {"id": post_id, "title": f"Post {post_id}", "content": "Content", "author": "Admin"}
    res.json(post)

@app.post("/posts")
async def create_post(req: Request, res: Response) -> Dict[str, Any]:
    """
    Create a new blog post.

    Body:
        title (str): Post title
        content (str): Post content
        author (str): Post author

    Returns:
        Dict: Created post information.
    """
    post_data = await req.json()
    post_data["id"] = 123  # Generated ID
    res.status(201)
    res.json(post_data)

@app.put("/posts/{post_id}")
async def update_post(req: Request, res: Response) -> Dict[str, Any]:
    """
    Update an existing blog post.

    Path Parameters:
        post_id (int): The ID of the post to update.

    Body:
        title (str): Updated post title
        content (str): Updated post content

    Returns:
        Dict: Updated post information.
    """
    post_id = req.params.get("post_id")
    update_data = await req.json()
    post = {"id": post_id, **update_data}
    res.json(post)

@app.delete("/posts/{post_id}")
def delete_post(req: Request, res: Response):
    """
    Delete a blog post.

    Path Parameters:
        post_id (int): The ID of the post to delete.

    Returns:
        Dict: Deletion confirmation.
    """
    post_id = req.params.get("post_id")
    res.json({"deleted": True, "post_id": post_id})

if __name__ == "__main__":
    print("🚀 Blog API running on http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    app.listen(8000)
```

## Testing API via Swagger UI

Swagger UI provides an interface for testing the API directly from the browser:

1. Open `http://localhost:8000/docs`
2. Click on the endpoint you want to test
3. Click "Try it out"
4. Fill in parameters and body if required
5. Click "Execute"
6. View the response at the bottom

## Swagger Tips

1. **Clear Docstrings**: Write descriptive docstrings for each endpoint
2. **Type Hints**: Use Python type hints for more accurate schemas
3. **Response Codes**: Document various response codes (200, 201, 400, 404, etc.)
4. **Examples**: Provide request/response examples in docstrings
5. **Grouping**: Group related endpoints with tags
6. **Authentication**: Document authentication requirements
7. **Versioning**: Update the API version when there are breaking changes

---

[Back to Table of Contents](../README.md)