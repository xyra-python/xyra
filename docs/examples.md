# Complete Examples

This section contains complete application examples that demonstrate various Xyra features in practice. These examples can be used as a starting point for your own projects.

## Simple REST API

Example API for user management with CRUD operations.

```python
from xyra import App, Request, Response
from typing import List, Dict, Any

app = App()

# In-memory storage (use database in production)
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
]

@app.get("/users")
def get_users(req: Request, res: Response) -> List[Dict[str, Any]]:
    """Get all users."""
    res.json(users_db)

@app.get("/users/{user_id}")
def get_user(req: Request, res: Response) -> Dict[str, Any]:
    """Get user by ID."""
    user_id = int(req.params.get("user_id"))
    user = next((u for u in users_db if u["id"] == user_id), None)
    
    if not user:
        res.status(404)
        res.json({"error": "User not found"})
        return
    
    res.json(user)

@app.post("/users")
async def create_user(req: Request, res: Response) -> Dict[str, Any]:
    """Create a new user."""
    user_data = await req.json()
    
    # Simple validation
    if not user_data.get("name") or not user_data.get("email"):
        res.status(400)
        res.json({"error": "Name and email are required"})
        return
    
    # Generate ID
    new_id = max(u["id"] for u in users_db) + 1 if users_db else 1
    user = {"id": new_id, **user_data}
    users_db.append(user)
    
    res.status(201)
    res.json(user)

@app.put("/users/{user_id}")
async def update_user(req: Request, res: Response) -> Dict[str, Any]:
    """Update user by ID."""
    user_id = int(req.params.get("user_id"))
    user_data = await req.json()
    
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        res.status(404)
        res.json({"error": "User not found"})
        return
    
    user.update(user_data)
    res.json(user)

@app.delete("/users/{user_id}")
def delete_user(req: Request, res: Response):
    """Delete user by ID."""
    user_id = int(req.params.get("user_id"))
    
    global users_db
    users_db = [u for u in users_db if u["id"] != user_id]
    
    res.status(204)  # No Content

if __name__ == "__main__":
    print("🚀 Users API running on http://localhost:8000")
    app.listen(8000)
```

## Blog API with Templating

Complete blog application with templating and static files.

```python
from xyra import App, Request, Response
import os

app = App(
    templates_directory="templates",
    swagger_options={
        "title": "Blog API",
        "version": "1.0.0",
        "description": "Blog API with templates"
    }
)

# Setup static files
app.static_files("/static", "static")

# Setup template helpers
app.templates.add_global("static", lambda path: f"/static/{path}")

# Sample blog posts
posts = [
    {
        "id": 1,
        "title": "Welcome to Xyra",
        "content": "This is our first blog post about Xyra framework.",
        "author": "Admin",
        "date": "2024-01-01"
    },
    {
        "id": 2,
        "title": "Getting Started",
        "content": "Learn how to build web applications with Xyra.",
        "author": "Admin",
        "date": "2024-01-02"
    }
]

@app.get("/")
def home(req: Request, res: Response):
    """Home page with latest posts."""
    res.render("home.html", 
              title="My Blog",
              posts=posts[:5])  # Show latest 5 posts

@app.get("/posts")
def list_posts(req: Request, res: Response):
    """List all posts."""
    page = int(req.query_params.get("page", ["1"])[0])
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    
    res.render("posts.html",
              title="All Posts",
              posts=posts[start:end],
              page=page,
              has_next=end < len(posts))

@app.get("/posts/{post_id}")
def view_post(req: Request, res: Response):
    """View single post."""
    post_id = int(req.params.get("post_id"))
    post = next((p for p in posts if p["id"] == post_id), None)
    
    if not post:
        res.status(404)
        res.render("404.html", title="Post Not Found")
        return
    
    res.render("post.html", title=post["title"], post=post)

@app.get("/api/posts")
def api_posts(req: Request, res: Response):
    """JSON API for posts."""
    res.json(posts)

@app.post("/api/posts")
async def api_create_post(req: Request, res: Response):
    """Create new post via API."""
    post_data = await req.json()
    
    new_post = {
        "id": len(posts) + 1,
        "title": post_data["title"],
        "content": post_data["content"],
        "author": post_data.get("author", "Anonymous"),
        "date": "2024-01-01"  # In real app, use current date
    }
    
    posts.append(new_post)
    res.status(201)
    res.json(new_post)

if __name__ == "__main__":
    print("🚀 Blog running on http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
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
            <a href="/posts">All Posts</a>
        </nav>
    </header>

    <main>
        <h2>Latest Posts</h2>
        {% for post in posts %}
        <article class="post">
            <h3><a href="/posts/{{ post.id }}">{{ post.title }}</a></h3>
            <p class="meta">By {{ post.author }} on {{ post.date }}</p>
            <p>{{ post.content[:100] }}...</p>
            <a href="/posts/{{ post.id }}">Read more</a>
        </article>
        {% endfor %}
    </main>

    <footer>
        <p>&copy; 2024 {{ title }}</p>
    </footer>
</body>
</html>
```

