from xyra.application import App
from xyra.request import Request
from xyra.response import Response
from xyra.middleware.cors import CorsMiddleware

# 1. Initialize the app with Swagger options
app = App(swagger_options={
    "title": "Xyra Example API",
    "version": "1.0.0",
    "swagger_ui_path": "/docs"  # URL to access Swagger UI
})

# 2. Define and use middlewares
async def logger_middleware(req: Request, res: Response, next_handler):
    print(f"Request: {req.method} {req.url}")
    await next_handler()
    print(f"Response: {res.status_code}")

app.use(logger_middleware)

# Use the reusable CorsMiddleware
cors_middleware = CorsMiddleware(
    allowed_origins=["*"],
    allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowed_headers=["Content-Type", "Authorization"],
)
app.use(cors_middleware)


# 3. Define some routes
@app.get("/")
def home(req: Request, res: Response):
    """
    A simple route that returns a welcome message.
    """
    res.json({"message": "Welcome to Xyra!"})

@app.post("/items")
async def create_item(req: Request, res: Response):
    """
    Creates an item.

    Expects a JSON body with "name" and "price".
    """
    data = await req.json()
    name = data.get("name")
    price = data.get("price")
    if not name or not price:
        res.status_code = 400
        res.json({"error": "Name and price are required."})
        return

    res.json({"id": "some-uuid", "name": name, "price": price})

@app.get("/items/{item_id}")
def get_item(req: Request, res: Response):
    """
    Gets a specific item by its ID.
    """
    item_id = req.params.get('item_id')
    res.json({"id": item_id, "name": f"Item {item_id}", "price": 10.0})

@app.put("/items/{item_id}")
async def update_item(req: Request, res: Response):
    """
    Updates an item.
    """
    item_id = req.params.get('item_id')
    item_data = await req.json()
    res.json({"id": item_id, "name": item_data.get("name"), "price": item_data.get("price"), "status": "updated"})

@app.delete("/items/{item_id}")
def delete_item(req: Request, res: Response):
    """
    Deletes an item.
    """
    item_id = req.params.get('item_id')
    res.json({"id": item_id, "status": "deleted"})

# 4. Run the app
if __name__ == "__main__":
    # To run: python -m xyra example/app.py
    # Docs will be at http://localhost:8000/docs
    app.listen(port=8000)