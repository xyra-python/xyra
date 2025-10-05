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
    app.listen(8080)