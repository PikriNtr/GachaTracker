"""Unified multi-game profile: per-game summary + cross-game totals.

All values recomputed from merged DB history — never accumulated.
"""
import statistics
from typing import Any, Dict, List

from analytics.pity import DEFAULT_GAME, GAME_BANNER_CONFIGS, calculate_pity_summary
from core.models import Pull

# Presentation order for /profile and /crossstats
GAME_ORDER = ["wuthering_waves", "genshin_impact", "honkai_star_rail"]

GAME_DISPLAY_NAMES = {
    "wuthering_waves": "Wuthering Waves",
    "genshin_impact": "Genshin Impact",
    "honkai_star_rail": "Honkai: Star Rail",
}

GAME_UI = {
    "wuthering_waves": {"currency_one": "Astrite"},
    "genshin_impact": {"currency_one": "Primogem"},
    "honkai_star_rail": {"currency_one": "Stellar Jade"},
}


def game_profile(pulls: List[Pull], game_id: str) -> Dict[str, Any]:
    """Per-game summary: totals, 5-star count/rate, featured pity, guarantee, 50/50."""
    cfg = GAME_BANNER_CONFIGS.get(game_id, GAME_BANNER_CONFIGS[DEFAULT_GAME])
    featured_pool = cfg["featured_pool"]

    summary = calculate_pity_summary(pulls, game_id)
    p1 = summary.get(featured_pool, {})
    hist = p1.get("history_5star", [])

    total_pulls = len(pulls)
    count_5 = sum(1 for p in pulls if p.quality_level == 5)
    count_4 = sum(1 for p in pulls if p.quality_level == 4)

    won = p1.get("won_5050", 0)
    lost = p1.get("lost_5050", 0)
    total_5050 = won + lost

    pities = sorted(h["pity"] for h in hist)

    return {
        "game_id": game_id,
        "total_pulls": total_pulls,
        "count_5": count_5,
        "count_4": count_4,
        "rate_5": (count_5 / total_pulls * 100) if total_pulls else 0.0,
        "featured_name": p1.get("name", ""),
        "featured_pity": p1.get("current_pity", 0),
        "featured_cap": p1.get("max_pity", 80),
        "is_guaranteed": p1.get("is_guaranteed", False),
        "won_5050": won,
        "lost_5050": lost,
        "win_rate_5050": (won / total_5050 * 100) if total_5050 else 0.0,
        "avg_pity": (sum(pities) / len(pities)) if pities else 0.0,
        "median_pity": statistics.median(pities) if pities else 0.0,
        "lifetime_since_5": p1.get("current_pity", 0),  # pulls since last featured 5-star
        "banner_summaries": summary,
    }


def unified_profile(pulls_by_game: Dict[str, List[Pull]]) -> Dict[str, Any]:
    """Builds per-game profiles + cross-game totals from raw pulls per game.

    pulls_by_game maps game_id -> list of Pull (already fetched from the repo).
    """
    games: Dict[str, Any] = {}
    for game_id in GAME_ORDER:
        pulls = pulls_by_game.get(game_id) or []
        if pulls:
            games[game_id] = game_profile(pulls, game_id)

    total_pulls = sum(g["total_pulls"] for g in games.values())
    total_5 = sum(g["count_5"] for g in games.values())
    total_4 = sum(g["count_4"] for g in games.values())
    # Currency equivalent: all three games price a pull at 160.
    total_currency = total_pulls * 160

    all_5050_won = sum(g["won_5050"] for g in games.values())
    all_5050_total = all_5050_won + sum(g["lost_5050"] for g in games.values())

    return {
        "games": games,
        "games_with_data": len(games),
        "total_pulls": total_pulls,
        "total_5": total_5,
        "total_4": total_4,
        "rate_5": (total_5 / total_pulls * 100) if total_pulls else 0.0,
        "total_currency": total_currency,
        "lifetime_5050_win_rate": (all_5050_won / all_5050_total * 100) if all_5050_total else 0.0,
    }
