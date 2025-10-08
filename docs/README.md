# Xyra Framework Documentation

Xyra is a lightweight and fast Python web framework built on top of socketify for high performance. The framework provides modern features such as flexible routing, templating, WebSocket support, and automatic API documentation.

## Key Features

- 🚀 High performance with socketify
- 🛣️ Flexible routing with parameters and query strings
- 📝 Jinja2 templating engine
- 🔌 WebSocket support for real-time applications
- 📚 Automatic API documentation with Swagger/OpenAPI
- 🔄 Asynchronous request handling
- 🧩 Middleware support for cross-cutting concerns
- 📁 Static file serving
- 🔧 Type hints and modern Python support

## Table of Contents

- [Installation](installation.md)
- [Getting Started](getting-started.md)
- [Routing](routing.md)
- [Request & Response](request-response.md)
- [Logger](logger.md)
- [Templating](templating.md)
- [WebSocket](websocket.md)
- [Swagger Documentation](swagger.md)
- [Middleware](middleware.md)
- [Static Files](static-files.md)
- [Complete Examples](examples.md)
- [API Reference](api-reference.md)

## Quick Start

```python
from xyra import App, Request, Response

app = App()

@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Hello, Xyra!"})

if __name__ == "__main__":
    app.listen(8000, logger=True)  # Enable logging
```

Visit `http://localhost:8000` to see the result.

## Why Xyra?

Xyra is designed to be simple yet powerful, providing the essential features you need for modern web development without unnecessary complexity. Built on socketify, it offers excellent performance while maintaining a clean, Pythonic API.

### Performance

Xyra leverages socketify's high-performance networking capabilities, making it suitable for applications requiring low latency and high throughput.

### Developer Experience

- Intuitive API design
- Comprehensive documentation
- Type hints support
- Modern Python features
- Easy testing and debugging

### Production Ready

- Built-in middleware for common tasks
- WebSocket support for real-time features
- Automatic API documentation
- Static file serving
- CORS support

## Community & Support

- 📖 [Documentation](https://xyra-framework.github.io/)
- 💬 [Discord Community](https://discord.gg/xyra)
- 🐛 [Issue Tracker](https://github.com/xyra-python/xyra/issues)
- 📧 [Mailing List](https://groups.google.com/g/xyra-framework)

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests on GitHub.

### Development Setup

```bash
git clone https://github.com/xyra-python/xyra.git
cd xyra
pip install -e .
```

### Running Tests

```bash
pytest
```

## License

MIT License - see the LICENSE file for details.

---

Made with ❤️ using Xyra Framework