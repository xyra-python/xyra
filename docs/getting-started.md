<file_path>
xyra/docs/getting-started.md
</file_path>

<edit_description>
Buat file memulai
</edit_description>

# Getting Started with Xyra

Welcome to Xyra! This section will help you create your first web application with the Xyra framework.

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher
- pip package manager
- Basic knowledge of Python

## Installation

First, install Xyra using pip:

```bash
pip install xyra
```

Or install from source:

```bash
git clone https://github.com/xyra-framework/xyra.git
cd xyra
pip install -e .
```

## Your First Application

Let's create a simple web application that displays "Hello, Xyra!".

### 1. Create the Application File

Create a new file named `app.py` and add the following code:

```python
from xyra import App, Request, Response

# Initialize the application
app = App()

# Define a route for the home page
@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Hello, Xyra!"})

# Run the server
if __name__ == "__main__":
    app.listen(8000)
```

### 2. Run the Application

Run the application with the command:

```bash
python app.py
```

You should see output like:

```
🚀 Xyra server running on http://0.0.0.0:8000
```

### 3. Access the Application

Open your browser and visit `http://localhost:8000`. You will see a JSON response:

```json
{
  "message": "Hello, Xyra!"
}
```

## Code Explanation

- `from xyra import App, Request, Response`: Import the main components from Xyra
- `app = App()`: Create an application instance
- `@app.get("/")`: Decorator to handle GET requests to the root path "/"
- `def home(req: Request, res: Response)`: Handler function that receives Request and Response objects
- `res.json({"message": "Hello, Xyra!"})`: Send a JSON response
- `app.listen(8000)`: Start the server on port 8000

## Building a More Complex Application

Let's create a simple API for managing tasks:

```python
from xyra import App, Request, Response
from typing import List, Dict, Any

app = App()

# In-memory storage (use a database in production)
tasks = [
    {"id": 1, "title": "Learn Xyra", "completed": False},
    {"id": 2, "title": "Build an app", "completed": True}
]

@app.get("/tasks")
def get_tasks(req: Request, res: Response) -> List[Dict[str, Any]]:
    """Get all tasks."""
    res.json(tasks)

@app.post("/tasks")
async def create_task(req: Request, res: Response) -> Dict[str, Any]:
    """Create a new task."""
    task_data = await req.json()

    # Validate input
    if not task_data.get("title"):
        res.status(400)
        res.json({"error": "Title is required"})
        return

    # Create new task
    new_task = {
        "id": len(tasks) + 1,
        "title": task_data["title"],
        "completed": task_data.get("completed", False)
    }

    tasks.append(new_task)
    res.status(201)
    res.json(new_task)

@app.put("/tasks/{task_id}")
async def update_task(req: Request, res: Response) -> Dict[str, Any]:
    """Update a task."""
    task_id = int(req.params.get("task_id"))
    update_data = await req.json()

    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        res.status(404)
        res.json({"error": "Task not found"})
        return

    task.update(update_data)
    res.json(task)

@app.delete("/tasks/{task_id}")
def delete_task(req: Request, res: Response):
    """Delete a task."""
    task_id = int(req.params.get("task_id"))

    global tasks
    tasks = [t for t in tasks if t["id"] != task_id]

    res.status(204)  # No Content

if __name__ == "__main__":
    print("🚀 Task API running on http://localhost:8000")
    app.listen(8000)
```

## Testing Your API

You can test the API using curl:

```bash
# Get all tasks
curl http://localhost:8000/tasks

# Create a new task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "New task"}'

# Update a task
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete a task
curl -X DELETE http://localhost:8000/tasks/1
```

## Adding HTML Templates

Let's add HTML rendering to your application:

```python
from xyra import App, Request, Response

app = App(templates_directory="templates")

@app.get("/")
def home(req: Request, res: Response):
    res.render("home.html", title="My Xyra App", message="Welcome!")

@app.get("/about")
def about(req: Request, res: Response):
    res.render("about.html", title="About", version="1.0.0")

if __name__ == "__main__":
    app.listen(8000)
```

Create a `templates` directory and add `home.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    <a href="/about">About</a>
</body>
</html>
```

## Next Steps

- Learn [Routing](routing.md) to add more endpoints
- Explore [Request & Response](request-response.md) to understand request/response objects
- Try [Templating](templating.md) for HTML rendering
- Check out [Middleware](middleware.md) for cross-cutting concerns
- See [Examples](examples.md) for complete applications

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port number in `app.listen(port)`
2. **Import errors**: Make sure Xyra is installed correctly with `pip install xyra`
3. **Template not found**: Ensure the `templates` directory exists and contains your template files

### Getting Help

- Check the [API Reference](api-reference.md) for detailed documentation
- Visit the [GitHub Issues](https://github.com/xyra-framework/xyra/issues) for common problems
- Join our [Discord Community](https://discord.gg/xyra) for support

---

[Back to Table of Contents](../README.md)