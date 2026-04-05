from xyra import App

app = App()

@app.get("/")
def home(req, res):
    res.json({"message": "Hello, World!"})

@app.get("/text")
def text_endpoint(req, res):
    res.send("Hello, World!")

if __name__ == "__main__":
    app.listen(8000)
