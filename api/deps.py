"""Shared FastAPI dependencies: DB handle, auth, pagination."""
from typing import Iterator, Optional

from fastapi import Header, HTTPException, Query, status

import config
from database.repository import Repository

_repo: Optional[Repository] = None


def get_repo() -> Iterator[Repository]:
    """Single shared Repository (SQLite, thread-safe enough for read-mostly use)."""
    global _repo
    if _repo is None:
        _repo = Repository(db_path=config.DB_PATH)
    yield _repo


def require_write_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Write endpoints (import/delete) always require the API key."""
    api_key = config.API_KEY  # read lazily (tests monkeypatch config)
    if not api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY is not configured; write endpoints are disabled.",
        )
    if x_api_key != api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-API-Key.")


def maybe_require_read_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Read endpoints are open unless API_REQUIRE_KEY_FOR_READS is enabled."""
    if not config.API_REQUIRE_KEY_FOR_READS:  # read lazily (tests monkeypatch config)
        return
    require_write_key(x_api_key)


class Pagination:
    """Common limit/offset query params (limit capped at 500)."""

    def __init__(
        self,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ):
        self.limit = limit
        self.offset = offset


def require_game(game_id: str) -> str:
    from analytics.pity import GAME_BANNER_CONFIGS

    if game_id not in GAME_BANNER_CONFIGS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown game '{game_id}'.")
    return game_id


def require_import_lock():
    """One import at a time across the process (API fetches take 10-30s)."""
    from api.state import import_lock

    if import_lock.locked():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="An import is already in progress.")
    return import_lock
