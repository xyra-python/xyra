<file_path>
xyra/docs/routing.md
</file_path>

<edit_description>
Buat file routing
</edit_description>

# Routing di Xyra

Routing adalah cara Xyra menangani request HTTP dan mengarahkan mereka ke handler yang sesuai. Xyra mendukung berbagai method HTTP dan routing yang fleksibel dengan parameter dan query string.

## Method HTTP

Xyra mendukung semua method HTTP standar:

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

## Parameter Route

Parameter route memungkinkan Anda menangkap nilai dari URL path.

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

Parameter diakses melalui `req.params`, yang merupakan dictionary.

## Query Parameters

Query parameters digunakan untuk data opsional atau filtering.

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
    
    # Logic untuk filtering, pagination, sorting
    res.json({
        "page": page,
        "per_page": per_page,
        "sort_by": sort_by,
        "users": []
    })
```

Query parameters diakses melalui `req.query_params`, yang merupakan dictionary dengan list sebagai nilai (untuk multiple values).

## Route dengan Method Generik

Anda juga dapat menggunakan method `route()` untuk register route dengan method tertentu:

```python
app.route("GET", "/custom", custom_handler)
app.route("POST", "/custom", custom_post_handler)
```

## Wildcard Routes

Xyra mendukung wildcard dengan `*`:

```python
@app.get("/files/*")
def serve_file(req: Request, res: Response):
    path = req.url.split("/files/", 1)[1]
    # Serve file logic
    res.text(f"Serving file: {path}")
```

## Middleware pada Route

Middleware dapat diterapkan pada route tertentu (fitur ini mungkin memerlukan implementasi khusus).

## Tips Routing

1. **Gunakan parameter yang deskriptif**: `/users/{user_id}` lebih baik daripada `/u/{id}`

2. **Validasi input**: Selalu validasi parameter dan query string

3. **Gunakan HTTP method yang tepat**: GET untuk retrieve, POST untuk create, PUT untuk update, DELETE untuk delete

4. **Handle error dengan baik**: Return status code yang sesuai (404 untuk not found, 400 untuk bad request)

## Contoh Lengkap

```python
from xyra import App, Request, Response

app = App()

# Route sederhana
@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Welcome to Xyra API"})

# Route dengan parameter
@app.get("/users/{user_id}")
def get_user(req: Request, res: Response):
    user_id = req.params.get("user_id")
    if not user_id:
        res.status(400)
        res.json({"error": "User ID required"})
        return
    
    # Logic untuk get user
    res.json({"user_id": user_id, "name": f"User {user_id}"})

# Route dengan query parameters
@app.get("/users")
def list_users(req: Request, res: Response):
    page = int(req.query_params.get("page", ["1"])[0])
    limit = int(req.query_params.get("limit", ["10"])[0])
    
    # Logic untuk pagination
    users = [
        {"id": i, "name": f"User {i}"}
        for i in range((page-1)*limit + 1, page*limit + 1)
    ]
    
    res.json({
        "page": page,
        "limit": limit,
        "users": users
    })

# Route POST dengan body
@app.post("/users")
async def create_user(req: Request, res: Response):
    try:
        user_data = await req.json()
        # Validasi data
        if not user_data.get("name"):
            res.status(400)
            res.json({"error": "Name is required"})
            return
        
        # Logic untuk create user
        res.status(201)
        res.json({"created": True, "user": user_data})
    except ValueError:
        res.status(400)
        res.json({"error": "Invalid JSON"})

if __name__ == "__main__":
    app.listen(8000)
```

---

[Kembali ke Daftar Isi](../README.md)