"""Calculator + simulation + embeds tests (post-audit behaviors)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.calculator import _expected_pulls_per_5star, calculate_astrite_cost
from analytics.pity import calculate_pity_summary
from analytics.simulation import PROBABILITY_MODELS, run_monte_carlo_simulation
from bot.embeds import calculate_embed, no_data_embed, pity_embed, stats_embed
from core.models import Pull


def pull(game_id, pool, name, q, t, item_type=""):
    return Pull(pool, "res", name, q, t, "u", game_id=game_id, item_type=item_type)


# ── Calculator ────────────────────────────────────────────────────────
def test_expected_pulls_sane_per_game():
    exp_wuwa = _expected_pulls_per_5star(PROBABILITY_MODELS["wuthering_waves"])
    exp_gi = _expected_pulls_per_5star(PROBABILITY_MODELS["genshin_impact"])
    assert 45 <= exp_wuwa <= 65   # WuWa ~53
    assert 55 <= exp_gi <= 80     # Genshin/HSR ~62


def test_avg_case_model_derived_and_clamped():
    c0 = calculate_astrite_cost(0, False, max_pity=90, game_id="genshin_impact")
    assert c0["avg_case"]["pulls"] == _expected_pulls_per_5star(PROBABILITY_MODELS["genshin_impact"])
    c80 = calculate_astrite_cost(80, False, max_pity=90, game_id="genshin_impact")
    assert c80["avg_case"]["pulls"] == 1   # past expected point: floor at 1 (soft pity nearly guarantees)


def test_worst_case_and_floor():
    assert calculate_astrite_cost(30, True, max_pity=90)["worst_case"]["pulls"] == 60
    assert calculate_astrite_cost(89, True, max_pity=90)["worst_case"]["pulls"] == 1   # floor
    c = calculate_astrite_cost(0, False, max_pity=80)
    assert c["worst_case"]["pulls"] == 160  # remaining + full extra pity
    assert "50/50" in c["worst_case"]["note"]


def test_currency_constant():
    c = calculate_astrite_cost(0, False, max_pity=80)
    assert c["best_case"]["astrites"] == 160
    assert c["worst_case"]["astrites"] == c["worst_case"]["pulls"] * 160


# ── Simulation ────────────────────────────────────────────────────────
@pytest.mark.parametrize("game_id,cap", [
    ("wuthering_waves", 80), ("genshin_impact", 90), ("honkai_star_rail", 90),
])
def test_simulation_percentile_bounds(game_id, cap):
    pulls = [pull(game_id, "1", "T", 5, "2024-01-01 10:00:00", item_type="Character")]
    res = run_monte_carlo_simulation(pulls, num_sims=200, game_id=game_id)
    assert 0 <= res["luck_percentile"] <= 100
    assert res["sim_mean_pity"] > 0
    assert PROBABILITY_MODELS[game_id]["cap"] == cap


def test_lucky_user_gets_high_percentile():
    # 5-stars at pity 5 twice -> very lucky vs simulated mean
    pulls = [
        pull("genshin_impact", "301", "A", 5, "2024-01-01 10:00:00", item_type="Character"),
        pull("genshin_impact", "301", "B", 5, "2024-01-20 10:00:00", item_type="Character"),
        pull("genshin_impact", "301", "C", 5, "2024-02-10 10:00:00", item_type="Character"),
    ]
    res = run_monte_carlo_simulation(pulls, num_sims=500, game_id="genshin_impact")
    assert res["luck_percentile"] > 80


# ── Embeds ────────────────────────────────────────────────────────────
def test_pity_embed_clamps_over_cap():
    summary = {"301": {"name": "Character Event Wish", "current_pity": 92, "max_pity": 90,
                       "total_pulls": 5, "history_5star": [], "is_guaranteed": False,
                       "won_5050": 0, "lost_5050": 0}}
    e = pity_embed("u", summary, "genshin_impact")
    assert "**90 / 90**" in e.fields[0].value
    assert "92 / 90" not in e.fields[0].value


def test_embed_wording_per_game():
    s = calculate_pity_summary([], "honkai_star_rail")
    assert pity_embed("u", s, "honkai_star_rail").title.startswith("Warp Pity")
    assert no_data_embed("honkai_star_rail").title == "No Warp History Found"
    assert no_data_embed("genshin_impact").title == "No Wish History Found"
    assert no_data_embed().title == "No Convene History Found"


def test_calculate_embed_currency_names():
    s = calculate_pity_summary([], "honkai_star_rail")
    calc = calculate_astrite_cost(0, False, max_pity=90, game_id="honkai_star_rail")
    e = calculate_embed("u", s, calc, "honkai_star_rail")
    assert e.title.startswith("Stellar Jade Cost Calculator")
    assert "Stellar Jades" in e.fields[0].value
    # weapon reference row present for HSR
    assert any("Light Cone Event Warp" in f.name for f in e.fields)


def test_stats_embed_currency_investment():
    pulls = [pull("genshin_impact", "301", "N", 5, "2024-01-01 10:00:00", item_type="Character")]
    s = calculate_pity_summary(pulls, "genshin_impact")
    e = stats_embed("u", pulls, s, "genshin_impact")
    assert e.fields[1].name == "Primogem Investment"
    assert "160" in e.fields[1].value
