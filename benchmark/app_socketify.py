from socketify import App

app = App()

def home(res, req):
    res.cork(lambda res: res.send({"message": "Hello, World!"}))

app.get("/", home)

if __name__ == "__main__":
    app.listen(3000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n"))
    app.run()
