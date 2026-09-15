"""GachaTracker REST API (Phase 11).

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000   (from gacha_tracker/)
Docs: http://localhost:8000/docs  (auto-generated Swagger UI)

Reads are open by default; set API_REQUIRE_KEY_FOR_READS=1 to gate them.
Writes (import/delete) always require the X-API-Key header.
"""
from fastapi import FastAPI

from api.routers_banners import router as banners_router
from api.routers_read import router as read_router
from api.routers_write import router as write_router

app = FastAPI(
    title="GachaTracker API",
    description="Multi-game gacha tracking and analytics (Wuthering Waves, Genshin Impact, Honkai: Star Rail).",
    version="0.6.0",
)

app.include_router(read_router, tags=["read"])
app.include_router(banners_router, tags=["banners"])
app.include_router(write_router, tags=["write"])


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
