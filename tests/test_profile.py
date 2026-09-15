"""Unified profile tests: per-game summaries, cross-game totals, chart render."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.charts import generate_profile_chart
from analytics.profile import unified_profile
from core.models import Pull


def pull(game_id, pool, name, q, t, item_type=""):
    return Pull(pool, "res", name, q, t, "u", game_id=game_id, item_type=item_type)


def test_unified_profile_aggregates_totals():
    pulls_by_game = {
        "wuthering_waves": [
            pull("wuthering_waves", "1", "Jinhsi", 5, "2025-01-01 12:00:00"),
            pull("wuthering_waves", "1", "F", 3, "2025-01-02 12:00:00"),
        ],
        "genshin_impact": [
            pull("genshin_impact", "301", "Nahida", 5, "2024-01-01 10:00:00", item_type="Character"),
            pull("genshin_impact", "301", "F", 4, "2024-01-02 10:00:00"),
            pull("genshin_impact", "301", "F2", 3, "2024-01-03 10:00:00"),
        ],
        # HSR absent — should simply be missing from games
    }
    u = unified_profile(pulls_by_game)
    assert u["games_with_data"] == 2
    assert "honkai_star_rail" not in u["games"]
    assert u["total_pulls"] == 5
    assert u["total_5"] == 2
    assert u["total_4"] == 1
    assert u["total_currency"] == 5 * 160


def test_per_game_summary_fields():
    pulls_by_game = {
        "genshin_impact": [
            pull("genshin_impact", "301", "Nahida", 5, "2024-01-01 10:00:00", item_type="Character"),
            pull("genshin_impact", "301", "Qiqi", 5, "2024-02-01 10:00:00", item_type="Character"),
            pull("genshin_impact", "301", "F", 3, "2024-02-05 10:00:00"),
        ],
    }
    u = unified_profile(pulls_by_game)
    g = u["games"]["genshin_impact"]
    assert g["total_pulls"] == 3
    assert g["count_5"] == 2
    assert g["rate_5"] == pytest.approx(2 / 3 * 100, rel=0.01)
    assert g["won_5050"] == 1 and g["lost_5050"] == 1  # Nahida won, Qiqi lost
    assert g["is_guaranteed"] is True
    assert g["avg_pity"] > 0


def test_empty_profile():
    u = unified_profile({})
    assert u["games_with_data"] == 0 and u["total_pulls"] == 0
    assert u["total_currency"] == 0


def test_profile_chart_renders_png():
    pulls_by_game = {
        "wuthering_waves": [pull("wuthering_waves", "1", "J", 5, "2025-01-01 12:00:00"),
                            pull("wuthering_waves", "1", "F", 3, "2025-01-02 12:00:00")],
        "genshin_impact": [pull("genshin_impact", "301", "N", 5, "2024-01-01 10:00:00", item_type="Character")],
    }
    profile = unified_profile(pulls_by_game)
    buf = generate_profile_chart(profile, "u")
    assert buf.getvalue()[:8] == b"\x89PNG\r\n\x1a\n"


def test_profile_chart_empty_data_renders():
    profile = unified_profile({})
    buf = generate_profile_chart(profile, "u")
    assert len(buf.getvalue()) > 1000
