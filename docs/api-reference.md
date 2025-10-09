# Xyra API Reference

Complete API documentation for the Xyra framework, including all available classes, methods, and properties.

## App Class

The main class for creating Xyra applications.

### Constructor

```python
App(options=None, templates_directory="templates", swagger_options=None)
```

**Parameters:**
- `options` (dict, optional): Options for socketify
- `templates_directory` (str): Directory for template files (default: "templates")
- `swagger_options` (dict, optional): Configuration for Swagger documentation

### Methods

#### route(method, path, handler=None)

Register route with specific HTTP method.

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

Register GET route.

```python
app.get("/users", get_users_handler)
```

#### post(path, handler=None)

Register POST route.

```python
app.post("/users", create_user_handler)
```

#### put(path, handler=None)

Register PUT route.

```python
app.put("/users/{id}", update_user_handler)
```

#### delete(path, handler=None)

Register DELETE route.

```python
app.delete("/users/{id}", delete_user_handler)
```

#### patch(path, handler=None)

Register PATCH route.

```python
app.patch("/users/{id}", patch_user_handler)
```

#### head(path, handler=None)

Register HEAD route.

```python
app.head("/users", head_users_handler)
```

#### options(path, handler=None)

Register OPTIONS route.

```python
app.options("/users", options_users_handler)
```

#### use(middleware)

Add middleware to the application.

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
- `path` (str): URL path for static files
- `directory` (str): Filesystem directory for static files

#### websocket(path, handler)

Register WebSocket route.

```python
app.websocket("/ws", websocket_handler)
```

**Parameters:**
- `path` (str): WebSocket path
- `handler` (callable or dict): WebSocket handler

#### listen(port=8000, host="0.0.0.0")

Run the server.

```python
app.listen(8000)  # localhost:8000
app.listen(3000, "127.0.0.1")  # localhost:3000
```

**Parameters:**
- `port` (int): Port for server (default: 8000)
- `host` (str): Host address (default: "0.0.0.0")

### Properties

#### router

Access to router instance.

```python
routes = app.router.routes
```

#### middlewares

List of registered middlewares.

```python
middlewares = app.middlewares
```

#### ws_routes

List of registered WebSocket routes.

```python
ws_routes = app.ws_routes
```

#### templates

Templating instance.

```python
app.templates.add_filter("custom", custom_filter)
```

## Request Class

Class for handling HTTP requests. Supports both synchronous and asynchronous operations.

### Constructor

```python
Request(req, params=None)
```

**Parameters:**
- `req`: Internal request object
- `params` (dict, optional): Route parameters

### Handler Types

Xyra supports both synchronous and asynchronous route handlers:

```python
# Synchronous handler
@app.get("/sync")
def sync_handler(req, res):
    res.json({"type": "sync"})

# Asynchronous handler
@app.get("/async")
async def async_handler(req, res):
    data = await req.json()
    res.json({"type": "async", "data": data})
```

Use async handlers for operations requiring `await` (like `req.json()`, `req.text()`, background tasks). Use sync handlers for simple operations.

### Properties

#### method

HTTP method of the request.

```python
method = req.method  # "GET", "POST", etc.
```

**Type:** str

#### url

Full URL of the request.

```python
url = req.url  # "http://localhost:8000/users?page=1"
```

**Type:** str

#### headers

Dictionary of all headers.

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

Parsed query parameters as dictionary with list values.

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

Get specific header value.

```python
auth = req.get_header("Authorization")
content_type = req.get_header("Content-Type", "application/json")
```

**Parameters:**
- `name` (str): Header name
- `default` (str, optional): Default value if header doesn't exist

**Returns:** Optional[str]

#### get_parameter(index)

Get route parameter by index.

```python
param = req.get_parameter(0)
```

**Parameters:**
- `index` (int): Parameter index

**Returns:** Optional[str]

#### text()

Get request body as text.

```python
async def handler(req, res):
    text_data = await req.text()
```

**Returns:** str

#### json()

Parse request body as JSON (asynchronous).

```python
async def handler(req, res):
    data = await req.json()
```

**Returns:** Any

**Raises:** ValueError if JSON is invalid

#### parse_json(json_string)

Parse a JSON string synchronously.

```python
def handler(req, res):
    json_str = req.query_params.get("data", ["{}"])[0]
    data = req.parse_json(json_str)
```

**Parameters:**
- `json_string` (str): JSON string to parse

**Returns:** Any

**Raises:** ValueError if JSON is invalid

#### form()

Parse request body as form data.

```python
async def handler(req, res):
    form_data = await req.form()
```

**Returns:** Dict[str, str]

#### is_json()

Check if content-type is JSON.

```python
if req.is_json():
    data = await req.json()
```

**Returns:** bool

#### is_form()

Check if content-type is form data.

```python
if req.is_form():
    data = await req.form()
```

**Returns:** bool

## Response Class

Class for creating HTTP responses.

### Methods

#### json(data)

Send JSON response.

```python
res.json({"status": "success", "data": []})
```

**Parameters:**
- `data` (Any): Data to be serialized to JSON

