# app/webapi.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from .cli import run

app = FastAPI(title="Web API")

@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"

@app.get("/")
async def root():
    return {"status": "ok", "docs": "/docs", "health": "/healthz"}

@app.get("/profile")
async def profile(username: str, query: str | None = None):
    data = await run(query=query, username=username, headless=True)
    return JSONResponse(data)

@app.get("/profile.txt", response_class=PlainTextResponse)
async def profile_txt(username: str):
    data = await run(query=None, username=username, headless=True)
    # Make a simple text output
    lines = [f"{k}: {v}" for k, v in data.items()]
    return "\n".join(lines)
