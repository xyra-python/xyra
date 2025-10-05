from xyra import App

# Inisialisasi dengan direktori template
app = App(templates_directory="templates")
```

Secara default, Xyra akan mencari template di direktori `templates/`. Anda dapat mengubahnya dengan parameter `templates_directory`.

## Render Template

Untuk merender template, gunakan method `render()` pada objek Response:

```python
@app.get("/page")
def render_page(req: Request, res: Response):
    res.render("page.html", title="My Page", users=["Alice", "Bob"])
```

Parameter pertama adalah nama file template, diikuti oleh context variables yang akan tersedia di template.

## Template HTML

Template menggunakan sintaks Jinja2. Berikut adalah contoh template HTML:

```html
<!-- templates/page.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ static('css/style.css') }}">
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
        <nav>
            <a href="{{ url_for('home') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
        </nav>
    </header>

    <main>
        <h2>Users</h2>
        <ul>
        {% for user in users %}
            <li>{{ user }}</li>
        {% endfor %}
        </ul>

        {% if users %}
            <p>Total users: {{ users|length }}</p>
        {% else %}
            <p>No users found.</p>
        {% endif %}
    </main>

    <footer>
        <p>&copy; {{ current_year }} My App</p>
    </footer>

    <script src="{{ static('js/app.js') }}"></script>
</body>
</html>
```

## Sintaks Jinja2

### Variables

Gunakan `{{ variable }}` untuk menampilkan nilai variable:

```html
<h1>Hello, {{ name }}!</h1>
<p>Age: {{ age }}</p>
```

### Filters

Filter mengubah nilai variable. Gunakan pipe `|` untuk menerapkan filter:

```html
<p>{{ name|upper }}</p>  <!-- NAMA BESAR -->
<p>{{ price|currency }}</p>  <!-- $1,234.56 -->
<p>{{ text|truncate(50) }}</p>  <!-- Potong teks menjadi 50 karakter -->
```

Filter built-in Jinja2:
- `upper`, `lower`: Ubah case
- `truncate`: Potong teks
- `length`: Panjang string/list
- `default`: Nilai default jika kosong

### Control Structures

#### If Statement

```html
{% if user.is_admin %}
    <p>Welcome, admin!</p>
{% elif user.is_moderator %}
    <p>Welcome, moderator!</p>
{% else %}
    <p>Welcome, user!</p>
{% endif %}
```

#### For Loop

```html
<ul>
{% for item in items %}
    <li>{{ item.name }}</li>
{% endfor %}
</ul>
```

#### Macros

```html
{% macro render_user(user) %}
    <div class="user">
        <h3>{{ user.name }}</h3>
        <p>{{ user.email }}</p>
    </div>
{% endmacro %}

{{ render_user(current_user) }}
```

## Custom Filters dan Globals

Xyra memungkinkan Anda menambahkan custom filters dan global functions ke template.

### Custom Filters

```python
# Tambah filter custom
app.templates.add_filter("currency", lambda value, symbol="$": f"{symbol}{value:,.2f}")
app.templates.add_filter("uppercase", lambda text: text.upper())

# Penggunaan di template
{{ 1234.56 | currency }}  <!-- $1,234.56 -->
{{ 1234.56 | currency("€") }}  <!-- €1,234.56 -->
{{ "hello" | uppercase }}  <!-- HELLO -->
```

### Global Functions

```python
# Tambah global function
app.templates.add_global("current_year", 2024)
app.templates.add_global("url_for", lambda route: f"/{route}")

# Penggunaan di template
<p>&copy; {{ current_year }} My App</p>
<a href="{{ url_for('about') }}">About</a>
```

## Static Files

Untuk file statis (CSS, JS, gambar), gunakan helper `static()`:

```python
app.templates.add_global("static", lambda path: f"/static/{path}")
```

Lalu di template:

```html
<link rel="stylesheet" href="{{ static('css/style.css') }}">
<script src="{{ static('js/app.js') }}"></script>
<img src="{{ static('images/logo.png') }}" alt="Logo">
```

## Render dari String

Selain dari file, Anda juga dapat merender template dari string:

```python
from xyra import App

app = App()

@app.get("/dynamic")
def dynamic_template(req: Request, res: Response):
    template_string = """
    <h1>{{ title }}</h1>
    <p>Message: {{ message }}</p>
    """
    
    # Render dari string
    html = app.templates.render_string(template_string, 
                                      title="Dynamic Page", 
                                      message="Hello from string template!")
    
    res.html(html)
```

## Contoh Lengkap

Berikut adalah contoh aplikasi lengkap dengan templating:

```python
from xyra import App, Request, Response

app = App(templates_directory="templates")

# Setup custom filters dan globals
app.templates.add_filter("currency", lambda value: f"Rp{value:,.0f}")
app.templates.add_global("current_year", 2024)
app.templates.add_global("static", lambda path: f"/static/{path}")

# Routes
@app.get("/")
def home(req: Request, res: Response):
    products = [
        {"name": "Laptop", "price": 15000000, "category": "Electronics"},
        {"name": "Book", "price": 50000, "category": "Education"},
        {"name": "Chair", "price": 750000, "category": "Furniture"}
    ]
    
    res.render("home.html", 
              title="My Store", 
              products=products,
              featured_product=products[0])

@app.get("/product/{product_id}")
def product_detail(req: Request, res: Response):
    product_id = req.params.get("product_id")
    
    # Simulasi get product from database
    product = {
        "id": product_id,
        "name": f"Product {product_id}",
        "price": 100000,
        "description": f"This is product {product_id}",
        "category": "General"
    }
    
    res.render("product.html", product=product)

@app.get("/about")
def about(req: Request, res: Response):
    res.render("about.html", title="About Us")

# Static files
app.static_files("/static", "static")

if __name__ == "__main__":
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
    <header>
        <h1>{{ title }}</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/about">About</a>
        </nav>
    </header>

    <main>
        <section class="featured">
            <h2>Featured Product</h2>
            <div class="product">
                <h3>{{ featured_product.name }}</h3>
                <p>Price: {{ featured_product.price | currency }}</p>
                <p>Category: {{ featured_product.category }}</p>
            </div>
        </section>

        <section class="products">
            <h2>All Products</h2>
            <div class="product-grid">
            {% for product in products %}
                <div class="product-card">
                    <h3>{{ product.name }}</h3>
                    <p>Price: {{ product.price | currency }}</p>
                    <p>Category: {{ product.category }}</p>
                    <a href="/product/{{ loop.index }}">View Details</a>
                </div>
            {% endfor %}
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; {{ current_year }} {{ title }}</p>
    </footer>
</body>
</html>
```

## Tips Templating

1. **Gunakan inheritance**: Manfaatkan template inheritance Jinja2 untuk layout yang konsisten
2. **Validasi context**: Pastikan semua variable yang digunakan di template tersedia di context
3. **Escape output**: Jinja2 secara otomatis escape HTML, tapi hati-hati dengan `|safe` filter
4. **Optimasi performa**: Gunakan caching untuk template yang sering digunakan
5. **Organisasi file**: Pisahkan template ke dalam subfolder berdasarkan fitur

---

[Kembali ke Daftar Isi](../README.md)