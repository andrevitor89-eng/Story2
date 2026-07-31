from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import auth, books, jobs, stories, voices

app = FastAPI(title="Story2 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stories.router)
app.include_router(books.router)
app.include_router(jobs.router)
app.include_router(voices.router)


@app.get("/health")
def health() -> dict:
    from app.config import settings

    return {
        "ok": True,
        "service": "story2",
        "has_gemini": bool(settings.gemini_api_key),
        "has_elevenlabs": bool(settings.elevenlabs_api_key),
        "storage_backend": settings.storage_backend,
        "offline_fallback": settings.offline_fallback,
    }


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
