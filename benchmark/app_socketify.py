from socketify import App

app = App()

def home(res, req):
    res.cork(lambda res: res.send({"message": "Hello, World!"}))

def text_endpoint(res, req):
    res.cork(lambda res: res.send("Hello, World!"))

def html_endpoint(res, req):
    res.cork(lambda res: res.end("<h1>Hello, World!</h1>"))

app.get("/", home)
app.get("/text", text_endpoint)
app.get("/html", html_endpoint)

if __name__ == "__main__":
    app.listen(3000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n"))
    app.run()
