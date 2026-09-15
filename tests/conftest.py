"""Shared fixtures for GachaTracker tests."""
import sys
from pathlib import Path

import pytest

from core.models import Pull

# Ensure the gacha_tracker package dir is importable (flat import style: core, analytics, ...)
PKG_DIR = Path(__file__).resolve().parent.parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))


def make_pull(
    pool: str = "1",
    name: str = "Jinhsi",
    quality: int = 5,
    time: str = "2025-01-01 12:00:00",
    player_id: str = "1001",
) -> Pull:
    return Pull(
        card_pool_type=pool,
        resource_id="1503",
        resource_name=name,
        quality_level=quality,
        time=time,
        player_id=player_id,
        game_id="wuthering_waves",
    )


@pytest.fixture
def pull_factory():
    return make_pull
