# Simple API Example with Xyra Framework

This example demonstrates a basic REST API using the Xyra framework in Python.

## Features Demonstrated

- Basic routing (GET, POST, PUT, DELETE)
- JSON request/response handling
- Route parameters
- Error handling
- CORS middleware
- Rate limiting middleware

## Code

```python
from xyra import App, Request, Response
from xyra.middleware import cors, rate_limiter

# Create app instance
app = App()

# Add middleware
app.use(cors(allowed_origins=["http://localhost:3000"]))
app.use(rate_limiter(requests=100, window=60))

# In-memory data store
users = [
    {"id": 1, "name": "John Doe", "email": "john@example.com"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
]
next_id = 3

# GET /users - Get all users
@app.get("/users")
def get_users(req: Request, res: Response):
    res.json(users)

# GET /users/{id} - Get user by ID
@app.get("/users/{id}")
def get_user(req: Request, res: Response):
    user_id = int(req.params.get("id"))
    user = next((u for u in users if u["id"] == user_id), None)

    if user:
        res.json(user)
    else:
        res.status(404).json({"error": "User not found"})

# POST /users - Create new user
@app.post("/users")
async def create_user(req: Request, res: Response):
    global next_id

    try:
        data = await req.json()

        # Validate required fields
        if not data or "name" not in data or "email" not in data:
            res.status(400).json({"error": "Name and email are required"})
            return

        # Check if email already exists
        if any(u["email"] == data["email"] for u in users):
            res.status(409).json({"error": "Email already exists"})
            return

        # Create new user
        new_user = {
            "id": next_id,
            "name": data["name"],
            "email": data["email"]
        }
        users.append(new_user)
        next_id += 1

        res.status(201).json(new_user)

    except Exception as e:
        res.status(400).json({"error": "Invalid JSON data"})

# PUT /users/{id} - Update user
@app.put("/users/{id}")
async def update_user(req: Request, res: Response):
    user_id = int(req.params.get("id"))

    # Find user
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        res.status(404).json({"error": "User not found"})
        return

    try:
        data = await req.json()

        # Update fields
        if "name" in data:
            user["name"] = data["name"]
        if "email" in data:
            # Check if email is taken by another user
            if any(u["email"] == data["email"] and u["id"] != user_id for u in users):
                res.status(409).json({"error": "Email already exists"})
                return
            user["email"] = data["email"]

        res.json(user)

    except Exception as e:
        res.status(400).json({"error": "Invalid JSON data"})

# DELETE /users/{id} - Delete user
@app.delete("/users/{id}")
def delete_user(req: Request, res: Response):
    user_id = int(req.params.get("id"))

    # Find and remove user
    for i, user in enumerate(users):
        if user["id"] == user_id:
            deleted_user = users.pop(i)
            res.json({"message": "User deleted", "user": deleted_user})
            return

    res.status(404).json({"error": "User not found"})

# GET /health - Health check endpoint
@app.get("/health")
def health_check(req: Request, res: Response):
    res.json({
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    })

if __name__ == "__main__":
    print("🚀 Starting Xyra API server...")
    print("📡 Server running on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    app.listen(8000, logger=True)
```

## Running the Example

1. Save the code to a file named `api.py`
2. Install Xyra: `pip install xyra`
3. Run the server: `python api.py`

## API Endpoints

- `GET /users` - Get all users
- `GET /users/{id}` - Get user by ID
- `POST /users` - Create new user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user
- `GET /health` - Health check

## Example Requests

### Get all users
```bash
curl http://localhost:8000/users
```

### Create a new user
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Johnson", "email": "bob@example.com"}'
```

### Get user by ID
```bash
curl http://localhost:8000/users/1
```

### Update user
```bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith"}'
```

### Delete user
```bash
curl -X DELETE http://localhost:8000/users/1
```

## Middleware Used

- **CORS**: Allows cross-origin requests from `http://localhost:3000`
- **Rate Limiter**: Limits to 100 requests per minute per IP address

This example shows how to build a complete REST API with proper error handling, validation, and middleware integration using the Xyra framework.