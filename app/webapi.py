from fastapi import FastAPI, Query
import os
from .cli import run

app = FastAPI()
HEADLESS = os.getenv("HEADLESS", "1") != "0"

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/profile")
def profile(username: str | None = Query(default=None), query: str | None = Query(default=None)):
    data = run(query=query, username=username, headless=HEADLESS)
    return data or {}
