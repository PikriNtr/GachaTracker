"""Pydantic response models — typed, self-documenting JSON (feeds /docs)."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PullOut(BaseModel):
    card_pool_type: str
    resource_id: str
    resource_name: str
    quality_level: int
    time: str
    player_id: str
    game_id: str
    item_type: str
    pity_at_pull: int
    is_5050_win: Optional[bool] = None


class PullPageOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[PullOut]


class BannerWindowOut(BaseModel):
    id: int
    game_id: str
    card_pool_type: str
    banner_name: str
    start_time: str
    end_time: str
    created_by: str
    created_at: str


class BannerScheduleOut(BaseModel):
    game_id: str
    now: str
    active: Dict[str, BannerWindowOut]
    upcoming: Dict[str, List[BannerWindowOut]]


class AccountOut(BaseModel):
    discord_id: str
    game_id: str
    player_id: str
    total_pulls: int


class AccountsOut(BaseModel):
    discord_id: str
    accounts: List[AccountOut]


class PitySummaryOut(BaseModel):
    game_id: str
    player_id: str
    banners: Dict[str, Dict[str, Any]]


class DeepStatsOut(BaseModel):
    game_id: str
    pools: Dict[str, Dict[str, Any]]


class ProfileOut(BaseModel):
    player_label: str
    profile: Dict[str, Any]


class ImportResultOut(BaseModel):
    game_id: str
    player_id: str
    new_pulls: int
    total_pulls: int


class DeleteResultOut(BaseModel):
    game_id: str
    deleted_pulls: int
