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

## Rate Limiting Middleware

Xyra provides a built-in rate limiter middleware to limit requests per client:

```python
from xyra import App
from xyra.middleware import rate_limiter

app = App()

# Add rate limiter: 100 requests per minute per IP
app.use(rate_limiter(requests=100, window=60))

@app.get("/")
def home(req, res):
    res.json({"message": "Hello World"})
```

### Rate Limiter Options

```python
# 10 requests per second
app.use(rate_limiter(requests=10, window=1))

# 1000 requests per hour
app.use(rate_limiter(requests=1000, window=3600))

# Custom key function (by user ID instead of IP)
def get_user_key(req):
    return req.get_header("X-User-ID") or "anonymous"

app.use(rate_limiter(requests=50, window=60, key_func=get_user_key))
```

### Rate Limit Headers

The middleware adds standard rate limit headers:

- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the limit resets (Unix timestamp)

### Rate Limit Response

When limit is exceeded, returns HTTP 429 with:

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

Plus `Retry-After` header with seconds until reset.

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
from xyra.middleware import rate_limiter

app = App()

# Rate limiting: 100 requests per minute
app.use(rate_limiter(requests=100, window=60))

# CORS middleware
def cors_middleware(req: Request, res: Response):
    res.set_header("Access-Control-Allow-Origin", "*")
    res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

# Authentication middleware
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

# JSON Content-Type validation
def json_middleware(req: Request, res: Response):
    if req.method in ["POST", "PUT", "PATCH"]:
        content_type = req.get_header("Content-Type")
        if content_type and "application/json" not in content_type:
            res.status(400)
            res.json({"error": "Content-Type must be application/json"})
            return

# Register middleware
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

Xyra provides several built-in middleware for common use cases:

### CORS Middleware

```python
from xyra.middleware import cors

app.use(cors(
    allowed_origins=["http://localhost:3000", "https://myapp.com"],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
    allowed_headers=["Content-Type", "Authorization"],
    allow_credentials=True
))
```

### Gzip Compression

```python
from xyra.middleware import gzip_middleware

app.use(gzip_middleware(minimum_size=1024, compress_level=6))
```

### HTTPS Redirect

```python
from xyra.middleware import https_redirect_middleware

app.use(https_redirect_middleware(redirect_status_code=301))
```

### Trusted Host

```python
from xyra.middleware import trusted_host_middleware

app.use(trusted_host_middleware(allowed_hosts=["myapp.com", "api.myapp.com"]))
```

### Rate Limiter

```python
from xyra.middleware import rate_limiter

app.use(rate_limiter(requests=100, window=60))
```

---

[Back to Table of Contents](../README.md)