## Chat Application dengan WebSocket

Aplikasi chat real-time menggunakan WebSocket.

```python
from xyra import App
import json

app = App()

# Store connected clients
connected_clients = set()

def on_open(ws):
    """Handle new WebSocket connection."""
    connected_clients.add(ws)
    print(f"Client connected. Total: {len(connected_clients)}")
    
    # Send welcome message
    ws.send(json.dumps({
        "type": "system",
        "message": "Welcome to the chat!",
        "online_count": len(connected_clients)
    }))
    
    # Notify others
    broadcast({
        "type": "system",
        "message": "A new user joined the chat",
        "online_count": len(connected_clients)
    }, exclude=ws)

def on_message(ws, message, opcode):
    """Handle incoming message."""
    try:
        data = json.loads(message)
        
        if data["type"] == "chat":
            # Broadcast chat message to all clients
            broadcast({
                "type": "chat",
                "message": data["message"],
                "timestamp": data.get("timestamp", "now")
            }, exclude=None)
        
        elif data["type"] == "typing":
            # Notify others that someone is typing
            broadcast({
                "type": "typing",
                "user": data.get("user", "Anonymous")
            }, exclude=ws)
            
    except json.JSONDecodeError:
        ws.send(json.dumps({"error": "Invalid JSON"}))

def on_close(ws, code, message):
    """Handle WebSocket disconnection."""
    connected_clients.discard(ws)
    print(f"Client disconnected. Total: {len(connected_clients)}")
    
    # Notify others
    broadcast({
        "type": "system",
        "message": "A user left the chat",
        "online_count": len(connected_clients)
    })

def broadcast(message, exclude=None):
    """Broadcast message to all connected clients."""
    for client in connected_clients:
        if client != exclude:
            try:
                client.send(json.dumps(message))
            except:
                # Client might be disconnected
                connected_clients.discard(client)

# WebSocket route
app.websocket("/chat", {
    "open": on_open,
    "message": on_message,
    "close": on_close
})

# HTTP routes for the chat interface
@app.get("/")
def chat_page(req, res):
    """Serve chat interface."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat Room</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
            #messageInput { width: 70%; padding: 5px; }
            button { padding: 5px 10px; }
            .message { margin-bottom: 5px; }
            .system { color: #666; font-style: italic; }
        </style>
    </head>
    <body>
        <h1>Chat Room</h1>
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>

        <script>
            const ws = new WebSocket('ws://localhost:8000/chat');
            const messages = document.getElementById('messages');
            const input = document.getElementById('messageInput');

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                
                if (data.type === 'chat') {
                    messageDiv.textContent = `${data.timestamp}: ${data.message}`;
                } else if (data.type === 'system') {
                    messageDiv.textContent = `System: ${data.message}`;
                    messageDiv.className += ' system';
                }
                
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            };

            function sendMessage() {
                const message = input.value.trim();
                if (message) {
                    ws.send(JSON.stringify({
                        type: 'chat',
                        message: message,
                        timestamp: new Date().toLocaleTimeString()
                    }));
                    input.value = '';
                }
            }

            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """
    res.html(html)

if __name__ == "__main__":
    print("🚀 Chat server running on http://localhost:8000")
    print("🌐 Open http://localhost:8000 in your browser")
    app.listen(8000)
```

## File Upload API

Contoh API untuk upload file.

