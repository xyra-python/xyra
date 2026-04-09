from xyra import App

app = App()

@app.get("/")
def home(req, res):
    res.json({"message": "Hello, World!"})

@app.get("/text")
def text_endpoint(req, res):
    res.send("Hello, World!")

@app.get("/html")
def html_endpoint(req, res):
    res.html("<h1>Hello, World!</h1>")

if __name__ == "__main__":
    app.listen(8000)
