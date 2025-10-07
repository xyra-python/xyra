# Xyra Framework

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/xyra.svg)](https://pypi.org/project/xyra/)

A high-performance, asynchronous web framework for Python, built on top of `socketify.py`. Xyra is designed to be fast, easy to use, and feature-rich, making it an excellent choice for building modern web applications, APIs, and real-time applications.

## ✨ Key Features

- 🚀 **High Performance**: Built on `socketify.py` for exceptional speed and low latency
- ⚡ **Asynchronous**: Full async/await support for non-blocking operations
- 🎯 **Simple API**: Intuitive design inspired by Flask and Express.js
- 🔧 **Middleware Support**: Easily add logging, authentication, CORS, and more
- 📚 **Auto API Docs**: Built-in Swagger/OpenAPI documentation generation
- 🔌 **WebSocket Support**: Real-time communication out of the box
- 📄 **Templating**: Jinja2 integration for HTML rendering
- 📁 **Static Files**: Efficient static file serving
- 🛡️ **Type Safety**: Full type hints support

## 📦 Installation

Install Xyra using pip:

```bash
pip install xyra
```

Or install from source for the latest features:

```bash
git clone https://github.com/xyra-python/xyra.git
cd xyra
pip install -e .
```

## 🚀 Quick Start

Create your first Xyra application:

```python
# app.py
from xyra import App, Request, Response

app = App()

@app.get("/")
def hello(req: Request, res: Response):
    res.json({"message": "Hello, Xyra!"})

if __name__ == "__main__":
    app.listen(8000)
```

Run the application:

```bash
python app.py
```

Visit `http://localhost:8000` to see your app in action!

## 📖 Documentation

- 📚 [Full Documentation](docs/README.md)
- 🚀 [Getting Started Guide](docs/getting-started.md)
- 🛣️ [Routing Guide](docs/routing.md)
- 📝 [API Reference](docs/api-reference.md)
- 💡 [Examples](docs/examples.md)

## 🎯 Example Applications

### REST API

```python
from xyra import App, Request, Response

app = App()

# In-memory storage
users = []

@app.get("/api/users")
def get_users(req: Request, res: Response):
    res.json(users)

@app.post("/api/users")
async def create_user(req: Request, res: Response):
    user_data = await req.json()
    user_data["id"] = len(users) + 1
    users.append(user_data)
    res.status(201).json(user_data)

if __name__ == "__main__":
    app.listen(8000)
```

### WebSocket Chat

```python
from xyra import App

app = App()
clients = set()

def on_open(ws):
    clients.add(ws)
    ws.send("Welcome to chat!")

def on_message(ws, message, opcode):
    for client in clients:
        if client != ws:
            client.send(f"User: {message}")

def on_close(ws, code, message):
    clients.discard(ws)

app.websocket("/chat", {
    "open": on_open,
    "message": on_message,
    "close": on_close
})

if __name__ == "__main__":
    app.listen(8000)
```

### HTML with Templates

```python
from xyra import App, Request, Response

app = App(templates_directory="templates")

@app.get("/")
def home(req: Request, res: Response):
    res.render("home.html", title="My App", users=["Alice", "Bob"])

if __name__ == "__main__":
    app.listen(8000)
```

## 🏃 Running Examples

Try the included examples:

```bash
# Simple app
python example/simple_app.py

# Full-featured app with templates and WebSocket
python example/app.py
```

Visit `http://localhost:8000` and explore the API docs at `http://localhost:8000/docs`.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Setup

```bash
git clone https://github.com/xyra-python/xyra.git
cd xyra
pip install -e .[dev]
pytest
```

### Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of [socketify.py](https://github.com/cirospaciari/socketify.py)
- Inspired by Flask, Express.js, and FastAPI
- Thanks to all our contributors!

## 📞 Support

- 📖 [Documentation](docs/README.md)
- 🐛 [Issues](https://github.com/xyra-python/xyra/issues)
- 💬 [Discussions](https://github.com/xyra-python/xyra/discussions)

---

Made with ❤️ for the Python community