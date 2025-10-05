<file_path>
xyra/docs/middleware.md
</file_path>

<edit_description>
Buat file middleware
</edit_description>

# Middleware di Xyra

Middleware adalah fungsi yang dijalankan sebelum atau sesudah handler route utama. Middleware memungkinkan Anda untuk menambahkan logika umum seperti autentikasi, logging, CORS handling, atau validasi input ke semua atau beberapa route tertentu.

## Cara Kerja Middleware

Middleware di Xyra adalah fungsi yang menerima parameter `req` (Request), `res` (Response), dan opsional `next` untuk melanjutkan ke middleware/route berikutnya.

```python
def my_middleware(req: Request, res: Response):
    # Logic middleware
    print(f"Request to: {req.url}")
    # Lanjutkan ke handler berikutnya
    # (implementasi internal akan handle ini)
```

## Menambahkan Middleware

Gunakan method `use()` pada objek App untuk menambahkan middleware:

```python
from xyra import App, Request, Response

app = App()

# Middleware logging
def logging_middleware(req: Request, res: Response):
    print(f"{req.method} {req.url} - {time.time()}")

# Middleware CORS
def cors_middleware(req: Request, res: Response):
    res.set_header("Access-Control-Allow-Origin", "*")
    res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

# Tambahkan middleware
app.use(logging_middleware)
app.use(cors_middleware)
```

## Urutan Eksekusi

Middleware dijalankan dalam urutan mereka ditambahkan:

```python
app.use(middleware1)  # Dijalankan pertama
app.use(middleware2)  # Dijalankan kedua
app.use(middleware3)  # Dijalankan ketiga

@app.get("/test")
def handler(req, res):
    # Dijalankan terakhir
    res.json({"message": "OK"})
```

## Middleware dengan Error Handling

Middleware dapat menghentikan request dengan mengirim response:

```python
def auth_middleware(req: Request, res: Response):
    token = req.get_header("Authorization")
    if not token:
        res.status(401)
        res.json({"error": "Unauthorized"})
        return  # Hentikan eksekusi
    
    # Verifikasi token...
    if not is_valid_token(token):
        res.status(403)
        res.json({"error": "Invalid token"})
        return
    
    # Lanjutkan ke handler berikutnya
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

## Tips Penggunaan Middleware

1. **Urutan Penting**: Middleware dijalankan dalam urutan registrasi
2. **Error Handling**: Middleware dapat menghentikan request dengan mengirim response
3. **Performance**: Middleware yang berat sebaiknya dioptimalkan
4. **Testing**: Test middleware secara terpisah dari route handlers
5. **Modularity**: Buat middleware yang fokus pada satu tanggung jawab
6. **Configuration**: Gunakan parameter untuk membuat middleware yang dapat dikonfigurasi

## Built-in Middleware

Xyra mungkin menyediakan beberapa middleware built-in di masa depan, tapi saat ini Anda perlu membuat middleware custom sesuai kebutuhan.

---

[Kembali ke Daftar Isi](../README.md)