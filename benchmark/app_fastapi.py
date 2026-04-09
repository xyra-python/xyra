from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, HTMLResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/text", response_class=PlainTextResponse)
async def text_endpoint():
    return "Hello, World!"

@app.get("/html", response_class=HTMLResponse)
async def html_endpoint():
    return "<h1>Hello, World!</h1>"
