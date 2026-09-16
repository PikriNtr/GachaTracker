"""Banner schedule chart tests: ensure windows are rendered and empty state handled."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.charts import generate_banner_schedule_chart


def make_window(pool, name, start_dt, end_dt):
    """Helper: build a window dict compatible with Repository.get_banner_windows()."""
    return {
        "id": 1,
        "game_id": pool.split("_")[0] if "_" in pool else "wuthering_waves",
        "card_pool_type": pool,
        "banner_name": name,
        "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "created_by": "test_user",
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }


@pytest.mark.parametrize("game_id", ["wuthering_waves", "genshin_impact", "honkai_star_rail"])
def test_banner_schedule_empty(game_id):
    buf = generate_banner_schedule_chart([], "u123", game_id)
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 800


def test_banner_schedule_with_one_game():
    base = datetime(2025, 1, 5, 10, 0, 0)
    windows = [
        make_window("1", "Featured Resonator", base, base + timedelta(days=14)),
        make_window("1", "Next Event", base + timedelta(days=16), base + timedelta(days=30)),
        make_window("2", "Weapon Pool", base + timedelta(days=5), base + timedelta(days=20)),
    ]
    buf = generate_banner_schedule_chart(windows, "u456", "wuthering_waves")
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 1200


def test_banner_schedule_mixed_pools():
    base = datetime(2024, 11, 1, 8, 0, 0)
    windows = [
        make_window("301", "Character Event Wish", base, base + timedelta(days=17)),
        make_window("302", "Standard Warp", base - timedelta(days=5), base + timedelta(days=10)),
        make_window("400", "Event Warp", base + timedelta(days=10), base + timedelta(days=25)),
    ]
    buf = generate_banner_schedule_chart(windows, "hsr_player", "genshin_impact")
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 1500
