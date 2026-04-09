from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
def h():
    return {"message": "Hello, World!"}

from robyn.robyn import Response

@app.get("/text")
def text_endpoint():
    return "Hello, World!"

@app.get("/html")
def html_endpoint():
    return Response(
        status_code=200,
        headers={"Content-Type": "text/html"},
        description="<h1>Hello, World!</h1>"
    )

if __name__ == "__main__":
    app.start(port=8002, host="127.0.0.1")
