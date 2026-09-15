"""Write routers: import (POST) and delete — always require the API key."""

import threading

from fastapi import APIRouter, Depends, HTTPException

from analytics.pity import GAME_BANNER_CONFIGS
from api.deps import get_repo, require_import_lock, require_write_key
from api.models import DeleteResultOut, ImportResultOut
from core.registry import registry
from database.repository import Repository
from games import register_all_plugins

router = APIRouter(dependencies=[Depends(require_write_key)])

_import_lock = threading.Lock()


def _plugin_for(game_id: str):
    with _import_lock:
        register_all_plugins(registry)
    return registry.get(game_id)


@router.post("/accounts/{discord_id}/import/{game_id}", response_model=ImportResultOut)
def import_history(discord_id: str, game_id: str, body: dict,
                   repo: Repository = Depends(get_repo),
                   lock: threading.Lock = Depends(require_import_lock)):
    """Fetch + merge gacha history for a user. Body: {"url": "..."}.

    Synchronous: a full import takes 10-30s (paginated upstream fetch with
    rate-limit pacing). Guarded by a process-wide lock; a second concurrent
    import gets HTTP 409.
    """
    require_game_id = game_id
    plugin = _plugin_for(require_game_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Unknown game '{game_id}'.")
    url = (body or {}).get("url", "").strip()
    if not url:
        raise HTTPException(status_code=422, detail="Body must be {\"url\": \"...\"}.")

    with lock:
        try:
            player_id, pulls = plugin.fetch_and_parse(url)
        except Exception as exc:  # upstream/API errors surface as 502
            raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {exc}") from exc
        if not pulls:
            raise HTTPException(status_code=422, detail="No records returned by the upstream API.")

        repo.save_account(discord_id=discord_id, game_id=game_id, player_id=player_id)
        new_count = repo.save_pulls(discord_id=discord_id, game_id=game_id,
                                    player_id=player_id, pulls=pulls)
        total = len(repo.get_pulls(discord_id, game_id))

    return ImportResultOut(game_id=game_id, player_id=player_id,
                           new_pulls=new_count, total_pulls=total)


@router.delete("/accounts/{discord_id}/{game_id}", response_model=DeleteResultOut)
def delete_account(discord_id: str, game_id: str, repo: Repository = Depends(get_repo)):
    """Deletes a user's pulls + account for one game (the /forget behavior)."""
    if game_id not in GAME_BANNER_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown game '{game_id}'.")
    removed = repo.delete_user_data(discord_id, game_id)
    return DeleteResultOut(game_id=game_id, deleted_pulls=removed)
