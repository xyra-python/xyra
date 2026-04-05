from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/text", response_class=PlainTextResponse)
async def text_endpoint():
    return "Hello, World!"
