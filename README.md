# Xyra Framework

Xyra is a high-performance, asynchronous web framework for Python, built on top of `socketify.py`. It's designed to be fast, easy to use, and feature-rich, making it an excellent choice for building modern web applications and APIs.

## Features

- **Asynchronous by Design:** Built for speed and efficiency with async/await support.
- **Fast:** Leverages the performance of `uWebSockets.js` through `socketify.py`.
- **Easy to Use:** A simple and intuitive API inspired by popular frameworks like Flask and Express.
- **Middleware Support:** Easily add functionality like logging, authentication, and CORS.
- **Built-in Swagger/OpenAPI:** Automatically generate interactive API documentation.
- **WebSockets:** Full support for WebSocket communication.
- **Static Files & Templating:** Serve static files and render templates with ease.

## Installation

To install Xyra, you can use pip:

```bash
pip install xyra
```

## Quickstart

Here's a simple "Hello, World!" example to get you started:

```python
# main.py
from xyra.application import App

app = App()

@app.get("/")
def home(req, res):
    res.send("Hello, World!")

if __name__ == "__main__":
    app.listen(8000)
```

To run this application, save it as `main.py` and use the following command:

```bash
python -m xyra main.py
```

## Running the Example

This repository includes a more comprehensive example in the `example/` directory. To run it, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/xyra.git
    cd xyra
    ```

2.  **Run the example application:**
    ```bash
    python -m xyra example/app.py
    ```

The application will be running at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.