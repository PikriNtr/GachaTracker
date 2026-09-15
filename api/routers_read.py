"""Read routers: games, accounts, pulls, pity, stats, profile."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from analytics import calculate_deep_statistics, calculate_pity_summary, unified_profile
from analytics.pity import GAME_BANNER_CONFIGS
from analytics.profile import GAME_ORDER
from api.deps import Pagination, get_repo, maybe_require_read_key, require_game
from api.models import (
    AccountOut,
    AccountsOut,
    DeepStatsOut,
    PitySummaryOut,
    ProfileOut,
    PullOut,
    PullPageOut,
)
from database.repository import Repository

router = APIRouter(dependencies=[Depends(maybe_require_read_key)])


@router.get("/games")
def list_games() -> Dict[str, Any]:
    """Registered games with their banner configs."""
    return {
        "games": [
            {
                "game_id": gid,
                "name": GAME_BANNER_CONFIGS[gid]["names"],
                "pools": GAME_BANNER_CONFIGS[gid]["pools"],
                "pity_caps": GAME_BANNER_CONFIGS[gid]["pity_caps"],
            }
            for gid in GAME_ORDER
        ]
    }


@router.get("/accounts/{discord_id}", response_model=AccountsOut)
def list_accounts(discord_id: str, repo: Repository = Depends(get_repo)):
    """All game accounts stored for a Discord user, with pull counts."""
    accounts: list[AccountOut] = []
    for gid in GAME_ORDER:
        account = repo.get_account_by_discord_id(discord_id, gid)
        if account is None:
            continue
        pulls = repo.get_pulls(discord_id, gid)
        accounts.append(AccountOut(
            discord_id=discord_id, game_id=gid,
            player_id=account.player_id, total_pulls=len(pulls),
        ))
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for this user.")
    return AccountsOut(discord_id=discord_id, accounts=accounts)


def _load_pulls_or_404(repo: Repository, discord_id: str, game_id: str):
    require_game(game_id)
    account = repo.get_account_by_discord_id(discord_id, game_id)
    pulls = repo.get_pulls(discord_id, game_id)
    if account is None or not pulls:
        raise HTTPException(
            status_code=404,
            detail=f"No data for user {discord_id} in '{game_id}'. Import first.",
        )
    return account, pulls


@router.get("/accounts/{discord_id}/pulls/{game_id}", response_model=PullPageOut)
def list_pulls(discord_id: str, game_id: str,
               pagination: Pagination = Depends(),
               card_pool_type: str | None = None,
               quality_level: int | None = None,
               repo: Repository = Depends(get_repo)):
    """Pull history, oldest-first, paginated. Filter by pool and/or rarity."""
    account, pulls = _load_pulls_or_404(repo, discord_id, game_id)
    if card_pool_type is not None:
        pulls = [p for p in pulls if str(p.card_pool_type) == str(card_pool_type)]
    if quality_level is not None:
        pulls = [p for p in pulls if p.quality_level == quality_level]

    page = pulls[pagination.offset: pagination.offset + pagination.limit]
    return PullPageOut(
        total=len(pulls),
        limit=pagination.limit,
        offset=pagination.offset,
        items=[PullOut(
            card_pool_type=p.card_pool_type,
            resource_id=p.resource_id,
            resource_name=p.resource_name,
            quality_level=p.quality_level,
            time=p.time,
            player_id=p.player_id,
            game_id=p.game_id,
            item_type=p.item_type,
            pity_at_pull=p.pity_at_pull,
            is_5050_win=p.is_5050_win,
        ) for p in page],
    )


@router.get("/accounts/{discord_id}/pity/{game_id}", response_model=PitySummaryOut)
def get_pity(discord_id: str, game_id: str, repo: Repository = Depends(get_repo)):
    """Per-banner pity summary (current pity, 50/50 record, guarantee state)."""
    account, pulls = _load_pulls_or_404(repo, discord_id, game_id)
    summary = calculate_pity_summary(pulls, game_id)
    return PitySummaryOut(game_id=game_id, player_id=account.player_id, banners=summary)


@router.get("/accounts/{discord_id}/stats/{game_id}", response_model=DeepStatsOut)
def get_stats(discord_id: str, game_id: str, repo: Repository = Depends(get_repo)):
    """Deep statistics: pity distribution, early 5-stars, char/weapon split."""
    account, pulls = _load_pulls_or_404(repo, discord_id, game_id)
    deep = calculate_deep_statistics(pulls, game_id)
    return DeepStatsOut(game_id=game_id, pools=deep)


@router.get("/accounts/{discord_id}/profile", response_model=ProfileOut)
def get_profile(discord_id: str, repo: Repository = Depends(get_repo)):
    """Unified cross-game profile (same data as the /profile command)."""
    pulls_by_game = {gid: repo.get_pulls(discord_id, gid) for gid in GAME_ORDER}
    profile = unified_profile(pulls_by_game)
    if not profile["games"]:
        raise HTTPException(status_code=404, detail="No data found for this user in any game.")

    label = ", ".join(
        repo.get_account_by_discord_id(discord_id, gid).player_id
        for gid in profile["games"]
        if repo.get_account_by_discord_id(discord_id, gid)
    ) or discord_id
    return ProfileOut(player_label=label, profile=profile)
