# Middleware in Xyra

Middleware are functions that are executed before the main route handler. Middleware allows you to add common logic such as authentication, logging, CORS handling, or input validation to routes.

## How Middleware Works

Middleware in Xyra are functions that receive `req` (Request) and `res` (Response) parameters. They are executed in the order they are registered before the route handler.

```python
def my_middleware(req: Request, res: Response):
    # Middleware logic
    print(f"Request to: {req.url}")
    # Continue to next middleware/route handler
    # (handled internally by the framework)
```

## Adding Middleware

Use the `use()` method on the App object to add middleware:

```python
from xyra import App, Request, Response

app = App()

# Logging middleware
def logging_middleware(req: Request, res: Response):
    print(f"{req.method} {req.url} - {time.time()}")

# CORS middleware
def cors_middleware(req: Request, res: Response):
    res.set_header("Access-Control-Allow-Origin", "*")
    res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

# Add middleware
app.use(logging_middleware)
app.use(cors_middleware)
```

## Execution Order

Middleware are executed in the order they are added:

```python
app.use(middleware1)  # Executed first
app.use(middleware2)  # Executed second
app.use(middleware3)  # Executed third

@app.get("/test")
def handler(req, res):
    # Executed last
    res.json({"message": "OK"})
```

## Middleware with Error Handling

Middleware can stop request processing by sending a response:

```python
def auth_middleware(req: Request, res: Response):
    token = req.get_header("Authorization")
    if not token:
        res.status(401)
        res.json({"error": "Unauthorized"})
        return  # Stop execution

    # Verify token...
    if not is_valid_token(token):
        res.status(403)
        res.json({"error": "Invalid token"})
        return

    # Continue to next handler
```

## Middleware untuk Validasi

```python
def json_validation_middleware(req: Request, res: Response):
    if req.method in ["POST", "PUT", "PATCH"]:
        if not req.get_header("Content-Type") == "application/json":
            res.status(400)
            res.json({"error": "Content-Type must be application/json"})
            return
```

## Middleware untuk Rate Limiting

```python
import time
from collections import defaultdict

# Simple in-memory rate limiting (untuk demo)
request_counts = defaultdict(list)

def rate_limit_middleware(req: Request, res: Response):
    client_ip = req.get_header("X-Forwarded-For") or "unknown"
    now = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < 60]
    
    # Check rate limit (10 requests per minute)
    if len(request_counts[client_ip]) >= 10:
        res.status(429)
        res.json({"error": "Too many requests"})
        return
    
    # Add current request
    request_counts[client_ip].append(now)
```

## Middleware untuk Static Files

```python
import os

def static_files_middleware(req: Request, res: Response):
    if req.url.startswith("/static/"):
        file_path = req.url[8:]  # Remove "/static/"
        full_path = os.path.join("static", file_path)
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            # Serve file (simplified)
            with open(full_path, "rb") as f:
                content = f.read()
            res.set_header("Content-Type", "application/octet-stream")
            res.status(200)
            # In real implementation, you'd stream the file
            return
        
        res.status(404)
        res.json({"error": "File not found"})
```

## Contoh Lengkap

Berikut adalah contoh aplikasi dengan berbagai middleware:

```python
from xyra import App, Request, Response
import time
from collections import defaultdict

app = App()

# Middleware 1: Logging
def logging_middleware(req: Request, res: Response):
    start_time = time.time()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {req.method} {req.url}")
    
    # Note: In real implementation, you'd modify response after handler
    # This is simplified for demonstration

# Middleware 2: CORS
def cors_middleware(req: Request, res: Response):
    res.set_header("Access-Control-Allow-Origin", "*")
    res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

# Middleware 3: Authentication
def auth_middleware(req: Request, res: Response):
    # Skip auth for login and register
    if req.url in ["/login", "/register"] or req.method == "OPTIONS":
        return
    
    token = req.get_header("Authorization")
    if not token or not token.startswith("Bearer "):
        res.status(401)
        res.json({"error": "Authorization header required"})
        return
    
    # Verify token (simplified)
    token_value = token[7:]  # Remove "Bearer "
    if token_value != "valid-token":
        res.status(403)
        res.json({"error": "Invalid token"})
        return

# Middleware 4: JSON Content-Type validation
def json_middleware(req: Request, res: Response):
    if req.method in ["POST", "PUT", "PATCH"]:
        content_type = req.get_header("Content-Type")
        if content_type and "application/json" not in content_type:
            res.status(400)
            res.json({"error": "Content-Type must be application/json"})
            return

# Register middleware
app.use(logging_middleware)
app.use(cors_middleware)
app.use(auth_middleware)
app.use(json_middleware)

# Routes
@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Welcome to API", "middleware": "applied"})

@app.post("/login")
async def login(req: Request, res: Response):
    data = await req.json()
    # Simulate login
    if data.get("username") == "admin" and data.get("password") == "password":
        res.json({"token": "valid-token"})
    else:
        res.status(401)
        res.json({"error": "Invalid credentials"})

@app.get("/protected")
def protected(req: Request, res: Response):
    res.json({"message": "This is protected content"})

@app.post("/data")
async def create_data(req: Request, res: Response):
    data = await req.json()
    res.status(201)
    res.json({"created": True, "data": data})

if __name__ == "__main__":
    print("🚀 API with middleware running on http://localhost:8000")
    app.listen(8000)
```

## Middleware Usage Tips

1. **Order Matters**: Middleware are executed in registration order
2. **Error Handling**: Middleware can stop request processing by sending a response
3. **Performance**: Optimize heavy middleware operations
4. **Testing**: Test middleware separately from route handlers
5. **Modularity**: Create middleware focused on single responsibilities
6. **Configuration**: Use parameters to make configurable middleware

## Built-in Middleware

Xyra may provide some built-in middleware in the future, but currently you need to create custom middleware as needed.

---

[Back to Table of Contents](../README.md)