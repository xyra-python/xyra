---
layout: default
---

# Request & Response in Xyra

In Xyra, each route handler receives two main parameters: `Request` and `Response`. These objects provide full access to HTTP request data and complete control over the response sent back to the client.

## Request Object

Objek `Request` berisi semua informasi tentang HTTP request yang masuk, termasuk headers, body, parameters, dan query string.

### Properties

```python
@app.get("/info")
def request_info(req: Request, res: Response):
    # Method HTTP
    method = req.method  # "GET", "POST", dll
    
    # URL lengkap
    url = req.url  # "http://localhost:8000/info?page=1"
    
    # Headers sebagai dictionary
    headers = req.headers
    user_agent = req.get_header("User-Agent")
    
    # Content type dan length
    content_type = req.content_type
    content_length = req.content_length
    
    # Route parameters
    params = req.params  # Dictionary dari parameter route
    
    # Raw query string
    query = req.query  # "?page=1&limit=10"
    
    # Parsed query parameters
    query_params = req.query_params  # Dictionary dengan list values
    
    res.json({
        "method": method,
        "url": url,
        "headers": headers,
        "content_type": content_type,
        "params": params,
        "query": query,
        "query_params": query_params
    })
```

### Methods

#### `get_header(name, default=None)`

Mengambil nilai header tertentu.

```python
@app.get("/headers")
def check_headers(req: Request, res: Response):
    auth_token = req.get_header("Authorization")
    content_type = req.get_header("Content-Type", "application/json")
    
    res.json({
        "auth_token": auth_token,
        "content_type": content_type
    })
```

#### `get_parameter(index)`

Mengambil parameter route berdasarkan index (jarang digunakan, lebih baik gunakan `req.params`).

#### `text()`

Mengambil body request sebagai text.

```python
@app.post("/text")
async def handle_text(req: Request, res: Response):
    text_data = await req.text()
    res.json({"received_text": text_data})
```

#### `json()`

Parse body request sebagai JSON.

```python
@app.post("/json")
async def handle_json(req: Request, res: Response):
    try:
        data = await req.json()
        res.json({"received_json": data})
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})
```

#### `form()`

Parse body request sebagai form data.

```python
@app.post("/form")
async def handle_form(req: Request, res: Response):
    form_data = await req.form()
    res.json({"received_form": form_data})
```

#### `is_json()`

Mengecek apakah content-type adalah JSON.

```python
@app.post("/smart")
async def smart_handler(req: Request, res: Response):
    if req.is_json():
        data = await req.json()
        res.json({"type": "json", "data": data})
    elif req.is_form():
        data = await req.form()
        res.json({"type": "form", "data": data})
    else:
        text = await req.text()
        res.json({"type": "text", "data": text})
```

#### `is_form()`

Mengecek apakah content-type adalah form data.

## Response Object

Objek `Response` digunakan untuk mengirim response kembali ke client. Anda dapat mengatur status code, headers, dan body response.

### Methods

#### `json(data)`

Mengirim response JSON.

```python
@app.get("/api/data")
def api_data(req: Request, res: Response):
    data = {"users": ["Alice", "Bob"], "total": 2}
    res.json(data)
```

#### `html(content)`

Mengirim response HTML.

```python
@app.get("/page")
def html_page(req: Request, res: Response):
    html = "<h1>Hello World</h1><p>This is HTML response</p>"
    res.html(html)
```

#### `text(content)`

Mengirim response plain text.

```python
@app.get("/text")
def text_response(req: Request, res: Response):
    res.text("This is plain text response")
```

#### `status(code)`

Mengatur status code HTTP.

```python
@app.get("/not-found")
def not_found(req: Request, res: Response):
    res.status(404)
    res.json({"error": "Not Found"})
```

#### `set_header(name, value)`

Mengatur header response.

```python
@app.get("/custom-headers")
def custom_headers(req: Request, res: Response):
    res.set_header("X-Custom-Header", "My Value")
    res.set_header("Cache-Control", "no-cache")
    res.json({"message": "Check headers"})
```

#### `redirect(url)`

Redirect ke URL lain.

```python
@app.get("/old-page")
def old_page(req: Request, res: Response):
    res.redirect("/new-page")
```

#### `set_cookie(name, value)`

Mengatur cookie.

```python
@app.get("/set-cookie")
def set_cookie_example(req: Request, res: Response):
    res.set_cookie("session_id", "abc123")
    res.set_cookie("theme", "dark", max_age=86400)  # 24 jam
    res.json({"message": "Cookies set"})
```

#### `render(template, **context)`

Render template (lihat [Templating](templating.md)).

```python
@app.get("/template")
def render_template_example(req: Request, res: Response):
    res.render("page.html", title="My Page", users=["Alice", "Bob"])
```

## Contoh Lengkap

Berikut adalah contoh lengkap yang menunjukkan penggunaan Request dan Response:

```python
from xyra import App, Request, Response

app = App()

@app.get("/user/{user_id}")
def get_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    
    # Validasi parameter
    if not user_id:
        res.status(400)
        res.json({"error": "User ID is required"})
        return
    
    # Simulasi database lookup
    user = {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
    
    res.json(user)

@app.post("/user")
async def create_user(req: Request, res: Response):
    # Cek content type
    if not req.is_json():
        res.status(400)
        res.json({"error": "Content-Type must be application/json"})
        return
    
    try:
        user_data = await req.json()
        
        # Validasi data
        required_fields = ["name", "email"]
        for field in required_fields:
            if field not in user_data:
                res.status(400)
                res.json({"error": f"{field} is required"})
                return
        
        # Simulasi create user
        user_data["id"] = "123"  # Generated ID
        
        res.status(201)
        res.set_header("Location", f"/user/{user_data['id']}")
        res.json(user_data)
        
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON data"})

@app.get("/search")
def search_users(req: Request, res: Response):
    # Query parameters
    query = req.query_params.get("q", [""])[0]
    limit = int(req.query_params.get("limit", ["10"])[0])
    offset = int(req.query_params.get("offset", ["0"])[0])
    
    # Simulasi search
    results = [
        {"id": str(i), "name": f"User {i}", "email": f"user{i}@example.com"}
        for i in range(offset + 1, offset + limit + 1)
        if query.lower() in f"user{i}".lower()
    ]
    
    res.set_header("X-Total-Count", str(len(results)))
    res.json({
        "query": query,
        "limit": limit,
        "offset": offset,
        "results": results
    })

@app.delete("/user/{user_id}")
def delete_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    
    if not user_id:
        res.status(400)
        res.json({"error": "User ID is required"})
        return
    
    # Simulasi delete
    # In real app, check if user exists and delete from database
    
    res.status(204)  # No Content

if __name__ == "__main__":
    app.listen(8000)
```

## Tips Penggunaan

1. **Selalu validasi input**: Cek parameter dan body request sebelum diproses
2. **Gunakan status code yang tepat**: 200 untuk OK, 201 untuk Created, 400 untuk Bad Request, 404 untuk Not Found, 500 untuk Internal Error
3. **Set headers yang sesuai**: Content-Type, Cache-Control, CORS headers, dll
4. **Handle error dengan baik**: Gunakan try-catch untuk parsing JSON dan operasi lainnya
5. **Gunakan async untuk I/O**: Gunakan `await` untuk `req.json()`, `req.text()`, dll

---

[Kembali ke Daftar Isi](../README.md)