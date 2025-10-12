---
layout: default
---

# Static Files in Xyra

Xyra allows you to serve static files such as CSS, JavaScript, images, and other files. Static files are stored in a specific directory and accessed through a defined URL path.

## Setup Static Files

Use the `static_files()` method on the App object to set up serving static files:

```python
from xyra import App

app = App()

# Serve static files from the "static" directory to the "/static" path
app.static_files("/static", "static")
```

Parameters:
- First path: The URL path used to access the files (e.g., "/static")
- Second path: The directory in the filesystem where static files are stored

## Directory Structure

Recommended directory organization:

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

## Accessing Static Files

After setup, files can be accessed via URL:

- `http://localhost:8000/static/css/style.css`
- `http://localhost:8000/static/js/app.js`
- `http://localhost:8000/static/images/logo.png`

## Using in Templates

In Jinja2 templates, you can use a helper function to generate URLs:

```python
# Add a global function for static files
app.templates.add_global("static", lambda path: f"/static/{path}")
```

Then in the template:

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

## Complete Example

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

## CSS File (static/css/style.css)

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

## JavaScript File (static/js/app.js)

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

You can set up multiple static directories for better organization:

```python
# Public assets
app.static_files("/public", "public")

# Admin assets
app.static_files("/admin-assets", "static/admin")

# User uploads
app.static_files("/uploads", "uploads")
```

## Security Considerations

1. **Path Traversal**: Xyra automatically prevents path traversal attacks
2. **File Permissions**: Ensure files have appropriate permissions
3. **Caching Headers**: Add cache headers for performance

```python
# Middleware for cache headers
def cache_middleware(req: Request, res: Response):
    if req.url.startswith("/static/"):
        res.set_header("Cache-Control", "public, max-age=31536000")  # 1 year
```

## Static Files Tips

1. **Versioning**: Add version/hash to filename for cache busting
2. **CDN**: For production, use CDN for static files
3. **Compression**: Enable gzip compression for text files
4. **Organization**: Group files by type (css, js, images)
5. **Minification**: Minify CSS and JS for production

## Troubleshooting

**File not found**: Ensure the directory path is correct and the file exists in the right location.

**CORS issues**: If static files are accessed from a different domain, add CORS headers.

**Performance**: For large applications, use a web server like Nginx to serve static files.

---

[Back to Table of Contents](../README.md)