#### html(content)

Send HTML response.

```python
res.html("<h1>Hello World</h1>")
```

**Parameters:**
- `content` (str): HTML content

#### text(content)

Send plain text response.

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

Redirect to another URL.

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
- `**context`: Context variables for template

## WebSocket Class

Class for handling WebSocket connections.

### Methods

#### send(message, opcode=OpCode.TEXT)

Send message to client.

```python
ws.send("Hello World")
ws.send(b"Binary data", OpCode.BINARY)
```

**Parameters:**
- `message` (str or bytes): Message content
- `opcode` (OpCode): Message type (default: OpCode.TEXT)

#### send_text(message)

Send text message.

```python
ws.send_text("Hello World")
```

**Parameters:**
- `message` (str): Text message

#### send_binary(message)

Send binary message.

```python
ws.send_binary(b"Binary data")
```

**Parameters:**
- `message` (bytes): Binary data

#### publish(topic, message, opcode=OpCode.TEXT, compress=False)

Publish message to topic (broadcast).

```python
ws.publish("room1", "Hello everyone!")
```

**Parameters:**
- `topic` (str): Topic name
- `message` (str or bytes): Message content
- `opcode` (OpCode): Message type
- `compress` (bool): Enable compression

#### subscribe(topic)

Subscribe to topic.

```python
ws.subscribe("notifications")
ws.subscribe("room1")
```

**Parameters:**
- `topic` (str): Topic name

#### unsubscribe(topic)

Unsubscribe from topic.

```python
ws.unsubscribe("room1")
```

**Parameters:**
- `topic` (str): Topic name

#### close(code=1000, message=None)

Close WebSocket connection.

```python
ws.close()  # Normal closure
ws.close(1001, "Going away")  # With code and message
```

**Parameters:**
- `code` (int): Close code (default: 1000)
- `message` (str, optional): Close message

#### ping(message=b"")

Send ping frame.

```python
ws.ping(b"ping data")
```

**Parameters:**
- `message` (str or bytes): Ping data

#### pong(message=b"")

Send pong frame.

```python
ws.pong(b"pong data")
```

**Parameters:**
- `message` (str or bytes): Pong data

### Properties

#### closed

Check if connection is closed.

```python
if ws.closed:
    print("Connection is closed")
```

**Type:** bool

## Templating Class

Class for handling template rendering with Jinja2.

### Constructor

```python
Templating(directory="templates", auto_reload=True)
```

**Parameters:**
- `directory` (str): Template directory
- `auto_reload` (bool): Auto reload templates during development

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

Render template from string.

```python
template = "<h1>{{ title }}</h1>"
html = app.templates.render_string(template, title="Hello")
```

**Parameters:**
- `template_string` (str): Template content
- `**context`: Context variables

**Returns:** str

#### add_global(name, value)

Add global variable to all templates.

```python
app.templates.add_global("current_year", 2024)
app.templates.add_global("url_for", lambda route: f"/{route}")
```

**Parameters:**
- `name` (str): Global variable name
- `value` (Any): Variable value

#### add_filter(name, func)

Add custom filter.

```python
def currency_filter(value):
    return f"Rp{value:,.0f}"

app.templates.add_filter("currency", currency_filter)
```

**Parameters:**
- `name` (str): Filter name
- `func` (callable): Filter function

#### list_templates()

List all available templates.

```python
templates = app.templates.list_templates()
```

**Returns:** List[str]

#### template_exists(template_name)

Check if template exists.

```python
if app.templates.template_exists("index.html"):
    # Template exists
    pass
```

**Parameters:**
- `template_name` (str): Template name

**Returns:** bool

#### get_template_source(template_name)

Get template source code (for debugging).

```python
source, filename, uptodate = app.templates.get_template_source("index.html")
```

**Parameters:**
- `template_name` (str): Template name

**Returns:** tuple

## Background Tasks

Xyra supports running background tasks asynchronously.

### create_background_task(func, *args, **kwargs)

Create and run a background task.

```python
from xyra.background import create_background_task

async def send_email(email):
    # Simulate sending email
    await asyncio.sleep(1)
    print(f"Email sent to {email}")

@app.post("/send-email")
async def send_email_endpoint(req, res):
    data = await req.json()
    email = data["email"]

    # Run in background
    task = create_background_task(send_email, email)

    res.json({"message": "Email will be sent in background"})
```

**Parameters:**
- `func` (callable): Async function to run
- `*args`, `**kwargs`: Arguments for the function

**Returns:** Task object

## Concurrency

Xyra provides utilities for concurrent operations.

### to_thread(func)

Run a blocking function in a thread pool.

```python
from xyra.concurrency import to_thread

@to_thread
def blocking_operation(x, y):
    # Simulate blocking I/O
    time.sleep(1)
    return x + y

@app.get("/compute")
async def compute(req, res):
    result = await blocking_operation(5, 3)
    res.json({"result": result})
```

**Parameters:**
- `func` (callable): Function to run in thread

**Returns:** Decorated async function

---

[Back to Table of Contents](../README.md)