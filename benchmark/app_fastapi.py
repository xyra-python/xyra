from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/text", response_class=PlainTextResponse)
async def text_endpoint():
    return "Hello, World!"
