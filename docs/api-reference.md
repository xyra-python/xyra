<file_path>
xyra/docs/api-reference.md
</file_path>

<edit_description>
Buat file api reference
</edit_description>

# API Reference Xyra

Dokumentasi lengkap API untuk framework Xyra, termasuk semua class, method, dan properti yang tersedia.

## App Class

Class utama untuk membuat aplikasi Xyra.

### Constructor

```python
App(options=None, templates_directory="templates", swagger_options=None)
```

**Parameters:**
- `options` (dict, optional): Opsi untuk socketify
- `templates_directory` (str): Direktori untuk template files (default: "templates")
- `swagger_options` (dict, optional): Konfigurasi untuk Swagger documentation

### Methods

#### route(method, path, handler=None)

Register route dengan method HTTP tertentu.

```python
app.route("GET", "/users", handler_function)
app.route("POST", "/users", handler_function)
```

**Parameters:**
- `method` (str): HTTP method (GET, POST, PUT, DELETE, etc.)
- `path` (str): Route path
- `handler` (callable, optional): Handler function

**Returns:** Union[callable, App]

#### get(path, handler=None)

Register route GET.

```python
app.get("/users", get_users_handler)
```

#### post(path, handler=None)

Register route POST.

```python
app.post("/users", create_user_handler)
```

#### put(path, handler=None)

Register route PUT.

```python
app.put("/users/{id}", update_user_handler)
```

#### delete(path, handler=None)

Register route DELETE.

```python
app.delete("/users/{id}", delete_user_handler)
```

#### patch(path, handler=None)

Register route PATCH.

```python
app.patch("/users/{id}", patch_user_handler)
```

#### head(path, handler=None)

Register route HEAD.

```python
app.head("/users", head_users_handler)
```

#### options(path, handler=None)

Register route OPTIONS.

```python
app.options("/users", options_users_handler)
```

#### use(middleware)

Tambahkan middleware ke aplikasi.

```python
def my_middleware(req, res):
    # middleware logic
    pass

app.use(my_middleware)
```

**Parameters:**
- `middleware` (callable): Middleware function

#### static_files(path, directory)

Setup serving static files.

```python
app.static_files("/static", "static")
```

**Parameters:**
- `path` (str): URL path untuk static files
- `directory` (str): Direktori filesystem untuk static files

#### websocket(path, handler)

Register WebSocket route.

```python
app.websocket("/ws", websocket_handler)
```

**Parameters:**
- `path` (str): WebSocket path
- `handler` (callable or dict): WebSocket handler

#### listen(port=8000, host="0.0.0.0")

Jalankan server.

```python
app.listen(8000)  # localhost:8000
app.listen(3000, "127.0.0.1")  # localhost:3000
```

**Parameters:**
- `port` (int): Port untuk server (default: 8000)
- `host` (str): Host address (default: "0.0.0.0")

### Properties

#### router

Akses ke router instance.

```python
routes = app.router.routes
```

#### middlewares

List middleware yang terdaftar.

```python
middlewares = app.middlewares
```

#### ws_routes

List WebSocket routes yang terdaftar.

```python
ws_routes = app.ws_routes
```

#### templates

Templating instance.

```python
app.templates.add_filter("custom", custom_filter)
```

## Request Class

Class untuk menangani HTTP request.

### Constructor

```python
Request(req, params=None)
```

**Parameters:**
- `req`: Internal request object
- `params` (dict, optional): Route parameters

### Properties

#### method

HTTP method dari request.

```python
method = req.method  # "GET", "POST", etc.
```

**Type:** str

#### url

URL lengkap dari request.

```python
url = req.url  # "http://localhost:8000/users?page=1"
```

**Type:** str

#### headers

Dictionary semua headers.

```python
headers = req.headers
user_agent = req.headers.get("User-Agent")
```

**Type:** Dict[str, str]

#### query

Raw query string.

```python
query = req.query  # "?page=1&limit=10"
```

**Type:** str

#### query_params

Parsed query parameters sebagai dictionary dengan list values.

```python
params = req.query_params
page = params.get("page", ["1"])[0]
```

**Type:** Dict[str, List[str]]

#### params

Route parameters.

```python
user_id = req.params.get("user_id")
```

**Type:** Dict[str, str]

#### content_type

Content-Type header.

```python
content_type = req.content_type
```

**Type:** Optional[str]

#### content_length

Content-Length header.

```python
length = req.content_length
```

**Type:** Optional[int]

### Methods

#### get_header(name, default=None)

Ambil nilai header tertentu.

```python
auth = req.get_header("Authorization")
content_type = req.get_header("Content-Type", "application/json")
```

**Parameters:**
- `name` (str): Nama header
- `default` (str, optional): Nilai default jika header tidak ada

**Returns:** Optional[str]

#### get_parameter(index)

Ambil parameter route berdasarkan index.

```python
param = req.get_parameter(0)
```

**Parameters:**
- `index` (int): Index parameter

**Returns:** Optional[str]

#### text()

Ambil body request sebagai text.

```python
async def handler(req, res):
    text_data = await req.text()
```

**Returns:** str

#### json()

Parse body request sebagai JSON.

```python
async def handler(req, res):
    data = await req.json()
```

**Returns:** Any

**Raises:** ValueError jika JSON invalid

#### form()

Parse body request sebagai form data.

```python
async def handler(req, res):
    form_data = await req.form()
```

**Returns:** Dict[str, str]

#### is_json()

Cek apakah content-type adalah JSON.

```python
if req.is_json():
    data = await req.json()
```

**Returns:** bool

#### is_form()

Cek apakah content-type adalah form data.

