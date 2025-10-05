<file_path>
xyra/docs/static-files.md
</file_path>

<edit_description>
Buat file static files
</edit_description>

# Static Files di Xyra

Xyra memungkinkan Anda untuk serve file statis seperti CSS, JavaScript, gambar, dan file lainnya. File statis disimpan di direktori tertentu dan diakses melalui URL path yang ditentukan.

## Setup Static Files

Gunakan method `static_files()` pada objek App untuk mengatur serving file statis:

```python
from xyra import App

app = App()

# Serve file statis dari direktori "static" ke path "/static"
app.static_files("/static", "static")
```

Parameter:
- Path pertama: URL path yang akan digunakan untuk mengakses file (contoh: "/static")
- Path kedua: Direktori di filesystem tempat file statis disimpan

## Struktur Direktori

Organisasi direktori yang direkomendasikan:

```
project/
├── app.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   ├── images/
│   │   └── logo.png
│   └── favicon.ico
└── templates/
    └── index.html
```

## Mengakses File Statis

Setelah setup, file dapat diakses melalui URL:

- `http://localhost:8000/static/css/style.css`
- `http://localhost:8000/static/js/app.js`
- `http://localhost:8000/static/images/logo.png`

## Menggunakan di Template

Di template Jinja2, Anda dapat menggunakan helper function untuk generate URL:

```python
# Tambahkan global function untuk static files
app.templates.add_global("static", lambda path: f"/static/{path}")
```

Lalu di template:

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ static('css/style.css') }}">
    <script src="{{ static('js/app.js') }}"></script>
</head>
<body>
    <img src="{{ static('images/logo.png') }}" alt="Logo">
</body>
</html>
```

## Contoh Lengkap

```python
from xyra import App, Request, Response

app = App(templates_directory="templates")

# Setup static files
app.static_files("/assets", "static")

# Setup template helper
app.templates.add_global("static", lambda path: f"/assets/{path}")

@app.get("/")
def home(req: Request, res: Response):
    res.render("home.html", title="Home Page")

@app.get("/about")
def about(req: Request, res: Response):
    res.render("about.html", title="About Us")

if __name__ == "__main__":
    print("🚀 Server running on http://localhost:8000")
    print("📁 Static files available at /assets")
    app.listen(8000)
```

Template `templates/home.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ static('css/style.css') }}">
</head>
<body>
    <h1>{{ title }}</h1>
    <p>Welcome to our website!</p>
    <img src="{{ static('images/logo.png') }}" alt="Company Logo">
    
    <script src="{{ static('js/app.js') }}"></script>
</body>
</html>
```

## File CSS (static/css/style.css)

```css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
}

img {
    max-width: 200px;
    height: auto;
}
```

## File JavaScript (static/js/app.js)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded!');
    
    // Add some interactivity
    const h1 = document.querySelector('h1');
    h1.addEventListener('click', function() {
        alert('Hello from static JS file!');
    });
});
```

## Multiple Static Directories

Anda dapat setup multiple direktori statis untuk organisasi yang lebih baik:

```python
# Public assets
app.static_files("/public", "public")

# Admin assets
app.static_files("/admin-assets", "static/admin")

# User uploads
app.static_files("/uploads", "uploads")
```

## Security Considerations

1. **Path Traversal**: Xyra secara otomatis mencegah path traversal attacks
2. **File Permissions**: Pastikan file memiliki permission yang tepat
3. **Caching Headers**: Tambahkan cache headers untuk performa

```python
# Middleware untuk cache headers
def cache_middleware(req: Request, res: Response):
    if req.url.startswith("/static/"):
        res.set_header("Cache-Control", "public, max-age=31536000")  # 1 year
```

## Tips Static Files

1. **Versioning**: Tambahkan version/hash ke filename untuk cache busting
2. **CDN**: Untuk production, gunakan CDN untuk static files
3. **Compression**: Enable gzip compression untuk text files
4. **Organization**: Kelompokkan file berdasarkan tipe (css, js, images)
5. **Minification**: Minify CSS dan JS untuk production

## Troubleshooting

**File tidak ditemukan**: Pastikan path direktori benar dan file ada di lokasi yang tepat.

**CORS issues**: Jika static files diakses dari domain berbeda, tambahkan CORS headers.

**Performance**: Untuk aplikasi besar, gunakan web server seperti Nginx untuk serve static files.

---

[Kembali ke Daftar Isi](../README.md)