---
layout: default
---

# Templating in Xyra

Xyra uses Jinja2 for templating. Templates allow you to generate dynamic HTML pages with data from your routes.

## Setup Templates

By default, Xyra looks for templates in the `templates/` directory. You can change it with the `templates_directory` parameter.

```python
from xyra import App

# Initialize with templates directory
app = App(templates_directory="templates")
```

## Render Template

To render a template, use the `render()` method on the Response object:

```python
@app.get("/page")
def render_page(req: Request, res: Response):
    res.render("page.html", title="My Page", users=["Alice", "Bob"])
```

The first parameter is the template file name, followed by context variables that will be available in the template.

## HTML Template

Templates use Jinja2 syntax. Here is an example HTML template:

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

## Jinja2 Syntax

### Variables

Use `{{ variable }}` to display variable values:

```html
<h1>Hello, {{ name }}!</h1>
<p>Age: {{ age }}</p>
```

### Filters

Filters modify variable values. Use the pipe `|` to apply a filter:

```html
<p>{{ name|upper }}</p>  <!-- ALL CAPS -->
<p>{{ price|currency }}</p>  <!-- $1,234.56 -->
<p>{{ text|truncate(50) }}</p>  <!-- Truncate text to 50 characters -->
```

Built-in Jinja2 filters:
- `upper`, `lower`: Change case
- `truncate`: Truncate text
- `length`: Length of string/list
- `default`: Default value if empty

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

## Custom Filters and Globals

Xyra allows you to add custom filters and global functions to templates.

### Custom Filters

```python
# Add custom filter
app.templates.add_filter("currency", lambda value, symbol="$": f"{symbol}{value:,.2f}")
app.templates.add_filter("uppercase", lambda text: text.upper())

# Usage in template
{{ 1234.56 | currency }}  <!-- $1,234.56 -->
{{ 1234.56 | currency("€") }}  <!-- €1,234.56 -->
{{ "hello" | uppercase }}  <!-- HELLO -->
```

### Global Functions

```python
# Add global function
app.templates.add_global("current_year", 2024)
app.templates.add_global("url_for", lambda route: f"/{route}")

# Usage in template
<p>&copy; {{ current_year }} My App</p>
<a href="{{ url_for('about') }}">About</a>
```

## Static Files

For static files (CSS, JS, images), use the `static()` helper:

```python
app.templates.add_global("static", lambda path: f"/static/{path}")
```

Then in the template:

```html
<link rel="stylesheet" href="{{ static('css/style.css') }}">
<script src="{{ static('js/app.js') }}"></script>
<img src="{{ static('images/logo.png') }}" alt="Logo">
```

## Render from String

In addition to files, you can also render templates from strings:

```python
from xyra import App

app = App()

@app.get("/dynamic")
def dynamic_template(req: Request, res: Response):
    template_string = """
    <h1>{{ title }}</h1>
    <p>Message: {{ message }}</p>
    """
    
    # Render from string
    html = app.templates.render_string(template_string, 
                                      title="Dynamic Page", 
                                      message="Hello from string template!")
    
    res.html(html)
```

## Complete Example

Here is a complete application example with templating:

```python
from xyra import App, Request, Response

app = App(templates_directory="templates")

# Setup custom filters and globals
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
    
    # Simulate get product from database
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

## Templating Tips

1. **Use inheritance**: Leverage Jinja2 template inheritance for consistent layouts
2. **Validate context**: Ensure all variables used in the template are available in the context
3. **Escape output**: Jinja2 automatically escapes HTML, but be careful with the `|safe` filter
4. **Performance optimization**: Use caching for frequently used templates
5. **File organization**: Separate templates into subfolders based on features

---

[Back to Table of Contents](../README.md)