```python
if req.is_form():
    data = await req.form()
```

**Returns:** bool

## Response Class

Class untuk membuat HTTP response.

### Methods

#### json(data)

Kirim response JSON.

```python
res.json({"status": "success", "data": []})
```

**Parameters:**
- `data` (Any): Data yang akan di-serialize ke JSON

#### html(content)

Kirim response HTML.

```python
res.html("<h1>Hello World</h1>")
```

**Parameters:**
- `content` (str): HTML content

#### text(content)

Kirim response plain text.

```python
res.text("Hello World")
```

**Parameters:**
- `content` (str): Text content

#### status(code)

Set HTTP status code.

```python
res.status(404)
res.json({"error": "Not found"})
```

**Parameters:**
- `code` (int): HTTP status code

#### set_header(name, value)

Set response header.

```python
res.set_header("Content-Type", "application/json")
res.set_header("X-Custom", "value")
```

**Parameters:**
- `name` (str): Header name
- `value` (str): Header value

#### redirect(url)

Redirect ke URL lain.

```python
res.redirect("/login")
```

**Parameters:**
- `url` (str): Target URL

#### set_cookie(name, value)

Set cookie.

```python
res.set_cookie("session_id", "abc123")
res.set_cookie("theme", "dark", max_age=86400)
```

**Parameters:**
- `name` (str): Cookie name
- `value` (str): Cookie value
- `max_age` (int, optional): Max age in seconds

#### render(template, **context)

Render template.

```python
res.render("index.html", title="Home", users=users)
```

**Parameters:**
- `template` (str): Template filename
- `**context`: Context variables untuk template

## WebSocket Class

Class untuk menangani WebSocket connections.

### Methods

#### send(message, opcode=OpCode.TEXT)

Kirim message ke client.

```python
ws.send("Hello World")
ws.send(b"Binary data", OpCode.BINARY)
```

**Parameters:**
- `message` (str or bytes): Message content
- `opcode` (OpCode): Message type (default: OpCode.TEXT)

#### send_text(message)

Kirim text message.

```python
ws.send_text("Hello World")
```

**Parameters:**
- `message` (str): Text message

#### send_binary(message)

Kirim binary message.

```python
ws.send_binary(b"Binary data")
```

**Parameters:**
- `message` (bytes): Binary data

#### publish(topic, message, opcode=OpCode.TEXT, compress=False)

Publish message ke topic (broadcast).

```python
ws.publish("room1", "Hello everyone!")
```

**Parameters:**
- `topic` (str): Topic name
- `message` (str or bytes): Message content
- `opcode` (OpCode): Message type
- `compress` (bool): Enable compression

#### subscribe(topic)

Subscribe ke topic.

```python
ws.subscribe("notifications")
ws.subscribe("room1")
```

**Parameters:**
- `topic` (str): Topic name

#### unsubscribe(topic)

Unsubscribe dari topic.

```python
ws.unsubscribe("room1")
```

**Parameters:**
- `topic` (str): Topic name

#### close(code=1000, message=None)

Tutup WebSocket connection.

```python
ws.close()  # Normal closure
ws.close(1001, "Going away")  # With code and message
```

**Parameters:**
- `code` (int): Close code (default: 1000)
- `message` (str, optional): Close message

#### ping(message=b"")

Kirim ping frame.

```python
ws.ping(b"ping data")
```

**Parameters:**
- `message` (str or bytes): Ping data

#### pong(message=b"")

Kirim pong frame.

```python
ws.pong(b"pong data")
```

**Parameters:**
- `message` (str or bytes): Pong data

### Properties

#### closed

Cek apakah connection sudah ditutup.

```python
if ws.closed:
    print("Connection is closed")
```

**Type:** bool

## Templating Class

Class untuk menangani template rendering dengan Jinja2.

### Constructor

```python
Templating(directory="templates", auto_reload=True)
```

**Parameters:**
- `directory` (str): Template directory
- `auto_reload` (bool): Auto reload templates saat development

### Methods

#### render(template_name, **context)

Render template file.

```python
html = app.templates.render("index.html", title="Home", users=users)
```

**Parameters:**
- `template_name` (str): Template filename
- `**context`: Context variables

**Returns:** str

#### render_string(template_string, **context)

Render template dari string.

```python
template = "<h1>{{ title }}</h1>"
html = app.templates.render_string(template, title="Hello")
```

**Parameters:**
- `template_string` (str): Template content
- `**context`: Context variables

**Returns:** str

#### add_global(name, value)

Tambah global variable ke semua templates.

```python
app.templates.add_global("current_year", 2024)
app.templates.add_global("url_for", lambda route: f"/{route}")
```

**Parameters:**
- `name` (str): Global variable name
- `value` (Any): Variable value

#### add_filter(name, func)

Tambah custom filter.

```python
def currency_filter(value):
    return f"Rp{value:,.0f}"

app.templates.add_filter("currency", currency_filter)
```

**Parameters:**
- `name` (str): Filter name
- `func` (callable): Filter function

#### list_templates()

List semua template yang tersedia.

```python
templates = app.templates.list_templates()
```

**Returns:** List[str]

#### template_exists(template_name)

Cek apakah template ada.

```python
if app.templates.template_exists("index.html"):
    # Template exists
    pass
```

**Parameters:**
- `template_name` (str): Template name

**Returns:** bool

#### get_template_source(template_name)

Ambil source code template (untuk debugging).

```python
source, filename, uptodate = app.templates.get_template_source("index.html")
```

**Parameters:**
- `template_name` (str): Template name

**Returns:** tuple

---

[Kembali ke Daftar Isi](../README.md)