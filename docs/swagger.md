<file_path>
xyra/docs/swagger.md
</file_path>

<edit_description>
Buat file swagger
</edit_description>

# Dokumentasi API dengan Swagger

Xyra terintegrasi dengan Swagger (OpenAPI) untuk menghasilkan dokumentasi API secara otomatis. Dokumentasi ini memungkinkan developer dan pengguna API untuk memahami endpoint, parameter, dan response yang tersedia.

## Enable Swagger

Untuk mengaktifkan Swagger di aplikasi Xyra, berikan opsi `swagger_options` saat inisialisasi aplikasi:

```python
from xyra import App

app = App(swagger_options={
    "title": "My API",
    "version": "1.0.0",
    "description": "API documentation for My App"
})
```

## Akses Dokumentasi

Setelah diaktifkan, dokumentasi Swagger akan tersedia di:

- **Swagger UI**: `http://localhost:8000/docs` (atau path custom)
- **JSON Spec**: `http://localhost:8000/docs/swagger.json` (atau path custom)

## Konfigurasi Swagger

Anda dapat mengustomisasi berbagai aspek dokumentasi API:

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

### Opsi Konfigurasi

- `title`: Judul API
- `version`: Versi API
- `description`: Deskripsi API
- `contact`: Informasi kontak (name, email, url)
- `license_info`: Informasi lisensi (name, url)
- `servers`: List server dengan URL dan deskripsi
- `swagger_ui_path`: Path untuk Swagger UI (default: "/docs")
- `swagger_json_path`: Path untuk JSON spec (default: "/docs/swagger.json")

## Dokumentasi Otomatis

Xyra secara otomatis menghasilkan dokumentasi dari:

- Route definitions
- Parameter types (dari docstrings)
- Request/response schemas
- HTTP methods

### Contoh Route dengan Dokumentasi

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

Untuk kontrol lebih baik atas schema response, Anda dapat menggunakan type hints dan docstrings:

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

Anda dapat menambahkan informasi autentikasi ke dokumentasi:

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

## Contoh Lengkap

Berikut adalah contoh aplikasi lengkap dengan Swagger:

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

## Testing API melalui Swagger UI

Swagger UI menyediakan interface untuk testing API langsung dari browser:

1. Buka `http://localhost:8000/docs`
2. Klik pada endpoint yang ingin ditest
3. Klik "Try it out"
4. Isi parameter dan body jika diperlukan
5. Klik "Execute"
6. Lihat response di bagian bawah

## Tips Swagger

1. **Docstrings yang Jelas**: Tulis docstring yang deskriptif untuk setiap endpoint
2. **Type Hints**: Gunakan type hints Python untuk schema yang lebih akurat
3. **Response Codes**: Dokumentasikan berbagai response codes (200, 201, 400, 404, dll)
4. **Examples**: Berikan contoh request/response di docstring
5. **Grouping**: Kelompokkan endpoint terkait dengan tags
6. **Authentication**: Dokumentasikan authentication requirements
7. **Versioning**: Update versi API saat ada perubahan breaking

---

[Kembali ke Daftar Isi](../README.md)