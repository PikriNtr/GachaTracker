"""Banner schedule router: active + upcoming windows per game."""
from typing import Dict

from fastapi import APIRouter, Depends

from api.deps import get_repo, maybe_require_read_key, require_game
from api.models import BannerScheduleOut, BannerWindowOut
from database.repository import Repository

router = APIRouter(dependencies=[Depends(maybe_require_read_key)])


@router.get("/banners/{game_id}", response_model=BannerScheduleOut)
def get_banners(game_id: str, repo: Repository = Depends(get_repo)):
    """Current + upcoming banners per pool (the /banners command data)."""
    require_game(game_id)
    now = None  # let the repo pick current UTC
    active_raw = repo.get_active_banners(game_id, now=now)
    upcoming_raw = repo.get_upcoming_banners(game_id, now=now)

    active: Dict[str, BannerWindowOut] = {
        pool: BannerWindowOut(**row) for pool, row in active_raw.items()
    }
    upcoming: Dict[str, list[BannerWindowOut]] = {
        pool: [BannerWindowOut(**row) for row in rows]
        for pool, rows in upcoming_raw.items()
    }

    return BannerScheduleOut(
        game_id=game_id,
        now=_now(),
        active=active,
        upcoming=upcoming,
    )


def _now() -> str:
    from analytics.schedule_time import now_canonical
    return now_canonical()
