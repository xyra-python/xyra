import sys
from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
def h():
    return "Hello, World!"

if __name__ == "__main__":
    app.start(port=8002, host="127.0.0.1")
