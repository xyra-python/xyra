---
layout: default
---

# Routing in Xyra

Routing is how Xyra handles HTTP requests and directs them to the appropriate handler. Xyra supports various HTTP methods and flexible routing with parameters and query strings.

## HTTP Methods

Xyra supports all standard HTTP methods:

```python
from xyra import App, Request, Response

app = App()

@app.get("/users")
def get_users(req: Request, res: Response):
    res.json({"users": []})

@app.post("/users")
def create_user(req: Request, res: Response):
    data = await req.json()
    res.json({"created": True, "user": data})

@app.put("/users/{user_id}")
def update_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    res.json({"updated": user_id})

@app.delete("/users/{user_id}")
def delete_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    res.json({"deleted": user_id})

@app.patch("/users/{user_id}")
def patch_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    res.json({"patched": user_id})

@app.head("/users")
def head_users(req: Request, res: Response):
    res.status(200)

@app.options("/users")
def options_users(req: Request, res: Response):
    res.set_header("Allow", "GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS")
    res.status(200)
```

## Route Parameters

Route parameters allow you to capture values from the URL path.

```python
@app.get("/users/{user_id}")
def get_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    res.json({"user_id": user_id, "name": f"User {user_id}"})

@app.get("/posts/{category}/{post_id}")
def get_post(req: Request, res: Response):
    category = req.params.get("category")
    post_id = req.params.get("post_id")
    res.json({"category": category, "post_id": post_id})
```

Parameters are accessed through `req.params`, which is a dictionary.

## Query Parameters

Query parameters are used for optional data or filtering.

```python
@app.get("/search")
def search(req: Request, res: Response):
    query = req.query_params.get("q", [""])[0]
    limit = int(req.query_params.get("limit", ["10"])[0])
    res.json({"query": query, "limit": limit, "results": []})

@app.get("/users")
def get_users_filtered(req: Request, res: Response):
    page = int(req.query_params.get("page", ["1"])[0])
    per_page = int(req.query_params.get("per_page", ["10"])[0])
    sort_by = req.query_params.get("sort_by", ["name"])[0]
    
    # Logic for filtering, pagination, sorting
    res.json({
        "page": page,
        "per_page": per_page,
        "sort_by": sort_by,
        "users": []
    })
```

Query parameters are accessed through `req.query_params`, which is a dictionary with lists as values (for multiple values).

## Routes with Generic Methods

You can also use the `route()` method to register a route with a specific method:

```python
app.route("GET", "/custom", custom_handler)
app.route("POST", "/custom", custom_post_handler)
```

## Wildcard Routes

Xyra supports wildcards with `*`:

```python
@app.get("/files/*")
def serve_file(req: Request, res: Response):
    path = req.url.split("/files/", 1)[1]
    # Serve file logic
    res.text(f"Serving file: {path}")
```

## Middleware on Routes

Middleware can be applied to specific routes (this feature may require special implementation).

## Routing Tips

1. **Use descriptive parameters**: `/users/{user_id}` is better than `/u/{id}`

2. **Validate input**: Always validate parameters and query strings

3. **Use the appropriate HTTP method**: GET for retrieve, POST for create, PUT for update, DELETE for delete

4. **Handle errors properly**: Return appropriate status codes (404 for not found, 400 for bad request)

## Complete Example

```python
from xyra import App, Request, Response

app = App()

# Simple route
@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Welcome to Xyra API"})

# Route with parameter
@app.get("/users/{user_id}")
def get_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    if not user_id:
        res.status(400)
        res.json({"error": "User ID required"})
        return
    
    # Logic to get user
    res.json({"user_id": user_id, "name": f"User {user_id}"})

# Route with query parameters
@app.get("/users")
def list_users(req: Request, res: Response):
    page = int(req.query_params.get("page", ["1"])[0])
    limit = int(req.query_params.get("limit", ["10"])[0])
    
    # Logic for pagination
    users = [
        {"id": i, "name": f"User {i}"}
        for i in range((page-1)*limit + 1, page*limit + 1)
    ]
    
    res.json({
        "page": page,
        "limit": limit,
        "users": users
    })

# POST route with body
@app.post("/users")
async def create_user(req: Request, res: Response):
    try:
        user_data = await req.json()
        # Validate data
        if not user_data.get("name"):
            res.status(400)
            res.json({"error": "Name is required"})
            return
        
        # Logic to create user
        res.status(201)
        res.json({"created": True, "user": user_data})
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})

if __name__ == "__main__":
    app.listen(8000)
```

---

[Back to Table of Contents](../README.md)