```python
from xyra import App, Request, Response
import os
import uuid

app = App()

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

@app.post("/upload")
async def upload_file(req: Request, res: Response):
    """Upload a file."""
    try:
        # In a real implementation, you'd handle multipart form data
        # This is a simplified example
        file_data = await req.text()  # Simulate file content
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.txt"
        filepath = os.path.join("uploads", filename)
        
        # Save file
        with open(filepath, "w") as f:
            f.write(file_data)
        
        res.status(201)
        res.json({
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": filename,
            "url": f"/files/{filename}"
        })
        
    except Exception as e:
        res.status(500)
        res.json({"error": f"Upload failed: {str(e)}"})

@app.get("/files/{filename}")
def get_file(req: Request, res: Response):
    """Serve uploaded file."""
    filename = req.params.get("filename")
    filepath = os.path.join("uploads", filename)
    
    if not os.path.exists(filepath):
        res.status(404)
        res.json({"error": "File not found"})
        return
    
    # In a real implementation, you'd stream the file
    # This is simplified
    with open(filepath, "r") as f:
        content = f.read()
    
    res.set_header("Content-Type", "text/plain")
    res.text(content)

@app.get("/files")
def list_files(req: Request, res: Response):
    """List uploaded files."""
    try:
        files = []
        for filename in os.listdir("uploads"):
            filepath = os.path.join("uploads", filename)
            stat = os.stat(filepath)
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "url": f"/files/{filename}"
            })
        
        res.json({"files": files})
    except Exception as e:
        res.status(500)
        res.json({"error": str(e)})

if __name__ == "__main__":
    print("🚀 File upload API running on http://localhost:8000")
    app.listen(8000)
```

## Aplikasi Full-Stack

Contoh aplikasi lengkap dengan frontend dan backend.

```python
from xyra import App, Request, Response
import json

app = App(templates_directory="templates")

# Setup static files
app.static_files("/static", "static")

# Setup template helpers
app.templates.add_global("static", lambda path: f"/static/{path}")

# In-memory todo list
todos = [
    {"id": 1, "title": "Learn Xyra", "completed": False},
    {"id": 2, "title": "Build an app", "completed": True}
]

# API Routes
@app.get("/api/todos")
def get_todos(req: Request, res: Response):
    """Get all todos."""
    res.json(todos)

@app.post("/api/todos")
async def create_todo(req: Request, res: Response):
    """Create new todo."""
    data = await req.json()
    
    new_todo = {
        "id": len(todos) + 1,
        "title": data["title"],
        "completed": False
    }
    
    todos.append(new_todo)
    res.status(201)
    res.json(new_todo)

@app.put("/api/todos/{todo_id}")
async def update_todo(req: Request, res: Response):
    """Update todo."""
    todo_id = int(req.params.get("todo_id"))
    data = await req.json()
    
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        res.status(404)
        res.json({"error": "Todo not found"})
        return
    
    todo.update(data)
    res.json(todo)

@app.delete("/api/todos/{todo_id}")
def delete_todo(req: Request, res: Response):
    """Delete todo."""
    todo_id = int(req.params.get("todo_id"))
    
    global todos
    todos = [t for t in todos if t["id"] != todo_id]
    
    res.status(204)

# Web Routes
@app.get("/")
def home(req: Request, res: Response):
    """Serve the main application."""
    res.render("index.html", title="Todo App")

if __name__ == "__main__":
    print("🚀 Todo App running on http://localhost:8000")
    app.listen(8000)
```

Template `templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ static('css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        
        <form id="todoForm">
            <input type="text" id="todoInput" placeholder="Add new todo..." required>
            <button type="submit">Add</button>
        </form>
        
        <ul id="todoList"></ul>
    </div>

    <script src="{{ static('js/app.js') }}"></script>
</body>
</html>
```

File JavaScript `static/js/app.js`:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const todoForm = document.getElementById('todoForm');
    const todoInput = document.getElementById('todoInput');
    const todoList = document.getElementById('todoList');

    // Load todos
    loadTodos();

    // Add todo
    todoForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const title = todoInput.value.trim();
        if (title) {
            await createTodo(title);
            todoInput.value = '';
            loadTodos();
        }
    });

    async function loadTodos() {
        const response = await fetch('/api/todos');
        const todos = await response.json();
        
        todoList.innerHTML = '';
        todos.forEach(todo => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="${todo.completed ? 'completed' : ''}">${todo.title}</span>
                <button onclick="toggleTodo(${todo.id}, ${todo.completed})">
                    ${todo.completed ? 'Undo' : 'Complete'}
                </button>
                <button onclick="deleteTodo(${todo.id})">Delete</button>
            `;
            todoList.appendChild(li);
        });
    }

    async function createTodo(title) {
        await fetch('/api/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
    }

    async function toggleTodo(id, completed) {
        await fetch(`/api/todos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completed: !completed })
        });
        loadTodos();
    }

    async function deleteTodo(id) {
        await fetch(`/api/todos/${id}`, {
            method: 'DELETE'
        });
        loadTodos();
    }
});
```

---

[Kembali ke Daftar Isi](../README.md)