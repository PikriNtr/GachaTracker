"""GachaTracker REST API (Phase 11 & 12).

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000   (from gacha_tracker/)
Docs: http://localhost:8000/docs  (auto-generated Swagger UI)
Web:  http://localhost:8000/      (interactive Web Dashboard)

Reads are open by default; set API_REQUIRE_KEY_FOR_READS=1 to gate them.
Writes (import/delete) always require the X-API-Key header.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers_banners import router as banners_router
from api.routers_read import router as read_router
from api.routers_write import router as write_router

app = FastAPI(
    title="GachaTracker API",
    description="Multi-game gacha tracking and analytics (Wuthering Waves, Genshin Impact, Honkai: Star Rail).",
    version="0.6.0",
)

# Enable CORS for web dashboards and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(read_router, tags=["read"])
app.include_router(banners_router, tags=["banners"])
app.include_router(write_router, tags=["write"])

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["meta"])
def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {
        "message": "GachaTracker API is running",
        "docs": "/docs",
        "health": "/health",
        "version": "0.6.0",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
