"""Pity engine tests: per-game banner configs, 50/50 chains, chronology, caps."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models import Pull
from analytics.pity import calculate_pity_summary, GAME_BANNER_CONFIGS


def pull(game_id, pool, name, q, t, item_type=""):
    return Pull(pool, "res", name, q, t, "player1", game_id=game_id, item_type=item_type)


# ── WuWa ──────────────────────────────────────────────────────────────
def test_wuwa_won_then_lost_5050_chain():
    pulls = [
        pull("wuthering_waves", "1", "Jinhsi", 5, "2025-01-01 12:00:00"),   # featured -> won
        pull("wuthering_waves", "1", "Jianxin", 5, "2025-02-01 12:00:00"),  # standard -> lost
    ]
    s = calculate_pity_summary(pulls, "wuthering_waves")
    hist = s["1"]["history_5star"]  # newest-first
    assert hist[0]["result"] == "Lost 50/50"
    assert hist[1]["result"] == "Won 50/50"
    assert s["1"]["is_guaranteed"] is True
    assert s["1"]["won_5050"] == 1 and s["1"]["lost_5050"] == 1


def test_wuwa_guaranteed_consumed():
    pulls = [
        pull("wuthering_waves", "1", "Jianxin", 5, "2025-01-01 12:00:00"),  # lost
        pull("wuthering_waves", "1", "Calcharo", 5, "2025-02-01 12:00:00"), # guaranteed (standard but consumed)
    ]
    s = calculate_pity_summary(pulls, "wuthering_waves")
    assert s["1"]["history_5star"][0]["result"] == "Guaranteed"
    assert s["1"]["is_guaranteed"] is False  # consumed


def test_wuwa_pity_counts_and_chronology():
    # Insert newest-first (API order); engine must sort chronologically
    pulls = [
        pull("wuthering_waves", "1", "Filler B", 3, "2025-02-01 12:00:00"),
        pull("wuthering_waves", "1", "Filler A", 3, "2025-01-01 12:00:00"),
    ]
    s = calculate_pity_summary(pulls, "wuthering_waves")
    assert s["1"]["current_pity"] == 2
    assert s["1"]["total_pulls"] == 2
    assert s["1"]["max_pity"] == 80


def test_wuwa_5050_only_on_pool_1():
    pulls = [pull("wuthering_waves", "3", "Jianxin", 5, "2025-01-01 12:00:00")]
    s = calculate_pity_summary(pulls, "wuthering_waves")
    assert s["3"]["history_5star"][0]["result"] == "N/A"
    assert s["3"]["is_guaranteed"] is False


def test_wuwa_weapon_5star_not_a_5050_loss():
    pulls = [
        pull("wuthering_waves", "1", "Jianxin", 5, "2025-01-01 12:00:00", item_type="Resonator"),
        pull("wuthering_waves", "1", "Some Weapon", 5, "2025-02-01 12:00:00", item_type="Resonator Equipment"),
    ]
    s = calculate_pity_summary(pulls, "wuthering_waves")
    hist = s["1"]["history_5star"]
    assert hist[0]["result"] == "N/A"          # weapon: N/A
    assert hist[0]["is_standard"] is True
    assert hist[1]["result"] == "Lost 50/50"   # chain preserved
    assert s["1"]["is_guaranteed"] is True     # weapon did not consume it


# ── Genshin ───────────────────────────────────────────────────────────
def test_genshin_caps_and_pools():
    s = calculate_pity_summary([], "genshin_impact")
    assert set(s) == {"301", "400", "302", "500", "200", "100"}
    assert s["301"]["max_pity"] == 90
    assert s["302"]["max_pity"] == 80
    assert s["100"]["max_pity"] == 20
    assert s["500"]["name"] == "Chronicled Wish"


def test_genshin_standard_set_and_guarantee():
    pulls = [
        pull("genshin_impact", "301", "Nahida", 5, "2024-01-01 10:00:00", item_type="Character"),
        pull("genshin_impact", "301", "Qiqi", 5, "2024-02-01 10:00:00", item_type="Character"),
        pull("genshin_impact", "301", "Nahida", 5, "2024-03-01 10:00:00", item_type="Character"),
    ]
    s = calculate_pity_summary(pulls, "genshin_impact")
    hist = s["301"]["history_5star"]
    assert hist[2]["result"] == "Won 50/50"
    assert hist[1]["result"] == "Lost 50/50"
    assert hist[0]["result"] == "Guaranteed"
    assert s["301"]["is_guaranteed"] is False


def test_genshin_400_also_has_5050():
    pulls = [pull("genshin_impact", "400", "Diluc", 5, "2024-01-01 10:00:00", item_type="Character")]
    s = calculate_pity_summary(pulls, "genshin_impact")
    assert s["400"]["history_5star"][0]["result"] == "Lost 50/50"


# ── HSR ───────────────────────────────────────────────────────────────
def test_hsr_light_cone_not_counted_as_5050_loss():
    pulls = [
        pull("honkai_star_rail", "1", "Bronya", 5, "2024-01-01 10:00:00", item_type="Character"),
        pull("honkai_star_rail", "1", "Moment of Victory", 5, "2024-02-01 10:00:00", item_type="Light Cone"),
        pull("honkai_star_rail", "1", "Seele", 5, "2024-03-01 10:00:00", item_type="Character"),
    ]
    s = calculate_pity_summary(pulls, "honkai_star_rail")
    hist = s["1"]["history_5star"]
    assert hist[1]["result"] == "N/A"          # LC: no 50/50 participation
    assert hist[0]["result"] == "Guaranteed"   # Bronya's loss -> Seele guaranteed
    assert hist[2]["result"] == "Lost 50/50"
    assert s["1"]["lost_5050"] == 1 and s["1"]["won_5050"] == 0


def test_hsr_lc_banner_not_marked_5050():
    assert "2" not in GAME_BANNER_CONFIGS["honkai_star_rail"]["5050_pools"]
    pulls = [pull("honkai_star_rail", "2", "Some LC", 5, "2024-01-01 10:00:00", item_type="Light Cone")]
    s = calculate_pity_summary(pulls, "honkai_star_rail")
    assert s["2"]["history_5star"][0]["result"] == "N/A"
    assert s["2"]["max_pity"] == 80


def test_hsr_standard_set():
    pulls = [pull("honkai_star_rail", "1", "Himeko", 5, "2024-01-01 10:00:00", item_type="Character")]
    s = calculate_pity_summary(pulls, "honkai_star_rail")
    assert s["1"]["history_5star"][0]["result"] == "Lost 50/50"


def test_pity_independent_across_pools():
    pulls = [
        pull("genshin_impact", "301", "Nahida", 5, "2024-01-01 10:00:00", item_type="Character"),
        pull("genshin_impact", "302", "Weapon", 5, "2024-01-01 10:00:00", item_type="Weapon"),
    ]
    s = calculate_pity_summary(pulls, "genshin_impact")
    assert s["301"]["current_pity"] == 0 and s["302"]["current_pity"] == 0
    assert s["200"]["current_pity"] == 0 and s["200"]["total_pulls"] == 0


def test_unknown_game_falls_back_to_wuwa():
    pulls = [pull("some_unknown", "1", "Jinhsi", 5, "2025-01-01 12:00:00")]
    s = calculate_pity_summary(pulls, "some_unknown")
    assert s["1"]["max_pity"] == 80
