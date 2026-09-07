# main.py
# This file does NOT change backend.py at all.
# It just imports the existing `app` object and attaches the frontend to it,
# so running this one file gives you both the API and the UI.

from backend import app  # <-- your original code, untouched
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Allow the frontend to call the API even if it's ever served from a
# different origin (safe to keep even when served from the same origin).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the UI's JS/CSS/images (currently just index.html, but keep the
# folder for anything you add later).
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")